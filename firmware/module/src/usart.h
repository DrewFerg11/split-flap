// Register-level, interrupt-driven UARTs for the split-flap module (STM32G031).
//   bus: USART1 on PA9/PA10 (remapped from the PA11/PA12 pins), hardware DE on PB3 -> GM3085E
//   dbg: USART2 on PA2/PA3 = J6 pads 6 (TX) / 7 (RX)
// The Arduino core's serial code is compiled out (HAL_UART_MODULE_ONLY) so these own the IRQ handlers.
#pragma once
#include <stdint.h>

void bus_init(uint32_t baud);
int  bus_read();                                   // -1 when empty
void bus_write(const uint8_t *p, uint16_t n);      // blocking; returns after the last stop bit (DE released)

void dbg_init(uint32_t baud);
int  dbg_read();
void dbg_write(const uint8_t *p, uint16_t n);
