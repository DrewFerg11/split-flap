# Plan — option 2 (wide name module + 2 digits)

Phased so each step proves one thing before the next depends on it. Option 1 (3 letters +
2 digits) stays documented in [README.md](README.md) and shares phases 1, 2 and 4–7. Only
phase 3 is specific to option 2.

Started 2026-10-08.

## Phase 0 — decisions that shape the module

**Focus (Drew, 2026-10-08): redesign the digit module first.** The wide name module waits
until the mechanism is proven, because its flap is the hardest part to make.

| # | Decision | Status |
|---|---|---|
| D1 | **Flap count** | **Fewer than 37** for the digit module (≥ 11: 0–9 + blank). Exact count found by prototyping a few variants, see [below](#flap-count-trade-offs). Name module: ≥ 21, decided later. |
| D2 | **Name module width** | Deferred. Longest names are 14 chars ("Crystal Palace", "Nott'm Forest"); rough 250–350 mm. |
| D3 | **Flap material / how flaps are made** | Deferred to the name module. Digit flaps are small enough to print. |
| D4 | **Printer** | **Bambu P2S, 256 × 256 × 256 mm.** Keep parts clear of the bed edge (edges print badly). Housings can be split into several parts; the **flap is the real limit**, since it must be one piece. Matters for the name module, not the digits. |
| D5 | **Module/row height** | **70 mm first target** (Drew, 2026-10-08); ≤ 91 mm hard limit; today's square is 77.12. 20 rows → 1400 mm. Rough consequence: flaps ≈ 30 mm long, digits ≈ 50 mm tall. Confirmed in phase 1. |
| D6 | **Position sensing** | **Hall homing first; encoder only if needed.** Fewer flaps means more angle per flap, which may make step counting + hall accurate enough. Leave room (and a PCB footprint) for an encoder, and decide from the digit prototype's measured error. AS5600 bench work already done (`docs/as5600-deep-dive.md`, development workspace); on-axis placement still fights motor-in-drum. |

### Flap count trade-offs

28BYJ-48: about **2038 steps per output revolution**. The commonly quoted 2048 is not
exact, because the gear ratio is ≈ 63.68 : 1. Typical **gear backlash is a few degrees** at
the output. Drew: ours is "not a lot". Not measured yet; measure it on the first prototype.

| Flaps | Angle per flap | Steps per flap | Margin before showing the wrong flap (≈ ½ flap) |
|---|---|---|---|
| 37 | 9.7° | 55 | ±4.9° |
| 20 | 18° | 102 | ±9° |
| 16 | 22.5° | 127 | ±11° |
| 12 | 30° | 170 | ±15° |

* **Accuracy:** fewer flaps means each flap covers more angle, so backlash and a few missed
  steps are a smaller fraction of a flap. 12 flaps is about 3× more forgiving than 37.
* **Speed:** a full turn is the same number of steps whatever the flap count, but any
  digit is fewer flaps away. 12 flaps also leaves one spare flap (e.g. "-").
* **Compactness — the catch:** with the **motor inside the drum**, the drum can't be
  smaller than the motor. A 28BYJ-48 is ~28 mm across, so the flap pivot circle stays
  around that size whatever the flap count. Fewer flaps then just means **wider spacing
  between flap pivots**, which also helps flaps release cleanly. It does not shrink the
  module by itself. Module height comes mostly from **flap height** (character size), so
  compactness is mainly a flap-size decision.
* **Flap fall:** with very few flaps, each flap swings through a larger angle before
  it's caught. Check that flaps still settle cleanly and don't bounce. Prototype it.

### Drive layout — decided 2026-10-08: **C**

Motor ears **trimmed** (the current design already bends them). The motor body sits **centred on the
drum axis**, held by a cup on the side wall that also keeps it from turning. The off-centre shaft
(8 mm) points into the drum, and a pinion on it turns an **internal ring gear** at the drum's far
end (~2:1). Only the wire housing (~17 mm from the axis) limits the drum, which gives a pivot
circle of **r ≈ 20.5**, versus ≈ 28 for direct drive (ruled out: bigger than today's r ≈ 23.5).
Drawing: https://claude.ai/artifact/ToaEbqmz4UjBHQFow83U5S

Plan: draw the mechanism with flap count as a parameter. Print 2–3 variants (e.g. 12, 16,
20). Measure position error, update time and flap settling on the 12 V bench.

## Phase 1 — mechanism from first principles

* Flap geometry (count, thickness, pivot radius → drum diameter), drum, axle, motor mount,
  sensor mount, worked out on paper/in a calc sheet before CAD.
* Inputs only from purchased-part datasheets and our own measurements
  ([`hardware/design-ownership.md`](../../hardware/design-ownership.md)).
* Start the design log.

## Phase 2 — digit module prototype

The narrow module first: cheapest to iterate, and it proves the mechanism, homing and
encoder before scaling up.

* New Fusion project, blank files.
* Print, run on the 12 V bench (`builds/12v-prototype`, development workspace), measure
  update time and homing reliability.

## Phase 3 — wide name module prototype

* Same mechanism, longer drum: check torque (more flap mass), drum sag/straightness, and
  whether it needs support at both ends.
* Flap printing/production method for full names (D3).

## Phase 4 — row board PCB

* One board per row driving **3 modules** (option 2) — or 5 (option 1).
* Bus choice and power from `docs/architecture-options.md` (development workspace)
  and the options register.

## Phase 5 — one complete row

* Row chassis: name module + 2 digit modules + row board, plugging into the left-side bus.

## Phase 6 — firmware and data

* New firmware: bus protocol, motion, homing/encoder, table logic.
* Data source: an EPL API whose licence allows this use, with sensible behaviour when it's
  down (brief issue 9).

## Phase 7 — full display

* 20 rows, frame and wall mount (15–25 kg+, into studs), power supply, wiring.

## Open questions

1. Flap count (D1): fewer than 37; settle it with the prototype variants.
2. Is a live-score mode still wanted with option 2? Full names make "home / away" rows easy;
   live scores in the points columns would need the digit modules to show scores.
3. What goes on the spare name flaps?
4. One drum/flap design shared by both modules (width as a parameter), or two designs?
