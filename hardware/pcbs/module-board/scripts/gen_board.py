"""Generate split-flap-module-board.kicad_pcb (32 x 54 mm, 2 layers) from the schematic netlist.

    "C:/Program Files/KiCad/10.0/bin/python.exe" gen_board.py

Deterministic: outline, footprint placement, the hand-routed chain band, GND pours. Everything
else is routed by autoroute.py. Re-running this script discards all routing.

Board frame: mm, origin at the top-left corner, +x toward the trunk (right edge, J1), +y down.
In the module the board stands upright at the back with its F side (all parts) facing the drum;
the top and bottom 1.5 mm are rail grooves (DESIGN-1 s8).
"""
import math, os, subprocess, sys, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexpr  # noqa: E402

NAME = "split-flap-module-board"
PROJ = os.path.dirname(HERE)
PCB = os.path.join(PROJ, NAME + ".kicad_pcb")
SCH = os.path.join(PROJ, NAME + ".kicad_sch")
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
FPDIR = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"

W, H = 32.0, 54.0
RAIL = 1.5                         # rail groove along the top and bottom edges: no parts
CHAIN_Y = [4.0 + 2.54 * i for i in range(5)]     # chain pins 1..5, same on both edges
# M3 retaining screw: half-round notch in the top edge, the screw head clamps the board to an enclosure
# boss. Copper keep-out (both layers) under a 5.5 mm socket-cap head; +12V_CHAIN copper starts at y 3.4.
SCREW_X, SCREW_R, SCREW_KEEP = W / 2, 1.7, 3.2
# Connector tabs: the board juts out under the chain connectors so their bodies rest on it
# instead of hanging on their pins. J2 socket body x -7.43..2.7, J1 header plastic x 30.9..33.44, both y 2.7..15.4
# (measured on the STEP). Tab edges stop 1.0 short of the socket mouth / 0.3 short of the header plastic.
TAB_L, TAB_R, TAB_Y, TAB_FILLET = -6.43, 33.14, 16.5, 0.5
# J1 header plastic overhangs the right edge, J2 socket the left. Each 1.0 inboard of the original 30.4 / 1.6
# (2026-10-18): socket mouth to header plastic = 40.87 for the 41 mm module pitch (modules butt, no side plate between)
J1_X, J2_X = 29.4, 2.6


def mm(v):
    return pcbnew.FromMM(v)


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


# ============================================================================ placement
# ref: (x, y, rotation, side, anchor pad or None = footprint origin)
PLACE = {}


def place(ref, x, y, rot=0, side="F", anchor=None):
    PLACE[ref] = (x, y, rot, side, anchor)


# chain connectors: pin 1 (+12V) at the top on both edges
place("J1", J1_X, CHAIN_Y[0], 0, anchor="1")       # male R/A header, pins point +x past the right edge
place("J2", J2_X, CHAIN_Y[0], 0, anchor="1")       # female R/A socket, body points -x past the left edge

# input protection + bulk (right column, under J1)
place("R4", 22.0, 16.0)                 # ENUM_IN series
place("R5", 22.0, 18.5)                 # ENUM_IN pull-down
place("F1", 27.5, 18.5, 180)            # pin 1 (chain side) on the right
place("Q1", 27.5, 22.5, 0)
place("DZ1", 22.5, 22.5, 0)
place("R1", 21.3, 25.0)
place("D1", 27.0, 26.9, 0)              # SMAJ18A, pad 1 (cathode) on the left
# C1 / LDO swapped 2026-10-19 (Drew): C1 sat in the hall-wire path at the motor side of the enclosure;
# rotated 90 it fits toward the centre, ~10 mm from U4's VM (was 7.6). LDO group takes the right column.
place("C1", 19.8, 31.5, 90)             # bulk 100u
place("U1", 26.5, 32.9, 180)            # HT7533-1, pins face its caps on the right
place("C4", 30.3, 31.2, 90)             # LDO out, beside pin 3 (VOUT)
place("C3", 30.3, 34.8, 270)            # LDO in, + pad toward pin 2 (VIN)

# motor driver + sense (right, lower)
place("U4", 24.8, 40.0, 0)
place("C10", 29.7, 44.2, 0)
place("C2", 29.7, 46.0, 0)
place("R7", 24.2, 45.4, 0)
place("J3", 21.5, 49.5, 0, anchor="1")  # ZH 6p motor, pads along +x

# RS-485 (left, under the band)
place("R6", 6.5, 15.0)                  # ENUM_OUT series
place("U3", 11.0, 19.0, 0)
place("C8", 15.9, 18.0, 90)
place("R2", 15.9, 21.3, 90)
place("JP1", 18.5, 16.0, 0, anchor="1")
place("R3", 18.5, 22.3, 90)

# MCU
place("U2", 11.5, 26.5, 0)
place("C5", 6.0, 25.0, 90)
place("C6", 6.0, 28.5, 90)
place("C7", 6.0, 32.0, 90)

# encoder / hall / ISEN filters and LED (grid under the MCU)
place("R9", 7.5, 35.5); place("R10", 11.0, 35.5); place("C11", 14.5, 35.5)
place("R11", 7.5, 38.5); place("R12", 11.0, 38.5); place("C12", 14.5, 38.5); place("C13", 18.0, 38.5)
place("R13", 7.5, 41.5); place("R14", 11.0, 41.5); place("C14", 14.5, 41.5); place("R8", 18.0, 41.5)
place("R15", 7.5, 44.5); place("D2", 11.0, 44.5); place("C9", 18.0, 44.5)

# connectors along the left edge and bottom
place("J6", 2.2, 18.0, 0, anchor="1")   # SWD + UART pads (DNP), vertical
place("J4", 2.2, 37.0, 0, anchor="1")   # motor solder pads (DNP), vertical
place("J5", 12.0, 49.1, 0, anchor="1")  # PH 3p hall

# test points: bottom side, pads only
for ref, (x, y) in {"TP1": (24.0, 29.5), "TP2": (16.0, 47.0), "TP3": (10.0, 14.5), "TP4": (13.5, 14.5),
                    "TP5": (21.0, 46.5), "TP6": (29.0, 47.0)}.items():
    place(ref, x, y, 0, "B")


# ============================================================================ build helpers
LOCAL_3D = {"JST_ZH_B6B-ZR_1x06_P1.50mm_Vertical", "Fuse_1812_4532Metric"}


def load_fp(fpid):
    lib, name = fpid.split(":")
    m = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
    assert m is not None, fpid
    m.SetFPID(pcbnew.LIB_ID(lib, name))
    if name in LOCAL_3D:   # KiCad 10 ships no model for these: use ../part-models (from LCSC, see its README)
        old = list(m.Models())                  # Models() hands back copies: rebuild the list instead
        new = pcbnew.FP_3DMODEL()
        new.m_Filename = f"${{KIPRJMOD}}/part-models/{name}.step"
        new.m_Offset, new.m_Scale, new.m_Rotation, new.m_Show = \
            old[0].m_Offset, old[0].m_Scale, old[0].m_Rotation, True
        m.Models().clear()
        m.Add3DModel(new)
    return m


def trk(board, netinfo, net, pts, w, layer=pcbnew.F_Cu):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1))
        t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(netinfo[net]); t.SetLocked(True)
        board.Add(t)


def zone(board, netinfo, net, layer, pts, prio=0):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(netinfo[net]); z.SetAssignedPriority(prio)
    z.SetMinThickness(mm(0.2)); z.SetLocalClearance(mm(0.25)); z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # solid: 1.5 mm-pitch ZH pads starve thermal spokes
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(x), mm(y))
    board.Add(z)


def edge(board, a, b, mid=None):
    s = pcbnew.PCB_SHAPE(board)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.05))
    if mid is None:
        s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*b))
    else:
        s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(*a), V(*mid), V(*b))
    board.Add(s)


def outline(board):
    """32 x 54 body + connector tabs, every corner rounded; open at the top-edge screw
    notch (screw_notch draws that arc). Each vertex: (x, y, fillet radius); the male tab is only 1.14 wide."""
    f = TAB_FILLET
    pts = [(SCREW_X + SCREW_R, 0, 0), (TAB_R, 0, 1.0), (TAB_R, TAB_Y, f), (W, TAB_Y, f), (W, H, 2.0),
           (0, H, 2.0), (0, TAB_Y, f), (TAB_L, TAB_Y, 1.5), (TAB_L, 0, 1.5), (SCREW_X - SCREW_R, 0, 0)]
    prev = pts[0][:2]
    for (px, py, _), (x, y, r), (nx, ny, _) in zip(pts, pts[1:], pts[2:]):
        d1 = ((x - px) / math.hypot(x - px, y - py), (y - py) / math.hypot(x - px, y - py))
        d2 = ((nx - x) / math.hypot(nx - x, ny - y), (ny - y) / math.hypot(nx - x, ny - y))
        a = (x - d1[0] * r, y - d1[1] * r)
        b = (x + d2[0] * r, y + d2[1] * r)
        c = (x - d1[0] * r + d2[0] * r, y - d1[1] * r + d2[1] * r)       # arc centre (right-angle corners)
        mid = (c[0] + r * (d1[0] - d2[0]) / math.sqrt(2), c[1] + r * (d1[1] - d2[1]) / math.sqrt(2))
        edge(board, prev, a)
        edge(board, a, b, mid)
        prev = b
    edge(board, prev, pts[-1][:2])


def screw_notch(board):
    """Notch arc on Edge.Cuts (the top edge's straight parts are drawn by the caller) + copper keep-out."""
    a = pcbnew.PCB_SHAPE(board)
    a.SetShape(pcbnew.SHAPE_T_ARC); a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.05))
    a.SetArcGeometry(V(SCREW_X - SCREW_R, 0), V(SCREW_X, SCREW_R), V(SCREW_X + SCREW_R, 0))
    board.Add(a)
    k = pcbnew.ZONE(board)
    k.SetIsRuleArea(True); k.SetZoneName("M3 screw head")
    k.SetLayerSet(pcbnew.LSET.AllCuMask())
    k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowPads(True)
    k.SetDoNotAllowZoneFills(True); k.SetDoNotAllowFootprints(False)
    ol = k.Outline(); ol.NewOutline()
    for i in range(33):                       # lower half-disc: the part on the board
        t = math.pi * i / 32
        ol.Append(mm(SCREW_X + SCREW_KEEP * math.cos(t)), mm(SCREW_KEEP * math.sin(t)))
    board.Add(k)


def build():
    net_file = os.path.join(tempfile.gettempdir(), "sfmb-board.net")
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net_file, SCH],
                   check=True, capture_output=True)
    comps, nets = sexpr.read_netlist(net_file)
    fp_cache = {ref: load_fp(c["footprint"]) for ref, c in comps.items()}   # before any board load

    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    tb = board.GetTitleBlock()
    tb.SetTitle("Split-flap module board v0.1"); tb.SetRevision("0.1"); tb.SetDate("2026-10-15")
    tb.SetCompany("Split-Flap Display"); tb.SetComment(0, "Generated by scripts/gen_board.py per design/DESIGN-1.md")

    netinfo = {}
    for name in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pin_net = {(r, p): n for n, pins in nets.items() for r, p in pins}

    missing = sorted(set(comps) - set(PLACE))
    assert not missing, f"unplaced: {missing}"
    for ref, c in sorted(comps.items()):
        m = fp_cache[ref]
        m.SetReference(ref)
        m.SetValue(c["value"])
        for k, v in c["fields"].items():
            if k in ("Footprint", "Datasheet", "Description") or not v:
                continue
            m.SetField(k, v)
            m.GetField(k).SetVisible(False)
        m.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        if c["dnp"]:
            m.SetDNP(True)
        for pad in m.Pads():
            n = pin_net.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
            elif ref == "U4" and pad.GetNumber() == "":      # DRV8870 thermal-pad vias/paste -> GND
                pad.SetNet(netinfo["GND"])
        x, y, rot, side, anchor = PLACE[ref]
        board.Add(m)
        m.SetPosition(V(0, 0))
        m.SetOrientationDegrees(rot)
        if side == "B":
            m.Flip(V(0, 0), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        if anchor is not None:
            p = [pd for pd in m.Pads() if pd.GetNumber() == anchor][0].GetPosition()
            m.SetPosition(pcbnew.VECTOR2I(mm(x) - p.x, mm(y) - p.y))
        else:
            m.SetPosition(V(x, y))
        m.Value().SetLayer(pcbnew.B_Fab if side == "B" else pcbnew.F_Fab)

    # outline
    def seg(a, b, layer=pcbnew.Edge_Cuts, w=0.05):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a)); s.SetEnd(V(*b)); s.SetLayer(layer); s.SetWidth(mm(w))
        board.Add(s)
    outline(board)
    screw_notch(board)
    for y0 in (0.0, H - RAIL):            # rail grooves, for reference
        for a, b in (((0, y0), (W, y0)), ((0, y0 + RAIL), (W, y0 + RAIL))):
            seg(a, b, pcbnew.Cmts_User, 0.1)

    # chain band: straight F.Cu pass-through, J1 -> J2 (pins 1, 2, 3, 4; pin 5 ENUM is not passed through)
    for pin, net, w in ((1, "+12V_CHAIN", 1.2), (2, "GND", 1.0), (3, "/RS485_A", 0.3), (4, "/RS485_B", 0.3)):
        trk(board, netinfo, net, [(J2_X, CHAIN_Y[pin - 1]), (J1_X, CHAIN_Y[pin - 1])], w)

    # GND pours: whole board on B.Cu, and F.Cu around the parts
    rect = [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)]
    zone(board, netinfo, "GND", pcbnew.B_Cu, rect)
    zone(board, netinfo, "GND", pcbnew.F_Cu, rect)

    board.GetDesignSettings().SetAuxOrigin(V(0, 0))
    board.GetDesignSettings().SetGridOrigin(V(0, 0))
    pcbnew.SaveBoard(PCB, board)
    subprocess.run([sys.executable if "kicad" not in sys.executable.lower() else "python",
                    os.path.join(HERE, "gen_project.py")], check=False, capture_output=True)
    return board


if __name__ == "__main__":
    b = build()
    print("wrote", PCB, len(b.GetFootprints()), "footprints")
