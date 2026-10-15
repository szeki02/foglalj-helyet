# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - layers for the proposed workshop additions + the workshop zone outlines.
# Re-runnable: deletes the outlines it created before (user text 'workshop_zones').
#
# Anything modelled on 09_Workshops::w<N>_... is exported by scripts/export_web.py and appears on the website's
# timeline from workshop N onward. Zones and colours mirror web/phases.json.
# Existing elements a workshop takes away are NOT deleted: they move to 10_Removed::w<N>_..., so the survey state
# can always be shown again (see scripts/layer_states.py).
import json
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
from System.Drawing import Color

doc = sc.doc
TAG = 'workshop_zones'
PHASES = 'C:/Users/David/DEV/Alfoldi_utca_6/web/phases.json'

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157


def W(s, n, z=0.0):
    return C_WORLD + U * (L - s) - V * n + rg.Vector3d(0, 0, z)


def hex_color(h):
    h = h.lstrip('#')
    return Color.FromArgb(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def layer(path, color, locked=False):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        parent_id = None
        if '::' in path:
            parent = path.rsplit('::', 1)[0]
            parent_id = doc.Layers[doc.Layers.FindByFullPath(parent, -1)].Id
        lay = Rhino.DocObjects.Layer()
        lay.Name = path.rsplit('::', 1)[-1]
        if parent_id:
            lay.ParentLayerId = parent_id
        lay.Color = color
        idx = doc.Layers.Add(lay)
    lay = doc.Layers[idx]
    lay.Color = color
    lay.IsLocked = locked
    doc.Layers.Modify(lay, idx, True)
    return idx


with open(PHASES) as f:
    cfg = json.load(f)

layer('09_Workshops', Color.FromArgb(90, 90, 90))
layer('10_Removed', Color.FromArgb(190, 60, 60))
zones_idx = layer('09_Workshops::_zones', Color.FromArgb(120, 120, 120))     # unlocked while rebuilding

ALL = Rhino.DocObjects.ObjectEnumeratorSettings()     # include objects on hidden / locked layers (layer states!)
ALL.HiddenObjects = True
ALL.LockedObjects = True
ALL.VisibleFilter = False
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)                 # quiet, ignore lock / hide modes

no = 0
made = []
for ph in cfg['phases']:
    if not ph.get('zone'):
        continue
    no += 1
    z = cfg['zones'][ph['zone']]
    col = hex_color(cfg['modes'][ph['modes'][0]]['color'])
    name = '%s_%s' % (ph['id'], ph['title'].lower().replace(' ', '_'))
    layer('09_Workshops::' + name, col)
    layer('10_Removed::' + name, Color.FromArgb(190, 60, 60))
    made.append(name)

    for r in [z] + z.get('more', []):                  # a workshop may work on several areas
        s0, s1 = r['s']; n0, n1 = r['n']
        crv = rg.PolylineCurve([W(s0, n0), W(s1, n0), W(s1, n1), W(s0, n1), W(s0, n0)])
        a = Rhino.DocObjects.ObjectAttributes()
        a.LayerIndex = zones_idx
        a.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
        a.ObjectColor = col
        a.Name = 'W%d zone - %s' % (no, r['label'])
        a.SetUserString('build', TAG)
        doc.Objects.AddCurve(crv, a)
        dot = rg.TextDot('W%d %s' % (no, r['label']), W((s0 + s1) / 2, (n0 + n1) / 2, 3.0))
        doc.Objects.AddTextDot(dot, a)

layer('09_Workshops::_zones', Color.FromArgb(120, 120, 120), locked=True)
doc.Views.Redraw()
print('layers: ' + ', '.join(made))
