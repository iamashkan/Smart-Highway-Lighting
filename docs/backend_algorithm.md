# Backend Algorithm

The Python backend is the control brain. It can run without Unity, MQTT, or hardware, which makes it useful for repeatable scenario replay.

## Modules

- `backend/highway_layout.py`: creates the 6-lane highway layout with 32 poles by default.
- `backend/vehicle_simulator.py`: emits scenario vehicles and scenario faults.
- `backend/sensor_simulator.py`: simulates mmWave radar, ambient, current, temperature, and communication status.
- `backend/lighting_controller.py`: adaptive lighting control.
- `backend/energy_model.py`: adaptive vs baseline energy and CO2 saving.
- `backend/health_model.py`: driver temperature, current, operating hours, faults, health score.
- `backend/rex_engine.py`: rule-based Re-X classification.
- `backend/passport.py`: digital product passport generator.
- `backend/mqtt_bridge.py`: optional MQTT bridge.
- `backend/scenario_runner.py`: orchestrates complete scenario runs.

## Lighting Functions

Implemented controller functions:

- `detect_nearest_pole(vehicle)`
- `determine_vehicle_direction(vehicle)`
- `calculate_lights_ahead(vehicle_speed, pole_spacing)`
- `calculate_sequential_brightness_targets(vehicle)`
- `apply_smooth_fade(current_brightness, target_brightness)`
- `emergency_zone_activation(vehicle)`
- `fade_back_after_delay()`
- `fault_fallback_control()`

## Normal Vehicle Logic

For a normal vehicle, ReLight-X only controls the luminaires facing the vehicle's travel direction.

Low, medium, and high speed thresholds select 2, 4, or 6 luminaires ahead. The nearest luminaire is driven to 100%, while downstream luminaires receive a speed and time-to-arrival weighted target. Smooth fade makes the wave visually gradual.

Direction A and Direction B are independent. Two vehicles in opposite directions can create two independent lighting waves.

## Emergency Logic

Emergency vehicles are classified by scenario metadata in the working demo:

- `ambulance`
- `police_car`
- `fire_truck`

The optional AI placeholder exposes `classify_vehicle(frame) -> vehicle_type, confidence` for future YOLO-style camera integration. The demo does not require a trained model or CCTV feed.

Emergency mode activates:

- Current zone.
- Next two zones in movement direction.
- Previous safety zone.

This activation is direction-specific by default to preserve energy savings while prioritizing safety.

## Fault Logic

Faults trigger safe fallback brightness, default 70%, and write fault history into the affected luminaire passport.

Supported simulated faults:

- Sensor fault.
- Communication loss.
- Degraded luminaire driver.

## Energy Model

The backend computes:

- Actual adaptive kWh.
- Baseline kWh if every luminaire stayed at 100%.
- Energy saved percentage.
- CO2 saving using a configurable emissions factor.
- Per-direction energy.
- Per-zone energy.

## Health and RUL

Health score is a transparent rule-based model using:

- Operating hours.
- Average brightness.
- Driver temperature.
- Fault count.
- Current anomalies and fault status.

RUL is a rule-based estimate from design life, health, thermal stress, and fault count. It is intentionally explainable for research demonstration.
