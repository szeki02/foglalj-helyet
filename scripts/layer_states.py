# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - named layer states for reviewing the workshop modifications.
# Re-run after every modification (new layers are only covered by states saved after they exist).
# Replaces all layer states whose names start with 'AU6 '; the user's current layer visibility is restored at the end.
#
#   AU6 00 Preexistence        survey state: everything as found, no workshop layers
#   AU6 00 Zones               survey state + the six workshop zone outlines
#   AU6 0N WN <title>          cumulative: the yard after workshop N (additions 1..N on, removals 1..N off)
#   AU6 0N WN changes          review: survey state + only workshop N's additions, its removed elements shown
#                              (on 10_Removed, red) and its zone outline
#   Pieces a later workshop packs away again sit on a '...::Stored_from_w<M>::<leaf>' sublayer of the workshop that
#   made them, and are hidden in cumulative states from workshop M on.
#
# Layer convention (scripts/setup_workshop_layers.py): additions on 09_Workshops::w<N>_..., existing elements a
# workshop takes away moved (not deleted) to 10_Removed::w<N>_...
import Rhino
import scriptcontext as sc
from Rhino.DocObjects.Tables import RestoreLayerProperties

doc = sc.doc
PREFIX = 'AU6 '
ALWAYS_HIDDEN = ('Layer 02',)          # hidden in the survey file
TMP = '_au6_restore_tmp'

layers = [L for L in doc.Layers if not L.IsDeleted]
work = sorted(set(L.FullPath.split('::')[1] for L in layers
                  if L.FullPath.startswith('09_Workshops::') and not L.FullPath.split('::')[1].startswith('_')))


def stage_no(leaf):
    return int(leaf.split('_')[0][1:])


def title(leaf):
    return leaf.split('_', 1)[1].replace('_', ' ').capitalize()


def stored_from(path):
    """'09_Workshops::w2_...::Stored_from_w4::Work_Table_Tops' -> 4: pieces a later workshop packs away again"""
    for seg in path.split('::')[2:]:
        if seg.startswith('Stored_from_w'):
            return int(seg[len('Stored_from_w'):].split('_')[0])
    return None


def away_in(path):
    """'09_Workshops::w5_...::Away_in_w6::Chair_Crates_Red' -> 6: pieces moved elsewhere for workshop 6 only (a copy
    stands in their place on that workshop's layers); back from workshop 7 on"""
    for seg in path.split('::')[2:]:
        if seg.startswith('Away_in_w'):
            return int(seg[len('Away_in_w'):].split('_')[0])
    return None


def visible_in(path, adds, removes, zones, upto=None):
    """adds / removes: sets of workshop leaf names whose additions are shown / whose removed elements are hidden;
    upto: the workshop number of a cumulative state (pieces stored away by then are hidden)"""
    if path == '09_Workshops':
        return bool(adds) or zones
    if path == '09_Workshops::_zones' or path.startswith('09_Workshops::_zones::'):
        return zones
    if path.startswith('09_Workshops::'):
        st = stored_from(path)
        if st is not None and upto is not None and st <= upto:
            return False
        aw = away_in(path)
        if aw is not None and upto is not None and aw == upto:
            return False
        return path.split('::')[1] in adds
    if path == '10_Removed':
        return True
    if path.startswith('10_Removed::'):
        return path.split('::')[1] not in removes
    return not path.startswith(ALWAYS_HIDDEN)


def apply(adds, removes, zones, upto=None):
    for L in layers:
        v = visible_in(L.FullPath, adds, removes, zones, upto)
        lay = doc.Layers[L.Index]
        lay.IsVisible = v
        lay.SetPersistentVisibility(v)
        doc.Layers.Modify(lay, L.Index, True)


def save(name):
    if name in list(doc.NamedLayerStates.Names):
        doc.NamedLayerStates.Delete(name)
    doc.NamedLayerStates.Save(name)


# keep the user's view of things
if TMP in doc.NamedLayerStates.Names:
    doc.NamedLayerStates.Delete(TMP)
doc.NamedLayerStates.Save(TMP)
current = doc.Layers.CurrentLayerIndex
doc.Layers.SetCurrentLayerIndex(doc.Layers.FindByFullPath('Default', -1), True)   # a hidden layer can't be current

for n in list(doc.NamedLayerStates.Names):
    if n.startswith(PREFIX):
        doc.NamedLayerStates.Delete(n)

saved = []
doc.Views.RedrawEnabled = False                  # ~14 states x ~150 layers: redrawing each change is what is slow
try:
    apply(set(), set(), False); save(PREFIX + '00 Preexistence'); saved.append('00 Preexistence')
    apply(set(), set(), True);  save(PREFIX + '00 Zones');    saved.append('00 Zones')
    for leaf in work:
        k = stage_no(leaf)
        upto = set(w for w in work if stage_no(w) <= k)
        name = '%02d W%d %s' % (k, k, title(leaf))
        apply(upto, upto, False, k); save(PREFIX + name); saved.append(name)
        name = '%02d W%d changes' % (k, k)
        apply(set([leaf]), set(), True); save(PREFIX + name); saved.append(name)
    doc.NamedLayerStates.Restore(TMP, RestoreLayerProperties.All)
    doc.NamedLayerStates.Delete(TMP)
    doc.Layers.SetCurrentLayerIndex(current, True)
finally:
    doc.Views.RedrawEnabled = True
doc.Views.Redraw()
print('layer states: ' + ' | '.join(saved))
