# ReLight-X Unity 6 Digital Twin Project

Open this folder directly in Unity Hub:

```text
Smart-Highway-Lighting/unity_projects/ReLightX_Unity6
```

This is a Unity 6.3.6f1 project scaffold. When the project opens, the editor setup script creates:

- `Assets/ReLightX/Scenes/ReLightXHighway.unity`
- generated materials
- a complete six-lane highway through a dark green mountain valley
- 96 close-spaced median lighting poles
- two independently controlled luminaires per pole
- downloaded CC0 vehicle models from Kenney
- downloaded CC0 street-lamp environment asset from Poly Haven
- random night traffic with adaptive lighting response
- selectable vehicle cameras: first-person, third-person, side-up wide, overview, and cinematic
- futuristic in-scene HUD and traffic controls
- black night environment where the road is mostly visible from pole lights, headlights, emergency beacons, lane markings, guardrails, and fog
- a small visible moon with very low moonlight
- no zone visualizer overlay in the road; the scene focuses on the night digital-twin visualization
- idle roadway lighting stays at 30%, then rises for approaching vehicles and fades down gradually after they pass

If the scene is not created automatically, run:

```text
Unity menu -> ReLight-X -> Build Unity 6 Highway Scene
```

Then open:

```text
Assets/ReLightX/Scenes/ReLightXHighway.unity
```

Press Play. Use the public methods on `HighwaySceneManager` for UI buttons or inspector testing:

- `TriggerNormalVehicleA`
- `TriggerNormalVehicleB`
- `TriggerEmergencyVehicleA`
- `TriggerEmergencyVehicleB`
- `TriggerSensorFault`
- `TriggerCommunicationFault`
- `TriggerSafeFallbackVisualization`

MQTT is optional. The project compiles without MQTTnet. To enable live MQTT, install MQTTnet into Unity and add the scripting define symbol `RELIGHTX_MQTTNET`.

The board is intentionally not shown in this Unity scene. Board design and board simulation are handled separately in:

```text
board_design/
board_simulation_wokwi/
```

## Camera Controls

- Click any vehicle to select it.
- Use `Prev Car` and `Next Car` in the panel to select only vehicles currently inside the road.
- Use `Car A`, `Car B`, `Emerg A`, and `Emerg B` to manually spawn visible vehicles in direction A or B.
- `1`: overview camera.
- `2`: third-person selected vehicle view.
- `3`: first-person selected vehicle view.
- `4`: side-up wide selected vehicle view.
- `5`: cinematic moving camera.

## Rebuilding After Changes

In `Edit -> Project Settings -> Player -> Active Input Handling`, keep the setting on `Both`.

If you already opened an older version of the scene, run:

```text
Stop Play Mode
Assets -> Refresh
Unity menu -> ReLight-X -> Build Unity 6 Highway Scene
Open Assets/ReLightX/Scenes/ReLightXHighway.unity
Clear the Console
Press Play
```

This regenerates the latest visualization-only digital twin scene. It also removes old generated objects such as the former `Direction A/B` road labels and `Zone Visualizer`.

This rebuild is required after the Input System fix and the mountain-night scene update, because older generated scenes may still contain Unity's legacy `StandaloneInputModule` or older daylight/pole-spacing settings.
