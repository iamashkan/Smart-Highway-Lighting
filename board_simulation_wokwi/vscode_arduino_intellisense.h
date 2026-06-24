#pragma once

#include <math.h>
#include <stddef.h>
#include <stdint.h>

#ifndef HIGH
#define HIGH 0x1
#endif

#ifndef LOW
#define LOW 0x0
#endif

#ifndef INPUT
#define INPUT 0x0
#endif

#ifndef OUTPUT
#define OUTPUT 0x1
#endif

#ifndef INPUT_PULLUP
#define INPUT_PULLUP 0x2
#endif

#define PA0 0
#define PA1 1
#define PA2 2
#define PA3 3
#define PA4 4
#define PA5 5
#define PA6 6
#define PA7 7
#define PA11 11
#define PA12 12
#define PB0 20
#define PB1 21
#define PB6 26
#define PB7 27
#define PB8 28
#define PB9 29
#define PB10 30
#define PB12 32
#define PB13 33
#define PB14 34
#define PB15 35
#define PC13 53

template <typename T>
T constrain(T value, T low, T high) {
  return value < low ? low : (value > high ? high : value);
}

class HardwareSerial {
public:
  void begin(unsigned long baud) {}

  size_t print(const char *value) { return 0; }
  size_t print(char value) { return 0; }
  size_t print(int value) { return 0; }
  size_t print(unsigned int value) { return 0; }
  size_t print(long value) { return 0; }
  size_t print(unsigned long value) { return 0; }
  size_t print(float value, int digits = 2) { return 0; }
  size_t print(double value, int digits = 2) { return 0; }

  size_t println() { return 0; }
  size_t println(const char *value) { return 0; }
  size_t println(char value) { return 0; }
  size_t println(int value) { return 0; }
  size_t println(unsigned int value) { return 0; }
  size_t println(long value) { return 0; }
  size_t println(unsigned long value) { return 0; }
  size_t println(float value, int digits = 2) { return 0; }
  size_t println(double value, int digits = 2) { return 0; }
};

extern HardwareSerial Serial;

void pinMode(int pin, int mode);
int digitalRead(int pin);
void digitalWrite(int pin, int value);
int analogRead(int pin);
void analogWrite(int pin, int value);
unsigned long millis();
void delay(unsigned long ms);
void delayMicroseconds(unsigned int us);
unsigned long pulseIn(int pin, int value, unsigned long timeout = 1000000UL);
