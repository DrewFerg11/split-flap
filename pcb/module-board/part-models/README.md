# part-models — parts KiCad 10 ships no model for

`gen_board.py` (`LOCAL_3D`) points these footprints at `${KIPRJMOD}/part-models/<footprint>.step`.
Both come from LCSC/EasyEDA via `easyeda2kicad` (2026-10-18). Aligned to the KiCad footprint
origin, so the model offset/rotation stay 0.

| File | Part | Source | Check |
|---|---|---|---|
| `JST_ZH_B6B-ZR_1x06_P1.50mm_Vertical.step` | J3 motor, C157984 | EasyEDA had only a WRL mesh (STEP 404): converted by `wrl2step.py <wrl> <step> 3.75 0` (0.1 in → mm, pin 1 to origin). Tessellated, not B-rep | body 10.5 × 3.5 × 4.5 mm, matches KiCad F.Fab outline |
| `Fuse_1812_4532Metric.step` | F1, C7433877 | EasyEDA STEP, unchanged | 4.5 × 3.2 × 1.04 mm, centred, matches F.Fab |

J3's mated plug and wires are not modelled: allow for them in the enclosure.

Renders of each part on the board (from `kicad-cli pcb render`, 2026-11-06):
`Fuse_1812_4532Metric.png` (F1) and `JST_ZH_B6B-ZR_1x06_P1.50mm_Vertical.png` (J3).
