"""flap-sets.md -> flap-sets.json: the drum lists in a form the firmware and the site demo can read.

    python build_json.py           write flap-sets.json from the "All sets side by side" table
    python build_json.py --check   exit 1 if flap-sets.json is out of date or the table breaks a rule

flap-sets.md stays the one place to edit; never edit the JSON by hand.

Each drum is a list of 52 entries, index = firmware flap number (0 = blank = home):
    {"kind": "text", "text": "ARSENAL"}       printed text
    {"kind": "blank"}                         blank flap (flap 0 is also home)
    {"kind": "open"}                          slot not decided yet
    {"kind": "divider"}
    {"kind": "colour", "colour": "yellow", "label": "yellow"}   label as written in the table
    {"kind": "symbol", "symbol": "ball"}      ball, pl-lion, trophy, wildcard
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, "flap-sets.md")
OUT = os.path.join(HERE, "flap-sets.json")
FLAPS = 52
DRUMS = ["name", "header_name", "digit", "header_digit"]       # table columns after "Flap"
COLOURS = {"yellow": "yellow", "cl blue": "blue", "europa orange": "orange",
           "conference green": "green", "red": "red", "white": "white"}
SYMBOLS = {"ball": "ball", "pl lion": "pl-lion", "trophy": "trophy", "wildcard": "wildcard"}


def entry(cell):
    c = cell.strip()
    low = c.lower()
    if low in ("blank", "blank (home)"):
        return {"kind": "blank"}
    if low == "open":
        return {"kind": "open"}
    if low == "divider":
        return {"kind": "divider"}
    if low in COLOURS:
        return {"kind": "colour", "colour": COLOURS[low], "label": c}
    if low in SYMBOLS:
        return {"kind": "symbol", "symbol": SYMBOLS[low]}
    return {"kind": "text", "text": c}


def parse():
    text = open(MD, encoding="utf-8").read()
    m = re.search(r"^## All sets side by side.*?$(.*?)^## ", text, re.S | re.M)
    if not m:
        sys.exit("flap-sets.md: no '## All sets side by side' section")
    rows = [r for r in m.group(1).splitlines() if re.match(r"^\|\s*\d+\s*\|", r)]
    drums = {d: [] for d in DRUMS}
    for want, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) != 1 + len(DRUMS):
            sys.exit(f"flap-sets.md: row {row!r} needs {1 + len(DRUMS)} columns")
        if int(cells[0]) != want:
            sys.exit(f"flap-sets.md: flap numbers must run 0..{FLAPS - 1} in order (found {cells[0]} at {want})")
        for d, c in zip(DRUMS, cells[1:]):
            drums[d].append(entry(c))
    problems = []
    for d, items in drums.items():
        if len(items) != FLAPS:
            problems.append(f"{d}: {len(items)} flaps, expected {FLAPS}")
        elif items[0]["kind"] != "blank":
            problems.append(f"{d}: flap 0 must be the blank (home)")
    if problems:
        sys.exit("flap-sets.md: " + "; ".join(problems))
    return {"source": "flap-sets.md (All sets side by side)", "flaps": FLAPS, "drums": drums}


def render(data):
    # one entry per line: readable diffs when a slot changes
    lines = ["{", f'  "source": {json.dumps(data["source"])},', f'  "flaps": {data["flaps"]},', '  "drums": {']
    for i, d in enumerate(DRUMS):
        lines.append(f'    "{d}": [')
        items = data["drums"][d]
        for j, it in enumerate(items):
            lines.append("      " + json.dumps(it, ensure_ascii=False) + ("," if j < len(items) - 1 else ""))
        lines.append("    ]" + ("," if i < len(DRUMS) - 1 else ""))
    lines += ["  }", "}", ""]
    return "\n".join(lines)


def main():
    out = render(parse())
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != out:
            sys.exit("flap-sets.json is out of date: run python build_json.py")
        print("flap-sets.json is up to date")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print(f"wrote {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
