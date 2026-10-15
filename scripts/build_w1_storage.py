# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - Workshop 1 (reorganisation): remove the brown corrugated shed and build a dedicated
# storage unit in the south-east corner between the pavilion's south end and the street wall.
# Re-runnable: rebuilds everything tagged 'w1_storage'; the shed parts are moved (not deleted) once.
#
# Brief (user, 2026-10-14): remove the shed marked by the box on ADDITIONS (s -8.96..-0.84, n 7.93..13.57);
# replace its storage function with a dedicated unit in the marked corner (s 18.51..23.33, n -4.58..0).
# Revision 2 (user): taller, and built like the removed shed - steel frame, wave (corrugated) sheet roof, OSB.
#
# Unit (all dimensions to be confirmed):
#   envelope   the marked box, 50 mm clear of pavilion end, east firewall and street wall
#   roof       mono-pitch corrugated sheet (same wave as the removed shed: 18 mm amplitude, 76 mm pitch),
#              3.00 m at the firewall falling to 2.60 m at the doors (~5 deg), 300 mm front overhang.
#              4.9 x 4.8 m = 23 m2: the removed shed roof (~27 m2) can be re-laid here.
#   frame      60x60 SHS posts on three frame lines (both ends + partition), 60x120 RHS rafters,
#              60x100 RHS eave beams, 40x60 RHS purlins, 40x40 SHS wall rails, on a 100 mm concrete pad
#   skin       OSB on the three faces against walls (as the removed shed's end walls),
#              galvanised wave sheet (vertical) on the open west face
#   access     two pairs of steel-framed doors with wave-sheet infill, 2 x 1.80 m openings, 2.10 m high,
#              painted the street-gate green
#   inside     partition into two compartments (tools / residents' belongings), 4 shelf levels on the back wall
#
# Frame: s = metres along the pavilion's west facade from its NORTH end (south +), n = metres west of the facade
# (east firewall at n = -4.58), z up. Same frame as build_courtyard.py / build_pavilion.py.
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance
TAG = 'w1_storage'
STAGE = 'w1_reorganisation'
ADD = '09_Workshops::' + STAGE
REM = '10_Removed::' + STAGE

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)                    # local x = L - s, local y = n


def P(s, n, z=0.0):
    return PL.PointAt(L - s, n, z)


# ------------------------------------------------------------------ layers / materials
def rmat(name):
    for rm in doc.RenderMaterials:
        if rm.Name == name:
            return rm
    return None


def layer(path, color, mat=None):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        parent = path.rsplit('::', 1)[0]
        pidx = doc.Layers.FindByFullPath(parent, -1)
        if pidx < 0:
            pidx = layer(parent, color)
        lay = Rhino.DocObjects.Layer()
        lay.Name = path.rsplit('::', 1)[-1]
        lay.ParentLayerId = doc.Layers[pidx].Id
        lay.Color = color
        idx = doc.Layers.Add(lay)
    if mat is not None:
        doc.Layers[idx].RenderMaterial = mat
    return idx


LAYERS = {
    'base':  ('Storage_Base', (190, 190, 185), 'AU6 Concrete light'),
    'steel': ('Storage_Steel_Frame', (48, 50, 52), 'AU6 Steel painted dark'),
    'roof':  ('Storage_Roof_Corrugated', (120, 92, 70), 'AU6 Corrugated sheet rusty'),
    'clad':  ('Storage_Cladding_Corrugated', (182, 188, 192), 'AU6 Zinc / profiled sheet'),
    'osb':   ('Storage_Sheathing_OSB', (200, 162, 108), 'AU6 OSB board'),
    'doors': ('Storage_Doors', (40, 110, 85), 'AU6 Steel painted green'),
    'iron':  ('Storage_Ironmongery', (48, 50, 52), 'AU6 Steel painted dark'),
    'rain':  ('Storage_Rainwater', (178, 182, 184), 'AU6 Galvanised steel'),
    'shelf': ('Storage_Shelving', (185, 148, 102), 'AU6 Timber pallet pine'),
}
OBSOLETE = ('Storage_Frame', 'Storage_Cladding', 'Storage_Roof')        # revision 1 (timber) layers
LIDX = {}
for k, (name, rgb, mname) in LAYERS.items():
    LIDX[k] = layer(ADD + '::' + name, Color.FromArgb(*rgb), rmat(mname))


# ------------------------------------------------------------------ 1. remove the brown shed (move to 10_Removed)
SHED_NAMES = ('shed roof (brown corrugated)', 'black curtain divider', 'shed OSB end wall',
              'shed front beam', 'shed front post')
ALL = Rhino.DocObjects.ObjectEnumeratorSettings()     # include objects on hidden / locked layers (layer states!)
ALL.HiddenObjects = True
ALL.LockedObjects = True
ALL.VisibleFilter = False
moved = 0
for o in list(doc.Objects.GetObjectList(ALL)):
    a = o.Attributes
    src = doc.Layers[a.LayerIndex]
    if not src.FullPath.startswith('04_Furniture_Elements::Sheds::') or (a.Name or '') not in SHED_NAMES:
        continue
    dst = REM + '::' + src.FullPath.replace('04_Furniture_Elements::', '').replace('::', '_')
    di = layer(dst, Color.FromArgb(190, 60, 60), src.RenderMaterial)
    a = a.Duplicate()
    a.SetUserString('orig_layer', src.FullPath)
    a.SetUserString('removed_in', STAGE)
    a.LayerIndex = di
    doc.Objects.ModifyAttributes(o, a, True)
    moved += 1

# ------------------------------------------------------------------ 2. storage unit
for o in [o for o in doc.Objects.GetObjectList(ALL) if o.Attributes.GetUserString('build') == TAG]:
    doc.Objects.Delete(o, True, True)                 # quiet, ignore lock / hide modes
for name in OBSOLETE:
    idx = doc.Layers.FindByFullPath(ADD + '::' + name, -1)
    if idx >= 0 and not doc.Objects.FindByLayer(doc.Layers[idx]):
        doc.Layers.Delete(idx, True)

made = []


def add(brep, key, name):
    if brep is None:
        print('FAILED: ' + name)
        return
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LIDX[key]
    a.Name = name
    a.SetUserString('build', TAG)
    gid = doc.Objects.AddBrep(brep, a)
    if gid == System.Guid.Empty:
        print('NOT ADDED (invalid brep): ' + name)
    else:
        made.append(gid)


def box(s0, s1, n0, n1, z0, z1):
    return rg.Box(PL, rg.Interval(L - max(s0, s1), L - min(s0, s1)), rg.Interval(min(n0, n1), max(n0, n1)),
                  rg.Interval(min(z0, z1), max(z0, z1))).ToBrep()


def hexa(s0, s1, n0, n1, zb, zt):
    """block from s0..s1, n0..n1 whose bottom and top follow functions of n (sloped members)"""
    c = [P(s0, n0, zb(n0)), P(s1, n0, zb(n0)), P(s1, n1, zb(n1)), P(s0, n1, zb(n1)),
         P(s0, n0, zt(n0)), P(s1, n0, zt(n0)), P(s1, n1, zt(n1)), P(s0, n1, zt(n1))]
    return rg.Brep.CreateFromBox(c)


def vcyl(s, n, z0, z1, r):
    circ = rg.Circle(rg.Plane(P(s, n, z0), rg.Vector3d.ZAxis), r)
    return rg.Cylinder(circ, z1 - z0).ToBrep(True, True)


def corrugated(origin, wdir, ddir, width, depth, amp=0.018, pitch=0.076):
    """wave sheet as in build_courtyard.py: profile along wdir, extruded along ddir; vectors in (s, n, z)"""
    o = rg.Vector3d(*origin)
    w = rg.Vector3d(*wdir)
    d = rg.Vector3d(*ddir)
    d.Unitize()
    nrm = rg.Vector3d.CrossProduct(w, d)
    nrm.Unitize()
    if nrm.Z < 0 or (abs(nrm.Z) < 1e-9 and nrm.Y < 0):
        nrm = -nrm
    k = int(width / pitch * 4)
    pts = []
    for i in range(k + 1):
        t = width * i / float(k)
        q = o + w * t + nrm * (amp * math.sin(2 * math.pi * t / pitch))
        pts.append(P(q.X, q.Y, q.Z))
    srf = rg.Surface.CreateExtrusion(rg.PolylineCurve(pts), P(d.X * depth, d.Y * depth, d.Z * depth) - P(0, 0, 0))
    return srf.ToBrep() if srf else None


G = 0.05
S0, S1 = 18.51 + G, 23.33 - G                    # 18.56 .. 23.28
NB, NF = -4.58 + G, 0.0 - G                      # back (firewall) -4.53 .. front (doors) -0.05
Z0 = 0.10                                        # top of concrete pad = floor
ROOF_F, ROOF_B = 2.60, 3.00                      # underside of the wave sheet (= top of purlins) front / back
OVER = 0.30                                      # front overhang of the sheet
SQ = 0.06                                        # 60x60 SHS posts
RAF_D, EAVE_D, PUR_D, PUR_W = 0.12, 0.10, 0.06, 0.04
DOORS = [(18.86, 20.66), (21.19, 22.99)]         # door openings along s
DOOR_TOP = Z0 + 2.10
PART = 20.925                                    # partition / middle frame line


def zr(n):                                       # underside of roof sheet
    return ROOF_F + (NF - n) / (NF - NB) * (ROOF_B - ROOF_F)


def raf_bot(n):
    return zr(n) - PUR_D - RAF_D


FRAMES = (S0 + SQ / 2, PART, S1 - SQ / 2)        # frame lines (s) carrying posts + rafters
PN_F, PN_B = NF - 0.04 - SQ / 2, NB + 0.03 + SQ / 2   # post centre lines (n), front sits behind the cladding

# pad
add(box(S0 - 0.03, S1 + 0.03, NB, NF + 0.10, 0.0, Z0), 'base', 'storage concrete pad')

# posts, eave beams, rafters
for s in FRAMES:
    for pn in (PN_F, PN_B):
        add(box(s - SQ / 2, s + SQ / 2, pn - SQ / 2, pn + SQ / 2, Z0, raf_bot(pn) - EAVE_D), 'steel', 'post 60x60 SHS')
    add(hexa(s - SQ / 2, s + SQ / 2, NB, NF + OVER - 0.05, raf_bot, lambda n: zr(n) - PUR_D), 'steel', 'rafter 60x120 RHS')
for pn, tag in ((PN_F, 'front'), (PN_B, 'back')):
    z1 = raf_bot(pn)
    add(box(S0, S1, pn - SQ / 2, pn + SQ / 2, z1 - EAVE_D, z1), 'steel', tag + ' eave beam 60x100 RHS')
    add(box(S0, S1, pn - SQ / 2, pn + SQ / 2, Z0, Z0 + 0.04), 'steel', tag + ' base rail 40x60')

# purlins along s, spaced ~0.9 m down the slope
k = int(math.ceil((NF + OVER - 0.08 - NB) / 0.9))
for i in range(k + 1):
    n = NB + 0.05 + i * (NF + OVER - 0.13 - NB) / k
    add(hexa(S0 - 0.02, S1 + 0.02, n - PUR_W / 2, n + PUR_W / 2, lambda q: zr(q) - PUR_D, zr), 'steel', 'purlin 40x60 RHS')

# roof: wave sheet, corrugations running down the slope (towards the doors)
dn, dz = (NF + OVER) - NB, zr(NF + OVER) - zr(NB)
slope_len = math.sqrt(dn * dn + dz * dz)
add(corrugated((S0 - 0.04, NB, zr(NB) + 0.018), (1, 0, 0), (0, dn, dz), (S1 - S0) + 0.08, slope_len),
    'roof', 'roof wave sheet (re-laid from the removed shed)')

# side rails on the front for the cladding (between posts, not across door openings)
FRONT_SOLID = [(S0, DOORS[0][0]), (DOORS[0][1], DOORS[1][0]), (DOORS[1][1], S1)]
for a, b in FRONT_SOLID:
    for z in (Z0 + 0.6, Z0 + 1.5):
        add(box(a, b, PN_F + SQ / 2 - 0.04, PN_F + SQ / 2, z, z + 0.04), 'steel', 'cladding rail 40x40 SHS')
for a, b in DOORS:
    for s in (a - 0.04, b):
        add(box(s, s + 0.04, PN_F - SQ / 2, PN_F + SQ / 2, Z0, DOOR_TOP), 'steel', 'door jamb 40x60 RHS')
    add(box(a - 0.04, b + 0.04, PN_F - SQ / 2, PN_F + SQ / 2, DOOR_TOP, DOOR_TOP + 0.06), 'steel', 'door header 60x60')

# front skin: vertical galvanised wave sheet, solid bays full height, strip above the doors
FRONT_TOP = raf_bot(PN_F) - 0.01
CN = NF - 0.02                                   # mean plane of the front sheet
for a, b in FRONT_SOLID:
    add(corrugated((a, CN, Z0), (1, 0, 0), (0, 0, 1), b - a, FRONT_TOP - Z0), 'clad', 'front wave sheet')
for a, b in DOORS:
    add(corrugated((a, CN, DOOR_TOP + 0.06), (1, 0, 0), (0, 0, 1), b - a, FRONT_TOP - DOOR_TOP - 0.06), 'clad',
        'wave sheet over door')

# OSB on the three faces against walls (outside the frame lines), sloped tops on the ends
add(hexa(S0, S1, NB, NB + 0.018, lambda n: Z0, lambda n: zr(n) - PUR_D), 'osb', 'back OSB (firewall side)')
add(hexa(S0, S0 + 0.018, NB, NF - 0.04, lambda n: Z0, lambda n: zr(n) - PUR_D), 'osb', 'north end OSB (pavilion side)')
add(hexa(S1 - 0.018, S1, NB, NF - 0.04, lambda n: Z0, lambda n: zr(n) - PUR_D), 'osb', 'south end OSB (street wall side)')
add(hexa(PART + SQ / 2, PART + SQ / 2 + 0.018, PN_B + SQ / 2, PN_F - SQ / 2, lambda n: Z0, lambda n: raf_bot(n)),
    'osb', 'compartment partition')

# doors: steel-framed leaves with wave-sheet infill, two per opening
LZ0, LZ1, LF = Z0 + 0.02, DOOR_TOP - 0.008, 0.04
for di, (a, b) in enumerate(DOORS):
    mid = (a + b) / 2
    for li, (la, lb) in enumerate(((a + 0.005, mid - 0.004), (mid + 0.004, b - 0.005))):
        nm = 'door %d leaf %s' % (di + 1, 'L' if li == 0 else 'R')
        n0, n1 = NF - LF, NF
        add(box(la, lb, n0, n1, LZ0, LZ0 + LF), 'doors', nm + ' frame')
        add(box(la, lb, n0, n1, LZ1 - LF, LZ1), 'doors', nm + ' frame')
        add(box(la, la + LF, n0, n1, LZ0 + LF, LZ1 - LF), 'doors', nm + ' frame')
        add(box(lb - LF, lb, n0, n1, LZ0 + LF, LZ1 - LF), 'doors', nm + ' frame')
        add(box(la + LF, lb - LF, n0, n1, (LZ0 + LZ1) / 2 - 0.02, (LZ0 + LZ1) / 2 + 0.02), 'doors', nm + ' mid rail')
        add(corrugated((la + LF, NF - 0.02, LZ0 + LF), (1, 0, 0), (0, 0, 1), lb - la - 2 * LF, LZ1 - LZ0 - 2 * LF,
                       amp=0.012), 'doors', nm + ' wave infill')
        hs = la if li == 0 else lb
        for z in (LZ0 + 0.25, (LZ0 + LZ1) / 2, LZ1 - 0.3):
            add(box(hs - 0.02, hs + 0.02, NF, NF + 0.02, z, z + 0.12), 'iron', nm + ' hinge')
    add(box(mid - 0.07, mid + 0.07, NF, NF + 0.012, 1.05, 1.20), 'iron', 'door %d hasp and staple' % (di + 1))
    add(box(mid - 0.025, mid + 0.025, NF + 0.012, NF + 0.04, 0.99, 1.07), 'iron', 'door %d padlock' % (di + 1))

# rainwater: gutter under the low edge of the sheet, downpipe at the street end
GE = NF + OVER
GZ = zr(GE) - 0.02
add(box(S0, S1, GE - 0.05, GE + 0.07, GZ - 0.09, GZ), 'rain', 'gutter 120 mm')
add(vcyl(S1 - 0.10, GE + 0.01, 0.0, GZ - 0.05, 0.035), 'rain', 'downpipe 70 mm')

# shelving on the back wall of each compartment, 4 levels
DEPTH = 0.45
SB = PN_B + SQ / 2
for (ca, cb), label in (((S0 + 0.02, PART - SQ / 2), 'tools'), ((PART + SQ / 2 + 0.02, S1 - 0.02), 'residents')):
    for s in (ca + 0.02, (ca + cb) / 2 - 0.02, cb - 0.06):
        add(box(s, s + 0.04, SB, SB + DEPTH, Z0, 2.30), 'shelf', 'shelf upright (%s)' % label)
    for z in (0.45, 1.05, 1.65, 2.22):
        add(box(ca + 0.02, cb - 0.02, SB, SB + DEPTH, z, z + 0.022), 'shelf', 'shelf board (%s)' % label)

doc.Views.Redraw()
print('shed parts moved to %s: %d' % (REM, moved))
print('storage objects: %d' % len(made))
print('roof underside front %.2f / back %.2f m, fall %.1f deg, sheet %.2f x %.2f m = %.1f m2' % (
    ROOF_F, ROOF_B, math.degrees(math.atan((ROOF_B - ROOF_F) / (NF - NB))), S1 - S0 + 0.08, slope_len,
    (S1 - S0 + 0.08) * slope_len))
