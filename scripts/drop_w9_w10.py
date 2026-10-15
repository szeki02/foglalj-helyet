# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - one-off, 2026-10-15 (user: "Delete the Willow garden and northern podium stages. ...
# Shrink the size of the cars"). Re-runnable.
#
# 1. The stages w9 (willow garden) and w10 (north platform) are gone: their empty stage layers are deleted, and the W8
#    copies of the fire circle furniture, packed away "from w9" on, are now packed away from the Opening
#    ('Stored_from_w9' -> 'Stored_from_open'), the next stage after the shelter table.
# 2. The street's parked-car proxies (D5_proxy::Cars) are scaled to 80 % about their centre on the ground, like the
#    yard's cars (build_w5_parked_cars.py). User text 'au6_scale' records it, so a re-run doesn't shrink them again.
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc

doc = sc.doc
log = []

for top in ('09_Workshops', '10_Removed'):
    for leaf in ('w9_willow_garden', 'w10_north_platform'):
        i = doc.Layers.FindByFullPath(top + '::' + leaf, -1)
        if i >= 0:
            lay = doc.Layers[i]
            if lay.GetChildren() or doc.Objects.FindByLayer(lay):
                log.append('NOT deleted (not empty): ' + lay.FullPath)
            else:
                doc.Layers.Delete(i, True)
                log.append('deleted ' + top + '::' + leaf)

i = doc.Layers.FindByFullPath('09_Workshops::w8_shelter_table::Stored_from_w9', -1)
if i >= 0:
    lay = doc.Layers[i]
    lay.Name = 'Stored_from_open'
    doc.Layers.Modify(lay, i, True)
    n = 0
    for c in lay.GetChildren() or []:
        for o in doc.Objects.FindByLayer(c) or []:
            if o.Attributes.GetUserString('stored_in') == 'w9':
                a = o.Attributes.Duplicate()
                a.SetUserString('stored_in', 'open')
                doc.Objects.ModifyAttributes(o, a, True)
                n += 1
    log.append('w8 copies now Stored_from_open (%d objects retagged)' % n)

li = doc.Layers.FindByFullPath('D5_proxy::Cars', -1)
scaled = 0
for o in list(doc.Objects.FindByLayer(doc.Layers[li]) or []):
    if o.Attributes.GetUserString('au6_scale'):
        continue
    bb = o.Geometry.GetBoundingBox(True)
    c = rg.Point3d((bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2, bb.Min.Z)
    oid = doc.Objects.Transform(o, rg.Transform.Scale(c, 0.8), True)
    no = doc.Objects.FindId(oid)
    a = no.Attributes.Duplicate()
    a.SetUserString('au6_scale', '0.8')
    doc.Objects.ModifyAttributes(no, a, True)
    scaled += 1
log.append('street car proxies scaled to 80%%: %d' % scaled)
doc.Views.Redraw()
print('\n'.join(log))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_drop_w9_w10_log.txt', 'w') as f:
    f.write('\n'.join(log))
