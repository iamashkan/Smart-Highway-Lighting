# ReLight-X Master Thesis Simulation Study

## Proposed Thesis Title

ReLight-X: A Simulation-Only Digital Twin and Virtual Embedded-Board Prototype for Emergency-Aware Adaptive Highway Lighting

## Abstract Draft

This thesis presents ReLight-X, a simulation-first prototype for adaptive highway lighting. The system combines a Python traffic and lighting-control backend, a Unity 6 night-road digital twin, a Streamlit control dashboard, a Wokwi STM32 edge-controller board simulation, and a five-node virtual board-network model using wireless gateway logic with RS485/CAN indicators. The main objective is to validate the control logic, visualization, board-level behavior, connectivity concept, energy-saving behavior, emergency-vehicle response, and fault-handling workflow without requiring access to real roadway luminaires, sensors, embedded boards, or road infrastructure.

The prototype is designed for a master thesis where physical hardware is unavailable. It therefore uses repeatable simulation instead of field deployment. Normal vehicles create direction-specific sequential lighting waves; emergency vehicles trigger wider 100% safety zones; sensor and communication faults force safe fallback brightness; and degraded luminaires update health, fault history, and digital product passport state. The embedded-board behavior is tested through Wokwi using an STM32 Blue Pill virtual board, simulated sensor inputs, PWM outputs for two luminaire channels, RS485/CAN activity indicators, a logic analyzer, and fault/test buttons. The validation workflow produces machine-readable and human-readable evidence reports from automated tests.

The thesis does not claim real-world certification, photometric compliance, electrical safety, or measured hardware performance. Instead, it claims a verified simulation architecture and an implementation-ready prototype workflow that can later be transferred to real STM32 hardware, certified dimming interfaces, physical sensors, and road authority validation.

## Research Problem

Conventional roadway lighting often operates at fixed brightness during the night, even when traffic is low. This wastes energy and does not explicitly adapt to emergency vehicles, localized failures, or luminaire health. Modern adaptive systems can reduce energy use by dimming during low-traffic periods and raising brightness when vehicles or pedestrians are detected. However, developing and evaluating such systems normally requires physical luminaires, sensors, microcontrollers, communication infrastructure, and field access.

This project addresses the practical research problem:

How can an adaptive highway lighting system be designed, visualized, and validated as a credible master-thesis prototype when no real roadway hardware is available?

## Thesis Scope

This thesis is about simulation, visualization, virtual embedded-board testing, and software validation.

It includes:

- Highway traffic and vehicle scenario simulation.
- Direction-aware adaptive lighting control.
- Emergency vehicle response.
- Fault fallback behavior.
- Energy and CO2 saving estimation.
- Simulated sensor readings.
- Digital product passport and Re-X lifecycle status.
- Unity 6 digital twin visualization.
- Streamlit control-panel dashboard.
- Wokwi STM32 board simulation with connected virtual luminaires.
- Five-node virtual board network with wireless gateway, RS485, and CAN status.
- Automated validation evidence.
- Comparison with fixed, sensor-based, rule-based, and AI-based lighting methods.

It does not include:

- Certified photometric road-lighting measurement.
- Electrical safety certification.
- EMC/surge certification.
- Physical 0-10V, DALI, DALI-2, or D4i compliance testing.
- Field deployment.
- Real camera dataset training.
- Real mmWave radar packet capture.
- Real CAN/RS485 bus electrical measurement.

## Research Questions

RQ1. Can a simulation-only environment reproduce the key functional behavior of an adaptive highway lighting controller?

RQ2. Can the system demonstrate energy-saving behavior while preserving higher brightness near normal and emergency vehicles?

RQ3. Can a virtual embedded-board simulation show luminaire outputs, sensor inputs, local test controls, fault behavior, and RS485/CAN-style communication activity?

RQ4. Can a digital twin and dashboard make the system behavior understandable enough for thesis evaluation without physical devices?

RQ5. How does the proposed simulation-first method compare with fixed schedules, simple motion-sensor control, rule-based adaptive control, and AI/deep-learning-based street-lighting methods?

## Contributions

1. A complete simulation-first architecture for adaptive highway lighting.
2. A Unity 6 night-road digital twin focused on visualization rather than board display.
3. A Python backend that simulates vehicles, sensors, lighting decisions, faults, energy, health, digital passports, and Re-X lifecycle decisions.
4. A Wokwi STM32 virtual board connected to two simulated luminaire channels, multiple sensor proxies, fault controls, RS485/CAN indicators, and a logic analyzer.
5. A five-node STM32 board-network simulation using wireless gateway logic with RS485/CAN health flags.
6. A Streamlit dashboard for scenario control, board-network inspection, energy, health, and passport visualization.
7. A repeatable validation script that generates formal evidence reports.
8. A comparison framework against conventional and AI-based approaches.

## Literature Position

Smart and adaptive street lighting has been studied as a way to reduce energy consumption while maintaining lighting service quality. Gagliardi et al. describe adaptive street lighting systems using sensing, communication, web monitoring, traffic detection, and dimming profiles, and report measured comparisons between standard, LED, and smart lighting systems ([Smart Cities, 2020](https://www.mdpi.com/2624-6511/3/4/71)). The same paper describes web-based access to lighting profiles, consumption, traffic information, and alarms, which is similar to the role of the ReLight-X Streamlit dashboard.

Deep-learning-based adaptive lighting methods use cameras or embedded AI boards. Asif et al. present a YOLOv5-based system using embedded video processing for vehicle and pedestrian detection and streetlight intensity control ([Energies, 2022](https://www.mdpi.com/1996-1073/15/17/6337)). ReLight-X does not claim a trained vision model, but it includes a YOLO-style classifier interface so that a real detector can later replace simulated scenario labels.

Roadway LED lighting is also important because LED optical controllability can reduce generated light while maintaining useful road-light levels. The U.S. Department of Energy notes that LED roadway lighting has demonstrated required road levels with less than half the total generated light compared with previous technologies, due to improved optical controllability ([DOE Roadway Lighting Research](https://www.energy.gov/cmei/ssl/roadway-lighting-research)). This supports the choice to model dimmable LED luminaires rather than fixed legacy lighting.

Urban digital twins are increasingly used for simulation, visualization, monitoring, and decision support. A 2025 systematic review of IoT, AI, and digital twins in smart cities identifies real-time representation, simulation, management, 3D immersive visualization, traffic management, energy systems, and impact-evaluation gaps as major themes ([Smart Cities, 2025](https://www.mdpi.com/2624-6511/8/5/175)). ReLight-X addresses this space at prototype scale by combining digital-twin visualization with reproducible simulation evidence.

The embedded-board simulation uses Wokwi because Wokwi supports STM32 Blue Pill simulation with GPIO, USART, I2C, SPI, ADC basic conversion, and timers used by `analogWrite()` ([Wokwi STM32 Blue Pill documentation](https://docs.wokwi.com/parts/board-stm32-bluepill)). Wokwi for VS Code also supports PlatformIO workflows and requires compiled firmware/ELF files before simulation ([Wokwi VS Code documentation](https://docs.wokwi.com/vscode/getting-started)). This justifies Wokwi as the virtual hardware-in-the-loop layer for a no-device thesis.

## Comparison With Other Methods

| Method | Description | Strength | Weakness | ReLight-X Position |
| --- | --- | --- | --- | --- |
| Fixed schedule | Lights follow a clock schedule, often full brightness during night. | Simple and cheap. | Wastes energy during low traffic and cannot react to emergencies. | Used as the baseline energy comparison: all luminaires at 100%. |
| Astronomical clock dimming | Brightness depends on sunset/sunrise and time bands. | Better than full-night constant brightness. | Does not react to live vehicles, faults, or emergency vehicles. | ReLight-X adds vehicle-aware and fault-aware control. |
| Simple motion sensor | Local sensor turns nearby light on/off or dim/full. | Hardware-light and interpretable. | Can create abrupt brightness changes and poor coordination between poles. | ReLight-X adds directional pre-lighting, hold time, and smooth fade. |
| Rule-based traffic adaptive | Uses vehicle location, direction, speed, and zones to set brightness. | Deterministic, explainable, easy to validate. | Requires good sensor data and tuning. | This is the core implemented control method. |
| Deep-learning vision | Camera and AI model detect vehicle/pedestrian type. | Can classify object type and traffic context. | Needs training data, privacy handling, compute hardware, and field calibration. | ReLight-X includes an AI-ready interface but uses simulated labels for thesis validation. |
| Reinforcement learning | Learns policies from reward functions. | Can optimize complex tradeoffs. | Harder to explain and validate for safety-critical lighting. | Recommended as future comparison, not current core. |
| Digital twin with virtual board | Software, visual scene, and virtual embedded node are validated together. | Works without hardware, repeatable, demonstrable, low cost. | Cannot replace physical certification or real photometry. | This is the thesis contribution. |

## System Architecture

The system has six layers.

1. Scenario layer:
   - Defines traffic cases such as empty highway, normal car direction A, normal car direction B, two opposite cars, ambulance, police/fire, sensor fault, communication loss, and degraded luminaire.

2. Backend simulation layer:
   - Moves vehicles along the road.
   - Simulates sensor updates.
   - Computes adaptive lighting targets.
   - Applies smooth fade.
   - Records energy, health, faults, and passports.
   - Optionally publishes MQTT messages.

3. Dashboard layer:
   - Shows command center status, highway map, energy, health, digital passport, board network, and board test controls.

4. Unity digital twin layer:
   - Shows a night highway, road, mountains, traffic, emergency vehicles, pole lights, light beams, camera views, cinematic view, and vehicle-following views.
   - It does not show the PCB because the project separates digital-twin visualization from board design.

5. Wokwi virtual board layer:
   - Shows a simulated STM32 pole node.
   - Connects PWM outputs to two light channels.
   - Adds ambient, radar proxy, PIR, ultrasonic, temperature, and voltage inputs.
   - Adds manual fault/test/emergency/vehicle buttons.
   - Shows RS485/CAN activity indicators and logic-analyzer channels.

6. Five-node virtual network layer:
   - Simulates five pole boards connected through a PLC/RTU gateway concept.
   - Tracks wireless RSSI, RS485 OK, CAN OK, brightness, sensor values, and faults.

## Control Algorithm

The backend control logic is deterministic and explainable.

1. At every simulation tick, active vehicles are updated.
2. Each vehicle has:
   - vehicle ID
   - type
   - direction A or B
   - lane
   - road position
   - speed
   - emergency flag
3. The controller finds the nearest pole to each vehicle.
4. For normal vehicles:
   - It lights only the vehicle direction.
   - It chooses how many poles ahead should be activated based on speed.
   - It creates a sequential wave ahead of the vehicle.
   - It keeps lights on briefly after the vehicle passes.
   - It fades back gradually to 30% eco brightness.
5. For emergency vehicles:
   - It finds the current zone.
   - It activates current, previous safety, and forward zones.
   - It sets the emergency-direction luminaires to 100% target brightness.
6. For faults:
   - Sensor fault and communication loss set affected zones to safe fallback.
   - Degraded luminaire reduces health score, records fault history, and updates the digital passport.
   - Safe fallback target brightness is 70%.
7. Energy is calculated by comparing adaptive brightness against a full-power baseline.

## Virtual Board Design in Wokwi

The Wokwi board is the proof that a board with lights connected to it can be tested without real hardware.

The simulated board uses:

- STM32 Blue Pill controller.
- Luminaire A PWM output on `PB6`.
- Luminaire B PWM output on `PB7`.
- RS485 driver-enable and TX indicators on `PB14` and `PB15`.
- CAN TX/RX monitor on `PA11` and `PA12`.
- Ambient light proxy on `PA0`.
- Radar/mmWave proxy slider on `PA1`.
- NTC temperature input on `PA2`.
- Line-voltage monitor on `PA3`.
- Fault button on `PA4`.
- Test button on `PA5`.
- Vehicle A button on `PA6`.
- Vehicle B button on `PA7`.
- Emergency button on `PB0`.
- Bus-fault button on `PB1`.
- PIR and ultrasonic presence inputs on `PB10`, `PB12`, and `PB13`.
- Fault, bus, RS485, and CAN LEDs.
- Logic analyzer channels for PWM, bus, fault, and status behavior.

What this proves:

- The firmware compiles for an STM32 target.
- The board has connected simulated lights.
- Manual vehicle events change the light brightness.
- Emergency mode forces high brightness.
- Fault mode forces safe fallback.
- Communication fault creates a visible bus/fallback condition.
- Sensor proxies can trigger lighting without physical sensors.

What this does not prove:

- Exact electrical behavior of a real 0-10V circuit.
- Real RS485 or CAN physical-layer signal quality.
- Real mmWave radar detection performance.
- Real luminaire compatibility.

## Five-Node Board Network

The five-node simulation represents how multiple boards would be placed on poles.

Each node contains:

- STM32 controller concept.
- One luminaire.
- mmWave radar concept.
- VEML7700/BH1750 ambient light concept.
- BME280 environment concept.
- NTC/DS18B20 temperature concept.
- Current monitor concept.
- Wireless link to gateway.
- RS485/CAN health flags.

The gateway model reports:

- number of wireless nodes online
- active faults
- node brightness values
- sensor values
- vehicle location
- RS485/CAN status

This lets the thesis demonstrate board-to-board and board-to-gateway behavior without real radio modules or bus transceivers.

## AI Component

The current project is AI-ready rather than AI-dependent.

Implemented now:

- `backend/ai_vehicle_classifier.py` provides a YOLO-style function:
  - input: simulated frame or metadata
  - output: vehicle type and confidence
- Scenarios provide simulated labels such as normal car, ambulance, police car, and fire truck.
- Emergency behavior is triggered from this simulated classification result.

Why this is acceptable for the thesis:

- The thesis goal is system simulation and validation without real hardware.
- Training a real detector requires a dataset, camera placement, privacy review, and embedded GPU hardware.
- The project still defines the exact integration point where a real AI model would be inserted.

Recommended comparison discussion:

- Rule-based ReLight-X is more explainable and easier to validate than deep learning.
- Deep learning is stronger for visual classification but needs data and hardware.
- A hybrid future system can use AI only for classification, while keeping lighting safety policy rule-based.

## Validation Methodology

The validation strategy follows a simulation-only evidence chain.

1. Source-code validation:
   - Python unit tests.
   - Scenario acceptance rules.
   - JSON/CSV checks.

2. Backend behavior validation:
   - Empty highway remains at 30%.
   - Normal direction A lights only direction A.
   - Normal direction B lights only direction B.
   - Opposite cars activate independent waves.
   - Ambulance activates emergency zones.
   - Police/fire activates emergency zones.
   - Sensor fault creates safe fallback.
   - Communication loss creates safe fallback.
   - Degraded luminaire updates health and passport.

3. Board simulation validation:
   - Wokwi diagram contains STM32, connected lights, sensors, buttons, bus indicators, and logic analyzer.
   - PlatformIO builds STM32 firmware.
   - Firmware binary and ELF exist for Wokwi.

4. Network validation:
   - Five board nodes exist.
   - Vehicle detection occurs.
   - Brightness wave moves across nodes.
   - Wireless gateway reports online nodes.
   - RS485/CAN health flags remain available.

5. Visualization validation:
   - Unity project contains the generator and scripts.
   - Vehicle assets exist.
   - Scene can be rebuilt in Unity 6.

6. Dashboard validation:
   - Streamlit dashboard shows backend, energy, health, board network, and board test pages.

## Automated Evidence

Run:

```bash
cd Smart-Highway-Lighting
source .venv/bin/activate
python tools/run_thesis_validation.py
```

The script writes:

```text
Smart-Highway-Lighting/data/runs/thesis_validation/validation_report.json
Smart-Highway-Lighting/data/runs/thesis_validation/validation_summary.md
```

Current validation result:

```text
7/7 checks passed
```

The generated scenario evidence includes:

- empty highway: 70.00% simulated energy saving
- normal direction A: 63.07% simulated energy saving
- normal direction B: 63.07% simulated energy saving
- two opposite cars: 56.14% simulated energy saving
- emergency ambulance direction A: 49.63% simulated energy saving
- police/fire direction B: 41.36% simulated energy saving
- sensor fault: 59.60% simulated energy saving
- communication loss: 59.88% simulated energy saving
- degraded luminaire: 62.60% simulated energy saving

These values are simulation outputs, not physical measurements.

## How to Defend Simulation-Only Approval

The thesis can be approved as a simulation and virtual-prototyping thesis if the claims are framed correctly.

Strong claims:

- The adaptive control algorithm was implemented and tested.
- Directional lighting behavior was validated in simulation.
- Emergency lighting behavior was validated in simulation.
- Fault fallback behavior was validated in simulation.
- Board-level firmware compiles for STM32 and runs in a virtual embedded environment.
- Simulated lights are connected to the virtual board.
- A five-node board network was modeled.
- A Unity digital twin visualizes the operating concept.
- A dashboard shows system state and testing outputs.
- The method is repeatable without physical hardware.

Claims to avoid:

- The system is ready for public-road deployment.
- The PCB is fabrication-certified.
- The dimming output is electrically certified.
- The system satisfies roadway lighting standards.
- The AI model is trained and field-validated.
- RS485/CAN physical performance is measured.

## Demonstration Script for Supervisor

1. Show the thesis document and architecture diagram.
2. Run the validation script.
3. Open the generated validation summary.
4. Start the Streamlit dashboard.
5. Show the Board Network page.
6. Open Wokwi and press Play.
7. Press `A`, `B`, `E`, `T`, `F`, and `C` in Wokwi to show vehicle, emergency, test, fault, and bus-fault behavior.
8. Open Unity 6.
9. Rebuild the highway scene from the ReLight-X menu if necessary.
10. Press Play and show the night highway, traffic, pole lights, emergency vehicles, and camera views.
11. Explain that Wokwi is the virtual board, Unity is the digital twin, Streamlit is the control panel, and Python is the control brain.
12. Open the comparison table and explain why the proposed method is credible without physical devices.

## Limitations

- Sensor readings are simulated.
- Vehicle positions are synthetic.
- AI classification uses scenario labels and a replaceable API.
- Energy saving is computed from brightness and configured luminaire power, not from a power meter.
- Wokwi validates firmware behavior but not real electrical noise, isolation, surge, or EMC.
- Unity validates visual behavior but not physical photometric road illumination.
- The PCB visualization is conceptual, not fabrication-ready.

## Future Work

1. Replace simulated classifier with a trained emergency-vehicle detector.
2. Connect real mmWave radar packets.
3. Implement real STM32 CAN/FDCAN and RS485 firmware.
4. Add MQTT bridge from STM32 gateway to backend.
5. Build one physical low-voltage board.
6. Measure real PWM and 0-10V output.
7. Create a KiCad fabrication-ready PCB.
8. Add photometric simulation with road-surface illuminance metrics.
9. Test cybersecurity behavior using digital twin fault injection.
10. Compare rule-based control with reinforcement learning in simulation.

## Conclusion

ReLight-X is suitable as a master-thesis simulation prototype because it presents a complete, testable, and repeatable system without requiring real roadway hardware. The project combines algorithmic control, virtual embedded-board testing, multi-node board-network simulation, digital twin visualization, dashboard monitoring, and formal validation evidence. Its strongest academic value is not claiming deployment readiness, but showing how a complex cyber-physical roadway lighting system can be designed and evaluated through transparent simulation when physical access is unavailable.
