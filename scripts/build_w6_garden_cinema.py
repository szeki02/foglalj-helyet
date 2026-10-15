# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 6 (garden cinema): garden furniture from milk crates and EUR pallets, set up
# as an open-air cinema / performance place in front of a patch of the west wall painted white. Re-runnable.
#
# Brief (user, 2026-10-14): "creation of garden furniture out of milk crates / EU pallets, stationed in front of a
# surface I highlighted (which will be painted white); the setup will serve as a garden cinema or a place for
# performances. The tables of the workshop space should be back in storage as well as the tools, and the newly made
# furniture positioned in front." Pallet bench reference: two pallets stacked flat as the seat, a third stood on its
# long edge behind as the backrest.
#
# Screen = the user's rectangle on ADDITIONS: west wall face n 13.57, s -7.23..-2.62, z 1.31..4.17 (4.61 x 2.86 m).
# Layout (s = metres from the NORTH wall towards the street, n = metres west of the pavilion facade; audience faces +n):
#   STAGE   n 11.2..13.57 kept clear in front of the screen (performances), a speaker on a crate stack each side.
#   Every crate seat has a slatted pallet-board backrest, raked back 10 deg like the pallet benches (user, 2026-10-14).
#   ROW 1   n ~11.0: three crate benches (3 crates on their side, pallet-board seat, cushion) + two crate chairs,
#           turned towards a point 3 m behind the screen so the row curves.
#   ROW 2   n ~9.75: three pallet benches after the reference (2 pallets + 1 upright backrest pallet, cushion), curved.
#   ROW 3   on a riser of 10 pallets (n 7.3..8.9): three crate benches, two crate side tables, and the projector on a
#           tower of 10 crates behind the middle bench (lens ~1.6 m, above the seated heads, throw 5.9 m).
# Packed away from this workshop on: both work tables, the sawhorses with their sheet and saw, the mitre box and the
# loose hand tools -> moved (not copied) to 09_Workshops::w2_workshop_space::Stored_from_w6::<leaf>, which the
# exporter and layer_states.py read as "visible from W2 until W6". In the store: table tops on edge by the shelving,
# trestles and sawhorses stacked, the sheet back in the rack, the tools in the lockable cabinet.
# Also renumbers the later stages' Rhino layers (fire circle w4 -> w5 ... north platform w7 -> w8).
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color
from Rhino.Render import RenderMaterial

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'w4_cinema'
STAGE = 'w6_garden_cinema'
ADD = '09_Workshops::' + STAGE
W2 = '09_Workshops::w2_workshop_space'
STORED = W2 + '::Stored_from_w6'

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)                    # local x = L - s, local y = n


def P(s, n, z=0.0):
    return PL.PointAt(L - s, n, z)


N_WALL = 13.57
SCREEN = (-7.23, -2.62, 1.31, 4.17)              # s0, s1, z0, z1
SC = (SCREEN[0] + SCREEN[1]) / 2                 # screen centre line, s -4.925
FOCUS = (SC, N_WALL + 3.0)                       # curved rows turn towards this point
CW, CH = 0.33, 0.28                              # milk crate 330 x 330 x 280, 12 mm walls
CT = 0.012
PAL_L, PAL_W, PAL_H = 1.2, 0.8, 0.144            # EUR pallet
BOARD = 0.022

ALL = Rhino.DocObjects.ObjectEnumeratorSettings()
ALL.HiddenObjects = True
ALL.LockedObjects = True
ALL.VisibleFilter = False

# ------------------------------------------------------------------ 0. renumber the later stages (idempotent)
RENAME = [('w7_north_platform', 'w8_north_platform'), ('w6_willow_garden', 'w7_willow_garden'),
          ('w5_shelter_table', 'w6_shelter_table'), ('w4_fire_circle', 'w7_fire_circle')]
renamed = []
for old, new in RENAME:
    for root in ('09_Workshops', '10_Removed'):
        i = doc.Layers.FindByFullPath(root + '::' + old, -1)
        if i >= 0 and doc.Layers.FindByFullPath(root + '::' + new, -1) < 0:
            lay = doc.Layers[i]
            lay.Name = new
            doc.Layers.Modify(lay, i, True)
            renamed.append(root + '::' + new)


def rmat(name, rgb=None, gloss=0.0):
    for rm in doc.RenderMaterials:
        if rm.Name == name:
            return rm
    if rgb is None:
        return None
    m = Rhino.DocObjects.Material()
    m.Name = name
    m.DiffuseColor = Color.FromArgb(*rgb)
    m.AmbientColor = Color.Black
    m.Reflectivity = 0.0
    m.ReflectionGlossiness = gloss
    m.Shine = gloss * Rhino.DocObjects.Material.MaxShine
    m.SpecularColor = Color.White if gloss > 0 else Color.Black
    rm = RenderMaterial.CreateBasicMaterial(m, doc)
    rm.Name = name
    doc.RenderMaterials.Add(rm)
    return rmat(name)


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
        m = mat if not isinstance(mat, str) else rmat(mat)
        if m is not None:
            doc.Layers[idx].RenderMaterial = m
    return idx


def group_for(name):
    try:
        gi = doc.Groups.Find(name)
    except Exception:
        gi = -1
    return gi if gi >= 0 else doc.Groups.Add(name)


if doc.Layers.FindByFullPath(ADD, -1) < 0:          # normally made by setup_workshop_layers.py (re-run it after)
    layer(ADD, Color.FromArgb(224, 122, 46))
    layer('10_Removed::' + STAGE, Color.FromArgb(190, 60, 60))

# ------------------------------------------------------------------ 1. clean previous run
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

# ------------------------------------------------------------------ 2. pack the workshop away (move, don't copy)
STORE_LEAVES = ('Work_Table_Tops', 'Work_Table_Trestles')
STORE_NAMES = {
    'Workshop_Benches_Stands': ('sawhorse', 'mitre box'),
    'Materials_Sheets': ('OSB sheet on the sawhorses',),
    'Tools_Hand_Steel': ('tool wall:', 'tool shelf:', 'panel saw', 'backsaw', 'clamp bar'),
    'Tools_Hand_Handles': ('tool wall:', 'panel saw', 'clamp jaw'),
}
stored = {}
for o in list(doc.Objects.GetObjectList(ALL)):
    src = doc.Layers[o.Attributes.LayerIndex]
    path = src.FullPath
    if not path.startswith(W2 + '::') or path.startswith(STORED):
        continue
    leaf = src.Name
    nm = o.Attributes.Name or ''
    if not (leaf in STORE_LEAVES or nm.startswith(STORE_NAMES.get(leaf, ()))):
        continue
    di = layer(STORED + '::' + leaf, src.Color, src.RenderMaterial)
    a = o.Attributes.Duplicate()
    a.SetUserString('orig_layer', path)
    a.SetUserString('stored_in', STAGE)
    a.LayerIndex = di
    doc.Objects.ModifyAttributes(o, a, True)
    stored[leaf] = stored.get(leaf, 0) + 1
# the two tables are packed at different times in the midway (B first, it stands on the cinema floor; A is the
# assembly table until the end): tag them, the exporter splits a layer by this 'piece' user text
tagged = 0
for o in list(doc.Objects.GetObjectList(ALL)):
    lay = doc.Layers[o.Attributes.LayerIndex]
    if not (lay.FullPath.startswith(STORED + '::Work_Table_')):
        continue
    s_c = L - o.Geometry.GetBoundingBox(PL).Center.X
    want = 'table A' if s_c < -10.0 else 'table B'
    if o.Attributes.GetUserString('piece') != want:
        a = o.Attributes.Duplicate()
        a.SetUserString('piece', want)
        doc.Objects.ModifyAttributes(o, a, True)
        tagged += 1
si = doc.Layers.FindByFullPath(STORED, -1)
if si >= 0:
    lay = doc.Layers[si]
    lay.Color = Color.FromArgb(150, 150, 150)
    doc.Layers.Modify(lay, si, True)

top_mat = doc.Layers[doc.Layers.FindByFullPath(STORED + '::Work_Table_Tops', -1)].RenderMaterial \
    if doc.Layers.FindByFullPath(STORED + '::Work_Table_Tops', -1) >= 0 else None

# ------------------------------------------------------------------ 3. layers
LY = {
    'plan':    layer(ADD + '::_Layout_Plan', Color.FromArgb(230, 180, 40)),
    'paint':   layer(ADD + '::Screen_Paint_White', Color.FromArgb(246, 246, 242),
                     rmat('AU6 Paint white screen', (246, 246, 242))),
    'pallet':  layer(ADD + '::Pallets', Color.FromArgb(196, 160, 112), 'AU6 Timber pallet pine'),
    'riser':   layer(ADD + '::Riser_Pallets', Color.FromArgb(196, 160, 112), 'AU6 Timber pallet pine'),   # laid first
    'board':   layer(ADD + '::Seat_Boards', Color.FromArgb(185, 148, 102), 'AU6 Timber pallet pine'),
    'red':     layer(ADD + '::Crates_Red', Color.FromArgb(196, 40, 40), rmat('AU6 Plastic crate red', (196, 40, 40), 0.2)),
    'blue':    layer(ADD + '::Crates_Blue', Color.FromArgb(38, 84, 160), rmat('AU6 Plastic crate blue', (38, 84, 160), 0.2)),
    'yellow':  layer(ADD + '::Crates_Yellow', Color.FromArgb(232, 184, 30), rmat('AU6 Plastic crate yellow', (232, 184, 30), 0.2)),
    'green':   layer(ADD + '::Crates_Green', Color.FromArgb(52, 132, 72), rmat('AU6 Plastic crate green', (52, 132, 72), 0.2)),
    'ochre':   layer(ADD + '::Cushions_Ochre', Color.FromArgb(204, 142, 52), rmat('AU6 Fabric ochre', (204, 142, 52))),
    'teal':    layer(ADD + '::Cushions_Teal', Color.FromArgb(40, 112, 120), rmat('AU6 Fabric teal', (40, 112, 120))),
    'av':      layer(ADD + '::Projector_Sound', Color.FromArgb(28, 28, 28), 'AU6 Plastic black'),
    'stab':    layer(ADD + '::Store_Packed_Tables', Color.FromArgb(200, 162, 108), top_mat or 'AU6 OSB board'),
    'stimber': layer(ADD + '::Store_Packed_Trestles', Color.FromArgb(185, 148, 102), 'AU6 Timber pallet pine'),
    'ssheet':  layer(ADD + '::Store_Packed_Sheet', Color.FromArgb(200, 162, 108), 'AU6 OSB board'),
}

# ------------------------------------------------------------------ 4. geometry helpers
pieces = {}                                      # (group name, layer key, object name) -> [brep]
order = []


def put(brep, key, name, group):
    if brep is None:
        print('FAILED: ' + name)
        return
    k = (group, key, name)
    if k not in pieces:
        pieces[k] = []
        order.append(k)
    pieces[k].append(brep)


class Frame(object):
    """piece frame: origin at (s, n, z), turned by phi (radians, from +n towards +s). Local (ds, dn, dz)."""
    def __init__(self, s, n, z=0.0, phi=0.0):
        self.s, self.n, self.z, self.phi = s, n, z, phi
        xf = rg.Transform.Rotation(phi, rg.Vector3d.ZAxis, rg.Point3d.Origin)
        ur, vr = rg.Vector3d(U), rg.Vector3d(V)
        ur.Transform(xf); vr.Transform(xf)
        self.ur, self.vr = ur, vr                # +ds = -ur, +dn = -vr
        self.pl = rg.Plane(P(s, n, z), ur, -vr)  # plane x = -ds, y = +dn, z up

    def box(self, s0, s1, n0, n1, z0, z1):
        return rg.Box(self.pl, rg.Interval(-max(s0, s1), -min(s0, s1)), rg.Interval(min(n0, n1), max(n0, n1)),
                      rg.Interval(min(z0, z1), max(z0, z1))).ToBrep()

    def pt(self, ds, dn, dz=0.0):
        return self.pl.PointAt(-ds, dn, dz)


def facing(s, n, target=FOCUS):
    return math.atan2(target[0] - s, target[1] - n)


def crate(fr, s0, n0, z0, open_face, key, name, group):
    """milk crate occupying [s0, s0+CW] x [n0, n0+dn] x [z0, z0+dz]; open_face '+z' (upright, open top),
    '-z' (upside down) or '+n' (on its side, opening towards +n = a cubby)"""
    if open_face == '+n':
        s1, n1, z1 = s0 + CW, n0 + CH, z0 + CW
    else:
        s1, n1, z1 = s0 + CW, n0 + CW, z0 + CH
    faces = {'-s': (s0, s0 + CT, n0, n1, z0, z1), '+s': (s1 - CT, s1, n0, n1, z0, z1),
             '-n': (s0 + CT, s1 - CT, n0, n0 + CT, z0, z1), '+n': (s0 + CT, s1 - CT, n1 - CT, n1, z0, z1),
             '-z': (s0 + CT, s1 - CT, n0 + CT, n1 - CT, z0, z0 + CT), '+z': (s0 + CT, s1 - CT, n0 + CT, n1 - CT, z1 - CT, z1)}
    for f, b in faces.items():
        if f == open_face:
            continue
        if f in ('-z', '+z'):                    # floor / lid sits inside the four walls
            put(fr.box(*b), key, name, group)
        else:
            put(fr.box(*b), key, name, group)
    # hand holds: a dark slot either side is too fine to read; a rim band gives the crate its profile instead
    rim = 0.03
    zr = z1 - rim if open_face != '-z' else z0
    for b in ((s0 - 0.01, s0, n0, n1, zr, zr + rim), (s1, s1 + 0.01, n0, n1, zr, zr + rim)):
        put(fr.box(*b), key, name, group)
    return z1


SEAT_CUT = 0.45                                  # seat pallets sawn off just past their second block row


def pallet(fp, key, name, group, depth=PAL_W):
    """EUR pallet in plane fp: x = length 1.2, y = width 0.8, z = height 0.144 (deck on top); depth < 0.8 = sawn off
    across the width at y = depth (blocks, bottom boards and deck boards beyond it are gone)"""
    def b(x0, x1, y0, y1, z0, z1):
        put(rg.Box(fp, rg.Interval(x0, x1), rg.Interval(y0, y1), rg.Interval(z0, z1)).ToBrep(), key, name, group)
    rows = [(y0, w) for y0, w in ((0.0, 0.10), (0.35, 0.10), (0.70, 0.10)) if y0 < depth]   # block rows
    for y0, w in rows:
        b(0, PAL_L, y0, y0 + w, 0, BOARD)                       # bottom boards
    for x0 in (0.0, 0.5275, 1.055):
        for y0, w in rows:
            b(x0, x0 + 0.145, y0, y0 + w, BOARD, BOARD + 0.078)  # blocks
        b(x0, x0 + 0.145, 0, min(PAL_W, depth), BOARD + 0.078, 2 * BOARD + 0.078)   # stringer boards
    zd = 2 * BOARD + 0.078
    w5 = (0.145, 0.10, 0.145, 0.10, 0.145)
    gap = (PAL_W - sum(w5)) / 4.0
    y = 0.0
    for w in w5:
        if y < depth:
            b(0, PAL_L, y, min(y + w, depth), zd, PAL_H)        # deck boards
        y += w + gap


def flat_pallet(fr, s0, n0, z0, key, name, group, depth=PAL_W):
    """pallet lying flat, 1.2 along s from s0, 0.8 (or depth) along n from n0"""
    fp = rg.Plane(fr.pt(s0 + PAL_L, n0, z0), fr.ur, -fr.vr)  # x runs towards -s from the +s corner
    pallet(fp, key, name, group, depth)


def seat_boards(fr, s0, s1, n0, n1, z0, key, name, group, count=3):
    w = (n1 - n0 - (count - 1) * 0.012) / count
    for i in range(count):
        a = n0 + i * (w + 0.012)
        put(fr.box(s0, s1, a, a + w, z0, z0 + BOARD), key, name, group)
    return z0 + BOARD


CRATE_COLS = ('red', 'blue', 'yellow', 'green')
_cc = [0]


def next_col():
    c = CRATE_COLS[_cc[0] % len(CRATE_COLS)]
    _cc[0] += 1
    return c


def slat_back(fr, n_back, z_seat, half, posts, label, g, lean=math.radians(10), height=0.46):
    """backrest from pallet boards: 70 mm uprights screwed to the back of the crates (n < n_back), carried up past the
    seat and raked back by `lean` above it, three 100 mm slats across their front face"""
    nb0, nb1 = n_back - BOARD, n_back
    for ps in posts:
        put(fr.box(ps - 0.035, ps + 0.035, nb0, nb1, 0.02, z_seat), 'board', label + ' back upright', g)
    ku, ks = (g, 'board', label + ' back upright, raked part'), (g, 'board', label + ' back slat')
    nu, ns = len(pieces.get(ku, [])), len(pieces.get(ks, []))
    for ps in posts:
        put(fr.box(ps - 0.035, ps + 0.035, nb0, nb1, z_seat, z_seat + height), 'board', ku[2], g)
    for dz in (0.10, 0.22, 0.34):
        put(fr.box(-half, half, nb1, nb1 + BOARD, z_seat + dz, z_seat + dz + 0.10), 'board', ks[2], g)
    rot = rg.Transform.Rotation(lean, fr.ur, fr.pt(0, nb0, z_seat))   # top leans back (towards -n)
    for b in pieces[ku][nu:] + pieces[ks][ns:]:
        b.Transform(rot)


def crate_bench(s, n, z, phi, cushion, label):
    """3 crates on their side (cubbies to the front), seat of 3 pallet boards 1.10 long overhanging 60 mm at the
    front, cushion, slatted backrest"""
    g = 'Cinema ' + label + ' (W6)'
    fr = Frame(s, n, z, phi)
    for i in range(3):
        crate(fr, -0.495 + i * CW, -CH / 2, 0.0, '+n', next_col(), label + ' crate', g)
    zt = seat_boards(fr, -0.55, 0.55, -CH / 2, CH / 2 + 0.06, CW, 'board', label + ' seat board', g)
    put(fr.box(-0.54, 0.54, -CH / 2 + 0.03, CH / 2 + 0.06, zt, zt + 0.06), cushion, label + ' cushion', g)
    slat_back(fr, -CH / 2, zt, 0.55, (-0.46, 0.0, 0.46), label, g)
    return g


def crate_chair(s, n, z, phi, cushion, label):
    """one crate upside down as the seat, cushion, slatted backrest"""
    g = 'Cinema ' + label + ' (W6)'
    fr = Frame(s, n, z, phi)
    zt = crate(fr, -CW / 2, -CW / 2, 0.0, '-z', next_col(), label + ' crate (upside down)', g)
    put(fr.box(-CW / 2 + 0.01, CW / 2 - 0.01, -CW / 2 + 0.03, CW / 2 - 0.01, zt, zt + 0.06), cushion, label + ' cushion', g)
    slat_back(fr, -CW / 2, zt, CW / 2 + 0.01, (-0.12, 0.12), label, g)
    return g


def crate_table(s, n, z, phi, label):
    g = 'Cinema ' + label + ' (W6)'
    fr = Frame(s, n, z, phi)
    zt = z0 = 0.0
    for k in range(2):
        zt = crate(fr, -CW / 2, -CW / 2, zt, '+z', next_col(), label + ' crate', g)
    seat_boards(fr, -0.21, 0.21, -0.21, 0.21, zt, 'board', label + ' top board', g, count=4)
    return g


def pallet_bench(s, n, phi, cushion, label, lean=math.radians(10)):
    """after the user's reference: two pallets stacked flat (seat), a third on its long edge behind (backrest)"""
    g = 'Cinema ' + label + ' (W6)'
    fr = Frame(s, n, 0.0, phi)
    # seat: the two pallets sawn off past their second block row (user, 2026-10-14), so the seat is 0.45 m deep
    # instead of 0.80; the cut edge is the front, the full edge stays against the backrest
    for k in range(2):
        flat_pallet(fr, -PAL_L / 2, -PAL_W / 2, k * PAL_H, 'pallet', label + ' seat pallet %d (cut)' % (k + 1), g,
                    depth=SEAT_CUT)
    zs = 2 * PAL_H
    put(fr.box(-0.59, 0.59, -0.39, -PAL_W / 2 + SEAT_CUT - 0.01, zs, zs + 0.08), cushion, label + ' seat cushion', g)
    # backrest: deck facing the seat; plane x along +s from the -s end, y up, z (pallet height) towards +n
    nb = -PAL_W / 2 - PAL_H                       # its back face
    fp = rg.Plane(fr.pt(-PAL_L / 2, nb, 0.0), -fr.ur, rg.Vector3d.ZAxis)
    before = len(order)
    key = (g, 'pallet', label + ' backrest pallet')
    n_before = len(pieces.get(key, []))
    pallet(fp, 'pallet', label + ' backrest pallet', g)
    rot = rg.Transform.Rotation(lean, fr.ur, fr.pt(0, nb, 0))   # top leans back (towards -n), about the back edge
    for b in pieces[key][n_before:]:
        b.Transform(rot)
    put(rg.Box(rg.Plane(fr.pt(-0.57, nb + PAL_H + 0.005, 0.30), -fr.ur, rg.Vector3d.ZAxis),
               rg.Interval(0, 1.14), rg.Interval(0, 0.45), rg.Interval(0, 0.06)).ToBrep(), cushion,
        label + ' back cushion', g)
    for b in pieces[(g, cushion, label + ' back cushion')]:
        b.Transform(rot)
    return g


# ------------------------------------------------------------------ 5. the white screen
s0, s1, z0, z1 = SCREEN
put(Frame(0, 0).box(s0, s1, N_WALL - 0.014, N_WALL - 0.002, z0, z1), 'paint', 'screen: wall painted white (2 coats)', 'Cinema screen (W6)')

# ------------------------------------------------------------------ 6. seating
ROW1_N, ROW2_N = 11.0, 9.75
RISER_N0, RISER_N1 = 7.3, 7.3 + 2 * PAL_W        # 7.3 .. 8.9
for i, ds in enumerate((-1.45, 0.0, 1.45)):
    s = SC + ds
    crate_bench(s, ROW1_N, 0.0, facing(s, ROW1_N), ('ochre', 'teal', 'ochre')[i], 'row 1 crate bench %d' % (i + 1))
for i, ds in enumerate((-2.45, 2.45)):
    s = SC + ds
    crate_chair(s, ROW1_N, 0.0, facing(s, ROW1_N), 'teal', 'row 1 crate chair %d' % (i + 1))
for i, ds in enumerate((-1.5, 0.0, 1.5)):
    s = SC + ds
    pallet_bench(s, ROW2_N, facing(s, ROW2_N), ('teal', 'ochre', 'teal')[i], 'row 2 pallet bench %d' % (i + 1))

g = 'Cinema riser (W6)'
fr = Frame(0, 0)
for row in range(2):
    for col in range(5):
        flat_pallet(fr, SC - 3.0 + col * PAL_L, RISER_N0 + row * PAL_W, 0.0, 'riser', 'riser pallet', g)
ROW3_N = 8.02
for i, ds in enumerate((-1.45, 0.0, 1.45)):
    crate_bench(SC + ds, ROW3_N, PAL_H, 0.0, ('teal', 'ochre', 'teal')[i], 'row 3 crate bench %d' % (i + 1))
for i, ds in enumerate((-2.55, 2.55)):
    crate_table(SC + ds, ROW3_N + 0.02, PAL_H, 0.0, 'row 3 crate side table %d' % (i + 1))

# projector tower: 2 x 5 crates zip-tied, on the riser behind the middle bench
g = 'Cinema projector tower (W6)'
fr = Frame(SC, RISER_N0 + 0.05 + CW / 2, PAL_H, 0.0)
zt = 0.0
for k in range(5):
    for j in range(2):
        crate(fr, -CW + j * CW, -CW / 2, zt, '+z', ('blue', 'red')[(j + k) % 2], 'projector tower crate', g)
    zt += CH
zt = seat_boards(fr, -0.36, 0.36, -0.18, 0.18, zt, 'board', 'projector tower top board', g, count=3)
put(fr.box(-0.15, 0.15, -0.12, 0.12, zt + 0.01, zt + 0.10), 'av', 'projector (borrowed), lens towards the screen', g)
put(fr.box(-0.12, -0.10, -0.12, -0.10, zt, zt + 0.01), 'av', 'projector foot', g)
put(fr.box(0.10, 0.12, -0.12, -0.10, zt, zt + 0.01), 'av', 'projector foot', g)
put(fr.box(-0.01, 0.01, 0.10, 0.12, zt, zt + 0.01), 'av', 'projector foot', g)
LENS = (SC, RISER_N0 + 0.05 + CW / 2 + 0.12, PAL_H + zt + 0.055)

# speakers beside the screen, each on 2 upright crates
for i, s in enumerate((SCREEN[0] - 0.45, SCREEN[1] + 0.45)):
    g = 'Cinema speaker %d (W6)' % (i + 1)
    fr = Frame(s, N_WALL - 0.45, 0.0, math.pi * 0)
    zt = 0.0
    for k in range(2):
        zt = crate(fr, -CW / 2, -CW / 2, zt, '+z', ('green', 'yellow')[k], 'speaker stand crate', g)
    put(fr.box(-0.13, 0.13, -0.11, 0.11, zt, zt + 0.42), 'av', 'speaker (borrowed)', g)

# ------------------------------------------------------------------ 7. the workshop, packed into the store
g = 'Packed workshop (W6)'                       # table A, trestles A, sawhorses, sheet: packed at the end
gB = 'Packed table B (W6)'                        # table B: packed first, it stands where the cinema goes
fr = Frame(0, 0)
for k, sa in enumerate((-10.87, -10.81)):        # the two 2.0 x 2.0 table tops, on edge beside the shelving
    put(fr.box(sa, sa + 0.05, 10.50, 12.50, 0.045, 2.045), 'stab', 'work table top on edge (stored)', (g, gB)[k])
for nb in (10.70, 12.20):
    put(fr.box(-10.92, -10.72, nb, nb + 0.07, 0.0, 0.045), 'stimber', 'batten under the stored table tops', gB)
# eight trestles nested in two rows (the far row is table B's), sawhorses by the sheet rack: simple A-frames
for row, n0 in enumerate((11.0, 11.85)):
    g = ('Packed workshop (W6)', gB)[row]
    for k in range(4):
        sa = -12.95 + k * 0.45
        put(fr.box(sa, sa + 0.12, n0, n0 + 0.68, 0.74, 0.80), 'stimber', 'trestle head (stored)', g)
        for dn in (0.04, 0.58):
            put(fr.box(sa - 0.10, sa - 0.04, n0 + dn, n0 + dn + 0.06, 0.0, 0.74), 'stimber', 'trestle leg (stored)', g)
            put(fr.box(sa + 0.16, sa + 0.22, n0 + dn, n0 + dn + 0.06, 0.0, 0.74), 'stimber', 'trestle leg (stored)', g)
g = 'Packed workshop (W6)'
for k, nb in enumerate((11.20, 11.62)):          # the two sawhorses, side by side by the sheet rack
    put(fr.box(-13.98, -13.03, nb, nb + 0.07, 0.70, 0.76), 'stimber', 'sawhorse beam (stored)', g)
    for sa in (-13.93, -13.13):
        put(fr.box(sa, sa + 0.05, nb - 0.12, nb - 0.07, 0.0, 0.70), 'stimber', 'sawhorse leg (stored)', g)
        put(fr.box(sa, sa + 0.05, nb + 0.14, nb + 0.19, 0.0, 0.70), 'stimber', 'sawhorse leg (stored)', g)
put(fr.box(-14.265, -14.247, 10.05, 12.55, 0.06, 1.31), 'ssheet', 'OSB sheet back in the rack', g)

# ------------------------------------------------------------------ 8. add, one object per piece / layer / name
made = {}
gids = {}
fails = []
for k in order:
    gname, key, name = k
    breps = pieces[k]
    merged = rg.Brep.MergeBreps(breps, min(TOL, 0.001)) if len(breps) > 1 else breps[0]
    if merged is None:
        fails.append('merge failed: %s / %s (%d breps)' % (key, name, len(breps)))
        continue
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY[key]
    a.Name = name
    a.SetUserString('build', TAG)
    if gname not in gids:
        gids[gname] = group_for(gname)
    a.AddToGroup(gids[gname])
    oid = doc.Objects.AddBrep(merged, a)
    if oid == System.Guid.Empty:
        fails.append('add failed: %s / %s (%d breps, valid %s)' % (key, name, len(breps), merged.IsValid))
    else:
        made[key] = made.get(key, 0) + 1
        doc.Objects.Find(oid).CreateMeshes(Rhino.Geometry.MeshType.Render, doc.GetMeshingParameters(doc.MeshingParameterStyle), False)

# ------------------------------------------------------------------ 9. layout plan (curves + dots, not exported)
def plan_attr(name):
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY['plan']
    a.Name = name
    a.SetUserString('build', TAG)
    return a


def rect(s0, s1, n0, n1, name, z=0.01):
    doc.Objects.AddCurve(rg.PolylineCurve([P(s0, n0, z), P(s1, n0, z), P(s1, n1, z), P(s0, n1, z), P(s0, n0, z)]), plan_attr(name))
    doc.Objects.AddTextDot(rg.TextDot(name, P((s0 + s1) / 2, (n0 + n1) / 2, 0.3)), plan_attr(name))


rect(SCREEN[0], SCREEN[1], 11.2, N_WALL, 'stage / performance strip (keep clear)')
lens = P(*LENS)
for sa, za in ((SCREEN[0], SCREEN[2]), (SCREEN[1], SCREEN[2]), (SCREEN[1], SCREEN[3]), (SCREEN[0], SCREEN[3])):
    doc.Objects.AddCurve(rg.LineCurve(lens, P(sa, N_WALL - 0.02, za)), plan_attr('projection beam'))
doc.Objects.AddTextDot(rg.TextDot('projector lens %.2f m, throw %.1f m' % (LENS[2], N_WALL - LENS[1]), lens), plan_attr('projector'))

doc.Views.Redraw()
report = ['renamed: %s' % (', '.join(renamed) or 'none'),
          'stored (moved to %s): %s' % (STORED, ', '.join('%s %d' % kv for kv in sorted(stored.items())) or 'already'),
          'table pieces tagged: %d' % tagged,
          'objects: %s' % ', '.join('%s %d' % kv for kv in sorted(made.items())),
          'groups: %d, crates: %d, lens at %.2f m' % (len(gids), _cc[0] + 10 + 4, LENS[2])] + fails
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_w4_log.txt', 'w') as f:   # the bridge may time out first
    f.write('\n'.join(report))
