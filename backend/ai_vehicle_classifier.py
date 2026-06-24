from __future__ import annotations

from typing import Any


def classify_vehicle(frame: Any) -> tuple[str, float]:
    """YOLO-style placeholder API for a future roadside camera model.

    The working demo uses simulated classification from scenario metadata. This
    hook intentionally mirrors the API a real detector would expose, so a later
    module can replace the mock without changing the lighting controller.
    """
    if isinstance(frame, dict) and "mock_vehicle_type" in frame:
        return str(frame["mock_vehicle_type"]), float(frame.get("confidence", 0.92))
    return "normal_car", 0.55
