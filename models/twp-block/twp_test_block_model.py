# TWP test block: PartDesign body with single-angle, compound-angle and vertical
# faces, pockets and holes on each, plus a hole at an angle into a flat face.
# All sketches fully constrained. Units: mm.
import math
import FreeCAD
import Part
import Sketcher

V = FreeCAD.Vector
R = FreeCAD.Rotation
P = FreeCAD.Placement

L, W, H = 120.0, 80.0, 50.0
report = {}


# ---------------------------------------------------------------- sketch helpers
def _pos(sk, geo, pos, x, y):
    """Fix a point by distances from the sketch origin (axis constraints at 0)."""
    if abs(x) < 1e-9:
        sk.addConstraint(Sketcher.Constraint("PointOnObject", geo, pos, -2))
    else:
        sk.addConstraint(Sketcher.Constraint("DistanceX", -1, 1, geo, pos, x))
    if abs(y) < 1e-9:
        sk.addConstraint(Sketcher.Constraint("PointOnObject", geo, pos, -1))
    else:
        sk.addConstraint(Sketcher.Constraint("DistanceY", -1, 1, geo, pos, y))


def rect(sk, x0, y0, w, h):
    pts = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]
    g = [
        sk.addGeometry(Part.LineSegment(V(*pts[i], 0), V(*pts[(i + 1) % 4], 0)))
        for i in range(4)
    ]
    for i in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", g[i], 2, g[(i + 1) % 4], 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", g[0]))
    sk.addConstraint(Sketcher.Constraint("Horizontal", g[2]))
    sk.addConstraint(Sketcher.Constraint("Vertical", g[1]))
    sk.addConstraint(Sketcher.Constraint("Vertical", g[3]))
    sk.addConstraint(Sketcher.Constraint("DistanceX", g[0], 1, g[0], 2, w))
    sk.addConstraint(Sketcher.Constraint("DistanceY", g[1], 1, g[1], 2, h))
    _pos(sk, g[0], 1, x0, y0)
    return g


def circle(sk, cx, cy, d):
    g = sk.addGeometry(Part.Circle(V(cx, cy, 0), V(0, 0, 1), d / 2))
    sk.addConstraint(Sketcher.Constraint("Diameter", g, d))
    _pos(sk, g, 3, cx, cy)
    return g


def _arc(cx, cy, r, a0, a1):
    return Part.ArcOfCircle(
        Part.Circle(V(cx, cy, 0), V(0, 0, 1), r), math.radians(a0), math.radians(a1)
    )


def rounded_rect(sk, cx, cy, w, h, r):
    xl, xr, yb, yt = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    bottom = sk.addGeometry(Part.LineSegment(V(xl + r, yb, 0), V(xr - r, yb, 0)))
    right = sk.addGeometry(Part.LineSegment(V(xr, yb + r, 0), V(xr, yt - r, 0)))
    top = sk.addGeometry(Part.LineSegment(V(xr - r, yt, 0), V(xl + r, yt, 0)))
    left = sk.addGeometry(Part.LineSegment(V(xl, yt - r, 0), V(xl, yb + r, 0)))
    br = sk.addGeometry(_arc(xr - r, yb + r, r, -90, 0))
    tr = sk.addGeometry(_arc(xr - r, yt - r, r, 0, 90))
    tl = sk.addGeometry(_arc(xl + r, yt - r, r, 90, 180))
    bl = sk.addGeometry(_arc(xl + r, yb + r, r, 180, 270))
    chain = [(bottom, br), (br, right), (right, tr), (tr, top), (top, tl), (tl, left), (left, bl), (bl, bottom)]
    for a, b in chain:
        sk.addConstraint(Sketcher.Constraint("Tangent", a, 2, b, 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", bottom))
    sk.addConstraint(Sketcher.Constraint("Horizontal", top))
    sk.addConstraint(Sketcher.Constraint("Vertical", right))
    sk.addConstraint(Sketcher.Constraint("Vertical", left))
    for a in (tr, tl, bl):
        sk.addConstraint(Sketcher.Constraint("Equal", br, a))
    sk.addConstraint(Sketcher.Constraint("Radius", br, r))
    sk.addConstraint(Sketcher.Constraint("DistanceX", bottom, 1, bottom, 2, w - 2 * r))
    sk.addConstraint(Sketcher.Constraint("DistanceY", left, 2, left, 1, h - 2 * r))
    _pos(sk, bl, 3, xl + r, yb + r)


def obround(sk, cx, cy, length, r):
    """Horizontal slot; length is centre-to-centre."""
    x1, x2 = cx - length / 2, cx + length / 2
    top = sk.addGeometry(Part.LineSegment(V(x2, cy + r, 0), V(x1, cy + r, 0)))
    bottom = sk.addGeometry(Part.LineSegment(V(x1, cy - r, 0), V(x2, cy - r, 0)))
    ra = sk.addGeometry(_arc(x2, cy, r, -90, 90))
    la = sk.addGeometry(_arc(x1, cy, r, 90, 270))
    for a, b in ((bottom, ra), (ra, top), (top, la), (la, bottom)):
        sk.addConstraint(Sketcher.Constraint("Tangent", a, 2, b, 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", top))
    sk.addConstraint(Sketcher.Constraint("Equal", ra, la))
    sk.addConstraint(Sketcher.Constraint("Radius", ra, r))
    sk.addConstraint(Sketcher.Constraint("DistanceX", la, 3, ra, 3, length))
    _pos(sk, la, 3, x1, cy)


# ---------------------------------------------------------------- document / body
doc = FreeCAD.newDocument("TWP_Test")
body = doc.addObject("PartDesign::Body", "TWPBlock")
body.Label = "TWP Test Block"
xy = next(
    o for o in body.Origin.OriginFeatures if getattr(o, "Role", "") == "XY_Plane" or o.Name.startswith("XY_Plane")
)


def datum(name, placement):
    d = body.newObject("PartDesign::Plane", name)
    d.AttachmentSupport = [(xy, "")]
    d.MapMode = "FlatFace"
    d.AttachmentOffset = placement
    d.Visibility = False
    return d


def sketch(name, support, offset=None):
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(support, "")]
    sk.MapMode = "FlatFace"
    if offset is not None:
        sk.AttachmentOffset = offset
    return sk


def vol():
    doc.recompute()
    return body.Shape.Volume


def check(name, before, feat):
    after = vol()
    sk = feat.Profile[0] if hasattr(feat, "Profile") and feat.Profile else None
    report[name] = {
        "removed": round(before - after, 1),
        "valid": feat.isValid(),
        "sketch_dof": getattr(sk, "FullyConstrained", None) if sk else None,
    }
    return after


# 1. base block
sk = sketch("SkBase", xy)
rect(sk, 0, 0, L, W)
pad = body.newObject("PartDesign::Pad", "Block")
pad.Profile = sk
pad.Length = H
sk.Visibility = False
v = vol()
report["Block"] = {"volume": round(v, 1), "sketch_full": sk.FullyConstrained}

# 2. 30 deg facet on +X end: plane through top edge x=90, sloping down to x=120
t1 = 30.0
drop = (L - 90.0) * math.tan(math.radians(t1))
c1 = V(105.0, W / 2, H - drop / 2)
D1 = datum("D_Facet30", P(c1, R(V(0, 1, 0), t1)))
sk = sketch("SkFacet30Cut", D1)
rect(sk, -25, -50, 65, 100)
cut = body.newObject("PartDesign::Pocket", "Facet30")
cut.Profile = sk
cut.Type = "Length"
cut.Length = 100
cut.Reversed = True
sk.Visibility = False
v = check("Facet30", v, cut)
report["Facet30"]["expected"] = round((L - 90) * drop / 2 * W, 1)

# 3. compound facet on the (-X, +Y, top) corner: azimuth 27, tilt 38
rot2 = R(V(0, 0, 1), 27).multiply(R(V(1, 0, 0), -38))
n2 = rot2.multVec(V(0, 0, 1))
A = V(0, W, 32.0)  # where the facet meets the vertical corner edge
# the facet's two other corners, on the top face along the back and left edges
B = V((n2.z * (H - A.z)) / -n2.x, W, H)
C = V(0, W - (n2.z * (H - A.z)) / n2.y, H)
a, b, c = (B - C).Length, (A - C).Length, (A - B).Length
inc = (A * a + B * b + C * c) * (1.0 / (a + b + c))  # incentre: most room for a hole
D2 = datum("D_FacetCompound", P(inc, rot2))
sk = sketch("SkCompoundCut", D2)
rect(sk, -80, -80, 160, 160)
cut = body.newObject("PartDesign::Pocket", "FacetCompound")
cut.Profile = sk
cut.Type = "Length"
cut.Length = 100
cut.Reversed = True
sk.Visibility = False
v = check("FacetCompound", v, cut)
report["FacetCompound"]["normal"] = [round(n2.x, 4), round(n2.y, 4), round(n2.z, 4)]
report["FacetCompound"]["corners"] = [[round(q, 2) for q in p] for p in (A, B, C)]

# 4. top pocket with a round island (flat reference)
top_off = P(V(0, 0, H), R())
sk = sketch("SkTopPocket", xy, top_off)
rounded_rect(sk, 53, 28, 50, 36, 6)
circle(sk, 53, 28, 14)
pk = body.newObject("PartDesign::Pocket", "TopPocket")
pk.Profile = sk
pk.Type = "Length"
pk.Length = 12
sk.Visibility = False
v = check("TopPocket", v, pk)


def hole(name, sk, dia, depth, cut=None):
    h = body.newObject("PartDesign::Hole", name)
    h.Profile = sk
    h.ThreadType = "None"
    h.Threaded = False
    h.Diameter = dia
    h.DepthType = "Dimension"
    h.Depth = depth
    h.DrillPoint = "Angled"
    h.DrillPointAngle = 118
    if cut:
        kind, cd, cdepth = cut
        h.HoleCutType = kind
        h.HoleCutDiameter = cd
        if kind == "Counterbore":
            h.HoleCutDepth = cdepth
        else:
            h.HoleCutCountersinkAngle = cdepth
    h.Refine = True
    sk.Visibility = False
    return h


# 5. two vertical holes in the top
sk = sketch("SkTopHoles", xy, top_off)
circle(sk, 84, 10, 6)
circle(sk, 84, 70, 6)
v = check("TopHoles", v, hole("TopHoles", sk, 6, 20))

# 6. hole at 20 deg into the flat top: no face is normal to it
rot4 = R(V(0, 1, 0), -20)
n4 = rot4.multVec(V(0, 0, 1))
D4 = datum("D_AngledHole", P(V(15, 25, H) + n4 * 5, rot4))  # start 5 mm clear of the top
sk = sketch("SkAngledHole", D4)
circle(sk, 0, 0, 6)
v = check("AngledHole", v, hole("AngledHole", sk, 6, 35))

# 7. rounded pocket on the 30 deg facet
sk = sketch("SkFacet30Pocket", D1)
rounded_rect(sk, 0, 0, 16, 36, 4)
pk = body.newObject("PartDesign::Pocket", "Facet30Pocket")
pk.Profile = sk
pk.Type = "Length"
pk.Length = 6
sk.Visibility = False
v = check("Facet30Pocket", v, pk)

# 8. two holes normal to the 30 deg facet
sk = sketch("SkFacet30Holes", D1)
circle(sk, 0, -30, 6)
circle(sk, 0, 30, 6)
v = check("Facet30Holes", v, hole("Facet30Holes", sk, 6, 18))

# 9. counterbored hole normal to the compound facet
sk = sketch("SkCompoundHole", D2)
circle(sk, 0, 0, 8)
v = check("CompoundHole", v, hole("CompoundHole", sk, 8, 25, ("Counterbore", 14, 4)))

# 10/11. front face (y = 0, tool axis horizontal): slot and countersunk hole
D3 = datum("D_Front", P(V(0, 0, 0), R(V(1, 0, 0), 90)))  # sketch x = world X, y = world Z
sk = sketch("SkFrontSlot", D3)
obround(sk, 35, 25, 30, 6)
pk = body.newObject("PartDesign::Pocket", "FrontSlot")
pk.Profile = sk
pk.Type = "Length"
pk.Length = 8
sk.Visibility = False
v = check("FrontSlot", v, pk)

sk = sketch("SkFrontHole", D3)
circle(sk, 75, 25, 5)
v = check("FrontHole", v, hole("FrontHole", sk, 5, 20, ("Countersink", 10, 90)))

doc.recompute()
report["final"] = {
    "volume": round(body.Shape.Volume, 1),
    "valid": body.Shape.isValid(),
    "solids": len(body.Shape.Solids),
    "faces": len(body.Shape.Faces),
    "bbox": str(body.Shape.BoundBox),
    "tip": body.Tip.Name,
    "invalid": [o.Name for o in doc.Objects if hasattr(o, "isValid") and not o.isValid()],
}
