#!/usr/bin/env python3
"""Run the simulation-only validation suite for the ReLight-X prototype."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "data" / "runs" / "validation"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str
    metrics: dict[str, Any] = field(default_factory=dict)


def run_command(name: str, command: list[str], timeout_s: int = 180) -> CheckResult:
    started = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            name=name,
            passed=False,
            details=f"Timed out after {timeout_s}s: {' '.join(command)}",
            metrics={"duration_s": round(time.time() - started, 2), "output": (exc.stdout or "")[-3000:]},
        )

    return CheckResult(
        name=name,
        passed=result.returncode == 0,
        details=result.stdout[-4000:] if result.stdout else "No output",
        metrics={
            "command": " ".join(command),
            "returncode": result.returncode,
            "duration_s": round(time.time() - started, 2),
        },
    )


def run_backend_scenario(name: str, steps: int = 70) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from backend.config import SimulationConfig
    from backend.scenario_runner import SimulationRuntime

    runtime = SimulationRuntime(scenario_name=name, config=SimulationConfig())
    states: list[dict[str, Any]] = []
    try:
        for _ in range(steps):
            states.append(runtime.step())
    finally:
        runtime.close()
    return states, states[-1]


def lum_values(states: list[dict[str, Any]], direction: str, field: str = "current_brightness") -> list[float]:
    values: list[float] = []
    for state in states:
        values.extend(float(lum[field]) for lum in state["luminaires"] if lum["direction"] == direction)
    return values


def all_modes(states: list[dict[str, Any]]) -> set[str]:
    modes = {state["system"]["active_mode"] for state in states}
    for state in states:
        modes.update(zone["mode"] for zone in state["zones"])
    return modes


def any_fault_kind(states: list[dict[str, Any]], kind: str) -> bool:
    for state in states:
        for fault in state["system"]["active_faults"]:
            if fault.get("kind") == kind:
                return True
    return False


def evaluate_scenario(name: str, states: list[dict[str, Any]], final: dict[str, Any]) -> CheckResult:
    max_a = max(lum_values(states, "A"), default=0.0)
    max_b = max(lum_values(states, "B"), default=0.0)
    max_target_a = max(lum_values(states, "A", "target_brightness"), default=0.0)
    max_target_b = max(lum_values(states, "B", "target_brightness"), default=0.0)
    modes = all_modes(states)
    energy_saved_pct = float(final.get("energy", {}).get("energy_saved_pct", 0.0))
    metrics = {
        "max_current_a": round(max_a, 3),
        "max_current_b": round(max_b, 3),
        "max_target_a": round(max_target_a, 3),
        "max_target_b": round(max_target_b, 3),
        "energy_saved_pct": round(energy_saved_pct, 2),
        "modes": sorted(modes),
        "final_fault_count": len(final["system"]["active_faults"]),
    }

    if name == "empty_highway":
        passed = max(max_a, max_b) <= 0.31 and modes <= {"eco"}
        details = "No traffic keeps both directions at 30% eco brightness."
    elif name == "normal_car_direction_a":
        passed = max_a >= 0.70 and max_b <= 0.31 and "normal_vehicle" in modes
        details = "Direction A vehicle creates a directional lighting wave without lighting direction B."
    elif name == "normal_car_direction_b":
        passed = max_b >= 0.70 and max_a <= 0.31 and "normal_vehicle" in modes
        details = "Direction B vehicle creates a directional lighting wave without lighting direction A."
    elif name == "two_cars_opposite":
        passed = max_a >= 0.70 and max_b >= 0.70 and "normal_vehicle" in modes
        details = "Opposite-direction vehicles independently activate both directional lighting waves."
    elif name == "emergency_ambulance_direction_a":
        emergency_zone_count = max(
            sum(1 for zone in state["zones"] if zone["mode"] == "emergency" and zone["direction"] == "A")
            for state in states
        )
        metrics["max_emergency_zones_a"] = emergency_zone_count
        passed = max_target_a >= 1.0 and emergency_zone_count >= 2 and "emergency" in modes
        details = "Ambulance in direction A forces multiple safety zones to 100% target brightness."
    elif name == "police_fire_direction_b":
        emergency_zone_count = max(
            sum(1 for zone in state["zones"] if zone["mode"] == "emergency" and zone["direction"] == "B")
            for state in states
        )
        metrics["max_emergency_zones_b"] = emergency_zone_count
        passed = max_target_b >= 1.0 and emergency_zone_count >= 2 and "emergency" in modes
        details = "Police/fire scenario in direction B forces multiple safety zones to 100% target brightness."
    elif name == "sensor_fault":
        fallback_seen = any(
            lum["fault_status"] == "sensor_fault" and lum["target_brightness"] >= 0.70
            for state in states
            for lum in state["luminaires"]
        )
        passed = any_fault_kind(states, "sensor_fault") and fallback_seen and "fault" in modes
        details = "Sensor fault is injected, marked in zone state, and forces safe fallback brightness."
    elif name == "communication_loss":
        fallback_seen = any(
            lum["fault_status"] == "communication_loss" and lum["target_brightness"] >= 0.70
            for state in states
            for lum in state["luminaires"]
        )
        passed = any_fault_kind(states, "communication_loss") and fallback_seen and "fault" in modes
        details = "Communication loss is injected and forces the affected board group to safe fallback."
    elif name == "degraded_luminaire":
        degraded_passport = next(
            passport for passport in final["passports"] if passport["luminaire_id"] == "P010-A"
        )
        p010_states = [
            lum
            for state in states
            for lum in state["luminaires"]
            if lum["luminaire_id"] == "P010-A"
        ]
        fallback_seen = any(lum["target_brightness"] >= 0.70 for lum in p010_states)
        metrics["p010_min_health_score"] = min(lum["health_score"] for lum in p010_states)
        metrics["p010_rex_decision"] = degraded_passport["rex_decision"]
        passed = (
            any(lum["fault_status"] == "driver_degraded" for lum in p010_states)
            and fallback_seen
            and degraded_passport["rex_decision"] in {"Repair", "Remanufacture"}
        )
        details = "Degraded luminaire triggers safe fallback, health reduction, and Re-X passport action."
    else:
        passed = energy_saved_pct > 0.0
        details = "Scenario executes and records positive simulated energy saving."

    if energy_saved_pct <= 0.0:
        passed = False
        details += " Energy saving metric was not positive."

    return CheckResult(name=f"Backend scenario: {name}", passed=passed, details=details, metrics=metrics)


def validate_backend_scenarios() -> CheckResult:
    from backend.vehicle_simulator import SCENARIOS

    scenario_results: list[dict[str, Any]] = []
    passed = True
    for scenario in SCENARIOS:
        states, final = run_backend_scenario(scenario)
        scenario_check = evaluate_scenario(scenario, states, final)
        scenario_results.append(
            {
                "name": scenario,
                "passed": scenario_check.passed,
                "details": scenario_check.details,
                "metrics": scenario_check.metrics,
            }
        )
        passed = passed and scenario_check.passed

    return CheckResult(
        name="Backend scenario validation",
        passed=passed,
        details="Validated all backend traffic, emergency, energy, and fault scenarios.",
        metrics={"scenarios": scenario_results},
    )


def validate_wokwi_board_files() -> CheckResult:
    diagram_path = ROOT / "board_simulation_wokwi" / "diagram.json"
    wokwi_path = ROOT / "board_simulation_wokwi" / "wokwi.toml"
    platformio_path = ROOT / "board_simulation_wokwi" / "platformio.ini"
    diagram = json.loads(diagram_path.read_text(encoding="utf-8"))
    parts = {part["id"]: part for part in diagram["parts"]}
    connections = {tuple(connection[:2]) for connection in diagram["connections"]}
    required_parts = {
        "stm32",
        "ledA",
        "ledB",
        "faultLed",
        "busLed",
        "rs485Tx",
        "canTx",
        "logic",
        "ldr",
        "radarPot",
        "ntc",
        "linePot",
        "pir",
        "range",
        "faultBtn",
        "testBtn",
        "vehABtn",
        "vehBBtn",
        "emergencyBtn",
        "busFaultBtn",
    }
    required_connections = {
        ("stm32:PB6", "rA:1"),
        ("rA:2", "ledA:A"),
        ("stm32:PB7", "rB:1"),
        ("rB:2", "ledB:A"),
        ("stm32:PB14", "logic:D2"),
        ("stm32:PB15", "logic:D3"),
        ("stm32:PA11", "logic:D4"),
        ("stm32:PA0", "ldr:AO"),
        ("stm32:PA1", "radarPot:SIG"),
        ("stm32:PA2", "ntc:OUT"),
        ("stm32:PA3", "linePot:SIG"),
    }

    missing_parts = sorted(required_parts - set(parts))
    missing_connections = sorted(
        f"{source} -> {target}" for source, target in required_connections if (source, target) not in connections and (target, source) not in connections
    )
    text_checks = {
        "wokwi_bluepill_firmware_path": ".pio/build/bluepill_f103c8/firmware.bin" in wokwi_path.read_text(encoding="utf-8"),
        "platformio_bluepill_env": "[env:bluepill_f103c8]" in platformio_path.read_text(encoding="utf-8"),
        "stm32_board_part": parts.get("stm32", {}).get("type") == "board-stm32-bluepill",
    }
    passed = not missing_parts and not missing_connections and all(text_checks.values())

    return CheckResult(
        name="Wokwi STM32 board wiring validation",
        passed=passed,
        details="Checked STM32 board, connected luminaires, sensors, RS485/CAN indicators, logic analyzer, and build paths.",
        metrics={
            "part_count": len(diagram["parts"]),
            "connection_count": len(diagram["connections"]),
            "missing_parts": missing_parts,
            "missing_connections": missing_connections,
            "text_checks": text_checks,
        },
    )


def validate_wokwi_firmware(build: bool) -> CheckResult:
    if build:
        build_result = run_command(
            "Build Wokwi STM32 firmware",
            [sys.executable, "board_simulation_wokwi/tools/run_platformio.py", "run"],
            timeout_s=300,
        )
        if not build_result.passed:
            return build_result

    firmware = ROOT / "board_simulation_wokwi" / ".pio" / "build" / "bluepill_f103c8" / "firmware.bin"
    elf = ROOT / "board_simulation_wokwi" / ".pio" / "build" / "bluepill_f103c8" / "firmware.elf"
    passed = firmware.exists() and elf.exists() and firmware.stat().st_size > 0 and elf.stat().st_size > 0
    return CheckResult(
        name="Wokwi firmware artifact validation",
        passed=passed,
        details="Checked compiled STM32 firmware artifacts used by Wokwi VS Code.",
        metrics={
            "firmware_bin": str(firmware),
            "firmware_bin_bytes": firmware.stat().st_size if firmware.exists() else 0,
            "firmware_elf": str(elf),
            "firmware_elf_bytes": elf.stat().st_size if elf.exists() else 0,
            "build_executed": build,
        },
    )


def validate_five_node_network() -> CheckResult:
    from board_design.simulation.five_node_network_sim import simulate

    result = simulate(steps=32, dt_s=1.0)
    records = result["records"]
    max_brightness = max(node["target_brightness"] for record in records for node in record["nodes"])
    all_bus_ok = all(node["rs485_ok"] and node["can_ok"] for record in records for node in record["nodes"])
    any_vehicle_detection = any(node["vehicle_detected"] for record in records for node in record["nodes"])
    online_counts = [record["gateway"]["wireless_nodes_online"] for record in records]
    passed = result["node_count"] == 5 and all_bus_ok and any_vehicle_detection and max_brightness >= 0.86 and min(online_counts) >= 4
    return CheckResult(
        name="Five-node STM32/RS485/CAN board network validation",
        passed=passed,
        details="Validated five simulated pole boards, wireless gateway status, RS485/CAN health, vehicle detection, and brightness wave.",
        metrics={
            "node_count": result["node_count"],
            "record_count": len(records),
            "max_target_brightness": max_brightness,
            "min_wireless_nodes_online": min(online_counts),
            "final_active_faults": records[-1]["gateway"]["active_faults"],
        },
    )


def validate_ai_placeholder() -> CheckResult:
    from backend.ai_vehicle_classifier import classify_vehicle

    vehicle_type, confidence = classify_vehicle({"mock_vehicle_type": "ambulance", "confidence": 0.97})
    fallback_type, fallback_confidence = classify_vehicle({})
    passed = vehicle_type == "ambulance" and confidence >= 0.95 and fallback_type == "normal_car"
    return CheckResult(
        name="AI interface validation",
        passed=passed,
        details="Checked the replaceable YOLO-style classifier interface used by the simulation.",
        metrics={
            "mock_classification": {"type": vehicle_type, "confidence": confidence},
            "fallback_classification": {"type": fallback_type, "confidence": fallback_confidence},
        },
    )


def validate_visualization_assets() -> CheckResult:
    required_files = [
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Editor" / "ReLightXUnity6ProjectBuilder.cs",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "TrafficSimulationManager.cs",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "DigitalTwinCameraRig.cs",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "DigitalTwinHUD.cs",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "LuminaireController.cs",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "DigitalTwinMaterialUtility.cs",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "ImportedAssets" / "KenneyCarKit" / "Models" / "FBX format" / "police.fbx",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "ImportedAssets" / "KenneyCarKit" / "Models" / "FBX format" / "ambulance.fbx",
        ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "ImportedAssets" / "KenneyCarKit" / "Models" / "FBX format" / "firetruck.fbx",
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    builder_text = required_files[0].read_text(encoding="utf-8") if required_files[0].exists() else ""
    traffic_text = required_files[1].read_text(encoding="utf-8") if required_files[1].exists() else ""
    highway_text = (ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "HighwaySceneManager.cs").read_text(encoding="utf-8")
    hud_text = (ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "DigitalTwinHUD.cs").read_text(encoding="utf-8")
    luminaire_text = required_files[4].read_text(encoding="utf-8") if required_files[4].exists() else ""
    vehicle_text = (ROOT / "unity_projects" / "ReLightX_Unity6" / "Assets" / "ReLightX" / "Scripts" / "VehicleController.cs").read_text(encoding="utf-8")
    material_text = required_files[5].read_text(encoding="utf-8") if required_files[5].exists() else ""
    feature_checks = {
        "clickable_light_panel": "Selected Light Card" in builder_text,
        "selected_vehicle_speed_buttons": "Car +10" in builder_text and "Car -10" in builder_text,
        "selected_vehicle_views": "First Top" in builder_text and "Third" in builder_text and "Side" in builder_text,
        "no_vehicle_selection_ring": "selected vehicle ring" not in vehicle_text,
        "vehicle_body_material_1_1": "VehicleBodyMetallic = 1.0f" in material_text and "TuneVehicleBodyHierarchy" in traffic_text,
        "directional_light_wave": "sensorPoleIndex" in highway_text and "offset <= 2" in highway_text and "SpeedBasedPreviewBrightness" in highway_text,
        "simple_luminaire_visuals": "Luminaire Housing" in highway_text and "Warm LED Diffuser" not in highway_text and "clean rebuild" not in highway_text,
        "single_spot_lighting": "Roadway Beam" in highway_text and "sourceGlowLight" not in luminaire_text and "roadGlowRenderer" not in luminaire_text,
        "no_extra_light_pool_objects": "CreateRoadGlowPatch" not in highway_text and "road light pool" not in highway_text,
        "wet_asphalt_metallic_09": "Night wet asphalt.mat" in builder_text and "0.90f, 0.10f" in builder_text,
        "light_intensity_30_to_100_mapping": "Mathf.InverseLerp(0.30f, 1.0f, brightness)" in luminaire_text and "Mathf.Lerp(2f, 40f, intensityLevel)" in luminaire_text,
        "fixed_spotlight_shape": "roadwayLight.range = 50f" in luminaire_text and "roadwayLight.spotAngle = 80f" in luminaire_text and "direction == \"A\" ? 97f : 82f" in highway_text,
        "segmented_road_for_urp_lights": "CreateSegmentedRoadSurface" in highway_text and "Asphalt Segment" in highway_text,
        "traffic_lights_no_hold_map": "_lightHoldUntil" not in highway_text and "hold/fade active" not in highway_text,
        "force_pixel_spotlights": "LightRenderMode.ForcePixel" in highway_text and "LightShadows.None" in highway_text,
        "unselected_vehicle_detection": "ApplyAdaptiveLightingFromVehicles(_vehicles)" in traffic_text and "cameraRig.selectedVehicle" not in highway_text,
        "full_direction_emergency": "AddDirectionTarget(vehicle.direction, emergencyBrightness" in highway_text,
        "energy_saved_hud": "savedEnergyKwh" in hud_text,
        "multi_vehicle_details": "Detected cars" in hud_text,
    }
    passed = not missing and all(feature_checks.values())
    return CheckResult(
        name="Unity digital twin asset validation",
        passed=passed,
        details="Checked Unity 6 generator, traffic/camera/HUD/light scripts, clickable-light details, speed buttons, energy HUD, and imported emergency vehicle assets.",
        metrics={"missing_files": missing, "checked_files": len(required_files), "feature_checks": feature_checks},
    )


def write_markdown_report(output_dir: Path, results: list[CheckResult]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    passed_count = sum(1 for result in results if result.passed)
    report_path = output_dir / "validation_summary.md"
    lines = [
        "# ReLight-X Simulation Validation Summary",
        "",
        f"Generated by `tools/run_validation.py`.",
        "",
        f"Overall result: {passed_count}/{len(results)} checks passed.",
        "",
        "## Validation Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        detail = result.details.replace("\n", " ")[:220]
        lines.append(f"| {result.name} | {status} | {detail} |")

    scenario_result = next((result for result in results if result.name == "Backend scenario validation"), None)
    if scenario_result:
        lines.extend(["", "## Scenario Metrics", "", "| Scenario | Result | Energy saved | Max A | Max B | Modes |", "| --- | --- | ---: | ---: | ---: | --- |"])
        for scenario in scenario_result.metrics.get("scenarios", []):
            metrics = scenario["metrics"]
            lines.append(
                "| "
                f"{scenario['name']} | "
                f"{'PASS' if scenario['passed'] else 'FAIL'} | "
                f"{metrics.get('energy_saved_pct', 0):.2f}% | "
                f"{metrics.get('max_current_a', 0):.2f} | "
                f"{metrics.get('max_current_b', 0):.2f} | "
                f"{', '.join(metrics.get('modes', []))} |"
            )

    lines.extend(
        [
            "",
            "## What This Validation Covers",
            "",
            "This validation package demonstrates repeatability without physical devices: the backend scenarios, STM32 Wokwi board model, five-node network model, AI interface, and Unity visualization assets can all be checked from source code and generated artifacts.",
            "",
            "Use this file together with `validation_report.json`, the Streamlit dashboard, Wokwi simulation, and Unity digital twin as the evidence set for the demo.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ReLight-X simulation validation checks.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skip-wokwi-build", action="store_true", help="Do not rebuild the STM32 Wokwi firmware.")
    args = parser.parse_args()

    output_dir = args.output_dir
    results: list[CheckResult] = []
    results.append(run_command("Python unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]))
    results.append(validate_backend_scenarios())
    results.append(validate_wokwi_board_files())
    results.append(validate_wokwi_firmware(build=not args.skip_wokwi_build))
    results.append(validate_five_node_network())
    results.append(validate_ai_placeholder())
    results.append(validate_visualization_assets())

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "project": "ReLight-X",
        "purpose": "Simulation-only validation evidence",
        "passed": all(result.passed for result in results),
        "checks": [
            {
                "name": result.name,
                "passed": result.passed,
                "details": result.details,
                "metrics": result.metrics,
            }
            for result in results
        ],
    }
    json_path = output_dir / "validation_report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = write_markdown_report(output_dir, results)

    for result in results:
        print(f"[{'PASS' if result.passed else 'FAIL'}] {result.name}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
