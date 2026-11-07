"""JLC placement-file (CPL) conventions, used by outputs.py.

1. Rotation: JLC's 3D models are not all oriented like KiCad's footprints. These corrections come
   from the 7-seg board's JLC preview (2026-09-30, same KiCad 10 libraries, same packages):
     U2 TSSOP-20, U3 SOIC-8, U4 HTSOP-8 (SO-8-EP)   +270
     U1 SOT-89, Q1 SOT-23                            +180
   From this board's own first JLC preview (2026-10-15, Drew's screenshots), the THT connectors:
     J1 R/A header   model's pins pointed down, must point right (+x)       +90
     J2 R/A socket   model's body lay below its pin row, must point left    +270
     J5 PH vertical  model stood across its 3 pads                          +90
   Second upload (same day): all three now sit correctly. J3 (ZH), D1, DZ1, Q1, U1-U4 checked fine.
   Passives / C1 not checked (C1 is hand-soldered).
   ALWAYS check pin 1 / polarity of every part in JLC's preview after uploading.
2. Position: for through-hole parts KiCad's origin is pin 1, but JLC centres its model on the CPL
   point, so THT parts report the centre of their pad pattern.
"""

JLC_ROT = {"U2": 270, "U3": 270, "U4": 270, "U1": 180, "Q1": 180, "J1": 90, "J2": 270, "J5": 90}


def place(ref, origin, rot, pads):
    tht = [(x, y) for x, y, t in pads if t]
    if tht:
        xs, ys = [p[0] for p in tht], [p[1] for p in tht]
        x, y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    else:
        x, y = origin
    return x, y, (rot + JLC_ROT.get(ref, 0)) % 360
