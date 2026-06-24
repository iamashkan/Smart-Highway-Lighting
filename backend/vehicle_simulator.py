from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Vehicle


EMERGENCY_TYPES = {"ambulance", "police_car", "fire_truck"}


@dataclass
class VehicleSpawn:
    spawn_time_s: float
    vehicle_id: str
    type: str
    direction: str
    lane_id: str
    start_position_m: float | None
    speed_mps: float


SCENARIOS: dict[str, list[VehicleSpawn]] = {
    "empty_highway": [],
    "normal_car_direction_a": [
        VehicleSpawn(0, "CAR-A-01", "normal_car", "A", "A2", -50.0, 24.0),
    ],
    "normal_car_direction_b": [
        VehicleSpawn(0, "CAR-B-01", "normal_car", "B", "B2", None, 24.0),
    ],
    "two_cars_opposite": [
        VehicleSpawn(0, "CAR-A-01", "normal_car", "A", "A1", -30.0, 22.0),
        VehicleSpawn(3, "CAR-B-01", "normal_car", "B", "B3", None, 26.0),
    ],
    "emergency_ambulance_direction_a": [
        VehicleSpawn(0, "AMB-A-01", "ambulance", "A", "A2", -70.0, 31.0),
    ],
    "police_fire_direction_b": [
        VehicleSpawn(0, "POL-B-01", "police_car", "B", "B2", None, 30.0),
        VehicleSpawn(12, "FIRE-B-02", "fire_truck", "B", "B1", None, 25.0),
    ],
    "sensor_fault": [
        VehicleSpawn(0, "CAR-A-FAULT", "normal_car", "A", "A2", -40.0, 22.0),
    ],
    "communication_loss": [
        VehicleSpawn(0, "CAR-B-COMM", "normal_car", "B", "B2", None, 24.0),
    ],
    "degraded_luminaire": [
        VehicleSpawn(0, "CAR-A-DEG", "normal_car", "A", "A2", -40.0, 23.0),
    ],
}


SCENARIO_FAULTS: dict[str, list[dict[str, Any]]] = {
    "sensor_fault": [
        {
            "time_s": 6,
            "kind": "sensor_fault",
            "zone_id": "A-Z01",
            "message": "Radar timeout on zone A-Z01",
        }
    ],
    "communication_loss": [
        {
            "time_s": 8,
            "kind": "communication_loss",
            "zone_id": "B-Z02",
            "message": "MQTT heartbeat lost for board group B-Z02",
        }
    ],
    "degraded_luminaire": [
        {
            "time_s": 2,
            "kind": "degraded_luminaire",
            "luminaire_id": "P010-A",
            "message": "Simulated driver thermal degradation",
        }
    ],
}


@dataclass
class VehicleSimulator:
    scenario_name: str
    road_length_m: float
    spawns: list[VehicleSpawn] = field(default_factory=list)
    active_vehicles: dict[str, Vehicle] = field(default_factory=dict)
    spawned_ids: set[str] = field(default_factory=set)

    @classmethod
    def from_scenario(cls, scenario_name: str, road_length_m: float) -> "VehicleSimulator":
        if scenario_name not in SCENARIOS:
            raise ValueError(f"Unknown scenario '{scenario_name}'. Available: {', '.join(sorted(SCENARIOS))}")
        return cls(scenario_name=scenario_name, road_length_m=road_length_m, spawns=SCENARIOS[scenario_name])

    def step(self, sim_time_s: float, dt_s: float) -> list[Vehicle]:
        for spawn in self.spawns:
            if spawn.vehicle_id in self.spawned_ids or sim_time_s < spawn.spawn_time_s:
                continue
            start = spawn.start_position_m
            if start is None:
                start = self.road_length_m + 50.0 if spawn.direction == "B" else -50.0
            self.active_vehicles[spawn.vehicle_id] = Vehicle(
                vehicle_id=spawn.vehicle_id,
                type=spawn.type,  # type: ignore[arg-type]
                direction=spawn.direction,  # type: ignore[arg-type]
                lane_id=spawn.lane_id,
                position_along_road=start,
                speed_mps=spawn.speed_mps,
                detection_status="simulated",
                emergency_status=spawn.type in EMERGENCY_TYPES,
            )
            self.spawned_ids.add(spawn.vehicle_id)

        for vehicle in self.active_vehicles.values():
            delta = vehicle.speed_mps * dt_s
            if vehicle.direction == "A":
                vehicle.position_along_road += delta
            else:
                vehicle.position_along_road -= delta

        margin = 120.0
        self.active_vehicles = {
            vehicle_id: vehicle
            for vehicle_id, vehicle in self.active_vehicles.items()
            if -margin <= vehicle.position_along_road <= self.road_length_m + margin
        }
        return list(self.active_vehicles.values())


def scenario_catalog() -> dict[str, Any]:
    return {
        name: [
            {
                "spawn_time_s": spawn.spawn_time_s,
                "vehicle_id": spawn.vehicle_id,
                "type": spawn.type,
                "direction": spawn.direction,
                "lane_id": spawn.lane_id,
                "start_position_m": spawn.start_position_m,
                "speed_mps": spawn.speed_mps,
            }
            for spawn in spawns
        ]
        for name, spawns in SCENARIOS.items()
    }
