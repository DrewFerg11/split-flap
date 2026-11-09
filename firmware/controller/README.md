# controller

The default controller: an ESP32 that drives [module boards](../module/) over the RS-485 bus, with a
serial console for bench work (calibrating, testing and running modules by hand). Every application
builds on the same library.

| Part | What |
|---|---|
| [`lib/sfctl/`](lib/sfctl/src/sfctl.h) | the controller library: bus requests and replies, scan, module status, each module's settings kept on the ESP32 and re-sent after it resets, calibration |
| [`lib/sfctl_core/`](lib/sfctl_core/src/calib.h) | hardware-free calibration maths (unit-tested) |
| [`src/console.cpp`](src/console.cpp) | the serial console on top of `sfctl` |
| [`../shared/sfbus.h`](../shared/sfbus.h) | the bus protocol, shared with the module firmware |

## Boards and wiring

| Env | Board | Bus UART | Console |
|---|---|---|---|
| `esp32dev` (default) | ESP32-WROOM DevKit V1 | UART2: RX GPIO16, TX GPIO17 | USB-serial bridge |
| `s3` | ESP32-S3 | UART1: RX GPIO5, TX GPIO6 | native USB (port marked USB) |
| `c3` | ESP32-C3 Super Mini | UART1: RX GPIO5, TX GPIO6 | native USB |

DE+RE is GPIO4 on all three, for a MAX3485 adapter; unused with the bridge board (a spare module board
flashed with the module's `bridge` env, wired to its J6 pads 5-7). Wiring pages:
[`wiring/bench-max3485.html`](wiring/bench-max3485.html) (MAX3485 adapter) and
[`wiring/bench-bridge.html`](wiring/bench-bridge.html) (bridge board); open them in a browser.

    pio run -e c3 -t upload        build + flash (your board's env)
    pio device monitor -e c3       console, then type ? for commands

The serial port is autodetected; add `upload_port` / `monitor_port` to an env to pin one. At boot it places
the modules (below) and selects the first one.

## Placing modules (ENUM chain)

Boards flashed with the module's `node` env have no address of their own; `enum` (and boot) gives them 1, 2, 3...
in order along the row. Wire the ESP's **ENUM pin to pin 5 of the row's plug** (the first board's right-edge
header; its `ENUM_IN`), on top of the usual bus wires and a common GND:

| Env | ENUM pin |
|---|---|
| `esp32dev` | GPIO18 |
| `s3`, `c3` | GPIO7 |

It is a 3.3 V logic signal: never 12 V. `Pins.enumHead = -1` turns the pin off if you tie pin 5 to 3.3 V instead.
Output lists each module's address and its position in the row (0 = next to the plug).

## First run, one module

    scan            -> [1] fw 1 uid ...        (nothing found: see the hint it prints)
    id              module 1's LED blinks fast for 3 s
    test            PASS = motor and encoder agree
    d 20            watch which way the drum turns; flaps should fall. Then: d 0
                    wrong way? set dir 1 (default 0)
    home            runs to the magnet
    f 1             one flap on; prints the error in counts
    cycle           steps through every flap, 1 s each (x stops)

## Calibrating a module (new motor or drum)

    cal             homes 4 times; each hall-to-hall rev gives counts/rev -> sets cpr
                    (also scales zone/dzone/lead/foff, which are in counts)
    f 0             go to flap 0
    go 20           nudge forward until flap 0 sits right (forward only; overshoot = go round again)
    here 0          "this is flap 0" -> sets foff
    cycle           check every flap; the brake lead self-tunes over the first moves

Prefix any command with an address (`2 home`) or `*` for all modules (`* f 0`). A bare `x` stops
everything.

## Settings

Module settings live on the ESP32 (flash namespace `ltmhost`, kept from the pre-migration bench
controller so stored settings survive the update). `set`, `here` and `cal` store them straight away;
`save` also stores the learned brake lead. A module that resets comes back on its compiled defaults
and gets its stored settings pushed before the next command. They're lost if the ESP32 is swapped,
so module defaults that every board needs belong in the module firmware (`sfbus.h` `KEY_DEFAULTS`).

## Tests

    pio test -e native      calibration maths (lib/sfctl_core) and console parsing (include/console_parse.h)

CI runs them and builds all three boards on each PR. Without a host compiler on Windows, run them in
Docker from `firmware/`: `docker run --rm -v "%cd%:/fw" -w /fw/controller python:3.12 sh -c "pip install -q platformio && pio test -e native"`.

## Releases

Tagged `fw/controller/vX.Y.Z`; CI builds every env in [`release.toml`](release.toml) from the tagged
source (see [RELEASING](../../.github/RELEASING.md)). Nothing released yet.

Migrated from `split-flap-display-pcb/firmware/ltm-host` at `fdae423` and split into `lib/sfctl` +
`src/console.cpp`; commands and output are unchanged apart from the banner.
