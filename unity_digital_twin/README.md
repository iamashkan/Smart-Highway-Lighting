# Unity Digital Twin

This folder contains Unity C# scripts and scene setup notes for the ReLight-X six-lane highway digital twin.

The Unity scene is the main presentation layer. It visualizes 32 configurable poles by default, two luminaires per pole, independent Direction A/B brightness, normal vehicle lighting waves, emergency zone activation, faults, and simple dashboard text.

## Recommended Scene Setup

1. Create a new Unity 3D project.
2. Copy `unity_digital_twin/Scripts` into `Assets/ReLightX/Scripts`.
3. Create an empty GameObject named `ReLightXScene`.
4. Attach `HighwaySceneManager`.
5. Attach `MQTTClientBridge` to the same object.
6. Optional: attach `DashboardUI`, `ZoneVisualizer`, `EmergencyModeVisualizer`, and `FaultVisualizer` to suitable UI/visual objects.
7. Press Play. The highway, lanes, poles, luminaires, and demo vehicles can be generated from code.

## MQTT Mode

The scripts compile without MQTT dependencies. To enable real MQTT inside Unity:

1. Install MQTTnet into the Unity project.
2. Add the scripting define symbol `RELIGHTX_MQTTNET`.
3. Configure broker host and port on `MQTTClientBridge`.
4. Run the Python backend with `python -m backend.main --scenario normal_car_direction_a --mqtt`.

Subscribed topics:

- `relightx/luminaire/+/brightness`
- `relightx/zone/+/mode`
- `relightx/system/energy`
- `relightx/system/emergency`

## Manual Demo Triggers

Use the public methods on `HighwaySceneManager` from Unity UI buttons:

- `TriggerNormalVehicleA`
- `TriggerNormalVehicleB`
- `TriggerEmergencyVehicleA`
- `TriggerEmergencyVehicleB`
- `TriggerSensorFault`
- `TriggerCommunicationFault`
- `TriggerBoardTestMode`

These triggers are visual-only helpers for interviews when the Python backend is not running.
