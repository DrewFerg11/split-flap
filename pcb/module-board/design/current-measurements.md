# Module current measurements

Supply current of the module board at 12 V, measured on the bench 2026-11-22. These numbers replace
the estimates in [DESIGN-1 §6](DESIGN-1.md#6-power).

## Setup

- Meter in series with the +12 V lead into the first board's J1 (pin 1), 10 A jack, DC A range
  ([wiring diagram](images/bringup-current-measure-10a.png)). The mA jack is fused at 600 mA, below the
  stall current, so every reading uses the 10 A jack.
- Boards: module-board v0.1, chained J1 into J2, placed with `enum`. The ESP32 controller is powered
  over USB and is not in the measured current.
- Firmware: `firmware/module` `node` image (20 kHz slow-decay PWM), `fast` = 30 on every module.
- "Peak" readings use the meter's MAX hold; "running" readings are live values taken a few seconds in.
- `I` is the board's own motor-current reading (R_ISEN 0.33 Ω on PA4), shown by the console's `w`.
  It sees motor current only, so it reads about the meter value minus the idle current.

## Tests

| # | Test | Console | Meter |
|---|---|---|---|
| 1 | Idle, placed, motor stopped | — | live |
| 2a | Start-up, full duty with no ramp | `* d 100` | MAX |
| 2b | Running at full duty | `* d 100` | live, ~5 s in |
| 3 | Normal moves (ramped) | `* home`, `* f 20`, `* f 5` | MAX |
| 4 | Drum held by hand during 2b | `* d 100` | MAX |

## Results

### 33 mm modules

| Test | 1 module | 2 modules | Per module |
|---|---|---|---|
| 1. Idle | 16 mA | 30 mA | **15 mA** |
| 2a. Start-up peak | — (`I` peak 435 mA) | 0.20–0.42 A | **up to ~0.44 A** |
| 2b. Running, full duty | 84 mA (`I` ≈ 62) | 177–178 mA (`I` 60–80) | **~89 mA** |
| 3. Normal moves, peak | 41–47 mA | 83–88 mA | **~45 mA** |
| 4. Hard hold, not stalled | 214–291 mA | 0.54 / 0.90 A | — |
| 4. Full stall (one motor) | — | 1.126 A | **~1.0 A** |

In the full-stall run the module stopped itself (`STALL (no encoder counts)`). The ~1.0 A matches the
DRV8870 current limit set by R_ISEN (DESIGN-1 §7.2).

### 200 mm module alone

| Test | Meter | `I` |
|---|---|---|
| 1. Idle | 15 mA | 0 |
| 2a. Start-up peak | — | 438–456 mA |
| 2b. Running, full duty | 130–131 mA | 69–131 mA, ~100 average |
| 3. Normal moves, peak | 46–48 mA | — |

### One row: two 33 mm + one 200 mm module

The 200 mm module is third in the chain (address 3); its `I` is the one shown.

| Test | Row of 3 | 200 mm module |
|---|---|---|
| 1. Idle | 48 mA | 16 mA |
| 2a. Start-up peak | 0.31–1.0 A (depends on how the three surges line up) | `I` peak 407–429 mA |
| 2b. Running, full duty | 309–319 mA | `I` 72–135 mA, ~95 average; ~115–135 mA total |
| 3. Normal moves, peak | 134–145 mA | ~50 mA (row minus 2 × 45) |
| 4. Whole row squeezed, none stalled | 0.79–0.81 A | — |

### Two rows (6 modules)

Two rows as above, both fed from one +12 V lead through the meter; GND, A, B and ENUM shared. The `I`
column is the second row's 200 mm module (address 5).

| Test | 2 rows | 1 row × 2 | 200 mm module |
|---|---|---|---|
| 1. Idle | 95 mA | 96 mA | — |
| 2a. Start-up peak | 0.71–1.91 A, no resets | — | `I` peak 431–465 mA |
| 2b. Running, full duty | 620–628 mA | 618–638 mA | `I` 70–115 mA, ~90 average |
| 3. Normal moves, peak | 263–290 mA | 268–290 mA | — |

Two rows draw exactly twice one row: the current scales linearly with the number of modules.

The 200 mm drum needs its end cap fitted to run, so it can't be held by hand on its own. The stall
current is set by the DRV8870 limit (~1.0 A), not by the drum, so the 33 mm stall figure applies to it.

## What it means

- **Chain connector:** a row (two 33 mm + one 200 mm) draws about 0.15 A in normal moves and 0.32 A
  with every motor at full duty. The worst case is one module stalled and two running (~1.2 A), or all
  three stalled (3 A) until the stall cut-off. The 5-pin chain (one +12 V pin, rated 3 A) is enough;
  no 7-pin change.
- **The 200 mm drum** draws about 1.5× a 33 mm drum at full duty (130 vs 89 mA) and the same in
  ramped moves (~47 vs ~45 mA).
- **Ramping:** a ramped move peaks at ~45 mA per module; an unramped full-duty start kicks to ~0.44 A.
  Moves should keep ramping, and broadcast commands should not start every module at full duty at once.
- **Jam detection:** a jam (0.2–1.0 A) is above normal running but below the unramped start-up surge,
  so the jam threshold has to ignore the first few hundred ms of a move.
- **ISEN:** the board's own reading tracks the meter. (Before this test the firmware read ISEN through
  the wrong pin number and always reported 0 mA; fixed in `firmware/module`.)
