# Parts shortlist — N20 digit module

> Applies to the module family (digit and name modules) used by every display. Paths written as
> `design-files/…` are in the private development workspace; the mechanics aren't migrated yet.

Goal: buy test motors fast (Amazon) and the production batch cheaper. It has to be **the same
part from both sources** so the CAD fits both. Checked 2026-10-08; prices move.

## Motor: Waveshare DCGM-N20-12V-EN-200RPM ⭐

The only N20 encoder motor found sold under **one part number by one maker** on both a fast
source and a bulk source, with an **official drawing and STEP model**. The CAD uses that model
(`design-files/sfd-leaguetable/ref/waveshare-dcgm-n20/`).

| | |
|---|---|
| Specs | 12 V, 1:150, 200 rpm no-load, ≥1.2 kg·cm stall, 0.1 A no-load / ≤1.1 A stall |
| Encoder | AB magnetic hall, 7 PPR → 1050 per output rev (×4 quadrature = 4200); encoder supply 3.3–5 V |
| Size (official drawing) | gearbox 12 × 10 × 9.03; motor + encoder 24.13 long; shaft Ø3 D (2.5 flat) × 10.17; encoder board 18.5 × 12 with magnet Ø9.2; L-shaped 6-pin connector |
| Connector | ZH1.5 6-pin |

| Source | Use | Price | Link |
|---|---|---|---|
| Amazon (sold by waveshare) | test samples, 2-day | $13.99 each | [B0CW1TCCTL](https://www.amazon.com/dp/B0CW1TCCTL) |
| waveshare.com (direct) | production batch | $6.99 · $6.59 (10+) · $6.39 (50+) · $6.31 (100+) | [product page](https://www.waveshare.com/dcgm-n20-12v-en-200rpm.htm) |
| Waveshare wiki | drawing, STEP, pinout | — | [wiki](https://www.waveshare.com/wiki/DCGM-N20-12V-EN-200RPM) |

60 modules ≈ **$385** at the 50+ tier, plus shipping.

Not found on AliExpress (Waveshare search returned nothing).

## Alternatives (not chosen)

| Option | Why not (yet) |
|---|---|
| **Chihai Motor CHF-GM12-N20ABHL** (the manufacturer; 7 PPR, 6–12 V) | On AliExpress at ~$13.31, so no cheaper than Waveshare via Amazon. Its Amazon listings are different variants (N20VA). |
| **Generic "GA12-N20 encoder 7PPR"** on AliExpress (~$1.77–5) | Cheapest, but board shape, connector and gearbox length vary by seller and batch. You can't match the exact part on Amazon, so test parts wouldn't prove production parts. Only worth it as a bulk lot from one listing, after measuring samples from that same listing. |
| Amazon generic 2-packs (e.g. "2Pcs DC 12V 140RPM N20 Encoder", ~$24/pair) | Same problem: no maker part number, no drawing. |

## Speed note

At 12 V the 200 rpm version spins the drum ~3.3 rev/s with direct drive, faster than needed.
Run it at reduced PWM. The encoder makes speed control easy, and it means more torque margin.

## Other parts (already in hand / known)

- A3144 hall sensor (4.5–24 V supply, open-collector output → pull up to 3.3 V)
- N52 Ø3 × 1 mm magnets
