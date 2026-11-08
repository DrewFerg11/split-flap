# Flap sets — the single list (52-flap modules)

**This file is the one place for what goes on each flap.** The build READMEs (`stl/sf-name-flaps/`,
`stl/sf-digit-flaps/`) and the outline files (`build/names200.json`, `build/digits52.json`) follow it.
Updated 2026-10-18 for the **52-flap** name (200 face) and digit modules. The 30-flap plan this file used to
hold is kept at the end for reference.

Status key: ✅ built (in the current print files) · 🔲 open (blank placeholder, to be decided) · 💡 candidate

## How a set works (rules that constrain choices)

- **52 positions per drum = 52 items.** Each position shows the front of one flap over the back of the one
  before it, so each flap carries the **top half of its own item** and the **bottom half of the next**.
  Changing item *k* means reprinting **flap k and flap k−1**.
- **The drum only turns one way.** Duplicates placed half a turn apart (26 slots) mean any item that appears
  twice is never more than 26 flaps away.
- **Colours at 47–52 on every drum, right before the blank** (Drew 2026-10-24): from home (blank) every module
  travels the same distance to a colour, so a whole-board colour change lands at once; colour → black is 1–6
  flaps. Cycling colours steps one flap, except the wrap back to the first colour (nearly a full turn).
- **Flap 01 = blank = home on every drum** (name, digit, header name, header digit; Drew 2026-10-18).
  A module homes to blank, and the list starts there. Firmware maps items to slots, so slot numbers
  don't need to mean anything else. (The built 52-flap print files still use the old numbering, home
  = 51, until they're regenerated; see the build READMEs for which hole.)
- **Sizes:** League Gothic, 32.7 mm cap-to-descender on every flap. Name: up to 187.7 mm wide, longer text
  is squeezed sideways only (Crystal Palace 93 %, Premier League 95 %). Digit: one character, or two squeezed
  into 26.6 mm (GO, AL, 10–19).
- **Colours:** black flap, white text (filament 2); digit colour flaps use filaments 3–5.
- **Trademarks:** club crests and league logos are trademarks; builders decide what to print.

---

## All sets side by side — by flap number (firmware numbering, 0–51)

The tables below number slots 01–52; the firmware numbers flaps 0–51. **Flap = slot − 1**, so flap 0 is slot 01,
the blank (home), on every drum. This table follows the **planned** sets; "open" is an undecided slot.
The header row has two drums (name and digit), so there are four columns.

| Flap | Name | Header name | Digit | Header digit |
|---|---|---|---|---|
| 0 | blank (home) | blank (home) | blank (home) | blank (home) |
| 1 | ARSENAL | PREMIER LEAGUE | −5 | 0 |
| 2 | ASTON VILLA | MATCHWEEK | −4 | 1 |
| 3 | BOURNEMOUTH | LIVE | −3 | 2 |
| 4 | BRENTFORD | RESULTS | −2 | 3 |
| 5 | BRIGHTON | FIXTURES | −1 | 4 |
| 6 | CHELSEA | POINTS | − | 5 |
| 7 | COVENTRY CITY | GOAL DIFFERENCE | 0 | 6 |
| 8 | CRYSTAL PALACE | GOALS FOR | 1 | 7 |
| 9 | EVERTON | GOALS AGAINST | 2 | 8 |
| 10 | FULHAM | PLAYED | 3 | 9 |
| 11 | HULL CITY | POSITION | 4 | R |
| 12 | IPSWICH TOWN | FA CUP | 5 | L |
| 13 | LEEDS UNITED | FA CUP QF | 6 | blank |
| 14 | LIVERPOOL | FA CUP SF | 7 | 0 |
| 15 | MAN CITY | FA CUP FINAL | 8 | 1 |
| 16 | MAN UNITED | LEAGUE CUP | 9 | 2 |
| 17 | NEWCASTLE | LEAGUE CUP QF | 10 | 3 |
| 18 | NOTT'M FOREST | LEAGUE CUP SF | 11 | 4 |
| 19 | SUNDERLAND | LEAGUE CUP FINAL | 12 | 5 |
| 20 | TOTTENHAM | UCL MATCHDAY | 13 | 6 |
| 21 | OPPONENT | UCL PLAY-OFF | 14 | 7 |
| 22 | KICK OFF | UCL LAST 16 | 15 | 8 |
| 23 | 1ST HALF | UCL QF | 16 | 9 |
| 24 | HALF TIME | UCL SF | 17 | R |
| 25 | 2ND HALF | UCL FINAL | 18 | L |
| 26 | EXTRA TIME | UEL MATCHDAY | 19 | blank |
| 27 | PENALTIES | UEL PLAY-OFF | 20 | 0 |
| 28 | FULL TIME | UEL LAST 16 | 21 | 1 |
| 29 | AGGREGATE | UEL QF | 22 | 2 |
| 30 | POSTPONED | UEL SF | 23 | 3 |
| 31 | GOAL! | UEL FINAL | :00 | 4 |
| 32 | VAR CHECK | UECL MATCHDAY | :15 | 5 |
| 33 | NO GOAL | UECL PLAY-OFF | :30 | 6 |
| 34 | RED CARD | UECL LAST 16 | :45 | 7 |
| 35 | MONDAY | UECL QF | ↑ | 8 |
| 36 | TUESDAY | UECL SF | ↓ | 9 |
| 37 | WEDNESDAY | UECL FINAL | = | R |
| 38 | THURSDAY | COMMUNITY SHIELD | ? | L |
| 39 | FRIDAY | SUPER CUP | ball | open |
| 40 | SATURDAY | CLUB WORLD CUP | PL lion | open |
| 41 | SUNDAY | FRIENDLY | trophy | open |
| 42 | EUROPA LEAGUE | INTERNATIONAL BREAK | wildcard | open |
| 43 | CONFERENCE LEAGUE | SEASON STARTS IN | wildcard | open |
| 44 | open | open | wildcard | open |
| 45 | divider | divider | divider | open |
| 46 | yellow | yellow | yellow | yellow |
| 47 | CL blue | CL blue | CL blue | CL blue |
| 48 | Europa orange | Europa orange | Europa orange | Europa orange |
| 49 | Conference green | Conference green | Conference green | Conference green |
| 50 | red | red | red | red |
| 51 | white | white | white | white |

The divider sits at 45 and the colours at 46–51 on every drum (divider moved here 2026-11-05). Kept in step with the per-set tables below: change those first, then this one.

---

## Name module — 52 flaps (200 face)

### Planned set (Drew, 2026-10-19) — replaces the built set below

The display tracks EPL clubs in **every competition** they play (league, FA Cup, League Cup, UCL / UEL /
UECL). The header row names the competition; club rows show the EPL club's own name, and a non-EPL
opponent shows **OPPONENT**. When two EPL clubs meet in a cup, both real names show.

| Slot | Item | Status |
|---|---|---|
| 01 | blank (home) | 💡 |
| 02–21 | **Clubs** (alphabetical): ARSENAL, ASTON VILLA, BOURNEMOUTH, BRENTFORD, BRIGHTON, CHELSEA, COVENTRY CITY, CRYSTAL PALACE, EVERTON, FULHAM, HULL CITY, IPSWICH TOWN, LEEDS UNITED, LIVERPOOL, MAN CITY, MAN UNITED, NEWCASTLE, NOTT'M FOREST, SUNDERLAND, TOTTENHAM | 💡 |
| 22 | OPPONENT (any non-EPL team) | 💡 |
| 23–30 | **Match flow**, in order: KICK OFF, 1ST HALF, HALF TIME, 2ND HALF, EXTRA TIME, PENALTIES, FULL TIME, AGGREGATE | 💡 |
| 31 | POSTPONED | 💡 |
| 32–35 | **Events:** GOAL!, VAR CHECK, NO GOAL, RED CARD | 💡 |
| 36–42 | **Days:** MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY (fixtures view: day on the status row, kick-off time on its digits) | 💡 |
| 43–44 | **Competitions:** EUROPA LEAGUE, CONFERENCE LEAGUE (head a block of rows when both play the same night) | 💡 |
| 45 | open | 🔲 |
| 46 | divider bar (same slot on every drum, right before the colours; 2026-11-05) | 💡 |
| 47–52 | **Colours, all together:** yellow, CL blue, Europa orange, Conference green, red, white (same slots and order on all four drums); 52's back carries the blank's bottom | 💡 |

- **Match flow in order:** each step of a live game is one flap forward (KICK OFF → 1ST HALF → … → FULL TIME).
  Event flashes (GOAL!, VAR CHECK …) cost one full turn wherever they sit (the drum turns one way).
- **Colour flaps (Drew 2026-10-24):** whole rows in colour with the digit colour flaps: zone flash, champions,
  goal wave, rainbow, flags (mockup, "Colour patterns"). Same filaments and black tip strip as the digit colours;
  grouped so only flaps 46–52 carry colour.
- **Cut for the colours (Drew 2026-10-24):** DELAYED (KICK OFF with the new time says it), ABANDONED (about once
  every few seasons), ADDED TIME (the status row keeps counting: 2ND HALF 93 = 90+3, 1ST HALF 47 = 45+2).
- **One blank** (as the digits). Spare rows in live mode (21 rows, 6 games × 3) show it.
- **Clubs:** Drew reprints club flaps each summer as needed (no promoted-club spares). A changed club means
  reprinting its flap and the one before it; alphabetical order may shift neighbours.
- **Moved to the header set:** PREMIER LEAGUE, MATCHWEEK, LIVE, competitions, rounds.
- **EUROPA LEAGUE / CONFERENCE LEAGUE here too (Drew 2026-10-24):** both are played on Thursday night but the
  header names one competition, so the other one's games sit under a row with its name. CONFERENCE LEAGUE ~76 %
  squeeze. Champions League doesn't need one (Tuesday / Wednesday).
- **Dropped:** the extra blanks, zone labels (no free row in table mode; the digit colour flaps mark zones),
  HOME / AWAY / VS (the 3-rows-per-game layout shows home on top).
- **Reuse from the built set:** the blank with ARSENAL on its back (→ 01), ARSENAL … SUNDERLAND (their backs
  still match), 1ST HALF, HALF TIME: 22 flaps. The other 30 are new.

### Built set (was stl/name-52-200-1, removed 2026-11-04 — git history; 2026-10-18; numbered with home = 01)

| Slot | Item | Status |
|---|---|---|
| 01–02 | blank (home), blank with ARSENAL's bottom half on its back | ✅ |
| 03–22 | the 20 clubs above | ✅ |
| 23 | PREMIER LEAGUE | ✅ |
| 24–27 | 1ST HALF, HALF TIME, 2ND HALF, FULL TIME | ✅ |
| 28 | GOAL! | ✅ |
| 29 | divider bar | ✅ |
| 30–32 | blank | ✅ |
| 33–52 | blank placeholders | ✅ |

---

## Header row (row 21) — its own flap set

The display will likely have **21 rows**: row 21 (top) is the header, built from the same name + 2 digit
enclosures with **header-only flap sets**. The name flap says what the board is showing (competition and stage,
or which stat); the digits carry the matchweek, round, matchday, leg or a countdown. Views are drawn in the
[Premier League demo](https://drewferg11.github.io/split-flap/demo/premier-league/) (it replaced the HTML mockup).

### Header name set (52) — Drew 2026-10-24

| Slot | Item | Digits | Example | Status |
|---|---|---|---|---|
| 01 | blank (home) | | | 💡 |
| 02–03 | PREMIER LEAGUE, MATCHWEEK | blank / 1–38 | MATCHWEEK 12 | 💡 |
| 04–06 | **Modes:** LIVE, RESULTS, FIXTURES | blank | | 💡 |
| 07–12 | **Stat labels:** POINTS, GOAL DIFFERENCE, GOALS FOR, GOALS AGAINST, PLAYED, POSITION | blank | GOAL DIFFERENCE | 💡 |
| 13–16 | FA CUP, FA CUP QF, FA CUP SF, FA CUP FINAL | R3–R5 / blank | FA CUP R4 | 💡 |
| 17–20 | LEAGUE CUP, LEAGUE CUP QF, LEAGUE CUP SF, LEAGUE CUP FINAL | R1–R4 / blank / L1–L2 (SF) | LEAGUE CUP SF L2 | 💡 |
| 21–26 | UCL MATCHDAY, UCL PLAY-OFF, UCL LAST 16, UCL QF, UCL SF, UCL FINAL | 1–8 / L1–L2 / blank | UCL LAST 16 L2 | 💡 |
| 27–32 | UEL MATCHDAY, UEL PLAY-OFF, UEL LAST 16, UEL QF, UEL SF, UEL FINAL | 1–8 / L1–L2 / blank | UEL MATCHDAY 3 | 💡 |
| 33–38 | UECL MATCHDAY, UECL PLAY-OFF, UECL LAST 16, UECL QF, UECL SF, UECL FINAL | 1–6 / L1–L2 / blank | | 💡 |
| 39–42 | **Other competitions:** COMMUNITY SHIELD, SUPER CUP, CLUB WORLD CUP, FRIENDLY | blank | | 💡 |
| 43–44 | INTERNATIONAL BREAK, SEASON STARTS IN | blank / days | SEASON STARTS IN 42 | 💡 |
| 45 | open | | | 🔲 |
| 46 | divider bar (as the name divider, same slot on every drum; 2026-11-05) | blank | | 💡 |
| 47–52 | **Colours:** yellow, CL blue, Europa orange, Conference green, red, white; 52's back carries the blank's bottom | blank | colour patterns | 💡 |

- **Stat labels:** standings can cycle points / goal difference / goals for / against / played; the header says
  which number the rows show. POSITION is for the Champions League league phase (36 clubs: 1–8 last 16, 9–24
  play-off).
- **QF / SF kept (Drew 2026-10-24):** the domestic cups name their late rounds, not number them (the FA Cup
  quarter-final is "R6" only on paper), and European knockout stages have no numbers at all, so the round digits
  alone don't cover them. Spelled out they're too narrow (LEAGUE CUP QUARTER-FINAL ~56 %, FA CUP QUARTER-FINAL
  ~69 %). They cost 4 domestic + 6 European slots, and there's room.
- **INTERNATIONAL BREAK spelled out** (~69 % squeeze, the tightest flap); INTL BREAK if it reads badly.
- Use **LEAGUE CUP**, not the sponsor's name (it changes). UCL / UEL / UECL: UEFA's own short names.
- Squeeze estimates (League Gothic advance widths, calibrated PREMIER LEAGUE 95 % / CRYSTAL PALACE 93 %):
  CONFERENCE LEAGUE 76 %, COMMUNITY SHIELD 81 %, SEASON STARTS IN 85 %, LEAGUE CUP FINAL 87 %,
  GOAL DIFFERENCE 91 %. Confirm when the outlines are generated.

### Header digit set (52, same set on both modules)

| Slot | Item | Status |
|---|---|---|
| 01–13 | blank (home), 0–9, **R** (round), **L** (leg) | 💡 |
| 14–26 | blank, 0–9, R, L (second copy) | 💡 |
| 27–39 | blank, 0–9, R, L (third copy) | 💡 |
| 40–46 | 7 open | 🔲 |
| 47–52 | **Colours:** yellow, CL blue, Europa orange, Conference green, red, white; 52's back carries the blank's bottom | 💡 |

- Three copies of the 13 numbers (was four), so any number change is ≤ 13 flaps; the fourth copy's slots went to
  the colours (Drew 2026-10-24) so the header row joins colour patterns across all 21 rows.
- The left module only ever shows blank, 1, 2, 3, R or L; the right shows 0–9.

---

## Digit module — 52 flaps

### Planned set (Drew, 2026-10-18) — replaces the built set below

Numbers run like a number line: blank → −5 … −1 → − → 0 → 9 → 10 … 23, one copy each. A rising number
(points, a score, the tens of a 3-digit number, goal difference improving) is always **one flap forward**.

| Slot | Item | Status |
|---|---|---|
| 01 | blank (home; the left module's leading blank) | 💡 |
| 02–07 | −5, −4, −3, −2, −1, − (left module: goal difference to −59; − alone = −1…−9, next to 0) | 💡 |
| 08–17 | 0–9 | 💡 |
| 18–31 | 10–23 (left module's two-digit flaps: a pair shows 0–199; 20–23 for 24-hour kick-off times) | 💡 |
| 32–35 | :00, :15, :30, :45 (right module: kick-off minutes, colon on the left so "17 :30" reads as a time; :00 also the left module's midnight hour) | 💡 |
| 36–39 | ↑, ↓, = (position movement), ? (data unavailable) | 💡 |
| 40–42 | ball, PL lion, trophy (simple PL-trophy silhouette: crown on top, handles) | 💡 |
| 43–45 | **Wildcard** (builder's choice): Liver bird, Liverpool jersey (red shirt silhouette), boot (adidas Copa Mundial side view: white outline, three stripes and sole on the black flap) | 💡 |
| 46 | divider (bar at the same height and thickness as the name divider, so a divider row reads as one line; same slot on every drum, right before the colours — moved here 2026-11-05) | 💡 |
| 47–52 | **Colours, all together:** yellow (champions / yellow card), CL blue, Europa orange, Conference green, red (relegation / red card), white; 52's back carries the blank's bottom | 💡 |

- **No duplicate 0–9:** a falling number (a score reset, goal difference rising back towards zero) takes up
  to a full turn, and the right digit wraps 9 → 0 over ~43 flaps (e.g. once every 10 minutes when showing
  the match minute).
- **Uses of 10–19 (kept, Drew 2026-10-18):** extra-time minutes 91–120 (cups), kick-off hours, goals
  for/against ≥ 100, points ≥ 100, other sports (NBA scores, MLB wins, NHL points), and two 0–19 numbers
  per row (e.g. NFL W–L).
- **Kick-off times (fixtures view):** left = hour, right = :00 / :15 / :30 / :45, in the time zone the
  controller is set to. Every time zone's offset is a multiple of 15 minutes, so these four cover any
  zone. 12-hour uses 1–12; 24-hour uses 20–23 too (in the set for builders on 24-hour clocks).
  The hours run straight on from 19, so a later kick-off is always further forward.
- **Negatives in number-line order (Drew 2026-10-24):** −5 … −1, − sit between blank and 0, so goal
  difference improving is 1 flap per step; getting worse (e.g. −9 → −10, − → −1) takes a full turn. The
  left module's blank → 1 (a number reaching 10) is 8 flaps instead of 2. Mode switches take about a
  full turn anyway, so the order is for reading the list, not speed.
- **Dropped:** ' (minute mark): a two-module pair can't show "67'". Also the second 0–9, two blanks,
  GO AL LI VE and KO HT FT (the name flaps say GOAL!, LIVE, HALF TIME etc.), W D L (form needs more
  digit modules than a row has), + (a plus is implied; only negatives get a sign).
- **Goal difference:** − on the left module covers −1…−9; the squeezed −1 … −5 flaps (like 10–19) cover
  −10…−59. Bottom clubs pass −39 most seasons; −6 (to −69, Sheffield Utd 2023–24) is left out for now and
  can replace a wildcard slot later (beyond −59 the display shows ?).
- **Colours grouped:** a flap's back shows the next item's bottom half, so grouped colours keep the colour
  filaments on 7 flaps (46–52) instead of spreading them around the drum. Each is two solid colours, no text.
  Yellow and red double as the cards (no separate card flaps).
- **No competition icons (CL, FA Cup, …):** the header row already names the competition, the logos are
  trademarks and detailed logos print poorly at digit size. A builder can put one in a wildcard slot.
- **No club crests outside the wildcard slots:** clubs change every year; only name flaps get reprinted.
- **Wildcard (44–46):** a short section builders fill with what they like (crests, logos, symbols).
  Trademarks: builders decide what to print.
- Most of the built set below changes, so the 52-flap digit flaps need regenerating.

### Built set (was stl/digit-52-1, removed 2026-11-04 — git history; 2026-10-18)

| Slot | Item | Status |
|---|---|---|
| 01–10 | 0–9 | ✅ |
| 11–15 | ↑, ↓, =, +, ' (minute mark) | ✅ |
| 16–19 | CL blue, Europa orange, relegation red, white (solid colour flaps) | ✅ |
| 20–22 | ball, PL lion, Liver bird | ✅ |
| 23–26 | GO, AL, LI, VE (GOAL / LIVE across two modules) | ✅ |
| 27–36 | 0–9 (second set, half a turn from 01–10) | ✅ |
| 37–46 | 10–19 (tens flaps: a pair of digit modules shows 0–199) | ✅ |
| 47–49 | FT, HT, KO | ✅ |
| 50–52 | blank (51 = home; 52's back carries the bottom of "0") | ✅ |

The built set has no minus sign; the planned set above fixes that.

---

## Reference: the 30-flap plan (2026-10-08, superseded)

Name: 20 clubs + blank, 1ST HALF / HALF TIME / 2ND HALF / FULL TIME, GOAL!, divider, PREMIER LEAGUE, 2 spare.
Digit: 0–9 ×2 + blank, − ↑ ↓, 4 zone colours, 2 spare. Built as `stl/name-1/name-flaps/` and
`stl/test-3/digit-flaps/` (30-flap modules; removed 2026-11-04, in git history).
