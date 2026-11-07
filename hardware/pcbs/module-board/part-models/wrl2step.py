"""EasyEDA WRL (0.1 in units) -> STEP (mm), translated by dx,dy, with per-shape colour."""
import re, sys
from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPControl import STEPControl_AsIs
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopLoc import TopLoc_Location
def bx(b):
    a, c = b.CornerMin(), b.CornerMax()
    return [round(v, 3) for v in (a.X(), a.Y(), a.Z(), c.X(), c.Y(), c.Z())]

src, dst, dx, dy = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
txt = open(src).read()
U = 2.54
doc = TDocStd_Document(TCollection_ExtendedString("doc"))
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
allb = Bnd_Box()
for blk in txt.split("Shape{")[1:]:
    col = [float(v) for v in re.search(r"diffuseColor\s+([\d.e-]+)\s+([\d.e-]+)\s+([\d.e-]+)", blk).groups()]
    pts = [float(v) for v in re.search(r"point\s*\[(.*?)\]", blk, re.S).group(1).replace(",", " ").split()]
    P = [gp_Pnt(pts[i] * U + dx, pts[i + 1] * U + dy, pts[i + 2] * U) for i in range(0, len(pts), 3)]
    idx = [int(v) for v in re.search(r"coordIndex\s*\[(.*?)\]", blk, re.S).group(1).replace(",", " ").split()]
    sew = BRepBuilderAPI_Sewing(1e-4)
    face = []
    for i in idx + [-1]:
        if i >= 0:
            face.append(i); continue
        if len(face) >= 3:
            poly = BRepBuilderAPI_MakePolygon()
            for j in face: poly.Add(P[j])
            poly.Close()
            if poly.IsDone():
                f = BRepBuilderAPI_MakeFace(poly.Wire(), True)
                if f.IsDone(): sew.Add(f.Face())
        face = []
    sew.Perform()
    sh = sew.SewedShape()
    # make solids from closed shells where possible
    comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
    ex = TopExp_Explorer(sh, TopAbs_SHELL)
    n = 0
    while ex.More():
        ms = BRepBuilderAPI_MakeSolid(TopoDS.Shell(ex.Current()))
        bb.Add(comp, ms.Solid() if ms.IsDone() else ex.Current()); n += 1; ex.Next()
    if n == 0: comp = sh
    b = Bnd_Box(); BRepBndLib.Add_s(comp, b); BRepBndLib.Add_s(comp, allb)
    print("shape colour", [round(c, 2) for c in col], "bbox", bx(b))
    lab = st.AddShape(comp, False)
    ct.SetColor(lab, Quantity_Color(*col, Quantity_TOC_RGB), XCAFDoc_ColorSurf)
print("TOTAL bbox (xmin ymin zmin xmax ymax zmax)", bx(allb))
w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True)
w.Transfer(doc, STEPControl_AsIs); print("write", w.Write(dst))
