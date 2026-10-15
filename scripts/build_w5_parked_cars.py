# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 5 (mobile garden), added 2026-10-14: cars parked in the W1 bays along the west
# wall, which come into use once the planters have rolled away to the nooks. Re-runnable.
#
# Brief (user): "add parked cars to the bays from the mobile garden stage on". Revised with the bays turned to 60 deg
# (three bays): two cars, in bays 1 and 3, driven in forwards: simple massing of a small hatchback, 4.0 x 1.76 m: body, glass
# cabin, roof, bumpers, wheels, head- and tail-lights. One group per car, so the website brings each in whole.
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'w3_cars'
ADD = '09_Workshops::w5_mobile_garden::Parked_Cars'

for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

LY = {
    'grey':   layer(ADD + '::Car_Paint_Grey', Color.FromArgb(72, 76, 80), rmat('AU6 Car paint grey', (72, 76, 80), 0.5)),
    'white':  layer(ADD + '::Car_Paint_White', Color.FromArgb(226, 226, 222), rmat('AU6 Car paint white', (226, 226, 222), 0.5)),
    'blue':   layer(ADD + '::Car_Paint_Blue', Color.FromArgb(62, 92, 132), rmat('AU6 Car paint blue', (62, 92, 132), 0.5)),
    'glass':  layer(ADD + '::Car_Glass', Color.FromArgb(34, 42, 50), rmat('AU6 Car glass', (34, 42, 50), 0.7)),
    'rubber': layer(ADD + '::Car_Rubber', Color.FromArgb(28, 28, 28), 'AU6 Plastic black'),
    'lamp':   layer(ADD + '::Car_Lights', Color.FromArgb(240, 236, 210), rmat('AU6 Car lamp', (240, 236, 210), 0.6)),
    'tail':   layer(ADD + '::Car_Taillights', Color.FromArgb(170, 30, 30), 'AU6 Sign red'),
}

# the bays (build_w1_parking_paint.py): three at 60 deg, open towards the gate
N0, ANG, PITCH, A = 9.30, math.radians(60), 2.30 / math.sin(math.radians(60)), 11.35
CARS = [(1, 'grey'), (3, 'blue')]                    # bay number (1 by the gate) and colour; bay 2 free
NC = 11.30                                            # car centre: nose 0.2 m off the wall, tail at the bay mouth
# 2026-10-15 (user: "shrink the size of the cars"): every car scaled to 80 % about its nose on the ground, so it still
# noses up 0.2 m off the wall: 3.2 x 1.41 m, 1.14 m high
SCALE = 0.80


def car(s, n, paint, label):
    g = 'Parked car, %s (W5)' % label
    fr = Frame(s, n, 0.0, math.atan2(-math.cos(ANG), math.sin(ANG)))   # +dn (the nose) into the bay, driven in forwards
    L2, B2 = 2.0, 0.88
    put(fr.box(-B2, B2, -L2 + 0.05, L2 - 0.05, 0.28, 0.80), paint, 'car body', g)
    put(fr.box(-B2 + 0.04, B2 - 0.04, 0.70, L2 - 0.12, 0.80, 0.88), paint, 'car bonnet', g)
    put(fr.box(-B2 + 0.08, B2 - 0.08, -1.55, 0.70, 0.80, 1.34), 'glass', 'car cabin glass', g)
    put(fr.box(-B2 + 0.12, B2 - 0.12, -1.45, 0.55, 1.34, 1.42), paint, 'car roof', g)
    for d in (1, -1):
        put(fr.box(-B2 + 0.02, B2 - 0.02, d * L2 - 0.08 if d > 0 else -L2, d * L2 if d > 0 else -L2 + 0.08, 0.25, 0.50),
            'rubber', 'car bumper', g)
        for x in (-B2 + 0.03, B2 - 0.03):          # wheels, inset into the body sides
            dn = d * 1.30
            put(rod(fr.pt(x - 0.10 * (1 if x > 0 else -1), dn, 0.31), fr.pt(x + 0.02 * (1 if x > 0 else -1), dn, 0.31), 0.31),
                'rubber', 'car wheel', g)
    for x in (-B2 + 0.15, B2 - 0.33):
        put(fr.box(x, x + 0.18, L2 - 0.06, L2 - 0.02, 0.62, 0.72), 'lamp', 'car headlight', g)
        put(fr.box(x, x + 0.18, -L2 + 0.02, -L2 + 0.06, 0.62, 0.74), 'tail', 'car taillight', g)
    xf = rg.Transform.Scale(fr.pt(0, L2, 0), SCALE)
    for k in order:
        if k[0] == g:
            for b in pieces[k]:
                b.Transform(xf)


for bay, paint in CARS:
    k = 3 - bay                                       # bay 1 is the one nearest the gate (highest s)
    car(A + (k + 0.5) * PITCH - (NC - N0) / math.tan(ANG), NC, paint, 'bay %d' % bay)

made, fails, gids = add_pieces(TAG, LY)
for colour in ('Grey', 'White', 'Blue'):             # drop paint layers no car uses any more
    i = doc.Layers.FindByFullPath(ADD + '::Car_Paint_' + colour, -1)
    if i >= 0 and not doc.Objects.FindByLayer(doc.Layers[i]):
        doc.Layers.Delete(i, True)
doc.Views.Redraw()
report = ['cars: %d, objects: %s' % (len(gids), ', '.join('%s %d' % kv for kv in sorted(made.items())))] + fails
print('\n'.join(report))
