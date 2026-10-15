# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 7 (fire circle): small fireside chairs and tables around the brick fire pit, a
# tripod with a cauldron over it for communal soup. Re-runnable.
#
# Brief (user, 2026-10-14): "The next workshop is the fire circle, smaller chairs and tables should surround the
# firepit (highlighted in the additions layer). The furniture and workshop equipment should be put away, the scene
# should be a communal cauldron soup making."
#
# The fire pit is the surveyed one (photogrammetry, 0.62 x 0.62 m, 0.45 m high, at s -0.57 n 1.93); the user had
# moved its four walls onto ADDITIONS to point at it. They go back to 04_Furniture_Elements::Brick_Fire_Pit (their
# empty home layer), so the pit is part of the yard as found and shows on the website from the survey on.
#
# Layout (s = metres from the NORTH wall towards the street, n = metres west of the pavilion facade):
#   The pit stands at the narrow north tip of the mulch bed; a brick curb runs diagonally ~0.9 m west of it
#   (driveway side) and the pavilion walkway is 0.3 m east of it. So the circle is a horseshoe, open towards the
#   pavilion (the way in, and the walkway stays clear):
#   7 milk crate chairs (as the cinema's: crate upside down, cushion, slatted pallet-board back; user, 2026-10-14)
#   facing the pit, 1.75 m from its centre (the north one 2.15 m, past the curb end), every one
#   kept 0.1 m or more off the curb; 3 small tables between them; the old metal stand south of the pit is the 4th
#   (bowls and ladles). Tripod + 25 l cauldron over the pit, logs in the pit, a log stack north of the circle,
#   a sand bucket by the metal stand.
# Put away from this workshop on (moved onto ...::Stored_from_w7::<leaf>, hidden from W7 on by the exporter, the
# viewer and layer_states.py):
#   - the garden cinema's furniture (pallets, crates, boards, cushions; projector and speakers were borrowed),
#     stored along the west wall under the painted screen, ready for the next film night (user, 2026-10-14):
#     pallets stacked and loose crates at the north end, the crate benches in a row under the screen;
#   - the hand pallet truck left in the yard after W5 (borrowed, returned).
#   The painted screen and everything already in the W2 store stay.
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'w5_fire'
STAGE = 'w7_fire_circle'
ADD = '09_Workshops::' + STAGE
PIT_LAYER = '04_Furniture_Elements::Brick_Fire_Pit'
W6 = '09_Workshops::w6_garden_cinema'
W5 = '09_Workshops::w5_mobile_garden'
W4_FURNITURE = ('Pallets', 'Riser_Pallets', 'Seat_Boards', 'Crates_Red', 'Crates_Blue', 'Crates_Yellow', 'Crates_Green',
                'Cushions_Ochre', 'Cushions_Teal', 'Projector_Sound')
W3_EQUIPMENT = ('Tool_Pallet_Truck', 'Tool_Pallet_Truck_Wheels')

if doc.Layers.FindByFullPath(ADD, -1) < 0:
    raise Exception('no layer %s: run scripts/setup_workshop_layers.py first' % ADD)

# ------------------------------------------------------------------ 0. clean previous run
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

# ------------------------------------------------------------------ 1. the fire pit back on its own layer
pit_idx = layer(PIT_LAYER, Color.FromArgb(150, 70, 50))
returned = 0
pit_box = rg.BoundingBox.Empty
for o in list(doc.Objects.GetObjectList(ALL)):
    if (o.Attributes.Name or '') != 'fire pit wall':
        continue
    if doc.Layers[o.Attributes.LayerIndex].FullPath == 'ADDITIONS':
        a = o.Attributes.Duplicate()
        a.LayerIndex = pit_idx
        a.SetUserString('highlighted', 'ADDITIONS, 2026-10-14 (W7 fire circle)')
        doc.Objects.ModifyAttributes(o, a, True)
        returned += 1
    pit_box.Union(o.Geometry.GetBoundingBox(PL))
if not pit_box.IsValid:
    raise Exception('fire pit walls not found')
PIT_S = L - (pit_box.Min.X + pit_box.Max.X) / 2
PIT_N = (pit_box.Min.Y + pit_box.Max.Y) / 2
PIT_TOP = pit_box.Max.Z
PIT_HALF = (pit_box.Max.X - pit_box.Min.X) / 2           # outer half width (0.31)
INNER = PIT_HALF - 0.12                                  # inside face of the 120 mm walls

# ------------------------------------------------------------------ 2. put the cinema furniture and the truck away
stored = {}
for o in list(doc.Objects.GetObjectList(ALL)):
    path = doc.Layers[o.Attributes.LayerIndex].FullPath
    root, leaf = path.rsplit('::', 1) if '::' in path else ('', path)
    if root == W6 and leaf in W4_FURNITURE:
        store_from(o, STAGE, W6 + '::Stored_from_w7')
    elif root == W5 and leaf in W3_EQUIPMENT:
        store_from(o, STAGE, W5 + '::Stored_from_w7')
    else:
        continue
    stored[leaf] = stored.get(leaf, 0) + 1
for root in (W6, W5):
    si = doc.Layers.FindByFullPath(root + '::Stored_from_w7', -1)
    if si >= 0:
        lay = doc.Layers[si]
        lay.Color = Color.FromArgb(150, 150, 150)
        doc.Layers.Modify(lay, si, True)

# ------------------------------------------------------------------ 3. layers
OILED = rmat('AU6 Timber oiled', (150, 104, 62))
LY = {
    'plan':    layer(ADD + '::_Layout_Plan', Color.FromArgb(230, 180, 40)),
    # the circle's chairs are milk crate chairs (user, 2026-10-14), as in the cinema: keys 'fc_*'
    'fc_red':    layer(ADD + '::Chair_Crates_Red', Color.FromArgb(196, 40, 40), 'AU6 Plastic crate red'),
    'fc_blue':   layer(ADD + '::Chair_Crates_Blue', Color.FromArgb(38, 84, 160), 'AU6 Plastic crate blue'),
    'fc_yellow': layer(ADD + '::Chair_Crates_Yellow', Color.FromArgb(232, 184, 30), 'AU6 Plastic crate yellow'),
    'fc_green':  layer(ADD + '::Chair_Crates_Green', Color.FromArgb(52, 132, 72), 'AU6 Plastic crate green'),
    'fc_board':  layer(ADD + '::Chair_Backrests', Color.FromArgb(150, 104, 62), OILED),
    'fc_ochre':  layer(ADD + '::Chair_Cushions_Ochre', Color.FromArgb(204, 142, 52), 'AU6 Fabric ochre'),
    'fc_teal':   layer(ADD + '::Chair_Cushions_Teal', Color.FromArgb(40, 112, 120), 'AU6 Fabric teal'),
    'table':   layer(ADD + '::Fireside_Tables', Color.FromArgb(150, 104, 62), OILED),
    'iron':    layer(ADD + '::Cauldron_Tripod', Color.FromArgb(48, 50, 52), 'AU6 Steel painted dark'),
    'kettle':  layer(ADD + '::Cauldron', Color.FromArgb(32, 30, 28), rmat('AU6 Cast iron black', (32, 30, 28), 0.3)),
    'logs':    layer(ADD + '::Firewood', Color.FromArgb(120, 84, 52), rmat('AU6 Firewood', (120, 84, 52))),
    'safety':  layer(ADD + '::Fire_Safety', Color.FromArgb(190, 30, 40), 'AU6 Sign red'),
    # the cinema furniture, stored along the west wall (keys as the shared crate helpers expect)
    'ppallet': layer(ADD + '::Store_Packed_Cinema_Pallets', Color.FromArgb(196, 160, 112), 'AU6 Timber pallet pine'),
    'board':   layer(ADD + '::Store_Packed_Seat_Boards', Color.FromArgb(185, 148, 102), 'AU6 Timber pallet pine'),
    'red':     layer(ADD + '::Store_Packed_Crates_Red', Color.FromArgb(196, 40, 40), 'AU6 Plastic crate red'),
    'blue':    layer(ADD + '::Store_Packed_Crates_Blue', Color.FromArgb(38, 84, 160), 'AU6 Plastic crate blue'),
    'yellow':  layer(ADD + '::Store_Packed_Crates_Yellow', Color.FromArgb(232, 184, 30), 'AU6 Plastic crate yellow'),
    'green':   layer(ADD + '::Store_Packed_Crates_Green', Color.FromArgb(52, 132, 72), 'AU6 Plastic crate green'),
    'ochre':   layer(ADD + '::Store_Packed_Cushions_Ochre', Color.FromArgb(204, 142, 52), 'AU6 Fabric ochre'),
    'teal':    layer(ADD + '::Store_Packed_Cushions_Teal', Color.FromArgb(40, 112, 120), 'AU6 Fabric teal'),
}


# ------------------------------------------------------------------ 4. fireside chairs and tables
def at_ring(deg, r):
    a = math.radians(deg)                        # 0 = towards the street (+s), 90 = towards the west wall (+n)
    return PIT_S + r * math.cos(a), PIT_N + r * math.sin(a)


def fireside_chair(s, n, label, k):
    """milk crate chair facing the pit: crate upside down, cushion (seat 0.34 m), slatted pallet-board back"""
    g = 'Fire circle ' + label + ' (W7)'
    crate_chair(Frame(s, n, 0.0, towards(s, n, (PIT_S, PIT_N))), ('fc_teal', 'fc_ochre')[k % 2], label, g, pre='fc_')


def fireside_table(s, n, label):
    """0.40 x 0.40 side table at 0.42 m with a low shelf"""
    g = 'Fire circle ' + label + ' (W7)'
    fr = Frame(s, n, 0.0, towards(s, n, (PIT_S, PIT_N)))
    for ds in ((-0.20, -0.16), (0.16, 0.20)):
        for dn in ((-0.20, -0.16), (0.16, 0.20)):
            put(fr.box(ds[0], ds[1], dn[0], dn[1], 0.0, 0.398), 'table', label + ' leg', g)
    for dn in ((-0.20, -0.16), (0.16, 0.20)):
        put(fr.box(-0.16, 0.16, dn[0], dn[1], 0.33, 0.398), 'table', label + ' apron', g)
    seat_boards(fr, -0.20, 0.20, -0.20, 0.20, 0.398, 'table', label + ' top slat', g, count=4)
    seat_boards(fr, -0.16, 0.16, -0.16, 0.16, 0.10, 'table', label + ' shelf slat', g, count=3)


CHAIRS = [(-10, 1.75), (30, 1.75), (60, 1.75), (90, 1.75), (120, 1.75), (150, 1.75), (180, 2.15)]
TABLES = [(75, 1.95), (135, 1.95), (165, 2.30)]
for i, (deg, r) in enumerate(CHAIRS):
    s, n = at_ring(deg, r)
    fireside_chair(s, n, 'chair %d' % (i + 1), i)
for i, (deg, r) in enumerate(TABLES):
    s, n = at_ring(deg, r)
    fireside_table(s, n, 'table %d' % (i + 1))

# ------------------------------------------------------------------ 5. tripod, cauldron, firewood, sand bucket
g = 'Fire circle cauldron (W7)'
fr = Frame(PIT_S, PIT_N, 0.0, 0.0)
APEX = fr.pt(0, 0, 1.55)
for deg in (90, 210, 330):                       # legs stand outside the pit walls
    a = math.radians(deg)
    put(rod(fr.pt(0.72 * math.cos(a), 0.72 * math.sin(a), 0.0), APEX, 0.012), 'iron', 'tripod leg (steel bar)', g)
put(fr.cyl(0, 0, 1.50, 0.03, 0.07), 'iron', 'tripod head', g)
KZ0, KZ1, KR = PIT_TOP + 0.08, PIT_TOP + 0.38, 0.21   # 25 l cauldron: bottom 80 mm above the pit walls
put(rod(APEX, fr.pt(0, 0, KZ1 + 0.24), 0.005), 'iron', 'chain', g)
outer = rg.Cylinder(rg.Circle(rg.Plane(fr.pt(0, 0, KZ0), rg.Vector3d.ZAxis), KR), KZ1 - KZ0).ToBrep(True, True)
inner = rg.Cylinder(rg.Circle(rg.Plane(fr.pt(0, 0, KZ0 + 0.01), rg.Vector3d.ZAxis), KR - 0.008), KZ1 - KZ0).ToBrep(True, True)
shell = rg.Brep.CreateBooleanDifference(outer, inner, TOL)
put(shell[0] if shell else outer, 'kettle', 'cauldron (bogracs, 25 l)', g)
bail = rg.Arc(fr.pt(-KR, 0, KZ1 - 0.02), fr.pt(0, 0, KZ1 + 0.24), fr.pt(KR, 0, KZ1 - 0.02)).ToNurbsCurve()
pipe = rg.Brep.CreatePipe(bail, 0.005, False, rg.PipeCapMode.Flat, True, TOL, 0.1)
if pipe:
    put(pipe[0], 'iron', 'cauldron bail', g)
for k, (ds, dn, ang) in enumerate(((-0.05, -0.06, 20), (0.04, 0.05, -35), (0.0, 0.0, 80))):   # logs in the pit
    a = math.radians(ang)
    h = INNER - 0.03
    put(rod(fr.pt(ds - h * math.cos(a), dn - h * math.sin(a), 0.05 + 0.06 * k),
            fr.pt(ds + h * math.cos(a), dn + h * math.sin(a), 0.05 + 0.06 * k), 0.04), 'logs', 'log in the pit', g)

g = 'Fire circle log stack (W7)'
fs = Frame(PIT_S - 2.85, PIT_N, 0.0, 0.0)            # north of the circle, on the asphalt past the curb end
for nb in (-0.42, 0.42):
    put(fs.box(-0.22, 0.22, nb - 0.035, nb + 0.035, 0.0, 0.045), 'logs', 'log stack batten', g)
for row in range(4):
    for k in range(5 - row % 2):
        ds = -0.18 + k * 0.09 + (0.045 if row % 2 else 0.0)
        z = 0.045 + 0.04 + row * 0.075
        put(rod(fs.pt(ds, -0.5, z), fs.pt(ds, 0.5, z), 0.04), 'logs', 'split log', g)

g = 'Fire circle safety (W7)'
sb_s, sb_n = PIT_S + 1.82, PIT_N + 0.29             # by the metal stand, between chairs 1 and 2
fb = Frame(sb_s, sb_n, 0.0, 0.0)
put(fb.cyl(0, 0, 0.0, 0.13, 0.28), 'safety', 'sand bucket', g)

# ------------------------------------------------------------------ 6. the cinema furniture, stored along the wall
# (user, 2026-10-14) Stored where it is used: along the west wall under the painted screen, ready for the next film
# night. Strip s -9.88..-0.40 (the store's side wall at s -9.95, a downpipe at s -0.66), n ~12.3..13.52:
#   north end, clear of the picture (it starts at s -7.23): two pallet stacks, the riser + bench pallets (the 2nd
#   stack 1.58 m high), and in front of them the loose crates (projector tower + speaker stands), the two crate side
#   tables and the two crate chairs, nothing higher than 1.12 m;
#   under the screen (its bottom edge at 1.31 m): the six crate benches in a row, backs to the wall (top 0.87 m).
WALL_N = 13.52
g = 'Stored cinema furniture (W7)'
fp = Frame(0, 0)
for row, (s0, full, cut) in enumerate(((-9.88, 8, 0), (-8.62, 5, 6))):   # 13 full pallets + the 6 cut seat pallets
    for k in range(full + cut):
        is_cut = k >= full
        flat_pallet(fp, s0, WALL_N - (0.45 if is_cut else PAL_W), k * PAL_H, 'ppallet', 'cinema pallet (stacked)', g,
                    depth=0.45 if is_cut else PAL_W)
left = 14                                        # projector tower (10) + speaker stands (4): loose crates
for level in range(4):
    for cs in (-9.86, -9.53, -9.20, -8.87):
        if left:
            crate(fp, cs, WALL_N - PAL_W - 0.06 - CW, level * CH, '+z', next_col(), 'cinema crate (stacked)', g)
            left -= 1
for i, s_c in enumerate((-8.40, -7.95)):          # crate side tables, then the crate chairs, in front of the stacks
    crate_table(Frame(s_c, 12.50, 0.0, math.pi), 'stored crate side table %d' % (i + 1), g)
for i, s_c in enumerate((-7.50, -7.05)):
    crate_chair(Frame(s_c, 12.42, 0.0, math.pi), 'teal', 'stored crate chair %d' % (i + 1), g)   # back clear of the stack
for i in range(6):                                # benches face away from the wall (phi = pi): raked back top 0.24 behind
    crate_bench(Frame(-6.80 + i * 1.17, WALL_N - 0.32, 0.0, math.pi), ('teal', 'ochre')[i % 2],
                'stored crate bench %d' % (i + 1), g)

# ------------------------------------------------------------------ 7. add
made, fails, gids = add_pieces(TAG, LY)
old = doc.Layers.FindByFullPath(ADD + '::Fireside_Chairs', -1)   # the first, pallet-wood chairs' layer
if old >= 0 and not doc.Objects.FindByLayer(doc.Layers[old]):
    doc.Layers.Delete(old, True)
og = doc.Groups.Find('Packed cinema furniture (W7)')              # the first version, packed in the W1 unit
if og >= 0 and not doc.Groups.GroupMembers(og):
    doc.Groups.Delete(og)


def plan_attr(name):
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LY['plan']
    a.Name = name
    a.SetUserString('build', TAG)
    return a


for r, name in ((1.0, 'keep clear: 1.0 m round the pit'), (1.75, 'chair ring 1.75 m')):
    c = rg.Circle(rg.Plane(P(PIT_S, PIT_N, 0.01), rg.Vector3d.ZAxis), r).ToNurbsCurve()
    doc.Objects.AddCurve(c, plan_attr(name))
    doc.Objects.AddTextDot(rg.TextDot(name, P(PIT_S - r, PIT_N, 0.3)), plan_attr(name))
doc.Objects.AddTextDot(rg.TextDot('open side: way in from the pavilion walkway', P(PIT_S, PIT_N - 1.5, 0.3)),
                       plan_attr('way in'))
doc.Views.Redraw()

report = ['pit walls returned to %s: %d (pit centre s %.2f n %.2f, top %.2f)' % (PIT_LAYER, returned, PIT_S, PIT_N, PIT_TOP),
          'put away (moved to ...::Stored_from_w7): %s' % (', '.join('%s %d' % kv for kv in sorted(stored.items())) or 'already'),
          'objects: %s' % ', '.join('%s %d' % kv for kv in sorted(made.items())),
          'groups: %d' % len(gids)] + fails
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_w5_log.txt', 'w') as f:
    f.write('\n'.join(report))
