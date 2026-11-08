# Design ownership — building the module from scratch

> Applies to the module family (digit and name modules) used by every display. Paths written as
> `design-files/…` are in the private development workspace; the mechanics aren't migrated yet.

**Goal (Drew, 2026-10-08): 100 % ownership of the new module.** It has to be a separate
design, not an adaptation of the existing one, so its licence is Drew's to choose.

## Why this needs rules

The module everything so far is based on is **Morgan Manly's**. His 3D files are licensed
**CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike); see the parent repo's
[`LICENSE-HARDWARE.md`](https://github.com/DrewFerg11/Split-Flap-Display/blob/main/LICENSE-HARDWARE.md).

Under that licence, *anything adapted from his files* is a derivative, however much it's
changed, and must stay CC BY-NC-SA with credit. That covers all existing work in this repo:

| Existing work | Derived from | Status |
|---|---|---|
| `design-files/square` (37 square) | Morgan Manly | derivative, CC BY-NC-SA, keep the credit |
| `design-files/square-48`, `square-dual`, `square-dual-48` | the 48-character version + the square | derivative, CC BY-NC-SA, keep the credit |

**"Different enough" isn't a measure of how much was changed. What matters is where the
geometry came from.** So the new module starts from a blank file and is designed from
first principles and from purchased parts. His design can inform *ideas*, but no geometry
is copied from it.

*This is a practical working rule, not legal advice.*

## The rules

**Allowed:**

* **General ideas and the split-flap mechanism itself.** Split-flap displays are a
  decades-old public mechanism. "Motor inside the drum", "flaps on a spool", "hall
  sensor for homing" are ideas, and ideas aren't protected.
* **Dimensions of purchased parts**, from datasheets or our own measurements: 28BYJ-48 body
  and mounting tabs, shaft, hall sensor, magnets, AS5600 board, screws, heat-set inserts.
* **Requirements and lessons learned** from building and running the existing modules:
  "77 mm rows fit the wall", "single hall sensor misses sometimes", "flaps need X mm
  clearance". Write them down as numbers and requirements, then design to those.
* **Other open designs** under licences that allow it (e.g. scottbez1 is Apache-2.0 for
  some parts). Record the source and licence before using anything.

**Not allowed in the new design files:**

* Opening, importing, copying, projecting, tracing or measuring Morgan's (or any derived)
  STEP/STL/3MF/f3d to create new geometry.
* Starting a new part from an existing body ("save as and modify").
* Re-using the existing build scripts (`design-files/square-48/build/*`). They reproduce
  derived geometry.
* Reproducing a distinctive feature's exact shape (flap profile, drum spoke pattern, clip
  details) from memory or screenshots.

**Practice:**

* New Fusion project/folder (suggested: **Project1 › League-Table**), new files from
  blank. Keep derived reference files out of that folder.
* Keep a short **design log** (`design-log.md`, added when the CAD starts): date, decision,
  why, and which datasheet/measurement each key dimension came from. This shows the
  design was created independently.
* Make choices for our own reasons (requirements, printability, cost), not to look
  different. Independent design will differ anyway: flap count, drum diameter, flap pivot,
  sensor/encoder mounting, PCB integration and the row chassis are all ours to choose.

## Things that are ours by default

These are new for this project and have no upstream:

* the row board PCB, bus and power architecture (this repo)
* the wide name module, the row chassis and the left-side bus rail
* the encoder integration
* new firmware (the brief already says the existing firmware is a guide only)

## Licence for the new design

To decide later. Options: keep it closed, a permissive licence (MIT/CERN-OHL-P), or a
share-alike one (CC BY-SA / CERN-OHL-S). Not urgent until something is published.
