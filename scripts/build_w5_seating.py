# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 5 (mobile garden): seating nooks between the beds along the west wall.
# Works on the beds AS ARRANGED IN RHINO (moved / copied by hand), found by their groups. Re-runnable.
#
# Brief (user, 2026-10-14): in the two highlighted spaces between the wall-row beds, attach bench portions to the
# beds' sides (same EUR-pallet logic) and put a detached table in the middle. The highlighted spaces were 1.32 m
# wide; the user chose to roll the beds apart so each nook is NOOK = 2.0 m:
#     bench 0.40 | knees 0.30 | table 0.60 | knees 0.30 | bench 0.40
#
# Bench (attached): two stacked half-width EUR pallets (a pallet ripped lengthwise: 1.2 along the bed end x 0.4),
#   on 4 low-profile swivel castors like the beds, 60 mm seat cushion (seat ~0.44 m), bolted to the bed end with
#   galvanised tie plates on the yard face. It joins the bed's group, so bed + bench roll as one unit.
# Table (detached): 1.2 x 0.6 top of pallet deck boards on doubled cross boards, four legs of 7 stacked pallet
#   blocks, a stretcher each side, 4 braked swivel castors (top ~0.71 m). Its own group.
#
# Frame: s = metres along the pavilion's west facade from its NORTH end (south +), n = metres west of it.
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

doc = sc.doc
TAG = 'w3_seating'
BED_TAG = 'w3_mobile'
ADD = '09_Workshops::w5_mobile_garden::Seating'
NOOK = 2.0
BENCH_D = 0.40
TABLE_W, TABLE_L = 0.60, 1.20
H = 0.095                                        # castor build height (as under the beds)
WALL_ROW_N = 13.2                                # beds whose back edge is beyond this stand against the west wall

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)                    # local x = L - s, local y = n


def P(s, n, z=0.0):
    return PL.PointAt(L - s, n, z)


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
    if mat is not None and rmat(mat) is not None:
        doc.Layers[idx].RenderMaterial = rmat(mat)
    return idx


def group_for(name):
    try:
        gi = doc.Groups.Find(name)
    except Exception:
        gi = -1
    return gi if gi >= 0 else doc.Groups.Add(name)


LY = {
    'wood': layer(ADD + '::Bench_Table_Pallets', Color.FromArgb(125, 95, 60), 'AU6 Timber weathered collar'),
    'cushion': layer(ADD + '::Seat_Cushions', Color.FromArgb(35, 35, 35), 'AU6 Fabric black'),
    'plate': layer(ADD + '::Tie_Plates', Color.FromArgb(178, 182, 184), 'AU6 Galvanised steel'),
    'steel': layer('09_Workshops::w5_mobile_garden::Castors::Castor_Steel', Color.FromArgb(178, 182, 184), 'AU6 Galvanised steel'),
    'wheel': layer('09_Workshops::w5_mobile_garden::Castors::Castor_Wheels', Color.FromArgb(28, 28, 28), 'AU6 Plastic black'),
    'brake': layer('09_Workshops::w5_mobile_garden::Castors::Brake_Levers', Color.FromArgb(190, 30, 40), 'AU6 Sign red'),
}

# ------------------------------------------------------------------ 0. clean previous seating
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

# ------------------------------------------------------------------ 1. find the beds (one group per bed)
beds = {}                                        # group index -> dict(ids, s0, s1, n0, n1, unit)
for o in doc.Objects.GetObjectList(ALL):
    a = o.Attributes
    if a.GetUserString('build') != BED_TAG or not a.GetUserString('planter_unit'):
        continue
    gl = a.GetGroupList()
    if not gl:
        continue
    g = gl[0]
    b = beds.setdefault(g, dict(ids=[], s0=1e9, s1=-1e9, n0=1e9, n1=-1e9, unit=a.GetUserString('planter_unit')))
    b['ids'].append(o.Id)
    if 'pallet' in (a.Name or ''):               # the pallet stack defines the bed footprint
        bb = o.Geometry.GetBoundingBox(PL)
        b['s0'] = min(b['s0'], L - bb.Max.X); b['s1'] = max(b['s1'], L - bb.Min.X)
        b['n0'] = min(b['n0'], bb.Min.Y); b['n1'] = max(b['n1'], bb.Max.Y)
row = sorted([b for b in beds.values() if b['n1'] > WALL_ROW_N and b['s1'] > b['s0']], key=lambda b: b['s0'])
print('beds found: %d, wall row: %s' % (len(beds), ', '.join('%s s %.2f-%.2f' % (b['unit'], b['s0'], b['s1']) for b in row)))
if len(row) < 3:
    raise Exception('expected 3 beds along the west wall, found %d' % len(row))
row = row[:3]

# ------------------------------------------------------------------ 2. roll the beds apart: nooks of NOOK metres
moves = []
for i in range(1, len(row)):
    want = row[i - 1]['s1'] + NOOK
    ds = want - row[i]['s0']
    if abs(ds) > 0.005:
        xf = rg.Transform.Translation(-U * ds)   # +s is the -U direction
        for gid in row[i]['ids']:
            doc.Objects.Transform(gid, xf, True)
        row[i]['s0'] += ds; row[i]['s1'] += ds
        moves.append('%s %+.3f m' % (row[i]['unit'], ds))
for i in range(1, len(row)):                     # beds are moved in order, so each nook is now exactly NOOK wide
    if row[i]['s0'] < row[i - 1]['s1'] + NOOK - 0.005:
        raise Exception('nook %d is narrower than %.2f m' % (i, NOOK))

# ------------------------------------------------------------------ 3. geometry helpers
made = {}


def add(brep, key, name, group):
    if brep is None:
        print('FAILED: ' + name)
        return
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY[key]
    a.Name = name
    a.SetUserString('build', TAG)
    a.AddToGroup(group)
    if doc.Objects.AddBrep(brep, a) != System.Guid.Empty:
        made[key] = made.get(key, 0) + 1


def box(s0, s1, n0, n1, z0, z1):
    return rg.Box(PL, rg.Interval(L - max(s0, s1), L - min(s0, s1)), rg.Interval(min(n0, n1), max(n0, n1)),
                  rg.Interval(min(z0, z1), max(z0, z1))).ToBrep()


def cyl_s(s, n, z, r, w):
    base = P(s - w / 2, n, z)
    axis = P(s + w / 2, n, z) - base
    return rg.Cylinder(rg.Circle(rg.Plane(base, axis), r), axis.Length).ToBrep(True, True)


def cyl_z(s, n, z0, r, h):
    return rg.Cylinder(rg.Circle(rg.Plane(P(s, n, z0), rg.Vector3d.ZAxis), r), h).ToBrep(True, True)


WR, WW = 0.0375, 0.032                           # same low-profile castor as build_w5_mobile_garden.py


def castor(s, n, brake, group, name):
    add(box(s - 0.05, s + 0.05, n - 0.0425, n + 0.0425, H - 0.005, H), 'steel', name + ' top plate', group)
    add(cyl_z(s, n, H - 0.015, 0.038, 0.010), 'steel', name + ' swivel race', group)
    wn = n + 0.02
    for side in (-1, 1):
        add(box(s + side * (WW / 2 + 0.002), s + side * (WW / 2 + 0.006), wn - 0.032, wn + 0.032, WR - 0.012, H - 0.015),
            'steel', name + ' fork', group)
    add(cyl_s(s, wn, WR, 0.007, WW + 0.014), 'steel', name + ' axle', group)
    add(cyl_s(s, wn, WR, WR, WW), 'wheel', name + ' wheel (polyurethane)', group)
    if brake:
        add(box(s - 0.018, s + 0.018, wn - 0.075, wn - 0.03, WR + 0.012, WR + 0.024), 'brake', name + ' foot brake', group)


def half_pallet(sa, n0, z0, name, group):
    """EUR pallet ripped lengthwise: 0.4 along s x 1.2 along n, 144 mm high; deck boards run along n"""
    t = 0.022
    rows = ((0.0, 0.10), (0.30, 0.10))                       # s offsets / widths of the two block rows
    for r0, w in rows:
        add(box(sa + r0, sa + r0 + w, n0, n0 + 1.2, z0, z0 + t), 'wood', name + ' bottom board', group)
    for a0 in (0.0, 0.5275, 1.055):
        for r0, w in rows:
            add(box(sa + r0, sa + r0 + w, n0 + a0, n0 + a0 + 0.145, z0 + t, z0 + t + 0.078), 'wood', name + ' block', group)
        add(box(sa, sa + 0.4, n0 + a0, n0 + a0 + 0.145, z0 + t + 0.078, z0 + 2 * t + 0.078), 'wood', name + ' cross board', group)
    zd = z0 + 2 * t + 0.078
    sb = sa
    for w in (0.145, 0.10, 0.145):
        add(box(sb, sb + w, n0, n0 + 1.2, zd, zd + t), 'wood', name + ' deck board', group)
        sb += w + 0.005
    return zd + t


def bench(sa, bed, side, nook_no):
    """bench against bed's end; sa = its north edge along s; joins the bed's group"""
    g = bed['gid']
    name = 'nook %d bench (bed %s, %s end)' % (nook_no, bed['unit'], side)
    n0, n1 = bed['n0'], bed['n0'] + 1.2
    z = H
    for k in range(2):
        z = half_pallet(sa, n0, z, name + ' half pallet %d' % (k + 1), g)
    add(box(sa + 0.01, sa + 0.39, n0 + 0.02, n1 - 0.02, z, z + 0.06), 'cushion', name + ' seat cushion', g)
    for cs in (sa + 0.05, sa + 0.35):
        for cn in (n0 + 0.0725, n1 - 0.0725):
            castor(cs, cn, False, g, name + ' castor')
    joint = sa + 0.4 if side == 'north' else sa                # the face that touches the bed
    for z0 in (H + 0.03, H + 0.174):                          # tie plates, one per pallet layer, yard face
        add(box(joint - 0.15, joint + 0.15, n0 - 0.006, n0, z0, z0 + 0.08), 'plate', name + ' tie plate', g)
    return z + 0.06


def table(sm, n0, nook_no):
    g = group_for('Nook %d table (W5)' % nook_no)
    name = 'nook %d table' % nook_no
    s0, s1, n1 = sm - TABLE_W / 2, sm + TABLE_W / 2, n0 + TABLE_L
    legs = [(ls, ln) for ls in (s0 + 0.03, s1 - 0.13) for ln in (n0 + 0.03, n1 - 0.175)]
    for ls, ln in legs:
        for k in range(7):                                   # leg: 7 stacked pallet blocks (100 x 145 x 78)
            add(box(ls, ls + 0.10, ln, ln + 0.145, H + k * 0.078, H + (k + 1) * 0.078), 'wood', name + ' leg block', g)
        castor(ls + 0.05, ln + 0.0725, True, g, name + ' castor')
    zt = H + 7 * 0.078
    for ln in (n0 + 0.03, n1 - 0.175):                      # doubled cross boards over each pair of legs
        for k in range(2):
            add(box(s0, s1, ln, ln + 0.145, zt + k * 0.022, zt + (k + 1) * 0.022), 'wood', name + ' cross board', g)
    for ls in (s0 + 0.03, s1 - 0.13):                       # stretchers along n between the legs
        add(box(ls, ls + 0.10, n0 + 0.175, n1 - 0.175, H + 0.17, H + 0.192), 'wood', name + ' stretcher', g)
    zt += 0.044
    w, gap = 0.145, (TABLE_W - 4 * 0.145) / 3.0
    for k in range(4):                                       # top: 4 deck boards along n
        add(box(s0 + k * (w + gap), s0 + k * (w + gap) + w, n0, n1, zt, zt + 0.022), 'wood', name + ' top board', g)
    return zt + 0.022


# ------------------------------------------------------------------ 4. benches + tables in each nook
for gid, b in beds.items():
    b['gid'] = gid
heights = []
for i in range(1, len(row)):
    left, right = row[i - 1], row[i]
    seat = bench(left['s1'], left, 'south', i)                 # on the south end of the northern bed
    bench(right['s0'] - BENCH_D, right, 'north', i)            # on the north end of the southern bed
    sm = 0.5 * (left['s1'] + right['s0'])
    top = table(sm, 0.5 * (left['n0'] + right['n0']), i)
    heights.append('nook %d: s %.2f-%.2f, seat %.2f m, table %.2f m' % (i, left['s1'], right['s0'], seat, top))

doc.Views.Redraw()
print('beds moved: %s' % (', '.join(moves) or 'none'))
print('\n'.join(heights))
print('parts: %s' % made)
