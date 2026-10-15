# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 1 (reorganisation), added 2026-10-14: marked parking bays along the west wall.
# Re-runnable.
#
# Brief (user): "the reorganisation tab should also include designated parking spaces in the indicated area in the
# addition layer (4 places) as well as playful painting on the road surface next to the entrance and close to the
# designated parking spaces". The area (curve on ADDITIONS, left there): s 9.61..18.71, n 9.25..13.60.
# The four original pallet planters stand along that wall until W5 rolls them to the nooks: the bays are painted in W1
# round them and can be used from W5 on (user's choice). The road mural by the gate began here and became workshop 3
# of its own (user: "Create separate workshop stage for the mural painting"): build_w3_road_mural.py.
#
# Paint is flat (planar surfaces) 5 mm above the asphalt.
#   BAYS      3 bays at 60 deg, 2.3 m wide, open towards the gate, 4.3 m deep (n 9.30..13.55), white 100 mm lines,
#             a painted bay number near the mouth (bay 1 by the gate, read from the driveway).
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'w1_paint'
ADD = '09_Workshops::w1_reorganisation'
Z = 0.005

for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)


LY = {
    'white':      layer(ADD + '::Parking_Lines', Color.FromArgb(240, 240, 236), rmat('AU6 Road paint white', (240, 240, 236))),
}


def planar(pts_sn, z, key, name, group):
    pts = [P(s, n, z) for s, n in pts_sn] + [P(pts_sn[0][0], pts_sn[0][1], z)]
    put(rg.Brep.CreatePlanarBreps(rg.PolylineCurve(pts), TOL)[0], key, name, group)


# ------------------------------------------------------------------ parking bays
# Revision (user): "the parking spaces should run diagonally towards the entrance for ease of parking". Echelon bays at
# 60 deg to the driveway, open towards the gate (a car coming in from the street turns into them nose first). Angled
# bays take more wall: four would need ~11.8 m, so three 2.3 m bays fill the 9.1 m area (user's choice). The two end
# lines stop at the area's edges.
S0, S1, N0, N1, LW = 9.65, 18.70, 9.30, 13.55, 0.10
ANG = math.radians(60)
COT = 1 / math.tan(ANG)                           # s the lines lean back (towards -s) per metre of depth
BW = 2.30                                         # bay width, square to the lines
PITCH = BW / math.sin(ANG)                        # 2.66 m along the driveway
A = 11.35                                         # s of the first line's front end: centres the two outer cars
NBAYS = 3


def line_s(k, n):
    return A + k * PITCH - (n - N0) * COT


def bay_centre(k, n):
    return A + (k + 0.5) * PITCH - (n - N0) * COT


g = 'Parking bays (W1)'
hw = LW / 2 / math.sin(ANG)                       # half the line width, measured along s
for k in range(NBAYS + 1):
    na, nb = N0, N1                               # clip the line to the area
    if line_s(k, N0) > S1:
        na = N0 + (line_s(k, N0) - S1) / COT
    if line_s(k, N1) < S0:
        nb = N0 + (line_s(k, N0) - S0) / COT
    planar([(line_s(k, na) - hw, na), (line_s(k, na) + hw, na), (line_s(k, nb) + hw, nb), (line_s(k, nb) - hw, nb)],
           Z, 'white', 'parking bay line', g)
numbers = 0
ds = doc.DimStyles.Current
up = (-math.cos(ANG), math.sin(ANG))              # into the bay, (ds, dn)
right = (-math.sin(ANG), -math.cos(ANG))          # a driver's right, facing into the bay


def vec(d):
    return P(d[0], d[1], 0) - P(0, 0, 0)


for k in range(NBAYS):
    label = str(NBAYS - k)                        # bay 1 is the one nearest the gate
    nc = N0 + 0.85
    target = P(bay_centre(k, nc), nc, Z)
    # The text tool takes its size from the dimension style, so the digit is scaled to 0.6 m afterwards; it lies along
    # the bay, reading from the driveway, 0.85 m in from the bay mouth.
    try:
        tp = rg.Plane(target, vec(right), vec(up))
        te = rg.TextEntity.Create(label, tp, ds, False, 0, 0)
        breps = list(te.CreateSurfaces(ds, 1.0, 0.0) or [])
        if not breps:
            continue
        bb = rg.BoundingBox.Empty
        for b in breps:
            bb.Union(b.GetBoundingBox(tp))
        c = tp.PointAt((bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2, 0)
        h = max(bb.Max.Y - bb.Min.Y, 1e-6)
        xf = rg.Transform.Translation(target - c) * rg.Transform.Scale(c, 0.6 / h)
        for b in breps:
            b.Transform(xf)
            put(b, 'white', 'parking bay number %s' % label, g)
            numbers += 1
    except Exception as e:
        print('bay number skipped: %s' % e)

made, fails, gids = add_pieces(TAG, LY)
# the mural's earlier layers here (it is now workshop 3, build_w3_road_mural.py), and the first, playground version's
for old in ('Road_Paint_Red', 'Road_Paint_Blue', 'Road_Paint_Yellow', 'Road_Paint_Green', 'Road_Paint_White',
            'Road_Mural_Terracotta', 'Road_Mural_Ochre', 'Road_Mural_Green', 'Road_Mural_Slate', 'Road_Mural_Charcoal',
            'Road_Mural_Offwhite'):
    i = doc.Layers.FindByFullPath(ADD + '::' + old, -1)
    if i >= 0 and not doc.Objects.FindByLayer(doc.Layers[i]):
        doc.Layers.Delete(i, True)
doc.Views.Redraw()
report = ['objects: %s' % ', '.join('%s %d' % kv for kv in sorted(made.items())), 'bay number surfaces: %d' % numbers] + fails
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_w1p_log.txt', 'w') as f:
    f.write('\n'.join(report))
