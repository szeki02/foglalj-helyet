# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 3 (road mural), added 2026-10-14: the painted mural on the asphalt inside the
# street gate, as a workshop of its own. Re-runnable.
#
# Brief (user): "Create separate workshop stage for the mural painting on the concrete". The mural was first part of
# workshop 1 (build_w1_parking_paint.py, which now keeps only the parking bays). Then (user: "move the mural workshop
# right after the workshop space as well as the poster workshop") it became workshop 3, before the window posters
# (scripts/reorder_workshops.py): the first decorating workshop, done before the bays are in use.
#
# The design (revised from a sun / hopscotch / dots: "make the murals less childish"): the asphalt s 18.85..23.15 x
# n 7.5..13.35 between the brick hut and the west wall, a 3 x 4 grid of 1.4 m tiles with 60 mm asphalt joints, each
# a ground colour with one shape over it (quarter circle, half circle, half-square triangle or plain), in terracotta,
# ochre, deep green, slate blue, charcoal and off-white. Paint is flat (planar surfaces) 5 mm above the asphalt, the
# shapes 7 mm.
#
# For the website's build-up every tile ground and every shape is its own piece (user text 'piece'), and grounds and
# shapes sit on separate layers (Road_Mural_<colour> / Road_Mural_Motif_<colour>): the grounds are rolled first, row by
# row from the wall, and the shapes cut in after them.
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'w7_mural'                                   # the tag of the first build, kept so a re-run finds its objects
ADD = '09_Workshops::w3_road_mural'
Z, Z2 = 0.005, 0.007
log = []

# ------------------------------------------------------------------ the stage's layers
for top in ('09_Workshops', '10_Removed'):
    if doc.Layers.FindByFullPath(top + '::w3_road_mural', -1) < 0:
        lay = Rhino.DocObjects.Layer()
        lay.Name = 'w3_road_mural'
        lay.ParentLayerId = doc.Layers[doc.Layers.FindByFullPath(top, -1)].Id
        doc.Layers.Add(lay)
        log.append('added %s::w3_road_mural' % top)

for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

COLOURS = {'terracotta': (184, 92, 62), 'ochre': (208, 158, 66), 'green': (54, 98, 80), 'slate': (64, 88, 120),
           'charcoal': (58, 58, 60), 'offwhite': (230, 224, 210)}
LY = {}
for c, rgb in COLOURS.items():
    name = 'Road_Mural_' + c.capitalize()
    mat = rmat('AU6 ' + name.replace('_', ' ').lower(), rgb)
    LY[c] = layer(ADD + '::' + name, Color.FromArgb(*rgb), mat)
    LY['motif ' + c] = layer(ADD + '::Road_Mural_Motif_' + c.capitalize(), Color.FromArgb(*rgb), mat)


def planar(pts_sn, z, key, name, group):
    pts = [P(s, n, z) for s, n in pts_sn] + [P(pts_sn[0][0], pts_sn[0][1], z)]
    put(rg.Brep.CreatePlanarBreps(rg.PolylineCurve(pts), TOL)[0], key, name, group)


def arc_pts(cs, cn, r, a0, a1, steps=18):
    return [(cs + r * math.cos(a0 + (a1 - a0) * i / steps), cn + r * math.sin(a0 + (a1 - a0) * i / steps)) for i in range(steps + 1)]


g = 'Road mural (W3)'
MS0, MS1, MN0, MN1, JOINT = 18.85, 23.15, 7.50, 13.35, 0.06
COLS, ROWS = 3, 4
TW, TH = (MS1 - MS0) / COLS, (MN1 - MN0) / ROWS
# (ground, shape colour, motif, rotation in quarter turns) per tile, row by row from the hut side (n) and the parking
# side (s); the quarter circles and triangles turn so their curves and diagonals run on from tile to tile
TILES = [('slate', 'offwhite', 'quarter', 0), ('terracotta', 'ochre', 'tri', 1), ('green', 'offwhite', 'semi', 2),
         ('ochre', 'slate', 'semi', 0), ('offwhite', 'terracotta', 'quarter', 2), ('charcoal', 'ochre', 'tri', 3),
         ('green', 'terracotta', 'tri', 0), ('slate', 'ochre', 'plain', 0), ('terracotta', 'offwhite', 'quarter', 1),
         ('offwhite', 'green', 'quarter', 3), ('ochre', 'charcoal', 'tri', 2), ('slate', 'terracotta', 'semi', 1)]

for idx, (ground, fg, motif, rot) in enumerate(TILES):
    col, row = idx % COLS, idx // COLS
    tid = '%d-%d' % (row + 1, col + 1)
    s0 = MS0 + col * TW + JOINT / 2; s1 = s0 + TW - JOINT
    n0 = MN0 + row * TH + JOINT / 2; n1 = n0 + TH - JOINT
    planar([(s0, n0), (s1, n0), (s1, n1), (s0, n1)], Z, ground, 'mural tile ' + tid, g)
    side = min(s1 - s0, n1 - n0)
    corners = [(s0, n0), (s1, n0), (s1, n1), (s0, n1)]
    if motif == 'quarter':                         # quarter circle from one corner, into the tile
        cs, cn = corners[rot % 4]
        a0 = rot * math.pi / 2
        planar([(cs, cn)] + arc_pts(cs, cn, side * 0.92, a0, a0 + math.pi / 2), Z2, 'motif ' + fg, 'mural shape ' + tid, g)
    elif motif == 'semi':                          # half circle standing on one edge
        mids = [((s0 + s1) / 2, n0, math.pi / 2), (s1, (n0 + n1) / 2, math.pi), ((s0 + s1) / 2, n1, -math.pi / 2), (s0, (n0 + n1) / 2, 0.0)]
        ms, mn, a = mids[rot % 4]
        planar(arc_pts(ms, mn, side * 0.45, a - math.pi / 2, a + math.pi / 2), Z2, 'motif ' + fg, 'mural shape ' + tid, g)
    elif motif == 'tri':                           # half-square triangle
        planar([corners[rot % 4], corners[(rot + 1) % 4], corners[(rot + 2) % 4]], Z2, 'motif ' + fg, 'mural shape ' + tid, g)

made, fails, gids = add_pieces(TAG, LY)
tagged = 0
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    a = o.Attributes.Duplicate()
    a.SetUserString('piece', o.Attributes.Name)    # 'mural tile 2-3' / 'mural shape 2-3': one mesh each on the website
    doc.Objects.ModifyAttributes(o, a, True)
    tagged += 1
doc.Views.Redraw()
report = log + ['objects: %s' % ', '.join('%s %d' % kv for kv in sorted(made.items())), 'pieces tagged: %d' % tagged] + fails
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_w7m_log.txt', 'w') as f:
    f.write('\n'.join(report))
