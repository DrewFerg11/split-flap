# Premier League (EPL)

A wall-mounted split-flap display showing the **English Premier League table**, one club per
row, re-sorting itself as the season goes on, plus **live scores** on match days. Rows aren't
fixed at 20: the EPL build is likely 21 (a header row), and the display is designed to grow.

**Try it in the browser:** [Premier League demo](https://drewferg11.github.io/split-flap/demo/premier-league/).

## Current state (2026-11-08)

| Part | State | Where |
|---|---|---|
| Module board | v0.1 ordered and brought up (power, SWD, motor, encoder, hall, RS-485) | [`pcb/module-board`](../../pcb/module-board/) |
| Module firmware | fixed bus addresses, homing, flap moves, calibration; ENUM auto-addressing not yet | [`firmware/module`](../../firmware/module/) |
| Controller | ESP32 serial bench console; Wi-Fi, web UI, Home Assistant and this app's firmware are planned (issues #10-#15) | [`firmware/controller`](../../firmware/controller/) |
| Mechanics | 52-flap digit module built and printed; name module designed, not yet printed. The flap print files still use the old numbering (home = slot 51) and need regenerating for the planned sets | CAD, scripts and print files not migrated yet (step 4, with the mechanics handoff notes) |
| Flap sets | the planned 52-flap name, digit and header drums | [`flap-sets/`](flap-sets/) |
| Rail (trunk up the side) | research, leaning to idea A | [`hardware/rail`](../../hardware/rail/) |

| Doc | What |
|---|---|
| [README.md](README.md) | this page: concept, the two layout options, the original numbers |
| [plan.md](plan.md) | phased plan for option 2, open questions |
| [flap-sets/flap-sets.md](flap-sets/flap-sets.md) | what goes on every flap of every drum (the single list) |
| [other-leagues.md](other-leagues.md) | which other leagues the same hardware can show, and where each breaks |
| [`hardware/design-ownership.md`](../../hardware/design-ownership.md) | the from-scratch rules for the module design |
| [`hardware/rail`](../../hardware/rail/) | the main rail / trunk on the right: options, current, leaning |
| [`firmware/controller/wiring`](../../firmware/controller/wiring/) | bench wiring: controller + modules on one RS-485 bus |

The sections below are the original concept notes (from 2026-10-08), kept as the record of how
the design was chosen. Some numbers have moved on: the motor is now an N20 gearmotor with an
encoder, both drums have 52 flaps, and the module board exists. Paths written as `docs/…` or
`design-files/…` are in the private development workspace and aren't migrated.

---

## Concept (2026-10-08)

This display is built on a **new module designed from scratch**: Drew's own design, not a
modification of the Morgan Manly enclosure that earlier work derives from. See
[`hardware/design-ownership.md`](../../hardware/design-ownership.md) for what "from scratch" means
in practice, and [plan.md](plan.md) for the build order.

The requirements in the original product brief (`docs/product-brief.md`: single 12 V rail,
side bus, ≤ 6 ft tall, motor inside the drum, cheap motors, better homing, row-level boards)
still apply unless this folder says otherwise.

---

## Layout options

Both stay on the record; **option 2 is the one being built.**

### Option 1 — letters (the original brief)

```
        ┌───┬───┬───┐   ┌───┬───┐
row 1   │ M │ C │ I │   │ 8 │ 8 │
row 2   │ A │ R │ S │   │ 8 │ 6 │
  …                                     20 rows
        └───┴───┴───┘   └───┴───┘
        3-letter code    2-digit points
```

* 5 modules per row, **100 modules** total.
* Every module is the same narrow design (letters A–Z + blank, digits 0–9 + blank).
* Most flexible: any league, live scores, messages.
* Most expensive and complex: 100 motors, 100 sensors, 5 drives per row board.

### Option 2 — full team name ⭐ (current focus)

```
        ┌───────────────────────┐   ┌───┬───┐
row 1   │ Man City              │   │ 8 │ 8 │
row 2   │ Arsenal               │   │ 8 │ 6 │
  …                                                20 rows
        └───────────────────────┘   └───┴───┘
        1 wide name module          2 digit modules
```

* 3 modules per row: one **wide name module** + two **digit modules**. **60 modules** total.
* The name drum carries the **20 current clubs**. Each summer the promoted clubs' flaps are
  printed and swapped in. Spare flaps carry other content (blank, headings, other text).
* Looks like the real table (full names, not codes), reads from across the room.
* Simpler: 40 % fewer modules, motors and sensors; 3 drives per row board.
* Less flexible: the name module only shows what's printed on its flaps.

| | Option 1 | Option 2 |
|---|---|---|
| Modules | 100 | **60** (20 wide + 40 digit) |
| Module designs | 1 | 2 (wide name, digit) — ideally one design family with width/flap count as parameters |
| Drives per row board | 5 | 3 |
| Shows | any 3-letter code + 2 chars | the 20 printed names + 2 digits |
| Season change | nothing | reprint/swap promoted clubs' flaps |

The points limit applies to both: **two digits top out at 99** (Man City had 100 in
2017–18). Accepted in the brief; firmware shows a defined fallback.

---

## Current numbers (option 2)

| | Value | Note |
|---|---|---|
| Rows | 20 | |
| Height budget | ≤ 1829 mm (6 ft) → ≤ 91 mm per row | from the brief |
| **Target module height** | **70 mm** | 20 rows = 1400 mm (today's square 37: 77.12 mm → 1542 mm) |
| Name flaps needed | 20 clubs + blank | 37 flaps leaves 16 spare; **fewer flaps = smaller drum, faster updates, possibly shorter rows** |
| Digit flaps | **fewer than 37** (≥ 11: 0–9 + blank) | count chosen by prototyping, e.g. 12 / 16 / 20 → [plan.md](plan.md#flap-count-trade-offs) |
| Motor | 28BYJ-48 (12 V version) | kept |
| Homing | hall sensor; **encoder only if the prototype needs it** | fewer flaps = more margin per flap; AS5600 bench work in `docs/as5600-deep-dive.md` |
| Printer | Bambu P2S, 256 × 256 × 256 mm | housings can be split; one-piece flaps are the limit (name module) |
| **Current focus** | **digit module redesign** | name module later |
| Electronics | own PCB: **one small MCU board per module** (2026-10-14) | RS-485 front-runner → [below](#electronics--first-ideas-drew-2026-10-14-draft) |

---

## Electronics — first ideas (Drew, 2026-10-14, draft)

Not decided yet; open questions are being worked through before the first prototype board.

* **12 V** everywhere (N20 motors are 12 V); logic comes from a small on-board regulator.
* **One ESP32 is the brain** for the whole display (data fetch, table logic, sends targets).
* **Bus** must handle **≥ 60 modules**, more if possible. Front-runner: RS-485 multi-drop
  (options register §3, `docs/options-register.md`); CAN is the alternative.
* **One small MCU board per module** (decided 2026-10-14), like adamgmakes' and Drew's
  mechanical-seven-segment v0.1 board (`mechanical-seven-segment-display/pcb/v0.1`: STM32G030 +
  RS-485 + chain auto-enumeration). The MCU runs the N20's encoder loop locally.
* **Board shape:** a rectangle standing upright **inside** the enclosure near the back, the back
  of the enclosure wrapped around it; it slides in on rails like the dowjames board.
* **Row layout:** `name – digit – digit`, ~20 rows stacked.
  * **All motors move to the right side** (2026-10-14): the enclosures are mirrored (same design),
    so every module slots together the same way and the name module's board sits next to the
    digits. Modules will screw together into one solid row (not designed yet).
  * Modules in a row **daisy-chain** (power + data in/out). Preferred: dowjames-style right-angle
    header / socket that plug straight into the neighbour, or JST cables. No pogo pins.
* **Main trunk on the right** with power + communication; each row is a **branch** off it.
  The trunk's form (PCB rail, bus bars, loom) is still to be investigated; ideally it reuses the
  same connector as the module chain. Options and numbers: [`hardware/rail`](../../hardware/rail/) (2026-10-31).
  ⚠️ This moves the bus from the left side (brief R9) to the right.
* **Addressing:** open; pros/cons being compared (auto-enumeration, UID discovery, DIP, flashed).
* **Firmware updates over the bus** (2026-10-14): each MCU gets a small bootloader, flashed once
  by SWD on the bench; after that the ESP32 broadcasts updates over RS-485 (it gets them over
  WiFi). Needs a 64 KB MCU (the 7-seg board's G030F6 is 32 KB) and SWD pads reachable before assembly.
* **Board design:** [`pcb/module-board`](../../pcb/module-board/design/DESIGN-1.md): STM32G031 + DRV8870 + GM3085E, 32 × 54 mm (ordered 2026-10-19, brought up 2026-10-27; released as `pcb/module-board/v0.1`).
* **Power:** one 12 V PSU sized to the load, feeding the trunk.
* **Serviceability:** each row slides out **to the left** for removal/installation, and mounts to
  the display's back board.
