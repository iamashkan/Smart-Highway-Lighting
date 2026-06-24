<div align="center">

# 🛣️ Smart Highway Lighting

### Emergency-Aware Adaptive Highway Lighting · Digital Twin · Edge-Controller Board

*A motorway that only lights the road you are actually driving on — and goes brighter the instant an ambulance appears.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](#)
[![MQTT](https://img.shields.io/badge/MQTT-Telemetry-660066?style=for-the-badge&logo=mqtt&logoColor=white)](#)
[![STM32](https://img.shields.io/badge/STM32-Edge%20Board-03234B?style=for-the-badge&logo=stmicroelectronics&logoColor=white)](#)
[![Unity 6](https://img.shields.io/badge/Unity%206-Digital%20Twin-000000?style=for-the-badge&logo=unity&logoColor=white)](#)

![Status](https://img.shields.io/badge/status-research%20prototype-success?style=flat-square)
![Simulation](https://img.shields.io/badge/mode-simulation--first-blue?style=flat-square)
![Energy](https://img.shields.io/badge/energy%20saved-up%20to%2070%25-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

</div>

---

## ✨ Overview

**Smart Highway Lighting** (engine codename **ReLight-X**) is a research-grade prototype for a **6-lane smart motorway lighting system**. Instead of blasting a whole highway at full power all night, it keeps the road in a low-energy "eco" glow and raises only the luminaires that a moving vehicle actually needs — then escalates to a **100% safety corridor** the moment an emergency vehicle is detected.

The system is **simulation-first** by design: it does not assume access to real luminaires or motorway infrastructure, so the full pipeline — sensing → control → lighting → telemetry → lifecycle — runs end-to-end on a laptop, and is wired to drive a **virtual STM32 edge-controller board** and a **Unity 6 digital twin**.

> Built to be credible for lab demonstration, thesis defense, and engineering review — **not** a certified road deployment.

<div align="center">

| 🛣️ Poles | 💡 Luminaires | 🚦 Lanes | 📏 Length | 🧭 Zones | 📡 Sensors | 🔌 Edge Boards |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **32** | **64** | **6** | **1.24 km** | **8** | **32** | **5 (STM32)** |

</div>

---

## 🧠 How It Behaves

```mermaid
flowchart LR
    S([📡 Sensors detect<br/>vehicle + speed]) --> D{What is on<br/>the road?}
    D -->|Empty| E[🌙 Eco mode<br/>30% both directions]
    D -->|Normal vehicle| N[🌊 Directional wave<br/>100% ahead of car<br/>only its direction]
    D -->|Emergency vehicle| M[🚨 Safety corridor<br/>100% in emergency<br/>direction]
    D -->|Fault detected| F[🛡️ Safe fallback<br/>70% + dashboard alert]
    E --> L[💡 Luminaire driver<br/>PWM / 0–10V dimming]
    N --> L
    M --> L
    F --> L
    L --> T[(📊 Telemetry · MQTT<br/>Dashboard · Digital Twin)]
    L --> H[♻️ Health · RUL ·<br/>Digital Passport · Re-X]
```

| Situation | Lighting response |
|---|---|
| 🌙 **Empty highway** | Both directions hold a configurable **30% eco brightness** |
| 🚗 **Normal vehicle** | Only luminaires facing the vehicle's direction create a smooth **sequential lighting wave** |
| 🚑 **Emergency vehicle** | Ambulance / police / fire scenarios trigger a **100% safety zone** in the emergency direction |
| ⚠️ **Faults** | Comms, sensor, or degraded-luminaire faults fall back to **70% safe brightness** + dashboard alert |
| ♻️ **Lifecycle** | Every luminaire gets **health, Remaining-Useful-Life, a digital passport, and a Re-X decision** |

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph EDGE["🔌 Edge Layer — 5x STM32 Board Network"]
        B1[Board 1<br/>Zone A]:::brd
        B2[Board 2<br/>Zone B]:::brd
        B3[Board 3<br/>Zone C]:::brd
        B4[Board 4]:::brd
        B5[Board 5]:::brd
        B1 <-->|RS485 / CAN| B2 <--> B3 <--> B4 <--> B5
    end

    subgraph CORE["🧠 Control Backend — Python"]
        C1[Sensor &<br/>Vehicle Sim]
        C2[Lighting<br/>Controller]
        C3[Energy &<br/>CO2 Model]
        C4[Health · RUL ·<br/>Re-X Engine]
        C1 --> C2 --> C3
        C2 --> C4
    end

    subgraph VIS["🖥️ Visualization & Ops"]
        V1[Streamlit<br/>Dashboard]
        V2[Unity 6<br/>Digital Twin]
    end

    EDGE <-->|MQTT telemetry| CORE
    CORE -->|state stream| VIS

    classDef brd fill:#03234B,stroke:#5b8def,color:#fff;
```

The same control logic drives three substitutable front-ends: a **Streamlit ops dashboard**, a **Unity 6 night-highway digital twin**, and a **virtual STM32 board network** (RS485 / CAN / wireless) — all fed by an MQTT telemetry bus.

---

## ⚡ Why It Matters

<div align="center">

| Metric | Value | Notes |
|---|---|---|
| 🌙 Energy saved (empty road) | **≈ 70%** | vs. all-luminaires-at-100% baseline |
| 🚗 Energy saved (single vehicle) | **≈ 63%** | directional wave, opposite direction stays eco |
| 💡 Max power / luminaire | **160 W** | dimmable LED roadway driver class |
| 🌍 Carbon factor | **0.404 kg CO₂ / kWh** | configurable grid intensity |
| 👁️ Detection range | **90 m** | look-ahead vehicle anticipation |

</div>

Targets the real class of **DALI / DALI-D4i, 0–10V / 1–10V, NEMA 7-pin, or Zhaga-D4i** LED roadway luminaires (Schréder IZYLUM-class, Signify Luma / RoadFocus-class). The lab prototype uses simulated PWM / 0–10V dimming; certified DALI/D4i is documented as the future hardware path.

---

## 🧩 Tech Stack

`Python` · `Streamlit` · `Plotly` · `Pandas` · `paho-mqtt / amqtt` · `STM32 (PlatformIO + Wokwi)` · `RS485 / CAN` · `Unity 6 (C#)` · `KiCad (board design)` · `ROS2 / Gazebo (optional)`

---

## 📂 Project Structure

```text
backend/                  Python simulation · MQTT bridge · control · energy · health · Re-X · passports
dashboard/                Streamlit monitoring dashboard
unity_digital_twin/       Lightweight Unity scripts & scene-setup notes
unity_projects/           Full Unity 6 project (open in Unity Hub)
edge_controller_firmware/ Legacy ESP32 PlatformIO firmware notes
board_design/             Board concept · BOM · pin map · KiCad placeholders · PCB visualization
board_simulation_wokwi/   Wokwi STM32 board simulation with RS485/CAN and sensors
data/                     Generated sample JSON / CSV datasets
docs/                     Research documentation, diagrams & thesis study
ros2_gazebo_optional/     Minimal optional ROS2 / Gazebo skeleton
tests/                    Backend smoke tests
```

---

## 🚀 Quick Start

```bash
# 1 — Set up the environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2 — Generate sample data & run a scenario
python -m backend.main --write-sample-data
python -m backend.main --scenario emergency_ambulance_direction_a --steps 90

# 3 — Launch the live dashboard
streamlit run dashboard/app.py
```

### 🔗 Five-Node Board Network Demo

```bash
source .venv/bin/activate
python tools/run_board_network_demo.py
```
Then open `http://127.0.0.1:8501` and pick **Board Network** in the sidebar.
Detailed guide → [Five-Node Board Demo](docs/five_node_board_demo.md)

### 🎮 Unity 6 Digital Twin

Open `unity_projects/ReLightX_Unity6` in Unity Hub. On first launch the editor script builds the full night-highway scene (`Assets/ReLightX/Scenes/ReLightXHighway.unity`); if it doesn't appear, run **ReLight-X → Build Unity 6 Highway Scene** from the menu. The scene is visualization-only: night highway, traffic, emergency vehicles, selectable vehicle cameras, and adaptive lighting.

### 🎓 Thesis-Style Validation

```bash
source .venv/bin/activate
python tools/run_thesis_validation.py   # → data/runs/thesis_validation/
```

---

## 🎬 Demo Scenarios

| Traffic | Emergency | Fault |
|---|---|---|
| `empty_highway` | `emergency_ambulance_direction_a` | `sensor_fault` |
| `normal_car_direction_a` | `police_fire_direction_b` | `communication_loss` |
| `normal_car_direction_b` | | `degraded_luminaire` |
| `two_cars_opposite` | | |

---

## 📚 Documentation

| | |
|---|---|
| 🧭 [System Architecture](docs/system_architecture.md) | 🧮 [Backend Algorithm](docs/backend_algorithm.md) |
| 📡 [MQTT Protocol](docs/mqtt_protocol.md) | 🔧 [Hardware Architecture](docs/hardware_architecture.md) |
| 🔌 [Board Design](docs/board_design.md) | 🎮 [Unity Digital Twin](docs/unity_digital_twin.md) |
| ✅ [Testing Plan](docs/testing_plan.md) | 🎓 [Master Thesis Simulation Study](docs/master_thesis_simulation_study.md) |
| 📋 [Thesis Demo & Validation Steps](docs/thesis_demo_and_validation_steps.md) | 🔭 [Limitations & Future Work](docs/limitations_and_future_work.md) |

---

## 🗺️ Roadmap

- [ ] Certified **DALI / D4i** dimming interface path
- [ ] Hardware-in-the-loop with a physical STM32 node
- [ ] On-board ML vehicle classifier on the edge
- [ ] Field-grade cybersecurity & surge / EMC hardening

---

## ⚠️ Safety Note

This repository does **not** claim real-world deployment readiness. Roadway lighting controllers must satisfy electrical safety, EMC, surge, photometric, cybersecurity, environmental, and road-authority requirements before any field use.

---

<div align="center">

**Built by [Ashkan Aghamoali](https://github.com/iamashkan)** · ⭐ Star the repo if it sparked an idea

</div>
