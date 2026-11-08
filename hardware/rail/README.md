# Main rail (trunk) — options

> Shared by every display (any number of rows). Paths written as `docs/…` are notes in the private
> development workspace and aren't migrated.

Started 2026-10-31. Research only, nothing decided. Wiring diagram of idea A: [rail-wiring.html](rail-wiring.html). Covers the vertical bus on the right of the rows that carries
power and data from the PSU + ESP32 at the bottom to every row.

## What earlier docs already say

| Source | What it says |
|---|---|
| `docs/product-brief.md` R9 | bus up the side, "proper rail (preferred) or a wiring loom"; rows connect on one edge only. Written for the **left**; moved to the **right** 2026-10-14 ([Premier League README](../../applications/premier-league/README.md#electronics--first-ideas-drew-2026-10-14-draft)) |
| `docs/architecture-options.md` §2, open Q4 | a rail is a multi-drop bus, 4 conductors (12 V, GND, A, B); "PCB backplane, busbar, or loom — as much mechanical as electrical" |
| `docs/options-register.md` §6 | pogo onto passive backplane ⭐ (adamgmakes), card edge ✅, board-to-board headers ✅ (not blind-mate), busbar + flying leads 💤 |
| [adamgmakes/SplitFlapDisplay](https://github.com/adamgmakes/SplitFlapDisplay) | publishes a passive 5-module bus board, 4 pogo pins per module (9 mm, 2.0 head, 5.0 tube) |
| `docs/action-items.md` | open: "evaluate pogo pins for the rail interface", "decide rail construction" |
| [`DESIGN-1.md`](../../pcb/module-board/design/DESIGN-1.md) §4–6, §9.1, open item 6 | trunk + one stub per row; 120 Ω at the two trunk ends, bias at the host; the rightmost digit's **male 5-pin 2.54 RA header** takes the row's plug (12V · GND · A · B · ENUM); 60 modules ≈ 15–20 A, PSU ~25–30 A; trunk wiring, per-row fusing, termination left to "a separate design" |

## Decisions (Drew, 2026-10-31)

| Decision | Consequence |
|---|---|
| **All rows move at once** (63 modules at 21 rows, more if possible) | size the spine for the full unison load + margin, not a firmware cap; per-row draw still to measure (motor on order) |
| **Row tap = the header already on the module boards** (T1) | the rail has a left-facing 5-pin 2.54 socket per row; alignment comes from the printed row guides |
| **Rows are swapped with the display off** | no hot-plug design on the rail (no make-first ground) |
| **Power: continuous 12 AWG solid bus pair, 22 AWG drops soldered on (P1/P7)**, for now | no cut bus, no middle feed; fuse on each 12 V drop |
| **Data: continuous 22 AWG wires pressed through each row's MTA-100 feed-through housing**, no solder | A/B as a twisted pair, untwisted ~2 cm at each housing; ENUM wire left out until the ENUM TODO is settled (module pulls ENUM_IN low with 10 k, so an empty pin 5 is safe) |

## ENUM on the rail — TODO (Drew 2026-10-31: not settled, revisit)

On the module board, `ENUM_IN` goes through 1 k into PB7 with a 10 k pull-down (`gen_schematic.py` R4/R5); the
module firmware just reads it (`F_ENUM` in `ltm_proto.h`). It's a chain *inside a row*: rail → digit → digit → name,
each module's `ENUM_OUT` feeding the next one's `ENUM_IN`. It tells a module its place in the row, not which row.

| Scheme | Spine conductors | Row identity |
|---|---|---|
| **Fixed** ⭐ for now: every tile holds its row's ENUM at ~3.3 V (resistor divider off 12 V on the tile) | 4: 12 V, GND, A, B | ESP32 finds modules by UID; the one-time setup is "which row is this?" × 21 (in-row position comes from ENUM) |
| **Switched**: ESP32 enables one row's ENUM at a time | 4 + a row-select chain (e.g. a shift register per tile: data, clock, latch = 3 more) | fully automatic, no setup |

The ENUM level must be ≤ 3.3 V-ish, **never 12 V** (12 V through the board's 1 k / 10 k puts ~11 V on PB7).
Keep a spare conductor or two in the tile-to-tile data link so the switched scheme can be added later.

## Numbers that size it

| | Value | Note |
|---|---|---|
| Rows | 21 for the EPL build, **not fixed** | never hard-code the count |
| Row pitch | ~75 (module 74.45 now) | not final; the rail must not bake it in |
| Spine length | ~1.6 m of rows + the bottom bay | |
| Modules | 63 at 21 rows | |
| Moving current / module | ~0.2–0.3 A | **estimate, unmeasured** (DESIGN-1 open item 3) |
| Stall limit / module | 1.0 A (DRV8870 limit) | row stalled = 3 A until the ~200 ms jam cut-off |
| All 63 moving at once | ~13–19 A | at the bottom of the spine (Drew: unison is a requirement) |
| Design target | **~25 A continuous** | 63 modules + room for more rows; revisit after the row measurement |
| Start-up spike | up to ~1 A/module for a few ms (≈ stall) → **~60 A if all 63 start on the same tick** | firmware ramps PWM and staggers starts by a few ms; 63 × 100 µF board caps (~6 mF) also soak it |
| One row | ≤ 1 A running, 3 A stalled | sets the row tap |
| Drop, 12 AWG pair, end-fed, 25 A spread up the spine | ~0.25 V | 5.2 mΩ/m; feeding both ends of the bus halves it |
| PSU | Mean Well **LRS-600-12** (50 A) or RSP-500-12 (41.7 A); LRS-350-12 (29 A) is tight | |

## Two separate questions

1. **Spine** — what runs the 1.6 m.
2. **Row tap** — how a row connects as it slides in from the left (blind-mate, since the right end is hard to reach
   once the display is on the wall).

### 1. Spine

| Option | For | Against |
|---|---|---|
| **A. One long PCB** | one part, cleanest | JLC 2-layer max **1020 × 600 mm** → 2+ pieces anyway; long boards cost/ship badly; row pitch frozen in copper; 20 A needs very wide pours |
| **B. Per-row tile PCB** ⭐ | identical tiles, any row count, pitch set by the back board not the PCB; cheap (fits 100 × 100 pricing); room for per-row polyfuse + TVS + LED + ENUM strap | tile-to-tile links must carry the current of every row above (20 A at the bottom) unless power bypasses them |
| **C. Loom** | cheapest, no PCB | 21+ hand-made drops; no fuse/indicator per row; rows plug by hand (no blind mate) |
| **D. Bus bars** (copper/brass bar or solid wire) | carries 20 A easily | power only; data still needs B or C |

### 2. Row tap

| Option | For | Against |
|---|---|---|
| **T1. Row's RA header into a left-facing socket** | already on the ordered boards, zero module change, cheapest | needs ~±0.3 mm alignment → printed lead-in/funnel; 3 A pins at the stall limit; no make-first ground for hot-plug (E1) |
| **T2. Pogo pins onto ENIG pads** | tolerant (pads can be long in the slide direction); proven by adamgmakes; 2 A/pin parts are common | 2 A/pin → double the power pins; ~1 N/pin pushes the row back out → needs a latch; extra part per row |
| T3. Card edge | no connector part on the row | module boards stand inside the enclosure; no exposed edge without a new board |
| T4. Pigtail plugged by hand | trivial | not blind-mate; fallback only |

T1 is chosen (Drew 2026-10-31). The rest of this page is about what the left-facing socket sits in and how power
and data reach it.

## Brainstorm (2026-10-31)

### Things to buy and modify

| # | Idea | What it is | Fit for us | Verdict |
|---|---|---|---|---|
| 1 | **IDC daisy-chain housings: TE MTA-100** (or Molex KK 254 IDC) | 2.54 single-row socket you press wires into; **feed-through** version lets one continuous wire pass through many housings. 5 A/contact, 22–28 AWG, mates 0.025" (0.64) square posts. Hand tool 59803-1 ≈ $37 | mates the row's header directly; A/B run as one unbroken twisted pair through every row's housing; Cat5e solid 24 AWG is exactly what IDC is made for (spare pairs = room for ENUM later) | ⭐ the off-the-shelf version of "wires the pins slot into" |
| 2 | **Panel busbar** (10 × 3 tinned copper, 1 m, e.g. Phoenix NLS-CU) on printed or bought supports | electrical-panel bar, ~80–140 A | power up the spine with zero worry; tap by drilling + M3 ring lugs | ✅ for power; 12 AWG wire does the same job cheaper |
| 3 | **48 V magnetic / DALI track lighting** | aluminium profile with 4 conductors (2 power + 2 DALI), tap anywhere; SLV 16 A, others 15 A max | RS-485 would ride the DALI pair; looks finished | ❌ 15–16 A < our ~25 A; proprietary contacts, we'd still design a printed shoe header→track; $$ per metre |
| 4 | 12/24 V shelf / under-cabinet power track | 2-conductor clip-anywhere strip | power only, a few amps | ❌ |
| 5 | **DIN rail + TBUS** (Phoenix) | bus connectors that click together inside a DIN rail; 5-pos, 8 A | pitch = housing width (17.5–22.5 mm), modules clip on from the front, not slide in sideways | ❌ for the tap; a DIN rail is still a handy spine to hang holders on (adamgmakes mounts modules on one) |
| 6 | Modular backplane kits (RC2014 / Tindie 72-pin) | short PCB backplanes that chain by RA headers | fixed slot pitch, logic-current traces | ❌ |
| 7 | Mill-Max RA spring-pin header (829-22-005, 3 A/contact) | pogo strip at 2.54 | needs flat pads on the row, not our header | only if T1 fails (T2) |

### DIY / own design

| # | Idea | How | For | Against |
|---|---|---|---|---|
| A | **Bus wires + IDC socket in a printed holder** (Drew's idea, with #1) | 2 × 12 AWG (or bars) up the spine for 12 V/GND; one Cat5e up the spine for A/B; per row an MTA-100 5-pos housing pressed onto the A/B pair (feed-through) + two short 22 AWG power drops from the bus; housing sits in a printed **floating pocket** with a funnel | no PCB; any row pitch and count; ~$1–2/row; every part off the shelf | no per-row fuse (needs an inline 5 A fuse per drop, see below); hand-terminated ×21; IDC is "once only" (re-pressing is not recommended) |
| B | **Rail tile PCB + bus wires** (previous leaning) | same as A, but each row's socket, fuse, LED, termination jumper on a small PCB; power drops from the bus land on the tile; A/B tile-to-tile by short cables | repeatable socket position; fuse + LED + test pads per row; easy to swap | a PCB to design; still ×21 cable joints |
| C | PCB strip with bus wire soldered on | long-ish PCB segments (≤ ~500 mm, LED-strip style) carrying the sockets + data; bare 12 AWG soldered along exposed copper for current | fewest loose parts | row pitch frozen in copper per segment; long-board pricing |
| D | One long PCB | | | JLC max 1020 mm, price, pitch frozen → ❌ |
| E | Copper tape / brass strip + wiper contacts | | | wiping contacts for RS-485 over years, oxidation → ❌ |

How-to search terms for the soldered tap: "DCC bus feeder wires soldering", "how to solder feeder to bus wire",
"strip wire in the middle Ideal Stripmaster", "T splice / tap splice soldering" (NASA calls it a "Western Union"
tap splice), "solder seal heat shrink wire tap".

### MTA-100 details (2026-10-31)

* Comes in 2 to 15+ positions, so **5-position exists**, in two styles: **closed end** (wire stops in the housing)
  and **feed-through** (wire passes through, for daisy chains). Each housing is made for **one wire gauge** (colour:
  22 AWG red, 24 white, 26 blue, 28 green); **one wire per slot**; 22 AWG is the biggest.
* So the 12 AWG bus can't go into the housing. Per row: **two short 22 AWG drops** (bus → fuse → housing) for 12 V/GND,
  and the data wires pass straight through. All five wires in a housing must be the same gauge → use the **22 AWG
  feed-through 5-pos** with 22 AWG data wires (or the 24 AWG one with Cat5e and 24 AWG drops; 24 AWG is fine for a
  1 A / 3 A-peak row over ~10 cm).
* Pin 5 of the row header is ENUM. A wire passing through every row would connect all rows' ENUM together — fine for
  the "fixed" scheme, wrong for "switched" (ENUM TODO above).
* Exact part numbers: pick from Digi-Key's MTA-100 filter (positions 5, feed-through, gauge). 3-640621-5 is listed as
  a 24 AWG feed-through 5-pos; confirm before ordering.

### Per-row fuse: buy or build

| Option | How | Cost | Notes |
|---|---|---|---|
| **Inline mini-blade fuse holders** on each row's 12 V drop | spliced between the bus and the MTA housing | ~$0.30–0.50/row + fuse | simplest with idea A; ~5 A fuse |
| **12-way blade fuse block with negative bus** × 2 at the bottom | each row gets its own 12 V wire from the bottom (star), GND on a common bus | Nilight ~$29, Blue Sea ST Blade ~$57–80 each; 100 A/block, 30 A/circuit | some have a **blown-fuse LED per circuit** (tells you which row); 21 × ~1.6 m of 18 AWG instead of a 12 AWG bus |
| DIN-rail fuse terminals | same star, on a DIN rail in the bottom bay | $$ | tidy, overkill |
| **Small PCB per row** | Keystone 3568 mini-blade holder (PCB mount, 30 A) or an 1812 polyfuse + LED + the socket | ~$1–2/row at JLC | 2-layer, ~10 parts, an evening in KiCad; this is idea B |

### Getting power from the trunk to each row (2026-10-31)

Every row needs its own 12 V and GND wire to its socket whether or not it has a fuse, so a bus always needs 21
taps. Options:

| # | How | For | Against |
|---|---|---|---|
| P1 | **Solder mid-span taps**: strip ~12 mm in the middle of the bus, wrap the drop, solder | the standard model-railway "feeder drop" pattern (solid 12 AWG bus, 22 AWG drops, [trains.com thread](https://forum.trains.com/t/stripping-wire-in-the-middle-for-dcc-power-bus/77727)); soldering is called the most reliable joint, though [Gateway NMRA](https://www.gatewaynmra.org/?p=975) prefers Scotchlok taps for speed | 42 joints with an iron on 12 AWG mounted on the board; heat near printed parts |
| P2 | Screw-on piercing taps (Posi-Tap 10–12 AWG run) | no solder, removable | no clear current rating; piercing a bus 42 times |
| P3 | **Star from fuse blocks at the bottom** ⭐: 2 × 12-way blade fuse blocks with negative bus in the bottom bay; each row gets its own 22 AWG pair straight from its fuse to pins 1–2 of its socket | **no taps, no bus**; all fuses in one reachable place; blown-fuse LED per row on some blocks; 24 circuits = 3 spare rows | ~21 × 2 runs of up to ~1.7 m (≈ 45 m of 22 AWG); a 42-wire bundle at the bottom, thinning as it goes up |
| P4 | **Two rigid bars** (copper/brass/aluminium flat bar), drilled and tapped M3 at each row (or slotted) | drops on ring terminals + inline fuse | never cut, screw joints, easy to redo; bars carry 25 A trivially | metalwork; bars need insulating standoffs and a cover |
| P5 | Cut the bus at each row into terminals on a per-row PCB | | every joint and the PCB carry up to the full 25 A → ❌ |
| P6 | **Cut the bus into row-length pieces, join with Wago 221-413 3-way lever connectors** (bus in · bus out · drop) | tool-free, re-doable, 12–24 AWG so the 22 AWG drop fits the same connector; 32 A IEC / **20 A UL** | each joint passes the current of every row above it: ~25 A at the bottom joints (over the UL 20 A) unless the bus is **fed in the middle as well** (then ≤ ~13 A per joint); a bad joint cuts every row above it; ~42 joints add ~0.1–0.2 V at the top (fine) |

| — | **Use solid-core bus wire for P1/P7/P8** (Drew 2026-10-31): 12 AWG solid THHN, red + black, sold by the foot at hardware stores | strips cleanly mid-span, doesn't fray, holds its shape on the board; what the model-railway guides use | only for a fixed bus (solid copper cracks if flexed repeatedly); a nick is a weak spot, so use a mid-span stripper or score lightly |
| P7 | **Continuous bus, heat-shrink solder sleeve taps** (Raychem SolderSleeve or generic "solder seal" sleeves): strip a ~12 mm window, lay the 22 AWG drop along it, heat gun | permanent; solder + insulation + strain relief in one step; no iron; inspection window | sleeves must be **threaded onto each bus before it's mounted** (21 per wire); check the sleeve fits 12 + 22 AWG |
| P8 | Continuous bus, **crimped parallel / tap splice** over the window + drop (Panduit/Ideal style), then heat-shrink | permanent, no heat | needs the right splice size for 12 + 22 AWG and its crimp tool; heat-shrink also pre-threaded |

P6 with a second feed from the PSU to the middle of the bus is a reasonable, simple version of the bus idea.
Drew wants a **continuous bus** (2026-10-31): P1 / P7 / P8 / P4. P7 is the easiest to do on the board.

Store-bought "fuse distribution modules" (e.g. OONO 12/18-position DIN-rail strips, LED per fuse) are the P3 star
in one part. The one seen: 30 A total input (tight against our ~25 A) and 3 A fuses fitted (a 3-motor stall is
~3 A, so fit 5 A).

P3 numbers: 22 AWG is 53 mΩ/m, so a 1.7 m row run drops ~0.18 V at 1 A, ~0.54 V for the 200 ms of a 3-motor
stall; a 5 A fuse protects 22 AWG (~7 A chassis rating); 22 AWG goes straight into the MTA-100 22 AWG housing with no
splice. Leaning P3, P4 second.

## Prior art, looked at in detail (2026-10-31)

### Dennis Gunia — [dennis9819/split-flap-controller](https://github.com/dennis9819/split-flap-controller)

Sysadmin in Frankfurt ([dennisgunia.de](https://www.dennisgunia.de)), inspired by the Frankfurt Airport board. Built on
David Königsmann's drum/flap design; everything else redesigned. AGPL-3.0, repo from 2025-09, "not final".

| | |
|---|---|
| Display | 12 × 3 = **36 modules**, 1U and 2U wide units, 45 flaps, 28BYJ-48 12 V |
| Module board | ATmega8 + SN75176 (RS-485) + ULN2003 + A1101 hall, **200 mA fuse per module**, ~110 mA per module running |
| Bus | RS-485 57600 baud, own "SFBus" protocol (start byte, 16-bit address, Modbus CRC); master always initiates |
| **Backplane** | **199 × 57 mm PCB for 4 modules**, 9 of them in the display. Each has four **2 × 8 card-edge sockets**: the module's controller board edge plugs straight in. Pins: 12 V, 5 V, GND ×4, A, B, RESET, DETECT in/out |
| Between backplanes | **Phoenix MSTB 5.08 pluggable terminal blocks**: 2-pin 12 V/GND, 3-pin A/B/GND, 3-pin DETECT/RESET/GND, cables between boards |
| On the backplane | L7805 (5 V for the modules), 74AHCT1G125 buffer for a shared RESET line, solder jumper |
| **DETECT chain** | runs module → module and **across backplanes** (in/out connectors), i.e. his version of our ENUM goes through the rail |
| Mechanics | backplanes screwed to a **sheet-metal backplate** (laser-cut DXF in the repo); printed upper/lower **slots** guide each unit onto its card-edge socket; sheet-metal brackets join the backplates |

Takeaways for us: (1) a short fixed-pitch backplane PCB per group of modules, chained with pluggable screw terminals,
works and is basically our "rail tile" idea; (2) blind-mate is done by printed slots guiding the board into the
socket, as we plan; (3) his chain signal goes through the rail, which is one answer to our ENUM question; (4) his
currents are tiny (~4 A for the whole display), so his PCB traces don't tell us anything about our ~25 A.

### Prior art: adamgmakes' bus board ([SplitFlapDisplay](https://github.com/adamgmakes/SplitFlapDisplay))

| | |
|---|---|
| `bus-board` | **572.65 × 24 mm** PCB with nothing on it but **4 bare copper strips** running the full length: 12 V 6.5 mm wide, A 2.5, B 2.5, GND 6.5 (mask open, 1 oz, 1.6 mm). One 1 mm hole at the end of each strip for the feed wire |
| `bus-board-5-module` | shorter version (~222 mm) |
| Module side | **4 pogo pins** (9 mm long, 2.0 head) on the driver board land on the strips; modules hang on a DIN rail |
| Point | **tap anywhere**: no connector per module, no fixed pitch; the strip is the connector |

Takeaways: the cheapest possible rail, and pitch-free. But (1) 6.5 mm of 1 oz copper carries a few amps, not 25 A
up 1.6 m (we'd need a soldered bus wire along it, or 2 oz and wide strips); (2) JLC tops out at ~1 m, so 2–3 boards
end to end; (3) needs pogo pins on our side, and we've chosen the existing header. Worth keeping as plan B (T2).

### Mechanics that apply to A or B

* **Floating socket:** the socket sits in a pocket ~0.5 mm oversize each way with a chamfered funnel in front; the
  row's header steers it the last few mm. Printed row guides on the back board do the coarse alignment.
* **End stop on the row guide, not the header:** the row bottoms out on a printed stop with the header fully
  seated, so pushing a row in doesn't push on the pins.
* Insertion: 5 pins × ~1 N ≈ 5 N, fine by hand.
* Check the PZ254R header's post is 0.64 square (MTA-100 / DuPont mate 0.025" posts).

### Printed rail mount (Drew 2026-10-31: yes, design one)

Printed in sections, joined to each other and/or screwed to the back board. Notes for the design:

* **One segment per row** (~75 tall, fits any printer, a spare row is one print) or 2–3 rows per segment (fewer joints).
  Row pitch is a parameter, the row count is not baked in.
* **Locate the socket from the row guide, not from the segment below**: tolerances stack over 21 segments. Best: the
  rail segment keys into (or is printed with) that row's guide and end stop, so header and socket line up from one part.
* Per segment: floating MTA pocket + funnel (as figure 3); a **clip-in channel for each 12 AWG bus** with an open
  window where the drop is soldered (the bus is laid in after the segments are mounted, sleeves pre-threaded);
  a channel for the data pair with room for its loop through the housing; a pocket or clip for the inline fuse;
  a snap-on cover over the taps.
* Slotted screw holes to the back board for adjustment; tongue/pin between segments for straightness only.
* Need before modelling: MTA-100 5-pos housing dimensions (sample or datasheet drawing), and the row header's
  position from the module (board position in the enclosure + PZ254R geometry).

### Protection either way

A shorted row must blow its own fuse, not cook a 22 AWG drop while the main 40–50 A fuse holds: **one ~5 A fuse per
row** (inline mini blade on the drop for A, polyfuse or blade on the tile for B). Main fuse at the PSU sized for the
12 AWG bus. Termination: 120 Ω at the host and at the top row; bias at the host (DESIGN-1 §4).

## Leaning (not decided)

1. **A** (bus wires + MTA-100 in a printed floating holder) as the first, cheap test — it's all bought parts and
   tests the blind-mate idea immediately.
2. **B** (rail tile) if A works mechanically but hand termination × 21 or the lack of per-row LED/fuse bugs us.
   A and B share the bus, the holder geometry and the row guides, so A is not wasted work.

## To do

1. Measure one full row's running and peak current on the real drums (Drew, 2026-10-31), then fix PSU, bus gauge, fuses.
2. Order an MTA-100 sample kit (feed-through 5-pos housings + 59803-1 tool) and a metre of Cat5e; print a floating
   holder + a row-end header block; test slide-in by feel.
3. **ENUM — TODO.** Level (~3.3 V, never 12 V) and fixed vs switched (above) still to talk through.
4. ~~Hot-plug~~ → display off for swaps.
5. Back-board layout: bus route, PSU + ESP32 bay at the bottom, row guides.

## Sources

* [JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) — 2-layer FR4 max 1020 × 600 mm (≥ 0.8 mm)
* [TE MTA-100 / MTA-156](https://te.com/en/products/connectors/pcb-connectors/intersection/mta-100-mta-156-connectors.html),
  [Digi-Key MTA](https://www.digikey.at/en/product-highlight/t/te-connectivity/mta-connectors) — 5 A, 22–28 AWG, feed-through daisy chain;
  [59803-1 tool](https://www.digikey.co.uk/en/products/detail/te-application-tooling/59803-1/132430)
* [Molex KK 254 header](https://uk.rs-online.com/web/p/pcb-headers/6795599P?gb=s) — 4–5 A/circuit
* DuPont 2.54 crimp: 3 A/contact ([Maplin](https://pro.maplin.co.uk/products/100-x-female-dupont-style-2-54mm-crimp-terminal))
* [Phoenix ME 22,5 TBUS 1,5/5](https://www.phoenixcontact.com/pi/products/2202543) — 5-pos, 3.81 pitch, 8 A
* Magnetic track: [SLV track systems](https://www.lampadario.ru/upload/iblock/0e7/v3hs8xcauc6omrc5s7mmdfuhzap61gfh/SLV%20TRACK%20SYSTEMS.pdf) (16 A),
  [Exenia Track 48](https://www.exenia.eu/en/product/track-48-twin/) (4 conductors: power + data bus)
* [Track01 shelf power rail](https://www.hktdc.com/event/hklightingfairae/en/product/1Z03F9ZUJ)
* [Tindie 72-pin modular backplane](https://www.tindie.com/products/electronics6/general-purpose-72-pin-modular-backplane/)
* [Mill-Max 829-22-005 RA spring header](https://www.digikey.com/en/products/detail/mill-max-manufacturing-corp/829-22-005-20-001101/2416226) — 3 A
* [Phoenix 10 × 3 Cu busbar](https://www.stoneway.com/Phoenix-Contact-Busbars/c4901-m4664)
* Mean Well [LRS-600-12](https://www.trcelectronics.com/products/mean-well-lrs-600-12) (50 A),
  [SE-600-12](https://www.progressiverc.com/en-ca/products/mean-well-se-600-12-power-supply)
* [Harwin pogo pins](https://www.harwin.com/products/P70-2200045/) (2 A),
  [Digi-Key: pogo basics](https://www.digikey.co.uk/en/articles/the-basics-of-pogo-pin-connectors)
* MTA-100 gauge colours / one wire per slot: [RS datasheet](https://docs.rs-online.com/90a4/0900766b814c10ee.pdf);
  [3-640621-6 (feed-through)](https://www.futureelectronics.com/p/interconnect--pin-and-socket-connectors--socket-plug-wire-mount/3-640621-6-te-connectivity-5933890)
* Fuse blocks: [Blue Sea ST Blade 12](https://www.westmarine.com/blue-sea-systems-st-blade-fuse-block-12-circuits-with-negative-bus-and-cover-3733490.html),
  [Nilight 12-way with LEDs](https://www.nilight.com/collections/most-bought-icart/products/nilight-12-way-blade-fuse-block-12-circuits-with-negative-bus-fuse-box-holder-with-led-indicator-ato-atc-fuse-panel-waterproof-cover-for-12v-automotive-cars-marine-boats-rvs-trailers-2-years-warranty);
  [Keystone 3568 PCB mini-blade holder](https://www.digikey.com.au/en/products/detail/keystone-electronics/3568/2137306)
* Prior art: [dennis9819 split-flap controller](https://github.com/dennis9819/split-flap-controller) (modules on one
  backplane, card edge), [adamgmakes](https://github.com/adamgmakes/SplitFlapDisplay) (pogo bus board, DIN rail mount)
