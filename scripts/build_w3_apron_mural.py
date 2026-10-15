# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 3, second mural (added 2026-10-15): the concrete apron in front of the raised
# platform. Re-runnable.
#
# Brief (user): "for the mural painting, do a similar project in the indicated area (additions layer)". The area is
# the rectangle drawn on ADDITIONS (efbb8262-...), s -10.82..-7.77 x n -2.65..1.85 in the yard frame: the concrete
# apron between the raised platform (s < -11.32), the ramp (n > 2.60), the WC steps (n < -3.40) and the gabled
# shelter (s > -7.33), clear of all of them.
#
# Same method and palette as the road mural (build_w3_road_mural.py), smaller: a 2 x 3 grid of ~1.45 m tiles with
# 60 mm joints. The four tiles on the shelter side carry one ochre circle across their shared corner, broken only by
# the joints; the two on the ramp side a white peak pointing at the ramp. Paint 5 mm above the concrete, shapes 7 mm.
# Own layers (Apron_Mural_<colour> / Apron_Mural_Motif_<colour>, the road mural's materials) so the website can paint
# it on its own in the workshop's build-up; every tile ground and shape is its own piece (user text 'piece').
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'w3_apron_mural'
ADD = '09_Workshops::w3_road_mural'
Z, Z2 = 0.005, 0.007
log = []

for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

COLOURS = {'terracotta': (184, 92, 62), 'ochre': (208, 158, 66), 'green': (54, 98, 80), 'slate': (64, 88, 120),
           'charcoal': (58, 58, 60), 'offwhite': (230, 224, 210)}
LY = {}
for c, rgb in COLOURS.items():
    mat = rmat('AU6 road mural ' + c, rgb)      # the road mural's paints
    LY[c] = layer(ADD + '::Apron_Mural_' + c.capitalize(), Color.FromArgb(*rgb), mat)
    LY['motif ' + c] = layer(ADD + '::Apron_Mural_Motif_' + c.capitalize(), Color.FromArgb(*rgb), mat)


def planar(pts_sn, z, key, name, group):
    pts = [P(s, n, z) for s, n in pts_sn] + [P(pts_sn[0][0], pts_sn[0][1], z)]
    put(rg.Brep.CreatePlanarBreps(rg.PolylineCurve(pts), TOL)[0], key, name, group)


def arc_pts(cs, cn, r, a0, a1, steps=18):
    return [(cs + r * math.cos(a0 + (a1 - a0) * i / steps), cn + r * math.sin(a0 + (a1 - a0) * i / steps)) for i in range(steps + 1)]


g = 'Apron mural (W3)'
MS0, MS1, MN0, MN1, JOINT = -10.816, -7.767, -2.652, 1.852, 0.06     # the drawn rectangle
COLS, ROWS = 2, 3
TW, TH = (MS1 - MS0) / COLS, (MN1 - MN0) / ROWS
# (ground, shape colour, motif, rotation in quarter turns), row by row from the shelter side (n) and the platform
# side (s). Quarter circles: rot = the tile corner they grow from (0 = s0 n0, 1 = s1 n0, 2 = s1 n1, 3 = s0 n1), here
# always the corner the four tiles share. Triangles: corners rot, rot+1, rot+2; the pair meet in a peak at the ramp.
TILES = [('slate', 'ochre', 'quarter', 2), ('green', 'ochre', 'quarter', 3),
         ('green', 'ochre', 'quarter', 1), ('slate', 'ochre', 'quarter', 0),
         ('terracotta', 'offwhite', 'tri', 0), ('charcoal', 'offwhite', 'tri', 3)]

for idx, (ground, fg, motif, rot) in enumerate(TILES):
    col, row = idx % COLS, idx // COLS
    tid = '%d-%d' % (row + 1, col + 1)
    s0 = MS0 + col * TW + JOINT / 2; s1 = s0 + TW - JOINT
    n0 = MN0 + row * TH + JOINT / 2; n1 = n0 + TH - JOINT
    planar([(s0, n0), (s1, n0), (s1, n1), (s0, n1)], Z, ground, 'apron tile ' + tid, g)
    side = min(s1 - s0, n1 - n0)
    corners = [(s0, n0), (s1, n0), (s1, n1), (s0, n1)]
    if motif == 'quarter':
        cs, cn = corners[rot % 4]
        a0 = rot * math.pi / 2
        planar([(cs, cn)] + arc_pts(cs, cn, side * 0.92, a0, a0 + math.pi / 2), Z2, 'motif ' + fg, 'apron shape ' + tid, g)
    elif motif == 'tri':
        planar([corners[rot % 4], corners[(rot + 1) % 4], corners[(rot + 2) % 4]], Z2, 'motif ' + fg, 'apron shape ' + tid, g)

made, fails, gids = add_pieces(TAG, LY)
tagged = 0
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    a = o.Attributes.Duplicate()
    a.SetUserString('piece', o.Attributes.Name)
    doc.Objects.ModifyAttributes(o, a, True)
    tagged += 1
doc.Views.Redraw()
report = log + ['objects: %s' % ', '.join('%s %d' % kv for kv in sorted(made.items())), 'pieces tagged: %d' % tagged,
                'tile %.3f x %.3f m, area %.1f m2' % (TW, TH, (MS1 - MS0) * (MN1 - MN0))] + fails
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_w3a_log.txt', 'w') as f:
    f.write('\n'.join(report))
