# Testing Plan

## Backend Smoke Tests

Run:

```bash
python -m unittest discover -s tests
```

Expected checks:

- Direction A normal vehicles only raise Direction A luminaires.
- Direction B normal vehicles only raise Direction B luminaires.
- Emergency vehicles activate the full A or B travel direction to 100%.
- Fault scenarios produce safe fallback and passport fault logs.

## Scenario Tests

1. Empty highway:
   - all luminaires remain at 30%.
2. Normal car Direction A:
   - Direction A wave only.
3. Normal car Direction B:
   - Direction B wave only.
4. Two cars opposite:
   - independent A and B waves.
5. Emergency ambulance Direction A:
   - emergency safety zones in Direction A.
6. Police/fire Direction B:
   - emergency safety zones in Direction B.
7. Sensor fault:
   - affected zone fallback at 70%.
8. Communication loss:
   - board/zone safe fallback.
9. Degraded luminaire:
   - health decreases and Re-X moves toward repair/remanufacture/recycle.

## HIL Test

1. Start Mosquitto.
2. Flash the STM32 firmware or build the Wokwi STM32 firmware.
3. Run backend with `--mqtt`.
4. Confirm PWM output follows brightness commands.
5. Confirm telemetry appears on dashboard and MQTT logs.

## Visual Verification

In Unity:

- Verify there are six lanes.
- Verify each pole has two independently controlled luminaires.
- Verify normal waves do not cross directions.
- Verify emergency mode is immediately visible.
- Verify faults are visible and logged.
