"""Fabrication outputs for JLCPCB into ./fab/

    "C:/Program Files/KiCad/10.0/bin/python.exe" outputs.py

  fab/gerbers/*            Gerbers (Protel names) + Excellon drill, zipped as fab/<board>-gerbers.zip
  fab/<board>-bom-jlc.csv  Comment, Designator, Footprint, LCSC  (DNP parts excluded)
  fab/<board>-cpl-jlc.csv  Designator, Mid X, Mid Y, Layer, Rotation (DNP excluded)
  fab/<board>.step         3D model for the enclosure check (the enclosure fit check in Fusion)
  fab/images/<board>-{top,bottom,3d}.png   renders
  fab/<board>-layers.pdf   copper/silk/fab prints;  ../<board>-schematic.pdf refreshed

Rotations/positions go through jlc_cpl.py (JLC model corrections + THT centring); check every
part in JLC's placement preview before paying (the most common error).
"""
import csv, os, subprocess, zipfile
from collections import defaultdict
import sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jlc_cpl                # JLC rotation corrections + THT centring (see jlc_cpl.py)

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "split-flap-module-board"
PROJ = os.path.dirname(HERE)          # module-board/: KiCad project + fab/ (scripts live in scripts/)
PCB = os.path.join(PROJ, NAME + ".kicad_pcb")
SCH = os.path.join(PROJ, NAME + ".kicad_sch")
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
FAB = os.path.join(PROJ, "fab")
GERB = os.path.join(FAB, "gerbers")
os.makedirs(GERB, exist_ok=True)


def run(*args):
    r = subprocess.run([CLI, *args], capture_output=True, text=True)
    if r.returncode:
        print("FAILED:", " ".join(args), r.stdout[-500:], r.stderr[-500:])
    return r


for f in os.listdir(GERB):
    os.remove(os.path.join(GERB, f))
run("pcb", "export", "gerbers", "--output", GERB + os.sep,
    "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts",
    "--use-drill-file-origin", "--subtract-soldermask", PCB)
run("pcb", "export", "drill", "--output", GERB + os.sep, "--format", "excellon",
    "--excellon-units", "mm", "--drill-origin", "plot", "--generate-map", "--map-format", "gerberx2", PCB)
zpath = os.path.join(FAB, NAME + "-gerbers.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(GERB)):
        z.write(os.path.join(GERB, f), f)

# ---------------------------------------------------------------- BOM + CPL from the board
b = pcbnew.LoadBoard(PCB)
groups = defaultdict(list)
# Hand-soldered, left out of the JLC BOM/CPL (Drew, 2026-10-15, after the first JLC upload):
#   C1: SMD electrolytic is "Standard PCBA only" at JLC (+$25 and a forced 70 x 70 mm panel)
# J1, J2, J5 stay with JLC; their 3D models land rotated in the preview: fix them there.
HAND = {"C1"}
hand = []
cpl = []
missing = []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if fp.IsDNP() or ref.startswith("TP"):
        continue
    if ref in HAND:                     # Drew solders these; JLC doesn't place them
        hand.append((ref, fp.GetValue(), fp.GetFieldText("LCSC") if fp.HasField("LCSC") else ""))
        continue
    lcsc = fp.GetFieldText("LCSC") if fp.HasField("LCSC") else ""
    if not lcsc:
        missing.append(ref)
    key = (lcsc, str(fp.GetFPID().GetLibItemName()))       # JLC orders by part, not by label
    groups[key].append((ref, fp.GetValue()))
    pos = fp.GetPosition()
    pads = [(pcbnew.ToMM(q.GetPosition().x), pcbnew.ToMM(q.GetPosition().y), q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
            for q in fp.Pads() if q.GetNumber()]
    x, y, rot = jlc_cpl.place(ref, (pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)), fp.GetOrientationDegrees(), pads)
    cpl.append((ref, round(x, 3), round(-y, 3), "Bottom" if fp.IsFlipped() else "Top", round(rot % 360, 1)))


def natural(r):
    import re
    m = re.match(r"([A-Z]+)(\d+)", r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


with open(os.path.join(FAB, NAME + "-bom-jlc.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
    for (lcsc, fpn), items in sorted(groups.items(), key=lambda kv: natural(sorted(r for r, _ in kv[1])[0])):
        refs = sorted((r for r, _ in items), key=natural)
        val = min((v for _, v in items), key=len)          # shortest label, e.g. "100nF" not "C_BS 100nF"
        w.writerow([val, ",".join(refs), fpn, lcsc])
with open(os.path.join(FAB, NAME + "-cpl-jlc.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for row in sorted(cpl, key=lambda r: natural(r[0])):
        w.writerow([row[0], f"{row[1]}mm", f"{row[2]}mm", row[3], row[4]])

with open(os.path.join(FAB, NAME + "-hand-solder.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Value", "LCSC", "Per board", "Note"])
    notes = {"C1": "polarized: stripe = minus; board silk marks +",
             "J1": "right-angle male header, pins point past the RIGHT edge",
             "J2": "right-angle female socket, opening past the LEFT edge",
             "J5": "JST PH vertical, hall sensor connector"}
    for ref, val, lcsc in sorted(hand):
        w.writerow([ref, val, lcsc, 1, notes.get(ref, "")])

# ---------------------------------------------------------------- 3D, renders, PDFs
run("pcb", "export", "step", "--output", os.path.join(FAB, NAME + ".step"), "--subst-models",
    "--no-dnp", "--force", PCB)   # J4/J6/JP1 are bare pads: no headers in the fit-check model
IMG = os.path.join(FAB, "images")
os.makedirs(IMG, exist_ok=True)
for side in ("top", "bottom"):
    run("pcb", "render", "--output", os.path.join(IMG, f"{NAME}-{side}.png"), "--side", side,   # zoom out: the J2 socket and J1 pins overhang the outline
        "--width", "1500", "--height", "1800", "--zoom", "0.8", "--quality", "high", "--background", "opaque", PCB)
run("pcb", "render", "--output", os.path.join(IMG, f"{NAME}-3d.png"), "--side", "top", "--rotate", "-35,0,25",
    "--perspective", "--width", "1600", "--height", "1600", "--quality", "high", "--background", "opaque", PCB)
run("pcb", "export", "pdf", "--output", os.path.join(FAB, NAME + "-layers.pdf"), "--mode-multipage",
    "--layers", "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Fab,Edge.Cuts", "--common-layers", "Edge.Cuts",
    "--include-border-title", PCB)
run("sch", "export", "pdf", "--output", os.path.join(PROJ, NAME + "-schematic.pdf"), SCH)

print("fab outputs in", FAB)
print("BOM lines:", len(groups), " placed parts:", len(cpl), " hand-solder:", sorted(r for r, _, _ in hand),
      " parts without LCSC:", missing or "none")
