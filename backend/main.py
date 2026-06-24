from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import DEFAULT_CONFIG
from .scenario_runner import run_scenario, write_sample_data
from .vehicle_simulator import SCENARIOS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ReLight-X adaptive highway lighting backend.")
    parser.add_argument("--scenario", default="normal_car_direction_a", choices=sorted(SCENARIOS.keys()))
    parser.add_argument("--steps", type=int, default=90)
    parser.add_argument("--mqtt", action="store_true", help="Publish state to a local MQTT broker.")
    parser.add_argument("--output-dir", default="data/runs/latest")
    parser.add_argument("--write-sample-data", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print final state JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.write_sample_data:
        write_sample_data()
        print("Wrote sample data to data/")
        return

    final_state = run_scenario(
        scenario_name=args.scenario,
        steps=args.steps,
        config=DEFAULT_CONFIG,
        output_dir=Path(args.output_dir),
        mqtt_enabled=args.mqtt,
    )
    if args.json:
        print(json.dumps(final_state, indent=2))
    else:
        energy = final_state["energy"]
        print(
            f"Scenario={args.scenario} mode={final_state['system']['active_mode']} "
            f"adaptive={energy.get('actual_kwh', 0):.4f}kWh "
            f"saved={energy.get('energy_saved_pct', 0):.1f}% "
            f"faults={len(final_state['system']['active_faults'])}"
        )


if __name__ == "__main__":
    main()
