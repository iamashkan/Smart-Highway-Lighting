# ReLight-X Thesis Demo and Validation Steps

This guide is the exact no-hardware demonstration path. Follow it from top to bottom when you want to show the project to a supervisor or examiner.

## 1. Open the Project

```bash
cd Smart-Highway-Lighting
source .venv/bin/activate
```

If the virtual environment does not exist:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the Full Thesis Validation

```bash
python tools/run_thesis_validation.py
```

Expected result:

```text
[PASS] Python unit tests
[PASS] Backend scenario validation
[PASS] Wokwi STM32 board wiring validation
[PASS] Wokwi firmware artifact validation
[PASS] Five-node STM32/RS485/CAN board network validation
[PASS] AI interface validation
[PASS] Unity digital twin asset validation
```

Evidence files:

```text
data/runs/thesis_validation/validation_report.json
data/runs/thesis_validation/validation_summary.md
```

Fast mode if the STM32 firmware was already built:

```bash
python tools/run_thesis_validation.py --skip-wokwi-build
```

## 3. Open the Validation Summary

```bash
open data/runs/thesis_validation/validation_summary.md
```

Show this file as formal evidence. It includes:

- pass/fail table
- energy-saving results
- scenario-by-scenario behavior
- board validation result
- network validation result
- Unity asset validation result

## 4. Run Backend Scenarios Manually

Empty road:

```bash
python -m backend.main --scenario empty_highway --steps 70
```

Normal car direction A:

```bash
python -m backend.main --scenario normal_car_direction_a --steps 70
```

Normal car direction B:

```bash
python -m backend.main --scenario normal_car_direction_b --steps 70
```

Two cars opposite:

```bash
python -m backend.main --scenario two_cars_opposite --steps 70
```

Emergency ambulance:

```bash
python -m backend.main --scenario emergency_ambulance_direction_a --steps 70
```

Police/fire:

```bash
python -m backend.main --scenario police_fire_direction_b --steps 70
```

Fault scenarios:

```bash
python -m backend.main --scenario sensor_fault --steps 70
python -m backend.main --scenario communication_loss --steps 70
python -m backend.main --scenario degraded_luminaire --steps 70
```

With JSON output:

```bash
python -m backend.main --scenario emergency_ambulance_direction_a --steps 70 --json
```

## 5. Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Open:

```text
http://127.0.0.1:8501
```

Show these pages:

- Command Center
- Overview
- Highway Map
- Energy
- Health
- Digital Passport
- Board Network
- Board Test

Important explanation:

- Dashboard is the control panel.
- Backend is the control brain.
- Board Network page is the five-node board simulation.
- Board Test page is the command/testing panel.

## 6. Run the Five-Node Board Network Demo

```bash
python tools/run_board_network_demo.py
```

Generated file:

```text
data/runs/five_node_board_network.json
```

Then refresh the dashboard and open:

```text
Board Network
```

Explain:

- There are five virtual STM32 pole boards.
- Each board has one light connected.
- Vehicle detection changes target brightness.
- Wireless status is shown through the gateway.
- RS485 and CAN health flags are shown.
- Faults such as low RSSI or thermal watch are simulated.

## 7. Run the Wokwi STM32 Board Simulation

Open this folder in VS Code:

```bash
cd Smart-Highway-Lighting/board_simulation_wokwi
code .
```

Build firmware:

```bash
python3 tools/run_platformio.py run
```

Expected firmware:

```text
.pio/build/bluepill_f103c8/firmware.bin
.pio/build/bluepill_f103c8/firmware.elf
```

Open:

```text
diagram.json
```

Press Wokwi Play.

## 8. Wokwi Test Actions

Press or click:

- `A` / `VEH A`: vehicle in direction A
- `B` / `VEH B`: vehicle in direction B
- `E` / `EMERG`: emergency mode
- `T` / `TEST`: local brightness sweep
- `F` / `FAULT`: forced safe fallback
- `C` / `BUS FAIL`: RS485/CAN communication fault

Move or trigger:

- Radar potentiometer: vehicle presence proxy
- PIR sensor: motion presence proxy
- HC-SR04 distance: near vehicle proxy
- NTC temperature: thermal fault test
- Line-voltage slider: undervoltage test
- LDR/photoresistor: ambient light proxy

Observe:

- Luminaire A LED
- Luminaire B LED
- Fault LED
- Bus activity LED
- RS485 TX LED
- CAN TX LED
- Logic analyzer channels
- Serial telemetry

## 9. Explain the Board Connection

In Wokwi:

- STM32 `PB6` connects to Luminaire A through resistor `rA`.
- STM32 `PB7` connects to Luminaire B through resistor `rB`.
- `PB14` and `PB15` represent RS485 driver-enable/TX.
- `PA11` and `PA12` represent CAN monitor pins.
- Sensor proxies feed ADC/GPIO pins.
- Buttons inject test events and faults.

This is a virtual board with lights connected to it. It proves code behavior and test flow, not physical electrical certification.

## 10. Open Unity Digital Twin

Open Unity Hub and open:

```text
Smart-Highway-Lighting/unity_projects/ReLightX_Unity6
```

Use Unity version:

```text
Unity 6.3.6f1
```

If the scene is missing or stale:

```text
ReLight-X -> Build Unity 6 Highway Scene
```

Open:

```text
Assets/ReLightX/Scenes/ReLightXHighway.unity
```

Press Play.

Show:

- night road
- green mountains
- close pole lights
- visible lighting only from pole lights and moonlight
- random cars
- emergency vehicles
- camera views
- selectable vehicles
- smooth light fade and hold behavior

## 11. Explain Why Board Is Not Shown in Unity

The Unity scene is the digital twin visualization of the road and lighting behavior.

The board is intentionally separate:

- Wokwi shows virtual embedded board and connected lights.
- Dashboard shows board network and telemetry.
- PCB viewer shows board concept.
- Unity shows road-level behavior.

This separation is better for the thesis because it matches real systems: drivers and controllers are usually hidden in enclosures, while the road user sees traffic and light behavior.

## 12. Show PCB and Board Details

Open PCB visual viewer:

```bash
open Smart-Highway-Lighting/board_design/pcb_visualization/pcb_viewer.html
```

Open board design files:

```text
board_design/README.md
board_design/pin_mapping.csv
board_design/bom.csv
board_design/implementation/five_node_network_architecture.md
board_design/implementation/edge_controller_implementation.md
board_design/pcb_visualization/relightx_stm32_node_pcb_top.png
board_design/3d_model/relightx_edge_controller_board.obj
board_design/3d_model/relightx_five_node_network.obj
```

Explain:

- PCB files are concept-level, not fabrication-ready.
- Wokwi is the working firmware/board behavior simulation.
- KiCad placeholders and visual PCB files are design documentation.

## 13. Optional MQTT Simulation

If you want to show local message connectivity:

```bash
python tools/run_mqtt_broker.py
```

In another terminal:

```bash
python -m backend.main --scenario normal_car_direction_a --mqtt --steps 70
```

If Mosquitto is not installed, this Python helper can provide a local broker fallback depending on available Python packages. If no broker is running, the backend still works offline and prints the scenario result.

## 14. Thesis Explanation Script

Use this spoken explanation:

```text
This thesis validates ReLight-X as a simulation-only cyber-physical prototype. I do not claim real-road deployment. The Python backend simulates vehicles, sensors, faults, energy, and control logic. Unity visualizes the highway digital twin. Wokwi simulates the STM32 edge controller board with connected light outputs, sensors, RS485/CAN indicators, and test buttons. Streamlit shows the control panel and five-node board network. The validation script runs all scenarios and generates reproducible evidence. Therefore, even without physical devices, the software behavior, board logic, connectivity concept, and visualization are testable and demonstrable.
```

## 15. What to Say If Asked About Real Hardware

Answer:

```text
The project is designed so that real hardware can be added later. The current thesis validates the control logic and virtual board behavior. For physical deployment, the next stage would require real STM32 PCB design, certified RS485/CAN transceivers, real mmWave radar, real 0-10V or DALI/D4i dimming interface, photometric testing, EMC/surge testing, enclosure testing, and road authority approval.
```

## 16. Final Evidence Checklist

Before presentation, confirm:

- `python tools/run_thesis_validation.py` passes.
- `validation_summary.md` exists.
- Dashboard opens at `http://127.0.0.1:8501`.
- Board Network page shows five nodes.
- Wokwi Play starts.
- Wokwi buttons change light behavior.
- Unity scene opens and plays.
- PCB viewer opens.
- Thesis document opens.

If these all work, the project is ready for a simulation-focused thesis demonstration.
