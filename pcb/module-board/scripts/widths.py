"""Per-net track width audit (Freerouting has dropped power widths before).

    "C:/Program Files/KiCad/10.0/bin/python.exe" widths.py [--fix]
Fails if any power/chain/rail net has a track narrower than its class minimum below.
"""
import os, sys
from collections import defaultdict
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "split-flap-module-board.kicad_pcb")
# motor nets carry <= 1.0 A (DRV8870 limit): 0.5 mm on 1 oz copper is ~1.5 A at a 10 C rise
MIN = {"+12V_CHAIN": 1.0, "+12V_FUSED": 0.6, "+12V_LOCAL": 0.6, "/MOT_OUT1": 0.5, "/MOT_OUT2": 0.5,
       "/ISEN": 0.5, "+3V3": 0.4}
b = pcbnew.LoadBoard(PCB)
w = defaultdict(list)
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA":
        w[t.GetNetname()].append(pcbnew.ToMM(t.GetWidth()))
bad = 0
for net in sorted(w):
    lo, hi, n = min(w[net]), max(w[net]), len(w[net])
    flag = ""
    if net in MIN and lo < MIN[net] - 1e-3:
        flag = f"  <-- below {MIN[net]}"; bad += 1
    print(f"{net:<16} segs {n:3}  min {lo:.2f}  max {hi:.2f}{flag}")
print("widths:", "OK" if not bad else f"{bad} nets too narrow")
sys.exit(1 if bad else 0)
