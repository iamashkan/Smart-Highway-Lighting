# System Architecture

ReLight-X separates the control brain, digital twin, edge controller, and lifecycle intelligence so each part can be tested independently.

## Full System

```mermaid
flowchart LR
  Unity["Unity 3D digital twin"] <--> MQTT["MQTT broker"]
  Dashboard["Streamlit dashboard"] <--> MQTT
  Backend["Python backend control brain"] <--> MQTT
  NODE["STM32 edge controller node / gateway bridge"] <--> MQTT
  NODE --> PWM["PWM / simulated 0-10V dimming"]
  PWM --> Luminaire["LED roadway luminaire driver"]
  Radar["mmWave radar"] --> NODE
  Ambient["Ambient light sensor"] --> NODE
  Temp["Temperature sensor"] --> NODE
  Current["Current sensor"] --> NODE
  Backend --> Energy["Energy model"]
  Backend --> Health["Health model"]
  Backend --> Passport["Digital product passports"]
  Passport --> Rex["Reuse / Repair / Remanufacture / Recycle"]
```

## MQTT Data Flow

```mermaid
sequenceDiagram
  participant DT as Unity Digital Twin
  participant BE as Python Backend
  participant MQ as MQTT Broker
  participant NODE as STM32 Node
  participant UI as Streamlit Dashboard

  BE->>MQ: relightx/luminaire/{id}/brightness
  MQ->>DT: brightness and health state
  MQ->>UI: energy, mode, passport state
  BE->>MQ: relightx/board/{id}/command
  MQ->>NODE: brightness command
  NODE->>MQ: relightx/board/{id}/telemetry
  MQ->>BE: board telemetry
  MQ->>UI: board telemetry
```

## Control Flow

```mermaid
flowchart TD
  Start["Vehicle or sensor update"] --> Detect["Detect nearest pole and direction"]
  Detect --> Emergency{"Emergency type?"}
  Emergency -- yes --> EmergencyZones["Full active A/B direction to 100%"]
  Emergency -- no --> Wave["Calculate direction-only sequential lighting wave"]
  Wave --> Smooth["Smooth fade toward targets"]
  EmergencyZones --> Smooth
  Smooth --> Fault{"Fault detected?"}
  Fault -- yes --> Fallback["Safe fallback brightness, alert, passport log"]
  Fault -- no --> Energy["Energy and health update"]
  Fallback --> Energy
  Energy --> Publish["Publish MQTT state and dashboard data"]
```

## Emergency Mode

```mermaid
flowchart LR
  EV["Ambulance / police / fire truck"] --> Zone["Find active A/B direction"]
  Zone --> Previous["Previous safety zone"]
  Zone --> Current["Current zone"]
  Zone --> Next1["Next zone"]
  Zone --> Next2["Second next zone"]
  Previous --> Full["100% brightness in emergency direction"]
  Current --> Full
  Next1 --> Full
  Next2 --> Full
  Full --> Exit["Hold until vehicle exits controlled area"]
  Exit --> Fade["Fade back to eco brightness"]
```

## Hardware-in-the-Loop

```mermaid
flowchart LR
  Backend["Python scenario runner"] --> MQTT["MQTT broker"]
  MQTT --> NODE["STM32 node or gateway bridge"]
  NODE --> Scope["Oscilloscope / multimeter"]
  NODE --> LED["Small LED module"]
  NODE --> MQTT
  MQTT --> Dashboard["Streamlit Board Test page"]
  MQTT --> Unity["Unity brightness visualization"]
```

## Digital Passport and Re-X

```mermaid
flowchart TD
  Telemetry["Brightness, current, temperature, faults"] --> Health["Health score"]
  Health --> RUL["Remaining useful life estimate"]
  Telemetry --> Passport["Digital product passport"]
  RUL --> Passport
  Passport --> Decision{"Rule-based Re-X decision"}
  Decision --> Reuse["Reuse"]
  Decision --> Repair["Repair"]
  Decision --> Remanufacture["Remanufacture"]
  Decision --> Recycle["Recycle"]
```
