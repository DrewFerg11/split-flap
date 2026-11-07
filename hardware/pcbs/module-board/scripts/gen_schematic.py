"""Generate split-flap-module-board.kicad_sch per design/DESIGN-1.md.

    python gen_schematic.py

Every pin gets a short stub ending in a net label or a power symbol, so connectivity is
explicit and a symbol can move without re-drawing wires. Pin positions come from KiCad's own
symbol libraries (symlib.py). Symbol UUIDs are derived from the reference, so the PCB's
footprint links survive a regeneration.
"""
import io, math, os, re, uuid
import symlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
NAME = "split-flap-module-board"
SCH = os.path.join(PROJ, NAME + ".kicad_sch")
LIB = os.path.join(PROJ, "split-flap-module-board.kicad_sym")
ROOT_UUID = "5d1c9a62-3f0e-4c8b-9a51-7e2b6c0d4a11"
POWER_NETS = {"GND", "+3V3", "+12V_CHAIN", "+12V_FUSED", "+12V_LOCAL"}
CUSTOM_POWER = ("+12V_CHAIN", "+12V_FUSED", "+12V_LOCAL")
STUB = 2.54


def uid():
    return str(uuid.uuid4())


def sym_uuid(ref):
    return str(uuid.uuid5(uuid.UUID(ROOT_UUID), "ltm-symbol:" + ref))


def f(v):
    s = f"{v:.2f}".rstrip('0').rstrip('.')
    return s if s != "-0" else "0"


# ----------------------------------------------------------------------------- project power symbols
def write_project_lib():
    """split-flap-module-board.kicad_sym (library sfmb): +12V_CHAIN / +12V_FUSED / +12V_LOCAL (from power:+12V) and GM3085E."""
    base = symlib.raw_symbol("power", "+12V")
    syms = "".join("\n\t" + base.replace("+12V", n) for n in CUSTOM_POWER)
    # GM3085E: KiCad's MAX3485 (same pinout) flattened into a plain symbol. The stock MAX3485 is
    # derived from LTC2850xS8 and always trips ERC's lib_symbol_mismatch (7SEG's ERC shows it too).
    rs = symlib.flat_symbol("Interface_UART:MAX3485").replace('(symbol "Interface_UART:MAX3485"', '(symbol "GM3085E"', 1)
    rs = rs.replace('(symbol "MAX3485_', '(symbol "GM3085E_')
    rs = rs.replace('(property "Value" "MAX3485"', '(property "Value" "GM3085E"', 1)
    rs = rs.replace('(property "Footprint" ""', '(property "Footprint" "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"', 1)
    syms += "\n\t" + rs
    io.open(LIB, "w", encoding="utf-8").write(
        '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "gen_schematic.py")\n\t(generator_version "10.0")'
        + syms + "\n)\n")
    symlib.PROJECT_LIBS["sfmb"] = LIB


write_project_lib()


# ----------------------------------------------------------------------------- model
symbols, wires, labels, ncs, texts = [], [], [], [], []
pinpos = {}                  # (ref, pin) -> (x, y, stub dx, stub dy)
npwr = [0]


def xform(px, py, x, y, rot, mirror):
    if mirror:
        px = -px
    return {0: (x + px, y - py), 90: (x - py, y - px), 180: (x - px, y + py), 270: (x + py, y + px)}[rot]


def vec(dx, dy, rot, mirror):
    """Library direction (Y up) -> schematic direction (Y down)."""
    a = xform(dx, dy, 0, 0, rot, mirror)
    return (round(a[0]), round(a[1]))


def sym(ref, lib, x, y, rot=0, value="", fp="", mirror=False, lcsc=None, dnp=False,
        ref_at=None, val_at=None, hide_ref=False, hide_val=False, justify=None, in_bom=True):
    s = dict(ref=ref, lib=lib, x=x, y=y, rot=rot, value=value, fp=fp, mirror=mirror,
             props={"LCSC": lcsc} if lcsc else {}, dnp=dnp, ref_at=ref_at, val_at=val_at,
             hide_ref=hide_ref, hide_val=hide_val, justify=justify, in_bom=in_bom)
    symbols.append(s)
    for num, (px, py, ang, _, _) in symlib.pins(lib).items():
        cx, cy = xform(px, py, x, y, rot, mirror)
        # a pin's angle points from its tip into the body; the stub goes the other way
        d = vec(-math.cos(math.radians(ang)), -math.sin(math.radians(ang)), rot, mirror)
        pinpos[(ref, num)] = (cx, cy, d[0], d[1])
    return s


def T(txt, x, y, size=1.5, bold=True):
    texts.append((txt, x, y, size, bold))


def power(net, x, y, d):
    """Power symbol whose graphic points along d, pin at (x, y)."""
    npwr[0] += 1
    lib = "power:" + net if net in ("GND", "+3V3") else "sfmb:" + net
    if net == "GND":
        rot = {(0, 1): 0, (1, 0): 90, (-1, 0): 270, (0, -1): 180}[d]
    else:
        rot = {(0, -1): 0, (-1, 0): 90, (1, 0): 270, (0, 1): 180}[d]
    if d[1]:            # vertical: value centred beyond the tip
        va, just = (x, y + d[1] * 5.08), None
    else:               # sideways: value reads horizontally beyond the tip
        va, just = (x + d[0] * 5.08, y), ("left" if d[0] > 0 else "right")
        if rot == 90:   # KiCad mirrors field justification on a 90-degree symbol
            just = "right" if just == "left" else "left"
    sym(f"#PWR{npwr[0]:03d}", lib, x, y, rot, value=net, hide_ref=True, val_at=va, justify=just, in_bom=False)


def conn(ref, pin, net):
    """Stub from a pin, ending in a label or power symbol. None = no-connect."""
    x, y, dx, dy = pinpos[(ref, str(pin))]
    if net is None:
        ncs.append((x, y))
        return
    e = (x + dx * STUB, y + dy * STUB)
    wires.append(((x, y), e))
    if net in POWER_NETS:
        power(net, e[0], e[1], (dx, dy))
    else:
        rot = 180 if dx < 0 else 0
        labels.append((net, e, rot))


def part(ref, lib, x, y, nets, rot=0, **kw):
    """Place a symbol and connect its pins: nets = {pin: net}."""
    sym(ref, lib, x, y, rot, **kw)
    for pin, net in nets.items():
        conn(ref, pin, net)


def two(ref, lib, x, y, n1, n2, value, fp, lcsc=None, dnp=False, horizontal=False, flip=False):
    """Two-pin part with pin 1 on top (vertical) or on the left (horizontal), whatever the
    library's own orientation (R/C are drawn vertical, diodes horizontal). flip puts pin 2 there."""
    p1 = symlib.pins(lib)["2" if flip else "1"]
    for rot in (0, 90, 180, 270):
        cx, cy = xform(p1[0], p1[1], 0, 0, rot, False)
        if (horizontal and cx < -1 and abs(cy) < 0.01) or (not horizontal and cy < -1 and abs(cx) < 0.01):
            break
    if horizontal:
        part(ref, lib, x, y, {"1": n1, "2": n2}, rot, value=value, fp=fp, lcsc=lcsc, dnp=dnp,
             ref_at=(x, y - 2.54), val_at=(x, y + 2.54))
    else:
        part(ref, lib, x, y, {"1": n1, "2": n2}, rot, value=value, fp=fp, lcsc=lcsc, dnp=dnp,
             ref_at=(x + 2.03, y - 1.27), val_at=(x + 2.03, y + 1.27), justify="left")


R0603, C0603 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric"
LCSC = dict(r100k="C25803", r10k="C25804", r4k7="C23162", r1k="C21190", r120="C22787", r100="C22775",
            c100n="C14663", c1u="C15849", c10u="C19702", c1n="C1588")


def R(ref, x, y, a, b, val, lcsc, **kw):
    two(ref, "Device:R", x, y, a, b, val, R0603, lcsc, **kw)


def C(ref, x, y, a, b, val, lcsc, **kw):
    two(ref, "Device:C", x, y, a, b, val, C0603, lcsc, **kw)


# ============================================================================= A  chain + input protection
T("A  CHAIN + INPUT PROTECTION", 20.32, 30.48)
T("J1 = right edge (toward the trunk), male right-angle header.  J2 = left edge, female socket: the live end of a row is shrouded.", 20.32, 34.29, 1.0, False)
T("+12V_CHAIN and GND pass straight through J1 -> J2 on copper. Only the local branch F1 -> Q1 -> +12V_LOCAL is protected.", 20.32, 36.83, 1.0, False)
chain = {"1": "+12V_CHAIN", "2": "GND", "3": "RS485_A", "4": "RS485_B"}
part("J1", "Connector_Generic:Conn_01x05", 33.02, 53.34, {**chain, "5": "ENUM_IN_RAW"}, mirror=True,
     value="CHAIN_IN  5p R/A header", fp="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Horizontal",
     lcsc="C492413", ref_at=(33.02, 44.45), val_at=(33.02, 62.23))
part("J2", "Connector_Generic:Conn_01x05", 33.02, 81.28, {**chain, "5": "ENUM_OUT_RAW"}, mirror=True,
     value="CHAIN_OUT  5p R/A socket", fp="Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Horizontal",
     lcsc="C2897387", ref_at=(33.02, 72.39), val_at=(33.02, 90.17))
T("Pinout: 1 +12V  2 GND  3 A  4 B  5 ENUM", 20.32, 96.52, 1.0, False)

two("F1", "Device:Polyfuse", 63.5, 55.88, "+12V_CHAIN", "+12V_FUSED", "2A hold 33V", "Fuse:Fuse_1812_4532Metric", "C7433877")
# Q1: DRAIN <- F1 (input side), SOURCE -> +12V_LOCAL (load). Body diode conducts only for correct
# polarity; reversed, Vgs ~ 0 and it blocks. (7SEG drew this backwards first.)
part("Q1", "Transistor_FET:AO3401A", 96.52, 55.88, {"3": "+12V_FUSED", "2": "+12V_LOCAL", "1": "Q1_GATE"}, 90,
     value="AO3401A", fp="Package_TO_SOT_SMD:SOT-23", lcsc="C15127", ref_at=(91.44, 48.26), val_at=(100.33, 48.26))
T("Q1: drain to F1, source to +12V_LOCAL", 83.82, 68.58, 1.0, False)
# DZ1 clamps Vgs: cathode on SOURCE (+12V_LOCAL), anode on the gate
two("DZ1", "Device:D_Zener", 127, 55.88, "+12V_LOCAL", "Q1_GATE", "MM1Z10 10V", "Diode_SMD:D_SOD-123", "C107591")
R("R1", 127, 76.2, "Q1_GATE", "GND", "100k", LCSC["r100k"])
two("D1", "Diode:SMAJ18A", 144.78, 55.88, "+12V_LOCAL", "GND", "SMAJ18A", "Diode_SMD:D_SMA", "C908771")
two("C1", "Device:C_Polarized", 162.56, 55.88, "+12V_LOCAL", "GND", "100u 35V", "Capacitor_SMD:CP_Elec_6.3x5.4", "C3151830")
C("C2", 180.34, 55.88, "+12V_LOCAL", "GND", "100n 50V (VM)", LCSC["c100n"])

# ============================================================================= B  3.3 V logic rail
T("B  3.3 V LOGIC RAIL  HT7533-1 (30 V in, 100 mA)", 200.66, 30.48)
T("HT75xx-1-SOT89: 1 GND  2 VIN (tab)  3 VOUT. Check Holtek's datasheet at layout.", 200.66, 34.29, 1.0, False)
part("U1", "Regulator_Linear:HT75xx-1-SOT89", 228.6, 53.34, {"1": "GND", "2": "+12V_LOCAL", "3": "+3V3"},
     value="HT7533-1", fp="Package_TO_SOT_SMD:SOT-89-3", lcsc="C14289", ref_at=(228.6, 40.64), val_at=(228.6, 43.18))
C("C3", 203.2, 55.88, "+12V_LOCAL", "GND", "1u 50V", LCSC["c1u"])
C("C4", 248.92, 55.88, "+3V3", "GND", "10u", LCSC["c10u"])

# ============================================================================= C  MCU
T("C  MCU  STM32G031F8P6 (64 KB)", 20.32, 111.76)
T("Pin map checked against ST STM32_open_pin_data (STM32G031F(4-6-8)Px, GPIO-STM32G03x modes) 2026-10-15.", 20.32, 115.57, 1.0, False)
T("TIM2 encoder (PA0/PA1 AF2)  TIM3 PWM (PA6/PA7 AF1)  USART1 TX/RX PA9/PA10 (remap, AF1) + DE PB3 (AF4)  USART2 debug PA2/PA3 (AF1)", 20.32, 118.11, 1.0, False)
T("Co-bonded pads stay analog in firmware: PB8 (1), PC14 (2), PA8/PB0/PB1 (15), PA11/PA12 (16/17), PA15 (19), PB4/PB5/PB6 (20).", 20.32, 120.65, 1.0, False)
part("U2", "MCU_ST_STM32G0:STM32G031F8Px", 71.12, 160.02, {
    "4": "+3V3", "5": "GND", "6": "NRST",
    "1": "ENUM_IN", "2": "ENUM_OUT", "3": "LED", "20": "RS485_DE",
    "7": "ENC_A", "8": "ENC_B", "9": "DBG_TX", "10": "DBG_RX", "11": "ISEN_ADC", "12": "HALL",
    "13": "MOT_IN1", "14": "MOT_IN2", "15": None, "16": "RS485_TX", "17": "RS485_RX",
    "18": "SWDIO", "19": "SWCLK"},
    value="STM32G031F8P6", fp="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm", lcsc="C529334",
    ref_at=(73.66, 132.08), val_at=(73.66, 134.62), justify="left")
T("PB7 ENUM_IN  PB9 ENUM_OUT  PC15 LED", 22.86, 190.5, 1.0, False)
T("pin 15 (PA8/PB0/PB1/PB2) spare", 106.68, 190.5, 1.0, False)
C("C5", 132.08, 137.16, "+3V3", "GND", "100n", LCSC["c100n"])
C("C6", 147.32, 137.16, "+3V3", "GND", "1u", LCSC["c1u"])
C("C7", 132.08, 165.1, "NRST", "GND", "100n", LCSC["c100n"])

# ============================================================================= D  RS-485 + enumeration
T("D  RS-485  GM3085E (MAX3485 pinout; project symbol sfmb:GM3085E)", 172.72, 111.76)
T("DE and /RE tied; R2 holds DE low through reset. Termination: trunk ends only (JP1 for bench use). Bias resistors at the host only.", 172.72, 115.57, 1.0, False)
part("U3", "sfmb:GM3085E", 205.74, 144.78, {
    "1": "RS485_RX", "2": "RS485_DE", "3": "RS485_DE", "4": "RS485_TX", "5": "GND",
    "6": "RS485_A", "7": "RS485_B", "8": "+3V3"},
    value="GM3085E", fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", lcsc="C269864",
    ref_at=(208.28, 127), val_at=(208.28, 129.54), justify="left")
C("C8", 233.68, 132.08, "+3V3", "GND", "100n", LCSC["c100n"])
R("R2", 182.88, 165.1, "RS485_DE", "GND", "100k", LCSC["r100k"])
R("R3", 241.3, 152.4, "RS485_A", "TERM_B", "120R", LCSC["r120"])
part("JP1", "Connector_Generic:Conn_01x02", 274.32, 152.4, {"1": "TERM_B", "2": "RS485_B"},
     value="JP_TERM bench only", fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     lcsc="C492401", dnp=True, ref_at=(276.86, 147.32), val_at=(276.86, 157.48), justify="left")

T("ENUMERATION  1k series both ways (hot-plug into an unpowered MCU); 10k pull-down on ENUM_IN", 172.72, 180.34, 1.0, True)
R("R4", 182.88, 190.5, "ENUM_IN_RAW", "ENUM_IN", "1k", LCSC["r1k"], horizontal=True)
R("R5", 213.36, 195.58, "ENUM_IN", "GND", "10k", LCSC["r10k"])
R("R6", 238.76, 190.5, "ENUM_OUT", "ENUM_OUT_RAW", "1k", LCSC["r1k"], horizontal=True)

# ============================================================================= E  motor driver
T("E  MOTOR DRIVER  DRV8870DDA", 289.56, 30.48)
T("I_TRIP = VREF / (10 x R7) = 3.3 / (10 x 0.33) = 1.0 A.  ISEN -> R8/C9 -> ADC for jam detection.", 289.56, 34.29, 1.0, False)
T("IN1/IN2 low (internal pull-downs) = coast while the MCU is in reset.", 289.56, 36.83, 1.0, False)
part("U4", "Driver_Motor:DRV8870DDA", 317.5, 58.42, {
    "1": "GND", "2": "MOT_IN2", "3": "MOT_IN1", "4": "+3V3", "5": "+12V_LOCAL",
    "6": "MOT_OUT1", "7": "ISEN", "8": "MOT_OUT2"},
    value="DRV8870DDAR", fp="Package_SO:Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias",
    lcsc="C86590", ref_at=(320.04, 45.72), val_at=(320.04, 48.26), justify="left")
two("R7", "Device:R", 345.44, 71.12, "ISEN", "GND", "0.33R 1% 0.5W", "Resistor_SMD:R_1206_3216Metric", "C858786")
R("R8", 360.68, 60.96, "ISEN", "ISEN_ADC", "1k", LCSC["r1k"], horizontal=True)
C("C9", 378.46, 66.04, "ISEN_ADC", "GND", "100n", LCSC["c100n"])
C("C10", 396.24, 66.04, "+12V_LOCAL", "GND", "100n 50V", LCSC["c100n"])

# ============================================================================= F  motor + encoder connector
T("F  MOTOR + ENCODER  N20 (Waveshare DCGM-N20-12V-EN-200RPM)", 289.56, 96.52)
T("Pin 1 = M1: order M1 GND C1 C2 VCC M2 (web listings; Drew's guess). Check with a meter at bring-up: reversed puts 3.3 V on the encoder's GND.", 289.56, 100.33, 1.0, False)
T("J4 = solder pads for the bare Waveshare lead (DNP), same nets as J3.", 289.56, 102.87, 1.0, False)
mot = {"1": "MOT_OUT1", "2": "GND", "3": "ENC_A_RAW", "4": "ENC_B_RAW", "5": "+3V3", "6": "MOT_OUT2"}
part("J3", "Connector_Generic:Conn_01x06", 302.26, 121.92, mot, mirror=True, value="MOTOR  ZH1.5 6p",
     fp="Connector_JST:JST_ZH_B6B-ZR_1x06_P1.50mm_Vertical", lcsc="C157984", ref_at=(302.26, 111.76), val_at=(302.26, 132.08))
part("J4", "Connector_Generic:Conn_01x06", 302.26, 152.4, mot, mirror=True, value="MOTOR pads (DNP)",
     fp="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", dnp=True, ref_at=(302.26, 142.24), val_at=(302.26, 162.56))
C("C11", 332.74, 116.84, "+3V3", "GND", "100n", LCSC["c100n"])
R("R9", 350.52, 116.84, "+3V3", "ENC_A_RAW", "10k", LCSC["r10k"])
R("R10", 365.76, 116.84, "+3V3", "ENC_B_RAW", "10k", LCSC["r10k"])
R("R11", 345.44, 137.16, "ENC_A_RAW", "ENC_A", "100R", LCSC["r100"], horizontal=True)
R("R12", 345.44, 152.4, "ENC_B_RAW", "ENC_B", "100R", LCSC["r100"], horizontal=True)
C("C12", 375.92, 142.24, "ENC_A", "GND", "1n", LCSC["c1n"])
C("C13", 391.16, 142.24, "ENC_B", "GND", "1n", LCSC["c1n"])

# ============================================================================= G  hall
T("G  HALL  A3144 (SplitFlap v5.1-compatible connector and pinout)", 289.56, 175.26)
T("1 OUT  2 GND  3 +12V. Open collector: pulled up to 3.3 V here. R14 4.7k limits current if 12 V ever reaches OUT.", 289.56, 179.07, 1.0, False)
part("J5", "Connector_Generic:Conn_01x03", 302.26, 195.58, {"1": "HALL_RAW", "2": "GND", "3": "+12V_LOCAL"}, mirror=True,
     value="HALL  PH2.0 3p", fp="Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical", lcsc="C2320",
     ref_at=(302.26, 187.96), val_at=(302.26, 203.2))
R("R13", 332.74, 195.58, "+3V3", "HALL_RAW", "10k", LCSC["r10k"])
R("R14", 350.52, 205.74, "HALL_RAW", "HALL", "4.7k", LCSC["r4k7"], horizontal=True)
C("C14", 370.84, 210.82, "HALL", "GND", "1n", LCSC["c1n"])

# ============================================================================= H  debug, LED, test points
T("H  DEBUG / LED / TEST POINTS", 20.32, 213.36)
T("J6: SWD (first flash) + USART2 debug. Pads only (DNP); a pogo jig or a hand-soldered header.", 20.32, 217.17, 1.0, False)
part("J6", "Connector_Generic:Conn_01x07", 33.02, 236.22, {
    "1": "+3V3", "2": "SWDIO", "3": "SWCLK", "4": "NRST", "5": "GND", "6": "DBG_TX", "7": "DBG_RX"}, mirror=True,
    value="SWD + UART pads (DNP)", fp="Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical", dnp=True,
    ref_at=(33.02, 224.79), val_at=(33.02, 248.92))
R("R15", 83.82, 228.6, "LED", "LED_A", "1k", LCSC["r1k"], horizontal=True)
two("D2", "Device:LED", 106.68, 236.22, "GND", "LED_A", "LED red", "LED_SMD:LED_0603_1608Metric", "C2286", flip=True)
for i, net in enumerate(("+12V_LOCAL", "+3V3", "RS485_A", "RS485_B", "ISEN_ADC", "GND")):
    x = 147.32 + i * 17.78
    part(f"TP{i + 1}", "Connector:TestPoint", x, 233.68, {"1": net}, value=net,
         fp="TestPoint:TestPoint_Pad_D1.5mm", ref_at=(x + 1.27, 228.6), hide_val=True, justify="left", in_bom=False)

# ============================================================================= power flags
T("PWR_FLAG", 289.56, 223.52, 1.2, False)
for i, net in enumerate(("+12V_CHAIN", "+12V_FUSED", "+12V_LOCAL", "GND")):
    x = 292.1 + i * 17.78
    npwr[0] += 1
    part(f"#FLG{i + 1:02d}", "power:PWR_FLAG", x, 233.68, {"1": net}, value="PWR_FLAG", hide_ref=True,
         val_at=(x, 228.6), in_bom=False)

T("Split-flap module board v0.1  -  per design/DESIGN-1.md  -  generated by scripts/gen_schematic.py, do not hand-edit", 20.32, 20.32, 2.0)
T("One board per module (digit and name). Single sheet; power symbols are global rails, labels are sheet-local.", 20.32, 24.13, 1.2, False)


# ============================================================================= emit
def prop(name, value, at, hide=False, justify=None, size=1.27, angle=0):
    j = f"\n\t\t\t\t(justify {justify})" if justify else ""
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (f'\n\t\t(property "{name}" "{value}"\n\t\t\t(at {f(at[0])} {f(at[1])} {angle}){h}\n\t\t\t(show_name no)'
            f'\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {size} {size})\n\t\t\t\t){j}\n\t\t\t)\n\t\t)')


def emit_symbol(s):
    x, y = s["x"], s["y"]
    mirror = "\n\t\t(mirror y)" if s["mirror"] else ""
    ra = s["ref_at"] or (x, y - 2.54)
    va = s["val_at"] or (x, y + 2.54)
    out = (f'\n\t(symbol\n\t\t(lib_id "{s["lib"]}")\n\t\t(at {f(x)} {f(y)} {s["rot"]}){mirror}\n\t\t(unit 1)\n\t\t(body_style 1)'
           f'\n\t\t(exclude_from_sim no)\n\t\t(in_bom {"yes" if s["in_bom"] else "no"})\n\t\t(on_board yes)\n\t\t(in_pos_files yes)'
           f'\n\t\t(dnp {"yes" if s["dnp"] else "no"})\n\t\t(uuid "{sym_uuid(s["ref"])}")')
    ang = 90 if s["rot"] in (90, 270) else 0      # keeps the text horizontal on a rotated symbol
    out += prop("Reference", s["ref"], ra, hide=s["hide_ref"], justify=s["justify"], angle=ang)
    out += prop("Value", s["value"], va, hide=s["hide_val"], justify=s["justify"], angle=ang)
    out += prop("Footprint", s["fp"], (x, y), hide=True)
    out += prop("Datasheet", "", (x, y), hide=True)
    for k, v in s["props"].items():
        out += prop(k, v, (x, y), hide=True)
    for num in symlib.pins(s["lib"]):
        out += f'\n\t\t(pin "{num}"\n\t\t\t(uuid "{uid()}")\n\t\t)'
    out += (f'\n\t\t(instances\n\t\t\t(project "{NAME}"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(reference "{s["ref"]}")'
            f'\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
    return out


def main():
    used = sorted({s["lib"] for s in symbols})
    libblk = "(lib_symbols" + "".join("\n\t\t" + symlib.flat_symbol(l) for l in used) + "\n\t)"
    out = io.StringIO()
    out.write('(kicad_sch\n\t(version 20260101)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n')
    out.write(f'\t(uuid "{ROOT_UUID}")\n\t(paper "A3")\n')
    out.write('\t(title_block\n\t\t(title "Split-flap module board v0.1")\n\t\t(date "2026-10-15")\n\t\t(rev "0.1")\n'
              '\t\t(company "Split-Flap Display")\n\t\t(comment 1 "Per design/DESIGN-1.md; generated by scripts/gen_schematic.py")\n\t)\n')
    out.write("\t" + libblk + "\n")
    for p in ncs:
        out.write(f'\t(no_connect\n\t\t(at {f(p[0])} {f(p[1])})\n\t\t(uuid "{uid()}")\n\t)\n')
    for a, b in wires:
        out.write(f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')
    for txt, x, y, size, bold in texts:
        b = " bold" if bold else ""
        out.write(f'\t(text "{txt}"\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size}){b}\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')
    for name, p, rot in labels:
        j = "right bottom" if rot == 180 else "left bottom"
        out.write(f'\t(label "{name}"\n\t\t(at {f(p[0])} {f(p[1])} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {j})\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')
    for s in symbols:
        out.write(emit_symbol(s) + "\n")
    out.write('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n')
    io.open(SCH, "w", encoding="utf-8").write(out.getvalue())
    nets = {}
    for n, _, _ in labels:
        nets[n] = nets.get(n, 0) + 1
    lonely = [n for n, c in nets.items() if c < 2]
    print(f"wrote {SCH}: {len([s for s in symbols if not s['ref'].startswith('#')])} parts, "
          f"{len(wires)} stubs, {len(labels)} labels, {len(ncs)} NC")
    if lonely:
        print("WARNING labels used once:", lonely)


if __name__ == "__main__":
    main()
