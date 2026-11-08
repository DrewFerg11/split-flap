# bringup

Bring-up firmware for the [module board](../../pcb/module-board/) v0.1 (STM32G031, DRV8870, N20 encoder motor,
A3144 hall): checks a newly assembled board before it gets the [module firmware](../module/).
Board design and bring-up log: [DESIGN-1.md](../../pcb/module-board/design/DESIGN-1.md) section 14.

## Flash
ST-Link V2 on the board's J6 pads (left edge, top to bottom): 1 3V3 (leave unconnected), 2 SWDIO, 3 SWCLK, 4 NRST, 5 GND, 6 TX, 7 RX.
Board powered from the bench 12 V on J1 (pin 1 +12V, pin 2 GND).

    pio run -e bringup  -t upload     normal bring-up build
    pio run -e autotest -t upload     same, plus a motor self-test (see below)

**ST-Link driver (Windows):** the V2 clone (USB 0483:3748) needs the WinUSB driver, installed with Zadig, or
OpenOCD says `Error: open failed`. Close CubeProgrammer/CubeIDE first if it still fails. If the device shows as
not present, replug it.

## What it does
- LED (PC15): solid for 8 s after reset (self-test), then a 60 ms blink each second. Solid ~150 ms whenever the
  encoder count changes or the hall sensor is low.
- Motor stays off until commanded. Serial commands (USART2 on J6 pads 6/7, 115200, needs a 3.3 V USB-UART):
  `p` status, `z` zero, `f<pct>` / `r<pct>` run (5..60), `s` stop, `b` brake. Stops on 300 ms of no counts or 3 s.
- `autotest` env: 10 s after reset, 50 % forward 1 s, pause, reverse 1 s. LED reports every 3 s:
  **3 blinks = pass**, 2 = counts run backwards, 1 = no counts.

## Pin map (as built)
PC15 LED (register-driven) | PA0/PA1 TIM2 encoder AF2 | PA6/PA7 TIM3 PWM AF1 -> DRV8870 IN1/IN2 |
PA4 ISEN (ADC, 0.33 ohm) | PA5 hall (low = magnet) | PA2/PA3 USART2.

## Pitfalls found (this Arduino core, `nucleo_g031k8` board)
1. `pinMode(PC_15, ...)` with a raw `PinName` configured the wrong pin. PC15 is driven by GPIOC registers; hall/ISEN use
   `pinNametoDigitalPin()`.
2. `HardwareTimer::setPWM(PA_6/PA_7)` hangs forever in `setMode`. PWM pins are AF-configured by hand.
3. `HardwareTimer::resume()` with no bound pin leaves TIM3 stopped, outputs off: set `TIM3->CCER` and `CR1.CEN` directly.
4. Debug without a UART: halt over SWD and read registers with openocd, e.g.
   `read_memory 0x50000814 32 1` is GPIOC ODR; TIM3 CCR1/2 are 0x40000434/38.

## Known / not done
25 % duty does not start the motor from rest in 1 s (50 % does): the real firmware needs a startup kick.
ISEN reading, RS-485, ENUM chain and bootloader are not written. `PIN_ENC*` etc. are plain constants at the top of `main.cpp`.

Migrated from `split-flap-display-pcb/firmware/ltm-bringup` (env `ltm` renamed `bringup`).
