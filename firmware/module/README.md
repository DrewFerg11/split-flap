# module

Firmware for the [module board](../../pcb/module-board/) (STM32G031): an RS-485 slave that homes on the hall
sensor and goes to flaps (motion logic from the earlier N20 bench sketch). The same project also builds the
**bridge** (a spare board used as the ESP32's RS-485 adapter). Host side: the ESP32 controller (not migrated
yet). Wiring pages: not migrated yet (EPL application).

## Flash (ST-Link on J6 pads 2-5, board on 12 V)

    pio run -e node1  -t upload     module at bus address 1 (node2..node4 for the next ones)
    pio run -e bridge -t upload     the bridge board

**Check after flashing:** a module blinks its address after reset (1 blink = address 1), then a 1 Hz heartbeat.
The bridge shows only the heartbeat, plus flicker while traffic passes.

## Tests

    pio test -e native      unit tests on the PC: protocol (CRC, framing, parser, wire sizes, defaults)
                            and motion maths (flap targets, duties, self-test verdicts, lead learning)

They cover the hardware-free headers [`../shared/sfbus.h`](../shared/sfbus.h) and `include/motion.h`; `src/` (timers, GPIO,
USART) needs a board. CI runs them and builds every board env on each PR (`.github/workflows/firmware.yml`).
Native tests need a host C++ compiler; on Windows without one, run them in Docker from `firmware/`
(it mounts `shared/` too):

    docker run --rm -v "%cd%:/fw" -w /fw/module python:3.12 sh -c "pip install -q platformio && pio test -e native"

## Protocol
[`firmware/shared/sfbus.h`](../shared/sfbus.h) (shared with the controller): 250 kbps, frames `A5 addr cmd len payload crc16`, address 0xFF = broadcast.
Commands: ping, status, stop, home, flap, drive, move, rev, set, get, zero, test, ident.

## Notes
- Settings (`sfbus.h` `KEY_DEFAULTS`) are the N20 bench values: 52 flaps, 10856 counts/rev, fast 40 %,
  slow 20 %, home 25 %. The module keeps them in RAM only. The ESP32 stores them (`save`) and re-sends them
  after a reset.
- **Motor direction** `dir` defaults to 0: every v0.1 board ran backwards with the bench rig's 1
  (2026-10-29). If a drum turns the wrong way (flaps should fall), use `set dir 1` then `save` on the host.
- The drive is slow decay (drive/brake PWM, as the TB6612 on the bench rig did), not the coast PWM that
  the bring-up firmware used, so low duties should start the motor now.
- The `ilim` jam cut-off is off (0) until ISEN has been measured ([DESIGN-1](../../pcb/module-board/design/DESIGN-1.md) §14.1 step 4). ISEN reads about I × duty.
- The Arduino core's Serial is compiled out (`-DHAL_UART_MODULE_ONLY`). `src/usart.cpp` drives USART1/2 by
  register and owns their IRQs.
- ENUM_IN (PB7) is reported in the status. ENUM_OUT isn't driven yet.

## Releases

Tagged `fw/module/vX.Y.Z`; CI builds every env in [`release.toml`](release.toml) from the tagged source
(see [RELEASING](../../.github/RELEASING.md)). Nothing released yet.

Migrated from `split-flap-display-pcb/firmware/ltm-node` at `776fba2` plus its uncommitted `node4` env.
