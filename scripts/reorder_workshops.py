# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - one-off, 2026-10-14: the workshops reordered (user: "move the mural workshop right after
# the workshop space as well as the poster workshop"). Runs once (a document string records it).
#
#   old  ->  new                            old  ->  new
#   w3 mobile garden  -> w5                 w6 window posters -> w4
#   w4 garden cinema  -> w6                 w7 road mural     -> w3
#   w5 fire circle    -> w7                 w1, w2, w8-w10 unchanged
#
# The posters now come before the fire circle exists, so its chairs and tables can no longer stand out among the
# posters: the copies on '...w6_window_posters::Stored_from_w7::...' are deleted and the originals come back from
# '...w5_fire_circle::Away_in_w6::...' to their own layers (user text 'orig_layer'). 'Stored_from_w4' (packed for the
# cinema) becomes 'Stored_from_w6', 'Stored_from_w5' (packed for the fire circle) 'Stored_from_w7'; group labels
# '(W3)'..'(W7)' follow the same map.
import re
import Rhino
import scriptcontext as sc

doc = sc.doc
KEY, DONE = 'au6_stage_order', 'mural+posters after workshop space'
STAGES = {'w3_mobile_garden': 'w5_mobile_garden', 'w4_garden_cinema': 'w6_garden_cinema',
          'w5_fire_circle': 'w7_fire_circle', 'w6_window_posters': 'w4_window_posters', 'w7_road_mural': 'w3_road_mural'}
SEGMENTS = {'Stored_from_w4': 'Stored_from_w6', 'Stored_from_w5': 'Stored_from_w7'}
GROUPS = {'3': '5', '4': '6', '5': '7', '6': '4', '7': '3'}
log = []


def rename(i, new):
    lay = doc.Layers[i]
    lay.Name = new
    doc.Layers.Modify(lay, i, True)


def delete_tree(path):
    i = doc.Layers.FindByFullPath(path, -1)
    if i < 0:
        return 0
    lay = doc.Layers[i]
    kids = [c.FullPath for c in (lay.GetChildren() or [])]
    n = 0
    for k in kids:
        n += delete_tree(k)
    for o in list(doc.Objects.FindByLayer(lay) or []):
        doc.Objects.Delete(o, True, True)
        n += 1
    doc.Layers.Delete(i, True)
    return n


if doc.Strings.GetValue(KEY) == DONE:
    log.append('already reordered')
else:
    # 1. the fire circle furniture shown among the posters: copies away, originals home
    log.append('poster-side copies deleted: %d' % delete_tree('09_Workshops::w6_window_posters::Stored_from_w7'))
    back = 0
    ai = doc.Layers.FindByFullPath('09_Workshops::w5_fire_circle::Away_in_w6', -1)
    if ai >= 0:
        for c in list(doc.Layers[ai].GetChildren() or []):
            for o in list(doc.Objects.FindByLayer(c) or []):
                orig = o.Attributes.GetUserString('orig_layer') or ''
                oi = doc.Layers.FindByFullPath(orig, -1)
                if oi < 0:
                    log.append('no home layer for %s (%s)' % (o.Attributes.Name, orig))
                    continue
                a = o.Attributes.Duplicate()
                a.LayerIndex = oi
                a.DeleteUserString('orig_layer')
                a.DeleteUserString('away_in')
                doc.Objects.ModifyAttributes(o, a, True)
                back += 1
        log.append('fire circle pieces back on their layers: %d; empty layers removed: %d'
                   % (back, delete_tree('09_Workshops::w5_fire_circle::Away_in_w6')))
    # 2. stage layers, through temporary names so no two ever clash
    for top in ('09_Workshops', '10_Removed'):
        for old in STAGES:
            i = doc.Layers.FindByFullPath(top + '::' + old, -1)
            if i >= 0:
                rename(i, '_tmp_' + old)
        for old, new in STAGES.items():
            i = doc.Layers.FindByFullPath(top + '::_tmp_' + old, -1)
            if i >= 0:
                rename(i, new)
                log.append('%s::%s -> %s' % (top, old, new))
    # 3. 'stored from' sublayers
    for lay in list(doc.Layers):
        if not lay.IsDeleted and lay.Name in SEGMENTS and lay.FullPath.startswith('09_Workshops::'):
            new = SEGMENTS[lay.Name]
            log.append('%s -> %s' % (lay.FullPath, new))
            rename(lay.Index, new)
    # 4. group labels (the group table can't be iterated directly: by index); the poster-side copies' groups are empty
    ng = gone = 0
    for i in range(doc.Groups.Count):
        g = doc.Groups.FindIndex(i)
        if g is None or not g.Name:
            continue
        if g.Name.endswith('by the posters (W6)'):
            doc.Groups.Delete(i)
            gone += 1
            continue
        m = re.search(r'\(W([3-7])\)$', g.Name)
        if m:
            doc.Groups.ChangeGroupName(i, g.Name[:m.start()] + '(W%s)' % GROUPS[m.group(1)])
            ng += 1
    log.append('groups relabelled: %d, empty ones removed: %d' % (ng, gone))
    doc.Strings.SetString(KEY, DONE)

doc.Views.Redraw()
print('\n'.join(log))
with open('C:/Users/David/DEV/Alfoldi_utca_6/scripts/_reorder_log.txt', 'w') as f:
    f.write('\n'.join(log))
