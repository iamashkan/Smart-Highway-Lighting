from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import SimulationConfig
from .highway_layout import HighwayLayout


@dataclass
class EnergyMeter:
    config: SimulationConfig
    total_actual_kwh: float = 0.0
    total_baseline_kwh: float = 0.0
    per_direction_kwh: dict[str, float] = field(default_factory=lambda: {"A": 0.0, "B": 0.0})
    per_zone_kwh: dict[str, float] = field(default_factory=dict)

    def step(self, layout: HighwayLayout, dt_s: float) -> dict[str, Any]:
        dt_h = dt_s / 3600.0
        actual = 0.0
        baseline = 0.0
        for luminaire in layout.luminaires.values():
            lum_actual = luminaire.max_power_watts * luminaire.current_brightness * dt_h / 1000.0
            lum_baseline = luminaire.max_power_watts * dt_h / 1000.0
            actual += lum_actual
            baseline += lum_baseline
            self.per_direction_kwh[luminaire.direction] += lum_actual
            pole_index = layout.pole_index(luminaire.pole_id)
            zone_id = layout.zone_id_for_index(luminaire.direction, pole_index)
            self.per_zone_kwh[zone_id] = self.per_zone_kwh.get(zone_id, 0.0) + lum_actual
            layout.zones[zone_id].energy_consumption += lum_actual
            luminaire.energy_history_kwh += lum_actual

        self.total_actual_kwh += actual
        self.total_baseline_kwh += baseline
        saved = max(0.0, self.total_baseline_kwh - self.total_actual_kwh)
        saved_pct = (saved / self.total_baseline_kwh * 100.0) if self.total_baseline_kwh else 0.0
        for zone_id, zone in layout.zones.items():
            baseline_zone = len(zone.pole_ids) * self.config.max_power_watts_per_luminaire * dt_h / 1000.0
            zone.energy_saved += max(0.0, baseline_zone - self.per_zone_kwh.get(zone_id, 0.0))
        return {
            "actual_kwh": self.total_actual_kwh,
            "baseline_kwh": self.total_baseline_kwh,
            "energy_saved_kwh": saved,
            "energy_saved_pct": saved_pct,
            "co2_saved_kg": saved * self.config.co2_kg_per_kwh,
            "per_direction_kwh": dict(self.per_direction_kwh),
            "per_zone_kwh": dict(self.per_zone_kwh),
        }
