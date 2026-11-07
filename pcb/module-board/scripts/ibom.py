"""Interactive HTML BOM into ./fab/ (InteractiveHtmlBom, run headless).

    "C:/Program Files/KiCad/10.0/bin/python.exe" -m pip install --user InteractiveHtmlBom   # once
    "C:/Program Files/KiCad/10.0/bin/python.exe" ibom.py

  fab/<board>-ibom.html    clickable board view + BOM (LCSC column, nets; test points hidden)

Called by outputs.py; run it alone to add the iBOM to an already ordered fab/ without touching
the other files.
  INTERACTIVE_HTML_BOM_CLI_MODE  stops the package registering itself as a pcbnew plugin, which
                                 outside KiCad pops an assert dialog and blocks.
  no --include-tracks            via widths trip another KiCad 10 assert dialog (PCB_VIA::GetWidth).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "split-flap-module-board"
PROJ = os.path.dirname(HERE)
PCB = os.path.join(PROJ, NAME + ".kicad_pcb")
FAB = os.path.join(PROJ, "fab")
OUT = os.path.join(FAB, NAME + "-ibom.html")

env = dict(os.environ, INTERACTIVE_HTML_BOM_CLI_MODE="1")
try:
    r = subprocess.run([sys.executable, "-m", "InteractiveHtmlBom.generate_interactive_bom", PCB,
                        "--no-browser", "--dest-dir", FAB, "--name-format", NAME + "-ibom",
                        "--include-nets", "--extra-fields", "LCSC", "--blacklist", "TP*", "--dark-mode"],
                       capture_output=True, text=True, env=env, timeout=120)
except subprocess.TimeoutExpired:
    sys.exit("iBOM timed out (a KiCad dialog is probably waiting: close it)")
if r.returncode or not os.path.exists(OUT):
    sys.exit("iBOM failed (is InteractiveHtmlBom installed in KiCad's Python?)\n" + r.stderr[-800:])
print("iBOM:", OUT)
