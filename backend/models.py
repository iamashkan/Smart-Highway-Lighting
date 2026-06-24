from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Direction = Literal["A", "B"]
VehicleType = Literal["normal_car", "ambulance", "police_car", "fire_truck"]
ZoneMode = Literal["eco", "normal_vehicle", "emergency", "fault", "maintenance"]
RexDecision = Literal["Reuse", "Repair", "Remanufacture", "Recycle"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class Pole:
    pole_id: str
    position_x: float
    position_y: float
    position_z: float
    zone_id: str
    luminaire_A_id: str
    luminaire_B_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Luminaire:
    luminaire_id: str
    pole_id: str
    direction: Direction
    current_brightness: float
    target_brightness: float
    max_power_watts: float
    dimming_protocol: str
    health_score: float
    driver_temperature: float
    current_consumption: float
    operating_hours: float
    fault_status: str
    digital_passport_id: str
    rex_status: RexDecision
    average_driver_temperature: float = 35.0
    fault_count: int = 0
    maintenance_history: list[dict[str, Any]] = field(default_factory=list)
    fault_history: list[dict[str, Any]] = field(default_factory=list)
    energy_history_kwh: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["current_brightness_pct"] = round(self.current_brightness * 100, 1)
        data["target_brightness_pct"] = round(self.target_brightness * 100, 1)
        return data


@dataclass
class Zone:
    zone_id: str
    direction: Direction
    pole_ids: list[str]
    mode: ZoneMode
    active_vehicle_id: str | None
    energy_consumption: float
    energy_saved: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Vehicle:
    vehicle_id: str
    type: VehicleType
    direction: Direction
    lane_id: str
    position_along_road: float
    speed_mps: float
    detection_status: str
    emergency_status: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SensorNode:
    node_id: str
    pole_id: str | None
    zone_id: str | None
    radar_status: str
    camera_status: str
    ambient_light_lux: float
    temperature: float
    current_sensor_value: float
    communication_status: str
    latest_detection: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DigitalPassport:
    passport_id: str
    luminaire_id: str
    manufacturer_placeholder: str
    model_placeholder: str
    installation_date: str
    driver_type: str
    dimming_protocol: str
    material_composition_placeholder: dict[str, str]
    maintenance_history: list[dict[str, Any]]
    operating_hours: float
    energy_history: dict[str, float]
    fault_history: list[dict[str, Any]]
    health_score: float
    remaining_useful_life_estimate: float
    rex_decision: RexDecision

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BoardTelemetry:
    board_id: str
    luminaire_id: str
    brightness: float
    pwm_duty_cycle: float
    simulated_output_voltage: float
    driver_temperature: float
    current_ma: float
    communication_health: str
    fault_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
