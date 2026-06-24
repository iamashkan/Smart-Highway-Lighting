# Unity Digital Twin

Unity is the main visual demonstration layer.

## Full Unity 6 Project

Open this folder in Unity Hub:

```text
Smart-Highway-Lighting/unity_projects/ReLightX_Unity6
```

The project contains Unity 6 project settings, packages, scripts, models, and an editor setup script. On first open, it creates:

- `Assets/ReLightX/Scenes/ReLightXHighway.unity`
- generated materials
- 96 close-spaced poles
- 192 independently controlled luminaires
- random traffic and emergency vehicles
- selectable first-person, third-person, side-up-wide, overview, and cinematic views
- downloaded CC0 vehicle assets
- night lighting, headlights, emergency beacons, fog, guardrails, and lane markings
- in-scene digital-twin HUD, light-inspection panel, energy-saved panel, and traffic controls

If the scene is not created automatically, use:

```text
Unity menu -> ReLight-X -> Build Unity 6 Highway Scene
```

## Scene Elements

- 6 lanes total: 3 lanes Direction A, 3 lanes Direction B.
- 96 configurable poles by default.
- Two luminaires per pole.
- Independent brightness per luminaire.
- Clickable luminaire inspection with pole ID, board node ID, direction, brightness, 0-10V output, simulated power, current, temperature, detected vehicle count, nearest vehicle distance, health, fault, and Re-X state.
- Random normal and emergency vehicles.
- Automatic spacing/gap control between vehicles in each lane.
- Multi-vehicle light aggregation so close vehicles behind each other can both be represented in the same luminaire's digital-twin data.
- Sensor/light logic uses all active traffic vehicles, not only the selected camera vehicle.
- Normal-vehicle lighting uses a continuous sensor window along the road axis, so poles at the beginning, middle, and end of the road are handled by the same calculation.
- Pole luminaires use a simple procedural design: mast, arms, one housing, and one roadway spotlight per luminaire.
- The asphalt road is split into short render segments so Unity URP can apply nearby pole lights consistently instead of dropping most lights on one huge mesh.
- Selected-car speed controls: `Car +10`, `Car -10`, and `Reset Car`.
- Close-follow test buttons: `2 Car A` and `2 Car B`.
- Emergency full-direction lighting response for the active A or B direction.
- Fault visualization.
- Energy panel showing baseline energy, adaptive energy, energy saved from scenario start until now, saved percentage, and CO2 avoided.
- Click-to-select vehicle camera handoff.
- First-person, third-person, side-up-wide, overview, and cinematic camera modes.
- Visualization-only digital twin with no board objects shown in the Unity scene.

## Integration

Unity can run in two modes:

1. Offline visual demo using `TrafficSimulationManager`.
2. MQTT-driven demo using `MQTTClientBridge` with MQTTnet enabled.

## Expected Demo Flow

1. Open the Unity 6 project.
2. Run `ReLight-X -> Build Unity 6 Highway Scene`.
3. Press Play.
4. Watch random traffic enter both directions at night.
5. Click any vehicle to switch to a third-person view.
6. Click any pole light to inspect its live digital-twin telemetry in the right-side panel.
7. Select one car, then use `Car +10`, `Car -10`, and `Reset Car` to change only that vehicle's speed.
8. Use `First Top`, `Third`, and `Side` for selected-car camera views, or `Overview` and `Cine` for scene-level views.
9. Use `2 Car A` or `2 Car B` to create a close-following two-car test and confirm selected lights show multiple detected vehicles when both cars influence the same area.
10. Watch normal vehicle lighting waves and emergency vehicle 100% safety zones.
