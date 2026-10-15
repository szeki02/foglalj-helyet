# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - the bulb strings (festoons) as model geometry, added 2026-10-15 (user: "Include the light
# strings as geometry in all the scenes"). Re-runnable.
#
# Until now they were only drawn by the website, for the film night (W6) and the yard at night. Now each string is
# built by the workshop whose place it lights and stays up from then on, in every later stage, day and night:
#   W6 garden cinema  - 3 strings round the cinema, two on poles
#   W7 fire circle    - pavilion to a pole beyond the fire pit
#   W8 shelter table  - under the shelter roof, end frame to end frame
#   Opening           - 2 long strings across the yard, pavilion to west wall (09_Workshops::open_festoons)
# Same positions, sags and bulb counts as the website's festoon props (phases.json, yard 'night'); the website now
# only adds their light at night and makes these bulbs glow (index.html, 'festoon').
#
# A string: black cable 10 mm, sagging as a parabola between its ends; bulbs 80 mm on 60 mm drops; a free end on a
# 32 mm steel pole on a 0.44 m weighted base. Layers Festoon_Wire / Festoon_Bulbs / Festoon_Poles under each
# workshop; one group per string.
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'festoons'
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

STAGES = {'w6': '09_Workshops::w6_garden_cinema', 'w7': '09_Workshops::w7_fire_circle',
          'w8': '09_Workshops::w8_shelter_table', 'open': '09_Workshops::open_festoons'}
LY = {}
for st, root in STAGES.items():
    LY[st + ' wire'] = layer(root + '::Festoon_Wire', Color.FromArgb(28, 28, 28), 'AU6 Plastic black')
    LY[st + ' bulb'] = layer(root + '::Festoon_Bulbs', Color.FromArgb(255, 226, 170),
                             rmat('AU6 Festoon bulb', (255, 232, 190), 0.6))
    LY[st + ' pole'] = layer(root + '::Festoon_Poles', Color.FromArgb(52, 54, 56), rmat('AU6 Festoon pole', (52, 54, 56), 0.3))

# (stage, label, from [s, n, z], to [s, n, z], sag, bulbs, pole at the 'from' end, pole at the 'to' end)
STRINGS = [
    ('w6', 'cinema, lean-to to west wall', (-10.0, 9.1, 2.45), (-7.6, 13.55, 3.0), 0.35, 12, False, False),
    ('w6', 'cinema, west wall to pole', (-2.2, 13.55, 3.0), (-1.7, 7.9, 2.6), 0.40, 12, False, True),
    ('w6', 'cinema, behind the back row', (-1.7, 7.9, 2.6), (-8.4, 7.3, 2.6), 0.45, 12, False, True),
    ('w7', 'fire circle', (0.05, 0.05, 2.7), (-3.4, 4.3, 2.6), 0.35, 12, False, True),
    ('w8', 'shelter roof', (-7.2, -3.3, 2.4), (-1.7, -3.3, 2.4), 0.12, 11, False, False),
    ('open', 'across the yard 1', (3.0, 0.05, 2.8), (5.0, 13.55, 3.0), 0.60, 22, False, False),
    ('open', 'across the yard 2', (9.5, 0.05, 2.8), (8.5, 13.55, 3.0), 0.60, 22, False, False),
]
STAGE_TAG = {'w6': 'W6', 'w7': 'W7', 'w8': 'W8', 'open': 'Opening'}
R_WIRE, R_BULB, DROP, R_POLE = 0.005, 0.04, 0.06, 0.016
poles_done = set()


def at(a, b, sag, u):
    return P(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u - sag * 4 * u * (1 - u))


# cable, holders and bulbs are light meshes (a 6-sided cable, 10-sided bulbs), not NURBS: as Breps their render
# meshes came to ~960 triangles a bulb, 120 000 for the strings, more than the rest of the yard's furniture
meshes = {}                                      # (group, layer key, name) -> rg.Mesh
mesh_order = []


def put_mesh(m, key, name, group):
    k = (group, key, name)
    if k not in meshes:
        meshes[k] = rg.Mesh()
        mesh_order.append(k)
    meshes[k].Append(m)


for st, label, a, b, sag, nb, pole_a, pole_b in STRINGS:
    g = 'Festoon, %s (%s)' % (label, STAGE_TAG[st])
    pts = [at(a, b, sag, i / 24.0) for i in range(25)]
    crv = rg.Curve.CreateInterpolatedCurve(pts, 3)
    put_mesh(rg.Mesh.CreateFromCurvePipe(crv, R_WIRE, 6, 24, rg.MeshPipeCapStyle.None, True, None),
             st + ' wire', 'festoon cable', g)
    for i in range(1, nb):
        p = at(a, b, sag, float(i) / nb)
        holder = rg.Cylinder(rg.Circle(rg.Plane(p - rg.Vector3d(0, 0, DROP), rg.Vector3d.ZAxis), 0.008), DROP)
        put_mesh(rg.Mesh.CreateFromCylinder(holder, 1, 6), st + ' wire', 'festoon bulb holder', g)
        put_mesh(rg.Mesh.CreateFromSphere(rg.Sphere(p - rg.Vector3d(0, 0, DROP + R_BULB * 0.8), R_BULB), 10, 6),
                 st + ' bulb', 'festoon bulb', g)
    for end, has in ((a, pole_a), (b, pole_b)):
        if not has or (end[0], end[1]) in poles_done:
            continue
        poles_done.add((end[0], end[1]))
        put(rod(P(end[0], end[1], 0.06), P(end[0], end[1], end[2] + 0.08), R_POLE), st + ' pole', 'festoon pole', g)
        base = rg.Cylinder(rg.Circle(rg.Plane(P(end[0], end[1], 0.0), rg.Vector3d.ZAxis), 0.22), 0.06).ToBrep(True, True)
        put(base, st + ' pole', 'festoon pole base', g)

made, fails, gids = add_pieces(TAG, LY)
for k in mesh_order:
    gname, key, name = k
    m = meshes[k]
    m.Normals.ComputeNormals()
    m.Compact()
    at_ = Rhino.DocObjects.ObjectAttributes()
    at_.LayerIndex = LY[key]
    at_.Name = name
    at_.SetUserString('build', TAG)
    if gname not in gids:
        gids[gname] = group_for(gname)
    at_.AddToGroup(gids[gname])
    if doc.Objects.AddMesh(m, at_) == System.Guid.Empty:
        fails.append('add failed: %s / %s' % (key, name))
    else:
        made[key] = made.get(key, 0) + 1
doc.Views.Redraw()
report = ['strings: %d, objects: %s' % (len(gids), ', '.join('%s %d' % kv for kv in sorted(made.items())))] + fails
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_festoons_log.txt', 'w') as f:
    f.write('\n'.join(report))
