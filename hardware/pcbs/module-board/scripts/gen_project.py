"""Write the KiCad project file (net classes, design rules) and sym-lib-table from project-template.kicad_pro.

    python gen_project.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
NAME = "split-flap-module-board"
TEMPLATE = os.path.join(HERE, "project-template.kicad_pro")   # KiCad defaults; this script sets the rest

pro = json.load(open(TEMPLATE, encoding="utf-8"))
pro["meta"]["filename"] = NAME + ".kicad_pro"
pro["schematic"]["top_level_sheets"] = [{"filename": NAME + ".kicad_sch", "name": NAME,
                                         "uuid": "00000000-0000-0000-0000-000000000000"}]
for k in ("sheets", "boards"):
    if k in pro:
        pro[k] = []
ns = pro["net_settings"]
# net classes: name -> (track, clearance, via_dia, via_drill)
CLASSES = {"Chain": (1.0, 0.25, 0.8, 0.4), "Ground": (0.5, 0.2, 0.6, 0.3),
           "Power": (0.6, 0.2, 0.6, 0.3), "Rail": (0.4, 0.2, 0.6, 0.3)}
base = dict(ns["classes"][0])
base.update(track_width=0.25, clearance=0.2, via_diameter=0.6, via_drill=0.3)
ns["classes"] = [base] + [dict(base, name=n, track_width=t, clearance=c, via_diameter=vd, via_drill=vr, priority=i)
                          for i, (n, (t, c, vd, vr)) in enumerate(CLASSES.items())]
ds = pro["board"].setdefault("design_settings", {})
ds.setdefault("rules", {}).update({          # JLC 2-layer standard capabilities, with margin
    "min_clearance": 0.15, "min_track_width": 0.15, "min_connection": 0.15,
    "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_through_hole_diameter": 0.3,
    "min_hole_to_hole": 0.25, "min_hole_clearance": 0.25, "min_copper_edge_clearance": 0.3,
    "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.12,
    "allow_blind_buried_vias": False, "allow_microvias": False})
ds["track_widths"] = [0.0, 0.25, 0.4, 0.6, 1.0, 1.5]
ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}, {"diameter": 0.8, "drill": 0.4}]
# Chain: pass-through rail (1 A row current, 3 A worst case). Power: local 12 V and motor outputs.
ns["netclass_patterns"] = (
    [{"netclass": "Chain", "pattern": "+12V_CHAIN"}, {"netclass": "Ground", "pattern": "GND"}]
    + [{"netclass": "Power", "pattern": p} for p in ("+12V_FUSED", "+12V_LOCAL", "/MOT_OUT1", "/MOT_OUT2", "/ISEN")]
    + [{"netclass": "Rail", "pattern": "+3V3"}])
json.dump(pro, open(os.path.join(PROJ, NAME + ".kicad_pro"), "w", encoding="utf-8", newline="\n"), indent=2)
open(os.path.join(PROJ, "sym-lib-table"), "w", newline="\n").write(
    '(sym_lib_table\n  (version 7)\n  (lib (name "sfmb")(type "KiCad")(uri "${KIPRJMOD}/split-flap-module-board.kicad_sym")(options "")'
    '(descr "Split-flap module board symbols (+12V_CHAIN, +12V_FUSED, +12V_LOCAL)"))\n)\n')
print("wrote", NAME + ".kicad_pro", "and sym-lib-table")
