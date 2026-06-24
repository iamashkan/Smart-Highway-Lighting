# Five-Node Board Demo Guide

This guide shows how to implement and view the five-board ReLight-X hardware concept in the current project.

## What Works Now

- A five-node board architecture is documented in `board_design/implementation/five_node_network_architecture.md`.
- Five boards are mapped in `board_design/five_node_board_map.csv`.
- A Python simulation generates board telemetry for five pole nodes.
- The Streamlit dashboard has a `Board Network` page that visualizes the five boards, brightness, sensor values, wireless RSSI, RS485/CAN health, and faults.
- Wokwi simulates one STM32 pole node with RS485/CAN indicators and sensor/fault test controls.
- KiCad placeholder files document what must be turned into a fabrication-ready STM32 PCB.

## Quick Demo

From the project root:

```bash
cd Smart-Highway-Lighting
source .venv/bin/activate
python tools/run_board_network_demo.py
```

Then open:

```text
http://127.0.0.1:8501
```

In the dashboard sidebar, select:

```text
Board Network
```

## Manual Commands

Generate five-node telemetry:

```bash
python board_design/simulation/five_node_network_sim.py --steps 30 --print-final
```

Start the dashboard:

```bash
streamlit run dashboard/app.py
```

Output data:

```text
data/runs/five_node_board_network.json
```

## What You Should See

The `Board Network` page shows:

- five board nodes `RLX-N01` to `RLX-N05`
- one pole and luminaire per node
- target brightness per board
- vehicle detection state
- ambient lux from VEML7700/BH1750 concept
- driver/enclosure temperature from NTC/DS18B20/BME280 concept
- current draw
- wireless RSSI
- RS485 and CAN health flags
- fault state such as `wireless_rssi_low` or `thermal_watch`

## Real Hardware Implementation Path

Build in this order:

1. Single lab node on a dev board:
   - STM32 Blue Pill, Nucleo, or Discovery board
   - one PWM output
   - one LED or 0-10V dimming test circuit
   - VEML7700/BH1750 on I2C
   - BME280 on I2C/SPI
   - NTC or DS18B20 temperature sensor
   - current sensor module
   - mmWave radar module
2. Add industrial buses:
   - isolated RS485 transceiver for Modbus RTU/service
   - CAN/CAN FD transceiver for local deterministic bus
3. Add wireless:
   - certified radio module selected for your region and deployment range
   - gateway connected to dashboard/backend
4. Duplicate into five nodes:
   - assign `RLX-N01` to `RLX-N05`
   - connect each node to one luminaire/driver
   - validate neighbor pre-lighting and fallback behavior
5. Move to PCB:
   - create real KiCad schematic from the placeholder notes
   - run ERC/DRC
   - review isolation, surge, enclosure, thermal, and EMC constraints

## Single-Node Wokwi Test

From the Wokwi folder:

```bash
cd Smart-Highway-Lighting/board_simulation_wokwi
python3 tools/run_platformio.py run
```

Then open `diagram.json` in VS Code and press the Wokwi Play button. Use `A`, `B`, `E`, `T`, `F`, and `C` to test vehicle direction, emergency, sweep test, forced fault, and RS485/CAN communication fault.

## Important Limit

This is a research/lab prototype. A real roadway system needs certified luminaire interfaces, surge/EMC design, electrical safety review, secure wireless communication, environmental testing, and authority approval.
