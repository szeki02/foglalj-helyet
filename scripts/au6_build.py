# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - shared helpers for the workshop build scripts (W7 on). Load with
#   execfile('C:/Users/David/DEV/Alfoldi_utca_6/scripts/au6_build.py')
# inside a build script; everything lands in the script's namespace. Before calling the geometry helpers the
# script sets LY = {key: layer index}; pieces are collected with put() and added by add_pieces() (one merged object
# per group / layer / name). Same yard frame and conventions as build_w6_garden_cinema.py (which predates this
# module and keeps its own copies).
import math
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from System.Drawing import Color
from Rhino.Render import RenderMaterial

doc = sc.doc
TOL = doc.ModelAbsoluteTolerance

C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)                    # local x = L - s, local y = n

ALL = Rhino.DocObjects.ObjectEnumeratorSettings()
ALL.HiddenObjects = True
ALL.LockedObjects = True
ALL.VisibleFilter = False

CW, CH, CT = 0.33, 0.28, 0.012                   # milk crate 330 x 330 x 280, 12 mm walls
PAL_L, PAL_W, PAL_H = 1.2, 0.8, 0.144            # EUR pallet
BOARD = 0.022                                    # pallet board thickness


def P(s, n, z=0.0):
    return PL.PointAt(L - s, n, z)


def sn_of(pt):
    ok, u, v = PL.ClosestParameter(pt)
    return L - u, v


def rmat(name, rgb=None, gloss=0.0):
    for rm in doc.RenderMaterials:
        if rm.Name == name:
            return rm
    if rgb is None:
        return None
    m = Rhino.DocObjects.Material()
    m.Name = name
    m.DiffuseColor = Color.FromArgb(*rgb)
    m.AmbientColor = Color.Black
    m.Reflectivity = 0.0
    m.ReflectionGlossiness = gloss
    m.Shine = gloss * Rhino.DocObjects.Material.MaxShine
    m.SpecularColor = Color.White if gloss > 0 else Color.Black
    rm = RenderMaterial.CreateBasicMaterial(m, doc)
    rm.Name = name
    doc.RenderMaterials.Add(rm)
    return rmat(name)


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
        m = mat if not isinstance(mat, str) else rmat(mat)
        if m is not None:
            doc.Layers[idx].RenderMaterial = m
    return idx


def group_for(name):
    try:
        gi = doc.Groups.Find(name)
    except Exception:
        gi = -1
    return gi if gi >= 0 else doc.Groups.Add(name)


def store_from(obj, stage_tag, stored_root):
    """move a workshop object onto '<its workshop>::Stored_from_wN::<leaf>' (packed away from workshop N on)"""
    src = doc.Layers[obj.Attributes.LayerIndex]
    di = layer(stored_root + '::' + src.Name, src.Color, src.RenderMaterial)
    a = obj.Attributes.Duplicate()
    a.SetUserString('orig_layer', src.FullPath)
    a.SetUserString('stored_in', stage_tag)
    a.LayerIndex = di
    doc.Objects.ModifyAttributes(obj, a, True)


# ------------------------------------------------------------------ piece collection
pieces = {}                                      # (group name, layer key, object name) -> [brep]
order = []


def put(brep, key, name, group):
    if brep is None:
        print('FAILED: ' + name)
        return
    k = (group, key, name)
    if k not in pieces:
        pieces[k] = []
        order.append(k)
    pieces[k].append(brep)


def add_pieces(tag, LY):
    """one merged object per (group, layer, name); returns ({layer key: count}, [failures], {group: index})"""
    made, fails, gids = {}, [], {}
    for k in order:
        gname, key, name = k
        breps = pieces[k]
        merged = rg.Brep.MergeBreps(breps, min(TOL, 0.001)) if len(breps) > 1 else breps[0]
        if merged is None:
            fails.append('merge failed: %s / %s (%d breps)' % (key, name, len(breps)))
            continue
        a = Rhino.DocObjects.ObjectAttributes()
        a.LayerIndex = LY[key]
        a.Name = name
        a.SetUserString('build', tag)
        if gname not in gids:
            gids[gname] = group_for(gname)
        a.AddToGroup(gids[gname])
        oid = doc.Objects.AddBrep(merged, a)
        if oid == System.Guid.Empty:
            fails.append('add failed: %s / %s (%d breps, valid %s)' % (key, name, len(breps), merged.IsValid))
        else:
            made[key] = made.get(key, 0) + 1
            doc.Objects.Find(oid).CreateMeshes(Rhino.Geometry.MeshType.Render,
                                               doc.GetMeshingParameters(doc.MeshingParameterStyle), False)
    return made, fails, gids


class Frame(object):
    """piece frame: origin at (s, n, z), turned by phi (radians, from +n towards +s). Local (ds, dn, dz)."""
    def __init__(self, s, n, z=0.0, phi=0.0):
        self.s, self.n, self.z, self.phi = s, n, z, phi
        xf = rg.Transform.Rotation(phi, rg.Vector3d.ZAxis, rg.Point3d.Origin)
        ur, vr = rg.Vector3d(U), rg.Vector3d(V)
        ur.Transform(xf); vr.Transform(xf)
        self.ur, self.vr = ur, vr                # +ds = -ur, +dn = -vr
        self.pl = rg.Plane(P(s, n, z), ur, -vr)  # plane x = -ds, y = +dn, z up

    def box(self, s0, s1, n0, n1, z0, z1):
        return rg.Box(self.pl, rg.Interval(-max(s0, s1), -min(s0, s1)), rg.Interval(min(n0, n1), max(n0, n1)),
                      rg.Interval(min(z0, z1), max(z0, z1))).ToBrep()

    def pt(self, ds, dn, dz=0.0):
        return self.pl.PointAt(-ds, dn, dz)

    def cyl(self, ds, dn, z0, r, h):              # vertical cylinder
        return rg.Cylinder(rg.Circle(rg.Plane(self.pt(ds, dn, z0), rg.Vector3d.ZAxis), r), h).ToBrep(True, True)


def towards(s, n, target):
    """phi that turns a piece at (s, n) so its +dn (front) faces target (s, n)"""
    return math.atan2(target[0] - s, target[1] - n)


def rod(a, b, r):
    """round bar between two world points"""
    axis = b - a
    return rg.Cylinder(rg.Circle(rg.Plane(a, axis), r), axis.Length).ToBrep(True, True)


def crate(fr, s0, n0, z0, open_face, key, name, group):
    """milk crate occupying [s0, s0+CW] x [n0, ..] x [z0, ..]; open_face '+z' (upright), '-z' (upside down) or
    '+n' (on its side, opening towards +n)"""
    if open_face == '+n':
        s1, n1, z1 = s0 + CW, n0 + CH, z0 + CW
    else:
        s1, n1, z1 = s0 + CW, n0 + CW, z0 + CH
    faces = {'-s': (s0, s0 + CT, n0, n1, z0, z1), '+s': (s1 - CT, s1, n0, n1, z0, z1),
             '-n': (s0 + CT, s1 - CT, n0, n0 + CT, z0, z1), '+n': (s0 + CT, s1 - CT, n1 - CT, n1, z0, z1),
             '-z': (s0 + CT, s1 - CT, n0 + CT, n1 - CT, z0, z0 + CT), '+z': (s0 + CT, s1 - CT, n0 + CT, n1 - CT, z1 - CT, z1)}
    for f, b in faces.items():
        if f != open_face:
            put(fr.box(*b), key, name, group)
    rim = 0.03
    zr = z1 - rim if open_face != '-z' else z0
    for b in ((s0 - 0.01, s0, n0, n1, zr, zr + rim), (s1, s1 + 0.01, n0, n1, zr, zr + rim)):
        put(fr.box(*b), key, name, group)
    return z1


def pallet(fp, key, name, group, depth=PAL_W):
    """EUR pallet in plane fp: x = length 1.2, y = width 0.8, z = height 0.144 (deck on top); depth < 0.8 = sawn off
    across the width at y = depth (e.g. 0.45: the W6 bench seats, cut past their second block row)"""
    def b(x0, x1, y0, y1, z0, z1):
        put(rg.Box(fp, rg.Interval(x0, x1), rg.Interval(y0, y1), rg.Interval(z0, z1)).ToBrep(), key, name, group)
    rows = [(y0, w) for y0, w in ((0.0, 0.10), (0.35, 0.10), (0.70, 0.10)) if y0 < depth]
    for y0, w in rows:
        b(0, PAL_L, y0, y0 + w, 0, BOARD)
    for x0 in (0.0, 0.5275, 1.055):
        for y0, w in rows:
            b(x0, x0 + 0.145, y0, y0 + w, BOARD, BOARD + 0.078)
        b(x0, x0 + 0.145, 0, min(PAL_W, depth), BOARD + 0.078, 2 * BOARD + 0.078)
    zd = 2 * BOARD + 0.078
    w5 = (0.145, 0.10, 0.145, 0.10, 0.145)
    gap = (PAL_W - sum(w5)) / 4.0
    y = 0.0
    for w in w5:
        if y < depth:
            b(0, PAL_L, y, min(y + w, depth), zd, PAL_H)
        y += w + gap


def flat_pallet(fr, s0, n0, z0, key, name, group, depth=PAL_W):
    """pallet lying flat, 1.2 along s from s0, 0.8 (or depth) along n from n0 (frame-local)"""
    pallet(rg.Plane(fr.pt(s0 + PAL_L, n0, z0), fr.ur, -fr.vr), key, name, group, depth)


def seat_boards(fr, s0, s1, n0, n1, z0, key, name, group, count=3):
    w = (n1 - n0 - (count - 1) * 0.012) / count
    for i in range(count):
        a = n0 + i * (w + 0.012)
        put(fr.box(s0, s1, a, a + w, z0, z0 + BOARD), key, name, group)
    return z0 + BOARD


def slat_back(fr, n_back, z_seat, half, posts, label, g, key='board', lean=math.radians(10), height=0.46,
              slats=(0.10, 0.22, 0.34), z_foot=0.02):
    """backrest: 70 mm uprights behind n_back from z_foot up past the seat, raked back by `lean` above it, slats
    across their front face"""
    nb0, nb1 = n_back - BOARD, n_back
    for ps in posts:
        put(fr.box(ps - 0.035, ps + 0.035, nb0, nb1, z_foot, z_seat), key, label + ' back upright', g)
    ku, ks = (g, key, label + ' back upright, raked part'), (g, key, label + ' back slat')
    nu, ns = len(pieces.get(ku, [])), len(pieces.get(ks, []))
    for ps in posts:
        put(fr.box(ps - 0.035, ps + 0.035, nb0, nb1, z_seat, z_seat + height), key, ku[2], g)
    for dz in slats:
        put(fr.box(-half, half, nb1, nb1 + BOARD, z_seat + dz, z_seat + dz + 0.10), key, ks[2], g)
    rot = rg.Transform.Rotation(lean, fr.ur, fr.pt(0, nb0, z_seat))   # top leans back (towards -dn)
    for b in pieces[ku][nu:] + pieces[ks][ns:]:
        b.Transform(rot)


CRATE_COLS = ('red', 'blue', 'yellow', 'green')
_cc = [0]


def next_col():
    c = CRATE_COLS[_cc[0] % len(CRATE_COLS)]
    _cc[0] += 1
    return c


def crate_bench(fr, cushion, label, g):
    """as in W6: 3 crates on their side, seat of 3 pallet boards (60 mm overhang at the front), cushion, backrest"""
    for i in range(3):
        crate(fr, -0.495 + i * CW, -CH / 2, 0.0, '+n', next_col(), label + ' crate', g)
    zt = seat_boards(fr, -0.55, 0.55, -CH / 2, CH / 2 + 0.06, CW, 'board', label + ' seat board', g)
    put(fr.box(-0.54, 0.54, -CH / 2 + 0.03, CH / 2 + 0.06, zt, zt + 0.06), cushion, label + ' cushion', g)
    slat_back(fr, -CH / 2, zt, 0.55, (-0.46, 0.0, 0.46), label, g)


def crate_chair(fr, cushion, label, g, pre=''):
    """one crate upside down (seat 0.34 m with the cushion), slatted pallet-board back; front = +dn.
    pre: prefix for the layer keys ('<pre>red' ..., '<pre>board'), so the same chair can go on other layers"""
    zt = crate(fr, -CW / 2, -CW / 2, 0.0, '-z', pre + next_col(), label + ' crate (upside down)', g)
    put(fr.box(-CW / 2 + 0.01, CW / 2 - 0.01, -CW / 2 + 0.03, CW / 2 - 0.01, zt, zt + 0.06), cushion, label + ' cushion', g)
    slat_back(fr, -CW / 2, zt, CW / 2 + 0.01, (-0.12, 0.12), label, g, key=pre + 'board')


def crate_table(fr, label, g):
    zt = 0.0
    for k in range(2):
        zt = crate(fr, -CW / 2, -CW / 2, zt, '+z', next_col(), label + ' crate', g)
    seat_boards(fr, -0.21, 0.21, -0.21, 0.21, zt, 'board', label + ' top board', g, count=4)
