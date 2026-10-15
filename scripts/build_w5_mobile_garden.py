# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 5 (mobile garden): put the four pallet beds on castors.
# Run AFTER build_pallet_planters.py (it moves that script's objects). Re-runnable.
#
# Brief (user, 2026-10-14): make the community garden mobile by adding heavy-duty wheels to the EUR pallets,
# fitted with the help of hand pallet trucks ("manual hydraulic forklifts").
#
# Why low-profile castors: a hand pallet truck lowers to ~85 mm and lifts to ~200 mm; its forks bear on the
# pallet's cross boards ~100 mm above the ground, so it can raise a bed by only ~100 mm. A standard Ø125 heavy
# castor stands ~160 mm and would not slide under. Low-profile castors (Ø75 wheel, ~95 mm build height,
# ~200-300 kg each) do; and afterwards the lowered forks still pass under the bottom boards between the castors,
# so a truck can lift a bed again later.
#
# Per bed (2 pallets side by side, 2 high, ~550 kg with wet soil): 6 castors under the bottom-pallet blocks
#   4 swivel at the corners (the 2 on the yard side with brakes), 2 fixed at the middle - their plates bridge the
#   joint between the two pallets and tie them together. Fitting: two trucks (one per pallet column) lift together,
#   castors slide under the corner / joint blocks, M10 coach bolts through the bottom boards into the blocks.
#
# Model convention: the grounded beds (preexistence) move to 10_Removed::w3_..., raised copies + castors go to
# 09_Workshops::w3_...::Beds / ::Castors; one pallet truck is shown as a workshop prop (own sub-layer).
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'w3_mobile'
PLANTER_TAG = 'pallets_build'
STAGE = 'w5_mobile_garden'
ADD = '09_Workshops::' + STAGE
REM = '10_Removed::' + STAGE

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)


def P(s, n, z=0.0):
    return PL.PointAt(L - s, n, z)


# beds as built by build_pallet_planters.py (keep in sync): front (yard-side) edge n0 = WALL_N - gap - 1.2
WALL_N = 13.58
UNITS = [('A', 9.0, 0.00), ('B', 11.3, 0.08), ('C', 13.3, 0.18), ('D', 15.4, 0.30)]
H = 0.095                                        # castor build height = how much the beds are raised

ALL = Rhino.DocObjects.ObjectEnumeratorSettings()
ALL.HiddenObjects = True
ALL.LockedObjects = True
ALL.VisibleFilter = False


def rmat(name):
    for rm in doc.RenderMaterials:
        if rm.Name == name:
            return rm
    return None


def layer(path, color, mat=None):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        parent = path.rsplit('::', 1)[0]
        pidx = doc.Layers.FindByFullPath(parent, -1)
        if pidx < 0:
            pidx = layer(parent, color)
        lay = Rhino.DocObjects.Layer()
        lay.Name = path.rsplit('::', 1)[-1]
        lay.ParentLayerId = doc.Layers[pidx].Id
        lay.Color = color
        idx = doc.Layers.Add(lay)
    if mat is not None:
        doc.Layers[idx].RenderMaterial = mat if not isinstance(mat, str) else rmat(mat)
    return idx


# ------------------------------------------------------------------ 0. clean previous run
# The mobile beds have since been arranged (moved / copied) by hand in Rhino and are edited by
# build_w5_seating.py. Rebuilding would throw that arrangement away, so it only happens on purpose.
try:
    REBUILD
except NameError:
    REBUILD = False
existing = [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') in (TAG, 'w3_seating')]
if existing and not REBUILD:
    raise Exception('Stage 2 objects exist (%d) and may have been arranged by hand. Set REBUILD = True before '
                    'execfile() to delete them and rebuild the beds in their original positions.' % len(existing))
for o in existing:
    doc.Objects.Delete(o, True, True)

# ------------------------------------------------------------------ 1. grounded beds -> 10_Removed (once)
moved = 0
for o in list(doc.Objects.GetObjectList(ALL)):
    a = o.Attributes
    src = doc.Layers[a.LayerIndex]
    if not a.GetUserString(PLANTER_TAG) or src.FullPath.startswith('10_Removed::'):
        continue
    di = layer(REM + '::' + src.Name, Color.FromArgb(190, 60, 60), src.RenderMaterial)
    a = a.Duplicate()
    a.SetUserString('orig_layer', src.FullPath)
    a.SetUserString('removed_in', STAGE)
    a.LayerIndex = di
    doc.Objects.ModifyAttributes(o, a, True)
    moved += 1

# ------------------------------------------------------------------ 2. raised copies on 09_Workshops::...::Beds
def group_for(name):
    """one group per bed (raised bed + its castors) and one for the truck (user: group the pallets individually)"""
    try:
        gi = doc.Groups.Find(name)
    except Exception:
        gi = -1
    return gi if gi >= 0 else doc.Groups.Add(name)


try:                                                 # the old single group for the whole stage is no longer used
    old = doc.Groups.Find('Mobile_Garden_W2')
    if old >= 0 and doc.Groups.GroupObjectCount(old) == 0:
        doc.Groups.Delete(old)
except Exception:
    pass
up = rg.Transform.Translation(0, 0, H)
copied = 0
for o in list(doc.Objects.GetObjectList(ALL)):
    a = o.Attributes
    src = doc.Layers[a.LayerIndex]
    if not a.GetUserString(PLANTER_TAG) or not src.FullPath.startswith(REM + '::'):
        continue
    g = o.Geometry.Duplicate()
    g.Transform(up)
    na = a.Duplicate()
    na.LayerIndex = layer(ADD + '::Beds::' + src.Name, Color.FromArgb(165, 125, 80), src.RenderMaterial)
    na.DeleteUserString(PLANTER_TAG)              # owned by this script, not by build_pallet_planters.py
    na.DeleteUserString('orig_layer')
    na.DeleteUserString('removed_in')
    na.SetUserString('build', TAG)
    na.RemoveFromAllGroups()
    na.AddToGroup(group_for('Mobile bed %s (W5)' % a.GetUserString('planter_unit')))
    doc.Objects.Add(g, na)
    copied += 1

# ------------------------------------------------------------------ 3. castors (+ pallet truck prop)
LY = {
    'steel': layer(ADD + '::Castors::Castor_Steel', Color.FromArgb(178, 182, 184), 'AU6 Galvanised steel'),
    'wheel': layer(ADD + '::Castors::Castor_Wheels', Color.FromArgb(28, 28, 28), 'AU6 Plastic black'),
    'brake': layer(ADD + '::Castors::Brake_Levers', Color.FromArgb(190, 30, 40), 'AU6 Sign red'),
    'truck': layer(ADD + '::Tool_Pallet_Truck', Color.FromArgb(215, 120, 40), 'AU6 Steel painted orange'),
    # own layer: the truck's wheels must come and go with the truck, not with the beds' castors
    'truckw': layer(ADD + '::Tool_Pallet_Truck_Wheels', Color.FromArgb(28, 28, 28), 'AU6 Plastic black'),
}
made = {}


def add(brep, key, name, unit=''):
    if brep is None:
        print('FAILED: ' + name)
        return
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY[key]
    a.Name = name
    a.SetUserString('build', TAG)
    if unit:
        a.SetUserString('planter_unit', unit)
        a.AddToGroup(group_for('Mobile bed %s (W5)' % unit))
    else:                                            # the pallet truck: installation tool, its own group
        a.AddToGroup(group_for('Pallet truck (W5)'))
    if doc.Objects.AddBrep(brep, a) != System.Guid.Empty:
        made[key] = made.get(key, 0) + 1


def box(s0, s1, n0, n1, z0, z1):
    return rg.Box(PL, rg.Interval(L - max(s0, s1), L - min(s0, s1)), rg.Interval(min(n0, n1), max(n0, n1)),
                  rg.Interval(min(z0, z1), max(z0, z1))).ToBrep()


def cyl_s(s, n, z, r, w):
    """cylinder with its axis along s (wheels / axles), centred on (s, n, z), width w"""
    base = P(s - w / 2, n, z)
    axis = P(s + w / 2, n, z) - base
    return rg.Cylinder(rg.Circle(rg.Plane(base, axis), r), axis.Length).ToBrep(True, True)


def cyl_z(s, n, z0, r, h):
    return rg.Cylinder(rg.Circle(rg.Plane(P(s, n, z0), rg.Vector3d.ZAxis), r), h).ToBrep(True, True)


def tube(p0, p1, r):
    a, b = P(*p0), P(*p1)
    return rg.Cylinder(rg.Circle(rg.Plane(a, b - a), r), (b - a).Length).ToBrep(True, True)


# low-profile heavy castor, Ø75 x 32 wheel, 100 x 85 plate, 95 mm build height
WR, WW = 0.0375, 0.032


def castor(s, n, kind, unit, name):
    add(box(s - 0.05, s + 0.05, n - 0.0425, n + 0.0425, H - 0.005, H), 'steel', name + ' top plate', unit)
    if kind == 'fixed':
        wn, ftop = n, H - 0.005
    else:                                        # swivel: ball race under the plate, wheel trails 20 mm
        add(cyl_z(s, n, H - 0.015, 0.038, 0.010), 'steel', name + ' swivel race', unit)
        wn, ftop = n + 0.02, H - 0.015
    for side in (-1, 1):
        add(box(s + side * (WW / 2 + 0.002), s + side * (WW / 2 + 0.006), wn - 0.032, wn + 0.032, WR - 0.012, ftop),
            'steel', name + ' fork', unit)
    add(cyl_s(s, wn, WR, 0.007, WW + 0.014), 'steel', name + ' axle', unit)
    add(cyl_s(s, wn, WR, WR, WW), 'wheel', name + ' wheel (polyurethane)', unit)
    if kind == 'brake':                          # foot brake pointing to the yard (n smaller)
        add(box(s - 0.018, s + 0.018, wn - 0.075, wn - 0.03, WR + 0.012, WR + 0.024), 'brake', name + ' foot brake', unit)


for u, s0, gap in UNITS:
    n1 = WALL_N - gap
    n0 = n1 - 1.2                                # yard side
    nf, nb = n0 + 0.0725, n1 - 0.0725            # centre lines of the front / back block rows
    for s, kind_f, kind_b, where in ((s0 + 0.055, 'brake', 'swivel', 'north corner'),
                                     (s0 + 0.80, 'fixed', 'fixed', 'middle'),
                                     (s0 + 1.545, 'brake', 'swivel', 'south corner')):
        castor(s, nf, kind_f, u, 'bed %s castor %s front (%s)' % (u, where, kind_f))
        castor(s, nb, kind_b, u, 'bed %s castor %s back (%s)' % (u, where, kind_b))

# pallet truck (prop): forks lowered, slid under the north pallet column of bed A from the yard side
u, s0, gap = UNITS[0]
n0 = WALL_N - gap - 1.2
for fs in (s0 + 0.21, s0 + 0.59):                # forks sit in the gaps between the pallet's bottom boards
    add(box(fs - 0.08, fs + 0.08, n0 - 0.02, n0 + 1.13, 0.035, 0.080), 'truck', 'pallet truck fork')
    add(cyl_s(fs, n0 + 1.06, 0.02, 0.02, 0.07), 'truckw', 'pallet truck fork roller')
add(box(s0 + 0.13, s0 + 0.67, n0 - 0.32, n0 - 0.02, 0.035, 0.20), 'truck', 'pallet truck chassis')
add(cyl_z(s0 + 0.40, n0 - 0.20, 0.20, 0.055, 0.28), 'truck', 'pallet truck hydraulic pump')
for ws in (s0 + 0.31, s0 + 0.49):
    add(cyl_s(ws, n0 - 0.24, 0.09, 0.09, 0.05), 'truckw', 'pallet truck steering wheel')
add(tube((s0 + 0.40, n0 - 0.20, 0.45), (s0 + 0.40, n0 - 0.62, 1.15), 0.018), 'truck', 'pallet truck tiller')
add(box(s0 + 0.28, s0 + 0.52, n0 - 0.66, n0 - 0.60, 1.12, 1.20), 'truck', 'pallet truck handle')

doc.Views.Redraw()
print('grounded bed parts moved to %s: %d' % (REM, moved))
print('raised copies (+%.3f m): %d' % (H, copied))
print('castor / truck parts: %s' % made)
