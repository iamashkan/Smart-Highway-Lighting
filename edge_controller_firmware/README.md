# ReLight-X ESP32 Edge Controller Firmware

This PlatformIO firmware is a lab prototype for the ReLight-X Edge Controller Board.

It connects to Wi-Fi, subscribes to MQTT brightness commands, drives two PWM outputs that represent the two roadway luminaires on a pole, and publishes simulated board telemetry for hardware-in-the-loop testing.

## Commands

- Board command: `relightx/board/{board_id}/command`
- Luminaire command: `relightx/luminaire/{luminaire_id}/command`

Example payload:

```json
{
  "board_id": "board-001",
  "luminaire_id": "P001-A",
  "brightness": 0.75
}
```

## Outputs

- `GPIO18`: Luminaire A PWM
- `GPIO19`: Luminaire B PWM
- `GPIO2`: status LED

The PWM output can drive a small LED through a suitable resistor or feed the documented RC filter plus op-amp 0-10V dimming circuit. Do not connect ESP32 pins directly to a real roadway luminaire dimming input without the interface circuit and driver datasheet validation.

## Test Path

1. Run an MQTT broker, for example Mosquitto.
2. Update `WIFI_SSID`, `WIFI_PASSWORD`, and `MQTT_HOST` in `src/main.cpp`.
3. Flash with `pio run -t upload`.
4. Run the backend with `python -m backend.main --scenario normal_car_direction_a --mqtt`.
5. Watch telemetry on `relightx/board/board-001/telemetry`.
