from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class SpeedThresholds:
    low_mps: float = 15.0
    medium_mps: float = 28.0
    low_ahead: int = 2
    medium_ahead: int = 4
    high_ahead: int = 6


@dataclass
class MqttConfig:
    host: str = "localhost"
    port: int = 1883
    keepalive: int = 30
    base_topic: str = "relightx"
    client_id: str = "relightx-backend"
    enabled: bool = False


@dataclass
class SimulationConfig:
    num_poles: int = 32
    pole_spacing_m: float = 40.0
    zone_size_poles: int = 8
    lane_width_m: float = 3.7
    lanes_per_direction: int = 3
    eco_brightness: float = 0.30
    emergency_brightness: float = 1.0
    normal_peak_brightness: float = 1.0
    safe_fallback_brightness: float = 0.70
    fade_rate_per_second: float = 0.18
    fade_back_delay_s: float = 8.0
    control_tick_s: float = 1.0
    max_power_watts_per_luminaire: float = 160.0
    co2_kg_per_kwh: float = 0.404
    detection_range_m: float = 90.0
    arrival_brightness_decay: float = 0.045
    speed_thresholds: SpeedThresholds = field(default_factory=SpeedThresholds)
    mqtt: MqttConfig = field(default_factory=MqttConfig)

    @property
    def road_length_m(self) -> float:
        return max(0, (self.num_poles - 1) * self.pole_spacing_m)

    @property
    def zone_count(self) -> int:
        return (self.num_poles + self.zone_size_poles - 1) // self.zone_size_poles

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_CONFIG = SimulationConfig()
