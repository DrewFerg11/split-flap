"""Silkscreen: place every reference where it clears pads, edges, other parts and other text;
drop footprint silk that overhangs the board edge; add the bottom-side pinout labels.

    "C:/Program Files/KiCad/10.0/bin/python.exe" silk.py

References that find no room are hidden on silk (they stay on the Fab layer).
"""
import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "split-flap-module-board.kicad_pcb")
W, H = 32.0, 54.0
TXT, THK, GAP = 0.8, 0.12, 0.12
# main parts whose automatic spot was ambiguous (Drew, 2026-10-15): (x, y, rotation), board mm
PINNED = {
    "U2": (11.5, 31.0, 0),       # MCU: centred under the chip
    "U3": (5.6, 19.0, 90),       # RS-485: left of the chip, clear of J2's overhang
    "U1": (26.5, 29.5, 0),       # 3.3 V regulator: above it, under D1
    "U4": (24.8, 36.7, 0),       # motor driver: between U1 and the chip
    "C1": (19.8, 31.5, 90),      # hand-soldered cap: inside its outline, visible until it's fitted
    "D1": (31.1, 26.9, 90),      # TVS: right of it (C1 now fills the space on its left)
}


def mm(v):
    return pcbnew.FromMM(v)


def rect(bb, grow=0.0):
    return (pcbnew.ToMM(bb.GetX()) - grow, pcbnew.ToMM(bb.GetY()) - grow,
            pcbnew.ToMM(bb.GetRight()) + grow, pcbnew.ToMM(bb.GetBottom()) + grow)


def hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def main():
    b = pcbnew.LoadBoard(PCB)
    fps = list(b.GetFootprints())
    old_labels = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.B_SilkS]
    # footprint silk that overhangs the board edge (the R/A chain connectors) goes -- removed at
    # the very end: SWIG loses its typing for later footprints after a Remove()
    doomed = []
    for fp in fps:
        for g in fp.GraphicalItems():
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and g.GetClass() != "PCB_TEXT":
                x0, y0, x1, y1 = rect(g.GetBoundingBox())
                if x0 < 0.2 or x1 > W - 0.2 or y0 < 0.2 or y1 > H - 0.2:
                    doomed.append((fp, g))
    doomed_ids = {id(g) for _, g in doomed}

    blocked = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    for fp in fps:
        for p in fp.Pads():
            r = rect(p.GetBoundingBox(), 0.15)
            if p.IsOnLayer(pcbnew.F_Cu):
                blocked[pcbnew.F_SilkS].append(r)
            if p.IsOnLayer(pcbnew.B_Cu):
                blocked[pcbnew.B_SilkS].append(r)
        for g in fp.GraphicalItems():          # the footprints' own outline silk
            if g.GetLayer() in blocked and g.GetClass() != "PCB_TEXT" and not any(g == d for _, d in doomed):
                blocked[g.GetLayer()].append(rect(g.GetBoundingBox(), 0.05))
    for t in b.GetTracks():                     # vias: keep silk off the holes
        if t.GetClass() == "PCB_VIA":
            r = rect(t.GetBoundingBox(), 0.1)
            blocked[pcbnew.F_SilkS].append(r); blocked[pcbnew.B_SilkS].append(r)
    crt = {}
    for fp in fps:
        side = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
        crt[fp.GetReference()] = (fp.IsFlipped(), rect(fp.GetCourtyard(side).BBox()))

    placed = hidden = 0
    for fp in sorted(fps, key=lambda f: -rect(f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox())[2]):
        ref = fp.Reference()
        layer = pcbnew.B_SilkS if fp.IsFlipped() else pcbnew.F_SilkS
        ref.SetLayer(layer)
        ref.SetTextSize(pcbnew.VECTOR2I(mm(TXT), mm(TXT))); ref.SetTextThickness(mm(THK))
        ref.SetKeepUpright(True)
        flipped, (x0, y0, x1, y1) = crt[fp.GetReference()]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        n = len(fp.GetReference())
        w, h = n * TXT * 0.75 + 0.2, TXT + 0.2
        cands = []
        for rot, tw, th in ((0, w, h), (90, h, w)):
            cands += [(cx, y0 - th / 2 - GAP, rot, tw, th), (cx, y1 + th / 2 + GAP, rot, tw, th),
                      (x0 - tw / 2 - GAP, cy, rot, tw, th), (x1 + tw / 2 + GAP, cy, rot, tw, th),
                      (x0 + tw / 2, y0 - th / 2 - GAP, rot, tw, th), (x1 - tw / 2, y0 - th / 2 - GAP, rot, tw, th),
                      (x0 + tw / 2, y1 + th / 2 + GAP, rot, tw, th), (x1 - tw / 2, y1 + th / 2 + GAP, rot, tw, th)]
        for rot, tw, th in ((0, w, h), (90, h, w)):          # wider search: a ring 0.5-3 mm out
            for d in (0.6, 1.2, 1.8, 2.6):
                for k in range(16):
                    import math
                    a = k * math.pi / 8
                    rx, ry = (x1 - x0) / 2 + tw / 2 + d, (y1 - y0) / 2 + th / 2 + d
                    cands.append((cx + rx * math.cos(a), cy + ry * math.sin(a), rot, tw, th))
        if fp.IsDNP():                                          # pads-only parts: label inside the outline
            cands.append((cx, cy, 90 if (y1 - y0) > (x1 - x0) else 0, h if (y1 - y0) > (x1 - x0) else w,
                          w if (y1 - y0) > (x1 - x0) else h))
        ok = None
        if fp.GetReference() in PINNED:                       # hand-picked spots for the main parts
            x, y, rot = PINNED[fp.GetReference()]
            tw, th = (w, h) if rot == 0 else (h, w)
            ok = (x, y, rot, (x - tw / 2, y - th / 2, x + tw / 2, y + th / 2))
            cands = []
        for x, y, rot, tw, th in cands:
            r = (x - tw / 2, y - th / 2, x + tw / 2, y + th / 2)
            if r[0] < 0.3 or r[1] < 0.3 or r[2] > W - 0.3 or r[3] > H - 0.3:
                continue
            if any(hit(r, q) for q in blocked[layer]):
                continue
            if any(hit(r, c) for other, (fl, c) in crt.items() if other != fp.GetReference() and fl == flipped) or                     (not fp.IsDNP() and hit(r, (x0, y0, x1, y1))):
                continue
            ok = (x, y, rot, r)
            break
        if ok:
            x, y, rot, r = ok
            ref.SetVisible(True)
            ref.SetTextAngleDegrees(rot)
            ref.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            blocked[layer].append((r[0] - 0.05, r[1] - 0.05, r[2] + 0.05, r[3] + 0.05))
            placed += 1
        else:
            ref.SetVisible(False)
            hidden += 1

    # bottom-side labels (mirrored silk): pinouts and the board name
    def label(text, x, y, size=0.8, angle=0, layer=pcbnew.B_SilkS):
        t = pcbnew.PCB_TEXT(b)
        t.SetText(text); t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(max(0.12, size * 0.15)))
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetTextAngleDegrees(angle)
        t.SetMirrored(layer == pcbnew.B_SilkS)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        b.Add(t)
    # read from the back: the trunk (right edge in the top view) is on the LEFT
    label("<- TRUNK SIDE", 24.5, 2.3, 0.8)
    for k, name in enumerate(("12V", "GND", "A", "B", "EN")):
        label(name, 5.2, 4.0 + 2.54 * k, 0.8)
        label(name, 26.8, 4.0 + 2.54 * k, 0.8)
    label("JP1 = 120R TERM, BENCH ONLY", 16.5, 21.4, 0.8)
    label("SPLIT-FLAP MODULE", 17.0, 24.6, 1.0)
    label("v0.1 2026-10", 17.0, 26.4, 0.8)
    label("3V3 DIO CLK RST GND TX RX", 4.6, 25.6, 0.8, 90)
    label("M1 GND A B 3V3 M2", 4.6, 43.35, 0.8, 90)
    label("M1 GND A B 3V3 M2", 25.25, 51.6, 0.8)
    label("OUT GND 12V", 14.0, 51.4, 0.8)
    for fp, g in doomed:
        fp.Remove(g)
    for t in old_labels:                       # a re-run replaces the previous labels
        b.Remove(t)
    pcbnew.SaveBoard(PCB, b)
    print(f"removed {len(doomed)} overhanging silk segments")
    print(f"references placed {placed}, hidden {hidden}")


if __name__ == "__main__":
    main()
