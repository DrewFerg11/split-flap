# Third-party notices

These materials are not covered by this project's CC BY-NC-SA 4.0 license. They keep their
own licenses.

## Not included

- **Premier League and club names, logos, and crests** are owned by the Premier League and
  the clubs. They are not distributed here. The flap-set generators take logos you supply
  yourself; you are responsible for your rights to use them.

## Fonts

- **League Gothic**, The League of Moveable Type. SIL Open Font License 1.1.
  <https://github.com/google/fonts/blob/main/ofl/leaguegothic/OFL.txt>
  Flap artwork rendered with the font is part of this project. If the font file itself is
  included, it remains under the OFL.

## PCB libraries

- **KiCad libraries** (symbols, footprints, 3D models): CC BY-SA 4.0 with an exception
  that allows their use in any design without the design becoming CC BY-SA.
  <https://www.kicad.org/libraries/license/>
- **Project symbols** (`hardware/pcbs/module-board/split-flap-module-board.kicad_sym`):
  `GM3085E` and `+12V_CHAIN` / `+12V_FUSED` / `+12V_LOCAL` are modified copies of KiCad's
  stock `MAX3485` and `+12V` symbols, under the KiCad library license above.
- **Part 3D models** (`hardware/pcbs/module-board/part-models/*.step`): from LCSC/EasyEDA
  (via `easyeda2kicad`), for JST ZH B6B-ZR (LCSC C157984) and a 1812 fuse (LCSC C7433877).
  They remain the property of their owners and are included only to render the board.

## Firmware frameworks (downloaded at build time by PlatformIO)

| Component | Used by | License |
|---|---|---|
| Arduino Core STM32 (STM32duino) | `firmware/module` | Mostly LGPL-2.1 and BSD-3-Clause; see its repository |
| STM32CubeG0 HAL/LL | `firmware/module` | BSD-3-Clause |
| Arduino core for ESP32 | `firmware/controller`, applications | LGPL-2.1 |
| ESP-IDF | `firmware/controller`, applications | Apache-2.0 |

Firmware binaries distributed in releases contain these components. Their full source and
this project's source are available, which satisfies the LGPL's relinking requirement.
