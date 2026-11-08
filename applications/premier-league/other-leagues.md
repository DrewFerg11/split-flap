# Other leagues and sports — what this display can show

The build is geared for the **Premier League table**. This note records which other leagues
the same hardware could show, and where each one breaks. Team counts are for the 2026
seasons; check them before printing flaps, because expansion is frequent.

## The display, as built

**Use for 20+ team leagues (Drew):** the main use is **live scores**, not the full table. The 6-game
live layout works the same at any league size; only the name-flap budget (≤ 40) limits it.

| Resource | Value | Consequence |
|---|---|---|
| Rows | **20–21** for the EPL build (21 likely: header row); code and hardware designed to **expand past 20** (Drew, 2026-10-15) | Rows are the soft limit. A bigger league needs more rows (cost, wall space), or a split (conference, division, top 20). |
| Name module | **40 flaps** per row, and every row has the **same** set | Teams + status words + headers + blank must total ≤ 40. |
| Number column | **2 digit modules** = one number **0–99** per row | One stat per row: points *or* wins, not W–L. Scores ≥ 100 don't fit. |
| Digit symbols | − ↑ ↓ and colour flaps (see [flap-sets.md](flap-sets/flap-sets.md)) | Goal difference to −99, movement arrows. |
| Changing league | Flaps are printed per league | 20 rows × 40 = **800 name flaps** per league. A league change is a re-flap, not a setting. |

### Two ways to use the rows

- **Standings:** one team per row, one number (points, wins, or games back).
- **Live games, 3 rows per game:** status row (a name flap such as `QTR`, `TOP`, `2ND HALF`, with the
  period, inning or minute on the digits), then home team + score, then away team + score.
  **6 games** fit in 18 rows, plus 2 header rows (e.g. `NFL` / `WEEK` + 12). Busier slates cycle.

Using a status word plus a digit (`QTR` + 3, `TOP` + 7) keeps the status flap count small, which
is what lets the 30–32 team leagues fit in 40 flaps.

## Summary

✅ works · ⚠️ works with a compromise · ❌ doesn't fit

| League | Teams | Standings | Live scores | Main limit |
|---|---|---|---|---|
| **Premier League** (target) | 20 | ✅ points | ✅ | Points > 99 (accepted) |
| La Liga, Serie A | 20 | ✅ | ✅ | Same as EPL |
| Bundesliga, Ligue 1 | 18 | ✅ | ✅ | — |
| **MLS** | 30 | ⚠️ one conference (15) | ✅ | 30 rows for the full table |
| **NWSL** | 16 | ✅ points | ✅ | — |
| **NFL** | 32 | ⚠️ one conference (16), wins only | ✅ | No W–L; 39 of 40 flaps used |
| **NHL** | 32 | ⚠️ wins, or points until ~99 | ✅ | Top teams pass 100 points |
| **MLB** | 30 | ⚠️ one league (15), wins until 99 | ✅ | 100-win teams most seasons |
| **NBA** | 30 | ✅ one conference (15), wins | ❌ | Most scores are 100+ |
| **WNBA** | 15 | ✅ wins | ✅ mostly | Rare 100+ scores |
| **College football (FBS)** | 136 | ⚠️ one conference | ⚠️ one conference's games | Too many teams for 40 flaps |
| **Men's college basketball** | 365 | ⚠️ one conference | ⚠️ occasional 100+ | Too many teams |
| **Women's college basketball** | 360+ | ⚠️ one conference | ✅ | Too many teams |
| CFL | 9 | ✅ | ✅ | — |
| EFL Championship | 24 | ❌ 24 rows | ✅ | Rows |
| Champions League | 36 | ❌ | ⚠️ | Rows, and the teams change every season |
| Formula 1 | 11 teams, 22 drivers | ❌ | — | 22 rows; points far above 99 |
| NASCAR, golf, cricket | — | ❌ | ❌ | Field size, scores in the hundreds, three-digit to-par/runs |

## US major leagues

### NFL — good for live games
- **Teams:** 32 (2 conferences × 4 divisions × 4).
- **Flap budget:** 32 nicknames + `QTR`, `HALFTIME`, `OT`, `FINAL`, `FINAL OT`, `NFL` header, blank = **39 / 40**.
  Use nicknames (`CHIEFS`, `49ERS`), not city + nickname.
- **Live:** scores are always < 100 (record 73). Quarter number on the digits. 6 games at a time;
  a Sunday 1 pm slate (8–10 games) cycles.
- **Standings:** one conference (16 rows + 4 division headers = 20 ✓), but only one number:
  **wins** (max 17). W–L or win % doesn't fit.

### NBA — standings only
- **Teams:** 30 (2 conferences × 15).
- **Standings:** one conference fits 15 rows. Wins max 73, so they fit. Games back needs a `½` flap.
- **Live:** ❌. A typical NBA score is 105–125. Unless the digits change (see
  [three-digit trick](#unlocking-three-digit-numbers)).

### MLB — good for live games
- **Teams:** 30 (2 leagues × 3 divisions × 5).
- **Flap budget:** 30 + `TOP`, `MID`, `BOT`, `END`, `FINAL`, `DELAYED`, `POSTPONED`, `MLB`, blank = **39 / 40**.
  Inning number on the digits (extras still fit).
- **Live:** scores ✅ (record 30).
- **Standings:** one league = 15 rows + 3 division headers ✓. **Wins pass 99** for 1–3 teams most
  seasons (record 116), so wins work until late September. Games back needs `½`.

### NHL — good for live games
- **Teams:** 32 (2 conferences × 16).
- **Flap budget:** 32 + `PERIOD`, `INT`, `OT`, `SO`, `FINAL`, `NHL`, blank = **39 / 40**.
- **Live:** scores ✅.
- **Standings:** one conference = 16 rows ✓. **Points pass 100** for the top 5–10 teams each season
  (record 135), so late-season points tables break. Wins (max ~65) always fit.

### MLS — closest to the EPL
- **Teams:** 30 (2 conferences × 15).
- **Standings:** one conference per display (15 rows ✓), points max ~80 ✓. The full 30-team
  Supporters' Shield table needs 30 rows ❌.
- **Live:** same status set as the EPL. Flap budget 30 + 6 statuses + header + blank = 38 ✓.

### NWSL — excellent fit
- **Teams:** 16. The whole league fits with 4 rows to spare (e.g. playoff line). Points ✓, scores ✓.

### WNBA — good fit
- **Teams:** 15. Whole league fits. Wins max 40-ish ✓.
- **Live:** scores are usually 70–95; a 100+ game happens a few times a season.

## College

The team count, not the rows, is the problem: every row carries the same 40 flaps, so a display
can only know **one conference** (or two small ones).

### College football (FBS, 136 teams)
| Conference (football) | Teams | Fits? |
|---|---|---|
| Big Ten | 18 | ✅ 18 rows, 18 + statuses = 25 flaps |
| ACC | 17 | ✅ |
| SEC | 16 | ✅ |
| Big 12 | 16 | ✅ |
| Big Ten + SEC on one set | 34 | ⚠️ 34 + `QTR`/`HALF`/`FINAL`/blank = 38 flaps; standings one at a time |

- **Live:** scores ✅ (100+ essentially never). One conference's Saturday games, 6 at a time.
- **AP Top 25 / CFP rankings:** ❌. 25 rows, and the ranked teams come from all 136.

### College basketball (men's 365 D1, women's 360+)
| Conference | Men | Women |
|---|---|---|
| Big Ten | 18 | 18 |
| ACC | 18 | 18 |
| SEC | 16 | 16 |
| Big 12 | 16 | 16 |
| Big East | 11 | 11 |

- **Standings:** one conference ✓ (conference wins).
- **Live:** men's scores pass 100 in a minority of games, women's rarely. Halves (men) need
  `1ST HALF`/`HALF`/`2ND HALF`; quarters (women) use `QTR` + digit.
- **March Madness:** ❌ (68 teams; bracket shape doesn't map to rows).

## Unlocking three-digit numbers

Most ❌/⚠️ entries above are "number > 99": NBA scores, NHL and MLB late-season standings, EPL 100-point
seasons. The cheapest fix doesn't need a third module:

- Give the **tens** digit module a flap set of `0`–`9` **plus** `10`–`19` as squeezed two-digit glyphs.
  That's 20 flaps + blank + `−` + spares, within its 30.
- Range becomes **0–199**: covers every NBA score (record 186), NHL points (135), MLB wins (116) and
  EPL points (max 114).
- **Costs:** `1x` glyphs are narrower than the single digits; the tens drum has fewer duplicates, so
  it turns further on average.

This is a flap-set change only, so it can be decided late.

## What changes per league

| Item | EPL build | Other league |
|---|---|---|
| Name flaps | 20 clubs + statuses | Reprint the whole set (800 flaps) |
| Digit flaps | 0–9 ×2, −, ↑↓, colours | Usually unchanged; `½` for games back; `1x` set for 0–199 |
| Firmware | EPL data feed | New data source + status mapping |
| Hardware | — | Unchanged (20 rows × 3 modules) |
