# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - community-garden raised beds along the west wall, built from EUR pallets.
# Re-runnable: deletes everything it created before (user text 'pallets_build'), including on hidden layers.
#
# Revision 2026-10-14 (user reference photos 1-3, see photos/ref_2026-10-14_*):
#   * 4 identical units (user: "make all 4 the same, like the large one"), each on its own pallet base so it can
#     later be lifted with a pallet jack: 2 pallets side by side (1.6 along the wall x 1.2), stacked 2 high,
#     a one-board box on top with corner posts sticking up, bamboo canes, lilies and leafy plants.
#     (No liner: removed at the user's request.) Each unit stands a little further off the wall than the one before
#     (photo 3: diagonal line).
#   * positions: fronts s 9.0 / 11.3 / 15.4 from the photo-5 calibration; the middle unit (13.3) and the far end
#     (~15.9, terracotta pot) checked against the ground plane of reference photo 3. The former 4th bed at s 18.2
#     (a guess) does not exist.
#   * props: white tub + galvanised watering can and a black container (photo 1), terracotta pot (photos 2, 3).
#
# EUR pallet (EN 13698-1) 1200 x 800 x 144 mm:
#   3 bottom boards (1200 long) / 9 blocks (145 x 100 x 78) / 3 cross boards (800 long) / 5 deck boards (1200 long)
import math
import random
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'pallets_build'

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
XF = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, rg.Plane(C_WORLD, U, -V))


def P(s, n, z=0.0):
    return rg.Point3d(L - s, n, z)


WALL_N = 13.58
UNITS = [dict(id='A', s0=9.0,  gap=0.00, props=''),
         dict(id='B', s0=11.3, gap=0.08, props=''),
         dict(id='C', s0=13.3, gap=0.18, props='tub'),
         dict(id='D', s0=15.4, gap=0.30, props='pot')]
BOARD_T = 0.022
POST = 0.06                                   # corner posts (pallet-board offcuts / 60x60)


# ------------------------------------------------------------------ layers + materials
def rmat(name):
    for rm in doc.RenderMaterials:
        if rm.Name == name:
            return rm
    return None


def layer(path, col, mat=None):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        parts = path.split('::')
        parent = System.Guid.Empty
        if len(parts) > 1:
            parent = doc.Layers[layer('::'.join(parts[:-1]), Color.FromArgb(165, 125, 80))].Id
        Lr = Rhino.DocObjects.Layer()
        Lr.Name = parts[-1]
        Lr.Color = col
        Lr.ParentLayerId = parent
        idx = doc.Layers.Add(Lr)
    if mat is not None and rmat(mat) is not None:
        doc.Layers[idx].RenderMaterial = rmat(mat)
    return idx


G = '02_Courtyard_Ground::Pallet_Planters::'
LY = {
    # everything is weathered grey-brown in the reference photos
    'deck': layer(G + 'Pallet_Boards', Color.FromArgb(178, 140, 95), 'AU6 Timber weathered collar'),
    'block': layer(G + 'Pallet_Blocks', Color.FromArgb(150, 115, 75), 'AU6 Timber weathered collar'),
    'collar': layer(G + 'Pallet_Collars', Color.FromArgb(125, 95, 60), 'AU6 Timber weathered collar'),  # boxes + posts
    'soil': layer(G + 'Soil', Color.FromArgb(55, 42, 32)),
    'tub': layer(G + 'Tubs_Pots', Color.FromArgb(30, 30, 30)),
    'white': layer(G + 'Tub_White', Color.FromArgb(240, 240, 236), 'AU6 Paint white patch'),
    'zinc': layer(G + 'Watering_Can', Color.FromArgb(178, 182, 184), 'AU6 Galvanised steel'),
    'terra': layer(G + 'Pot_Terracotta', Color.FromArgb(165, 75, 55), 'AU6 Brick red'),
    'cane': layer(G + 'Bamboo_Canes', Color.FromArgb(200, 175, 120), 'AU6 Timber pallet pine'),
    'plants': layer('03_Vegetation::Planter_Plants', Color.FromArgb(70, 140, 70)),
}

# ------------------------------------------------------------------ cleanup (own objects, hidden ones included)
s_ = Rhino.DocObjects.ObjectEnumeratorSettings()
s_.HiddenObjects = True
s_.LockedObjects = True
s_.VisibleFilter = False
n_old = 0
for o in list(doc.Objects.GetObjectList(s_)):
    a = o.Attributes
    nm = a.Name or ''
    if a.GetUserString(TAG) or (a.GetUserString('garden_build') and (nm.startswith('pallet-collar raised bed') or nm == 'planter plants')):
        doc.Objects.Delete(o, True, True)
        n_old += 1

def group_for(name):
    """one group per bed (user: group the pallets individually); reuses an existing group of that name"""
    try:
        gi = doc.Groups.Find(name)
    except Exception:
        gi = -1
    return gi if gi >= 0 else doc.Groups.Add(name)


try:                                                 # the old single group for all beds is no longer used
    old = doc.Groups.Find('Pallet_Planters_Alfoldi6')
    if old >= 0 and doc.Groups.GroupObjectCount(old) == 0:
        doc.Groups.Delete(old)
except Exception:
    pass
count = {}


def put(geo, key, name, unit):
    geo.Transform(XF)
    at = Rhino.DocObjects.ObjectAttributes()
    at.LayerIndex = LY[key]
    at.WireDensity = -1
    at.Name = name
    at.SetUserString(TAG, '2026-10-14')
    at.SetUserString('planter_unit', unit)          # which mobile unit this part belongs to (for the wheels stage)
    at.SetUserString('source', 'user reference photos 2026-10-14 + photo-5 calibration')
    at.AddToGroup(group_for('Pallet bed %s' % unit))
    if isinstance(geo, rg.Brep):
        doc.Objects.AddBrep(geo, at)
    else:
        doc.Objects.Add(geo, at)
    count[key] = count.get(key, 0) + 1


def box(s0, s1, n0, n1, z0, z1, key, name, unit):
    b = rg.BoundingBox(P(max(s0, s1), min(n0, n1), min(z0, z1)), P(min(s0, s1), max(n0, n1), max(z0, z1)))
    put(rg.Box(b).ToBrep(), key, name, unit)


def pallet(s0, n0, z0, name, unit, orient='long'):
    """EUR pallet with base at z0. orient 'long': 1.20 along s / 0.80 along n; 'cross': 0.80 along s / 1.20 along n.
    Deck boards always run along the 1.20 side. Returns the top of the deck (z0 + 0.144)."""
    t = BOARD_T
    LEN, WID = 1.2, 0.8

    def B(a0, a1, b0, b1, z_0, z_1, key, nm):      # a = along the 1.2 side, b = along the 0.8 side
        if orient == 'long':
            box(s0 + a0, s0 + a1, n0 + b0, n0 + b1, z_0, z_1, key, nm, unit)
        else:
            box(s0 + b0, s0 + b1, n0 + a0, n0 + a1, z_0, z_1, key, nm, unit)

    rows = ((0.0, 0.10), (WID / 2 - 0.0725, 0.145), (WID - 0.10, 0.10))
    for b0, w in rows:
        B(0.0, LEN, b0, b0 + w, z0, z0 + t, 'deck', name + ' bottom board')
    for a0 in (0.0, LEN / 2 - 0.0725, LEN - 0.145):
        for b0, w in rows:
            B(a0, a0 + 0.145, b0, b0 + w, z0 + t, z0 + t + 0.078, 'block', name + ' block')
    zc = z0 + t + 0.078
    for a0 in (0.0, LEN / 2 - 0.0725, LEN - 0.145):
        B(a0, a0 + 0.145, 0.0, WID, zc, zc + t, 'deck', name + ' cross board')
    zd = zc + t
    widths = (0.145, 0.10, 0.145, 0.10, 0.145)
    gap = (WID - sum(widths)) / 4.0
    b0 = 0.0
    for w in widths:
        B(0.0, LEN, b0, b0 + w, zd, zd + t, 'deck', name + ' deck board')
        b0 += w + gap
    return zd + t


def bed_box(s0, s1, n0, n1, z0, h, name, unit, post_from=None, stub=0.08):
    """open-topped box of single pallet boards on edge, with corner posts that stick up above the rim.
    post_from: lower end of the corner posts (legs) if the box is raised; defaults to the box bottom."""
    t = BOARD_T
    box(s0, s1, n0, n0 + t, z0, z0 + h, 'collar', name + ' side board', unit)
    box(s0, s1, n1 - t, n1, z0, z0 + h, 'collar', name + ' side board', unit)
    box(s0, s0 + t, n0 + t, n1 - t, z0, z0 + h, 'collar', name + ' end board', unit)
    box(s1 - t, s1, n0 + t, n1 - t, z0, z0 + h, 'collar', name + ' end board', unit)
    zb = z0 if post_from is None else post_from
    for sc_ in (s0 + t, s1 - t - POST):
        for nc in (n0 + t, n1 - t - POST):
            box(sc_, sc_ + POST, nc, nc + POST, zb, z0 + h + stub, 'collar', name + ' corner post', unit)
    return z0 + h


def bush(s, n, zbase, r, h, name, unit):
    """foliage mass of height h (m) and plan radius r standing on the soil at zbase (slightly sunk into it)"""
    sph = rg.Sphere(rg.Point3d(0, 0, 0), 1.0).ToBrep()
    sph.Transform(rg.Transform.Scale(rg.Plane.WorldXY, r, r * 0.8, h / 2.0))
    sph.Transform(rg.Transform.Translation(rg.Vector3d(P(s, n, zbase + 0.45 * h))))
    put(sph, 'plants', name, unit)


def cane(s, n, z0, h, lean, unit):
    top = P(s + lean[0], n + lean[1], z0 + h)
    base = P(s, n, z0)
    c = rg.Cylinder(rg.Circle(rg.Plane(base, top - base), 0.006), (top - base).Length)
    put(c.ToBrep(True, True), 'cane', 'bamboo cane', unit)


def cyl(s, n, z0, r, h, key, name, unit, r_top=None):
    if r_top is None:
        put(rg.Cylinder(rg.Circle(rg.Plane(P(s, n, z0), rg.Vector3d.ZAxis), r), h).ToBrep(True, True), key, name, unit)
    else:                                            # tapered pot: loft between two circles
        c0 = rg.ArcCurve(rg.Circle(rg.Plane(P(s, n, z0), rg.Vector3d.ZAxis), r))
        c1 = rg.ArcCurve(rg.Circle(rg.Plane(P(s, n, z0 + h), rg.Vector3d.ZAxis), r_top))
        lofts = rg.Brep.CreateFromLoft([c0, c1], rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Straight, False)
        if lofts:
            put(lofts[0].CapPlanarHoles(TOL) or lofts[0], key, name, unit)


random.seed(1014)

# ------------------------------------------------------------------ 4 identical beds
for un in UNITS:
    u = un['id']
    name = 'bed %s' % u
    s0, n1 = un['s0'], WALL_N - un['gap']                    # n1: back edge (wall side)
    n0 = n1 - 1.2
    z = 0.0
    for layer_k in range(2):                                # two layers of pallets, 2 side by side ('cross')
        for k in range(2):
            zt = pallet(s0 + k * 0.8, n0, z, '%s pallet %d.%d' % (name, layer_k + 1, k + 1), u, 'cross')
        z = zt
    # the box sits a little back from the front edge and the north end, so the bottom pallets show (photo 2)
    bs0, bs1, bn0, bn1 = s0 + 0.10, s0 + 1.6, n0 + 0.10, n1
    rim = bed_box(bs0, bs1, bn0, bn1, z, 0.18, name, u, stub=0.10)
    soil = rim - 0.04
    box(bs0 + 0.03, bs1 - 0.03, bn0 + 0.03, bn1 - 0.03, z, soil, 'soil', name + ' soil', u)
    for j in range(7):                                      # bamboo canes, 1.1-1.6 m
        cane(bs0 + 0.15 + j * 0.2 + random.uniform(-0.05, 0.05), bn0 + random.uniform(0.25, 0.9), soil,
             random.uniform(1.1, 1.6), (random.uniform(-0.08, 0.08), random.uniform(-0.05, 0.08)), u)
    n_pl = 5 if not un['props'] else 3                      # fewer plants where props take up the bed
    for j in range(n_pl):                                   # lilies / leafy shrubs, 0.5-0.9 m
        h = random.uniform(0.5, 0.9)
        bush(bs0 + 0.2 + j * (1.2 / n_pl) * (5.0 / 4.0 if n_pl == 3 else 1.0) * 0.9 + random.uniform(-0.05, 0.05),
             bn0 + random.uniform(0.45, 0.9), soil, random.uniform(0.16, 0.26), h, name + ' plants', u)
    # props on the front half of the bed (photos 1-3)
    if un['props'] == 'tub':                                # white tub with a galvanised watering can in it
        box(bs1 - 0.75, bs1 - 0.15, bn0 + 0.08, bn0 + 0.48, soil, soil + 0.16, 'white', 'white plastic tub', u)
        cyl(bs1 - 0.45, bn0 + 0.28, soil + 0.02, 0.10, 0.26, 'zinc', 'galvanised watering can', u)
    elif un['props'] == 'pot':                              # terracotta trough + black plastic container
        box(bs1 - 0.62, bs1 - 0.15, bn0 + 0.08, bn0 + 0.36, soil, soil + 0.14, 'terra', 'terracotta trough', u)
        cyl(bs0 + 0.30, bn0 + 0.28, soil, 0.15, 0.30, 'tub', 'black plastic container', u)

doc.Views.Redraw()
print('removed %d previous planter objects' % n_old)
for k in sorted(count):
    print('%s: %d' % (k, count[k]))
