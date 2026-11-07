"""Render the board's copper + fab layers to a PNG for review (optionally cropped, board mm)."""
import os, subprocess, sys
import pymupdf
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "split-flap-module-board.kicad_pcb")
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
out = sys.argv[1]
layers = sys.argv[2] if len(sys.argv) > 2 else "F.Cu,B.Cu,F.Fab,Edge.Cuts"
svg = out + ".svg"
subprocess.run([CLI, "pcb", "export", "svg", "--layers", layers, "--mode-single", "--fit-page-to-board",
                "--exclude-drawing-sheet", "-o", svg, PCB], check=True, capture_output=True)
d = pymupdf.open(svg); pg = d[0]
clip = None
if len(sys.argv) > 3:
    x0, y0, x1, y1 = map(float, sys.argv[3].split(","))
    k = pg.rect.width / 32.0
    clip = pymupdf.Rect(x0 * k, y0 * k, x1 * k, y1 * k)
pg.get_pixmap(dpi=int(sys.argv[4]) if len(sys.argv) > 4 else 900, clip=clip).save(out)
os.remove(svg)
