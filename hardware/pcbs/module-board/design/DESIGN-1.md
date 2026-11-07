# Split-flap module board v0.1 — Design document, revision 1

**Board:** one small MCU board per split-flap module (digit and name) for the league-table display.
**Status:** steps 1–4 done (2026-10-15): schematic ERC-clean, board laid out and routed, DRC-clean, **fab package in `fab/`**. Step 5 done: **Ordered 2026-10-19:** JLCPCB, 10 boards, Economic PCBA top side (green, 1.6 mm, HASL), est. ship 2026-10-23; C1 hand-solder caps from LCSC (20× C3151830, separate shipment).
**Date:** 2026-10-14
**Target:** KiCad 10, fabricated and assembled by JLCPCB.

The electronics follow Drew's earlier mechanical seven-segment display module board ("7SEG" below): same host model,
same bus, same MCU family, same addressing hardware and the same protection. **7SEG had not been
ordered or brought up as of 2026-10-14, so its choices are reviewed but not yet proven.**

## Steps (plan of record)

| Step | What | Status |
|---|---|---|
| 1 | Design doc: requirements, blocks, parts with LCSC numbers, pin map, connectors, power | **this document** |
| 2 | Board outline from the digit enclosure (Fusion), connector reach between modules | **done for now, §8** (Drew: "works for now") |
| 3 | Schematic in KiCad, ERC-clean | **done, §13a** |
| 4 | Layout, DRC, verify scripts, fab package in `fab/` | **done, §13b** (JLC preview check is part of step 5) |
| 5 | Order 5 boards, bench one digit module (ESP32 + RS-485 adapter as host) | |

---

## 1. What this board is

```
                     row n:  NAME ──── DIGIT ──── DIGIT ──── trunk (right side)
                             [board]   [board]    [board]      12V GND A B
 ESP32 ─RS-485─ trunk ─┬─ row 1   (each row is a short branch off the trunk)
 (host, WiFi)          ├─ row 2
                       └─ … row 20      60 modules, identical boards

 each board:  12V ─► protection ─► DRV8870 ─► N20 motor
                              └─► 3.3 V LDO ─► STM32G031 ◄─ encoder A/B, A3144 hall
                                               └─► GM3085E ─► A/B bus
```

* **Host:** one ESP32 (WiFi, table logic, enumeration, per-module settings, firmware updates).
* **Module MCU** runs everything time-critical: encoder counting, motor speed loop, homing,
  "go to flap N", jam detection, status reporting.
* **Identical boards** in every module. The name module uses the same board at its motor end.

## 2. Settled decisions (Drew, 2026-10-14)

| Decision | Consequence for this board |
|---|---|
| **MCU per module**, not per row | 60 boards; motor, encoder and hall wiring stay inside the module |
| **One ESP32 host** | board is a bus slave only; no WiFi |
| **12 V** single rail | N20 runs straight off 12 V; only a 3.3 V LDO on board, no buck |
| **RS-485** | ≥ 60 nodes now, up to 256 with 1/8-unit-load transceivers |
| **All motors on the right** (enclosures mirrored, same design) | name module's board sits next to the first digit; every module plugs together the same way |
| **Board stands upright inside the enclosure near the back**, slides in on rails | outline set by the enclosure's back section, §8 |
| **Chain: right-angle header / socket** on the board edges; no pogo pins | modules plug straight into their neighbour, §9 |
| **Main trunk on the right**, one branch per row; rows slide out to the left | rows are bus stubs, §4 |
| **Firmware updates over the bus** | 64 KB MCU + bootloader; SWD pads only for the first flash, §11 |
| **Unison and sequenced moves** | protocol/firmware only (broadcast GO, per-module start delay, group addresses) |

## 3. Requirements

| # | Requirement |
|---|---|
| F1 | Drive one 12 V N20 (Waveshare DCGM-N20-12V-EN-200RPM) both directions with PWM speed control |
| F2 | Count its quadrature encoder in hardware (10856 counts per drum rev measured, `firmware/n20-bench`) |
| F3 | Read one A3144 hall sensor for homing |
| F4 | RS-485 slave: addressed commands, broadcast GO, status/fault replies, CRC on every frame |
| F5 | Detect a jam: motor current (sense resistor → ADC) and "no encoder counts while driven" |
| F6 | Firmware update over the bus (bootloader), first flash by SWD |
| F7 | Bring-up standalone: status LED, SWD + UART pads |
| F8 | Boards identical; no per-board parts or jumpers in normal use |
| S1 | 60 modules on one bus, more without board changes |
| S2 | Row of 3 modules chained through the board connectors, all motors stalled at once (3.3 A) |
| M1 | Fit the back section of the digit enclosure (§8); same board fits the name module |
| E1 | Survive hot-plugging a module/row on a live 12 V rail and a reversed 12 V/GND plug |
| E2 | JLC 2-layer, JLC SMT assembly; THT connectors JLC-assembled or hand-soldered |

## 4. Bus — RS-485

| Item | Decision |
|---|---|
| Transceiver | **GM3085E** `C269864` (7SEG's): 3–5.5 V, 1 Mbps, 256 nodes, half-duplex, SOP-8 |
| Direction | hardware `USART1_DE`; DE and /RE tied; 100 k pull-down holds the driver off during reset (7SEG §4) |
| Baud | start at 250 kbps; 500 k–1 M only if needed |
| Topology | trunk + 20 row branches; A/B pass straight through each board |
| **Stubs** | each row is a stub of ~0.3 m (name ~172 + 2 × 43 mm + its plug). At 250 kbps that is well inside the usual "stub ≪ bit time" limit. Revisit if baud goes up |
| Termination | 120 Ω **at the two ends of the trunk only** (on the trunk / host side), not on modules. A `JP_TERM` jumper stays on the board for bench use (one module = both ends) |
| Fail-safe bias | once, at the host |
| Protocol | address byte, command, payload, CRC-16; broadcast address; group addresses (row, all digits, all names) |

## 5. Addressing

Drew wants the simplest and cheapest that works. Board-level choice: **wire `ENUM_IN` / `ENUM_OUT`
through the chain connector (one pin, two resistors), and decide the scheme in firmware.**

| Scheme | Hardware | Notes |
|---|---|---|
| **UID discovery + one-time map** ⭐ | none (STM32 96-bit UID) | Host finds every module on the bus, then you assign each one its spot once (it spins; you click its position in a web page). Swap a module → re-map that one |
| ENUM chain (7SEG §5) | 1 pin | With a trunk + branches the chain can't run through all 60 without returning from each row's end; but **within a row** it gives each module its position (digit 2 / digit 1 / name) automatically if the trunk holds the row's first `ENUM_IN` high |
| DIP switches | 6 switches | not chosen: board space, 60 boards to set by hand |
| Flashed address | none | not chosen: 60 different configs; swap needs a reflash |

Leading option: UID discovery, with the in-row ENUM position as a cross-check. Firmware decision,
no board change either way.

## 6. Power

### 6.1 Budget per module (12 V)

| Load | Current | Source |
|---|---|---|
| N20 no-load / stall | 0.1 A / ≤ 1.1 A | Waveshare |
| N20 moving the drum | ~0.2–0.3 A | **estimate — measure on the bench** |
| Logic (MCU, transceiver TX, encoder, LED) | ≤ 60 mA at 3.3 V | datasheets; transceiver driving a terminated bus dominates |

### 6.2 Through the chain

* **1 pin each for +12 V and GND** (Drew, 2026-10-14: 5-pin chain for now, 7 pins possible later).
  2.54 mm header pins are rated 3 A.
* Normal running: 3 motors × ~0.2–0.3 A ≈ 1 A through the first board's connector.
* Worst case: all three motors in a row stalled = 3 × **1.0 A** (DRV8870 limit, §7.2) = 3.0 A, at the
  pin rating, only until the firmware's jam cut-off (~200 ms).
* Pass-through +12 V / GND as copper pours, not traces.
* If the bench shows more current than expected, go to 7 pins (2 × 12 V, 2 × GND).

### 6.3 Display total

60 moving together ≈ 15–20 A at 12 V (estimate). PSU ~25–30 A (e.g. Mean Well LRS-350-12).
Trunk wiring and per-row fusing are a trunk design question, not this board.

### 6.4 Protection (from 7SEG §6.3, kept)

| Part | Job |
|---|---|
| **F1** BSMD1812-200-33V polyfuse (2 A hold / 4 A trip) `C7433877` | short circuit on the local branch only (not the pass-through) |
| **Q1** AO3401A P-FET `C15127` (Basic) + **DZ1** MM1Z10 `C107591` + 100 k | reverse-polarity ideal diode. **Drain to F1, source to +12V_LOCAL** (7SEG drew it backwards first) |
| **D2** SMAJ18A TVS `C908771` | hot-plug surge clamp on +12V_LOCAL |
| Bulk cap | C1 100 µF 35 V 6.3 × 5.4 electrolytic on +12V_LOCAL (motor + hot-plug) |

The pass-through +12 V is not fused or switched on this board; a mid-row board plugged in reversed
still passes the reversal downstream (7SEG §6.1 caveat). The fixed header/socket pair can't be
reversed between modules; only the row-to-trunk plug can.

### 6.5 Logic rail

**HT7533-1** `C14289` (Holtek, **Basic**, 30 V in, 100 mA, SOT-89): already proven on Drew's earlier 12 V module board.
Worst case (12 − 3.3) V × 60 mA ≈ 0.5 W only while transmitting; average well under 0.2 W. Give it a
copper pad. 1 µF in / 10 µF out (check the datasheet's minimum at step 3).
**Pinout check at step 3:** 7SEG's HT7333 symbol had VIN and VOUT swapped.

## 7. Blocks

### 7.1 MCU — STM32G031F8P6

`C529334`, TSSOP-20, Extended, 12,551 in stock (snapshot), ~$1.24. **64 KB flash / 8 KB RAM**:
room for a ~4 KB bootloader and two firmware copies later. Same package and pinout family as 7SEG's
STM32G030F6P6 (32 KB), so its pin work carries over; **the G031 adds the 32-bit TIM2 and LPTIMs**.
Fallback: STM32G030K8T6 (LQFP-32, 64 KB, `C431631`) if pins run out.

**Why not an ATtiny (e.g. the ATtiny1616, common on stepper-driven boards):** the N20 encoder gives ~35,000 edges/s at full
speed (10856 counts/rev × ~3.3 rev/s). The STM32 counts them in a hardware timer with no CPU time; the
ATtiny has no quadrature mode, so it would need an interrupt every ~28 µs competing with the bus, and
its 16 KB flash is tight next to a bootloader. A stepper needs no encoder, so the ATtiny suits those designs, not this one.

**Later option: CH32V003** (`C5187096`, TSSOP-20, ~$0.29 vs $1.24, hardware encoder mode). Saves
~$57 over 60 boards, but 16 KB / 2 KB and new tools (WCH-LinkE). Consider for v0.2 (Drew, 2026-10-14).

Pin map, **checked 2026-10-15 against ST's STM32_open_pin_data** (`mcu/STM32G031F(4-6-8)Px.xml`
for the bonded pads, `mcu/IP/GPIO-STM32G03x_gpio_v1_0_Modes.xml` for the AF numbers):

| Pin | Port (co-bonded) | Net | Function | AF |
|---|---|---|---|---|
| 1 | PB7 (PB8) | ENUM_IN | GPIO in | — |
| 2 | PB9 (PC14) | ENUM_OUT | GPIO out | — |
| 3 | PC15 | LED | GPIO out | — |
| 6 | PF2-NRST | NRST | reset, 100 nF | — |
| 7 / 8 | PA0 / PA1 | ENC_A / ENC_B | **TIM2_CH1 / CH2, encoder mode (32-bit)** | AF2 |
| 9 / 10 | PA2 / PA3 | DBG_TX / DBG_RX | USART2 debug | AF1 |
| 11 | PA4 | ISEN_ADC | ADC1_IN4 | analog |
| 12 | PA5 | HALL | GPIO in + EXTI | — |
| 13 / 14 | PA6 / PA7 | MOT_IN1 / MOT_IN2 | TIM3_CH1 / CH2 PWM | AF1 |
| 15 | PA8 / PB0 / PB1 / PB2 | — | **spare** (no-connect) | |
| 16 / 17 | PA9 / PA10 (remap of PA11 / PA12) | RS485_TX / RS485_RX | USART1 | AF1 |
| 18 / 19 | PA13 / PA14 (PA15) | SWDIO / SWCLK | SWD, never reassign | AF0 |
| 20 | PB3 (PB4 / PB5 / PB6) | RS485_DE | USART1_DE (hardware DE) | AF4 |

Firmware notes (as 7SEG §18.1): set `SYSCFG_CFGR1.PA11_RMP/PA12_RMP` before USART1; leave the
co-bonded ports analog (PB8, PC14, PA8/PB0/PB1/PB2 if unused, PA11, PA12, PA15, PB4/PB5/PB6 —
PB4/PB5 carry TIM3_CH1/CH2 alternates and must not fight PA6/PA7); enable PA10's pull-up (RO floats
while this node transmits); the ROM bootloader can't drive DE, hence the custom bootloader (§11).

### 7.2 Motor driver — DRV8870

**DRV8870DDAR** `C86590` (TI, HSOP-8 with exposed pad), 6.5–45 V, 3.6 A peak, Extended, 24,475 in
stock, ~$0.41.

* **Why not the bench TB6612:** 15 V absolute max, too little headroom on a 12 V bus with hot-plug spikes.
  DRV8833 tops out at 10.8 V.
* **Why DRV8870, not DRV8871:** same chip family; the 8870 takes an external sense resistor, which
  also gives the MCU a current reading for jam detection (F5), and costs $0.41 vs $2.05.
* Current limit: I = V_REF / (10 × R_ISEN). With V_REF = 3.3 V and R_ISEN = 0.33 Ω → **~1.0 A**
  (the N20's stall is ≤ 1.1 A; this keeps a stalled row at the 5-pin chain's 3 A, §6.2).
  Sense resistor 0.33 Ω 1 % 1206, ≥ 0.5 W. Final values at step 3.
* IN1/IN2 from TIM PWM: forward / reverse / coast / brake, which also gives the short reverse
  "settle" pulse noted in the HANDOFF.

### 7.3 Sensors

| Sensor | Supply | Signal |
|---|---|---|
| N20 encoder (on the motor's board) | **3.3 V**, 100 nF at the connector | C1 = A, C2 = B; 10 k pull-ups to 3.3 V, then 100 Ω + 1 nF (≈ 100 ns) into the MCU against brushed-motor noise |
| A3144 hall | **+12V_LOCAL** (4.5–24 V; not 3.3 V) | open collector → 10 k pull-up to 3.3 V, then **4.7 k series** + 1 nF. The 4.7 k keeps injection under ~2 mA if 12 V ever lands on OUT (a reversed lead) |

## 8. Mechanical — board outline (step 2; as laid out in §13b)

Measured in Fusion **SFD-Digit-N20 v48** (test 3), module coordinates: x = depth (front face −22,
back +40), y = height, z = width (motor wall at z 0, side plate to z 43).

| Measurement | Value |
|---|---|
| Module | 43 wide × 74 tall × 62 deep |
| Back of the enclosure | **open** today (no back wall yet) |
| Drum + hanging flaps reach back to | x ≈ 26.7 |
| Inside height at the back (floor → ceiling) | y −37.5 → +32.6 = **70.1** |
| Back corner pillars (insert posts) | x ≈ 33–37, y 25.6–32.6 and −37.5 to −30.5 → clear height between them **56.1** |
| Motor wall inner face at the back | z 6.8 (wire channels make it thick here) |
| Side plate inner face | z 40.5 |

**Proposed board: 32 wide × 54 tall × 1.6, standing in the y–z plane at x ≈ 35–38** (behind the
flap sweep, ~8–10 mm clear of the flaps, between the corner pillars), sliding in on two printed rails.

Why 32 wide: the chain connectors are on the left and right edges and must mate across the gap to
the next module's board. A mated right-angle male header (2.5 mm plastic) + female socket (8.5 mm
body) puts the two board edges **~11 mm apart**, so the board is 43 − 11 = **32 mm** wide, and
both side walls need a window at the connector. If the module width changes, the board width
follows: **W = module width − 11**.

**This will change** as the enclosure is refined (back wall, mirroring, rail design, screw-together
row). The KiCad outline will be driven by these few numbers.

Board faces: components on the back face (toward the wall), clear of the flaps. ZH and hall
connectors at the motor (right) edge, near where the motor and hall wires arrive.

## 9. Connectors

### 9.1 Chain (board edges) — 5 pins, 2.54 mm, right angle

Drew, 2026-10-14: **5 pins for now**; 7 (2 × 12 V, 2 × GND) stays an option if the bench needs it.

| Pin | Signal |
|---|---|
| 1 | +12 V |
| 2 | GND |
| 3 | A |
| 4 | B |
| 5 | ENUM (IN on the right edge, OUT on the left edge) |

GND sits between +12 V and the data pair.

* **Right edge (toward the trunk) = male header** `PZ254R-11-05P` `C492413` (1×5 right angle, 3 A, 80 k in stock).
* **Left edge (away from the trunk) = female socket** `PM254-1-05-W-8.5` `C2897387` (1×5 right
  angle, 8.5 mm body, 2.7 k in stock; the SplitFlap v5.1 board uses the 4-pin `C2897386`).
* Power flows right → left, so the **live end of a row is a shrouded socket**, never bare pins.
* The rightmost digit's male header takes the row's plug from the trunk (5-pin 2.54 housing).
* A cable between modules (JST) remains possible if the boards don't line up.

### 9.2 Others

| Ref | Connector | LCSC | Notes |
|---|---|---|---|
| J_MOT | **JST ZH 1.5 mm 6-pin** (B6B-ZR) **+ 6 solder pads (J4)** | `C157984` | **Pin 1 = M1: M1 · GND · C1 · C2 · VCC · M2** (2026-10-15: the order web listings give, the reverse of the silkscreen reading M2 VCC C2 C1 GND M1; Drew's guess was M1). **Meter-check at bring-up:** reversed, 3.3 V lands on the encoder's GND. Waveshare's lead is **bare at the far end**: plan is a double-ended ZH 6-pin cable, **pin 1 to pin 1** (not the reversed kind), 10–20 cm; the pads take the bare lead as a fallback (Drew, 2026-10-14) |
| J_HALL | **Compatible with the SplitFlap v5.1 hall sensor lead (`WSH130`):** JST PH 2.0 mm 3-pin vertical, B3B-PH-K footprint | `C2320` (same part as v5.1; `C131339` JST original as alternate) | **pin 1 OUT · pin 2 GND · pin 3 +12 V**, v5.1's order, so existing hall leads plug straight in (v5.1 feeds 5 V; this board feeds 12 V, fine for the A3144's 4.5–24 V) |
| J_SWD | pads (tag-connect style or 1.27 mm) | — | first flash only; reachable before the board goes in the module |
| JP_TERM | 2-pin header + shunt | `C492401` | bench only |

## 10. Draft BOM

LCSC data from the local JLC snapshot (2026-08-03). **Re-check stock live before ordering.**

| Ref | Part | LCSC | Tier | ~$ |
|---|---|---|---|---|
| U1 | STM32G031F8P6 | C529334 | Ext | 1.24 |
| U2 | GM3085E | C269864 | Ext | 0.12 |
| U3 | HT7533-1 | C14289 | **Basic** | 0.13 |
| U4 | DRV8870DDAR | C86590 | Ext | 0.41 |
| Q1 | AO3401A | C15127 | **Basic** | 0.07 |
| DZ1 | MM1Z10 | C107591 | Ext | 0.02 |
| D2 | SMAJ18A | C908771 | Ext | 0.03 |
| F1 | BSMD1812-200-33V | C7433877 | Ext | 0.16 |
| J1 / J2 | 5-pin right-angle header / socket | C492413 / C2897387 | Ext | 0.05 / 0.15 |
| J_MOT, J_HALL | ZH 6 / PH 3 | C157984 / C2320 | Ext | 0.15 / 0.04 |
| R, C, LED | 0603 passives, sense resistor, bulk cap | Basic where possible | | ~0.3 |
| | | | **≈ $2.9 / board** + PCB + JLC setup (~$3 per Extended part per order) |

## 11. Firmware split and updates

* **ESP32:** WiFi, data, table logic, discovery/addressing, per-module settings (pushed at boot,
  the module stores nothing permanent), GO/sequence scheduling, status polling, firmware distribution.
* **Module:** encoder + speed loop, homing, go-to-flap, settle pulse, jam detection, status.
* **Bootloader** (~4 KB) in the module's flash: the first flash is by SWD on the bench; after that
  the ESP32 broadcasts new firmware to all modules at once over RS-485 and each checks a CRC before
  switching. Firmware work only; the board just needs the SWD pads and the 64 KB part.

## 12. Lessons carried over from 7SEG's reviews

| 7SEG finding | What we do |
|---|---|
| LDO symbol had VIN/VOUT swapped | check every regulator pinout against the datasheet at step 3 |
| Reverse-polarity FET drawn backwards | drain to fuse, source to load; note it on the schematic |
| Wrong LCSC numbers (value / package) | verify every LCSC number's value **and** package |
| Enumeration couldn't start (no host ENUM pin) | trunk plug carries ENUM to the row's first board |
| JLC rotated a connector 180° | check every connector in JLC's placement preview |
| DE floating during reset | 100 k pull-down on DE/RE |
| Hot-plug into an unpowered MCU through ENUM | 1 k series on ENUM in/out |

## 13a. Schematic (step 3)

`split-flap-module-board.kicad_sch`, generated by `scripts/gen_schematic.py` (pin
positions read from KiCad's own libraries, `scripts/symlib.py`). `python scripts/build.py`
regenerates the project + schematic, runs ERC (**0 errors, 0 warnings**, `fab/erc-report.txt`),
exports `split-flap-module-board-schematic.pdf` and writes every net to `fab/netlist.txt`.

Blocks A–H on one A3 sheet: chain + protection, 3.3 V rail, MCU, RS-485 + enumeration, motor
driver, motor/encoder connector, hall, debug/LED/test points.

Decisions made while drawing:

| Item | Choice |
|---|---|
| GM3085E symbol | project symbol `sfmb:GM3085E` = KiCad's MAX3485 flattened (same pinout). The stock MAX3485 always raises an ERC lib-mismatch warning (7SEG's ERC has it too) |
| Bulk 12 V cap | C1 **100 µF 35 V 6.3 × 5.4** (`C3151830`, ROQANG RVT1V101M0605): 7SEG's 6.3 × 7.7 part was too tall for the ~8–10 mm between the board and the flaps |
| VM bypass | C2 + C10 100 nF 50 V (`C14663`) — one at the input, one at U4 |
| VREF | tied to +3V3 → I_TRIP 1.0 A with R7 0.33 Ω (`C858786`, Yageo 0.5 W 1206) |
| ISEN → ADC | R8 1 k + C9 100 nF (τ 100 µs) |
| MCU decoupling | C5 100 nF + C6 1 µF at VDD; C4 10 µF at the LDO output |
| Debug | J6 7-pad header, DNP: +3V3 · SWDIO · SWCLK · NRST · GND · TX · RX |
| Motor pads | J4 6 × 2.54 mm pads (DNP) beside J3, same nets |
| Test points | TP1–TP6: +12V_LOCAL, +3V3, A, B, ISEN_ADC, GND |
| JP1 | termination jumper, DNP (hand-fit for the bench) |
| TVS | D1 SMAJ18A `C908771` (52 k in stock; 7SEG's `C571369` had 5 k) |

## 13b. Layout (step 4)

**Board:** 32 × 54 mm, 2 layers, 1.6 mm, JLC standard rules (0.2 mm clearance, 0.3 mm vias, 0.3 mm
copper-to-edge). Every part on the **F side, which faces the drum** (tallest: J5 PH 6 mm, C1 5.4 mm,
J3 ZH 4.5 mm). Test points TP1–6 are bare pads on the back. Top and bottom 1.5 mm are the **rail
grooves** (no parts).

| Region (board mm, +x toward the trunk, +y down) | What |
|---|---|
| top edge, x 16 | **M3 retaining-screw notch** (Drew, 2026-10-18): half-round R 1.7 into the top edge; the screw goes into an enclosure boss and its head clamps the board, so it slides out on the rails with the screw only loosened. Copper keep-out R 3.2 on both layers (2 GND stitching vias dropped). Use a socket-cap head (5.5 mm): +12V_CHAIN copper starts at y 3.4, so a 7 mm pan head/washer would sit over it unless nylon. The top rail stops short of the notch |
| y 4.0–14.2, full width | **chain band**: J2 socket (x 1.6, body overhangs the left edge ~8.4 mm) and J1 header (x 30.4, plastic + 6 mm pins overhang the right edge), pin 1 at the top. +12V_CHAIN (1.2 mm), GND (1.0), A, B run straight across on F.Cu |
| right column under J1 | F1 → Q1/DZ1/R1 → D1, ENUM_IN R4/R5, LDO U1 (180°) + C4/C3 beside its pins |
| centre | **C1** (rotated 90°, + toward U4, ~10 mm from VM). Moved 2026-10-19 from the right column, where it sat in the hall-wire path at the motor side of the enclosure; swapped with the LDO group. Flap-wall gap unchanged (7.0, same height on the board) |
| left / centre | RS-485 U3 + C8/R2/R3/JP1, MCU U2 + C5/C6/C7, ENUM_OUT R6 |
| lower centre | encoder, hall and ISEN filters, LED |
| lower right | DRV8870 U4 (thermal pad + 6 vias), R7 sense, C10/C2 VM bypass |
| bottom edge | J5 hall (PH), J3 motor (ZH) |
| left edge | J6 SWD/UART pads (DNP), J4 motor pads (DNP) |

**Mating geometry:** J1's header plastic ends ~2.4 mm past the right edge; J2's socket mouth sits
~8.4 mm past the left edge; mated, the two board edges are **~10.8 mm apart**, which is where both
enclosure side walls go (windows for the connector bodies). Board width = module width − ~11.

**Revised 2026-10-18 (Fusion fit check):** modules butt side by side with no side plate between them, so
the pitch is **41**, not 43, and the header plastic hit the neighbour's socket by 1.87. J1/J2 each moved
**1.0 mm inboard** (x 29.4 / 2.6): socket mouth 7.43 past the left edge, header plastic 1.44 past the
right edge, 40.87 overall (0.13 gap at the joint, pins 5.87 into the socket, as checked before). In the
enclosure: socket mouth flush with the left wall face → **board x 0 at 7.43 in from it**. **Connector tabs**
carry the connector bodies instead of their pins: the outline juts to x −6.43 (1.0 short
of the socket mouth) and x 33.14 (0.3 short of the header plastic), from the top edge to y 16.5, 0.5
fillets inside. No copper on the tabs. Board extents x −6.43…33.14 × 54. All outer corners rounded: body bottom r 2.0, female tab r 1.5, male tab r 1.0 top / 0.5 bottom (it's 1.14 wide).

**Routing:** GND is both pours (B.Cu everywhere, F.Cu around the parts) plus a fan-out via at every
GND pad and connectivity-checked stitching; everything else by Freerouting (net-class widths: chain
1.0, 12 V 0.6, motor outputs/ISEN ≥ 0.5, 3V3 0.4, signals 0.25). `widths.py` audits them after every
route (Freerouting has dropped power widths before). ~75 vias, ~400 track segments.

**Checks (2026-10-15):** ERC 0/0; DRC 0 errors, 0 unconnected, schematic parity clean. Two warnings
are intentional: J1/J2 differ from the library because their off-board silk was trimmed.

**Pipeline:** `python scripts/build.py` (schematic + ERC) then
`python scripts/route_all.py` (place → GND fan-out → Freerouting → finish → prune →
stitch/fill → silk → width audit → DRC → fab outputs → review images), ~10 minutes. Freerouting
varies run to run; re-check the DRC after any rebuild.

**Fab package (`fab/`):** Gerbers + drill (`gerbers/`, zipped), JLC BOM (25 lines, all
with LCSC numbers) and CPL (42 placed parts; DNP J4/J6/JP1 and the TPs excluded), STEP, layers PDF,
renders and review images in `images/`, ERC/DRC reports, `netlist.txt`.

## 13. Open questions

| # | Question | Blocks |
|---|---|---|
| 1 | Final enclosure back: rails (top/bottom edges, 1.5 mm kept clear), back wall, pillar positions, wall windows for the chain connectors (~10.8 mm between boards) | **fit-check the STEP in Fusion before ordering** |
| 2 | ~~Waveshare lead~~ **answered:** bare at the far end → ZH header + fallback pads, double-ended ZH cable | — |
| 2a | Motor ZH pin 1: **set to M1** (web listings + Drew's guess, not confirmed by a datasheet). Meter-check: the encoder's GND pin should ring through to the motor's encoder-board ground | bring-up |
| 3 | N20 running current on the real drum (bench) | power numbers only |
| 4 | Stock / second source for the 5-pin right-angle female socket | BOM |
| 5 | ~~THT connectors~~ **decided 2026-10-15 (first JLC upload):** Drew hand-solders **C1** only (SMD electrolytic is Standard-PCBA-only at JLC: +$25 and a forced 70 × 70 mm panel); it's left out of the JLC BOM/CPL and listed in `fab/*-hand-solder.csv`. JLC places every connector; J1, J2, J5 landed rotated 90° in the first preview and are fixed by hand in the preview | — |
| 6 | Trunk design (loom / PCB rail / bus bars), row plug, termination location | separate design: [`builds/league-table/rail.md`](../../../builds/league-table/rail.md) |
| 7 | **JLC rotations**: U1/U2/U3/U4/Q1 carry 7SEG's preview corrections (`scripts/jlc_cpl.py`); every other part, and the THT connectors, are unverified. Check pin 1 / polarity of every part in JLC's placement preview | order |
| 8 | Chain connectors overhang the board edges (J2's socket body ~8.4 mm, held only by its pins). Fine on the bench; the enclosure window should support it | enclosure |
| 9 | B.Cu ground plane is broken into a few islands by bottom-side signal hops (all stitched to the main plane; DRC clean). Acceptable for these slow signals; a v0.2 could keep B.Cu solid | v0.2 |
| 10 | 5 of 51 silkscreen references sit a little away from their parts (no room); `fab/images/*-assembly-top.png` shows every reference exactly on its part | none |
| 11 | Socket `C2897387` stock (2.7 k in the August snapshot) and every Extended part: re-check live stock at order | order |

## 14. Bring-up log

**2026-10-27, board #1** (JLC-assembled, C1 and the motor lead hand-soldered by Drew):

| Check | Result |
|---|---|
| Unpowered, J1 pin 1 (+12V) to J1 pin 2 (GND) | no short; reading rose then settled (caps charging) |
| Unpowered, J6 pad 1 (+3V3) to J6 pad 5 (GND) | no short; reading rose, higher than the 12 V rail |
| Motor lead GND to encoder-board GND (open item 2a) | **not verified**: Drew could not prove it |
| Motor winding, J3 pin 1 to pin 6 | **not verified** |

So the motor pin order is still unconfirmed. Safe next step is first power on a current-limited
supply; with the motor connected, if the encoder's pin order is reversed it would put 3.3 V on its GND,
so read J3 pin 5 against J3 pin 2 with no motor first. Bring-up firmware: `firmware/ltm-bringup/` (builds; not yet flashed).
Annotated probe-point picture: `images/bringup-meter-points.png`.

**Later 2026-10-27, board #1:** first power OK (12 V, supply current display 0, 3.33 V on 3V3, Q1/U4 not warm). ST-Link V2 clone needed a WinUSB driver (Zadig) before OpenOCD could open it. SWD flash over J6 works (verified OK; PIO board `nucleo_g031k8`, upload `stlink`). LED D2 lights (PC15 high), so D2's orientation is right.
Firmware lessons (`firmware/ltm-bringup`): this Arduino core mis-reads a raw `PC_15`/`PA_x` PinName in `pinMode()` (configured the wrong pin), and `HardwareTimer::setPWM(PA_6/PA_7)` hangs in `setMode`. LED and PWM pins are now set up by register/HAL, hall/ISEN via `pinNametoDigitalPin()`.
Debug trick: halt over SWD and read GPIO registers with openocd (`read_memory 0x50000814 32 1` = GPIOC ODR).

**Later still, board #1 (bring-up passed):** hall (A3144 on J5) pulls the LED solid with a magnet. Motor on the **J4 pads** (not J3), wire order read from the motor's encoder-board silkscreen: matches J3/J4 (M1 GND A B 3V3 M2), so **open item 2a is resolved**. Encoder counts hand-turned and under power. `firmware/ltm-bringup` env `autotest` (motor 50 % fwd 1 s, rev 1 s, LED reports): **3 blinks = pass**, forward counts rose and reverse fell, so TIM2 sign and motor direction agree with no flip needed.
Not yet checked on this board: ISEN current reading, RS-485, ENUM chain, a second board in the chain, motor on J3 via the ZH cable, 25 % duty startup (the motor did not start in 1 s at 25 %; 50 % does).
Firmware lesson 3: `HardwareTimer::resume()` with no bound pin leaves TIM3 stopped and its outputs disabled; set `TIM3->CCER` and `CR1.CEN` directly.

### 14.1 Pick up here (written 2026-10-27)

Board #1 works end to end on the bench. Picture aids in `images/`: `bringup-meter-points.png` (probe points J1/J6/J3), `bringup-led-d2.png`, `bringup-current-measure.png`. Bench: ST-Link V2 clone (needs the Zadig WinUSB driver), 12 V bench supply, Crenova MS8233D meter (mA jack is the right-hand one, red lead back to VOhm after).
Next, in order:
1. Re-flash board #1 with `pio run -e ltm -t upload` (the `autotest` build is on it and spins the motor 10 s after every reset).
2. Repeat the unpowered shorts check (J1 pin 1 to 2, J6 pad 1 to 5), power-up and flash on boards #2-#10. Look at D2 and the hall/J3 connectors too.
3. Move the motor from the J4 pads to J3 with a ZH cable once one is available (J3 untested with a motor).
4. Read ISEN (PA4, 0.33 ohm sense) under a held motor and set the jam threshold; fix the 25 % startup.
5. RS-485 + ENUM chain firmware (USART1 remap PA9/PA10, hardware DE on PB3, design sections 4-5), then two boards chained, then the bootloader (section 11).
Open hardware items still open: 3, 4, 7 (JLC rotations: D2 turned out fine), 8.

**2026-10-28: bus firmware written, builds, not yet flashed.** `firmware/ltm-node` (envs `node1..3` = fixed
bus address, `bridge` = spare board as the ESP32's RS-485 adapter via J6 pads 5-7) and `firmware/ltm-host`
(ESP32 on COM4, text commands as in n20-bench). Wiring pages: `builds/league-table/ltm-3-module-wiring-bridge.html`
(no adapter) and `ltm-3-module-wiring.html` (MAX3485 module, ordered option). Plan: bridge + one module first, then 3.
Drive changed to slow decay (drive/brake PWM) to match the bench TB6612; `dir` defaults to 1 (bench) and is unverified on this board.

**2026-10-28/29: RS-485 works.** Bridge + board #1 (address 1, digit, uid 00490028-…) found, homed and calibrated:
`cal` measured **10855 counts/rev** with the "78 RPM" motor (same as the bench motor's 10856, so that one was a
~1:388 gearbox too); revs agree within 6 counts. A second board flashed `node2` (name module, uid 00390029-…) also answers.
**Faulty board:** the first board flashed as `node2` receives (193 bytes, 0 CRC errors read over SWD) and its PB3 (DE)
and PA9 (TX) toggle correctly, but its replies never reach the bus: suspect a U2 joint (DE pin 3 / DI pin 4) or U2 itself.
Set aside, not yet metered (`images/bringup-bus-ab-probe.png` shows the A/B probe points for the forced-driver test).

**2026-11-04: host moved to an ESP32-C3 Super Mini** (`ltm-host` env `c3`, MAX3485 5-pin module, wiring page board switch).
Board 1 turned the **wrong way** again: its flashed build predates the `dir 0` default, and the fix had only ever lived in the
old ESP32's saved settings (pushed back on every module reset). The C3 starts empty, so the board fell back to its own
compiled `dir 1`. Source default is `dir 0` (`ltm_proto.h`); **reflash board 1 (and any board flashed before 2026-10-29
20:37) with the current build** so the direction no longer depends on which host is attached. Calibration (cpr, foff,
lead) was also only on the old ESP32.
