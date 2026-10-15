# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 2 (workshop space): fit out the cleared lean-to in the NW corner as a shared
# workshop for residents and coordinators, with a lockable tool + material store. Re-runnable.
#
# Brief (user, 2026-10-14): area highlighted on ADDITIONS (s -14.38..-8.85, n 4.60..13.57); large work tables
# modelled by the user; "the closed off section will be a storage unit for tools, materials etc." = the part of the
# lean-to closed by the two corrugated screens (n > 9.15).
# Revision (user): LOW BUDGET - fewer tools, hand tools instead of power tools; at least one of the user's tables
# under the roof (table A was moved there: 2.0 x 2.0 at s -13.19..-11.19, n 5.88..7.88).
# See docs/w2_workshop_tools.md for the tool list.
#
# Layout (s = metres from the NORTH wall towards the street, n = metres west of the pavilion facade):
#   STORE   s -14.38..-10.0, n 9.15..13.57 : timber wall brackets on the west wall, sheet rack on the north wall,
#           one steel shelving unit, lockable tool cabinet; 1.2 m double door in the screen.
#   WORK    s -14.38..-10.0, n 4.60..9.15 (under the lean-to roof): the user's table A in the middle (~1.2 m clear
#           on three sides, 0.8 m to the open front), tool wall (pegboard, hand tools, shelf) on the store screen,
#           clamp rail on the north wall, mitre box on the table, two LED battens,
#           safety point (first aid kit with eye wash, extinguisher, PPE, sign-out sheet) on the front corner post.
#   CUTTING s -10.0..-8.85 (open, in front of the posts): two sawhorses with a sheet and a panel saw;
#           two bins (offcuts / general) in front of the store.
#   TABLE B s -8.3..-5.7, n 8.3..11.0 (open yard south of the lean-to): the user's second table (not built here).
#   Both tables: 09_Workshops::w2_workshop_space::Work_Table_Tops / ::Work_Table_Trestles.
#   The park bench that stood in the work area is relocated (moved to 10_Removed); the old corrugated screen at
#   n 9.15 is replaced by one with the store door.
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'w2_workshop'
STAGE = 'w2_workshop_space'
ADD = '09_Workshops::' + STAGE
REM = '10_Removed::' + STAGE

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)                    # local x = L - s, local y = n


def P(s, n, z=0.0):
    return PL.PointAt(L - s, n, z)


S_N, N_W = -14.38, 13.57                         # north wall face, west wall face
S_POST, N_SCREEN, N_EAST = -10.0, 9.15, 4.60     # lean-to front post line, store screen, east edge of the area
S_OUT = -8.85                                    # south edge of the highlighted area
TABLE_A = (-13.19, -11.19, 5.88, 7.88)           # user's table moved under the roof
TABLE_B = (-8.40, -5.60, 8.25, 11.05)            # user's table in the yard (rotated; plan box around it)
TABLE_Z = 0.85                                   # top of the user's tables


def roof_z(s):                                   # underside of the lean-to roof (build_courtyard.py: 3.05, fall 0.13/m)
    return 3.05 - 0.13 * (s - S_N) - 0.03


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


# ------------------------------------------------------------------ 0. clean previous run
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

# ------------------------------------------------------------------ 1. relocate the park bench + replace the screen
RELOCATE = ('park bench (by ramp)',)
moved = 0
for o in list(doc.Objects.GetObjectList(ALL)):
    a = o.Attributes
    src = doc.Layers[a.LayerIndex]
    if src.FullPath.startswith('10_Removed::'):
        continue
    nm = a.Name or ''
    is_bench = nm.startswith(RELOCATE)
    is_screen = nm == 'corrugated back screen' and abs(o.Geometry.GetBoundingBox(PL).Center.Y - N_SCREEN) < 0.2
    if not (is_bench or is_screen):
        continue
    di = layer(REM + '::' + src.Name, Color.FromArgb(190, 60, 60), src.RenderMaterial)
    a = a.Duplicate()
    a.SetUserString('orig_layer', src.FullPath)
    a.SetUserString('removed_in', STAGE)
    a.LayerIndex = di
    doc.Objects.ModifyAttributes(o, a, True)
    moved += 1

# ------------------------------------------------------------------ 2. layers
LY = {
    'zone':   layer(ADD + '::_Layout_Plan', Color.FromArgb(230, 180, 40)),            # curves + dots, not exported
    'screen': layer(ADD + '::Store_Screen_Door', Color.FromArgb(182, 188, 192), 'AU6 Zinc / profiled sheet'),
    'door':   layer(ADD + '::Store_Door_Leaves', Color.FromArgb(40, 110, 85), 'AU6 Steel painted green'),
    'rack':   layer(ADD + '::Store_Racks_Shelving', Color.FromArgb(178, 182, 184), 'AU6 Galvanised steel'),
    'cab':    layer(ADD + '::Store_Cabinets', Color.FromArgb(70, 105, 125), 'AU6 Steel painted blue-grey'),
    'timber': layer(ADD + '::Materials_Timber', Color.FromArgb(185, 148, 102), 'AU6 Timber pallet pine'),
    'sheet':  layer(ADD + '::Materials_Sheets', Color.FromArgb(200, 162, 108), 'AU6 OSB board'),
    'boxes':  layer(ADD + '::Materials_Boxes', Color.FromArgb(28, 28, 28), 'AU6 Plastic black'),
    'bench':  layer(ADD + '::Workshop_Benches_Stands', Color.FromArgb(185, 148, 102), 'AU6 Timber pallet pine'),
    'board':  layer(ADD + '::Tool_Wall_Pegboard', Color.FromArgb(200, 162, 108), 'AU6 OSB board'),
    'steel':  layer(ADD + '::Tools_Hand_Steel', Color.FromArgb(48, 50, 52), 'AU6 Steel painted dark'),
    'handle': layer(ADD + '::Tools_Hand_Handles', Color.FromArgb(215, 120, 40), 'AU6 Steel painted orange'),
    'red':    layer(ADD + '::Safety_Red', Color.FromArgb(190, 30, 40), 'AU6 Sign red'),
    'green':  layer(ADD + '::Safety_Green', Color.FromArgb(40, 110, 50), 'AU6 Plastic green'),
    'elec':   layer(ADD + '::Electrical_Lighting', Color.FromArgb(235, 235, 232), 'AU6 Paint white frames'),
    'bin2':   layer(ADD + '::Waste_Bins_Dark', Color.FromArgb(28, 28, 28), 'AU6 Plastic black'),
}
G_STORE, G_WORK, G_CUT = group_for('Workshop store (W2)'), group_for('Workshop fit-out (W2)'), group_for('Cutting area (W2)')
made = {}


def tag(a, name, group):
    a.Name = name
    a.SetUserString('build', TAG)
    if group is not None:
        a.AddToGroup(group)


def add(brep, key, name, group):
    if brep is None:
        print('FAILED: ' + name)
        return
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY[key]
    tag(a, name, group)
    if doc.Objects.AddBrep(brep, a) != System.Guid.Empty:
        made[key] = made.get(key, 0) + 1


def box(s0, s1, n0, n1, z0, z1):
    return rg.Box(PL, rg.Interval(L - max(s0, s1), L - min(s0, s1)), rg.Interval(min(n0, n1), max(n0, n1)),
                  rg.Interval(min(z0, z1), max(z0, z1))).ToBrep()


def B(s0, s1, n0, n1, z0, z1, key, name, group):
    add(box(s0, s1, n0, n1, z0, z1), key, name, group)


def cyl(axis, c, r, length, key, name, group):
    """cylinder centred on c=(s, n, z) with its axis along 's', 'n' or 'z'"""
    s, n, z = c
    d = {'s': (length / 2, 0, 0), 'n': (0, length / 2, 0), 'z': (0, 0, length / 2)}[axis]
    a, b = P(s - d[0], n - d[1], z - d[2]), P(s + d[0], n + d[1], z + d[2])
    add(rg.Cylinder(rg.Circle(rg.Plane(a, b - a), r), (b - a).Length).ToBrep(True, True), key, name, group)


def corrugated(origin, wdir, ddir, width, depth, key, name, group, amp=0.018, pitch=0.076):
    o, w, d = rg.Vector3d(*origin), rg.Vector3d(*wdir), rg.Vector3d(*ddir)
    d.Unitize()
    nrm = rg.Vector3d.CrossProduct(w, d)
    nrm.Unitize()
    k = int(width / pitch * 4)
    pts = []
    for i in range(k + 1):
        t = width * i / float(k)
        q = o + w * t + nrm * (amp * math.sin(2 * math.pi * t / pitch))
        pts.append(P(q.X, q.Y, q.Z))
    srf = rg.Surface.CreateExtrusion(rg.PolylineCurve(pts), P(d.X * depth, d.Y * depth, d.Z * depth) - P(0, 0, 0))
    add(srf.ToBrep() if srf else None, key, name, group)


def plan(pts_sn, name, label):
    """layout outline (curve at z 0.01) + label dot on the _Layout_Plan layer"""
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY['zone']
    tag(a, name, None)
    doc.Objects.AddCurve(rg.PolylineCurve([P(s, n, 0.01) for s, n in pts_sn + [pts_sn[0]]]), a)
    cs = sum(p[0] for p in pts_sn) / len(pts_sn)
    cn = sum(p[1] for p in pts_sn) / len(pts_sn)
    doc.Objects.AddTextDot(rg.TextDot(label, P(cs, cn, 0.3)), a)


def rect(s0, s1, n0, n1):
    return [(s0, n0), (s1, n0), (s1, n1), (s0, n1)]


# ------------------------------------------------------------------ 3. layout plan
plan(rect(S_N, S_OUT, N_EAST, N_W), 'workshop area (user highlight)', 'W2 WORKSHOP AREA')
plan(rect(S_N, S_POST, N_SCREEN, N_W), 'store (closed section)', 'TOOL + MATERIAL STORE')
plan(rect(*TABLE_A), 'work table A under the roof (modelled by the user)', 'WORK TABLE A (user)')
plan(rect(*TABLE_B), 'work table B in the yard (modelled by the user)', 'WORK TABLE B (user)')
plan(rect(S_POST, S_OUT, N_EAST, 9.15), 'cutting area (open)', 'SHEET CUTTING / SAWHORSES')
plan(rect(-13.9, -12.7, N_SCREEN - 1.0, N_SCREEN), 'store door swing / clear zone', 'DOOR CLEAR')

# ------------------------------------------------------------------ 4. store: screen with door, racks, cabinet
SD0, SD1 = -13.9, -12.7                          # door opening in the screen
for a0, a1 in ((S_N + 0.02, SD0 - 0.05), (SD1 + 0.05, S_POST - 0.05)):
    corrugated((a0, N_SCREEN, 0.0), (1, 0, 0), (0, 0, 1), a1 - a0, roof_z(a1) - 0.05, 'screen', 'store screen (corrugated)', G_STORE)
    for s in (a0, a1 - 0.04):
        B(s, s + 0.04, N_SCREEN - 0.03, N_SCREEN + 0.03, 0.0, roof_z(s) - 0.02, 'rack', 'screen post 40x60', G_STORE)
for s in (SD0 - 0.05, SD1):                      # door frame
    B(s, s + 0.05, N_SCREEN - 0.03, N_SCREEN + 0.03, 0.0, 2.10, 'rack', 'door frame jamb', G_STORE)
B(SD0 - 0.05, SD1 + 0.05, N_SCREEN - 0.03, N_SCREEN + 0.03, 2.10, 2.16, 'rack', 'door frame head', G_STORE)
mid = 0.5 * (SD0 + SD1)
for la, lb in ((SD0 + 0.005, mid - 0.004), (mid + 0.004, SD1 - 0.005)):
    for z0, z1 in ((0.02, 0.06), (2.04, 2.08)):
        B(la, lb, N_SCREEN - 0.02, N_SCREEN + 0.02, z0, z1, 'door', 'store door leaf frame', G_STORE)
    for s in (la, lb - 0.04):
        B(s, s + 0.04, N_SCREEN - 0.02, N_SCREEN + 0.02, 0.06, 2.04, 'door', 'store door leaf frame', G_STORE)
    corrugated((la + 0.04, N_SCREEN, 0.06), (1, 0, 0), (0, 0, 1), lb - la - 0.08, 1.98, 'door', 'store door leaf infill', G_STORE, amp=0.012)
B(mid - 0.06, mid + 0.06, N_SCREEN - 0.035, N_SCREEN - 0.02, 1.0, 1.14, 'steel', 'door hasp + padlock', G_STORE)

# timber wall brackets on the west wall (3 levels, made in the workshop from offcuts), timber on them
for s in (-14.10, -12.40, -10.70):
    B(s, s + 0.07, N_W - 0.05, N_W, 0.0, 1.70, 'timber', 'timber rack upright 45x70 (screwed to the wall)', G_STORE)
    for z in (0.45, 0.95, 1.45):
        B(s, s + 0.045, N_W - 0.50, N_W - 0.05, z - 0.07, z, 'timber', 'timber rack bracket', G_STORE)
for k, z in enumerate((0.45, 0.95, 1.45)):
    for j in range(4 - k):
        n0 = N_W - 0.47 + j * 0.09
        B(-14.25, -11.25 + 0.3 * (j % 2), n0, n0 + 0.07, z, z + 0.045, 'timber', 'timber stock 45x70 x 3.0 m (incl. reclaimed pallet wood)', G_STORE)

# sheet rack on the north wall: a few sheets standing on their long edge
B(S_N, S_N + 0.30, 9.95, 12.75, 0.0, 0.06, 'timber', 'sheet rack base batten', G_STORE)
for n in (10.0, 12.65):
    B(S_N, S_N + 0.30, n, n + 0.05, 0.06, 1.40, 'timber', 'sheet rack upright', G_STORE)
for k in range(3):
    s0 = S_N + 0.05 + k * 0.021
    B(s0, s0 + 0.018, 10.05, 12.55, 0.06, 1.31, 'sheet', 'sheet stock OSB 2500x1250x18', G_STORE)

# one steel shelving unit along the south screen, inside, with boxes of fixings / consumables
s0, s1, n0 = S_POST - 0.55, S_POST - 0.05, 9.35
for s in (s0, s1 - 0.03):
    for n in (n0, n0 + 0.97):
        B(s, s + 0.03, n, n + 0.03, 0.0, 1.8, 'rack', 'shelving upright', G_STORE)
for z in (0.15, 0.70, 1.25, 1.77):
    B(s0, s1, n0, n0 + 1.0, z, z + 0.03, 'rack', 'shelf 1000x500', G_STORE)
    if z < 1.7:
        for j in range(3):
            B(s0 + 0.05, s1 - 0.05, n0 + 0.04 + j * 0.32, n0 + 0.32 + j * 0.32, z + 0.03, z + 0.28, 'boxes',
              'storage box (screws, nails, bolts, glue, gloves)', G_STORE)

# lockable tool cabinet behind the screen
B(-12.50, -11.50, N_SCREEN + 0.06, N_SCREEN + 0.56, 0.0, 1.80, 'cab', 'lockable tool cabinet 1000x500x1800 (hand tools out of hours)', G_STORE)
B(-11.95, -11.93, N_SCREEN + 0.04, N_SCREEN + 0.06, 0.9, 1.1, 'steel', 'cabinet lock', G_STORE)

# ------------------------------------------------------------------ 5. work area under the roof
# tool wall on the store screen's work-area face: pegboard, hand tools, one shelf
TW0, TW1 = -12.55, -10.35
NF = N_SCREEN - 0.035                            # face of the pegboard
B(TW0, TW1, NF - 0.018, NF, 1.00, 2.00, 'board', 'tool wall pegboard 2200x1000 (OSB)', G_WORK)
for s in (TW0, TW1 - 0.05):
    B(s, s + 0.05, NF - 0.05, NF, 0.0, 2.00, 'bench', 'tool wall post', G_WORK)
B(TW0, TW1, NF - 0.30, NF, 0.88, 0.92, 'bench', 'tool wall shelf', G_WORK)
HAND = [  # (s offset, z, width, height, handle?, name)
    (0.08, 1.70, 0.05, 0.30, True, 'claw hammer'), (0.18, 1.70, 0.05, 0.30, True, 'claw hammer'),
    (0.30, 1.72, 0.09, 0.28, True, 'rubber mallet'),
    (0.46, 1.35, 0.14, 0.60, True, 'panel saw'), (0.66, 1.45, 0.12, 0.40, True, 'tenon saw'),
    (0.84, 1.55, 0.12, 0.28, True, 'coping saw'), (0.84, 1.20, 0.12, 0.28, True, 'hacksaw'),
    (1.02, 1.62, 0.30, 0.30, False, 'try square + combination square'), (1.02, 1.25, 0.08, 0.08, False, 'tape measure 8 m'),
    (1.14, 1.25, 0.08, 0.08, False, 'tape measure 8 m'), (1.36, 1.55, 0.22, 0.25, True, 'chisels 6/12/20/25'),
    (1.36, 1.20, 0.20, 0.25, True, 'screwdrivers'), (1.62, 1.10, 0.05, 0.80, False, 'spirit level 1.2 m'),
    (1.72, 1.50, 0.10, 0.45, False, 'pry bar / pallet breaker'), (1.86, 1.60, 0.14, 0.30, True, 'pliers, pincers, snips'),
    (1.86, 1.20, 0.18, 0.30, False, 'adjustable spanners x2'), (2.06, 1.45, 0.08, 0.40, True, 'rasp + file'),
]
for ds, z, w, h, handle, nm in HAND:
    B(TW0 + ds, TW0 + ds + w, NF - 0.035, NF - 0.018, z, z + h, 'steel', 'tool wall: ' + nm, G_WORK)
    if handle:                                   # coloured handles so the silhouettes read
        B(TW0 + ds, TW0 + ds + w, NF - 0.040, NF - 0.035, z, z + min(0.12, h * 0.4), 'handle', 'tool wall: ' + nm + ' (handle)', G_WORK)
SHELF = [(0.10, 0.30, 0.10, 'hand drill (brace / eggbeater) + bits'), (0.50, 0.30, 0.12, 'socket set case'),
         (0.90, 0.24, 0.10, 'block plane + smoothing plane'), (1.25, 0.30, 0.10, 'sanding blocks + paper'),
         (1.65, 0.40, 0.08, 'pencils, marking gauge, chalk line, bradawl')]
for ds, w, h, nm in SHELF:
    B(TW0 + ds, TW0 + ds + w, NF - 0.25, NF - 0.05, 0.92, 0.92 + h, 'steel', 'tool shelf: ' + nm, G_WORK)

# clamp rail on the north wall: 4 F-clamps + 2 quick clamps
B(S_N, S_N + 0.04, 7.95, 8.75, 1.05, 1.13, 'bench', 'clamp rail', G_WORK)
for j in range(6):
    n = 8.0 + j * 0.12
    B(S_N + 0.04, S_N + 0.06, n, n + 0.02, 0.60, 1.13, 'steel', 'clamp bar', G_WORK)
    B(S_N + 0.04, S_N + 0.12, n - 0.01, n + 0.03, 0.66, 0.74, 'handle', 'clamp jaw', G_WORK)

# mitre box + backsaw on table A (replaces the power mitre saw)
ms, mn = TABLE_A[0] + 0.35, TABLE_A[2] + 0.45
B(ms, ms + 0.12, mn, mn + 0.40, TABLE_Z, TABLE_Z + 0.09, 'bench', 'mitre box (beech)', G_WORK)
B(ms + 0.04, ms + 0.08, mn - 0.05, mn + 0.45, TABLE_Z + 0.09, TABLE_Z + 0.18, 'steel', 'backsaw in the mitre box', G_WORK)

# two LED battens under the roof (one socket circuit for light only)
for s in (-12.70, -11.05):
    B(s - 0.04, s + 0.04, 5.6, 8.2, roof_z(s) - 0.12, roof_z(s) - 0.08, 'elec', 'LED batten 1.5 m (IP65)', G_WORK)

# safety point on the front corner post (visible from the ramp and the yard)
SP_S, SP_N0 = S_POST + 0.05, 4.72
B(SP_S, SP_S + 0.02, SP_N0, SP_N0 + 0.70, 0.80, 1.90, 'bench', 'safety point board', G_WORK)
B(SP_S + 0.02, SP_S + 0.12, SP_N0 + 0.05, SP_N0 + 0.40, 1.35, 1.70, 'green', 'first aid kit (with eye wash bottle)', G_WORK)
cyl('z', (SP_S + 0.10, SP_N0 + 0.55, 1.05), 0.075, 0.50, 'red', 'fire extinguisher 6 kg ABC', G_WORK)
B(SP_S + 0.02, SP_S + 0.06, SP_N0 + 0.05, SP_N0 + 0.40, 0.95, 1.25, 'steel', 'hooks: work gloves, safety glasses, dust masks', G_WORK)
B(SP_S + 0.02, SP_S + 0.03, SP_N0 + 0.42, SP_N0 + 0.68, 1.75, 1.87, 'elec', 'tool sign-out sheet', G_WORK)

# ------------------------------------------------------------------ 6. cutting area in front of the posts
for n0 in (6.00, 8.00):                          # two sawhorses (built in the first session) carrying a sheet
    for s in (-9.85, -9.05):
        B(s, s + 0.05, n0, n0 + 0.05, 0.0, 0.70, 'bench', 'sawhorse leg', G_CUT)
    B(-9.90, -8.95, n0 - 0.02, n0 + 0.07, 0.70, 0.76, 'bench', 'sawhorse beam', G_CUT)
B(-9.97, -8.72, 5.85, 8.35, 0.76, 0.778, 'sheet', 'OSB sheet on the sawhorses', G_CUT)
B(-9.60, -9.46, 6.60, 7.20, 0.778, 0.785, 'steel', 'panel saw on the sheet', G_CUT)
B(-9.62, -9.44, 7.20, 7.32, 0.778, 0.82, 'handle', 'panel saw handle', G_CUT)
for k, nm in enumerate(('offcuts bin (timber for reuse / kindling)', 'general waste bin')):
    n0 = 9.65 + k * 0.62
    B(-9.95, -9.40, n0, n0 + 0.56, 0.0, 1.0, 'bin2', nm, G_CUT)

# ------------------------------------------------------------------ 7. drop layers left empty by earlier revisions
for name in ('Tools_Power', 'Tools_Blades_Rails', 'Store_Flammables_Cabinet', 'Waste_Bins'):
    idx = doc.Layers.FindByFullPath(ADD + '::' + name, -1)
    if idx >= 0 and not doc.Objects.FindByLayer(doc.Layers[idx]):
        doc.Layers.Delete(idx, True)

doc.Views.Redraw()
print('relocated / replaced (moved to %s): %d' % (REM, moved))
print('parts: %s' % made)
