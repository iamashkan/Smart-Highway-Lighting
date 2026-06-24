# Board-Level Test Plan

## Bring-Up

1. Verify 12V/24V input polarity protection path with current-limited bench supply.
2. Measure 5V buck output and 3.3V regulator output without the STM32 fitted.
3. Flash the STM32 firmware and confirm serial boot messages.
4. Confirm gateway/wireless, RS485, or CAN connection status depending on the prototype stage.

## PWM Output Test

1. Send `{"brightness": 0.30}` to `relightx/board/board-001/command`.
2. Measure PWM duty cycle on the STM32 timer PWM pins used for luminaire channels A and B.
3. Repeat for 0.70 and 1.00 brightness.
4. Confirm firmware enters safe fallback at 0.70 if MQTT is disconnected.

## 0-10V Circuit Test

1. Connect PWM output to RC filter and op-amp stage.
2. Verify approximate analog outputs:
   - 30% command -> 3.0V
   - 70% command -> 7.0V
   - 100% command -> 10.0V
3. Confirm output is stable enough for the selected LED driver dimming input.
4. Add protection and isolation review before connecting to real luminaires.

## Sensor Test

1. Confirm radar UART packets are received or simulated.
2. Confirm ambient light reading changes under a flashlight/covered sensor test.
3. Confirm current sensor reading tracks LED load changes.
4. Heat the temperature sensor gently and confirm telemetry changes.

## HIL Demo Test

1. Run Mosquitto.
2. Run `python -m backend.main --scenario emergency_ambulance_direction_a --mqtt`.
3. Flash the STM32 Wokwi or hardware node and watch PWM channel A move to emergency brightness.
4. Open `streamlit run dashboard/app.py` and view board telemetry.
5. Open Unity scene and confirm the same luminaires visualize the MQTT state.

## Five-Node Network Test

1. Review `implementation/five_node_network_architecture.md`.
2. Run:
   ```bash
   python3 board_design/simulation/five_node_network_sim.py --steps 30 --print-final
   ```
3. Confirm `data/runs/five_node_board_network.json` contains five board nodes.
4. Confirm each node reports vehicle detection, ambient lux, driver temperature, enclosure temperature, current draw, brightness, wireless RSSI, RS485 health, CAN health, and fault status.
5. Confirm the simulated vehicle causes upstream pre-lighting, peak brightness under the active pole, then fade-to-eco behavior.
