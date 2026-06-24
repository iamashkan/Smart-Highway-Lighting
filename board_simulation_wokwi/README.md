# ReLight-X STM32 Board Simulation in Wokwi

This folder is the Wokwi lab prototype for one ReLight-X pole controller node. It now uses an STM32 Blue Pill target and exposes RS485/CAN-style bus activity, dimming outputs, sensors, and manual test/fault controls.

## What This Simulates

- STM32F103C8 pole-node controller.
- Two 0-10V/PWM luminaire channels.
- RS485 direction-enable/TX activity and CAN TX monitor outputs.
- Ambient light input as a BH1750/VEML7700 behavior proxy.
- PIR, ultrasonic distance, and radar slider as vehicle/mmWave presence proxies.
- NTC pole-board temperature.
- Line voltage slider.
- Fault, communication fault, emergency, vehicle A/B, and local test buttons.
- Serial telemetry with mode, dimming voltage, sensor values, current estimate, RS485 frame count, CAN frame count, and fault count.

Wokwi does not model every industrial transceiver or every exact sensor IC internally, so the diagram uses Wokwi-supported controllable parts where they are strongest: STM32 GPIO/ADC/PWM, buttons, sliders, PIR, HC-SR04, NTC, LDR, LEDs, and the logic analyzer.

## Files

- `wokwi.toml`: Wokwi VS Code configuration. Firmware points to `.pio/build/bluepill_f103c8/firmware.bin`.
- `diagram.json`: STM32 Blue Pill board, sensors, test controls, bus LEDs, and logic analyzer.
- `sketch.ino`: standalone STM32 Arduino firmware.
- `platformio.ini`: PlatformIO STM32 build configuration.
- `src/main.cpp`: PlatformIO wrapper that reuses `sketch.ino`.
- `vscode_arduino_intellisense.h`: VS Code IntelliSense-only Arduino/STM32 symbol helper.

## How to Run in VS Code / Wokwi

1. Open this folder in VS Code:

   ```bash
   cd Smart-Highway-Lighting/board_simulation_wokwi
   code .
   ```

2. Build the firmware:

   ```bash
   python3 tools/run_platformio.py run
   ```

   Or use `Terminal -> Run Build Task -> Build Wokwi firmware`.

3. Confirm this file exists:

   ```text
   .pio/build/bluepill_f103c8/firmware.bin
   ```

4. Open `diagram.json` and press the green Wokwi Play button.

If VS Code says `pio: command not found`, run `Terminal -> Run Task -> Install PlatformIO Core`, then build again. The task uses `tools/run_platformio.py`, so it also works without a global `pio` command.

## Test Controls

- `VEH A` or keyboard `A`: simulate a vehicle approaching direction A.
- `VEH B` or keyboard `B`: simulate a vehicle approaching direction B.
- `EMERG` or keyboard `E`: emergency preemption, both luminaires go to 100%.
- `TEST` or keyboard `T`: local dimming sweep.
- `FAULT` or keyboard `F`: forced safe fallback.
- `BUS FAIL` or keyboard `C`: communication fault for RS485/CAN fallback behavior.
- Click the PIR and choose `Simulate Motion`.
- Click the HC-SR04 and move the distance slider below 150 cm to trigger vehicle presence.
- Move the radar potentiometer above about 62% to trigger vehicle presence.
- Move the NTC temperature high to test thermal derating.
- Move the line-voltage slider low to test undervoltage safe mode.

## What to Observe

- Luminaire A/B LEDs stay near 30% at idle.
- Vehicle presence raises the related direction and partially pre-lights the opposite direction.
- Emergency mode raises both directions to full brightness.
- Faults force a safe fallback brightness and blink the STM32 status output.
- RS485/CAN LEDs and the logic analyzer show bus activity during vehicle/fault/test events.
- The serial monitor prints a line like:

  ```text
  node=RLX_STM32_01 mode=adaptive_vehicle pwmA=0.92 pwmB=0.55 ...
  ```

For the real PCB workflow, see `Smart-Highway-Lighting/board_design/implementation/` and `Smart-Highway-Lighting/board_design/pcb_visualization/`.
