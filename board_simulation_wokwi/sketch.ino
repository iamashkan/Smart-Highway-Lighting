#if defined(__INTELLISENSE__)
#include "vscode_arduino_intellisense.h"
#else
#include <Arduino.h>
#endif
#include <math.h>

// ReLight-X STM32 pole-node simulation.
// Wokwi uses sensors/buttons as controllable lab inputs for the future PCB.
const int PWM_A_PIN = PB6;
const int PWM_B_PIN = PB7;
const int STATUS_LED_PIN = PC13;
const int FAULT_LED_PIN = PB8;
const int BUS_LED_PIN = PB9;

const int RS485_DE_PIN = PB14;
const int RS485_TX_PIN = PB15;
const int CAN_TX_PIN = PA11;
const int CAN_RX_PIN = PA12;

const int AMBIENT_LDR_PIN = PA0;
const int RADAR_PROXY_PIN = PA1;
const int TEMP_NTC_PIN = PA2;
const int LINE_VOLTAGE_PIN = PA3;

const int FAULT_BUTTON_PIN = PA4;
const int TEST_BUTTON_PIN = PA5;
const int VEHICLE_A_BUTTON_PIN = PA6;
const int VEHICLE_B_BUTTON_PIN = PA7;
const int EMERGENCY_BUTTON_PIN = PB0;
const int BUS_FAULT_BUTTON_PIN = PB1;

const int PIR_PIN = PB10;
const int ULTRASONIC_TRIG_PIN = PB12;
const int ULTRASONIC_ECHO_PIN = PB13;

const float IDLE_BRIGHTNESS = 0.30f;
const float VEHICLE_BRIGHTNESS = 0.92f;
const float EMERGENCY_BRIGHTNESS = 1.00f;
const float SAFE_FALLBACK_BRIGHTNESS = 0.70f;
const float SMOOTH_STEP = 0.035f;

float brightnessA = IDLE_BRIGHTNESS;
float brightnessB = IDLE_BRIGHTNESS;
float targetA = IDLE_BRIGHTNESS;
float targetB = IDLE_BRIGHTNESS;

unsigned long holdAUntil = 0;
unsigned long holdBUntil = 0;
unsigned long emergencyUntil = 0;
unsigned long lastTelemetry = 0;
unsigned long lastBusBlink = 0;
uint16_t rs485FrameCounter = 0;
uint16_t canFrameCounter = 0;

int ambientRaw = 0;
int radarRaw = 0;
int tempRaw = 0;
int lineRaw = 0;
int distanceCm = 400;
float temperatureC = 24.0f;
float lineVoltage = 24.0f;
bool pirMotion = false;
bool forcedFault = false;
bool commsFault = false;
bool overTemperature = false;
bool underVoltage = false;
bool localTest = false;
bool emergencyMode = false;
bool vehicleAActive = false;
bool vehicleBActive = false;

float clamp01(float value) {
  if (value < 0.0f) {
    return 0.0f;
  }
  if (value > 1.0f) {
    return 1.0f;
  }
  return value;
}

float maxf(float a, float b) {
  return a > b ? a : b;
}

int analogDuty(float brightness) {
  return (int)(clamp01(brightness) * 255.0f + 0.5f);
}

bool buttonPressed(int pin) {
  return digitalRead(pin) == LOW;
}

float analogNorm(int raw) {
  return clamp01(raw / 1023.0f);
}

float ntcToCelsius(int raw) {
  int value = raw;
  if (value < 1) {
    value = 1;
  } else if (value > 1022) {
    value = 1022;
  }

  const float beta = 3950.0f;
  return 1.0f / (log(1.0f / (1023.0f / value - 1.0f)) / beta + 1.0f / 298.15f) - 273.15f;
}

int readDistanceCm() {
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 30000UL);
  if (duration == 0) {
    return 400;
  }
  int cm = (int)(duration / 58UL);
  if (cm < 2) {
    return 2;
  }
  if (cm > 400) {
    return 400;
  }
  return cm;
}

void readInputs() {
  ambientRaw = analogRead(AMBIENT_LDR_PIN);
  radarRaw = analogRead(RADAR_PROXY_PIN);
  tempRaw = analogRead(TEMP_NTC_PIN);
  lineRaw = analogRead(LINE_VOLTAGE_PIN);

  pirMotion = digitalRead(PIR_PIN) == HIGH;
  distanceCm = readDistanceCm();
  temperatureC = ntcToCelsius(tempRaw);
  lineVoltage = 18.0f + analogNorm(lineRaw) * 12.0f;

  forcedFault = buttonPressed(FAULT_BUTTON_PIN);
  localTest = buttonPressed(TEST_BUTTON_PIN);
  commsFault = buttonPressed(BUS_FAULT_BUTTON_PIN);
  overTemperature = temperatureC > 70.0f;
  underVoltage = lineVoltage < 20.0f;

  unsigned long now = millis();
  bool radarPresence = analogNorm(radarRaw) > 0.62f;
  bool ultrasonicPresence = distanceCm < 150;
  if (buttonPressed(VEHICLE_A_BUTTON_PIN) || radarPresence || pirMotion || ultrasonicPresence) {
    holdAUntil = now + 4500UL;
  }
  if (buttonPressed(VEHICLE_B_BUTTON_PIN)) {
    holdBUntil = now + 4500UL;
  }
  if (buttonPressed(EMERGENCY_BUTTON_PIN)) {
    emergencyUntil = now + 6500UL;
  }

  vehicleAActive = now < holdAUntil;
  vehicleBActive = now < holdBUntil;
  emergencyMode = now < emergencyUntil;
}

void computeTargets() {
  targetA = IDLE_BRIGHTNESS;
  targetB = IDLE_BRIGHTNESS;

  if (vehicleAActive) {
    targetA = VEHICLE_BRIGHTNESS;
    targetB = maxf(targetB, 0.55f);
  }
  if (vehicleBActive) {
    targetB = VEHICLE_BRIGHTNESS;
    targetA = maxf(targetA, 0.55f);
  }
  if (emergencyMode) {
    targetA = EMERGENCY_BRIGHTNESS;
    targetB = EMERGENCY_BRIGHTNESS;
  }

  bool safeFallback = forcedFault || commsFault || overTemperature || underVoltage;
  if (safeFallback) {
    targetA = maxf(targetA, SAFE_FALLBACK_BRIGHTNESS);
    targetB = maxf(targetB, SAFE_FALLBACK_BRIGHTNESS);
  }

  if (localTest) {
    float phase = (millis() % 5000UL) / 5000.0f;
    targetA = 0.30f + phase * 0.70f;
    targetB = 1.00f - phase * 0.70f;
  }
}

float smoothToward(float current, float target) {
  if (current < target - SMOOTH_STEP) {
    return current + SMOOTH_STEP;
  }
  if (current > target + SMOOTH_STEP) {
    return current - SMOOTH_STEP;
  }
  return target;
}

void writeOutputs() {
  brightnessA = smoothToward(brightnessA, targetA);
  brightnessB = smoothToward(brightnessB, targetB);

  analogWrite(PWM_A_PIN, analogDuty(brightnessA));
  analogWrite(PWM_B_PIN, analogDuty(brightnessB));

  bool anyFault = forcedFault || commsFault || overTemperature || underVoltage;
  digitalWrite(FAULT_LED_PIN, anyFault ? HIGH : LOW);
  digitalWrite(STATUS_LED_PIN, anyFault ? ((millis() / 180UL) % 2UL ? HIGH : LOW) : LOW);
}

void writeBusActivity() {
  unsigned long now = millis();
  bool busActive = vehicleAActive || vehicleBActive || emergencyMode || localTest || forcedFault || commsFault;
  if (!busActive || now - lastBusBlink < 220UL) {
    if (!busActive) {
      digitalWrite(RS485_DE_PIN, LOW);
      digitalWrite(RS485_TX_PIN, LOW);
      digitalWrite(CAN_TX_PIN, LOW);
      digitalWrite(BUS_LED_PIN, LOW);
    }
    return;
  }

  lastBusBlink = now;
  rs485FrameCounter++;
  canFrameCounter++;

  digitalWrite(RS485_DE_PIN, HIGH);
  digitalWrite(RS485_TX_PIN, HIGH);
  digitalWrite(CAN_TX_PIN, !commsFault ? HIGH : LOW);
  digitalWrite(BUS_LED_PIN, HIGH);
  delay(16);
  digitalWrite(RS485_TX_PIN, LOW);
  digitalWrite(CAN_TX_PIN, LOW);
  digitalWrite(BUS_LED_PIN, LOW);
  digitalWrite(RS485_DE_PIN, LOW);
}

const char *modeName() {
  if (forcedFault) {
    return "forced_fault";
  }
  if (commsFault) {
    return "rs485_can_fault";
  }
  if (overTemperature) {
    return "thermal_derate";
  }
  if (underVoltage) {
    return "undervoltage_safe";
  }
  if (emergencyMode) {
    return "emergency_preempt";
  }
  if (localTest) {
    return "local_test_sweep";
  }
  if (vehicleAActive || vehicleBActive) {
    return "adaptive_vehicle";
  }
  return "idle_30_percent";
}

void printTelemetry() {
  if (millis() - lastTelemetry < 1000UL) {
    return;
  }
  lastTelemetry = millis();

  float currentA = 80.0f + brightnessA * 900.0f;
  float currentB = 80.0f + brightnessB * 900.0f;

  Serial.print("node=RLX_STM32_01 mode=");
  Serial.print(modeName());
  Serial.print(" pwmA=");
  Serial.print(brightnessA, 2);
  Serial.print(" pwmB=");
  Serial.print(brightnessB, 2);
  Serial.print(" outputA_V=");
  Serial.print(brightnessA * 10.0f, 2);
  Serial.print(" outputB_V=");
  Serial.print(brightnessB * 10.0f, 2);
  Serial.print(" ambientRaw=");
  Serial.print(ambientRaw);
  Serial.print(" radarRaw=");
  Serial.print(radarRaw);
  Serial.print(" pir=");
  Serial.print(pirMotion ? 1 : 0);
  Serial.print(" distanceCm=");
  Serial.print(distanceCm);
  Serial.print(" tempC=");
  Serial.print(temperatureC, 1);
  Serial.print(" lineV=");
  Serial.print(lineVoltage, 1);
  Serial.print(" currentA_mA=");
  Serial.print(currentA, 0);
  Serial.print(" currentB_mA=");
  Serial.print(currentB, 0);
  Serial.print(" rs485Frames=");
  Serial.print(rs485FrameCounter);
  Serial.print(" canFrames=");
  Serial.print(canFrameCounter);
  Serial.print(" faults=");
  Serial.print((forcedFault ? 1 : 0) + (commsFault ? 1 : 0) + (overTemperature ? 1 : 0) + (underVoltage ? 1 : 0));
  Serial.println();
}

void setup() {
  Serial.begin(115200);

  pinMode(PWM_A_PIN, OUTPUT);
  pinMode(PWM_B_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(FAULT_LED_PIN, OUTPUT);
  pinMode(BUS_LED_PIN, OUTPUT);
  pinMode(RS485_DE_PIN, OUTPUT);
  pinMode(RS485_TX_PIN, OUTPUT);
  pinMode(CAN_TX_PIN, OUTPUT);
  pinMode(CAN_RX_PIN, INPUT_PULLUP);

  pinMode(FAULT_BUTTON_PIN, INPUT_PULLUP);
  pinMode(TEST_BUTTON_PIN, INPUT_PULLUP);
  pinMode(VEHICLE_A_BUTTON_PIN, INPUT_PULLUP);
  pinMode(VEHICLE_B_BUTTON_PIN, INPUT_PULLUP);
  pinMode(EMERGENCY_BUTTON_PIN, INPUT_PULLUP);
  pinMode(BUS_FAULT_BUTTON_PIN, INPUT_PULLUP);
  pinMode(PIR_PIN, INPUT);
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);

  writeOutputs();
  Serial.println("ReLight-X STM32 + RS485/CAN Wokwi node ready");
}

void loop() {
  readInputs();
  computeTargets();
  writeOutputs();
  writeBusActivity();
  printTelemetry();
  delay(35);
}
