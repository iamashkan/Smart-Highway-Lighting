from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import DATA_DIR, DEFAULT_CONFIG, MqttConfig, SimulationConfig
from .energy_model import EnergyMeter
from .health_model import HealthMonitor
from .highway_layout import HighwayLayout, create_highway_layout
from .lighting_controller import LightingController
from .mqtt_bridge import MqttBridge, topic
from .passport import generate_passports, write_passports
from .rex_engine import RexEngine
from .sensor_simulator import SensorSimulator
from .vehicle_simulator import SCENARIO_FAULTS, VehicleSimulator, scenario_catalog


@dataclass
class SimulationRuntime:
    scenario_name: str = "normal_car_direction_a"
    config: SimulationConfig = field(default_factory=lambda: DEFAULT_CONFIG)
    mqtt_config: MqttConfig | None = None
    layout: HighwayLayout = field(init=False)
    vehicle_simulator: VehicleSimulator = field(init=False)
    sensor_simulator: SensorSimulator = field(default_factory=SensorSimulator)
    controller: LightingController = field(init=False)
    energy_meter: EnergyMeter = field(init=False)
    health_monitor: HealthMonitor = field(default_factory=HealthMonitor)
    rex_engine: RexEngine = field(default_factory=RexEngine)
    mqtt: MqttBridge = field(init=False)
    sim_time_s: float = 0.0
    active_faults: list[dict[str, Any]] = field(default_factory=list)
    _activated_fault_keys: set[str] = field(default_factory=set)
    last_energy: dict[str, Any] = field(default_factory=dict)
    last_control: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.layout = create_highway_layout(self.config)
        self.vehicle_simulator = VehicleSimulator.from_scenario(self.scenario_name, self.config.road_length_m)
        self.controller = LightingController(self.config)
        self.energy_meter = EnergyMeter(self.config)
        mqtt_config = self.mqtt_config or self.config.mqtt
        self.mqtt = MqttBridge(mqtt_config)
        self.mqtt.connect()

    def inject_fault(self, fault: dict[str, Any]) -> None:
        fault_key = json.dumps(fault, sort_keys=True)
        if fault_key not in self._activated_fault_keys:
            self.active_faults.append(fault)
            self._activated_fault_keys.add(fault_key)

    def _activate_scenario_faults(self) -> None:
        for fault in SCENARIO_FAULTS.get(self.scenario_name, []):
            if self.sim_time_s >= float(fault["time_s"]):
                self.inject_fault(fault)

    def step(self, dt_s: float | None = None) -> dict[str, Any]:
        dt_s = dt_s or self.config.control_tick_s
        self._activate_scenario_faults()
        vehicles = self.vehicle_simulator.step(self.sim_time_s, dt_s)
        self.sensor_simulator.step(self.layout, vehicles, self.sim_time_s, self.active_faults)
        self.last_control = self.controller.step(self.layout, vehicles, self.sim_time_s, dt_s, self.active_faults)
        self.health_monitor.step(self.layout, dt_s)
        self.rex_engine.update_layout(self.layout)
        self.last_energy = self.energy_meter.step(self.layout, dt_s)
        state = self.export_state(vehicles)
        self.publish_state(state)
        self.sim_time_s += dt_s
        return state

    def export_state(self, vehicles: list[Any] | None = None) -> dict[str, Any]:
        vehicles = vehicles or list(self.vehicle_simulator.active_vehicles.values())
        passports = generate_passports(self.layout, self.rex_engine)
        return {
            "time_s": round(self.sim_time_s, 2),
            "scenario": self.scenario_name,
            "system": {
                "active_mode": self._active_mode(),
                "emergency_active": any(vehicle.emergency_status for vehicle in vehicles),
                "active_faults": list(self.active_faults),
            },
            "vehicles": [vehicle.to_dict() for vehicle in vehicles],
            "poles": [pole.to_dict() for pole in self.layout.poles.values()],
            "luminaires": [luminaire.to_dict() for luminaire in self.layout.luminaires.values()],
            "zones": [zone.to_dict() for zone in self.layout.zones.values()],
            "sensors": [sensor.to_dict() for sensor in self.layout.sensors.values()],
            "energy": self.last_energy,
            "control": self.last_control,
            "passports": [passport.to_dict() for passport in passports],
        }

    def _active_mode(self) -> str:
        modes = {zone.mode for zone in self.layout.zones.values()}
        if "emergency" in modes:
            return "emergency"
        if "fault" in modes:
            return "fault"
        if "normal_vehicle" in modes:
            return "normal_vehicle"
        return "eco"

    def publish_state(self, state: dict[str, Any]) -> None:
        base = self.config.mqtt.base_topic
        self.mqtt.publish_json(topic(base, "system", "energy"), state.get("energy", {}))
        self.mqtt.publish_json(topic(base, "system", "emergency"), state["system"])
        for vehicle in state["vehicles"]:
            self.mqtt.publish_json(topic(base, "vehicle", vehicle["vehicle_id"], "state"), vehicle)
        for luminaire in state["luminaires"]:
            self.mqtt.publish_json(topic(base, "luminaire", luminaire["luminaire_id"], "brightness"), luminaire)
            self.mqtt.publish_json(topic(base, "luminaire", luminaire["luminaire_id"], "health"), {
                "health_score": luminaire["health_score"],
                "temperature": luminaire["driver_temperature"],
                "fault_status": luminaire["fault_status"],
                "rex_status": luminaire["rex_status"],
            })
        for zone in state["zones"]:
            self.mqtt.publish_json(topic(base, "zone", zone["zone_id"], "mode"), zone)
            self.mqtt.publish_json(topic(base, "zone", zone["zone_id"], "energy"), {
                "energy_consumption": zone["energy_consumption"],
                "energy_saved": zone["energy_saved"],
            })
        for passport in state["passports"]:
            self.mqtt.publish_json(topic(base, "passport", passport["luminaire_id"]), passport, retain=True)

    def close(self) -> None:
        self.mqtt.stop()


def run_scenario(
    scenario_name: str,
    steps: int = 90,
    config: SimulationConfig | None = None,
    output_dir: str | Path | None = None,
    mqtt_enabled: bool = False,
) -> dict[str, Any]:
    config = config or DEFAULT_CONFIG
    config.mqtt.enabled = mqtt_enabled
    runtime = SimulationRuntime(scenario_name=scenario_name, config=config)
    states: list[dict[str, Any]] = []
    try:
        for _ in range(steps):
            states.append(runtime.step())
    finally:
        runtime.close()

    final_state = states[-1] if states else runtime.export_state()
    if output_dir is not None:
        write_run_outputs(states, final_state, output_dir)
    return final_state


def write_run_outputs(states: list[dict[str, Any]], final_state: dict[str, Any], output_dir: str | Path) -> None:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "latest_state.json").write_text(json.dumps(final_state, indent=2), encoding="utf-8")

    rows: list[dict[str, Any]] = []
    for state in states:
        for luminaire in state["luminaires"]:
            rows.append(
                {
                    "time_s": state["time_s"],
                    "luminaire_id": luminaire["luminaire_id"],
                    "direction": luminaire["direction"],
                    "brightness": luminaire["current_brightness"],
                    "target_brightness": luminaire["target_brightness"],
                    "temperature_c": luminaire["driver_temperature"],
                    "fault_status": luminaire["fault_status"],
                    "health_score": luminaire["health_score"],
                    "rex_status": luminaire["rex_status"],
                }
            )
    if rows:
        with (path / "luminaire_timeseries.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def write_sample_data(output_dir: str | Path | None = None) -> None:
    output = Path(output_dir or DATA_DIR)
    output.mkdir(parents=True, exist_ok=True)
    layout = create_highway_layout(DEFAULT_CONFIG)
    layout.write_json(output / "highway_layout.json")
    (output / "vehicle_scenarios.json").write_text(json.dumps(scenario_catalog(), indent=2), encoding="utf-8")
    (output / "energy_model.json").write_text(
        json.dumps(
            {
                "max_power_watts_per_luminaire": DEFAULT_CONFIG.max_power_watts_per_luminaire,
                "eco_brightness": DEFAULT_CONFIG.eco_brightness,
                "baseline": "all luminaires at 100% brightness",
                "co2_kg_per_kwh": DEFAULT_CONFIG.co2_kg_per_kwh,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output / "luminaire_specs.json").write_text(
        json.dumps(
            {
                "target_luminaire_class": [
                    "Schreder IZYLUM / IZYLUM NEO / NEOS GEN2 style roadway luminaires",
                    "Philips/Signify Luma gen2 or RoadFocus LED style roadway luminaires",
                    "Any Zhaga-D4i or NEMA 7-pin compatible LED roadway luminaire with dimmable driver",
                ],
                "prototype_dimming": "simulated PWM and 0-10V lab interface",
                "future_dimming": "DALI/D4i via certified transceiver and protocol stack",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    run_scenario("degraded_luminaire", steps=25, output_dir=output / "sample_run")
    runtime = SimulationRuntime(scenario_name="empty_highway")
    try:
        runtime.step()
        write_passports(runtime.layout, runtime.rex_engine, output / "digital_passports_sample.json")
        sensor_rows = [sensor.to_dict() for sensor in runtime.layout.sensors.values()]
        with (output / "sensor_data.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(sensor_rows[0].keys()))
            writer.writeheader()
            writer.writerows(sensor_rows)
    finally:
        runtime.close()
    (output / "maintenance_history.json").write_text(
        json.dumps(
            [
                {
                    "luminaire_id": "P010-A",
                    "date": "2026-04-18",
                    "action": "Simulated driver inspection",
                    "result": "Thermal degradation marker used for Re-X demo",
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
