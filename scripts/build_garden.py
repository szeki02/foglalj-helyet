# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - garden beds, curb, walkway, trees and garden furniture in the
# Alfoldi u. 6 courtyard, positioned by single-image photogrammetry against the pavilion facade.
# Re-runnable: deletes everything it created before (user text 'garden_build').
#
# Coordinates used below: s = metres along the pavilion's west facade from its NORTH end (south +),
#                         n = metres west of the facade (garden side +), z up from ground.
import math
import random
import sys
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

sys.path.insert(0, 'C:/Users/David/DEV/Alfoldi_utca_6/scripts')
import photogrammetry as pg
reload(pg)

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'garden_build'

# ------------------------------------------------------------------ frame (same as build_pavilion.py)
C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
XF = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, rg.Plane(C_WORLD, U, -V))


def P(s, n, z=0.0):
    """photo frame (s, n, z) -> local pavilion frame (X from south, Y west)"""
    return rg.Point3d(L - s, n, z)


# ------------------------------------------------------------------ cameras (re-solved from facade picks)
F = 1127.0   # iPhone main camera, 26 mm equiv., 1500 px wide
FACADE = {
    'p5': ([((5.865, 0, 2.16), (181, 474)), ((6.862, 0, 2.16), (232, 494)), ((5.865, 0, 0.02), (177, 806)), ((6.862, 0, 0.02), (229, 773)),
            ((9.371, -0.03, 2.05), (298, 528)), ((10.298, -0.03, 2.05), (321, 540)), ((9.371, -0.03, 0.05), (296, 740)), ((10.298, -0.03, 0.05), (317, 727)),
            ((13.974, 0, 3.33), (373, 480)), ((13.974, 0, 2.45), (373, 533)), ((5.925, 0.04, 1.06), (187, 657)), ((6.802, 0.04, 1.06), (232, 651)),
            ((18.57, 0.06, 3.49), (433, 490)), ((18.57, 0.06, 3.49), (433, 490))],
           750., 562.5, [F, -2.17, 2.43, 1.23, 0.17, 0.05]),
    'p8': ([((9.371, -0.03, 2.05), (1146, 604)), ((10.298, -0.03, 2.05), (1224, 600)), ((9.371, -0.03, 0.05), (1146, 830)), ((10.298, -0.03, 0.05), (1224, 840)),
            ((5.865, 0, 2.16), (946, 612)), ((6.862, 0, 2.16), (994, 608)), ((5.865, 0, 0.02), (946, 800)), ((6.862, 0, 0.02), (994, 804)),
            ((11.570, 0, 2.20), (1352, 576)), ((11.570, 0, 0.0), (1352, 856)), ((12.727, 0, 2.20), (1488, 568)), ((12.727, 0, 0.0), (1488, 864)),
            ((4.628, 0, 2.20), (900, 610)), ((4.628, 0, 0.0), (900, 768))],
           750., 562.5, [F, 18.0, 7.92, 1.43, math.radians(-156.7), math.radians(5.6)]),
    'p9': ([((5.865, 0, 2.16), (272, 626)), ((6.862, 0, 2.16), (313, 640)), ((5.865, 0, 0.02), (273, 937)), ((6.862, 0, 0.02), (312, 900)),
            ((9.371, -0.03, 2.05), (373, 674)), ((10.298, -0.03, 2.05), (390, 679)), ((9.371, -0.03, 0.05), (373, 874)), ((10.298, -0.03, 0.05), (390, 862)),
            ((13.974, 0, 3.33), (437, 615)), ((13.974, 0, 2.45), (437, 680)), ((5.925, 0.04, 1.06), (275, 800)), ((6.802, 0.04, 1.06), (320, 791)),
            ((18.57, 0.06, 3.49), (494, 633)), ((18.57, 0.06, 3.49), (494, 633))],
           562.5, 750., [F, -2.02, 2.32, 1.30, -0.035, 0.0]),
    'p12': ([((5.865, 0, 2.16), (412, 465)), ((6.862, 0, 2.16), (493, 483)), ((5.865, 0, 0.02), (412, 841)), ((6.862, 0, 0.02), (493, 783)),
             ((9.371, -0.03, 2.05), (618, 530)), ((10.298, -0.03, 2.05), (649, 537)), ((9.371, -0.03, 0.05), (618, 757)), ((10.298, -0.03, 0.05), (649, 746)),
             ((13.974, 0, 3.33), (735, 470)), ((13.974, 0, 2.45), (735, 538)), ((5.925, 0.04, 1.06), (417, 670)), ((6.802, 0.04, 1.06), (501, 663)),
             ((18.57, 0.06, 3.49), (811, 491)), ((18.57, 0.06, 3.49), (811, 491))],
            750., 562.5, [F, -0.17, 3.43, 1.25, -0.23, 0.05]),
}
CAM = {}
for k, (obs, cx, cy, p0) in FACADE.items():
    p, rms, _ = pg.pc_solve(obs, cx, cy, p0, fixed=(0,))
    CAM[k] = (p, cx, cy, rms)


def ground(cam, u, v, z=0.0):
    p, cx, cy, _ = CAM[cam]
    return pg.pc_ground(p, u, v, cx, cy, z)


def tri(*obs):
    return pg.triangulate_bearings([(CAM[c][0], CAM[c][1], CAM[c][2], u, v) for c, u, v in obs])


def top_z(cam, s, n, u, v):
    """height of pixel (u, v) above a known plan position (s, n)"""
    p, cx, cy, _ = CAM[cam]
    ds, dn, up = pg.pc_ray(p, u, v, cx, cy)
    d = math.hypot(s - p[1], n - p[2])
    return p[3] + up / math.hypot(ds, dn) * d


def avg(pts):
    return (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts))


# ------------------------------------------------------------------ measured plan positions
WALK_W = avg([ground('p5', 181, 1031), ground('p5', 304, 877), ground('p5', 381, 804), ground('p9', 316, 1088),
               ground('p9', 189, 1252), ground('p12', 475, 925), ground('p12', 762, 762)])[1]
curb_pts = [ground('p5', 827, 1108), ground('p5', 846, 962), ground('p5', 854, 862), ground('p5', 856, 777),
            ground('p9', 921, 915), ground('p9', 905, 1062), ground('p9', 889, 1241), ground('p9', 863, 1441),
            ground('p12', 1215, 1010), ground('p12', 1170, 1110), ground('p8', 660, 830), ground('p8', 620, 1100)]
# least squares line n = a + b s
ns = len(curb_pts)
ms, mn = sum(q[0] for q in curb_pts) / ns, sum(q[1] for q in curb_pts) / ns
b_c = sum((q[0] - ms) * (q[1] - mn) for q in curb_pts) / sum((q[0] - ms) ** 2 for q in curb_pts)
a_c = mn - b_c * ms
curb_rms = math.sqrt(sum((q[1] - (a_c + b_c * q[0])) ** 2 for q in curb_pts) / ns)


def curb_n(s):
    return a_c + b_c * s


T1 = tri(('p5', 795, 862), ('p12', 1117, 988), ('p9', 860, 994))
T4 = tri(('p5', 832, 760), ('p12', 1250, 800))
T2 = avg([tri(('p5', 492, 688), ('p12', 875, 675), ('p9', 550, 800)), ground('p5', 492, 688)])
T3 = (22.9, 6.9)          # photo 15: trunk with green birdhouse stands in front of the wall left of the gate pillar
T5 = (-2.0, -0.7)         # photo 8 bearing at s = -2 (base hidden), leans towards the pavilion
SAPLING = ground('p12', 875, 800)
STAND = avg([ground('p9', 484, 1278), ground('p9', 584, 1288), ground('p9', 500, 1231), ground('p9', 600, 1220)])
SLABS_C = avg([ground('p12', 930, 882), ground('p12', 1025, 890), ground('p12', 1200, 915)])
MOUND1 = avg([ground('p8', 860, 880), ground('p8', 1000, 880), ground('p13' if False else 'p8', 930, 845), ground('p8', 930, 910)])
MOUND2 = avg([ground('p8', 1070, 945), ground('p8', 1280, 945), ground('p8', 1175, 910), ground('p8', 1175, 980)])

S_NORTH, S_SOUTH = -2.4, 18.5     # bed ends (north: beyond photo 5/9 camera; south: pavilion end)
T2 = (T2[0], max(T2[1], WALK_W + 0.25))   # base lands on the walkway edge -> keep it in the bed

# heights
T1_FORK = 2.3
T1_HEAD = top_z('p8', T1[0], T1[1], 600, 430)                  # pollard heads (cut stubs)
T1_TOP = max(top_z('p8', T1[0], T1[1], 600, 0), 10.0)          # leaders leave the frame -> lower bound
T4_CUT = top_z('p12', T4[0], T4[1], 1250, 400)
T4_TOP = top_z('p12', T4[0], T4[1], 1280, 50)
T2_TOP = top_z('p5', T2[0], T2[1], 560, 290)
T3_TOP = top_z('p5', T3[0], T3[1], 450, 100)
T5_TOP = 7.2

# ------------------------------------------------------------------ layers
def layer(path, col, transp=None):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        parts = path.split('::')
        parent = System.Guid.Empty
        if len(parts) > 1:
            parent = doc.Layers[layer('::'.join(parts[:-1]), Color.FromArgb(150, 150, 150))].Id
        Lr = Rhino.DocObjects.Layer()
        Lr.Name = parts[-1]
        Lr.Color = col
        Lr.ParentLayerId = parent
        idx = doc.Layers.Add(Lr)
    if transp is not None:
        m = Rhino.DocObjects.Material()
        m.Name = path.split('::')[-1]
        m.DiffuseColor = col
        m.Transparency = transp
        lay = doc.Layers[idx]
        lay.RenderMaterialIndex = doc.Materials.Add(m)
        lay.CommitChanges()
    return idx

LY = {
    'walk': layer('02_Courtyard_Ground::Walkway_Concrete_Slabs', Color.FromArgb(178, 176, 170)),
    'bed': layer('02_Courtyard_Ground::Garden_Bed_Mulch', Color.FromArgb(140, 105, 75)),
    'curb': layer('02_Courtyard_Ground::Brick_Curb_Edging', Color.FromArgb(220, 185, 95)),
    'steps': layer('02_Courtyard_Ground::Stepping_Slabs', Color.FromArgb(160, 160, 155)),
    'soil': layer('02_Courtyard_Ground::Soil_Mounds', Color.FromArgb(45, 38, 32)),
    'planter': layer('02_Courtyard_Ground::Pallet_Planters', Color.FromArgb(165, 125, 80)),
    'trunk': layer('03_Vegetation::Tree_Trunks_Branches', Color.FromArgb(95, 75, 60)),
    'crown': layer('03_Vegetation::Tree_Crowns', Color.FromArgb(105, 150, 70), 0.55),
    'shrub': layer('03_Vegetation::Shrubs', Color.FromArgb(85, 125, 60)),
    'plants': layer('03_Vegetation::Planter_Plants', Color.FromArgb(70, 140, 70)),
    'pit': layer('04_Furniture_Elements::Brick_Fire_Pit', Color.FromArgb(185, 85, 55)),
    'steel': layer('04_Furniture_Elements::Metal_Stand', Color.FromArgb(40, 40, 40)),
    'birdhouse': layer('04_Furniture_Elements::Birdhouse', Color.FromArgb(240, 140, 180)),
    'marks': layer('06_Reference::Photo_Survey_Points', Color.FromArgb(255, 0, 255)),
}
doc.Layers[LY['marks']].IsVisible = False

# ------------------------------------------------------------------ cleanup previous run
s_ = Rhino.DocObjects.ObjectEnumeratorSettings()
s_.HiddenObjects = True
s_.LockedObjects = True
for o in [o for o in doc.Objects.GetObjectList(s_) if o.Attributes.GetUserString(TAG)]:
    doc.Objects.Delete(o, True, True)

group = doc.Groups.Add('Garden_Alfoldi6')
count = {}


def put(geo, key, name=None, note=None):
    geo.Transform(XF)
    at = Rhino.DocObjects.ObjectAttributes()
    at.LayerIndex = LY[key]
    at.WireDensity = -1
    at.SetUserString(TAG, '2026-10-13')
    at.SetUserString('source', 'photogrammetry: photos 5/8/9/12 calibrated on pavilion facade')
    if note:
        at.SetUserString('note', note)
    if name:
        at.Name = name
    at.AddToGroup(group)
    if isinstance(geo, rg.Brep):
        doc.Objects.AddBrep(geo, at)
    elif isinstance(geo, rg.Curve):
        doc.Objects.AddCurve(geo, at)
    elif isinstance(geo, rg.Point):
        doc.Objects.AddPoint(geo.Location, at)
    elif isinstance(geo, rg.TextDot):
        doc.Objects.AddTextDot(geo, at)
    else:
        doc.Objects.Add(geo, at)
    count[key] = count.get(key, 0) + 1


def slab(pts_sn, z0, z1, key, name=None, note=None):
    """extrude a plan polygon given in (s, n) from z0 to z1"""
    poly = rg.PolylineCurve([P(s, n, z0) for s, n in pts_sn] + [P(pts_sn[0][0], pts_sn[0][1], z0)])
    ext = rg.Extrusion.Create(poly, z1 - z0, True)
    if ext is None or ext.GetBoundingBox(True).Max.Z < z0 + 1e-4:
        ext = rg.Extrusion.Create(poly, -(z1 - z0), True)
    if ext is not None:
        put(ext.ToBrep(), key, name, note)


def rect_sn(sc_, nc, ls, ln, ang=0.0):
    """rectangle centred (sc_, nc), size ls (along s) x ln (along n), rotated ang (rad) in plan"""
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        ds, dn = a * ls / 2, b * ln / 2
        out.append((sc_ + ds * ca - dn * sa, nc + ds * sa + dn * ca))
    return out


def ellipsoid(s, n, zc, rs, rn, rz, key, name=None):
    sph = rg.Sphere(rg.Point3d(0, 0, 0), 1.0).ToBrep()
    sph.Transform(rg.Transform.Scale(rg.Plane.WorldXY, rs, rn, rz))
    sph.Transform(rg.Transform.Translation(rg.Vector3d(P(s, n, zc))))
    put(sph, key, name)


def limb(p0, p1, r0, r1, key='trunk', name=None):
    """tapered round member between two (s, n, z) points"""
    a, b = P(*p0), P(*p1)
    axis = b - a
    pl0 = rg.Plane(a, axis)
    pl1 = rg.Plane(b, axis)
    c0 = rg.ArcCurve(rg.Circle(pl0, r0))
    c1 = rg.ArcCurve(rg.Circle(pl1, r1))
    lofts = rg.Brep.CreateFromLoft([c0, c1], rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Straight, False)
    if lofts:
        br = lofts[0].CapPlanarHoles(TOL) or lofts[0]
        put(br, key, name)


# ------------------------------------------------------------------ walkway (concrete slabs along the west facade)
s = S_NORTH
while s < S_SOUTH - 1e-6:
    s1 = min(s + 1.0, S_SOUTH)
    slab([(s + 0.01, 0.02), (s1 - 0.01, 0.02), (s1 - 0.01, WALK_W), (s + 0.01, WALK_W)], 0.0, 0.05, 'walk', 'walkway slab')
    s = s1
# apron in front of the north facade
slab([(-1.2, -4.62), (-0.02, -4.62), (-0.02, 0.0), (-1.2, 0.0)], 0.0, 0.05, 'walk', 'north apron slabs (assumed)')

# ------------------------------------------------------------------ garden bed (mulch) between walkway and curb
CURB_W = 0.065
bed_pts = [(S_NORTH, WALK_W), (S_SOUTH, WALK_W), (S_SOUTH, curb_n(S_SOUTH) - CURB_W / 2),
           (S_NORTH, curb_n(S_NORTH) - CURB_W / 2)]
slab(bed_pts, -0.02, 0.03, 'bed', 'garden bed - wood chip mulch',
     note='bed from s=%.1f to %.1f; north/south ends approximate' % (S_NORTH, S_SOUTH))

# ------------------------------------------------------------------ brick curb (yellow bricks on edge)
def curb_run(p0, p1, name):
    (sa, na), (sb, nb) = p0, p1
    dl = math.hypot(sb - sa, nb - na)
    ts, tn = (sb - sa) / dl, (nb - na) / dl
    os_, on = -tn * CURB_W / 2, ts * CURB_W / 2
    slab([(sa - os_, na - on), (sb - os_, nb - on), (sb + os_, nb + on), (sa + os_, na + on)], -0.08, 0.07, 'curb', name)

curb_run((S_NORTH, curb_n(S_NORTH)), (S_SOUTH, curb_n(S_SOUTH)), 'brick curb (driveway side)')
curb_run((S_SOUTH, WALK_W), (S_SOUTH, curb_n(S_SOUTH)), 'brick curb (south end, assumed)')
curb_run((S_NORTH, WALK_W), (S_NORTH, curb_n(S_NORTH)), 'brick curb (north end, assumed)')

# ------------------------------------------------------------------ stepping slabs across the bed (perpendicular to curb)
ang_curb = math.atan(b_c)
perp = (-math.sin(ang_curb), math.cos(ang_curb))
# start at walkway edge on the line through the measured slab centre
t0 = (WALK_W + 0.30 - SLABS_C[1]) / perp[1]
for i in range(5):
    c = (SLABS_C[0] + perp[0] * (t0 + i * 0.68), SLABS_C[1] + perp[1] * (t0 + i * 0.68))
    if c[1] > curb_n(c[0]) - 0.3:
        break
    slab(rect_sn(c[0], c[1], 0.45, 0.50, ang_curb), 0.0, 0.05, 'steps', 'stepping slab')

# ------------------------------------------------------------------ soil mounds (fresh black soil, photos 8/13)
for (ms_, mn_), r in ((MOUND1, (0.75, 0.55)), (MOUND2, (0.95, 0.70))):
    mn_ = min(max(mn_, WALK_W + r[1]), curb_n(ms_) - r[1] - 0.1)
    ellipsoid(ms_, mn_, 0.0, r[0], r[1], 0.28, 'soil', 'soil mound')

# ------------------------------------------------------------------ shrubs (low spreading mass, ~0.6-0.9 m)
random.seed(6)
keep_out = [(T1, 0.75), (T4, 0.6), (MOUND1, 0.8), (MOUND2, 1.0), (STAND, 0.6), (SAPLING, 0.3)]
shr = 0
s = 2.7
while s < 16.6:
    n_lo, n_hi = WALK_W + 0.35, curb_n(s) - 0.40
    n = n_lo
    while n < n_hi:
        ss = s + random.uniform(-0.25, 0.25)
        nn = n + random.uniform(-0.2, 0.2)
        on_path = abs((ss - SLABS_C[0]) * math.cos(ang_curb) + (nn - SLABS_C[1]) * math.sin(ang_curb)) < 0.45
        blocked = on_path or any(math.hypot(ss - k[0][0], nn - k[0][1]) < k[1] for k in keep_out)
        if not blocked:
            rs, rn = random.uniform(0.45, 0.75), random.uniform(0.45, 0.7)
            rn = min(rn, nn - WALK_W - 0.05, curb_n(ss) - nn - 0.05)   # stay inside walkway edge / curb
            if rn < 0.25:
                n += 0.5
                continue
            h = random.uniform(0.55, 0.9)
            ellipsoid(ss, nn, h * 0.35, rs, rn, h * 0.65, 'shrub', 'shrub')
            shr += 1
        n += random.uniform(0.75, 1.0)
    s += random.uniform(0.8, 1.05)

# ------------------------------------------------------------------ trees
def pollard_heads(base, fork_z, head_z, top_z, limbs, r_trunk, name):
    s0, n0 = base
    limb((s0, n0, 0.0), (s0, n0, fork_z), r_trunk, r_trunk * 0.85, name=name + ' trunk')
    for i, (ds, dn) in enumerate(limbs):
        hs, hn = s0 + ds, n0 + dn
        limb((s0, n0, fork_z - 0.2), (hs, hn, head_z), r_trunk * 0.6, r_trunk * 0.45, name=name + ' limb')
        # cut stubs at the head
        for k in range(3):
            a = 2 * math.pi * (k / 3.0) + i
            limb((hs, hn, head_z - 0.1), (hs + 0.35 * math.cos(a), hn + 0.35 * math.sin(a), head_z + 0.35), 0.06, 0.05, name=name + ' cut stub')
        # thin regrowth leaders
        for k in range(3):
            a = 2 * math.pi * (k / 3.0) + 0.6 + i
            ls = top_z - head_z
            limb((hs, hn, head_z), (hs + 0.25 * ls * math.cos(a), hn + 0.25 * ls * math.sin(a), top_z - random.uniform(0, 1.5)), 0.045, 0.012, name=name + ' leader')


# T1 - large pollarded willow next to the curb
pollard_heads(T1, T1_FORK, T1_HEAD, T1_TOP, [(-0.6, -0.4), (0.5, 0.45)], 0.20, 'T1 pollarded willow')
ellipsoid(T1[0], T1[1], (T1_HEAD + T1_TOP) / 2 + 1.0, 1.9, 1.9, (T1_TOP - T1_HEAD) / 2 - 0.6, 'crown', 'T1 crown (sparse, narrow leaves)')

# T4 - second pollarded trunk with regrowth (pink birdhouse beside it)
pollard_heads(T4, T4_CUT - 0.6, T4_CUT, T4_TOP, [(0.0, 0.0)], 0.14, 'T4 pollarded tree')
ellipsoid(T4[0], T4[1], (T4_CUT + T4_TOP) / 2, 1.7, 1.7, max((T4_TOP - T4_CUT) / 2, 0.8), 'crown', 'T4 regrowth crown')
slab(rect_sn(T4[0] - 0.35, T4[1] + 0.3, 0.3, 0.3), 1.55, 1.85, 'birdhouse', 'pink birdhouse')
limb((T4[0] - 0.35, T4[1] + 0.3, 0.0), (T4[0] - 0.35, T4[1] + 0.3, 1.55), 0.025, 0.025, 'steel', 'birdhouse post')

# T2 - weeping willow at the south end of the bed (two leaning stems)
limb((T2[0], T2[1], 0.0), (T2[0] + 0.6, T2[1] + 0.9, 3.2), 0.16, 0.11, name='T2 weeping willow stem')
limb((T2[0], T2[1], 0.0), (T2[0] - 0.4, T2[1] + 1.4, 3.0), 0.13, 0.09, name='T2 weeping willow stem')
ellipsoid(T2[0] + 0.1, T2[1] + 1.1, T2_TOP * 0.55, 3.0, 3.0, T2_TOP * 0.45, 'crown', 'T2 weeping willow crown')

# T3 - large tree by the street wall (tree-of-heaven type, pinnate leaves, pink seed clusters)
limb((T3[0], T3[1], 0.0), (T3[0], T3[1], T3_TOP * 0.35), 0.24, 0.18, name='T3 large tree trunk')
ellipsoid(T3[0], T3[1], T3_TOP * 0.66, 4.0, 4.0, T3_TOP * 0.34, 'crown', 'T3 large tree crown')

# T5 - large-leaved tree north of the pavilion, leaning towards it
limb((T5[0], T5[1], 0.0), (T5[0] + 0.9, T5[1] - 0.2, 3.4), 0.16, 0.11, name='T5 large-leaved tree trunk')
ellipsoid(T5[0] + 1.2, T5[1] - 0.3, 5.1, 2.4, 2.4, 2.1, 'crown', 'T5 crown (large leaves)')

# sapling in the bed (thin stem on a stake)
limb((SAPLING[0], SAPLING[1], 0.0), (SAPLING[0], SAPLING[1], 1.8), 0.015, 0.01, name='sapling')
ellipsoid(SAPLING[0], SAPLING[1], 1.5, 0.3, 0.3, 0.35, 'crown', 'sapling foliage')

# ------------------------------------------------------------------ brick fire pit (hollow box, 6 courses)
PIT_S, PIT_N, PIT_L, PIT_H, PIT_T = -0.57, 1.93, 0.62, 0.45, 0.12
o = PIT_L / 2
slab([(PIT_S - o, PIT_N - o), (PIT_S + o, PIT_N - o), (PIT_S + o, PIT_N - o + PIT_T), (PIT_S - o, PIT_N - o + PIT_T)], 0, PIT_H, 'pit', 'fire pit wall')
slab([(PIT_S - o, PIT_N + o - PIT_T), (PIT_S + o, PIT_N + o - PIT_T), (PIT_S + o, PIT_N + o), (PIT_S - o, PIT_N + o)], 0, PIT_H, 'pit', 'fire pit wall')
slab([(PIT_S - o, PIT_N - o + PIT_T), (PIT_S - o + PIT_T, PIT_N - o + PIT_T), (PIT_S - o + PIT_T, PIT_N + o - PIT_T), (PIT_S - o, PIT_N + o - PIT_T)], 0, PIT_H, 'pit', 'fire pit wall')
slab([(PIT_S + o - PIT_T, PIT_N - o + PIT_T), (PIT_S + o, PIT_N - o + PIT_T), (PIT_S + o, PIT_N + o - PIT_T), (PIT_S + o - PIT_T, PIT_N + o - PIT_T)], 0, PIT_H, 'pit', 'fire pit wall')

# ------------------------------------------------------------------ metal stand (square tube frame, 0.47 m)
ST_L, ST_W, ST_H, TB = 0.36, 0.30, 0.47, 0.02
for a in (-1, 1):
    for b in (-1, 1):
        cs, cn = STAND[0] + a * (ST_L / 2 - TB / 2), STAND[1] + b * (ST_W / 2 - TB / 2)
        slab(rect_sn(cs, cn, TB, TB), 0.0, ST_H, 'steel', 'stand leg')
for a in (-1, 1):
    slab(rect_sn(STAND[0] + a * (ST_L / 2 - TB / 2), STAND[1], TB, ST_W), ST_H - TB, ST_H, 'steel', 'stand rail')
    slab(rect_sn(STAND[0], STAND[1] + a * (ST_W / 2 - TB / 2), ST_L, TB), ST_H - TB, ST_H, 'steel', 'stand rail')

# ------------------------------------------------------------------ pallet planters along the grey west wall (n = 13.6, OSM)
WALL_N = 13.6
p5 = CAM['p5'][0]
fronts = []
for u, v in ((1180, 750), (1350, 775), (1490, 780)):
    ds, dn, up = pg.pc_ray(p5, u, v, 750., 562.5)
    k = (WALL_N - 0.8 - p5[2]) / dn
    fronts.append(p5[1] + k * ds)
s_lo, s_hi = min(fronts) - 0.6, max(fronts) + 0.6
n_pl = int(round((s_hi - s_lo) / 1.3))
# the planters themselves are now built from real EUR pallets by build_pallet_planters.py (photo 37)

# ------------------------------------------------------------------ survey marks (hidden) - measured photo points
for nm, (s0, n0) in (('T1', T1), ('T4', T4), ('T2', T2), ('stand', STAND), ('slabs', SLABS_C), ('mound1', MOUND1), ('mound2', MOUND2), ('sapling', SAPLING)):
    put(rg.TextDot(nm, P(s0, n0, 0.1)), 'marks', 'survey ' + nm)
for q in curb_pts:
    put(rg.Point(P(q[0], q[1], 0.0)), 'marks', 'curb survey point')

doc.Views.Redraw()
for k in sorted(CAM):
    p, cx, cy, rms = CAM[k]
    print('cam %s: s=%.2f n=%.2f h=%.2f yaw=%.1f pitch=%.1f rms=%.1f px' % (k, p[1], p[2], p[3], math.degrees(p[4]), math.degrees(p[5]), rms))
print('walkway width %.2f | curb n = %.2f + %.3f s (%.1f deg, rms %.2f m)' % (WALK_W, a_c, b_c, math.degrees(ang_curb), curb_rms))
print('T1 %s fork %.1f head %.1f top>=%.1f | T4 %s cut %.1f top %.1f | T2 %s top %.1f | T3 %s top %.1f' % (
    tuple(round(x, 2) for x in T1), T1_FORK, T1_HEAD, T1_TOP, tuple(round(x, 2) for x in T4), T4_CUT, T4_TOP,
    tuple(round(x, 2) for x in T2), T2_TOP, T3, T3_TOP))
print('stand %s slabs %s mounds %s %s sapling %s planters s %.1f-%.1f (%d)' % (
    tuple(round(x, 2) for x in STAND), tuple(round(x, 2) for x in SLABS_C), tuple(round(x, 2) for x in MOUND1),
    tuple(round(x, 2) for x in MOUND2), tuple(round(x, 2) for x in SAPLING), s_lo, s_hi, n_pl))
print('shrubs %d' % shr)
for k in sorted(count):
    print('%s: %d' % (k, count[k]))
