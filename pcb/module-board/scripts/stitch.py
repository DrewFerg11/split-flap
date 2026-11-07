"""GND fan-out: a via beside every top-side SMD GND pad, into the B.Cu ground plane.

    "C:/Program Files/KiCad/10.0/bin/python.exe" stitch.py           # before autorouting
    "C:/Program Files/KiCad/10.0/bin/python.exe" stitch.py --prune   # after routing: drop dangling stubs
    "C:/Program Files/KiCad/10.0/bin/python.exe" stitch.py --fill    # then: extra stitching + zone fill

GND is never autorouted (autoroute.py strips it): the pours plus these vias carry it.
"""
import math, os, subprocess, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "split-flap-module-board.kicad_pcb")
VIA_D, VIA_DRILL, CLR = 0.6, 0.3, 0.25
W, H = 32.0, 54.0
SCREW_X, SCREW_KEEP = W / 2, 3.2


def mm(v):
    return pcbnew.FromMM(v)


def obstacles(board):
    """(x, y, radius, net) circles approximating every pad, via and track point (mm)."""
    obs = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()))
            obs.append(("box", x0, y0, x1, y1, p.GetNetname(), p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition(); r = pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2
            x, y = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
            obs.append(("box", x - r, y - r, x + r, y + r, t.GetNetname(), True, True))
        else:
            a, b = t.GetStart(), t.GetEnd(); hw = pcbnew.ToMM(t.GetWidth()) / 2
            ax, ay, bx, by = (pcbnew.ToMM(v) for v in (a.x, a.y, b.x, b.y))
            obs.append(("seg", ax, ay, bx, by, t.GetNetname(), t.GetLayer() == pcbnew.F_Cu, t.GetLayer() == pcbnew.B_Cu, hw))
    return obs


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def clear(x, y, r, obs, own_net="GND"):
    if x - r < 0.5 or y - r < 0.5 or x + r > W - 0.5 or y + r > H - 0.5:
        return False
    if math.hypot(x - SCREW_X, y) < SCREW_KEEP + r:      # M3 screw-head keep-out (gen_board.py)
        return False
    for o in obs:
        if o[5] == own_net:
            continue
        if o[0] == "box":
            _, x0, y0, x1, y1 = o[:5]
            dx = max(x0 - x, 0, x - x1); dy = max(y0 - y, 0, y - y1)
            if math.hypot(dx, dy) < r + CLR:
                return False
        else:
            _, ax, ay, bx, by, _, _, _, hw = o
            if seg_dist(x, y, ax, ay, bx, by) < r + hw + CLR:
                return False
    return True


def add_via(board, net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL))
    v.SetNet(net); v.SetLocked(True)
    board.Add(v)


def add_trk(board, net, a, b, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
    t.SetWidth(mm(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); t.SetLocked(True)
    board.Add(t)


def fanout(board):
    gnd = board.FindNet("GND")
    n = 0
    for fp in board.GetFootprints():
        if fp.IsFlipped():
            continue
        fc = fp.GetPosition()
        for p in fp.Pads():
            if p.GetNetname() != "GND" or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not p.GetNumber():
                continue
            if fp.GetReference() == "U4" and p.GetNumber() == "9":      # thermal pad has its own vias
                continue
            px, py = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
            sx, sy = (pcbnew.ToMM(v) for v in (p.GetBoundingBox().GetWidth(), p.GetBoundingBox().GetHeight()))
            out = math.atan2(py - pcbnew.ToMM(fc.y), px - pcbnew.ToMM(fc.x))
            obs = obstacles(board)
            done = False
            tw = 0.25 if min(sx, sy) < 0.6 else 0.4          # fine-pitch pads get a thin neck
            for dist in (0.0, 0.4, 0.8, 1.2, 1.8):
                for k in range(16):
                    a = out + (k // 2) * (1 if k % 2 else -1) * math.pi / 8
                    reach = max(sx, sy) / 2 + VIA_D / 2 + 0.15 + dist
                    x, y = px + reach * math.cos(a), py + reach * math.sin(a)
                    if clear(x, y, VIA_D / 2, obs) and all(
                            seg_dist(ox, oy, px, py, x, y) > 0 for ox, oy in []):
                        # the joining track must also clear other nets
                        ok = all(o[5] == "GND" or not o[6] or (o[0] == "box" and not _seg_hits_box(px, py, x, y, o, tw / 2)) or
                                 (o[0] == "seg" and _seg_seg(px, py, x, y, o) >= o[8] + tw / 2 + CLR)
                                 for o in obs)
                        if ok:
                            add_trk(board, gnd, (px, py), (x, y), tw)
                            add_via(board, gnd, x, y)
                            n += 1; done = True
                            break
                if done:
                    break
            if not done:
                print(f"  no fan-out room: {fp.GetReference()}.{p.GetNumber()}")
    return n


def _seg_hits_box(ax, ay, bx, by, o, hw=0.2):
    _, x0, y0, x1, y1 = o[:5]
    for i in range(21):
        x, y = ax + (bx - ax) * i / 20, ay + (by - ay) * i / 20
        dx = max(x0 - x, 0, x - x1); dy = max(y0 - y, 0, y - y1)
        if math.hypot(dx, dy) < hw + 0.2:
            return True
    return False


def _seg_seg(ax, ay, bx, by, o):
    _, cx, cy, dx, dy = o[:5]
    return min(seg_dist(ax, ay, cx, cy, dx, dy), seg_dist(bx, by, cx, cy, dx, dy),
               seg_dist(cx, cy, ax, ay, bx, by), seg_dist(dx, dy, ax, ay, bx, by))


def grid_stitch(board, pitch=4.0):
    """Extra GND vias on a grid where both layers are free, to tie the F pour to the B plane."""
    gnd = board.FindNet("GND")
    obs = obstacles(board)
    n = 0
    y = 2.0
    while y < H - 1.5:
        x = 2.0
        while x < W - 1.5:
            if clear(x, y, VIA_D / 2 + 0.3, obs, own_net=None):
                add_via(board, gnd, x, y)
                obs.append(("box", x - 0.3, y - 0.3, x + 0.3, y + 0.3, "GND", True, True))
                n += 1
            x += pitch
        y += pitch
    return n


def _frags(board):
    out = []          # (layer_name, SHAPE_POLY_SET)
    for z in board.Zones():
        if z.GetNetname() != "GND" or z.GetIsRuleArea():
            continue
        for L, nm in ((pcbnew.F_Cu, "F"), (pcbnew.B_Cu, "B")):
            if not z.IsOnLayer(L):
                continue
            ps = z.GetFilledPolysList(L)
            for i in range(ps.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    one.AddHole(ps.Hole(i, h))
                out.append((nm, one))
    return out


def stitch_fragments(board):
    """Union-find over GND pour fragments joined by vias / THT pads; tie every group that is not
    the main one to the main group with a via where they overlap. One via per call per group."""
    gnd = board.FindNet("GND")
    frags = _frags(board)
    parent = list(range(len(frags)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    anchors = [t.GetPosition() for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
    anchors += [p.GetPosition() for fp in board.GetFootprints() for p in fp.Pads()
                if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for a in anchors:
        hit = [i for i, (_, f) in enumerate(frags) if f.Contains(a)]
        for i in hit[1:]:
            parent[find(i)] = find(hit[0])
    area = lambda f: f.Area()
    main = find(max(range(len(frags)), key=lambda i: area(frags[i][1])))
    groups = {}
    for i in range(len(frags)):
        groups.setdefault(find(i), []).append(i)
    obs = obstacles(board)
    added = 0
    for root, members in groups.items():
        if root == main:
            continue
        placed = False
        for i in members:
            lay, f = frags[i]
            other = [frags[j][1] for j in groups[main] if frags[j][0] != lay]
            bb = f.BBox()
            x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()))
            y = y0
            while y <= y1 and not placed:
                x = x0
                while x <= x1 and not placed:
                    pts = [(x, y)] + [(x + 0.4 * math.cos(k * math.pi / 4), y + 0.4 * math.sin(k * math.pi / 4)) for k in range(8)]
                    vs = [pcbnew.VECTOR2I(mm(a), mm(b)) for a, b in pts]
                    if all(f.Contains(v) for v in vs) and any(all(o.Contains(v) for v in vs) for o in other):
                        add_via(board, gnd, x, y); added += 1; placed = True
                    x += 0.2
                y += 0.2
            if placed:
                break
        if not placed:
            bb = frags[members[0]][1].BBox()
            print(f"  isolated GND group near ({pcbnew.ToMM(bb.GetX()):.1f},{pcbnew.ToMM(bb.GetY()):.1f}): no overlap with the main plane")
    return added


def prune(board):
    """Delete track segments with a free end (Freerouting leftovers): one pass. The caller repeats it in a
    fresh process, since SWIG typing breaks after board.Remove()."""
    total = 0
    if True:
        tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
        ends = {}
        for t in tracks:
            for p in (t.GetStart(), t.GetEnd()):
                ends[(p.x, p.y, t.GetLayer())] = ends.get((p.x, p.y, t.GetLayer()), 0) + 1
        def anchored(p, layer, net):
            for v in board.GetTracks():
                if v.GetClass() == "PCB_VIA" and v.GetNetname() == net and (v.GetPosition() - p).EuclideanNorm() < mm(0.05):
                    return True
            for fp in board.GetFootprints():
                for pad in fp.Pads():
                    if pad.GetNetname() == net and pad.IsOnLayer(layer) and pad.HitTest(p):
                        return True
            return False
        dead = [t for t in tracks if not t.IsLocked() and any(
            ends[(p.x, p.y, t.GetLayer())] < 2 and not anchored(p, t.GetLayer(), t.GetNetname())
            for p in (t.GetStart(), t.GetEnd()))]
        if not dead:
            return total
        for t in dead:
            board.Remove(t)
        total += len(dead)
    return total


def fill(board):
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


if __name__ == "__main__":
    b = pcbnew.LoadBoard(PCB)
    if "--prune" in sys.argv:          # own process per pass: SWIG typing breaks after board.Remove()
        n = prune(b)
        print("pruned dangling segments:", n)
        if n:
            pcbnew.SaveBoard(PCB, b)
            sys.exit(subprocess.run([sys.executable, os.path.abspath(__file__), "--prune"]).returncode)
    elif "--fill" in sys.argv:
        print("grid stitching vias:", grid_stitch(b))
        fill(b)
        for _ in range(6):
            n = stitch_fragments(b)
            print("fragment stitching vias:", n)
            fill(b)
            if not n:
                break
    else:
        print("GND fan-out vias:", fanout(b))
    pcbnew.SaveBoard(PCB, b)
