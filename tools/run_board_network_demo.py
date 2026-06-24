from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_URL = "http://127.0.0.1:8501"


def port_is_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ReLight-X five-node board-network demo.")
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--no-dashboard", action="store_true", help="Only generate five-node telemetry JSON.")
    args = parser.parse_args()

    sim_cmd = [
        sys.executable,
        str(ROOT / "board_design" / "simulation" / "five_node_network_sim.py"),
        "--steps",
        str(args.steps),
    ]
    subprocess.run(sim_cmd, cwd=str(ROOT), check=True)

    print()
    print("Five-node board telemetry is ready:")
    print(f"  {ROOT / 'data' / 'runs' / 'five_node_board_network.json'}")
    print()
    print("Dashboard page:")
    print("  Sidebar -> Board Network")
    print(f"  {DASHBOARD_URL}")
    print()

    if args.no_dashboard:
        return 0

    if port_is_open("127.0.0.1", 8501):
        print("Streamlit already appears to be running on port 8501.")
        print("Refresh the browser and open the Board Network page.")
        return 0

    print("Starting Streamlit dashboard. Press Ctrl+C to stop it.")
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "dashboard" / "app.py")],
        cwd=str(ROOT),
    )


if __name__ == "__main__":
    raise SystemExit(main())
