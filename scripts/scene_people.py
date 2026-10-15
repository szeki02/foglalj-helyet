# -*- coding: utf-8 -*-
# CPython - seat positions for the people in the finished-stage scenes of web/phases.json that sit on modelled
# furniture whose placement is computed (the garden cinema's curved rows). Prints JSON to paste into the W6 "scene".
# Bench placement mirrors build_w6_garden_cinema.py: rows turn towards FOCUS, 3 m behind the screen; a seat point
# (ds along the bench, dn towards its front) maps to s = sc + ds cos(phi) + dn sin(phi), n = nc - ds sin(phi) + dn cos(phi).
import json
import math

SC = (-7.23 + -2.62) / 2                         # screen centre line
FOCUS = (SC, 13.57 + 3.0)
COLS = ['blue', 'olive', 'rust', 'grey']


def facing(s, n):
    return math.atan2(FOCUS[0] - s, FOCUS[1] - n)


people = []


def sit(sc, nc, phi, ds, dn, seat, act='watch', z=0.0, **extra):
    s = sc + ds * math.cos(phi) + dn * math.sin(phi)
    n = nc - ds * math.sin(phi) + dn * math.cos(phi)
    p = {'act': act, 'seat': seat, 's': round(s, 3), 'n': round(n, 3),
         'face': [round(s + 3 * math.sin(phi), 2), round(n + 3 * math.cos(phi), 2)], 'color': COLS[len(people) % 4]}
    if z:
        p['z'] = z
    p.update(extra)
    people.append(p)


# row 1: crate benches (seat 0.412: crate on its side 0.33 + board + cushion) and crate chairs (0.34)
for i, ds in enumerate((-1.45, 0.0, 1.45)):
    s = SC + ds
    ph = facing(s, 11.0)
    sit(s, 11.0, ph, -0.3, 0.0, 0.412, 'talk' if i == 0 else 'watch')
    sit(s, 11.0, ph, 0.3, 0.0, 0.412)
for ds in (-2.45, 2.45):
    s = SC + ds
    sit(s, 11.0, facing(s, 11.0), 0.0, 0.01, 0.34)
# row 2: pallet benches, seat 0.368 (two pallets + cushion), cut seat 0.45 deep against the backrest
for i, ds in enumerate((-1.5, 0.0, 1.5)):
    s = SC + ds
    ph = facing(s, 9.75)
    sit(s, 9.75, ph, -0.3, -0.2, 0.368, 'eat' if i == 1 else 'watch', **({'tool2': 'bowl'} if i == 1 else {}))
    sit(s, 9.75, ph, 0.3, -0.2, 0.368)
# row 3: crate benches on the pallet riser (0.144), straight
for i, ds in enumerate((-1.45, 0.0, 1.45)):
    s = SC + ds
    if i != 1:
        sit(s, 8.02, 0.0, -0.3, 0.0, 0.412, z=0.144)
    sit(s, 8.02, 0.0, 0.3, 0.0, 0.412, 'talk' if i == 2 else 'watch', z=0.144)

print(json.dumps(people))
