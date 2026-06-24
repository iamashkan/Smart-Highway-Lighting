from __future__ import annotations

import random
from dataclasses import dataclass, field

from .highway_layout import HighwayLayout
from .models import clamp


@dataclass
class HealthMonitor:
    seed: int = 7
    rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def step(self, layout: HighwayLayout, dt_s: float) -> None:
        dt_h = dt_s / 3600.0
        for luminaire in layout.luminaires.values():
            sensor = layout.sensors.get(f"S-{luminaire.pole_id}")
            ambient = sensor.temperature if sensor else 32.0
            thermal_noise = self.rng.uniform(-0.8, 0.8)
            temperature = ambient + 18.0 * luminaire.current_brightness + thermal_noise
            luminaire.driver_temperature = round(temperature, 2)
            luminaire.average_driver_temperature = round(
                luminaire.average_driver_temperature * 0.98 + temperature * 0.02,
                2,
            )
            current_a = (luminaire.max_power_watts * luminaire.current_brightness) / 48.0
            luminaire.current_consumption = round(current_a, 3)
            luminaire.operating_hours += dt_h

            thermal_penalty = max(0.0, temperature - 70.0) * 0.002
            brightness_penalty = luminaire.current_brightness * 0.00002
            fault_penalty = 0.00035 if luminaire.fault_status != "ok" else 0.0
            luminaire.health_score = clamp(
                luminaire.health_score - thermal_penalty - brightness_penalty - fault_penalty,
                0.0,
                100.0,
            )

            if temperature > 82.0 and luminaire.fault_status == "ok":
                luminaire.fault_status = "over_temperature"
                luminaire.fault_count += 1
                luminaire.fault_history.append({"fault": "over_temperature", "temperature_c": temperature})
