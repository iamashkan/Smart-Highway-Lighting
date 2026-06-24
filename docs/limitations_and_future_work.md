# Limitations and Future Work

## Current Limitations

- The project uses simulated vehicle detection and simulated sensor readings.
- No trained emergency vehicle computer vision model is included.
- No real roadway luminaire, DALI bus, or D4i socket is controlled by default.
- The KiCad files are placeholders, not fabrication-ready designs.
- The energy, health, and RUL models are transparent approximations for research demonstration.
- Unity scripts are provided as scene-ready components, not a full committed Unity project with binary scene assets.

## Future Work

- Integrate real mmWave radar packets into the STM32 firmware.
- Connect an edge AI camera module and implement real emergency vehicle classification.
- Add a certified DALI/D4i interface and protocol stack.
- Validate against a real dimmable LED driver in a controlled lab.
- Calibrate energy and thermal models using measured luminaire data.
- Add cybersecurity hardening for MQTT authentication, TLS, and device identity.
- Add deployment-grade enclosure, environmental, surge, EMC, and electrical safety design.
- Extend the digital passport with OEM-provided bill of materials and maintenance records.
- Add optional ROS2/Gazebo support for robotics-style simulation experiments.
