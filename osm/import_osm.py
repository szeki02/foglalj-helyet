# -*- coding: utf-8 -*-
# IronPython 2.7 - imports OSM JSON (Overpass, out body geom) into the active Rhino doc
import io, json, math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

HERE = OSM_DIR  # injected by caller
PATH = HERE + "/alfoldi6_osm.json"
SITE_REL = 3332603
FLOOR_H = 3.5      # Budapest tenement floor-to-floor
DEFAULT_LEVELS = 4  # fallback when OSM has no height / levels
doc = sc.doc
tol = doc.ModelAbsoluteTolerance

# .NET read -> real unicode (IronPython's json + io.open mangles UTF-8)
data = json.loads(System.IO.File.ReadAllText(PATH, System.Text.Encoding.UTF8))
els = data['elements']


def fx(s):
    # IronPython json decodes UTF-8 bytes as latin-1 -> undo that
    try:
        return s.encode('latin-1').decode('utf-8')
    except Exception:
        return s


for e in els:
    if 'tags' in e:
        e['tags'] = dict((fx(k), fx(v)) for k, v in e['tags'].items())
site = [e for e in els if e['type'] == 'relation' and e['id'] == SITE_REL][0]

# ---- projection: local tangent plane, origin = centroid of the site outer ring
ring = []
for m in site['members']:
    if m.get('role') == 'outer':
        ring += m['geometry'][:-1]
LAT0 = sum(p['lat'] for p in ring) / len(ring)
LON0 = sum(p['lon'] for p in ring) / len(ring)
A = 6378137.0
E2 = 0.00669437999014
s = math.sin(math.radians(LAT0))
N = A / math.sqrt(1 - E2 * s * s)
M = A * (1 - E2) / math.pow(1 - E2 * s * s, 1.5)
KX = math.radians(1) * N * math.cos(math.radians(LAT0))
KY = math.radians(1) * M


def P(g):
    return rg.Point3d((g['lon'] - LON0) * KX, (g['lat'] - LAT0) * KY, 0)


# ---- layers
def layer(path, col):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx >= 0:
        return idx
    parts = path.split('::')
    parent = System.Guid.Empty
    if len(parts) > 1:
        pidx = layer('::'.join(parts[:-1]), Color.FromArgb(150, 150, 150))
        parent = doc.Layers[pidx].Id
    L = Rhino.DocObjects.Layer()
    L.Name = parts[-1]
    L.Color = col
    L.ParentLayerId = parent
    return doc.Layers.Add(L)


O = '07_OSM_Context::'
LY = {
    'bld': layer(O + 'Buildings_3D', Color.FromArgb(190, 190, 190)),
    'bldpart': layer(O + 'Building_Parts_3D', Color.FromArgb(190, 190, 190)),
    'foot': layer(O + 'Building_Footprints', Color.FromArgb(90, 90, 90)),
    'rd_main': layer(O + 'Roads_Main', Color.FromArgb(210, 70, 40)),
    'rd_res': layer(O + 'Roads_Residential', Color.FromArgb(230, 150, 60)),
    'rd_srv': layer(O + 'Roads_Service', Color.FromArgb(200, 180, 120)),
    'rd_ped': layer(O + 'Footways_Pedestrian', Color.FromArgb(160, 120, 160)),
    'tram': layer(O + 'Tram', Color.FromArgb(40, 40, 160)),
    'subway': layer(O + 'Subway_Underground', Color.FromArgb(120, 120, 220)),
    'platform': layer(O + 'Platforms', Color.FromArgb(100, 100, 180)),
    'green': layer(O + 'Green_Areas', Color.FromArgb(110, 170, 90)),
    'trees': layer(O + 'Trees', Color.FromArgb(40, 120, 40)),
    'water': layer(O + 'Water', Color.FromArgb(60, 140, 220)),
    'landuse': layer(O + 'Landuse_Other', Color.FromArgb(200, 170, 200)),
    'parking': layer(O + 'Parking', Color.FromArgb(150, 150, 200)),
    'labels': layer(O + 'Street_Labels', Color.FromArgb(60, 60, 60)),
    'site_b': layer('00_Site_Boundary', Color.Black),
    'site_bld': layer('01_Existing_Buildings', Color.FromArgb(120, 120, 120)),
    'court': layer('02_Courtyard_Ground', Color.FromArgb(170, 140, 100)),
}
doc.Layers[LY['subway']].IsVisible = False

# idempotent: remove anything a previous run of this importer created
old = [o.Id for o in doc.Objects if o.Attributes.GetUserString('osm_id') or o.Attributes.GetUserString('osm_import')]
for gid in old:
    doc.Objects.Delete(gid, True)
print('removed %d objects from previous import' % len(old))


def attrs(lyr, e=None, name=None):
    at = Rhino.DocObjects.ObjectAttributes()
    at.LayerIndex = LY[lyr]
    at.SetUserString('osm_import', '2026-10-13')
    if e is not None:
        t = e.get('tags', {})
        at.SetUserString('osm_id', '%s/%d' % (e['type'], e['id']))
        for k, v in t.items():
            at.SetUserString('osm:' + k, v)
        nm = name or t.get('name')
        if not nm and t.get('addr:street'):
            nm = u'%s %s' % (t.get('addr:street'), t.get('addr:housenumber', ''))
        if nm:
            at.Name = nm.strip()
    return at


def polyline(geom):
    pts = [P(g) for g in geom]
    pl = rg.Polyline(pts)
    pl.DeleteShortSegments(tol)
    if pl.Count < 2:
        return None
    return rg.PolylineCurve(pl)


def closed_rings(member_geoms):
    """join way pieces into closed planar rings"""
    crvs = [c for c in (polyline(g) for g in member_geoms) if c]
    if not crvs:
        return []
    joined = rg.Curve.JoinCurves(crvs, 0.01)
    out = []
    for c in joined:
        if not c.IsClosed and c.PointAtStart.DistanceTo(c.PointAtEnd) < 0.05:
            c.MakeClosed(0.05)
        if c.IsClosed:
            out.append(c)
    return out


def num(v):
    try:
        return float(str(v).replace(',', '.').replace('m', '').strip().split(';')[0])
    except Exception:
        return None


def heights(t):
    """returns (base, top, source)"""
    h = num(t.get('height'))
    lv = num(t.get('building:levels'))
    mh = num(t.get('min_height'))
    ml = num(t.get('building:min_level'))
    base = mh if mh is not None else (ml * FLOOR_H if ml is not None else 0.0)
    roof_lv = num(t.get('roof:levels')) or 0
    if h is not None:
        return base, h, 'height'
    if lv is not None:
        return base, (lv + roof_lv) * FLOOR_H, 'levels'
    b = t.get('building') or t.get('building:part') or ''
    if b in ('garage', 'garages', 'shed', 'hut', 'roof', 'carport', 'kiosk', 'toilets', 'container'):
        return base, 3.0, 'estimate-small'
    return base, DEFAULT_LEVELS * FLOOR_H, 'estimate-default'


def inside(outer, crv):
    pl = crv.TryGetPolyline()
    pts = list(pl[1])[:-1] if pl[0] else [crv.PointAtStart]
    return all(outer.Contains(p, rg.Plane.WorldXY, tol) != rg.PointContainment.Outside for p in pts)


def massing(outers, inners, base, top):
    """vertical extrusion of footprint (with courtyard holes); returns list of geometry"""
    res = []
    hgt = top - base
    if hgt <= 0.1:
        return res
    for o in outers:
        holes = [i for i in inners if inside(o, i)]
        if not holes:
            ex = rg.Extrusion.Create(o, hgt, True)
            if ex is not None and ex.GetBoundingBox(True).Min.Z < -hgt * 0.5:
                ex = rg.Extrusion.Create(o, -hgt, True)
            if ex is None:
                continue
            geo = ex
        else:
            faces = rg.Brep.CreatePlanarBreps([o] + holes, tol)
            if not faces:
                continue
            path = rg.LineCurve(rg.Point3d(0, 0, 0), rg.Point3d(0, 0, hgt))
            geo = faces[0].Faces[0].CreateExtrusion(path, True)
            if geo is None:
                continue
        if base:
            geo.Transform(rg.Transform.Translation(0, 0, base))
        res.append(geo)
    return res


stats = {}


def bump(k):
    stats[k] = stats.get(k, 0) + 1


# ---- members of building relations (to avoid duplicates)
rel_member_ways = set()
for e in els:
    if e['type'] == 'relation' and 'building' in e.get('tags', {}):
        for m in e.get('members', []):
            if m['type'] == 'way':
                rel_member_ways.add(m['ref'])

# building parts (to decide if an outline should be massed or only drawn)
part_pts = []
for e in els:
    if e['type'] == 'way' and 'building:part' in e.get('tags', {}):
        c = polyline(e['geometry'])
        if c:
            part_pts.append(rg.AreaMassProperties.Compute(c).Centroid if c.IsClosed else c.PointAtStart)


def has_parts(outers):
    for o in outers:
        for p in part_pts:
            if o.Contains(p, rg.Plane.WorldXY, tol) == rg.PointContainment.Inside:
                return True
    return False


ROAD = {
    'motorway': 'rd_main', 'trunk': 'rd_main', 'primary': 'rd_main', 'secondary': 'rd_main', 'tertiary': 'rd_main',
    'primary_link': 'rd_main', 'secondary_link': 'rd_main', 'tertiary_link': 'rd_main',
    'residential': 'rd_res', 'living_street': 'rd_res', 'unclassified': 'rd_res',
    'service': 'rd_srv', 'track': 'rd_srv',
    'pedestrian': 'rd_ped', 'footway': 'rd_ped', 'path': 'rd_ped', 'steps': 'rd_ped', 'cycleway': 'rd_ped',
    'platform': 'platform',
}
GREEN = set(['park', 'grass', 'garden', 'forest', 'wood', 'scrub', 'flowerbed', 'playground', 'pitch',
             'dog_park', 'fitness_station', 'meadow', 'village_green', 'tree_row', 'cemetery', 'recreation_ground'])

street_best = {}
add = doc.Objects

for e in els:
    t = e.get('tags', {})
    typ = e['type']

    # ---- site building (courtyard block)
    if typ == 'relation' and e['id'] == SITE_REL:
        outs = closed_rings([m['geometry'] for m in e['members'] if m.get('role') == 'outer'])
        ins = closed_rings([m['geometry'] for m in e['members'] if m.get('role') == 'inner'])
        base, top, src = heights(t)
        at = attrs('site_bld', e, u'Alföldi utca 6-8')
        at.SetUserString('height_m', '%.1f' % top)
        at.SetUserString('height_source', src)
        for g in massing(outs, ins, base, top):
            add.Add(g, at)
        for o in outs:
            add.AddCurve(o, attrs('site_b', e, u'Alföldi utca 6-8 - plot/building outline'))
        for i in ins:
            add.AddCurve(i, attrs('court', e, u'Courtyard outline (OSM inner ring)'))
            for b in rg.Brep.CreatePlanarBreps(i, tol) or []:
                add.AddBrep(b, attrs('court', e, u'Courtyard ground (OSM)'))
        bump('site')
        continue

    # ---- buildings
    if 'building' in t or 'building:part' in t:
        is_part = 'building:part' in t and 'building' not in t
        if typ == 'way':
            if e['id'] in rel_member_ways and not is_part:
                continue
            outs = closed_rings([e['geometry']])
            ins = []
        elif typ == 'relation':
            if 'building' not in t:
                continue
            outs = closed_rings([m['geometry'] for m in e.get('members', []) if m.get('role') == 'outer' and 'geometry' in m])
            ins = closed_rings([m['geometry'] for m in e.get('members', []) if m.get('role') == 'inner' and 'geometry' in m])
        else:
            continue
        if not outs:
            continue
        for o in outs:
            add.AddCurve(o, attrs('foot', e))
        for i in ins:
            add.AddCurve(i, attrs('foot', e))
        if not is_part and has_parts(outs):
            bump('outline_with_parts')
            continue
        base, top, src = heights(t)
        at = attrs('bldpart' if is_part else 'bld', e)
        at.SetUserString('height_m', '%.1f' % top)
        at.SetUserString('height_source', src)
        for g in massing(outs, ins, base, top):
            add.Add(g, at)
        bump('building_part' if is_part else 'building')
        bump('h_' + src)
        continue

    # ---- trees
    if typ == 'node' and t.get('natural') == 'tree':
        p = P(e)
        add.AddPoint(p, attrs('trees', e))
        add.AddCircle(rg.Circle(p, 3.0), attrs('trees', e))
        bump('tree')
        continue

    if typ != 'way' and typ != 'relation':
        continue

    # ---- linear transport
    if 'highway' in t and t['highway'] in ROAD and t.get('area') != 'yes':
        c = polyline(e['geometry'])
        if c:
            lyr = ROAD[t['highway']]
            if t.get('tunnel') == 'yes' or t.get('layer', '0').startswith('-'):
                lyr = 'subway' if lyr != 'rd_ped' else lyr
            add.AddCurve(c, attrs(lyr, e))
            bump('hw_' + lyr)
            nm = t.get('name')
            if nm and lyr in ('rd_main', 'rd_res', 'rd_ped'):
                L = c.GetLength()
                if nm not in street_best or L > street_best[nm][0]:
                    street_best[nm] = (L, c.PointAtNormalizedLength(0.5))
        continue
    if 'railway' in t:
        c = polyline(e['geometry']) if typ == 'way' else None
        if c:
            r = t['railway']
            lyr = 'tram' if r == 'tram' else ('subway' if r == 'subway' else 'platform')
            add.AddCurve(c, attrs(lyr, e))
            bump('rail_' + lyr)
        continue

    # ---- areas
    kind = t.get('leisure') or t.get('natural') or t.get('landuse') or t.get('amenity')
    lyr = None
    if kind in GREEN:
        lyr = 'green'
    elif kind == 'water':
        lyr = 'water'
    elif t.get('amenity') == 'parking':
        lyr = 'parking'
    elif 'landuse' in t:
        lyr = 'landuse'
    if lyr is None:
        continue
    if typ == 'way':
        geoms_o = [e['geometry']]
        geoms_i = []
    else:
        geoms_o = [m['geometry'] for m in e.get('members', []) if m.get('role') == 'outer' and 'geometry' in m]
        geoms_i = [m['geometry'] for m in e.get('members', []) if m.get('role') == 'inner' and 'geometry' in m]
    outs = closed_rings(geoms_o)
    if not outs:  # e.g. tree_row: open line
        for g in geoms_o:
            c = polyline(g)
            if c:
                add.AddCurve(c, attrs(lyr, e))
        bump('area_line_' + lyr)
        continue
    ins = closed_rings(geoms_i)
    for c in outs + ins:
        add.AddCurve(c, attrs(lyr, e))
    bump('area_' + lyr)

# ---- street labels
for nm, (L, p) in street_best.items():
    td = rg.TextDot(nm, rg.Point3d(p.X, p.Y, 1.0))
    td.FontHeight = 12
    add.AddTextDot(td, attrs('labels', None, nm))

# ---- georeference
doc.Strings.SetString('geo_origin_lat', '%.8f' % LAT0)
doc.Strings.SetString('geo_origin_lon', '%.8f' % LON0)
doc.Strings.SetString('geo_projection', 'local tangent plane (WGS84), origin = centroid of Alfoldi u. 6-8 outer ring, +Y = true north, metres')
doc.Strings.SetString('osm_source', 'OpenStreetMap contributors (ODbL), Overpass API, fetched 2026-10-13')
ea = doc.EarthAnchorPoint
ea.EarthBasepointLatitude = LAT0
ea.EarthBasepointLongitude = LON0
ea.ModelBasePoint = rg.Point3d.Origin
ea.ModelNorth = rg.Vector3d.YAxis
ea.ModelEast = rg.Vector3d.XAxis
doc.EarthAnchorPoint = ea

doc.Views.Redraw()
print('origin lat/lon: %.7f, %.7f' % (LAT0, LON0))
for k in sorted(stats):
    print('%s: %d' % (k, stats[k]))
print('street labels: %d' % len(street_best))
