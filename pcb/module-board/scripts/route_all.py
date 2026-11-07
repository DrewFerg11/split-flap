"""Board pipeline after the schematic: place -> GND fan-out -> autoroute -> finish -> stitch/fill -> width audit -> DRC.

    python route_all.py           (~10 minutes; Freerouting runs 4 tries in parallel)
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
KPY = r"C:/Program Files/KiCad/10.0/bin/python.exe"
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
PCB = os.path.join(PROJ, "split-flap-module-board.kicad_pcb")


def step(label, cmd, ok_fail=False):
    print("==", label, flush=True)
    r = subprocess.run(cmd, cwd=HERE, text=True, capture_output=True)
    print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "memory leak" not in l)[-1200:])
    if r.returncode and not ok_fail:
        sys.exit(f"failed: {label}")


step("board", [KPY, "gen_board.py"])
step("project", [sys.executable, "gen_project.py"])
step("placement check", [KPY, "check_place.py"])
step("GND fan-out", [KPY, "stitch.py"])
step("autoroute", [KPY, "autoroute.py", "60", "80", "100", "120"])
step("autoroute finish", [KPY, "autoroute.py", "--finish", "30", "40"])
step("prune", [KPY, "stitch.py", "--prune"])
step("stitch + fill", [KPY, "stitch.py", "--fill"])
step("silkscreen", [KPY, "silk.py"])
step("width audit", [KPY, "widths.py"])
step("DRC", [CLI, "pcb", "drc", "--severity-all", "--schematic-parity", "-o",
             os.path.join(PROJ, "fab", "drc-report.txt"), PCB], ok_fail=True)
step("fab outputs", [KPY, "outputs.py"])
IMG = os.path.join(PROJ, "fab", "images", "split-flap-module-board-")
step("review image: copper + exact references", [sys.executable, "snap.py", IMG + "assembly-top.png", "F.Cu,F.Fab,Edge.Cuts", "-7,0,34,54", "760"])
step("review image: bottom", [sys.executable, "snap.py", IMG + "copper-bottom.png", "B.Cu,B.Silkscreen,Edge.Cuts", "-7,0,34,54", "760"])
