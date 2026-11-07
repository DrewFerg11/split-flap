"""Courtyard overlap and board-edge check for the placed board (no routing needed).

    "C:/Program Files/KiCad/10.0/bin/python.exe" check_place.py
"""
import os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "split-flap-module-board.kicad_pcb")
OVERHANG = {"J1", "J2"}          # R/A chain connectors overhang the side edges by design
W, H, RAIL = 32.0, 54.0, 1.5

b = pcbnew.LoadBoard(PCB)
boxes = {}
for fp in b.GetFootprints():
    side = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    bb = fp.GetCourtyard(side).BBox()
    boxes[fp.GetReference()] = (fp.IsFlipped(), [pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom())])
bad = 0
refs = sorted(boxes)
for i, a in enumerate(refs):
    fa, (ax0, ay0, ax1, ay1) = boxes[a]
    if a not in OVERHANG and (ax0 < 0 or ax1 > W or ay0 < RAIL - 0.01 or ay1 > H - RAIL + 0.01):
        print(f"EDGE {a}: {ax0:.2f},{ay0:.2f} {ax1:.2f},{ay1:.2f}"); bad += 1
    for c in refs[i + 1:]:
        fc, (cx0, cy0, cx1, cy1) = boxes[c]
        if fa != fc:
            continue
        ox, oy = min(ax1, cx1) - max(ax0, cx0), min(ay1, cy1) - max(ay0, cy0)
        if ox > 0.01 and oy > 0.01:
            print(f"OVERLAP {a} / {c}: {ox:.2f} x {oy:.2f}"); bad += 1
print("placement:", "OK" if not bad else f"{bad} problems")
sys.exit(1 if bad else 0)
