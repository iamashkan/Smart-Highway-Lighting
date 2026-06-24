# PCB Layout Guide

## Proposed Board Size

- Lab PCB: 95 mm x 65 mm.
- Four M3 mounting holes.
- Keep the certified wireless module antenna at the board edge with a copper keepout.
- Put high-current/power entry and protection close to input connector.
- Keep analog 0-10V traces away from switching regulator noise.

## Placement

```text
+---------------------------------------------------+
| antenna keepout | STM32 + radio  | 12/24V input   |
|                 |                | fuse + TVS     |
| radar UART      | I2C sensors    | buck converter |
| ADC current     | status LEDs    | 3.3V regulator |
| DALI future     | op-amp 0-10V   | terminal blocks|
| placeholder     | RC filters     | DIM A / DIM B  |
+---------------------------------------------------+
```

## Routing Rules

- Use wider traces for input power and dimming common return.
- Add ground pour with clear analog/digital return strategy.
- Keep buck converter loop compact.
- Place RC filter and op-amp close to dimming terminals.
- Route PWM away from sensor lines where possible.
- Add test pads:
  - 24V input.
  - 5V.
  - 3.3V.
  - PWM A/B.
  - analog 0-10V A/B.
  - UART RX/TX.

## Mechanical Notes

- Place terminal blocks at the enclosure cable-gland side.
- Leave enough finger access for screw terminals.
- Add silkscreen labels matching Unity 3D model labels:
  - VIN
  - PWM A
  - PWM B
  - 0-10V A
  - 0-10V B
  - DALI future
  - mmWave UART
  - I2C sensors
  - current
  - fault

## Manufacturing Note

Do not fabricate from the placeholder KiCad files. Use this guide to create a real schematic and layout, then run ERC/DRC and peer review before ordering boards.
