# KiCad Placeholder Notes

This folder intentionally contains a minimal KiCad project placeholder rather than a fabrication-ready PCB.

Before fabrication, create a reviewed schematic with:

- STM32 MCU power, clock, reset, SWD programming, boot pins, and debug connector.
- ESP32/ESP32-S3 module only if keeping the lab fallback version.
- 12V/24V input protection, fuse, TVS, reverse polarity protection, and buck converter.
- Sensor headers with ESD protection and level compatibility for mmWave radar, VEML7700/BH1750, BME280, NTC/DS18B20, and current sensing.
- Isolated RS485 transceiver footprint for Modbus RTU/service bus.
- CAN/CAN FD transceiver footprint for deterministic local bus or wired fallback.
- Wireless module footprint and antenna keepout/feedthrough.
- PWM-to-0-10V RC filter and op-amp scaling with measured ripple.
- Isolated or compliant DALI/D4i interface if DALI/D4i is implemented.
- Creepage, clearance, enclosure, thermal, and surge review for roadside use.
