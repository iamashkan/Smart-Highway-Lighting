#!/usr/bin/env python3
"""Small launcher for VS Code tasks so they do not depend on a global `pio` path."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


BOARD_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BOARD_DIR.parent


def existing_python(path: Path) -> str | None:
    return str(path) if path.exists() and os.access(path, os.X_OK) else None


def python_candidates() -> list[str]:
    candidates: list[str] = []
    env_python = os.environ.get("PLATFORMIO_PYTHON")
    if env_python:
        candidates.append(env_python)

    for path in (
        REPO_DIR / ".venv" / "bin" / "python",
        BOARD_DIR / ".venv" / "bin" / "python",
    ):
        found = existing_python(path)
        if found:
            candidates.append(found)

    candidates.extend([sys.executable, "python3", "python"])

    unique: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in unique:
            unique.append(candidate)
    return unique


def has_platformio_module(python: str) -> bool:
    try:
        result = subprocess.run(
            [python, "-m", "platformio", "--version"],
            cwd=str(BOARD_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def find_platformio_runner() -> list[str] | None:
    pio = shutil.which("pio")
    if pio:
        return [pio]

    for python in python_candidates():
        if has_platformio_module(python):
            return [python, "-m", "platformio"]
    return None


def install_platformio() -> int:
    for python in python_candidates():
        try:
            subprocess.run([python, "--version"], check=True, stdout=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            continue

        print(f"Installing PlatformIO Core with: {python} -m pip install platformio")
        return subprocess.call([python, "-m", "pip", "install", "platformio"], cwd=str(BOARD_DIR))

    print("Could not find Python to install PlatformIO Core.")
    return 127


def print_missing_platformio_help() -> None:
    print()
    print("PlatformIO Core was not found, so Wokwi cannot build firmware.bin yet.")
    print()
    print("Fix option 1, from VS Code:")
    print("  Terminal -> Run Task -> Install PlatformIO Core")
    print()
    print("Fix option 2, from Terminal:")
    print("  cd Smart-Highway-Lighting")
    print("  source .venv/bin/activate")
    print("  python -m pip install platformio")
    print("  cd board_simulation_wokwi")
    print("  python3 tools/run_platformio.py run")
    print()
    print("After the build succeeds, Wokwi will find:")
    print("  .pio/build/bluepill_f103c8/firmware.bin")


def main() -> int:
    args = sys.argv[1:]
    if args == ["--install"]:
        return install_platformio()

    runner = find_platformio_runner()
    if runner is None:
        print_missing_platformio_help()
        return 127

    command = runner + args
    print("Running:", " ".join(command))
    return subprocess.call(command, cwd=str(BOARD_DIR))


if __name__ == "__main__":
    raise SystemExit(main())
