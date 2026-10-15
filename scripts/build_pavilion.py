# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - builds the glazed steel pavilion in the Alfoldi u. 6 courtyard.
# Re-runnable: deletes everything it created before (user text 'pavilion_build').
#
# Geometry source
#   footprint : OSM way 246908973 (south end C-D kept), long side extended to 16 bays
#               (photo count, confirmed in 2 photos; matches user's Layer 02 strip = 18.51 m)
#   module    : 1.157 m long side (door photo: bay 265 px vs 2.0 m door leaf), 4.621/4 short side
#   heights   : door photo (frontal, 1 px = 4.37 mm) + corner photos for the fascia
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'pavilion_build'

# ------------------------------------------------------------------ parameters (m)
C_WORLD = rg.Point3d(-10.31, -19.80, 0)          # SW corner (OSM, south/street end)
U = rg.Vector3d(-0.33761, 0.94128, 0)            # along long side, south -> north
V = rg.Vector3d(0.94130, 0.33757, 0)             # across, west facade -> east firewall
N_LONG, N_SHORT = 16, 4
M = 1.157                                        # bay, long side
W = 4.6213                                       # width (OSM)
MW = W / N_SHORT                                 # bay, short side
L = N_LONG * M                                   # 18.512

Z_PLINTH = 0.28      # top of plinth panel / bottom rail of lower glazing
Z_TRANSOM0 = 2.20    # top of lower glazing / door head
Z_TRANSOM1 = 2.40    # top of transom band
Z_HEAD0 = 3.38       # top of upper windows
Z_HEAD1 = 3.49       # top of head beam = bottom of fascia
Z_FASCIA = 4.70      # top of fascia on west side = underside of rafters at facade
RAFTER_D = 0.12
ROOF_T = 0.03
ROOF_FALL = 0.0195   # rises towards the firewall (east)
EAVE = 0.35          # rafter overhang beyond west facade

POST_W, POST_D = 0.08, 0.12
CORNER = 0.12
FRAME_W, FRAME_D0, FRAME_D1 = 0.05, 0.02, 0.08
GLASS_D = 0.05
FASCIA_OUT = 0.06    # fascia sits proud of the facade line

# west facade bays numbered 1..16 from the NORTH corner
WEST_GLAZED_DOOR = [6]
WEST_SOLID_DOOR = [9]          # cream door with vent grille
WEST_UPPER_LOUVRE = [13]
WEST_SMALL_GRILLE = [15]
# north facade bays numbered 1..4 from the EAST (firewall) end
NORTH_GLAZED_DOOR = [2, 4]

# ------------------------------------------------------------------ layers
def layer(path, col, mat=None):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        parts = path.split('::')
        parent = System.Guid.Empty
        if len(parts) > 1:
            parent = doc.Layers[layer('::'.join(parts[:-1]), Color.FromArgb(200, 0, 0))].Id
        Lr = Rhino.DocObjects.Layer()
        Lr.Name = parts[-1]
        Lr.Color = col
        Lr.ParentLayerId = parent
        idx = doc.Layers.Add(Lr)
    if mat is not None:
        m = Rhino.DocObjects.Material()
        m.Name = path.split('::')[-1]
        m.DiffuseColor = col
        m.Transparency = mat
        mi = doc.Materials.Add(m)
        lay = doc.Layers[idx]
        lay.RenderMaterialIndex = mi
        lay.CommitChanges()
    return idx

P = 'ADDITIONS::Pavilion::'
LY = {
    'structure': layer(P + 'Steel_Structure', Color.FromArgb(70, 105, 125)),
    'frames': layer(P + 'Window_Frames', Color.FromArgb(165, 165, 160)),
    'glass': layer(P + 'Glazing', Color.FromArgb(150, 185, 200), 0.65),
    'plinth': layer(P + 'Plinth', Color.FromArgb(55, 58, 60)),
    'doors': layer(P + 'Doors', Color.FromArgb(230, 220, 185)),
    'louvres': layer(P + 'Louvres_Grilles', Color.FromArgb(120, 125, 125)),
    'fascia': layer(P + 'Fascia_Profiled_Sheet', Color.FromArgb(180, 186, 190)),
    'roof': layer(P + 'Roof', Color.FromArgb(110, 110, 110)),
    'rafters': layer(P + 'Rafters', Color.FromArgb(140, 75, 35)),
    'drain': layer(P + 'Gutter_Downpipes', Color.FromArgb(195, 198, 200)),
    'foot': layer(P + 'Footprint', Color.FromArgb(200, 0, 0)),
    'old': layer('ADDITIONS::_superseded_placeholder', Color.FromArgb(200, 120, 120)),
}

# ------------------------------------------------------------------ cleanup previous run
s = Rhino.DocObjects.ObjectEnumeratorSettings()
s.HiddenObjects = True
s.LockedObjects = True
old = [o for o in doc.Objects.GetObjectList(s) if o.Attributes.GetUserString(TAG)]
for o in old:
    doc.Objects.Delete(o, True, True)

# park the user's 5 m placeholder + OSM outline (kept for reference, hidden)
# only the two original placeholder objects - never touch anything else the user draws on ADDITIONS
PLACEHOLDERS = ('714ca105-1c65-40eb-883c-a3d4e06913d5', 'd130d65a-dcf4-418e-8616-43965c9ed3f6')
for gid in PLACEHOLDERS:
    o = doc.Objects.FindId(System.Guid(gid))
    if o is None:
        continue
    a = o.Attributes.Duplicate()
    a.LayerIndex = LY['old']
    doc.Objects.ModifyAttributes(o, a, True)
lo = doc.Layers[LY['old']]
lo.IsVisible = False
lo.CommitChanges()

# ------------------------------------------------------------------ helpers (local frame)
# local: X along U (0..L), Y towards WEST (-V) so building is Y in [-W, 0], Z up
plane_local = rg.Plane(C_WORLD, U, -V)
XF = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane_local)
group = doc.Groups.Add('Pavilion_Alfoldi6')
count = {}


def put(geo, key, name=None):
    geo.Transform(XF)
    at = Rhino.DocObjects.ObjectAttributes()
    at.LayerIndex = LY[key]
    at.WireDensity = -1          # no isocurves (clean glazing in shaded views)
    at.SetUserString(TAG, '2026-10-13')
    at.SetUserString('source', 'site photos + OSM way 246908973 (north end extended to 16 bays)')
    if name:
        at.Name = name
    at.AddToGroup(group)
    if isinstance(geo, rg.Brep):
        gid = doc.Objects.AddBrep(geo, at)
    elif isinstance(geo, rg.Curve):
        gid = doc.Objects.AddCurve(geo, at)
    elif isinstance(geo, rg.Surface):
        gid = doc.Objects.AddSurface(geo, at)
    else:
        gid = doc.Objects.Add(geo, at)
    count[key] = count.get(key, 0) + 1
    return gid


def box(x0, x1, y0, y1, z0, z1, key, name=None, pl=None):
    xs, ys, zs = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    if xs[1] - xs[0] < 1e-4 or ys[1] - ys[0] < 1e-4 or zs[1] - zs[0] < 1e-4:
        return None
    b = rg.Box(pl or rg.Plane.WorldXY, rg.Interval(*xs), rg.Interval(*ys), rg.Interval(*zs))
    return put(b.ToBrep(), key, name)


# facade mapping: (s along facade, d depth INTO building from outer face, z) -> local box
class Facade(object):
    def __init__(self, kind):
        self.kind = kind

    def box(self, s0, s1, d0, d1, z0, z1, key, name=None):
        if self.kind == 'W':      # face y=0, s = x
            return box(s0, s1, -d0, -d1, z0, z1, key, name)
        if self.kind == 'N':      # face x=L, s = y
            return box(L - d0, L - d1, s0, s1, z0, z1, key, name)
        if self.kind == 'S':      # face x=0, s = y
            return box(d0, d1, s0, s1, z0, z1, key, name)


def frame_and_glass(F, s0, s1, z0, z1, glass=True, fw=FRAME_W, name=''):
    """rectangular sash frame inside opening + glass pane"""
    F.box(s0, s1, FRAME_D0, FRAME_D1, z0, z0 + fw, 'frames', name + ' frame')
    F.box(s0, s1, FRAME_D0, FRAME_D1, z1 - fw, z1, 'frames', name + ' frame')
    F.box(s0, s0 + fw, FRAME_D0, FRAME_D1, z0 + fw, z1 - fw, 'frames', name + ' frame')
    F.box(s1 - fw, s1, FRAME_D0, FRAME_D1, z0 + fw, z1 - fw, 'frames', name + ' frame')
    if glass:
        F.box(s0 + fw, s1 - fw, GLASS_D - 0.005, GLASS_D + 0.005, z0 + fw, z1 - fw, 'glass', name + ' glass')


def louvre(F, s0, s1, z0, z1, n, name):
    F.box(s0, s1, GLASS_D + 0.005, GLASS_D + 0.015, z0, z1, 'louvres', name + ' back plate')
    step = (z1 - z0) / float(n)
    for i in range(n):
        zz = z0 + i * step + step * 0.25
        F.box(s0, s1, FRAME_D0 - 0.01, GLASS_D, zz, zz + step * 0.45, 'louvres', name + ' slat')


def bay_infill(F, s0, s1, kind, label):
    """s0,s1 = clear opening between post faces"""
    # ---- upper zone (always)
    if kind.get('upper') == 'louvre':
        frame_and_glass(F, s0, s1, Z_TRANSOM1, Z_HEAD0, glass=False, name=label + ' upper')
        louvre(F, s0 + FRAME_W, s1 - FRAME_W, Z_TRANSOM1 + FRAME_W, Z_HEAD0 - FRAME_W, 12, label + ' louvre')
    else:
        frame_and_glass(F, s0 + 0.02, s1 - 0.02, Z_TRANSOM1 + 0.02, Z_HEAD0 - 0.02, name=label + ' upper window')
    # ---- lower zone
    low = kind.get('lower', 'glazed')
    if low == 'glazed':
        F.box(s0, s1, FRAME_D0, FRAME_D1 - 0.02, 0.0, Z_PLINTH, 'plinth', label + ' plinth panel')
        frame_and_glass(F, s0, s1, Z_PLINTH, Z_TRANSOM0, name=label + ' lower')
        if kind.get('grille'):
            mid = 0.5 * (s0 + s1)
            F.box(mid - 0.15, mid + 0.15, GLASS_D - 0.02, GLASS_D + 0.01, 0.95, 1.25, 'louvres', label + ' vent grille')
    elif low == 'glazed_door':
        # fixed frame, door leaf frame, glass, timber push board
        frame_and_glass(F, s0, s1, 0.0, Z_TRANSOM0, glass=False, fw=0.04, name=label + ' door case')
        frame_and_glass(F, s0 + 0.04, s1 - 0.04, 0.02, Z_TRANSOM0 - 0.04, fw=0.07, name=label + ' glazed door')
        F.box(s0 + 0.04, s1 - 0.04, FRAME_D0, FRAME_D1, 0.02, 0.30, 'frames', label + ' door kick plate')
        F.box(s0 + 0.10, s1 - 0.10, -0.05, FRAME_D0, 1.00, 1.12, 'rafters', label + ' timber push board')
    elif low == 'solid_door':
        frame_and_glass(F, s0, s1, 0.0, Z_TRANSOM0, glass=False, fw=0.07, name=label + ' door case')
        lx0, lx1 = s0 + 0.075, s1 - 0.075            # leaf ~0.93 m
        F.box(lx0, lx1, FRAME_D0 + 0.005, FRAME_D0 + 0.045, 0.05, 2.05, 'doors', label + ' door leaf')
        F.box(s0 + 0.07, s1 - 0.07, FRAME_D0, FRAME_D1, 2.05, Z_TRANSOM0 - 0.07, 'frames', label + ' door head infill')
        for zr in (0.72, 1.35):                        # panel rails
            F.box(lx0 + 0.03, lx1 - 0.03, FRAME_D0 - 0.008, FRAME_D0 + 0.005, zr - 0.02, zr + 0.02, 'doors', label + ' door rail')
        mid = 0.5 * (lx0 + lx1)
        F.box(mid - 0.205, mid + 0.205, FRAME_D0 - 0.012, FRAME_D0 + 0.02, 0.28, 0.68, 'louvres', label + ' door vent grille')
        F.box(lx1 - 0.10, lx1 - 0.04, -0.06, FRAME_D0, 1.02, 1.05, 'drain', label + ' door handle')


def posts_and_beams(F, s_start, s_end, n, mod, corner_start, corner_end, label):
    for j in range(n + 1):
        sc_ = s_start + j * mod
        if j == 0:
            a, b = s_start, s_start + (CORNER if corner_start else POST_W)
        elif j == n:
            a, b = s_end - (CORNER if corner_end else POST_W), s_end
        else:
            a, b = sc_ - POST_W / 2, sc_ + POST_W / 2
        F.box(a, b, 0.0, POST_D if not (j in (0, n)) else CORNER, 0.0, Z_HEAD1, 'structure', '%s post %d' % (label, j))
    F.box(s_start, s_end, 0.0, POST_D, Z_TRANSOM0, Z_TRANSOM1, 'structure', label + ' transom beam')
    F.box(s_start, s_end, 0.0, POST_D, Z_HEAD0, Z_HEAD1, 'structure', label + ' head beam')


def openings(s_start, n, mod, s_end):
    """clear openings between post faces"""
    res = []
    for j in range(n):
        a = s_start + j * mod + (CORNER if j == 0 else POST_W / 2)
        b = s_start + (j + 1) * mod - (CORNER if j == n - 1 else POST_W / 2)
        res.append((a, b))
    return res


# ------------------------------------------------------------------ WEST facade (long, glazed, faces garden)
FW = Facade('W')
posts_and_beams(FW, 0.0, L, N_LONG, M, True, True, 'W')
for j, (a, b) in enumerate(openings(0.0, N_LONG, M, L)):
    bay_from_north = N_LONG - j
    kind = {}
    if bay_from_north in WEST_GLAZED_DOOR:
        kind['lower'] = 'glazed_door'
    if bay_from_north in WEST_SOLID_DOOR:
        kind['lower'] = 'solid_door'
    if bay_from_north in WEST_UPPER_LOUVRE:
        kind['upper'] = 'louvre'
    if bay_from_north in WEST_SMALL_GRILLE:
        kind['grille'] = True
    bay_infill(FW, a, b, kind, 'W bay %02d' % bay_from_north)

# ------------------------------------------------------------------ NORTH facade (short, 2 glazed doors)
FN = Facade('N')
posts_and_beams(FN, -W, 0.0, N_SHORT, MW, True, True, 'N')
for j, (a, b) in enumerate(openings(-W, N_SHORT, MW, 0.0)):
    kind = {'lower': 'glazed_door'} if (j + 1) in NORTH_GLAZED_DOOR else {}
    bay_infill(FN, a, b, kind, 'N bay %d' % (j + 1))

# ------------------------------------------------------------------ SOUTH facade (short, not visible in photos -> glazed, assumed)
FS = Facade('S')
posts_and_beams(FS, -W, 0.0, N_SHORT, MW, True, True, 'S')
for j, (a, b) in enumerate(openings(-W, N_SHORT, MW, 0.0)):
    bay_infill(FS, a, b, {}, 'S bay %d (assumed)' % (j + 1))

# ------------------------------------------------------------------ EAST side: abuts the firewall of Alfoldi u. 6-8
box(0.0, L, -W, -W + 0.05, 0.0, Z_FASCIA, 'structure', 'E back wall (abuts firewall, assumed)')

# ------------------------------------------------------------------ roof (rafters + sheet), slight fall to the west gutter
def z_rafter_bottom(y):          # y local (west = 0, east = -W)
    return Z_FASCIA + (-y) * ROOF_FALL

roof_pl = rg.Plane(rg.Point3d(0, 0, Z_FASCIA), rg.Vector3d(1, 0, 0), rg.Vector3d(0, 1, -ROOF_FALL))
n_raf = int(round(L / (M / 2.0)))
for i in range(n_raf + 1):
    x = min(max(i * (M / 2.0), 0.04), L - 0.04)
    box(x - 0.04, x + 0.04, -W, EAVE, 0.0, RAFTER_D - 0.005, 'rafters', 'rafter %02d' % i, pl=roof_pl)
box(-FASCIA_OUT, L + FASCIA_OUT, -W, EAVE + 0.04, RAFTER_D, RAFTER_D + ROOF_T, 'roof', 'roof sheet', pl=roof_pl)

# ------------------------------------------------------------------ fascia (horizontal profiled sheet) W / N / S
RIB = 0.12
def ribs(axis, a0, a1, fixed0, fixed1, z0, z_top_fn):
    z = z0 + RIB / 2
    while z < z_top_fn() - 0.03:
        if axis == 'x':
            box(a0, a1, fixed0, fixed1, z - 0.012, z + 0.012, 'fascia', 'fascia rib')
        else:
            box(fixed0, fixed1, a0, a1, z - 0.012, z + 0.012, 'fascia', 'fascia rib')
        z += RIB

# west: below the rafter tails
box(-FASCIA_OUT, L + FASCIA_OUT, 0.0, FASCIA_OUT, Z_HEAD1, Z_FASCIA, 'fascia', 'W fascia')
ribs('x', -FASCIA_OUT, L + FASCIA_OUT, FASCIA_OUT, FASCIA_OUT + 0.015, Z_HEAD1, lambda: Z_FASCIA)

# north / south: closes the roof edge, top follows the roof fall
def end_fascia(x0, x1, rib_x0, rib_x1, label):
    top_w = z_rafter_bottom(0) + RAFTER_D + ROOF_T
    top_e = z_rafter_bottom(-W) + RAFTER_D + ROOF_T
    pts = [rg.Point3d(0, FASCIA_OUT, Z_HEAD1), rg.Point3d(0, -W, Z_HEAD1),
           rg.Point3d(0, -W, top_e), rg.Point3d(0, EAVE + 0.04, top_w - (EAVE + 0.04) * ROOF_FALL),
           rg.Point3d(0, FASCIA_OUT, top_w - FASCIA_OUT * ROOF_FALL), rg.Point3d(0, FASCIA_OUT, Z_HEAD1)]
    prof = rg.PolylineCurve(pts)
    prof.Transform(rg.Transform.Translation(x0, 0, 0))
    ext = rg.Extrusion.Create(prof, -(x1 - x0), True)
    if ext is None or ext.GetBoundingBox(True).Max.X < x0 + 1e-3:
        ext = rg.Extrusion.Create(prof, (x1 - x0), True)
    put(ext.ToBrep(), 'fascia', label + ' fascia')
    ribs('y', -W, FASCIA_OUT, rib_x0, rib_x1, Z_HEAD1, lambda: top_w - 0.02)

end_fascia(L, L + FASCIA_OUT, L + FASCIA_OUT, L + FASCIA_OUT + 0.015, 'N')
end_fascia(-FASCIA_OUT, 0.0, -FASCIA_OUT - 0.015, -FASCIA_OUT, 'S')

# ------------------------------------------------------------------ gutter + downpipes
GR = 0.075
g_y = EAVE + GR + 0.01
g_z = z_rafter_bottom(0) + RAFTER_D - EAVE * ROOF_FALL     # top edge of gutter just under roof edge
gpl = rg.Plane(rg.Point3d(-FASCIA_OUT, g_y, g_z), rg.Vector3d(0, 1, 0), rg.Vector3d(0, 0, -1))
arc = rg.ArcCurve(rg.Arc(gpl, GR, math.pi))
gs = rg.Surface.CreateExtrusion(arc, rg.Vector3d(L + 2 * FASCIA_OUT, 0, 0))
put(gs.ToBrep(), 'drain', 'gutter (half-round)')

def downpipe(x, label):
    pts = [rg.Point3d(x, g_y, g_z - GR), rg.Point3d(x, g_y, 3.45),
           rg.Point3d(x, 0.08, 3.05), rg.Point3d(x, 0.08, 0.15), rg.Point3d(x, 0.30, 0.05)]
    pl = rg.PolylineCurve(pts)
    crv = rg.Curve.CreateFilletCornersCurve(pl, 0.12, TOL, math.radians(1)) or pl
    pipes = rg.Brep.CreatePipe(crv, 0.05, False, rg.PipeCapMode.Flat, True, TOL, math.radians(1))
    for p in pipes or []:
        put(p, 'drain', label)

downpipe(L - 0.10, 'downpipe N')
downpipe(0.10, 'downpipe S')

# ------------------------------------------------------------------ footprint outline (outer face of facades)
fp = rg.PolylineCurve([rg.Point3d(0, 0, 0), rg.Point3d(L, 0, 0), rg.Point3d(L, -W, 0),
                       rg.Point3d(0, -W, 0), rg.Point3d(0, 0, 0)])
put(fp, 'foot', 'Pavilion footprint %.2f x %.2f m (16 x %.3f / 4 x %.3f)' % (L, W, M, MW))

doc.Views.Redraw()
print('L=%.3f W=%.3f module long=%.3f short=%.3f' % (L, W, M, MW))
for k in sorted(count):
    print('%s: %d' % (k, count[k]))
print('superseded placeholder objects moved: hidden layer ADDITIONS::_superseded_placeholder')
