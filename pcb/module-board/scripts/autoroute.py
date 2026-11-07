"""Autoroute everything except GND with Freerouting, on top of gen_board.py + stitch.py.

    "C:/Program Files/KiCad/10.0/bin/python.exe" autoroute.py [passes...]
    "C:/Program Files/KiCad/10.0/bin/python.exe" autoroute.py --finish

Export Specctra DSN -> strip GND (it is the pours + stitch.py's vias) -> Freerouting, several
tries in parallel -> keep the fewest-incomplete / fewest-vias result -> import SES -> save.
Net-class widths (Chain 1.0, Power 0.6, Rail 0.4) go to Freerouting in the DSN; widen.py audits
them afterwards (Freerouting has dropped power widths before).
--finish locks all copper and routes only what is still open.
"""
import os, re, subprocess, sys, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PCB = os.path.join(PROJ, "split-flap-module-board.kicad_pcb")
JAR = os.path.expanduser(r"~/.kicad-mcp/freerouting-2.1.0.jar")
POUR_NETS = {"GND"}
FINISH = "--finish" in sys.argv
SCHEDULE = [int(x) for x in sys.argv[1:] if x.isdigit()] or     ([30, 30, 40, 40] if FINISH else [60, 60, 80, 80, 100, 100, 60, 120])
NO_B_CU = []          # B.Cu is the ground plane; signals may hop under, at a cost

# F.Cu is the signal layer; B.Cu (ground plane) only for short hops.
AUTOROUTE_SETTINGS = """
    (autoroute_settings
      (fanout off)
      (autoroute on)
      (postroute on)
      (vias on)
      (via_costs 30)
      (plane_via_costs 5)
      (start_ripup_costs 100)
      (start_pass_no 1)
      (layer_rule F.Cu (active on) (preferred_direction horizontal)
        (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs 1.2))
      (layer_rule B.Cu (active on) (preferred_direction vertical)
        (preferred_direction_trace_costs 2.5) (against_preferred_direction_trace_costs 3.0))
    )"""


def mm(v):
    return pcbnew.FromMM(v)


def keepout_rect(board, x0, y0, x1, y1, layer):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowZoneFills(False); z.SetDoNotAllowFootprints(False)
    z.SetLayer(layer)
    z.SetZoneName("TMP_AUTOROUTE_KEEPOUT")
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(mm(x), mm(y))
    board.Add(z)
    return z


def strip_pour_nets(dsn_text):
    """Remove (net "GND" ...) blocks from the network section and from any class lists."""
    out, i = [], 0
    pat = re.compile(r'\(net\s+("?)(' + "|".join(re.escape(n) for n in POUR_NETS) + r')\1\s')
    while True:
        m = pat.search(dsn_text, i)
        if not m:
            out.append(dsn_text[i:])
            break
        # only strip inside the network section: a (net ...) that owns (pins ...)
        depth, j = 0, m.start()
        while True:
            c = dsn_text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = dsn_text[m.start():j + 1]
        if "(pins" in block:
            out.append(dsn_text[i:m.start()])
        else:
            out.append(dsn_text[i:j + 1])
        i = j + 1
    text = "".join(out)
    for n in POUR_NETS:     # class membership lists: (class name net1 "net 2" ...)
        text = re.sub(r'(\(class\s+\S+[^()]*?)\s"?' + re.escape(n) + r'"?(?=[\s)])', r"\1", text)
    return text


def main():
    board = pcbnew.LoadBoard(PCB)
    if FINISH:
        for t in board.GetTracks():
            t.SetLocked(True)
    tmp = [keepout_rect(board, *r, pcbnew.B_Cu) for r in NO_B_CU]
    # board-edge keep-out (Freerouting otherwise runs copper ~0.2 mm from the edge; rule is 0.3)
    W, H, E = 32.0, 54.0, 0.45
    # + the connector tabs (gen_board.py TAB_*): no copper on them
    for r in ((0, 0, W, E), (0, H - E, W, H), (0, 0, E, H), (W - E, 0, W, H),
              (-6.43, 0, 0, 16.5 + E), (W, 0, 33.14, 16.5 + E),
              (0, H - 2.5, 2.5, H), (W - 2.5, H - 2.5, W, H)):        # r 2 rounded bottom corners
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            tmp.append(keepout_rect(board, *r, layer))
    work = tempfile.mkdtemp(prefix="sfmb-route-")
    dsn, ses = os.path.join(work, "board.dsn"), os.path.join(work, "board.ses")
    assert pcbnew.ExportSpecctraDSN(board, dsn), "DSN export failed"
    text = strip_pour_nets(open(dsn, encoding="utf-8").read())
    j = text.find("    (boundary", text.find("(structure"))     # right after the (layer ...) blocks
    text = text[:j] + AUTOROUTE_SETTINGS.strip("\n") + "\n" + text[j:]
    open(dsn, "w", encoding="utf-8").write(text)
    print("DSN:", dsn)
    # All tries run at once (Freerouting is single-threaded and its result varies run to
    # run), then the fewest-incomplete / fewest-vias result is kept.
    procs = []
    for k, passes in enumerate(SCHEDULE):
        out = os.path.join(work, f"try{k}.ses")
        log = open(os.path.join(work, f"try{k}.log"), "w", encoding="utf-8")
        procs.append((k, passes, out, log, subprocess.Popen(
            ["java", "-jar", JAR, "-de", dsn, "-do", out, "-mp", str(passes), "--gui.enabled=false"],
            stdout=log, stderr=subprocess.STDOUT)))
    best = None
    for k, passes, out, log, pr in procs:
        try:
            pr.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            pr.kill()
        log.close()
        text_log = open(log.name, encoding="utf-8", errors="replace").read()
        m = re.findall(r'"incomplete_count":\s*(\d+)', text_log)
        v = re.findall(r'"vias":\s*\{\s*"total_count":\s*(\d+)', text_log)
        if not m or not os.path.exists(out):
            print(f"  try {k}: no result"); continue
        score = (int(m[-1]), int(v[-1]) if v else 999)
        print(f"  try {k} (-mp {passes}): incomplete {score[0]}, vias {score[1]}")
        if best is None or score < best[0]:
            best = (score, out)
    assert best, "no SES produced"
    import shutil
    shutil.copy(best[1], ses)
    print("best:", best[0])
    assert os.path.exists(ses), "no SES produced"
    for z in tmp:
        board.Remove(z)
    assert pcbnew.ImportSpecctraSES(board, ses), "SES import failed"
    pcbnew.SaveBoard(PCB, board)
    print("routed ->", PCB)


if __name__ == "__main__":
    main()
