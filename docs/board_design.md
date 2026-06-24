# Board Design

The board deliverables live in `board_design/`.

Included:

- `README.md`: board architecture and 0-10V/DALI notes.
- `bom.csv`: practical component list.
- `pin_mapping.csv`: STM32-first pin mapping with ESP32 lab fallback notes.
- `../board_simulation_wokwi/`: STM32 Blue Pill Wokwi simulation with RS485/CAN and sensor test controls.
- `five_node_board_map.csv`: five pole-node mapping with sensors, wireless, and fault behavior.
- `test_plan.md`: bring-up, PWM, 0-10V, sensor, and HIL validation.
- `kicad_placeholders/`: minimal KiCad project placeholders.
- `implementation/five_node_network_architecture.md`: STM32 plus wireless plus RS485/CAN multi-board plan.

## Practical Retrofit Position

The edge board is intended to sit between sensing/control infrastructure and the luminaire dimming input. For lab work, PWM can drive a small LED or RC/op-amp test circuit. For real luminaires, the dimming interface must be validated against the exact LED driver datasheet.

## Future DALI/D4i Path

The prototype does not implement DALI. Future work should use certified DALI/D4i interface hardware, bus power design, isolation where required, and a tested protocol stack.
