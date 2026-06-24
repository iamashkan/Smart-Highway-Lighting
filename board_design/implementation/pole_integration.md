# Pole Integration Detail

## Unity Placement

In the Unity 6 project, each `PoleManager` receives:

- Two luminaire cubes with spotlights:
  - `Pxxx-A`
  - `Pxxx-B`
- One `ReLight-X Edge Controller Board` object.
- In the five-node hardware model, five poles each receive their own `RLX-Nxx` edge-node board with local luminaire and sensor telemetry.
- Board model components:
  - weatherproof backplate
  - transparent enclosure cover
  - green PCB
  - STM32 edge MCU or ESP32-S3 lab fallback module
  - 12/24V buck converter
  - 3.3V regulator
  - PWM to RC filter
  - op-amp 0-10V stage
  - DALI/D4i future placeholder
  - terminal blocks
  - sensor headers
  - wireless module and antenna
  - RS485/CAN service connectors
  - status LEDs
  - cable glands

## Real Pole Concept

The board should not replace a certified luminaire driver. It should sit in a serviceable enclosure and command the driver's approved dimming input.

Suggested physical routing:

- Board VIN from pole service power or protected low-voltage supply.
- 0-10V A to Luminaire A dimming input.
- 0-10V B to Luminaire B dimming input.
- Radar mounted with line of sight to lanes.
- Ambient sensor shielded from direct luminaire glare.
- BME280 inside the enclosure for environmental telemetry.
- NTC or DS18B20 temperature sensor placed near driver enclosure or representative thermal location.
- Current sensor placed on controlled LED/driver feed only where safe and permitted.
- Wireless antenna placed outside metal enclosures or with approved feedthrough.

## Safety Position

For demo use, use a small LED module or isolated lab supply. For real roadway equipment, follow the LED driver datasheet, local electrical code, isolation requirements, surge requirements, and road authority rules.
