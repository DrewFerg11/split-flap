# Third-party notices

Material in this repository that isn't covered by the project's CC BY-NC-SA 4.0 license
is listed here with its own license. Each entry is added together with the material it
covers.

## Site fonts

The WOFF2 files in `docs/public/assets/fonts/` are distributed under the
SIL Open Font License 1.1, independently of the project's license.
Full copyright notices and license texts accompany the files:

- **League Gothic**, regular 400, Latin subset (Google Fonts v13):
  [license](../docs/public/assets/fonts/league-gothic-OFL.txt),
  [upstream](https://github.com/google/fonts/tree/main/ofl/leaguegothic).
- **Archivo**, variable weight 100–900, normal width, Latin subset
  (Google Fonts v25):
  [license](../docs/public/assets/fonts/archivo-OFL.txt),
  [upstream](https://github.com/google/fonts/tree/main/ofl/archivo).
- **IBM Plex Mono**, regular 400 and medium 500, Latin subsets
  (Google Fonts v20):
  [license](../docs/public/assets/fonts/ibm-plex-mono-OFL.txt),
  [upstream](https://github.com/google/fonts/tree/main/ofl/ibmplexmono).

The files are hosted locally; page views do not contact Google Fonts.
Download sources and update notes are recorded in
[`docs/public/assets/fonts/README.md`](../docs/public/assets/fonts/README.md).

## Not included

- **League and club names, logos, and crests** belong to their owners. None are
  distributed in this repository. You are responsible for your rights to any logos you
  add to your own build.

## PCB libraries

- **KiCad libraries** (symbols, footprints, 3D models): CC BY-SA 4.0 with an exception
  that allows their use in any design without the design becoming CC BY-SA.
  <https://www.kicad.org/libraries/license/>
- **Project symbols** (`pcb/module-board/split-flap-module-board.kicad_sym`):
  `GM3085E` and `+12V_CHAIN` / `+12V_FUSED` / `+12V_LOCAL` are modified copies of KiCad's
  stock `MAX3485` and `+12V` symbols, under the KiCad library license above.
- **Part 3D models** (`pcb/module-board/part-models/*.step`): from LCSC/EasyEDA
  (via `easyeda2kicad`), for JST ZH B6B-ZR (LCSC C157984) and a 1812 fuse (LCSC C7433877).
  They remain the property of their owners and are included only to render the board.
