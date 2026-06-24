from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import SimulationConfig
from .highway_layout import HighwayLayout
from .models import Luminaire, Vehicle, clamp


@dataclass
class LightingController:
    config: SimulationConfig
    hold_until: dict[str, float] = field(default_factory=dict)
    last_emergency_vehicle_ids: set[str] = field(default_factory=set)

    def detect_nearest_pole(self, layout: HighwayLayout, vehicle: Vehicle) -> str:
        return min(
            layout.poles.values(),
            key=lambda pole: abs(pole.position_x - vehicle.position_along_road),
        ).pole_id

    def determine_vehicle_direction(self, vehicle: Vehicle) -> str:
        return vehicle.direction

    def calculate_lights_ahead(self, vehicle_speed: float, pole_spacing: float | None = None) -> int:
        thresholds = self.config.speed_thresholds
        if vehicle_speed < thresholds.low_mps:
            return thresholds.low_ahead
        if vehicle_speed < thresholds.medium_mps:
            return thresholds.medium_ahead
        return thresholds.high_ahead

    def calculate_sequential_brightness_targets(
        self,
        layout: HighwayLayout,
        vehicle: Vehicle,
    ) -> dict[str, float]:
        nearest_pole_id = self.detect_nearest_pole(layout, vehicle)
        nearest_index = layout.pole_index(nearest_pole_id)
        direction_step = 1 if vehicle.direction == "A" else -1
        ahead_count = self.calculate_lights_ahead(vehicle.speed_mps, self.config.pole_spacing_m)
        targets: dict[str, float] = {}

        for offset in range(ahead_count + 1):
            pole_index = nearest_index + offset * direction_step
            if pole_index < 0 or pole_index >= self.config.num_poles:
                continue
            pole_id = f"P{pole_index + 1:03d}"
            luminaire_id = layout.luminaire_id_for(pole_id, vehicle.direction)
            pole = layout.poles[pole_id]
            time_to_arrival = abs(pole.position_x - vehicle.position_along_road) / max(vehicle.speed_mps, 0.1)
            if offset == 0:
                brightness = self.config.normal_peak_brightness
            else:
                brightness = self.config.normal_peak_brightness - time_to_arrival * self.config.arrival_brightness_decay
                brightness -= max(0, offset - 1) * 0.05
            targets[luminaire_id] = clamp(brightness, self.config.eco_brightness, self.config.normal_peak_brightness)
        return targets

    def emergency_zone_activation(self, layout: HighwayLayout, vehicle: Vehicle) -> list[str]:
        nearest_pole_id = self.detect_nearest_pole(layout, vehicle)
        current_zone = layout.pole_index(nearest_pole_id) // self.config.zone_size_poles
        if vehicle.direction == "A":
            zone_indices = [current_zone - 1, current_zone, current_zone + 1, current_zone + 2]
        else:
            zone_indices = [current_zone + 1, current_zone, current_zone - 1, current_zone - 2]
        zone_ids = []
        for index in zone_indices:
            if 0 <= index < self.config.zone_count:
                zone_ids.append(f"{vehicle.direction}-Z{index:02d}")
        return zone_ids

    def apply_smooth_fade(self, luminaire: Luminaire, dt_s: float) -> None:
        max_delta = self.config.fade_rate_per_second * dt_s
        delta = luminaire.target_brightness - luminaire.current_brightness
        if abs(delta) <= max_delta:
            luminaire.current_brightness = luminaire.target_brightness
        else:
            luminaire.current_brightness += max_delta if delta > 0 else -max_delta
        luminaire.current_brightness = clamp(luminaire.current_brightness, 0.0, 1.0)

    def fade_back_after_delay(self, target_map: dict[str, float], layout: HighwayLayout, sim_time_s: float) -> None:
        expired: list[str] = []
        for luminaire_id, until_s in self.hold_until.items():
            if until_s <= sim_time_s:
                expired.append(luminaire_id)
                continue
            luminaire = layout.luminaires.get(luminaire_id)
            if luminaire is not None:
                target_map[luminaire_id] = max(target_map.get(luminaire_id, self.config.eco_brightness), luminaire.current_brightness)
        for luminaire_id in expired:
            self.hold_until.pop(luminaire_id, None)

    def fault_fallback_control(
        self,
        layout: HighwayLayout,
        target_map: dict[str, float],
        active_faults: list[dict[str, Any]],
        sim_time_s: float,
    ) -> None:
        for fault in active_faults:
            if fault.get("kind") == "degraded_luminaire":
                luminaire_id = fault.get("luminaire_id")
                if luminaire_id in layout.luminaires:
                    luminaire = layout.luminaires[luminaire_id]
                    luminaire.fault_status = "driver_degraded"
                    luminaire.health_score = min(luminaire.health_score, 48.0)
                    luminaire.fault_count += 1
                    luminaire.fault_history.append({"time_s": sim_time_s, "fault": fault.get("message", "degraded")})
                    target_map[luminaire_id] = self.config.safe_fallback_brightness
                continue

            zone_id = fault.get("zone_id")
            if not zone_id or zone_id not in layout.zones:
                continue
            layout.zones[zone_id].mode = "fault"
            for pole_id in layout.zones[zone_id].pole_ids:
                luminaire_id = layout.luminaire_id_for(pole_id, layout.zones[zone_id].direction)
                luminaire = layout.luminaires[luminaire_id]
                luminaire.fault_status = fault.get("kind", "fault")
                if not luminaire.fault_history or luminaire.fault_history[-1].get("fault") != fault.get("message"):
                    luminaire.fault_count += 1
                    luminaire.fault_history.append({"time_s": sim_time_s, "fault": fault.get("message", "fault")})
                target_map[luminaire_id] = max(target_map.get(luminaire_id, 0), self.config.safe_fallback_brightness)

    def step(
        self,
        layout: HighwayLayout,
        vehicles: list[Vehicle],
        sim_time_s: float,
        dt_s: float,
        active_faults: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        active_faults = active_faults or []
        target_map = {
            luminaire_id: self.config.eco_brightness
            for luminaire_id in layout.luminaires
        }

        for zone in layout.zones.values():
            zone.mode = "eco"
            zone.active_vehicle_id = None

        for vehicle in vehicles:
            if vehicle.emergency_status:
                zone_ids = self.emergency_zone_activation(layout, vehicle)
                for zone_id in zone_ids:
                    zone = layout.zones[zone_id]
                    zone.mode = "emergency"
                    zone.active_vehicle_id = vehicle.vehicle_id
                    for pole_id in zone.pole_ids:
                        luminaire_id = layout.luminaire_id_for(pole_id, vehicle.direction)
                        target_map[luminaire_id] = self.config.emergency_brightness
                        self.hold_until[luminaire_id] = sim_time_s + self.config.fade_back_delay_s
                self.last_emergency_vehicle_ids.add(vehicle.vehicle_id)
                continue

            vehicle_targets = self.calculate_sequential_brightness_targets(layout, vehicle)
            for luminaire_id, brightness in vehicle_targets.items():
                target_map[luminaire_id] = max(target_map.get(luminaire_id, 0), brightness)
                self.hold_until[luminaire_id] = sim_time_s + self.config.fade_back_delay_s
                pole_id = layout.luminaires[luminaire_id].pole_id
                zone_id = layout.zone_id_for_index(vehicle.direction, layout.pole_index(pole_id))
                if layout.zones[zone_id].mode != "fault":
                    layout.zones[zone_id].mode = "normal_vehicle"
                    layout.zones[zone_id].active_vehicle_id = vehicle.vehicle_id

        self.fade_back_after_delay(target_map, layout, sim_time_s)
        self.fault_fallback_control(layout, target_map, active_faults, sim_time_s)

        for luminaire_id, luminaire in layout.luminaires.items():
            luminaire.target_brightness = clamp(target_map[luminaire_id], 0.0, 1.0)
            self.apply_smooth_fade(luminaire, dt_s)

        return {
            "active_emergency": any(vehicle.emergency_status for vehicle in vehicles),
            "lit_luminaires": sum(1 for luminaire in layout.luminaires.values() if luminaire.current_brightness > self.config.eco_brightness + 0.02),
            "fault_count": len(active_faults),
        }
