// Module firmware, bridge build: a spare module board used as a 3.3 V serial <-> RS-485 adapter.
// Bytes from J6 (USART2, from the ESP32) go out on the bus; bytes from the bus go back to J6.
// Same baud both sides, so it is a plain byte copy; the GM3085E's DE is driven by USART1 hardware.
// ENUM_OUT (PB9) is held high, so the board plugged into its J2 is the head of the row for the ENUM chain.
// LED: 1 Hz heartbeat, lit while traffic passes.
#ifdef SFBUS_BRIDGE
#include <Arduino.h>
#include "sfbus.h"
#include "usart.h"

static void ledInit() { __HAL_RCC_GPIOC_CLK_ENABLE(); GPIOC->MODER = (GPIOC->MODER & ~(3u << 30)) | (1u << 30); }
static void ledSet(bool on) { GPIOC->BSRR = on ? (1u << 15) : (1u << 31); }

void setup() {
  ledInit();
  __HAL_RCC_GPIOB_CLK_ENABLE();                // PB9 ENUM_OUT high: board 1's ENUM_IN
  GPIOB->BSRR = 1u << 9;
  GPIOB->MODER = (GPIOB->MODER & ~(3u << 18)) | (1u << 18);
  bus_init(sfbus::BAUD);
  dbg_init(sfbus::BAUD);
}

void loop() {
  static uint32_t ledUntil = 0;
  uint8_t buf[32];
  uint16_t n = 0;
  int b;

  while (n < sizeof buf && (b = dbg_read()) >= 0) buf[n++] = b;
  if (n) { bus_write(buf, n); ledUntil = millis() + 30; }

  n = 0;
  while (n < sizeof buf && (b = bus_read()) >= 0) buf[n++] = b;
  if (n) { dbg_write(buf, n); ledUntil = millis() + 30; }

  uint32_t now = millis();
  ledSet(now < ledUntil || (now % 1000) < 60);
}
#endif
