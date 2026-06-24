from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "runs" / "five_node_board_network.json"


@dataclass
class BoardNodeState:
    node_id: str
    pole_id: str
    luminaire_id: str
    x_m: float
    vehicle_detected: bool
    vehicle_distance_m: float
    vehicle_speed_mps: float
    ambient_lux: float
    driver_temp_c: float
    enclosure_temp_c: float
    current_ma: float
    target_brightness: float
    wireless_rssi_dbm: int
    rs485_ok: bool
    can_ok: bool
    fault: str
    event: str


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def brightness_for_distance(distance_m: float, speed_mps: float) -> float:
    if distance_m < 12:
        return 1.0
    if distance_m < 34:
        return 0.86
    if distance_m < 65:
        return 0.62 + clamp(speed_mps / 30.0, 0.0, 0.22)
    return 0.30


def node_event(distance_m: float, vehicle_x: float, node_x: float, brightness: float) -> str:
    if distance_m < 12:
        return "vehicle under pole, peak brightness"
    if vehicle_x < node_x and distance_m < 65:
        return "vehicle approaching, pre-light active"
    if vehicle_x > node_x and brightness > 0.30:
        return "vehicle passed, hold then fade to eco"
    return "eco watch"


def simulate(steps: int = 24, dt_s: float = 1.0) -> dict:
    node_spacing_m = 34.0
    node_positions = [index * node_spacing_m for index in range(5)]
    vehicle_speed_mps = 11.5
    initial_vehicle_x = -40.0
    ambient_lux = 2.8
    records = []

    for step in range(steps):
        t_s = step * dt_s
        vehicle_x = initial_vehicle_x + vehicle_speed_mps * t_s
        step_nodes: list[BoardNodeState] = []

        for index, node_x in enumerate(node_positions):
            distance_m = abs(vehicle_x - node_x)
            detected = distance_m <= 70.0
            brightness = brightness_for_distance(distance_m, vehicle_speed_mps) if detected else 0.30
            thermal_rise = brightness * 18.0 + max(0.0, 14.0 - distance_m) * 0.08
            current_ma = 95.0 + brightness * 850.0
            rssi = -62 - index * 4 - int(abs(math.sin(t_s * 0.19 + index)) * 5)
            fault = "none"
            if index == 3 and step > steps * 0.70:
                fault = "wireless_rssi_low"
                rssi -= 14
            if index == 2 and brightness > 0.95 and step > steps * 0.45:
                fault = "thermal_watch"

            step_nodes.append(
                BoardNodeState(
                    node_id=f"RLX-N{index + 1:02d}",
                    pole_id=f"P{index + 1:03d}",
                    luminaire_id=f"L{index + 1:03d}",
                    x_m=node_x,
                    vehicle_detected=detected,
                    vehicle_distance_m=round(distance_m, 2),
                    vehicle_speed_mps=vehicle_speed_mps if detected else 0.0,
                    ambient_lux=ambient_lux,
                    driver_temp_c=round(31.0 + thermal_rise, 1),
                    enclosure_temp_c=round(28.5 + brightness * 4.0, 1),
                    current_ma=round(current_ma, 0),
                    target_brightness=round(brightness, 2),
                    wireless_rssi_dbm=rssi,
                    rs485_ok=True,
                    can_ok=True,
                    fault=fault,
                    event=node_event(distance_m, vehicle_x, node_x, brightness),
                )
            )

        records.append(
            {
                "time_s": round(t_s, 1),
                "vehicle_x_m": round(vehicle_x, 2),
                "gateway": {
                    "type": "industrial PLC/RTU gateway",
                    "wireless_nodes_online": sum(1 for node in step_nodes if node.wireless_rssi_dbm > -92),
                    "active_faults": [node.node_id for node in step_nodes if node.fault != "none"],
                },
                "nodes": [asdict(node) for node in step_nodes],
            }
        )

    return {
        "system": "ReLight-X five-node wireless board network",
        "node_count": 5,
        "controller": "STM32 edge node with RS485/CAN footprints",
        "gateway": "Industrial PLC/RTU wireless gateway",
        "sensors": ["mmWave radar", "VEML7700/BH1750", "BME280", "NTC/DS18B20", "current monitor"],
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate five ReLight-X pole-controller boards.")
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--dt", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--print-final", action="store_true")
    args = parser.parse_args()

    result = simulate(steps=args.steps, dt_s=args.dt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    final = result["records"][-1]
    print(f"Wrote {args.output}")
    print(
        "Final: "
        f"vehicle_x={final['vehicle_x_m']}m "
        f"online={final['gateway']['wireless_nodes_online']}/5 "
        f"faults={','.join(final['gateway']['active_faults']) or 'none'}"
    )
    if args.print_final:
        print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()
