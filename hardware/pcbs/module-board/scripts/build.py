"""Regenerate the project and schematic, run ERC, export the schematic PDF and a net list.

    python build.py

Outputs: ../split-flap-module-board.kicad_pro/.kicad_sch/-schematic.pdf, ../fab/erc-report.txt,
../fab/netlist.txt (every net and its pins, for review). Fails if ERC finds anything.
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
FAB = os.path.join(PROJ, "fab")
NAME = "split-flap-module-board"
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
SCH = os.path.join(PROJ, NAME + ".kicad_sch")


def run(*args):
    print(">", " ".join(os.path.basename(a) if os.path.isabs(a) else a for a in args))
    subprocess.run(args, check=True)


def netlist_txt(src, dst):
    t = open(src, encoding="utf-8").read()
    t = t[t.find("(nets"):]
    lines = []
    for blk in re.split(r"\n\t\t\(net\n", t)[1:]:
        name = re.search(r'\(name "([^"]*)"', blk).group(1)
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)(?:\s*\(pinfunction "([^"]*)"\))?', blk)
        nodes = sorted(f"{r}.{p}" + (f"[{fn}]" if fn and not fn.startswith("Pin_") else "") for r, p, fn in nodes)
        lines.append(f"{name:<24} {' '.join(nodes)}")
    open(dst, "w", newline="\n").write("\n".join(sorted(lines)) + "\n")


def main():
    run(sys.executable, os.path.join(HERE, "gen_project.py"))
    run(sys.executable, os.path.join(HERE, "gen_schematic.py"))
    erc = os.path.join(FAB, "erc-report.txt")
    run(CLI, "sch", "erc", "--severity-all", "-o", erc, SCH)
    run(CLI, "sch", "export", "pdf", "-o", os.path.join(PROJ, NAME + "-schematic.pdf"), SCH)
    net = os.path.join(FAB, "netlist.net")
    run(CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, SCH)
    netlist_txt(net, os.path.join(FAB, "netlist.txt"))
    os.remove(net)
    report = open(erc, encoding="utf-8").read()
    m = re.search(r"ERC messages: (\d+)", report)
    if not m or m.group(1) != "0":
        sys.exit("ERC is not clean, see fab/erc-report.txt")
    print("ERC clean; netlist in fab/netlist.txt")


if __name__ == "__main__":
    main()
