# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 8 (shelter table): a beer-tent set (sorpad) from the store and a notice board
# under the gabled shelter, furnished with the fire circle's crate chairs and side tables (W7). Re-runnable.
#
# Brief (user, 2026-10-14): "the shelter table area should be populated with the furniture made for the fireplace
# in tab 8". (user, 2026-10-15): "There is no need to build a table for the shelter table, there are ones in storage
# that can be used" - "use typical sorpad model".
#
# The shelter is the surveyed galvanised gable (04_Furniture_Elements::Shelter_3_Gable): posts at s -7.30 / -5.40 /
# -3.50 / -1.60 on the lines n -2.10 (yard side) and n -4.52; mesh panels close both ends and the yard side past
# s -2.60 and before s -6.40, so the way in is the 3.8 m opening between them. Inside: s -7.27..-1.63, n -4.49..-2.13.
#
# What this workshop sets up (09_Workshops::w8_shelter_table):
#   - nothing is built for the table: a standard Hungarian beer-tent set (sorpad garnitura) comes out of the store,
#     a folding table 2200 x 500 at 760 mm and two folding benches 2200 x 250 at 470 mm, spruce tops on painted steel
#     tube leg frames, set up lengthwise in the middle of the shelter;
#   - a notice board (OSB with a cork face, timber frame) on the inside of the shelter's east end panel, facing the
#     table, with a few notes pinned on it.
# The fire circle's 7 crate chairs and 3 side tables are carried over for this workshop: 5 chairs round 2 side tables
# make a low corner at the west end, 2 chairs and the 3rd side table stand by the notice board at the east end.
# The originals move to 09_Workshops::w7_fire_circle::Away_in_w8::<leaf> (hidden at W8 only, back at the fire from
# W9 on, so the opening's fire circle is furnished) and copies stand under the shelter on this workshop's
# '...::Stored_from_w9::<leaf>' layers (gone again from W9 on), with the same leaf names, so the viewer's midway can
# take them away at the fire and bring them in here.
# Re-running build_w7_fire_circle.py recreates the fire furniture on its own layers: run this script after it.
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'w8_shelter'
STAGE = 'w8_shelter_table'
ADD = '09_Workshops::' + STAGE
W7 = '09_Workshops::w7_fire_circle'
AWAY = W7 + '::Away_in_w8'
FURN_LEAVES = ('Chair_Crates_Red', 'Chair_Crates_Blue', 'Chair_Crates_Yellow', 'Chair_Crates_Green',
               'Chair_Backrests', 'Chair_Cushions_Ochre', 'Chair_Cushions_Teal', 'Fireside_Tables')

if doc.Layers.FindByFullPath(ADD, -1) < 0:
    raise Exception('no layer %s: run scripts/setup_workshop_layers.py first' % ADD)

# ------------------------------------------------------------------ 0. clean previous run
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

# ------------------------------------------------------------------ 1. where the fire circle furniture stands (W7)
pit_box = rg.BoundingBox.Empty
for o in doc.Objects.GetObjectList(ALL):
    if (o.Attributes.Name or '') == 'fire pit wall':
        pit_box.Union(o.Geometry.GetBoundingBox(PL))
if not pit_box.IsValid:
    raise Exception('fire pit walls not found')
PIT_S = L - (pit_box.Min.X + pit_box.Max.X) / 2
PIT_N = (pit_box.Min.Y + pit_box.Max.Y) / 2


def at_ring(deg, r):                             # as build_w7_fire_circle.py
    a = math.radians(deg)
    return PIT_S + r * math.cos(a), PIT_N + r * math.sin(a)


W7_CHAIRS = [(-10, 1.75), (30, 1.75), (60, 1.75), (90, 1.75), (120, 1.75), (150, 1.75), (180, 2.15)]
W7_TABLES = [(75, 1.95), (135, 1.95), (165, 2.30)]

# ------------------------------------------------------------------ 2. the layout under the shelter
TS, TN = -4.10, -3.30                            # beer-tent set centre: table s -5.20..-3.00
TL, TW, TZ = 2.20, 0.50, 0.76                    # table: length, width, top height
BL, BW, BZ = 2.20, 0.25, 0.47                    # benches
BOFF = 0.42                                      # bench centre lines from the table's (inner edges just under it)
WC = (-6.30, TN)                                 # west corner: 5 crate chairs round 2 side tables
EC = (-2.30, TN)                                 # east: 2 chairs and the 3rd side table under the notice board
# (s, n, face): chairs face their side tables; side tables square to the shelter
NEW_CHAIRS = [(-6.30, -2.55, WC), (-6.30, -4.05, WC), (-6.98, TN, WC), (-5.70, -2.80, WC), (-5.70, -3.80, WC),
              (-2.30, -2.62, EC), (-2.30, -3.98, EC)]
NEW_TABLES = [(-6.30, -3.08), (-6.30, -3.52), EC]

# ------------------------------------------------------------------ 3. layers
OILED = rmat('AU6 Timber oiled', (150, 104, 62))
LY = {
    'plan':   layer(ADD + '::_Layout_Plan', Color.FromArgb(230, 180, 40)),
    'stop':   layer(ADD + '::Sorpad_Tops', Color.FromArgb(214, 176, 120), rmat('AU6 Spruce varnished', (214, 176, 120), 0.2)),
    'sleg':   layer(ADD + '::Sorpad_Legs', Color.FromArgb(48, 50, 52), 'AU6 Steel painted dark'),
    'nboard': layer(ADD + '::Notice_Board', Color.FromArgb(150, 104, 62), OILED),
    'cork':   layer(ADD + '::Notice_Board_Cork', Color.FromArgb(176, 128, 84), rmat('AU6 Cork', (176, 128, 84))),
    'notes':  layer(ADD + '::Notice_Board_Notes', Color.FromArgb(236, 232, 214), rmat('AU6 Paper', (236, 232, 214))),
    'notes2': layer(ADD + '::Notice_Board_Notes_Yellow', Color.FromArgb(236, 206, 90), rmat('AU6 Paper yellow', (236, 206, 90))),
}
for leaf in FURN_LEAVES:                         # the copies: same leaf names and materials as the originals, on a
    src = doc.Layers[doc.Layers.FindByFullPath(W7 + '::' + leaf, -1)] if doc.Layers.FindByFullPath(W7 + '::' + leaf, -1) >= 0 \
        else doc.Layers[doc.Layers.FindByFullPath(AWAY + '::' + leaf, -1)]
    LY[leaf] = layer(ADD + '::Stored_from_w9::' + leaf, src.Color, src.RenderMaterial)   # gone again from W9 on
    old = doc.Layers.FindByFullPath(ADD + '::' + leaf, -1)                                # (the first run's layers)
    if old >= 0:
        for o in doc.Objects.FindByLayer(doc.Layers[old]) or []:
            doc.Objects.Delete(o, True, True)
        doc.Layers.Delete(old, True)


# ------------------------------------------------------------------ 4. carry the fire circle furniture over
def members(gname):
    gi = doc.Groups.Find(gname)
    return list(doc.Groups.GroupMembers(gi) or []) if gi >= 0 else []


def move_xf(s0, n0, phi0, s1, n1, phi1):
    """rigid move of a piece standing at (s0, n0) turned phi0 to (s1, n1) turned phi1 (Frame's phi convention)"""
    rot = rg.Transform.Rotation(phi1 - phi0, rg.Vector3d.ZAxis, P(s0, n0))
    return rg.Transform.Translation(P(s1, n1) - P(s0, n0)) * rot


carried, sent_away = 0, 0
jobs = [('chair %d' % (i + 1), at_ring(*W7_CHAIRS[i]), NEW_CHAIRS[i]) for i in range(7)] + \
       [('table %d' % (i + 1), at_ring(*W7_TABLES[i]), (NEW_TABLES[i][0], NEW_TABLES[i][1], None)) for i in range(3)]
for label, (s0, n0), (s1, n1, face) in jobs:
    phi0 = towards(s0, n0, (PIT_S, PIT_N))
    phi1 = towards(s1, n1, face) if face else 0.0
    xf = move_xf(s0, n0, phi0, s1, n1, phi1)
    objs = members('Fire circle %s (W7)' % label)
    if not objs:
        raise Exception('group not found: Fire circle %s (W7)' % label)
    gi = group_for('Shelter %s (W8)' % label)
    for o in objs:
        src = doc.Layers[o.Attributes.LayerIndex]
        if src.Name not in FURN_LEAVES:
            continue
        g = o.Geometry.Duplicate()
        g.Transform(xf)
        a = Rhino.DocObjects.ObjectAttributes()
        a.LayerIndex = LY[src.Name]
        a.Name = o.Attributes.Name
        a.SetUserString('build', TAG)
        a.SetUserString('from', 'fire circle (W7), carried over for W8')
        a.AddToGroup(gi)
        oid = doc.Objects.AddBrep(g, a) if isinstance(g, rg.Brep) else doc.Objects.Add(g, a)
        if oid != System.Guid.Empty:
            doc.Objects.Find(oid).CreateMeshes(rg.MeshType.Render, doc.GetMeshingParameters(doc.MeshingParameterStyle), False)
            carried += 1
        if not src.FullPath.startswith(AWAY + '::'):  # the original: away for this workshop only
            di = layer(AWAY + '::' + src.Name, src.Color, src.RenderMaterial)
            aa = o.Attributes.Duplicate()
            aa.SetUserString('orig_layer', src.FullPath)
            aa.SetUserString('away_in', STAGE)
            aa.LayerIndex = di
            doc.Objects.ModifyAttributes(o, aa, True)
            sent_away += 1
ai = doc.Layers.FindByFullPath(AWAY, -1)
if ai >= 0:
    lay = doc.Layers[ai]
    lay.Color = Color.FromArgb(150, 150, 150)
    doc.Layers.Modify(lay, ai, True)

# ------------------------------------------------------------------ 5. the beer-tent set (sorpad garnitura)
T = 0.025                                        # 25 mm steel tube; 25 mm spruce tops


def sorpad(fr, length, width, ztop, boards, half_leg, foot, label, g):
    """folding beer-tent table / bench in frame fr (length along ds): spruce top of `boards` boards on two battens,
    a folding leg frame 0.22 m in from each end (two uprights `half_leg` off the centre line, a foot tube `foot` wide
    on the ground, a head tube under the top) and a folding strut from each frame to the underside"""
    z0 = ztop - T
    gap = 0.003
    w = (width - (boards - 1) * gap) / boards
    for i in range(boards):
        a = -width / 2 + i * (w + gap)
        put(fr.box(-length / 2, length / 2, a, a + w, z0, ztop), 'stop', label + ' top board (spruce)', g)
    for dn in (-width / 2 + 0.05, width / 2 - 0.05 - 0.04):
        put(fr.box(-length / 2 + 0.02, length / 2 - 0.02, dn, dn + 0.04, z0 - 0.02, z0), 'stop', label + ' batten', g)
    ds_leg = length / 2 - 0.22
    for sgn in (-1, 1):
        ds = sgn * ds_leg
        zh = z0 - 0.02                                # head tube under the battens
        put(fr.box(ds - T / 2, ds + T / 2, -half_leg - T / 2, half_leg + T / 2, zh - T, zh), 'sleg', label + ' leg frame', g)
        for dn in (-half_leg, half_leg):
            put(rod(fr.pt(ds, dn * (foot / 2) / half_leg if foot else dn, T / 2), fr.pt(ds, dn, zh - T), T / 2),
                'sleg', label + ' leg upright', g)
        put(fr.box(ds - T / 2, ds + T / 2, -foot / 2, foot / 2, 0.0, T), 'sleg', label + ' leg frame foot', g)
        put(rod(fr.pt(ds, 0.0, zh * 0.45), fr.pt(ds - sgn * 0.42 * ds_leg, 0.0, zh - 0.01), 0.008),
            'sleg', label + ' folding strut', g)


ft = Frame(TS, TN, 0.0, 0.0)
sorpad(ft, TL, TW, TZ, 5, 0.20, 0.46, 'sorpad table', 'Shelter sorpad table (W8)')
for k, dn in enumerate((BOFF, -BOFF)):           # bench 1 on the yard side (+n), bench 2 at the back
    sorpad(Frame(TS, TN + dn, 0.0, 0.0), BL, BW, BZ, 2, 0.08, 0.30, 'sorpad bench %d' % (k + 1),
           'Shelter sorpad bench %d (W8)' % (k + 1))

# ------------------------------------------------------------------ 6. the notice board
g = 'Shelter notice board (W8)'
fn = Frame(-1.68, TN, 0.0, -math.pi / 2)         # front (+dn) faces the table (-s); back clear of the end panel
put(fn.box(-0.60, 0.60, -0.045, -0.027, 0.95, 1.85), 'nboard', 'notice board backing (OSB 18)', g)
put(fn.box(-0.56, 0.56, -0.027, -0.017, 0.99, 1.81), 'cork', 'notice board cork face', g)
for z0, z1, x0, x1 in ((0.95, 0.99, -0.60, 0.60), (1.81, 1.85, -0.60, 0.60), (0.99, 1.81, -0.60, -0.56), (0.99, 1.81, 0.56, 0.60)):
    put(fn.box(x0, x1, -0.027, -0.007, z0, z1), 'nboard', 'notice board frame', g)
put(fn.box(-0.64, 0.64, -0.05, -0.007, 1.85, 1.87), 'nboard', 'notice board drip cap', g)
NOTES = [(-0.42, 1.52, 0.21, 0.30, 'notes'), (-0.12, 1.58, 0.15, 0.15, 'notes2'), (0.14, 1.46, 0.21, 0.30, 'notes'),
         (0.40, 1.60, 0.15, 0.15, 'notes2'), (-0.30, 1.10, 0.30, 0.21, 'notes'), (0.28, 1.12, 0.15, 0.15, 'notes2')]
for x, z, wx, hz, key in NOTES:
    put(fn.box(x - wx / 2, x + wx / 2, -0.017, -0.015, z - hz / 2, z + hz / 2), key, 'pinned note', g)

# ------------------------------------------------------------------ 7. add
made, fails, gids = add_pieces(TAG, LY)


def plan_attr(name):
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY['plan']
    a.Name = name
    a.SetUserString('build', TAG)
    return a


doc.Objects.AddTextDot(rg.TextDot('way in: 3.8 m opening between the mesh panels', P(-4.5, -1.6, 0.3)), plan_attr('way in'))
doc.Objects.AddTextDot(rg.TextDot('chairs + side tables: fire circle (W7), here for W8 only', P(-6.3, -3.3, 1.0)),
                       plan_attr('borrowed furniture'))
doc.Objects.AddTextDot(rg.TextDot('beer-tent set from the store: table 220x50, 2 benches 220x25', P(TS, TN, 1.2)),
                       plan_attr('beer-tent set'))
for leaf in ('Table_Frame', 'Table_Top'):        # the first version's built long table
    old = doc.Layers.FindByFullPath(ADD + '::' + leaf, -1)
    if old >= 0 and not doc.Objects.FindByLayer(doc.Layers[old]):
        doc.Layers.Delete(old, True)
og = doc.Groups.Find('Shelter long table (W8)')
if og >= 0 and not doc.Groups.GroupMembers(og):
    doc.Groups.Delete(og)
doc.Views.Redraw()

report = ['fire pit centre s %.2f n %.2f' % (PIT_S, PIT_N),
          'fire circle objects carried over (copies): %d; originals moved to %s: %d' % (carried, AWAY, sent_away),
          'objects: %s' % ', '.join('%s %d' % kv for kv in sorted(made.items())),
          'groups: %d' % len(gids)] + fails
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_w8_log.txt', 'w') as f:
    f.write('\n'.join(report))
