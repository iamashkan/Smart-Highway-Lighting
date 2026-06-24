from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DEFAULT_CONFIG, SimulationConfig
from .models import Luminaire, Pole, SensorNode, Zone


@dataclass
class HighwayLayout:
    config: SimulationConfig
    poles: dict[str, Pole]
    luminaires: dict[str, Luminaire]
    zones: dict[str, Zone]
    sensors: dict[str, SensorNode]

    @property
    def road_length_m(self) -> float:
        return self.config.road_length_m

    def luminaire_id_for(self, pole_id: str, direction: str) -> str:
        pole = self.poles[pole_id]
        return pole.luminaire_A_id if direction == "A" else pole.luminaire_B_id

    def pole_index(self, pole_id: str) -> int:
        return int(pole_id.replace("P", "")) - 1

    def zone_id_for_index(self, direction: str, pole_index: int) -> str:
        return f"{direction}-Z{pole_index // self.config.zone_size_poles:02d}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "poles": [pole.to_dict() for pole in self.poles.values()],
            "luminaires": [lum.to_dict() for lum in self.luminaires.values()],
            "zones": [zone.to_dict() for zone in self.zones.values()],
            "sensors": [sensor.to_dict() for sensor in self.sensors.values()],
        }

    def write_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


def create_highway_layout(config: SimulationConfig | None = None) -> HighwayLayout:
    config = config or DEFAULT_CONFIG
    poles: dict[str, Pole] = {}
    luminaires: dict[str, Luminaire] = {}
    zones: dict[str, Zone] = {}
    sensors: dict[str, SensorNode] = {}

    for direction in ("A", "B"):
        for zone_index in range(config.zone_count):
            start = zone_index * config.zone_size_poles
            end = min(config.num_poles, start + config.zone_size_poles)
            zone_id = f"{direction}-Z{zone_index:02d}"
            zones[zone_id] = Zone(
                zone_id=zone_id,
                direction=direction,  # type: ignore[arg-type]
                pole_ids=[f"P{i + 1:03d}" for i in range(start, end)],
                mode="eco",
                active_vehicle_id=None,
                energy_consumption=0.0,
                energy_saved=0.0,
            )

    for i in range(config.num_poles):
        pole_id = f"P{i + 1:03d}"
        zone_id = f"Z{i // config.zone_size_poles:02d}"
        luminaire_a_id = f"{pole_id}-A"
        luminaire_b_id = f"{pole_id}-B"
        poles[pole_id] = Pole(
            pole_id=pole_id,
            position_x=i * config.pole_spacing_m,
            position_y=0.0,
            position_z=8.0,
            zone_id=zone_id,
            luminaire_A_id=luminaire_a_id,
            luminaire_B_id=luminaire_b_id,
        )
        for direction, luminaire_id in (("A", luminaire_a_id), ("B", luminaire_b_id)):
            luminaires[luminaire_id] = Luminaire(
                luminaire_id=luminaire_id,
                pole_id=pole_id,
                direction=direction,  # type: ignore[arg-type]
                current_brightness=config.eco_brightness,
                target_brightness=config.eco_brightness,
                max_power_watts=config.max_power_watts_per_luminaire,
                dimming_protocol="simulated_pwm_0_10v",
                health_score=98.0,
                driver_temperature=35.0,
                current_consumption=0.0,
                operating_hours=0.0,
                fault_status="ok",
                digital_passport_id=f"DPP-{luminaire_id}",
                rex_status="Reuse",
            )
        sensors[f"S-{pole_id}"] = SensorNode(
            node_id=f"S-{pole_id}",
            pole_id=pole_id,
            zone_id=zone_id,
            radar_status="ok",
            camera_status="mock_ready",
            ambient_light_lux=12.0,
            temperature=32.0,
            current_sensor_value=0.0,
            communication_status="ok",
        )

    return HighwayLayout(config=config, poles=poles, luminaires=luminaires, zones=zones, sensors=sensors)
