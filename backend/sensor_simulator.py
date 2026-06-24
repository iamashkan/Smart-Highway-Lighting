from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

from .highway_layout import HighwayLayout
from .models import SensorNode, Vehicle


@dataclass
class SensorSimulator:
    seed: int = 42
    rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def step(
        self,
        layout: HighwayLayout,
        vehicles: list[Vehicle],
        sim_time_s: float,
        active_faults: list[dict[str, Any]],
    ) -> dict[str, SensorNode]:
        fault_zone_ids = {fault.get("zone_id", "").replace("A-", "").replace("B-", "") for fault in active_faults}
        for sensor in layout.sensors.values():
            pole = layout.poles[sensor.pole_id] if sensor.pole_id else None
            sensor.ambient_light_lux = 10.0 + 2.0 * math.sin(sim_time_s / 40.0)
            sensor.temperature = 31.0 + 1.5 * math.sin(sim_time_s / 55.0)
            sensor.current_sensor_value = 0.0
            sensor.latest_detection = {}
            sensor.radar_status = "ok"
            sensor.communication_status = "ok"

            if sensor.zone_id in fault_zone_ids:
                sensor.radar_status = "fault"
                sensor.communication_status = "degraded"
                continue

            if pole is None:
                continue

            nearby = [
                vehicle
                for vehicle in vehicles
                if abs(vehicle.position_along_road - pole.position_x) <= layout.config.detection_range_m
            ]
            if nearby:
                nearest = min(nearby, key=lambda vehicle: abs(vehicle.position_along_road - pole.position_x))
                distance = nearest.position_along_road - pole.position_x
                sensor.latest_detection = {
                    "vehicle_id": nearest.vehicle_id,
                    "vehicle_type": nearest.type,
                    "distance_m": round(distance, 2),
                    "speed_mps": nearest.speed_mps,
                    "direction": nearest.direction,
                    "confidence": round(0.82 + self.rng.random() * 0.14, 2),
                }
        return layout.sensors
