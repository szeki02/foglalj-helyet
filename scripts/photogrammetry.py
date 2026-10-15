# -*- coding: utf-8 -*-
# Minimal single-image photogrammetry against a known vertical plane (the pavilion facade).
# Pure python (IronPython 2.7 compatible). World frame of a facade:
#   X = s  (metres along facade), Y = z (height), Z = facade normal (sign resolved so camera Z > 0)
import math


def _solve(A, b):
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        for k in range(c, n + 1):
            M[c][k] /= pv
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] for i in range(n)]


def homography(pairs):
    """pairs: [((X, Y), (u, v))] -> 3x3 H with h33 = 1 (least squares)"""
    rows, rhs = [], []
    for (X, Y), (u, v) in pairs:
        rows.append([X, Y, 1, 0, 0, 0, -u * X, -u * Y]); rhs.append(u)
        rows.append([0, 0, 0, X, Y, 1, -v * X, -v * Y]); rhs.append(v)
    AtA = [[sum(r[i] * r[j] for r in rows) for j in range(8)] for i in range(8)]
    Atb = [sum(rows[k][i] * rhs[k] for k in range(len(rows))) for i in range(8)]
    h = _solve(AtA, Atb) + [1.0]
    return [h[0:3], h[3:6], h[6:9]]


def apply_h(H, X, Y):
    w = H[2][0] * X + H[2][1] * Y + H[2][2]
    return ((H[0][0] * X + H[0][1] * Y + H[0][2]) / w, (H[1][0] * X + H[1][1] * Y + H[1][2]) / w)


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _norm(a):
    return math.sqrt(sum(x * x for x in a))


def calibrate(pairs, cx, cy, f=None):
    """returns dict(H, f, R(rows=r1,r2,r3 world axes in cam), t, C (camera centre in world), rms)"""
    H = homography(pairs)
    # shift principal point to origin
    Hs = [[H[0][j] - cx * H[2][j] for j in range(3)],
          [H[1][j] - cy * H[2][j] for j in range(3)],
          [H[2][j] for j in range(3)]]
    h1 = [Hs[0][0], Hs[1][0], Hs[2][0]]
    h2 = [Hs[0][1], Hs[1][1], Hs[2][1]]
    h3 = [Hs[0][2], Hs[1][2], Hs[2][2]]
    f_est = None
    d = h1[2] * h2[2]
    if abs(d) > 1e-15:
        f2 = -(h1[0] * h2[0] + h1[1] * h2[1]) / d
        if f2 > 0:
            f_est = math.sqrt(f2)
    if f is None:
        f = f_est
    k1 = [h1[0] / f, h1[1] / f, h1[2]]
    k2 = [h2[0] / f, h2[1] / f, h2[2]]
    k3 = [h3[0] / f, h3[1] / f, h3[2]]
    lam = 2.0 / (_norm(k1) + _norm(k2))
    if k3[2] * lam < 0:
        lam = -lam
    r1 = [x * lam for x in k1]
    r2 = [x * lam for x in k2]
    # orthonormalise r1, r2
    n1 = _norm(r1); r1 = [x / n1 for x in r1]
    dot = sum(r1[i] * r2[i] for i in range(3))
    r2 = [r2[i] - dot * r1[i] for i in range(3)]
    n2 = _norm(r2); r2 = [x / n2 for x in r2]
    r3 = _cross(r1, r2)
    t = [x * lam for x in k3]
    # camera centre C = -R^T t, R columns = r1 r2 r3
    C = [-(r1[i] * t[0] + r2[i] * t[1] + r3[i] * t[2]) for i in range(3)]
    # transpose properly: R = [r1 r2 r3] as columns -> R^T t = (r1.t, r2.t, r3.t)
    C = [-(r1[0] * t[0] + r1[1] * t[1] + r1[2] * t[2]),
         -(r2[0] * t[0] + r2[1] * t[1] + r2[2] * t[2]),
         -(r3[0] * t[0] + r3[1] * t[1] + r3[2] * t[2])]
    cam = dict(H=H, f=f, f_est=f_est, r1=r1, r2=r2, r3=r3, t=t, C=C, cx=cx, cy=cy)
    err = []
    for (X, Y), (u, v) in pairs:
        pu, pv = project(cam, (X, Y, 0.0))
        err.append((pu - u) ** 2 + (pv - v) ** 2)
    cam['rms'] = math.sqrt(sum(err) / len(err))
    return cam


def project(cam, P):
    r1, r2, r3, t, f = cam['r1'], cam['r2'], cam['r3'], cam['t'], cam['f']
    pc = [r1[i] * P[0] + r2[i] * P[1] + r3[i] * P[2] + t[i] for i in range(3)]
    return (cam['cx'] + f * pc[0] / pc[2], cam['cy'] + f * pc[1] / pc[2])


def ray(cam, u, v):
    """world-space ray direction for pixel"""
    f = cam['f']
    dc = [(u - cam['cx']) / f, (v - cam['cy']) / f, 1.0]
    r1, r2, r3 = cam['r1'], cam['r2'], cam['r3']
    # world = R^T dc ; R columns r1 r2 r3 => world_k = r_k . dc
    return [sum(r1[i] * dc[i] for i in range(3)),
            sum(r2[i] * dc[i] for i in range(3)),
            sum(r3[i] * dc[i] for i in range(3))]


def ground_point(cam, u, v, height=0.0):
    """intersect pixel ray with horizontal plane Y = height; returns (s, n) or None"""
    d = ray(cam, u, v)
    C = cam['C']
    if abs(d[1]) < 1e-9:
        return None
    k = (height - C[1]) / d[1]
    if k <= 0:
        return None
    return (C[0] + k * d[0], C[2] + k * d[2])


# ---------------------------------------------------------------------------
# Level-camera model (no roll, pitch absorbed into horizon row v0) - far better
# conditioned than a free homography for very oblique views of one facade.
# World: s along facade, n perpendicular (+ towards camera side), z up.
#   params p = [f, s_c, n_c, h, psi, v0]
#   forward F = (cos psi, sin psi), right R = (-sin psi, cos psi)  (in s,n)
def level_project(p, s, n, z, cx):
    f, sc_, nc, h, psi, v0 = p
    ds, dn = s - sc_, n - nc
    Z = ds * math.cos(psi) + dn * math.sin(psi)
    X = -ds * math.sin(psi) + dn * math.cos(psi)
    return (cx + f * X / Z, v0 + f * (h - z) / Z)


def level_solve(obs, cx, p0, fixed=(), iters=60):
    """obs: [((s, n, z), (u, v))]; Levenberg-Marquardt with numeric jacobian"""
    p = list(p0)
    free = [i for i in range(6) if i not in fixed]
    lam = 1e-3

    def resid(pp):
        r = []
        for (s, n, z), (u, v) in obs:
            pu, pv = level_project(pp, s, n, z, cx)
            r += [pu - u, pv - v]
        return r

    r = resid(p)
    cost = sum(x * x for x in r)
    for _ in range(iters):
        J = []
        for i in free:
            dp = list(p)
            step = 1e-6 * max(1.0, abs(p[i]))
            dp[i] += step
            ri = resid(dp)
            J.append([(ri[k] - r[k]) / step for k in range(len(r))])
        m = len(free)
        A = [[sum(J[a][k] * J[b][k] for k in range(len(r))) for b in range(m)] for a in range(m)]
        g = [-sum(J[a][k] * r[k] for k in range(len(r))) for a in range(m)]
        while True:
            Al = [[A[a][b] * (1 + lam if a == b else 1) for b in range(m)] for a in range(m)]
            d = _solve(Al, g)
            pn = list(p)
            for a, i in enumerate(free):
                pn[i] += d[a]
            rn = resid(pn)
            cn = sum(x * x for x in rn)
            if cn < cost:
                p, r, cost = pn, rn, cn
                lam *= 0.3
                break
            lam *= 10
            if lam > 1e8:
                break
        if lam > 1e8:
            break
    rms = math.sqrt(cost / len(obs))
    return p, rms, r


def level_ground(p, u, v, cx, z=0.0):
    """pixel -> (s, n) on horizontal plane at height z"""
    f, sc_, nc, h, psi, v0 = p
    if v - v0 <= 1e-6:
        return None
    Z = f * (h - z) / (v - v0)
    X = (u - cx) * Z / f
    return (sc_ + Z * math.cos(psi) - X * math.sin(psi), nc + Z * math.sin(psi) + X * math.cos(psi))


def level_height(p, u_base, v_base, v_top, cx):
    """height of a vertical feature from its ground pixel and top pixel"""
    f, sc_, nc, h, psi, v0 = p
    Z = f * h / (v_base - v0)
    return h - (v_top - v0) * Z / f


# ---------------------------------------------------------------------------
# Pitched camera (no roll): params p = [f, s_c, n_c, h, psi, phi], principal point fixed.
def pc_project(p, s, n, z, cx, cy):
    f, sc_, nc, h, psi, phi = p
    ds, dn, up = s - sc_, n - nc, z - h
    Zl = ds * math.cos(psi) + dn * math.sin(psi)
    Xl = -ds * math.sin(psi) + dn * math.cos(psi)
    Zc = Zl * math.cos(phi) + up * math.sin(phi)
    Yd = -(up * math.cos(phi) - Zl * math.sin(phi))
    return (cx + f * Xl / Zc, cy + f * Yd / Zc)


def pc_solve(obs, cx, cy, p0, fixed=(), iters=80):
    p = list(p0)
    free = [i for i in range(6) if i not in fixed]
    lam = 1e-3

    def resid(pp):
        r = []
        for (s, n, z), (u, v) in obs:
            pu, pv = pc_project(pp, s, n, z, cx, cy)
            r += [pu - u, pv - v]
        return r

    r = resid(p)
    cost = sum(x * x for x in r)
    for _ in range(iters):
        J = []
        for i in free:
            dp = list(p)
            step = 1e-6 * max(1.0, abs(p[i]))
            dp[i] += step
            ri = resid(dp)
            J.append([(ri[k] - r[k]) / step for k in range(len(r))])
        m = len(free)
        A = [[sum(J[a][k] * J[b][k] for k in range(len(r))) for b in range(m)] for a in range(m)]
        g = [-sum(J[a][k] * r[k] for k in range(len(r))) for a in range(m)]
        while True:
            Al = [[A[a][b] * (1 + lam if a == b else 1) for b in range(m)] for a in range(m)]
            d = _solve(Al, g)
            pn = list(p)
            for a, i in enumerate(free):
                pn[i] += d[a]
            rn = resid(pn)
            cn = sum(x * x for x in rn)
            if cn < cost:
                p, r, cost = pn, rn, cn
                lam *= 0.3
                break
            lam *= 10
            if lam > 1e8:
                break
        if lam > 1e8:
            break
    return p, math.sqrt(cost / len(obs)), r


def pc_ray(p, u, v, cx, cy):
    """world ray direction (ds, dn, dz) for a pixel"""
    f, sc_, nc, h, psi, phi = p
    x, yd = (u - cx) / f, (v - cy) / f
    # camera frame: forward (0,0,1), right (1,0,0), down (0,1,0) -> level frame
    # level: Zl = cos(phi) - yd*... rotate about right axis by phi (pitch up)
    Zl = math.cos(phi) + yd * math.sin(phi)
    up = math.sin(phi) - yd * math.cos(phi)
    Xl = x
    ds = Zl * math.cos(psi) - Xl * math.sin(psi)
    dn = Zl * math.sin(psi) + Xl * math.cos(psi)
    return (ds, dn, up)


def pc_ground(p, u, v, cx, cy, z=0.0):
    f, sc_, nc, h, psi, phi = p
    ds, dn, up = pc_ray(p, u, v, cx, cy)
    if up >= -1e-9:
        return None
    k = (z - h) / up
    return (sc_ + k * ds, nc + k * dn)


def pc_height(p, u_base, v_base, u_top, v_top, cx, cy):
    """height of vertical feature: base pixel on ground, top pixel above it"""
    g = pc_ground(p, u_base, v_base, cx, cy)
    if g is None:
        return None
    f, sc_, nc, h, psi, phi = p
    ds, dn, up = pc_ray(p, u_top, v_top, cx, cy)
    dist = math.hypot(g[0] - sc_, g[1] - nc)
    return h + up / math.hypot(ds, dn) * dist


def triangulate_bearings(cams_obs):
    """cams_obs: [(p, cx, cy, u, v)] -> least-squares (s, n) intersection of horizontal bearing rays"""
    A = [[0.0, 0.0], [0.0, 0.0]]
    b = [0.0, 0.0]
    for p, cx, cy, u, v in cams_obs:
        ds, dn, up = pc_ray(p, u, v, cx, cy)
        l = math.hypot(ds, dn)
        ds, dn = ds / l, dn / l
        # projector onto line normal: I - d d^T
        m = [[1 - ds * ds, -ds * dn], [-ds * dn, 1 - dn * dn]]
        for i in range(2):
            for j in range(2):
                A[i][j] += m[i][j]
        b[0] += m[0][0] * p[1] + m[0][1] * p[2]
        b[1] += m[1][0] * p[1] + m[1][1] * p[2]
    return tuple(_solve(A, b))


def height_at(cam, u_base, v_base, u_top, v_top):
    """height of a vertical object whose base pixel lies on the ground"""
    g = ground_point(cam, u_base, v_base)
    if g is None:
        return None
    s, n = g
    C = cam['C']
    d = ray(cam, u_top, v_top)
    # closest approach of top ray to the vertical line through (s, n)
    hd = math.sqrt(d[0] ** 2 + d[2] ** 2)
    dist = math.sqrt((s - C[0]) ** 2 + (n - C[2]) ** 2)
    return C[1] + d[1] / hd * dist
