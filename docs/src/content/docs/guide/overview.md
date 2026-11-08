---
title: The project
description: How the parts of the split-flap ecosystem fit together.
---

A split-flap display turns information into physical motion. Each module moves
a drum of printed flaps to show a name, number, or colour. Modules combine into
rows; rows combine into a display.

## Four pieces of one build

| Part | What it contains | Source |
|---|---|---|
| Hardware | Printed modules and physical assemblies | [hardware/](https://github.com/DrewFerg11/split-flap/tree/main/hardware) |
| Electronics | Module boards and fabrication packages | [pcb/](https://github.com/DrewFerg11/split-flap/tree/main/pcb) |
| Firmware | Module software, the shared bus protocol, and later the controller | [firmware/](https://github.com/DrewFerg11/split-flap/tree/main/firmware) |
| Applications | League-specific flap sets, layouts, and display modes | [applications/](https://github.com/DrewFerg11/split-flap/tree/main/applications) |

The electronics and firmware coordinate modules over an RS-485 bus. Applications
decide what the display shows, using the flaps actually installed on each drum.

## Pick a place to start

- **Explore the layouts:** [display demos](../../demo/) will use sample data
  to show what each application can do.
- **Work on the software:** see [firmware](../firmware/) and the build instructions
  in the source repository.
- **Follow a physical build:** browse the hardware and PCB files above.
  Detailed assembly guides will be added as the designs develop.

## Releases and contributions

[GitHub releases](https://github.com/DrewFerg11/split-flap/releases) group files
by component: boards, physical parts, firmware targets, and applications can
each be released independently.

Fixes, new flap sets, enclosure variants, and documentation improvements are
welcome. Read the
[contribution guidelines](https://github.com/DrewFerg11/split-flap/blob/main/.github/CONTRIBUTING.md)
and [project license](https://github.com/DrewFerg11/split-flap/blob/main/LICENSE.md)
before sharing a change.
