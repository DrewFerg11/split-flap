#!/usr/bin/env python3
"""Crude STEP (ISO-10303-21) geometry inspector.

STEP files are plain text, so we can pull useful facts out without a CAD kernel:
bounding boxes, and the cylindrical surfaces that correspond to bores, shafts and
bosses. Enough to answer clearance questions.

Usage:
    python tools/step-inspect.py <file.step> [...]
    python tools/step-inspect.py pcb/module-board/fab/*.step
"""
import collections
import glob
import os
import re
import sys

POINT_RE = re.compile(
    r"#(\d+)\s*=\s*CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(([^)]*)\)", re.I)
DIR_RE = re.compile(
    r"#(\d+)\s*=\s*DIRECTION\s*\(\s*'[^']*'\s*,\s*\(([^)]*)\)", re.I)
AXIS_RE = re.compile(
    r"#(\d+)\s*=\s*AXIS2_PLACEMENT_3D\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*#(\d+)", re.I)
CYL_RE = re.compile(
    r"#(\d+)\s*=\s*CYLINDRICAL_SURFACE\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*([0-9.E+-]+)", re.I)


def nums(text):
    out = []
    for tok in text.split(","):
        tok = tok.strip()
        try:
            out.append(float(tok))
        except ValueError:
            return None
    return out


def inspect(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        data = fh.read()
    # STEP allows statements to wrap across lines; flatten whitespace.
    flat = re.sub(r"\s+", " ", data)

    points = {}
    for pid, body in POINT_RE.findall(flat):
        vals = nums(body)
        if vals and len(vals) == 3:
            points[pid] = vals
    dirs = {}
    for did, body in DIR_RE.findall(flat):
        vals = nums(body)
        if vals and len(vals) == 3:
            dirs[did] = vals
    axes = {aid: (pid, did) for aid, pid, did in AXIS_RE.findall(flat)}

    print(f"\n=== {os.path.basename(path)} ===")
    if not points:
        print("  no CARTESIAN_POINTs found")
        return

    # Onshape/AP242 exports are in metres; report mm.
    scale = 1000.0 if "SI_UNIT($,.METRE.)" in flat.replace(" ", "") else 1.0

    def pct(vals, frac):
        vals = sorted(vals)
        return vals[min(len(vals) - 1, int(frac * (len(vals) - 1)))]

    cols = list(zip(*points.values()))
    for name, vals in zip("XYZ", cols):
        vals = [v * scale for v in vals]
        lo, hi = min(vals), max(vals)
        p1, p99 = pct(vals, 0.01), pct(vals, 0.99)
        note = ""
        if (hi - lo) > 3 * (p99 - p1) and (p99 - p1) > 0:
            note = f"   [1-99%: {p1:7.2f} .. {p99:7.2f} — outliers present]"
        print(f"  {name} {lo:9.2f} .. {hi:9.2f} mm  (span {hi - lo:8.2f}){note}")
    print(f"  {len(points)} points")

    # Group cylinders by (radius, axis direction, axis position) to find bores.
    cyls = collections.defaultdict(int)
    for _cid, aid, radius in CYL_RE.findall(flat):
        if aid not in axes:
            continue
        pid, did = axes[aid]
        loc = points.get(pid)
        vec = dirs.get(did)
        if loc is None or vec is None:
            continue
        key = (round(float(radius) * scale, 2),
               tuple(round(v, 2) for v in vec),
               tuple(round(v * scale, 1) for v in loc))
        cyls[key] += 1

    if not cyls:
        return
    print(f"  {len(cyls)} distinct cylindrical surfaces; largest by radius:")
    for (radius, vec, loc), count in sorted(cyls.items(), reverse=True)[:14]:
        print(f"    dia {radius * 2:7.2f} mm  axis={vec}  at={loc}  x{count}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    paths = []
    for arg in args:
        paths.extend(glob.glob(arg))
    for path in sorted(paths):
        inspect(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
