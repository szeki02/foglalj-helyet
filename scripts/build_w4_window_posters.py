# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 4 (window posters): posters made by the residents, pasted onto the lower windows
# of the machinery house (the glazed pavilion), facing the yard. Re-runnable.
#
# Brief (user, 2026-10-14): "decorating the machinery house windows with posters, areas highlighted in the additions
# layer". The highlights (on ADDITIONS, left there) cover the lower panes of the west facade, bays 07, 08 and 10-16
# (bay 09 is a door): each pane 0.98 x 1.82 m, z 0.33..2.15, glass at n -0.06..-0.04 behind 20 mm frames.
#
# Posters are stuck on the outside of the glass with wheat paste (washes off): 3 mm sheets at n -0.0395..-0.0365.
# Sizes B1 0.70 x 1.00, A1 0.594 x 0.841, A2 0.42 x 0.594, A3 0.297 x 0.42, in four arrangements that repeat along
# the facade (21 posters). Every poster is its own object with user text 'piece' = 'poster:<design>:<bay>-<k>', so the
# exporter keeps it as its own mesh and the website draws that design on it (web/index.html, posterTexture); in
# Rhino the layer colour stands for the design's main colour.
# Workshop 4 since 2026-10-14 (it was 6; scripts/reorder_workshops.py): it now comes before the fire circle, so the
# fire circle's chairs and tables no longer stand out among the posters (that section is gone, with its copies).
execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')

TAG = 'w6_posters'                                  # the tag of the first build, kept so a re-run finds its objects
STAGE = 'w4_window_posters'
ADD = '09_Workshops::' + STAGE

# ------------------------------------------------------------------ 0. the stage's layers
if doc.Layers.FindByFullPath(ADD, -1) < 0:         # normally made by setup_workshop_layers.py (re-run it after)
    layer(ADD, Color.FromArgb(201, 162, 39))
    layer('10_Removed::' + STAGE, Color.FromArgb(190, 60, 60))

# ------------------------------------------------------------------ 1. clean previous run
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)

# ------------------------------------------------------------------ 2. the panes (from the pavilion's own glass)
BAYS = ('07', '08', '10', '11', '12', '13', '14', '15', '16')
panes = {}
for o in doc.Objects.GetObjectList(ALL):
    nm = o.Attributes.Name or ''
    for b in BAYS:
        if nm == 'W bay %s lower glass' % b:
            bb = o.Geometry.GetBoundingBox(PL)
            panes[b] = (L - bb.Max.X, L - bb.Min.X, bb.Min.Z, bb.Max.Z)
missing = [b for b in BAYS if b not in panes]
if missing:
    raise Exception('panes not found: %s' % ', '.join(missing))

# ------------------------------------------------------------------ 3. layers, designs, arrangements
LY = {
    'red':    layer(ADD + '::Posters_Red', Color.FromArgb(200, 60, 50), rmat('AU6 Poster red', (200, 60, 50))),
    'yellow': layer(ADD + '::Posters_Yellow', Color.FromArgb(235, 190, 50), rmat('AU6 Poster yellow', (235, 190, 50))),
    'blue':   layer(ADD + '::Posters_Blue', Color.FromArgb(40, 80, 150), rmat('AU6 Poster blue', (40, 80, 150))),
    'green':  layer(ADD + '::Posters_Green', Color.FromArgb(60, 130, 80), rmat('AU6 Poster green', (60, 130, 80))),
    'cream':  layer(ADD + '::Posters_Cream', Color.FromArgb(240, 228, 205), rmat('AU6 Poster cream', (240, 228, 205))),
}
# design index -> (word, main colour); the same list is drawn by web/index.html (POSTER_DESIGNS)
DESIGNS = [('MOZI', 'blue'), (u'T\u0170Z', 'red'), ('KERT', 'green'), (u'M\u0170HELY', 'yellow'), ('LEVES', 'cream'),
           ('UDVAR', 'blue'), (u'EGY\u00dcTT', 'red'), (u'ALF\u00d6LDI 6', 'yellow'), ('NYITVA', 'green')]
SIZES = {'B1': (0.70, 1.00), 'A1': (0.594, 0.841), 'A2': (0.42, 0.594), 'A3': (0.297, 0.42)}
# arrangements: (size, u from the pane's north edge, v from its sill)
LAYOUTS = [
    [('A1', 0.19, 0.85), ('A3', 0.10, 0.25), ('A3', 0.55, 0.30)],
    [('B1', 0.14, 0.60)],
    [('A2', 0.06, 1.05), ('A2', 0.52, 0.95), ('A2', 0.28, 0.30)],
    [('A1', 0.19, 0.20), ('A3', 0.34, 1.25)],
]
N0, N1 = -0.0395, -0.0365                          # on the outside face of the glass, inside the frame's depth

fr = Frame(0, 0)
made = 0
d = 0
for i, b in enumerate(BAYS):
    s0, s1, z0, z1 = panes[b]
    gi = group_for('Window posters bay %s (W4)' % b)
    for k, (size, u, v) in enumerate(LAYOUTS[i % len(LAYOUTS)]):
        w, h = SIZES[size]
        if u + w > s1 - s0 + 1e-6 or v + h > z1 - z0 + 1e-6:
            raise Exception('poster %s-%d does not fit its pane' % (b, k))
        word, col = DESIGNS[d % len(DESIGNS)]
        a = Rhino.DocObjects.ObjectAttributes()
        a.LayerIndex = LY[col]
        a.Name = 'poster bay %s #%d %s (%s)' % (b, k + 1, word, size)
        a.SetUserString('build', TAG)
        a.SetUserString('piece', 'poster:%d:%s-%d' % (d % len(DESIGNS), b, k + 1))
        a.AddToGroup(gi)
        oid = doc.Objects.AddBrep(fr.box(s0 + u, s0 + u + w, N0, N1, z0 + v, z0 + v + h), a)
        if oid != System.Guid.Empty:
            doc.Objects.Find(oid).CreateMeshes(Rhino.Geometry.MeshType.Render,
                                               doc.GetMeshingParameters(doc.MeshingParameterStyle), False)
            made += 1
        d += 1

doc.Views.Redraw()
report = ['panes: %s' % ', '.join('%s s %.2f-%.2f' % (b, panes[b][0], panes[b][1]) for b in BAYS), 'posters: %d' % made]
print('\n'.join(report))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_w6_log.txt', 'w') as f:
    f.write('\n'.join(report))
