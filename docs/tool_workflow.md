# ReLight-X Tool Workflow

## Unity 6.3.6f1

Use Unity only for the highway digital twin visualization:

- Night highway scene.
- Random traffic.
- Normal cars, police, ambulance, firetruck.
- Adaptive lighting waves.
- Emergency lighting mode.
- Selectable vehicle cameras.
- First-person, third-person, overview, and cinematic views.

The Unity scene should not show the board.

## Streamlit Web Control Panel

Use the Streamlit dashboard as the system command center:

- Backend simulation control.
- 3D highway status view.
- Energy and CO2 saving.
- Health and fault state.
- Digital passports.
- MQTT and board connection indicators.
- HIL board command publishing.

Run:

```bash
streamlit run dashboard/app.py
```

## Wokwi

Use Wokwi for the STM32 pole-node board simulation:

- PWM dimming A/B.
- RS485/CAN bus activity indicators.
- Ambient light, PIR, ultrasonic, radar proxy, temperature, and line-voltage inputs.
- Safe fallback mode.
- Communication fault and emergency tests.
- Local test mode.
- Fault button.
- Serial telemetry.

Folder:

```text
board_simulation_wokwi/
```

## KiCad

Use KiCad for schematic, PCB layout, routing, BOM, manufacturing outputs, and 3D board preview.

Folder:

```text
board_design/
```

The KiCad files here are still placeholders plus implementation guides. Use the layout guide and PCB visualization files to make the real schematic and PCB.
