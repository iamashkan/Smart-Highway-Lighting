# MQTT Protocol

Default broker: `localhost:1883`

Base topic: `relightx`

## Topics

| Topic | Direction | Purpose |
| --- | --- | --- |
| `relightx/pole/{pole_id}/state` | backend to clients | Pole state placeholder |
| `relightx/luminaire/{luminaire_id}/brightness` | backend to Unity/dashboard | Brightness and luminaire state |
| `relightx/luminaire/{luminaire_id}/command` | dashboard/backend to board | Brightness command |
| `relightx/luminaire/{luminaire_id}/health` | backend to clients | Health telemetry |
| `relightx/luminaire/{luminaire_id}/fault` | backend to clients | Fault alert |
| `relightx/zone/{zone_id}/mode` | backend to clients | Eco, normal, emergency, fault, maintenance |
| `relightx/zone/{zone_id}/energy` | backend to clients | Zone energy data |
| `relightx/vehicle/{vehicle_id}/state` | backend to clients | Vehicle state |
| `relightx/system/emergency` | backend to clients | System emergency state |
| `relightx/system/energy` | backend to clients | Total energy state |
| `relightx/passport/{luminaire_id}` | backend to clients | Digital product passport |
| `relightx/board/{board_id}/telemetry` | STM32 node/gateway to backend/dashboard | Board telemetry |
| `relightx/board/{board_id}/command` | backend/dashboard to STM32 node/gateway | Board command |

## Brightness State Payload

```json
{
  "luminaire_id": "P001-A",
  "pole_id": "P001",
  "direction": "A",
  "current_brightness": 0.66,
  "target_brightness": 1.0,
  "max_power_watts": 160.0,
  "dimming_protocol": "simulated_pwm_0_10v",
  "health_score": 98.0,
  "driver_temperature": 43.4,
  "fault_status": "ok",
  "rex_status": "Reuse"
}
```

## Board Command Payload

```json
{
  "board_id": "board-001",
  "luminaire_id": "P001-A",
  "brightness": 0.75,
  "source": "backend_or_dashboard",
  "safe_fallback_brightness": 0.7
}
```

## Board Telemetry Payload

```json
{
  "board_id": "board-001",
  "luminaire_id": "P001-A",
  "brightness": 0.75,
  "pwm_duty_cycle": 0.75,
  "simulated_output_voltage": 7.5,
  "driver_temperature": 45.5,
  "current_ma": 755.0,
  "communication_health": "ok",
  "fault_status": "ok"
}
```

## Notes

The backend can run without MQTT. When `--mqtt` is not passed, it executes all control, energy, health, and passport logic offline.
