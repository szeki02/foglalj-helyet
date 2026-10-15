# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - courtyard walls, ground surfaces, ramp/platform, street wall + gate,
# sheds, shelter, handrails and small elements of the Alfoldi u. 6 yard.
# Re-runnable: deletes everything it created before (user text 'courtyard_build').
#
# Frame: s = metres along the pavilion's west facade from its NORTH end (south +),
#        n = metres west of that facade line, z up.  Yard: s -14.4..23.6, n -4.6..13.6.
#
# Sources
#   plan anchors : OSM building faces (east n=-4.6, north s=-14.4, west n=13.6, street s~23.6)
#                  + user Layer 02 footprints (shelter, ramp zone, NW lean-to, brown shed, brick hut, street wall)
#   measured     : photogrammetry on photos 5/8 (north wall 16.3 m, white patch, west-wall niche column,
#                  gate/pillar heights), brick coursing in photo 15 (gate 1.8 m, wall 2.3 m, gate 2.9 m wide)
#   estimated    : west wall 18.5 m, east wall 19 m (>=17.5 measured), shed/shelter/ramp details from
#                  standard dimensions (door 0.9x2.0, risers 0.16, handrails 0.9/0.75)
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'courtyard_build'

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
XF = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, rg.Plane(C_WORLD, U, -V))


def P(s, n, z=0.0):
    return rg.Point3d(L - s, n, z)


# ------------------------------------------------------------------ key dimensions
N_E, S_N, N_W = -4.6, -14.4, 13.6          # east / north / west wall faces


def S_ST(n):                                # street wall inner face (user Layer 02 line)
    return 23.53 + (n + 4.8) * (23.84 - 23.53) / (7.17 + 4.8)

H_NORTH = 16.3      # measured (photo 8)
H_WEST = 28.0       # tallest (northern) part of the stepped west firewall, photo 36 (estimate)
H_EAST = 19.0       # estimate, >= 17.5 measured
WALL_T = 1.0        # skin thickness behind the yard faces

PLAT_Z = 0.85       # photo 34: 5 risers x 0.17 below the WC landing; photo 18: platform wall 0.82 m
                    # above the wet ground (pallet-stack check)
# platform + ramp: user moved the group 1.14 m south and cut the platform back to the ramp's outer edge
SHIFT = 1.14
RAMP_N0, RAMP_N1 = 2.6, 4.6
RAMP_TOP_S, RAMP_BOT_S = -12.6 + SHIFT, -8.4 + SHIFT    # -11.46 .. -7.26 (user)
PLAT_BACK_S = -14.4 + SHIFT                 # platform back edge -13.26 (user; gap to the north wall)
PLAT_N_S1 = -12.6 + SHIFT                   # north platform front edge -11.46 (user)
PLAT_E_N1 = -3.4                            # east platform front edge (user)
PLAT_W_N = RAMP_N1                          # platform now ends at the ramp's outer edge (user)

# --- WC entrance (photo 34, calibrated on the door opening 1.00 x 2.10 m; people check 1.78 / 1.68 m)
#     plan position + depths from the user's edit (door plane n -5.87, facade n -4.6);
#     widths / heights / step layout from the photo.  Heights below are above the landing (PLAT_Z).
WC_DOOR_S = -10.675 + SHIFT - 1.92          # door centre: user moved the whole WC bay 1.92 m north (bay -12.91..-10.49)
AIL_S = -8.565                               # tree-of-heaven stays where it was (not moved by the user)
WC_S0, WC_S1 = WC_DOOR_S - 1.45, WC_DOOR_S + 0.97   # opening between the piers (photo: -1.45 / +0.97)
WC_DEPTH = 1.0                              # facade -4.6 -> back wall -5.60 (user's back-wall block)
WC_ARCH = (3.30, 3.52, 3.96)                # spring, crown (intrados), top of spandrel band
WC_ARCH2 = (7.55, 7.86, 8.25)
WC_CANOPY = (2.68, 2.52, 1.15)              # z at wall, z at front edge, projection beyond facade (overlay-tuned)
WC_BRACKET_Z = 1.72                         # bracket feet on the piers
STEP_R, STEP_T = PLAT_Z / 5.0, 0.30         # 5 risers, 0.30 treads
STEP_L = WC_DOOR_S - 0.47                   # stair's north end = platform side face (photo -0.36..-0.68)
LAND_D = 0.67                               # landing depth in front of the door (photo)

GATE_N0, GATE_N1 = 7.72, 10.62              # 2.9 m opening between 0.55 m pillars
PIL_W = 0.55
GATE_H, WALLST_H = 1.85, 2.30

# ------------------------------------------------------------------ layers
def layer(path, col, transp=None):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        parts = path.split('::')
        parent = System.Guid.Empty
        if len(parts) > 1:
            parent = doc.Layers[layer('::'.join(parts[:-1]), Color.FromArgb(150, 150, 150))].Id
        Lr = Rhino.DocObjects.Layer()
        Lr.Name = parts[-1]
        Lr.Color = col
        Lr.ParentLayerId = parent
        idx = doc.Layers.Add(Lr)
    if transp is not None:
        m = Rhino.DocObjects.Material()
        m.Name = path.split('::')[-1]
        m.DiffuseColor = col
        m.Transparency = transp
        lay = doc.Layers[idx]
        lay.RenderMaterialIndex = doc.Materials.Add(m)
        lay.CommitChanges()
    return idx

E = '01_Existing_Buildings::'
G = '02_Courtyard_Ground::'
FU = '04_Furniture_Elements::'
LY = {
    'wallW': layer(E + 'Courtyard_Facade_West_grey', Color.FromArgb(128, 128, 126)),
    'wallN': layer(E + 'Courtyard_Facade_North_brick', Color.FromArgb(196, 170, 125)),
    'wallE': layer(E + 'Courtyard_Facade_East_beige', Color.FromArgb(214, 196, 140)),
    'patch': layer(E + 'Facade_Paint_Patches', Color.FromArgb(240, 240, 236)),
    'brick': layer(E + 'Facade_Exposed_Brick', Color.FromArgb(170, 120, 85)),
    'win': layer(E + 'Facade_Windows_Doors', Color.FromArgb(235, 235, 235)),
    'winGreen': layer(E + 'Facade_Windows_Doors_Green_Timber', Color.FromArgb(30, 95, 60)),
    'sill': layer(E + 'Facade_Sills', Color.FromArgb(150, 150, 145)),
    'patchDark': layer(E + 'Facade_Render_Dark_Grey', Color.FromArgb(75, 75, 75)),
    'patchBeige': layer(E + 'Facade_Render_Beige_Exposed', Color.FromArgb(205, 190, 150)),
    'wglass': layer(E + 'Facade_Window_Glass', Color.FromArgb(70, 85, 95), 0.3),
    'pipe': layer(E + 'Facade_Downpipes', Color.FromArgb(200, 120, 60)),
    'street': layer(E + 'Street_Wall', Color.FromArgb(150, 150, 145)),
    'gate': layer(E + 'Street_Gate', Color.FromArgb(40, 120, 95)),
    'hut': layer(E + 'Brick_Hut', Color.FromArgb(165, 75, 55)),
    'asph': layer(G + 'Asphalt_Yard', Color.FromArgb(95, 95, 98)),
    'conc': layer(G + 'Concrete_Apron', Color.FromArgb(185, 185, 180)),
    'ramp': layer(G + 'Ramp_Platform_Steps', Color.FromArgb(205, 205, 200)),
    'rail': layer(FU + 'Handrails', Color.FromArgb(55, 60, 65)),
    'shedR': layer(FU + 'Sheds::Corrugated_Roofs', Color.FromArgb(120, 95, 75)),
    'shedS': layer(FU + 'Sheds::Steel_Structure', Color.FromArgb(45, 45, 45)),
    'shedW': layer(FU + 'Sheds::OSB_Plywood_Walls', Color.FromArgb(200, 160, 105)),
    'shedC': layer(FU + 'Sheds::Curtains_Panels', Color.FromArgb(35, 35, 35)),
    'shelF': layer(FU + 'Shelter_3_Gable::Galvanised_Frame', Color.FromArgb(175, 178, 180)),
    'shelR': layer(FU + 'Shelter_3_Gable::Polycarbonate_Roof', Color.FromArgb(200, 210, 215), 0.55),
    'shelM': layer(FU + 'Shelter_3_Gable::Mesh_Panels', Color.FromArgb(160, 165, 170), 0.75),
    'canopy': layer(FU + 'WC_Entrance_Canopy', Color.FromArgb(110, 70, 50)),
    'ladder': layer(FU + 'Fire_Ladder', Color.FromArgb(215, 120, 40)),
    'bench': layer(FU + 'Benches', Color.FromArgb(160, 105, 60)),
    'bin': layer(FU + 'Bins', Color.FromArgb(40, 110, 50)),
    'sign': layer(FU + 'Signs', Color.FromArgb(240, 210, 120)),
    'trunk': layer('03_Vegetation::Tree_Trunks_Branches', Color.FromArgb(95, 75, 60)),
    'crown': layer('03_Vegetation::Tree_Crowns', Color.FromArgb(105, 150, 70), 0.55),
}

# ------------------------------------------------------------------ cleanup (protects user edits)
# Every generated object carries 'build_key' (name#occurrence), 'build_sig' (geometry signature) and
# 'build_layer'. On re-run, an object whose geometry or layer no longer matches what the script made
# was edited by the user: it is KEPT and the script skips regenerating that element.
def geo_sig(g):
    # 5 cm grid on the loose bbox: robust to how Rhino stores curved surfaces, still catches real moves
    bb = g.GetBoundingBox(False)
    return ','.join('%d' % int(round(v / 0.05)) for v in (bb.Min.X, bb.Min.Y, bb.Min.Z, bb.Max.X, bb.Max.Y, bb.Max.Z))

s_ = Rhino.DocObjects.ObjectEnumeratorSettings()
s_.HiddenObjects = True
s_.LockedObjects = True
KEEP = set()
# elements the user deleted: never regenerate them (keys stored in the document)
SUPPRESSED = set(k for k in (doc.Strings.GetValue('courtyard_suppressed') or '').split(';') if k)
KEEP |= SUPPRESSED
for o in [o for o in doc.Objects.GetObjectList(s_) if o.Attributes.GetUserString(TAG)]:
    a = o.Attributes
    k, sig, lay = a.GetUserString('build_key'), a.GetUserString('build_sig'), a.GetUserString('build_layer')
    edited = (sig is not None and sig != geo_sig(o.Geometry)) or (lay is not None and lay != str(doc.Layers[a.LayerIndex].Id)) \
        or a.GetUserString('user_edited') == '1'
    if k and edited:
        KEEP.add(k)
        continue
    doc.Objects.Delete(o, True, True)
if KEEP:
    print('kept %d user-edited objects: %s' % (len(KEEP), ', '.join(sorted(KEEP))))

group = doc.Groups.Add('Courtyard_Alfoldi6')
count = {}
occ = {}


def put(geo, key, name=None, note=None):
    if geo is None:
        return
    bkey = '%s|%s' % (key, name or '')
    occ[bkey] = occ.get(bkey, 0) + 1
    bkey = '%s#%d' % (bkey, occ[bkey])
    if bkey in KEEP:
        return
    geo.Transform(XF)
    at = Rhino.DocObjects.ObjectAttributes()
    at.LayerIndex = LY[key]
    at.WireDensity = -1
    at.SetUserString(TAG, '2026-10-13')
    at.SetUserString('build_key', bkey)
    at.SetUserString('build_sig', geo_sig(geo))
    at.SetUserString('build_layer', str(doc.Layers[LY[key]].Id))
    if note:
        at.SetUserString('note', note)
    if name:
        at.Name = name
    at.AddToGroup(group)
    if isinstance(geo, rg.Brep):
        doc.Objects.AddBrep(geo, at)
    elif isinstance(geo, rg.Curve):
        doc.Objects.AddCurve(geo, at)
    else:
        doc.Objects.Add(geo, at)
    count[key] = count.get(key, 0) + 1


def box(s0, s1, n0, n1, z0, z1, key, name=None, note=None):
    s0, s1 = sorted((s0, s1))
    n0, n1 = sorted((n0, n1))
    z0, z1 = sorted((z0, z1))
    if s1 - s0 < 1e-4 or n1 - n0 < 1e-4 or z1 - z0 < 1e-4:
        return
    b = rg.BoundingBox(P(s1, n0, z0), P(s0, n1, z1))
    put(rg.Box(b).ToBrep(), key, name, note)


def hexa(pts8, key, name=None, note=None):
    """8 corners (s, n, z): bottom 4 ccw then top 4 in the same order"""
    br = rg.Brep.CreateFromBox([P(*q) for q in pts8])
    put(br, key, name, note)


def solid_box_brep(s0, s1, n0, n1, z0, z1):
    s0, s1 = sorted((s0, s1))
    n0, n1 = sorted((n0, n1))
    return rg.Box(rg.BoundingBox(P(s1, n0, z0), P(s0, n1, z1))).ToBrep()


def tube(pts, r, key, name=None):
    pl = rg.PolylineCurve([P(*q) for q in pts])
    crv = pl
    if len(pts) > 2:
        f = rg.Curve.CreateFilletCornersCurve(pl, r * 2.5, TOL, math.radians(1))
        if f:
            crv = f
    pipes = rg.Brep.CreatePipe(crv, r, False, rg.PipeCapMode.Flat, True, TOL, math.radians(1))
    for p in pipes or []:
        put(p, key, name)


def plane_quad(a, b, c, d, key, name=None):
    """planar 4-corner surface, corners (s, n, z)"""
    br = rg.Brep.CreateFromCornerPoints(P(*a), P(*b), P(*c), P(*d), TOL)
    put(br, key, name)


def corrugated(origin, wdir, ddir, width, depth, key, name, amp=0.018, pitch=0.076):
    """corrugated sheet: origin (s, n, z), wdir/ddir unit vectors in (s, n, z)"""
    o = rg.Vector3d(*origin)
    w = rg.Vector3d(*wdir)
    d = rg.Vector3d(*ddir)
    nrm = rg.Vector3d.CrossProduct(w, d)
    nrm.Unitize()
    if nrm.Z < 0:
        nrm = -nrm
    pts = []
    k = int(width / pitch * 4)
    for i in range(k + 1):
        t = width * i / float(k)
        q = o + w * t + nrm * (amp * math.sin(2 * math.pi * t / pitch))
        pts.append(P(q.X, q.Y, q.Z))
    prof = rg.PolylineCurve(pts)
    a = P(0, 0, 0)
    b = P(d.X * depth, d.Y * depth, d.Z * depth)
    srf = rg.Surface.CreateExtrusion(prof, b - a)
    if srf:
        put(srf.ToBrep(), key, name)


def ellipsoid(s, n, zc, rs, rn, rz, key, name=None):
    sph = rg.Sphere(rg.Point3d(0, 0, 0), 1.0).ToBrep()
    sph.Transform(rg.Transform.Scale(rg.Plane.WorldXY, rs, rn, rz))
    sph.Transform(rg.Transform.Translation(rg.Vector3d(P(s, n, zc))))
    put(sph, key, name)


def limb(p0, p1, r0, r1, key='trunk', name=None):
    a, b = P(*p0), P(*p1)
    axis = b - a
    c0 = rg.ArcCurve(rg.Circle(rg.Plane(a, axis), r0))
    c1 = rg.ArcCurve(rg.Circle(rg.Plane(b, axis), r1))
    lofts = rg.Brep.CreateFromLoft([c0, c1], rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Straight, False)
    if lofts:
        put(lofts[0].CapPlanarHoles(TOL) or lofts[0], key, name)


# ================================================================== 1. COURTYARD FACADES (skins)
# --- west (grey) wall with the niche column (photo 5 photogrammetry: s 14.51..16.85)
NICHE_S0, NICHE_S1, NICHE_D = 14.51, 16.85, 0.9
# NW corner light-well strip (photo 35, user frame s -14.4..-7.71, z 2.9..18.5): a 2.1 m wide strip,
# set ~0.7 m back from the firewall face, with 4 stacked windows; firewall to the south of it is peeling
CW_S0, CW_S1, CW_D, CW_Z0 = S_N, S_N + 2.1, 0.7, 2.9
# Stepped firewall top + slot column (photo 36, looking south from the brown shed; calibrated on the
# niche corners, the downpipe at s -0.25 and the wall's south corner; heights from the window spacing)
SLOT_S0, SLOT_S1, SLOT_D, SLOT_Z0 = 4.98, 5.88, 0.5, 7.5      # at the north edge of the user's frame (s 4.98..10.57)
WEST_TOP = [(S_ST(N_W), 18.5), (17.0, 21.5), (14.2, 21.5),      # A: low gable over the niche column
            (14.2, 22.0), (SLOT_S1 + 0.3, 27.0),                    # B: roof-pitch slope up to the slot column
            (SLOT_S1 + 0.3, H_WEST), (S_N, H_WEST)]                 # C: taller part north of the slot column
                                                                    # (step 0.3 m off the slot: no coplanar faces)
NICHE_TOP = 20.89                           # top arch closes the niche (user's arch profile repeated)


def west_top_z(s):
    pts = sorted(WEST_TOP, key=lambda q: -q[0])
    for (sa, za), (sb, zb) in zip(pts, pts[1:]):
        if sb <= s <= sa and sa != sb:
            return za + (zb - za) * (sa - s) / (sa - sb)
    return H_WEST

prof = [P(S_N, N_W - 0.02, 0.0), P(S_ST(N_W), N_W - 0.02, 0.0)] + [P(s, N_W - 0.02, z) for s, z in WEST_TOP] + [P(S_N, N_W - 0.02, 0.0)]
srf = rg.Surface.CreateExtrusion(rg.PolylineCurve(prof), P(0, N_W + WALL_T, 0) - P(0, N_W - 0.02, 0))
west = srf.ToBrep().CapPlanarHoles(TOL)
if west.SolidOrientation == rg.BrepSolidOrientation.Inward:
    west.Flip()
for c in (solid_box_brep(NICHE_S0, NICHE_S1, N_W - 0.1, N_W + NICHE_D, 2.9, NICHE_TOP),
          solid_box_brep(CW_S0 - 0.05, CW_S1, N_W - 0.1, N_W + CW_D, CW_Z0, H_WEST + 0.1),
          solid_box_brep(SLOT_S0, SLOT_S1, N_W - 0.1, N_W + SLOT_D, SLOT_Z0, H_WEST + 0.1)):
    diff = rg.Brep.CreateBooleanDifference(west, c, TOL)
    if diff:
        west = diff[0]
put(west, 'wallW', 'west courtyard facade (grey, firewall)',
    note='stepped top + slot column from photo 36 (estimated); niche column measured on photo 5')
# chimney stacks on the stepped top (photo 36)
for cs in (17.0, 11.6, 9.7, 8.4):
    zt = west_top_z(cs)
    box(cs - 0.25, cs + 0.25, N_W + 0.05, N_W + 0.95, zt - 0.3, zt + 1.2, 'brick', 'chimney stack')
    box(cs - 0.3, cs + 0.3, N_W, N_W + 1.0, zt + 1.2, zt + 1.3, 'brick', 'chimney cap')
# niche column: 4 window levels under the user's segmental arch heads (springs 7.19 / 11.89 / 16.59, 4.70 m
# spacing); L0/L1 measured on photo 5, L2/L3 follow the arch spacing; one more arch generated at the top
NICHE_WINS = [(2.49, 6.57, 'barred'), (8.04, 10.89, ''), (12.75, 15.6, ''), (17.45, 20.0, '')]
NICHE_ARCHES = [20.45]                      # generated; the three lower arches are the user's own objects
box(NICHE_S0, NICHE_S1, N_W - 0.02, N_W + NICHE_D, 2.15, 2.33, 'wallW', 'niche slab')
for z0, z1, kind in NICHE_WINS:
    box(15.15, 16.25, N_W + NICHE_D - 0.08, N_W + NICHE_D, z0, z1, 'win', 'niche window frame')
    box(15.25, 16.15, N_W + NICHE_D - 0.1, N_W + NICHE_D - 0.08, z0 + 0.1, z1 - 0.1, 'wglass', 'niche window glass')
    if kind == 'barred':
        for k in range(6):
            sb = 15.3 + k * 0.17
            box(sb, sb + 0.02, N_W + NICHE_D - 0.16, N_W + NICHE_D - 0.14, z0 + 0.1, z1 - 0.1, 'win', 'window bars')
for zs in NICHE_ARCHES:                     # same profile as the user's arches: rise 0.22, band 0.44, depth 0.48
    a = P(NICHE_S0, N_W - 0.02, zs); m = P(0.5 * (NICHE_S0 + NICHE_S1), N_W - 0.02, zs + 0.22); b = P(NICHE_S1, N_W - 0.02, zs)
    arc = rg.ArcCurve(rg.Arc(a, m, b))
    poly = rg.PolylineCurve([b, P(NICHE_S1, N_W - 0.02, zs + 0.44), P(NICHE_S0, N_W - 0.02, zs + 0.44), a])
    prof_a = rg.Curve.JoinCurves([arc, poly], TOL)[0]
    sa = rg.Surface.CreateExtrusion(prof_a, P(0, N_W + 0.46, 0) - P(0, N_W - 0.02, 0))
    if sa:
        put(sa.ToBrep().CapPlanarHoles(TOL), 'wallW', 'niche arch head')
# slot column: 4 tall narrow openings (photo 36), the lowest broken out with a brick reveal
SLOT_BACK = N_W + SLOT_D
box(SLOT_S0, SLOT_S1, SLOT_BACK - 0.012, SLOT_BACK - 0.002, SLOT_Z0, H_WEST, 'patchDark', 'slot column back wall (dark render)')
for i, (z0, z1) in enumerate(((9.0, 11.0), (12.0, 15.0), (16.6, 20.0), (21.0, 23.8))):
    s0, s1 = SLOT_S0 + 0.12, SLOT_S1 - 0.12
    if i == 0:
        box(s0 - 0.1, s1 + 0.1, SLOT_BACK - 0.03, SLOT_BACK - 0.012, z0 - 0.9, z1 + 0.2, 'brick', 'broken-out opening (brick reveal)')
        box(s0, s1, SLOT_BACK - 0.04, SLOT_BACK - 0.03, z0, z1, 'wglass', 'open slot (dark)')
        continue
    fw = 0.05
    nf = SLOT_BACK - 0.07
    box(s0, s1, nf, nf + 0.06, z0, z0 + fw, 'win', 'slot window frame')
    box(s0, s1, nf, nf + 0.06, z1 - fw, z1, 'win', 'slot window frame')
    box(s0, s0 + fw, nf, nf + 0.06, z0, z1, 'win', 'slot window frame')
    box(s1 - fw, s1, nf, nf + 0.06, z0, z1, 'win', 'slot window frame')
    box(s0 + fw, s1 - fw, nf + 0.025, nf + 0.035, z0 + fw, z1 - fw, 'wglass', 'slot window glass')
# white pipe running diagonally down the wall face from the slot column to the brown shed roof (photo 36)
tube([(SLOT_S0 - 0.2, N_W - 0.25, 12.2), (SLOT_S0 - 0.45, N_W - 0.12, 12.0), (-1.75, N_W - 0.12, 2.85)], 0.04, 'pipe', 'white pipe (diagonal)')
# peeling render on the slope section and around the slot column (photo 36)
for pts in ([(14.0, 22.0), (11.0, 23.6), (8.5, 24.8), (7.5, 21.0), (9.8, 18.5), (12.6, 19.2)],
            [(SLOT_S1 + 0.1, 11.0), (SLOT_S1 + 0.1, 19.0), (6.2, 17.6), (5.6, 14.0), (6.4, 12.0)],
            [(SLOT_S0 - 0.05, 20.0), (SLOT_S0 - 0.05, 26.0), (1.0, 26.4), (-0.5, 23.5), (1.2, 21.8)],
            [(14.3, 9.2), (14.3, 11.4), (12.2, 11.8), (11.6, 10.0)],
            [(18.2, 9.0), (18.2, 10.4), (19.6, 10.8), (20.2, 9.4)]):
    poly = rg.PolylineCurve([P(s, N_W - 0.03, z) for s, z in pts] + [P(pts[0][0], N_W - 0.03, pts[0][1])])
    br = rg.Brep.CreatePlanarBreps(poly, TOL)
    if br:
        put(br[0], 'patchBeige', 'exposed beige render (peeling, photo 36)')
# small red-framed window + orange downpipe left of the brown shed (photo 25)
box(-1.25, -0.65, N_W - 0.04, N_W, 1.55, 2.25, 'win', 'small window (red frame)')
# photo 36: the downpipe stops at ~6.1 m and turns south into the wall
tube([(-0.25, N_W - 0.08, 0.15), (-0.25, N_W - 0.08, 2.6), (-0.6, N_W - 0.08, 3.4), (-0.6, N_W - 0.08, 6.1), (0.3, N_W - 0.08, 6.1), (0.3, N_W + 0.05, 6.1)], 0.055, 'pipe', 'downpipe')
# exposed brick plinth behind the planters / sheds (photos 11, 25)
box(-10.0, 23.0, N_W - 0.03, N_W - 0.02, 0.0, 2.9, 'brick', 'exposed brick plinth (graffiti)')

# --- NW corner light-well strip details (photo 35)
CW_BACK = N_W + CW_D                        # back face of the strip
box(CW_S0, CW_S1, CW_BACK - 0.012, CW_BACK - 0.002, CW_Z0, H_WEST, 'patchDark', 'dark grey render (light-well strip)')
FLOOR = 3.5                                 # floor-to-floor, from the window spacing in the photo
win_s1 = CW_S1 - 0.36                       # window edge 0.36 m from the strip's south edge


def strip_window(z0, w, h, kind, name):
    s0, s1 = win_s1 - w, win_s1
    fw = 0.06
    nf = CW_BACK - 0.06
    key = 'win' if kind == 'white' else 'winGreen'
    box(s0, s1, nf, nf + 0.06, z0, z0 + fw, key, name + ' frame')
    box(s0, s1, nf, nf + 0.06, z0 + h - fw, z0 + h, key, name + ' frame')
    box(s0, s0 + fw, nf, nf + 0.06, z0, z0 + h, key, name + ' frame')
    box(s1 - fw, s1, nf, nf + 0.06, z0, z0 + h, key, name + ' frame')
    box(s0 + fw, s1 - fw, nf + 0.025, nf + 0.035, z0 + fw, z0 + h - fw, 'wglass', name + ' glass')
    if kind == 'green4':                    # 2 x 2 casement + transom bars
        box(0.5 * (s0 + s1) - 0.025, 0.5 * (s0 + s1) + 0.025, nf, nf + 0.05, z0, z0 + h, key, name + ' mullion')
        for t in (0.42, 0.72):
            box(s0, s1, nf, nf + 0.05, z0 + h * t - 0.025, z0 + h * t + 0.025, key, name + ' transom')
    if kind == 'green2':
        box(0.5 * (s0 + s1) - 0.025, 0.5 * (s0 + s1) + 0.025, nf, nf + 0.05, z0, z0 + h * 0.8, key, name + ' mullion')
        box(s0, s1, nf, nf + 0.05, z0 + h * 0.8 - 0.025, z0 + h * 0.8 + 0.025, key, name + ' transom')
    box(s0 - 0.04, s1 + 0.04, nf - 0.08, nf + 0.06, z0 - 0.05, z0, 'sill', name + ' sill')

z1 = 3.95                                   # lowest sill ~0.9 m above the lean-to roof (photo)
strip_window(z1, 1.00, 1.75, 'green4', 'light-well window L1 (green, 4-light)')
strip_window(z1 + FLOOR, 0.90, 1.75, 'white', 'light-well window L2 (white PVC)')
box(win_s1 - 0.94, win_s1 + 0.04, CW_BACK - 0.2, CW_BACK - 0.06, z1 + FLOOR + 1.75, z1 + FLOOR + 1.97, 'win', 'roller-shutter box')
strip_window(z1 + 2 * FLOOR, 0.95, 1.70, 'green2', 'light-well window L3 (green)')
strip_window(z1 + 3 * FLOOR, 0.85, 1.75, 'white', 'light-well window L4 (white PVC)')
# AC outdoor unit under the top window + condensate / refrigerant pipe up its north side
acz = z1 + 3 * FLOOR - 0.62
box(win_s1 - 0.84, win_s1 - 0.04, CW_BACK - 0.36, CW_BACK - 0.06, acz, acz + 0.55, 'win', 'AC outdoor unit')
tube([(win_s1 + 0.12, CW_BACK - 0.1, acz + 0.3), (win_s1 + 0.12, CW_BACK - 0.1, z1 + 3 * FLOOR + 1.9)], 0.02, 'win', 'AC pipe')
# small wall lamp below the lowest window
tube([(win_s1 - 0.45, CW_BACK - 0.02, z1 - 0.32), (win_s1 - 0.45, CW_BACK - 0.12, z1 - 0.32)], 0.09, 'win', 'wall lamp')

# --- peeling firewall south of the strip: beige render / exposed brick patches over the grey render (photo 35)
def patch(pts_sz, key, name, off=0.03):       # wall face is at N_W - 0.02 -> patches sit 1 cm in front
    poly = rg.PolylineCurve([P(s, N_W - off, z) for s, z in pts_sz] + [P(pts_sz[0][0], N_W - off, pts_sz[0][1])])
    br = rg.Brep.CreatePlanarBreps(poly, TOL)
    if br:
        put(br[0], key, name)

patch([(-12.30, 6.2), (-12.30, 16.9), (-11.2, 17.6), (-10.4, 16.2), (-9.9, 13.3), (-10.2, 10.6), (-9.6, 8.6),
       (-10.3, 6.9), (-11.4, 5.4)], 'patchBeige', 'exposed beige render (peeling)')
patch([(-10.2, 17.8), (-8.6, 18.3), (-7.71, 17.6), (-7.71, 15.2), (-8.9, 14.6), (-9.6, 15.9)], 'patchBeige', 'exposed beige render (peeling)')
patch([(-12.30, 2.95), (-12.30, 4.4), (-10.9, 5.0), (-9.3, 4.5), (-8.4, 5.1), (-7.71, 4.6), (-7.71, 2.95)], 'patchBeige',
      'exposed beige render (peeling, lower band)')
patch([(-9.0, 2.95), (-9.0, 3.6), (-8.2, 3.9), (-7.71, 3.7), (-7.71, 2.95)], 'brick', 'exposed brick (lower band)', off=0.035)

# --- north (brick / beige) wall, measured 16.3 m (photo 8)
box(S_N - WALL_T, S_N + 0.02, N_E, N_W, 0.0, H_NORTH, 'wallN', 'north courtyard facade (firewall)')
box(S_N + 0.02, S_N + 0.03, -0.3, 4.9, PLAT_Z, 4.5, 'patch', 'white painted patch (measured photo 8)')
for n0, n1 in ((4.55, 4.9), (1.45, 1.8)):           # brick pilasters in the white patch (photo 16)
    box(S_N + 0.03, S_N + 0.04, n0, n1, PLAT_Z, 4.0, 'brick', 'brick pilaster strip')
box(S_N + 0.03, S_N + 0.04, -0.8, 5.4, 4.0, 4.5, 'brick', 'exposed brick lintel band')
for nc in (10.9, 4.5, -1.5):                         # chimney stacks (photo 8)
    box(S_N - 0.9, S_N - 0.3, nc - 0.45, nc + 0.45, H_NORTH, H_NORTH + 1.0, 'brick', 'chimney stack')

# --- east (beige) wall with the WC light-well bay
east = solid_box_brep(S_N, 23.53, N_E - WALL_T, N_E + 0.02, 0.0, H_EAST)
cut = solid_box_brep(WC_S0, WC_S1, N_E - WC_DEPTH, N_E + 0.1, 0.0, 14.5)
diff = rg.Brep.CreateBooleanDifference(east, cut, TOL)
put(diff[0] if diff else east, 'wallE', 'east courtyard facade (Alfoldi u. 6-8)', note='height estimated 19 m (>=17.5 measured)')

WC_BACK = N_E - WC_DEPTH                      # door / light-well back wall
WD = WC_DOOR_S


def arch_band(z_spring, z_crown, z_top, name):
    """segmental arch + spandrel band spanning the bay, extruded through the bay depth"""
    a = P(WC_S0, N_E + 0.02, z_spring)
    m = P(0.5 * (WC_S0 + WC_S1), N_E + 0.02, z_crown)
    b = P(WC_S1, N_E + 0.02, z_spring)
    arc = rg.ArcCurve(rg.Arc(a, m, b))
    poly = rg.PolylineCurve([b, P(WC_S1, N_E + 0.02, z_top), P(WC_S0, N_E + 0.02, z_top), a])
    prof = rg.Curve.JoinCurves([arc, poly], TOL)[0]
    srf = rg.Surface.CreateExtrusion(prof, P(0, WC_BACK, 0) - P(0, N_E + 0.02, 0))
    br = srf.ToBrep().CapPlanarHoles(TOL) if srf else None
    if br:
        put(br, 'wallE', name)                  # P() is already in the local frame; put() applies XF

for zs, zc, zt in (WC_ARCH, WC_ARCH2, (11.80, 12.11, 12.50)):
    arch_band(PLAT_Z + zs, PLAT_Z + zc, PLAT_Z + zt, 'light-well arch + spandrel band (photo 34)')


def window(s0, s1, z0, z1, name, n_face=None, side=None):
    """frame + glass on the back wall (n_face) or on a side wall (side = s plane, s0/s1 used as n range)"""
    fw = 0.05
    if side is None:
        nf = WC_BACK if n_face is None else n_face
        box(s0, s1, nf, nf + 0.06, z0, z0 + fw, 'win', name + ' frame')
        box(s0, s1, nf, nf + 0.06, z1 - fw, z1, 'win', name + ' frame')
        box(s0, s0 + fw, nf, nf + 0.06, z0, z1, 'win', name + ' frame')
        box(s1 - fw, s1, nf, nf + 0.06, z0, z1, 'win', name + ' frame')
        box(s0 + fw, s1 - fw, nf + 0.02, nf + 0.03, z0 + fw, z1 - fw, 'wglass', name + ' glass')
    else:
        box(side, side + 0.06, s0, s1, z0, z0 + fw, 'win', name + ' frame')
        box(side, side + 0.06, s0, s1, z1 - fw, z1, 'win', name + ' frame')
        box(side, side + 0.06, s0, s0 + fw, z0, z1, 'win', name + ' frame')
        box(side, side + 0.06, s1 - fw, s1, z0, z1, 'win', name + ' frame')
        box(side + 0.02, side + 0.03, s0 + fw, s1 - fw, z0 + fw, z1 - fw, 'wglass', name + ' glass')

# WC door (opening 1.00 x 2.10 measured; white steel leaf with glazed top panel)
box(WD - 0.55, WD + 0.55, WC_BACK, WC_BACK + 0.08, PLAT_Z + 2.10, PLAT_Z + 2.16, 'win', 'WC door frame head')
for sj in (WD - 0.55, WD + 0.5):
    box(sj, sj + 0.05, WC_BACK, WC_BACK + 0.08, PLAT_Z, PLAT_Z + 2.16, 'win', 'WC door frame jamb')
box(WD - 0.5, WD + 0.5, WC_BACK + 0.02, WC_BACK + 0.06, PLAT_Z, PLAT_Z + 1.58, 'win', 'WC door leaf (white steel)')
box(WD - 0.5, WD + 0.5, WC_BACK + 0.02, WC_BACK + 0.06, PLAT_Z + 2.0, PLAT_Z + 2.10, 'win', 'WC door leaf top rail')
for sj in (WD - 0.5, WD + 0.42):
    box(sj, sj + 0.08, WC_BACK + 0.02, WC_BACK + 0.06, PLAT_Z + 1.58, PLAT_Z + 2.0, 'win', 'WC door leaf stile')
box(WD - 0.42, WD + 0.42, WC_BACK + 0.035, WC_BACK + 0.045, PLAT_Z + 1.58, PLAT_Z + 2.0, 'wglass', 'WC door glazed panel')
# tall narrow window left of the downpipe (measured 1.36..3.13 above landing)
window(WD - 1.40, WD - 1.12, PLAT_Z + 1.36, PLAT_Z + 3.13, 'WC tall window')
box(WD - 1.13, WD - 0.93, WC_BACK, WC_BACK + 0.02, PLAT_Z + 2.75, PLAT_Z + 2.95, 'win', 'vent grille')
# light-well windows: level 1 measured (5.39..6.26 above landing), level 2 repeated one storey up
for dz in (0.0, 4.25):
    window(WD - 0.69, WD - 0.25, PLAT_Z + 5.42 + dz, PLAT_Z + 6.20 + dz, 'light-well window (back wall)')
    window(WD + 0.15, WD + 0.78, PLAT_Z + 5.46 + dz, PLAT_Z + 6.26 + dz, 'light-well window (back wall)')
    window(WC_BACK + 0.25, WC_BACK + 0.80, PLAT_Z + 5.40 + dz, PLAT_Z + 6.25 + dz, 'light-well window (north side wall)', side=WC_S0)
# ventilation grilles (measured)
box(WD - 0.44, WD - 0.12, WC_BACK, WC_BACK + 0.02, PLAT_Z + 7.08, PLAT_Z + 7.33, 'win', 'vent grille')
box(WD + 0.48, WD + 0.83, WC_BACK, WC_BACK + 0.02, PLAT_Z + 7.36, PLAT_Z + 7.60, 'win', 'vent grille')
# downpipe in front of the back wall, left of the door (measured s -0.80, socket at 7.0 above landing)
DP_S = WD - 0.80
tube([(DP_S, WC_BACK + 0.1, 0.1), (DP_S, WC_BACK + 0.1, 14.5), (DP_S, N_E - 0.3, 15.5), (DP_S, N_E - 0.3, H_EAST)], 0.065, 'pipe', 'light-well downpipe')
for zs_ in (PLAT_Z + 7.0, PLAT_Z + 2.4):
    tube([(DP_S, WC_BACK + 0.1, zs_), (DP_S, WC_BACK + 0.1, zs_ + 0.18)], 0.085, 'pipe', 'downpipe socket')

# ================================================================== 2. GROUND SURFACES
box(S_N, 23.6, N_E, N_W, -0.12, -0.006, 'asph', 'asphalt yard surface')
box(S_N, RAMP_BOT_S + 0.6, N_E, PLAT_W_N, -0.006, 0.0, 'conc', 'concrete apron (ramp area)')

# ================================================================== 3. PLATFORM, RAMP, STEPS (WC access)
box(PLAT_BACK_S, PLAT_N_S1, N_E, PLAT_W_N, 0.0, PLAT_Z, 'ramp', 'raised platform along north wall')
box(PLAT_N_S1, STEP_L, N_E, PLAT_E_N1, 0.0, PLAT_Z, 'ramp', 'raised platform along east wall')
box(WC_S0, STEP_L, WC_BACK, N_E, 0.0, PLAT_Z, 'ramp', 'raised platform (inside WC bay)')
LAND_N = WC_BACK + LAND_D
box(STEP_L, WC_S1, WC_BACK, LAND_N, 0.0, PLAT_Z, 'ramp', 'WC landing')
# 4 steps below the landing (5 risers); inside the bay they stop at the south pier, in front of the
# facade they run past it (photo: right ends at +1.45 / +1.73 from the door centre)
n0 = LAND_N
for k in range(1, 5):
    n1 = n0 + STEP_T
    # inside the bay the step stops at the south pier; in front of the facade it runs past it (photo 34)
    s_end = WC_S1 if n0 < N_E - 0.05 else WD + {1: 1.29, 2: 1.45, 3: 1.56, 4: 1.73}[k]
    box(STEP_L, s_end, n0, n1, 0.0, PLAT_Z - k * STEP_R, 'ramp', 'WC step %d' % k)
    n0 = n1
hexa([(RAMP_TOP_S, RAMP_N0, -0.02), (RAMP_BOT_S, RAMP_N0, -0.02), (RAMP_BOT_S, RAMP_N1, -0.02), (RAMP_TOP_S, RAMP_N1, -0.02),
      (RAMP_TOP_S, RAMP_N0, PLAT_Z), (RAMP_BOT_S, RAMP_N0, 0.0), (RAMP_BOT_S, RAMP_N1, 0.0), (RAMP_TOP_S, RAMP_N1, PLAT_Z)],
     'ramp', 'accessible ramp (%.0f%%)' % (100 * PLAT_Z / (RAMP_BOT_S - RAMP_TOP_S)),
     note='extent from user Layer 02 zone; rise = platform height 0.85 (photo 34/18) -> slope looks too steep, ramp length unverified')

# ================================================================== 4. HANDRAILS (RAL 7016 tube 48 mm)
R = 0.024


def rail_run(a, b, z_a, z_b, levels, posts_every=1.6, name='handrail'):
    """a, b = (s, n); z_a/z_b = walking surface at ends; levels = rail heights above surface"""
    for h in levels:
        tube([(a[0], a[1], z_a + h), (b[0], b[1], z_b + h)], R, 'rail', name)
    dl = math.hypot(b[0] - a[0], b[1] - a[1])
    k = max(1, int(math.ceil(dl / posts_every)))
    top = max(levels)
    for i in range(k + 1):
        t = i / float(k)
        ps, pn = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        zs = z_a + (z_b - z_a) * t
        tube([(ps, pn, zs), (ps, pn, zs + top)], R, 'rail', name + ' post')

for nr in (RAMP_N0 + 0.05, RAMP_N1 - 0.05):
    rail_run((RAMP_BOT_S + 0.3, nr), (RAMP_TOP_S, nr), 0.0, PLAT_Z, (0.1, 0.75, 0.9), name='ramp handrail')
rail_run((PLAT_N_S1 + 0.05, PLAT_E_N1), (PLAT_N_S1 + 0.05, RAMP_N0), PLAT_Z, PLAT_Z, (0.1, 0.5, 1.0), name='platform guard rail')
if PLAT_W_N - RAMP_N1 > 0.3:
    rail_run((PLAT_N_S1 + 0.05, RAMP_N1), (PLAT_N_S1 + 0.05, PLAT_W_N - 0.1), PLAT_Z, PLAT_Z, (0.1, 0.5, 1.0), name='platform guard rail')
# platform end on the ramp's outer side: the ramp's outer handrail continues along it to the back edge
rail_run((PLAT_N_S1, RAMP_N1 - 0.05), (PLAT_BACK_S + 0.05, RAMP_N1 - 0.05), PLAT_Z, PLAT_Z, (0.1, 0.75, 0.9), name='ramp handrail (platform run)')
rail_run((PLAT_N_S1, PLAT_E_N1 - 0.05), (STEP_L - 0.05, PLAT_E_N1 - 0.05), PLAT_Z, PLAT_Z, (0.1, 0.5, 1.0), name='platform guard rail')
# guard rail along the platform edge beside the WC steps, ending at the door jamb (photo 34)
rail_run((STEP_L - 0.05, PLAT_E_N1 - 0.05), (STEP_L - 0.05, LAND_N - 0.1), PLAT_Z, PLAT_Z, (0.1, 0.5, 1.0), name='platform guard rail (WC steps)')
if PLAT_BACK_S - S_N < 0.2:     # platform against the north wall -> wall-mounted handrail
    rail_run((S_N + 0.12, N_E + 0.3), (S_N + 0.12, PLAT_W_N - 0.2), PLAT_Z, PLAT_Z, (0.9,), posts_every=3.0, name='wall handrail')
else:                           # free back edge (user moved the platform off the wall) -> guard rail
    rail_run((PLAT_BACK_S + 0.05, N_E + 0.05), (PLAT_BACK_S + 0.05, PLAT_W_N - 0.05), PLAT_Z, PLAT_Z, (0.1, 0.5, 1.0), name='platform guard rail (back edge)')

# ================================================================== 5. WC ENTRANCE CANOPY (corrugated on 2 brackets, photo 34)
cz_wall, cz_front, c_proj = WC_CANOPY
c_s0, c_s1 = WD - 1.95, WC_S1 + 0.08            # runs ~0.5 m past the north pier, ends at the south pier
dl = math.hypot(c_proj, cz_front - cz_wall)
corrugated((c_s0, N_E + 0.02, PLAT_Z + cz_wall), (1, 0, 0), (0, c_proj / dl, (cz_front - cz_wall) / dl), c_s1 - c_s0, dl,
           'canopy', 'WC entrance canopy (corrugated, rusted)')
box(c_s0, c_s1, N_E + c_proj - 0.04, N_E + c_proj, PLAT_Z + cz_front - 0.06, PLAT_Z + cz_front, 'canopy', 'canopy front angle')
for sb in (WC_S0 - 0.08, WC_S1 + 0.08):
    tube([(sb, N_E + 0.02, PLAT_Z + WC_BRACKET_Z), (sb, N_E + c_proj - 0.05, PLAT_Z + cz_front - 0.06)], 0.02, 'canopy', 'canopy bracket')

# ================================================================== 6. 3-GABLE SHELTER (user Layer 02: s -7.3..-1.6, n -4.5..-2.1)
SH_S0, SH_S1, SH_N0, SH_N1 = -7.3, -1.6, N_E + 0.08, -2.1
EAVE, RIDGE = 2.25, 2.85
bay = (SH_S1 - SH_S0) / 3.0
F = 0.025
for i in range(4):
    sp = SH_S0 + i * bay
    for nn in (SH_N0, SH_N1):
        box(sp - F, sp + F, nn - F, nn + F, 0.0, EAVE, 'shelF', 'shelter post')
for nn in (SH_N0, SH_N1):
    box(SH_S0 - F, SH_S1 + F, nn - F, nn + F, EAVE - 0.05, EAVE, 'shelF', 'shelter eave beam')
for i in range(3):
    s_a, s_b = SH_S0 + i * bay, SH_S0 + (i + 1) * bay
    sm = 0.5 * (s_a + s_b)
    for (sx, sy) in ((s_a, sm), (s_b, sm)):
        plane_quad((sx, SH_N0, EAVE), (sy, SH_N0, RIDGE), (sy, SH_N1 + 0.15, RIDGE), (sx, SH_N1 + 0.15, EAVE), 'shelR', 'polycarbonate roof')
    tube([(sm, SH_N0, RIDGE), (sm, SH_N1 + 0.15, RIDGE)], 0.02, 'shelF', 'ridge tube')
    for nn in (SH_N0, SH_N1):
        tube([(s_a, nn, EAVE), (sm, nn, RIDGE), (s_b, nn, EAVE)], 0.018, 'shelF', 'gable rafter')
for sx in (SH_S0, SH_S1):                              # mesh end panels
    plane_quad((sx, SH_N0, 0.1), (sx, SH_N1, 0.1), (sx, SH_N1, EAVE - 0.1), (sx, SH_N0, EAVE - 0.1), 'shelM', 'mesh end panel')
for s_a, s_b in ((SH_S0, SH_S0 + 0.9), (SH_S1 - 1.0, SH_S1)):   # partial mesh on front (photo 21)
    plane_quad((s_a, SH_N1, 0.1), (s_b, SH_N1, 0.1), (s_b, SH_N1, 2.0), (s_a, SH_N1, 2.0), 'shelM', 'mesh front panel')
box(SH_S0 - 0.05, SH_S0 - 0.03, SH_N1 - 0.3, SH_N1 + 0.05, 1.45, 1.75, 'sign', 'MOSDO <- sign')

# ================================================================== 7. NW LEAN-TO (user Layer 02 / OSM: s -14.3..-10, n 7.9..13.6)
LT_S1, LT_N0 = -10.0, PLAT_W_N
corrugated((S_N + 0.02, LT_N0 - 0.1, 3.05), (0, 1, 0), (1, 0, -0.13), N_W - LT_N0 + 0.1, (LT_S1 - S_N) + 0.2, 'shedR', 'lean-to roof (corrugated, grey)')
for nn in (LT_N0 + 0.05, 0.5 * (LT_N0 + N_W), N_W - 0.05):
    box(LT_S1 - 0.03, LT_S1 + 0.03, nn - 0.03, nn + 0.03, 0.0, 2.48, 'shedS', 'lean-to post')
box(S_N + 0.02, LT_S1 + 0.03, LT_N0, LT_N0 + 0.05, 2.45, 2.55, 'shedS', 'lean-to beam')
box(LT_S1 - 0.05, LT_S1 + 0.05, LT_N0, N_W, 2.42, 2.52, 'shedS', 'lean-to front beam')
corrugated((S_N + 0.1, 10.5, 0.0), (0, 1, 0), (0, 0, 1), 2.3, 2.4, 'shedC', 'corrugated back screen')

# ================================================================== 8. 'HIPSE' storeroom (s -10..-7.35, along west wall)
HS_N0 = 11.6
box(-10.0, -7.35, HS_N0, N_W, 0.0, 0.05, 'shedW', 'storeroom floor')
for s0, s1 in ((-10.0, -9.95), (-7.4, -7.35)):
    box(s0, s1, HS_N0, N_W, 0.0, 2.4, 'shedW', 'storeroom side wall')
box(-10.0, -7.35, HS_N0, HS_N0 + 0.04, 0.0, 2.4, 'shedW', 'storeroom front wall (graffiti door)')
corrugated((-10.1, N_W, 2.55), (1, 0, 0), (0, -0.98, -0.1), 2.85, 2.1, 'shedR', 'storeroom roof (blue-grey corrugated)')

# ================================================================== 9. BROWN SHED (user Layer 02: s -7.35..-1.63, n 9.3..13.6, photo 25)
BS_S0, BS_S1, BS_N0 = -7.35, -1.63, 9.3
for s0, s1 in ((BS_S0, BS_S0 + 0.03), (BS_S1 - 0.03, BS_S1)):
    box(s0, s1, BS_N0, N_W, 0.0, 2.45, 'shedW', 'shed OSB end wall')
for sp in (BS_S0 + 0.05, -5.2, -3.4, BS_S1 - 0.05):
    box(sp - 0.03, sp + 0.03, BS_N0 - 0.03, BS_N0 + 0.03, 0.0, 2.45, 'shedS', 'shed front post')
box(BS_S0, BS_S1, BS_N0 - 0.04, BS_N0 + 0.04, 2.35, 2.45, 'shedS', 'shed front beam')
box(-4.55, -4.5, BS_N0 + 0.3, N_W - 0.2, 0.05, 2.3, 'shedC', 'black curtain divider')
corrugated((BS_S0 - 0.15, N_W, 2.75), (1, 0, 0), (0, -0.995, -0.07), (BS_S1 - BS_S0) + 0.3, (N_W - BS_N0) + 0.25, 'shedR', 'shed roof (brown corrugated)')

# ================================================================== 10. STREET WALL, PILLARS, GATE, BRICK HUT
# The plain wall segments are the user's own (ADDITIONS, 0.2 m thick on the yard side of the plot line,
# n -4.8..7.17 and 12.67..13.52, 2.3 m - matches the photo measurement). Only the gate assembly and
# copings are added here, fitted to those walls.
def S_LINE(n):                              # plot line: user's wall line + gate line
    if n <= 7.17:
        return 23.53 + (n + 4.8) * (23.84 - 23.53) / (7.17 + 4.8)
    return 23.84 + (n - 7.17) * (23.99 - 23.84) / (12.67 - 7.17)

UW = 0.2                                    # user's wall thickness (yard side of the line)


def street_box(n0, n1, z0, z1, key, name, inner=UW, outer=0.0):
    sl = S_LINE(0.5 * (n0 + n1))
    box(sl - inner, sl + outer, n0, n1, z0, z1, key, name)

street_box(-4.8, 7.17, WALLST_H, WALLST_H + 0.07, 'street', 'wall coping', inner=UW + 0.05, outer=0.05)
street_box(12.67, 13.52, WALLST_H, WALLST_H + 0.07, 'street', 'wall coping', inner=UW + 0.05, outer=0.05)
street_box(7.17, GATE_N0, 0.0, WALLST_H + 0.05, 'street', 'gate pillar (left)', inner=0.35, outer=0.1)
street_box(7.13, GATE_N0 + 0.04, WALLST_H + 0.05, WALLST_H + 0.15, 'street', 'pillar cap', inner=0.4, outer=0.15)
street_box(GATE_N1, GATE_N1 + PIL_W, 0.0, WALLST_H + 0.05, 'street', 'gate pillar (right)', inner=0.35, outer=0.1)
street_box(GATE_N1 - 0.04, GATE_N1 + PIL_W + 0.04, WALLST_H + 0.05, WALLST_H + 0.15, 'street', 'pillar cap', inner=0.4, outer=0.15)
street_box(GATE_N1 + PIL_W, 12.67, 0.0, WALLST_H, 'street', 'concrete pier / wall right of gate (photo 15: continues out of frame)', inner=0.3, outer=0.1,)
street_box(GATE_N1 + PIL_W, 12.67, WALLST_H, WALLST_H + 0.07, 'street', 'wall coping', inner=0.35, outer=0.15)
gs = S_LINE(0.5 * (GATE_N0 + GATE_N1)) - 0.12
half = 0.5 * (GATE_N1 - GATE_N0)
for k in range(2):
    a, b = GATE_N0 + k * half + 0.01, GATE_N0 + (k + 1) * half - 0.01
    box(gs - 0.01, gs + 0.01, a, b, 0.05, GATE_H, 'gate', 'gate leaf sheet')
    for (z0, z1) in ((0.05, 0.1), (GATE_H - 0.05, GATE_H), (0.83, 0.88), (0.98, 1.03)):
        box(gs - 0.03, gs + 0.01, a, b, z0, z1, 'gate', 'gate rail')
    for nn in (a, 0.5 * (a + b), b - 0.05):
        box(gs - 0.03, gs + 0.01, nn, nn + 0.05, 0.05, GATE_H, 'gate', 'gate stile')
tube([(gs - 0.04, GATE_N0 + half + 0.1, 0.15), (gs - 0.04, GATE_N1 - 0.1, GATE_H - 0.1)], 0.015, 'gate', 'gate diagonal brace')

# brick hut (user Layer 02: s 20.65..23.8, n 2.3..6.4, 2.14 m)
HB_S0, HB_N0, HB_N1, HB_H, BW = 20.65, 2.3, 6.4, 2.14, 0.25
hs1 = S_LINE(0.5 * (HB_N0 + HB_N1)) - UW
hut = solid_box_brep(HB_S0, hs1, HB_N0, HB_N1, 0.0, HB_H)
inner = solid_box_brep(HB_S0 + BW, hs1 + 0.01, HB_N0 + BW, HB_N1 - BW, -0.1, HB_H - 0.15)
door = solid_box_brep(HB_S0 - 0.1, HB_S0 + BW + 0.1, 3.9, 4.8, 0.0, 1.95)
d1 = rg.Brep.CreateBooleanDifference(hut, inner, TOL)
hut2 = d1[0] if d1 else hut
d2 = rg.Brep.CreateBooleanDifference(hut2, door, TOL)
put(d2[0] if d2 else hut2, 'hut', 'brick hut', note='door position assumed')
box(HB_S0 - 0.12, hs1, HB_N0 - 0.1, HB_N1 + 0.1, HB_H, HB_H + 0.08, 'hut', 'hut roof slab')
box(HB_S0 + 0.05, HB_S0 + 0.09, 3.9, 4.8, 0.0, 1.95, 'shedW', 'hut timber door')

# ================================================================== 11. SMALL ELEMENTS
# fire escape cage ladder on the east wall, just north of the pavilion (photos 20, 21)
# the ladder only reaches the top of the steel-frame pavilion (user), not the full firewall
LD_S, LD_Z0 = -1.0, 2.3
LD_TOP = 4.94                               # pavilion top (end fascia top, build_pavilion.py)
for ss in (LD_S - 0.22, LD_S + 0.22):
    tube([(ss, N_E + 0.18, LD_Z0), (ss, N_E + 0.18, LD_TOP)], 0.02, 'ladder', 'ladder stile')
z = LD_Z0 + 0.15
while z < LD_TOP:
    tube([(LD_S - 0.22, N_E + 0.18, z), (LD_S + 0.22, N_E + 0.18, z)], 0.012, 'ladder', 'ladder rung')
    z += 0.3
z = LD_Z0 + 0.4
while z < LD_TOP:
    arc = rg.Arc(P(LD_S - 0.35, N_E + 0.05, z), P(LD_S, N_E + 0.8, z), P(LD_S + 0.35, N_E + 0.05, z))
    ring = rg.Brep.CreatePipe(rg.ArcCurve(arc), 0.012, False, rg.PipeCapMode.Flat, True, TOL, math.radians(1))
    for r_ in ring or []:
        put(r_, 'ladder', 'ladder cage hoop')
    z += 0.9

# benches (photos 21, 22)
def bench(s0, s1, n0, facing, name):
    seat_d, nn = 0.45, n0
    for k in range(3):
        box(s0, s1, nn + facing * k * 0.15, nn + facing * (k * 0.15 + 0.12), 0.42, 0.45, 'bench', name + ' seat slat')
    nb = nn - facing * 0.05
    for k in range(2):
        box(s0, s1, nb, nb - facing * 0.03, 0.6 + k * 0.15, 0.7 + k * 0.15, 'bench', name + ' back slat')
    for ss in (s0 + 0.1, s1 - 0.1):
        box(ss - 0.03, ss + 0.03, nb - facing * 0.03, nn + facing * seat_d, 0.0, 0.42, 'shedS', name + ' cast frame')

bench(-11.6, -10.0, 5.25, 1, 'park bench (by ramp)')
bench(-1.0, 0.6, N_E + 0.35, 1, 'park bench (by shelter)')

# wheelie bins at the pavilion's south end (photos 9, 12)
for i, (col_key, nn) in enumerate((('bin', 0.08), ('sign', 0.72))):
    box(18.7, 19.43, nn, nn + 0.58, 0.0, 1.07, col_key, 'wheelie bin 240 l')

# ailanthus sapling beside the WC entrance (photos 17, 26)
limb((AIL_S + 0.6, N_E + 0.35, 0.0), (AIL_S + 0.7, N_E + 0.5, PLAT_Z + 2.5), 0.06, 0.035, name='ailanthus stem')
ellipsoid(AIL_S + 0.75, N_E + 0.6, PLAT_Z + 3.0, 0.75, 0.6, 1.3, 'crown', 'ailanthus crown')   # photo 34: beside the south pier

# ================================================================== 12. OSM neighbour masses -> measured / estimated heights
TARGET_H = {'relation/3332612': H_NORTH, 'relation/3332602': 21.5, 'relation/3332603': H_EAST}
for o in list(doc.Objects.GetObjectList(s_)):
    oid = o.Attributes.GetUserString('osm_id')
    if oid in TARGET_H and isinstance(o.Geometry, (rg.Extrusion, rg.Brep)):
        h0 = o.Geometry.GetBoundingBox(True).Max.Z
        if h0 > 1.0 and abs(h0 - TARGET_H[oid]) > 0.01:   # skip flat courtyard surfaces
            doc.Objects.Transform(o, rg.Transform.Scale(rg.Plane.WorldXY, 1, 1, TARGET_H[oid] / h0), True)
            o2 = doc.Objects.FindId(o.Id)
            a = o2.Attributes.Duplicate()
            a.SetUserString('height_m', '%.1f' % TARGET_H[oid])
            a.SetUserString('height_source', 'courtyard photos (build_courtyard.py)')
            doc.Objects.ModifyAttributes(o2, a, True)
            print('rescaled %s %.1f -> %.1f m' % (oid, h0, TARGET_H[oid]))

# user massing layer superseded by detailed elements -> hide (not deleted)
li = doc.Layers.FindByFullPath('Layer 02', -1)
if li >= 0:
    doc.Layers[li].IsVisible = False
    doc.Layers[li].CommitChanges()

doc.Views.Redraw()
for k in sorted(count):
    print('%s: %d' % (k, count[k]))
