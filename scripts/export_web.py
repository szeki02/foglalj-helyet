# -*- coding: utf-8 -*-
# CPython 3 + rhino3dm - exports the courtyard model's cached render meshes for the web viewer (web/index.html).
# Run headless (no Rhino needed):
#   <python with rhino3dm> scripts/export_web.py [path/to/model.3dm]
# Writes web/model/manifest.json + web/model/geometry.b64.txt (base64 of the packed binary buffers).
#
# Meshes are merged per (layer, workshop zone). Small courtyard elements (layers 02_/03_/04_) whose plan centre
# falls inside a zone rectangle of web/phases.json are tagged with that zone, so the viewer can highlight them.
# Proposed geometry: put it on sub-layers of '09_Workshops' named after a phase id (e.g. '09_Workshops::w3_seats');
# the viewer shows it from that phase onward. Existing elements a workshop takes away live on
# '10_Removed::<phase id>_...' (moved there, not deleted); the viewer shows them until that phase.
#
# Axes: Rhino Z-up metres -> three.js Y-up, centred on the yard: (x, y, z) -> (x - cx, z, -(y - cy)).
import array
import base64
import json
import math
import os
import struct
import sys

import rhino3dm as r

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'rhino', 'Alfoldi6_courtyard_site.3dm')
OUT = os.path.join(ROOT, 'web', 'model')
PHASES = os.path.join(ROOT, 'web', 'phases.json')

# yard frame (same as build_pavilion.py / build_garden.py)
C_WORLD = (-10.31, -19.80)
U = (-0.33761, 0.94128)
V = (0.94130, 0.33757)
L = 16 * 1.157

CONTEXT_RADIUS = 160.0          # m around the yard centre for OSM massing
ZONE_MAX_DIAG = 12.0            # larger objects (ground sheets, big crowns) are never zone-tagged

# objects kept off the website (they were hidden in Rhino on purpose): replaced or duplicated building masses
WEB_HIDDEN = {
    '4bd71e7f-0fbf-4525-a83b-f49db7b1c319',          # 07_OSM_Context::Buildings_3D_Replaced
    'ab06df41-b5c5-4e40-a70a-85fecfa71c54',          # 01_Existing_Buildings: Alföldi utca 6-8 (OSM mass)
    '16a9a017-8f8b-4cd9-9994-d290be882978',          # 07_OSM_Context::Buildings_3D: Vay Ádám utca 6
}
SKIP_PREFIXES = (
    'Layer 02', 'ADDITIONS::_superseded_placeholder', 'D5_cameras', '06_Reference',
    '07_OSM_Context::Context_Ground', '07_OSM_Context::Buildings_3D_Replaced',
)
ZONE_LAYER_PREFIXES = ('02_Courtyard_Ground::', '03_Vegetation::', '04_Furniture_Elements::')
ZONE_LAYER_EXCLUDE = ('04_Furniture_Elements::Fire_Ladder', '03_Vegetation::Tree_Crowns',
                      '03_Vegetation::Tree_Trunks_Branches')

# layers exported one mesh per object, so the viewer can fade a single tree or roof that blocks the view
SPLIT_LAYERS = (
    '03_Vegetation::Tree_Crowns', '03_Vegetation::Tree_Trunks_Branches', 'D5_proxy::Street_Trees',
    '04_Furniture_Elements::Sheds::Corrugated_Roofs', '04_Furniture_Elements::Shelter_3_Gable::Polycarbonate_Roof',
    '04_Furniture_Elements::WC_Entrance_Canopy',
)

# workshop layers exported one mesh per Rhino group (each mobile bed, bench + bed, table is a group)
# (mobile garden w5, garden cinema w6, fire circle w7 since the reorder of 2026-10-14; shelter table w8)
SPLIT_BY_GROUP = ('09_Workshops::w5_mobile_garden', '10_Removed::w5_mobile_garden', '09_Workshops::w6_garden_cinema',
                  '09_Workshops::w7_fire_circle', '09_Workshops::w8_shelter_table')

# viewer groups -> what the layer toggles in the UI act on
GROUPS = [
    ('proposed', ('09_Workshops',)),
    ('pavilion', ('ADDITIONS',)),
    ('yard', ('02_', '03_', '04_', '10_Removed')),
    ('buildings', ('01_',)),
    ('street', ('05_', '08_', 'D5_proxy')),
    ('context', ('07_',)),
]


# vertex-clustering cell size (m) for heavy smooth layers; everything else is exported as meshed in Rhino
DECIMATE = {
    '03_Vegetation::Shrubs': 0.16,
    '03_Vegetation::Planter_Plants': 0.09,
    '03_Vegetation::Tree_Crowns': 0.35,
    '02_Courtyard_Ground::Soil_Mounds': 0.15,
    'D5_proxy::Street_Trees': 0.35,
}


def world_from_sn(s, n):
    a = L - s
    return (C_WORLD[0] + a * U[0] - n * V[0], C_WORLD[1] + a * U[1] - n * V[1])


def sn_from_world(x, y):
    dx, dy = x - C_WORLD[0], y - C_WORLD[1]
    return L - (dx * U[0] + dy * U[1]), -(dx * V[0] + dy * V[1])


def group_of(path):
    for g, prefixes in GROUPS:
        if path.startswith(prefixes):
            return g
    return 'context'


def meshes_of(geom):
    if isinstance(geom, r.Mesh):
        return [geom]
    if isinstance(geom, r.Extrusion):
        m = geom.GetMesh(r.MeshType.Any)
        return [m] if m is not None else []
    if isinstance(geom, r.Brep):
        out = []
        for i in range(len(geom.Faces)):
            m = geom.Faces[i].GetMesh(r.MeshType.Any)
            if m is not None:
                out.append(m)
        return out
    return []


def cluster(pos, nrm, idx, cell):
    """Vertex-clustering decimation: snap vertices to a grid, average them, drop collapsed triangles."""
    remap, acc = {}, []
    new_of = array.array('I', [0]) * (len(pos) // 3)
    for i in range(len(pos) // 3):
        x, y, z = pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]
        k = (int(math.floor(x / cell)), int(math.floor(y / cell)), int(math.floor(z / cell)))
        j = remap.get(k)
        if j is None:
            j = remap[k] = len(acc)
            acc.append([0.0] * 7)
        a = acc[j]
        a[0] += x; a[1] += y; a[2] += z
        a[3] += nrm[3 * i]; a[4] += nrm[3 * i + 1]; a[5] += nrm[3 * i + 2]
        a[6] += 1
        new_of[i] = j
    p2, n2, i2 = array.array('f'), array.array('f'), array.array('I')
    for a in acc:
        c = a[6]
        p2.extend((a[0] / c, a[1] / c, a[2] / c))
        ln = math.sqrt(a[3] ** 2 + a[4] ** 2 + a[5] ** 2) or 1.0
        n2.extend((a[3] / ln, a[4] / ln, a[5] / ln))
    seen = set()
    for t in range(0, len(idx), 3):
        a, b, c = new_of[idx[t]], new_of[idx[t + 1]], new_of[idx[t + 2]]
        if a == b or b == c or a == c:
            continue
        key = tuple(sorted((a, b, c)))
        if key in seen:
            continue
        seen.add(key)
        i2.extend((a, b, c))
    return p2, n2, i2


def quantise(pos, nrm, idx):
    """positions -> int16 per part (offset + scale), normals -> int8, indices -> uint16 when they fit."""
    lo = [min(pos[k::3]) for k in range(3)]
    hi = [max(pos[k::3]) for k in range(3)]
    scale = [max(hi[k] - lo[k], 1e-6) / 65535.0 for k in range(3)]
    q = array.array('h', (int(round((pos[i] - lo[i % 3]) / scale[i % 3])) - 32768 for i in range(len(pos))))
    qn = array.array('b', (max(-127, min(127, int(round(v * 127)))) for v in nrm))
    qi = array.array('H' if len(pos) // 3 < 65536 else 'I', idx)
    return q, qn, qi, lo, scale


def material_of(model, layer, obj_idx=-1):
    idx = obj_idx if obj_idx >= 0 else layer.RenderMaterialIndex
    if idx is not None and 0 <= idx < len(model.Materials):
        mt = model.Materials[idx]
        d = mt.DiffuseColor
        return {'name': mt.Name, 'color': [d[0], d[1], d[2]], 'opacity': round(1.0 - mt.Transparency, 3)}
    c = layer.Color
    return {'name': layer.Name, 'color': [c[0], c[1], c[2]], 'opacity': 1.0}


def main():
    with open(PHASES, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    zones = cfg['zones']
    phase_ids = [p['id'] for p in cfg['phases']]

    cs, cn = 4.6, 4.5                              # yard centre in (s, n)
    cx, cy = world_from_sn(cs, cn)

    model = r.File3dm.Read(SRC)
    layers = model.Layers
    buckets = {}                                   # (layer index, zone) -> dict(pos, nrm, idx)
    skipped = {'hidden': 0, 'no_mesh': 0, 'far': 0}

    for obj in model.Objects:
        attr = obj.Attributes
        geom = obj.Geometry
        if not isinstance(geom, (r.Brep, r.Extrusion, r.Mesh)):
            continue
        li = attr.LayerIndex
        layer = layers.FindIndex(li)
        path = layer.FullPath
        # Hiding objects in Rhino is working-view state and doesn't take them off the website (2026-10-15: posters,
        # cars, plants and street trees hidden while working); only the objects in WEB_HIDDEN are left out on purpose.
        # Workshop layers are exported whatever is switched on: the website shows them stage by stage.
        workshop_layer = path.startswith(('09_Workshops::', '10_Removed::'))
        if str(attr.Id) in WEB_HIDDEN:
            skipped['hidden'] += 1
            continue
        if path.startswith(SKIP_PREFIXES) or path == 'ADDITIONS' or path.startswith('09_Workshops::_zones'):
            continue
        if not layer.Visible and not workshop_layer:
            continue
        mat_idx = -1
        if attr.MaterialSource == r.ObjectMaterialSource.MaterialFromObject:
            mat_idx = attr.MaterialIndex
        bb = geom.GetBoundingBox()
        mx, my = (bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2
        if path.startswith('07_') and math.hypot(mx - cx, my - cy) > CONTEXT_RADIUS:
            skipped['far'] += 1
            continue

        zone = ''
        if path.startswith(ZONE_LAYER_PREFIXES) and not path.startswith(ZONE_LAYER_EXCLUDE):
            diag = math.hypot(bb.Max.X - bb.Min.X, bb.Max.Y - bb.Min.Y)
            if diag <= ZONE_MAX_DIAG:
                s, n = sn_from_world(mx, my)
                for zid, z in zones.items():
                    if any(r['s'][0] <= s <= r['s'][1] and r['n'][0] <= n <= r['n'][1] for r in [z] + z.get('more', [])):
                        zone = zid
                        break

        ms = meshes_of(geom)
        if not ms:
            skipped['no_mesh'] += 1
            print('  no render mesh (shade it in Rhino and save): %s / %s' % (path, attr.Name))
            continue
        split = str(attr.Id) if path.startswith(SPLIT_LAYERS) else ''
        if not split and path.startswith(SPLIT_BY_GROUP):         # one mesh per bed / table, so the viewer can
            groups = attr.GetGroupList()                          # bring each in or out whole
            if groups is not None and len(groups):
                grp = model.Groups.FindIndex(groups[0])
                split = 'g:' + (grp.Name if grp is not None and grp.Name else str(groups[0]))
        if not split and attr.GetUserString('piece'):             # e.g. 'table A' / 'table B' on a shared layer
            split = 'u:' + attr.GetUserString('piece')
        b = buckets.setdefault((li, zone, mat_idx, split), {'pos': array.array('f'), 'nrm': array.array('f'), 'idx': array.array('I')})
        pos, nrm, idx = b['pos'], b['nrm'], b['idx']
        for m in ms:
            base = len(pos) // 3
            vs = m.Vertices
            nv = len(vs)
            ns = m.Normals
            has_n = len(ns) == nv
            for i in range(nv):
                p = vs[i]
                pos.extend((p.X - cx, p.Z, -(p.Y - cy)))
                if has_n:
                    q = ns[i]
                    nrm.extend((q.X, q.Z, -q.Y))
                else:
                    nrm.extend((0.0, 0.0, 0.0))
            fs = m.Faces
            for i in range(fs.Count):
                a, b2, c, d = fs[i]
                idx.extend((base + a, base + b2, base + c))
                if c != d:
                    idx.extend((base + a, base + c, base + d))

    os.makedirs(OUT, exist_ok=True)
    blob = bytearray()
    parts = []
    for (li, zone, mat_idx, split), b in sorted(buckets.items(), key=lambda kv: (layers.FindIndex(kv[0][0]).FullPath,) + kv[0][1:]):
        if not b['idx']:
            continue
        layer = layers.FindIndex(li)
        path = layer.FullPath
        mat = material_of(model, layer, mat_idx)
        phase = removed = ''
        if path.startswith(('09_Workshops::', '10_Removed::')):
            leaf = path.split('::')[1].lower()
            pid = next((p for p in phase_ids if leaf == p.lower() or leaf.startswith(p.lower() + '_')), '')
            if path.startswith('09_'):
                phase = pid
            else:
                removed = pid
        # pieces a later workshop packs away again: '...::Stored_from_w4::<leaf>' -> until 'w4'
        until = next((seg[len('Stored_from_'):] for seg in path.split('::')[2:] if seg.startswith('Stored_from_')), '')
        until = next((p for p in phase_ids if until.lower() == p.lower() or until.lower().startswith(p.lower() + '_')), '') if until else ''
        # pieces moved elsewhere for one workshop only (a copy stands in for them there): '...::Away_in_w6::<leaf>'
        away = next((seg[len('Away_in_'):] for seg in path.split('::')[2:] if seg.startswith('Away_in_')), '')
        away = next((p for p in phase_ids if away.lower() == p.lower() or away.lower().startswith(p.lower() + '_')), '') if away else ''
        pos, nrm, idx = b['pos'], b['nrm'], b['idx']
        # workshop copies / removed originals keep the leaf name of their source layer (e.g. ...::Planter_Plants)
        cell = DECIMATE.get(path) or next((c for p_, c in DECIMATE.items()
                                           if path.startswith(('09_', '10_')) and path.endswith('::' + p_.split('::')[-1])), None)
        if cell:
            pos, nrm, idx = cluster(pos, nrm, idx, cell)
            if not idx:
                continue
        q, qn, qi, lo, scale = quantise(pos, nrm, idx)
        entry = {'layer': path, 'group': group_of(path), 'zone': zone, 'phase': phase, 'removed': removed, 'until': until, 'away': away,
                 'piece': split[2:] if split.startswith(('g:', 'u:')) else '', 'material': mat,
                 'pmin': [round(v, 5) for v in lo], 'pscale': [v for v in scale], 'itype': qi.typecode}
        for key, arr in (('position', q), ('normal', qn), ('index', qi)):
            while len(blob) % 4:
                blob.append(0)
            entry[key] = [len(blob), len(arr)]
            blob.extend(arr.tobytes())
        parts.append(entry)

    sw = [world_from_sn(s, n) for s, n in ((-14.4, -4.6), (23.6, -4.6), (23.6, 13.6), (-14.4, 13.6))]
    manifest = {
        'source': os.path.basename(SRC),
        'units': 'm',
        'origin_world': [cx, cy],
        'frame': {'C': C_WORLD, 'U': U, 'V': V, 'L': L},
        'yard_outline': [[x - cx, -(y - cy)] for x, y in sw],
        'parts': parts,
        'bytes': len(blob),
    }
    # base64 text so static hosts that only serve web media types (e.g. claude.ai artifacts) accept it
    b64 = base64.b64encode(bytes(blob))
    manifest['b64_bytes'] = len(b64)
    with open(os.path.join(OUT, 'geometry.b64.txt'), 'wb') as f:
        f.write(b64)
    stale = os.path.join(OUT, 'geometry.bin')
    if os.path.exists(stale):
        os.remove(stale)
    with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(',', ':'))

    tris = sum(p['index'][1] for p in parts) // 3
    tagged = {}
    for p in parts:
        if p['zone']:
            tagged[p['zone']] = tagged.get(p['zone'], 0) + p['index'][1] // 3
    print('parts %d  triangles %d  bytes %.1f MB  skipped %s' % (len(parts), tris, len(blob) / 1e6, skipped))
    print('zone triangles', tagged)


if __name__ == '__main__':
    main()
