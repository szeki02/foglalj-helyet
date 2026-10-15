# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - which windows of the buildings round the courtyard are lit on the evening stages (the film
# night, the fire circle). Re-runnable.
#
# Tags every pane on 01_Existing_Buildings::Facade_Window_Glass with user text 'piece' = 'lit:<k>' or 'dark:<k>':
# the exporter keeps each tagged pane as its own mesh, and the website makes the 'lit' ones glow at dusk
# (web/index.html, applyLight). About half are lit, spread over the walls and storeys, so it reads as a lived-in
# evening rather than a pattern.
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc

doc = sc.doc
C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)

# (name prefix, rounded s of the pane's north edge, rounded sill height) of the panes that are lit
LIT = [('WC tall window glass', -10.5, 1.7),
       ('light-well window (back wall) glass', -12.1, 6.3),
       ('light-well window (north side wall) glass', -12.9, 10.6),
       ('light-well window L2', -13.5, 7.5), ('light-well window L3', -13.6, 11.0),
       ('niche window glass', 15.2, 8.1), ('niche window glass', 15.2, 17.5),
       ('slot window glass', 5.1, 12.1), ('slot window glass', 5.1, 21.0)]

i = doc.Layers.FindByFullPath('01_Existing_Buildings::Facade_Window_Glass', -1)
lit = dark = 0
for k, o in enumerate(sorted(doc.Objects.FindByLayer(doc.Layers[i]), key=lambda o: str(o.Id))):
    nm = o.Attributes.Name or ''
    bb = o.Geometry.GetBoundingBox(PL)
    s0, z0 = round(L - bb.Max.X, 1), round(bb.Min.Z, 1)
    on = any(nm.startswith(p) and abs(s0 - s) < 0.15 and abs(z0 - z) < 0.15 for p, s, z in LIT)
    a = o.Attributes.Duplicate()
    a.SetUserString('piece', '%s:%d' % ('lit' if on else 'dark', k))
    doc.Objects.ModifyAttributes(o, a, True)
    if on:
        lit += 1
    else:
        dark += 1
print('windows lit at dusk: %d, dark: %d' % (lit, dark))
