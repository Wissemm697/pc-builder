"""
model_fan.py — Ventilateur de boîtier 120 mm (12 x 12 x 2,5 cm).

Orientation : axe de rotation = X. L'air entre par la face +X (côté pales visibles)
et ressort par la face -X (côté croisillons / moteur). Ainsi, les 3 ventilateurs de
façade (aspiration) et celui de l'arrière (extraction) ont la même orientation :
l'air traverse le boîtier de l'avant vers l'arrière.

    blender -b -P scripts/blender/model_fan.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401  (doit précéder bmesh quand bpy est utilisé comme module Python)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import common as C  # noqa: E402

SIZE = 12.0
DEPTH = 2.5
BORE = 5.85        # rayon du passage d'air
HUB_R = 2.0
TIP_R = 5.62
N_BLADES = 7


def _blade_bm(phase_deg, r_hub=HUB_R + 0.02, r_tip=TIP_R, x_lead=0.92, x_trail=-0.86,
              width_hub=44.0, width_tip=50.0, sweep=22.0, thick=0.11, ns=9, nc=12):
    """Une pale : surface vrillée et balayée, épaissie. Axe du ventilateur = X."""
    bm = bmesh.new()
    top, bot = [], []
    for i in range(ns + 1):
        s = i / ns
        r = r_hub + (r_tip - r_hub) * s
        width = math.radians(width_hub + (width_tip - width_hub) * s)
        center = math.radians(phase_deg - sweep * s ** 1.4)
        # le pas (vrillage) diminue vers l'extrémité, comme une vraie pale
        xl = x_lead * (1.0 - 0.10 * s)
        xt = x_trail * (1.0 - 0.10 * s)
        rt, rb = [], []
        for j in range(nc + 1):
            t = j / nc
            phi = center + width * (0.5 - t)            # bord d'attaque (t=0) = angle le plus grand
            camber = 0.16 * math.sin(math.pi * t)       # cambrure
            x = xl + (xt - xl) * t + camber
            y, z = r * math.cos(phi), r * math.sin(phi)
            half = thick * (0.55 + 0.45 * math.sin(math.pi * min(max(t, 0.04), 0.96)))
            rt.append(bm.verts.new((x + half, y, z)))
            rb.append(bm.verts.new((x - half, y, z)))
        top.append(rt)
        bot.append(rb)
    for i in range(ns):
        for j in range(nc):
            bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
            bm.faces.new((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    for i in range(ns):  # bords d'attaque et de fuite
        bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0]))
        bm.faces.new((top[i][nc], top[i + 1][nc], bot[i + 1][nc], bot[i][nc]))
    for j in range(nc):  # extrémité et pied
        bm.faces.new((top[ns][j], top[ns][j + 1], bot[ns][j + 1], bot[ns][j]))
        bm.faces.new((top[0][j], bot[0][j], bot[0][j + 1], top[0][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def build_fan_parts(prefix='fan', center=(0, 0, 0), rotor_name='fan_rotor', frame_mat='plastic_black',
                    blade_mat='plastic_dark', with_rotor=True):
    """Construit cadre + rotor d'un ventilateur 120 mm centré sur `center`.
    Renvoie (liste d'objets du cadre, objet rotor)."""
    cx, cy, cz = center
    h = SIZE / 2
    d = DEPTH / 2

    # --- Cadre : carré arrondi percé d'un passage circulaire
    frame_bm = C.bm_prism(C.rounded_rect_pts(SIZE, SIZE, 0.55, segs=4), DEPTH, axis='x', offset=-d)
    frame = C.add(prefix + '_frame', frame_bm, frame_mat)
    bore = C.bm_cylinder(BORE, DEPTH + 1, axis='x', segs=72)
    holes = []
    for sy in (-1, 1):
        for sz in (-1, 1):
            holes.append(C.bm_cylinder(0.24, DEPTH + 1, axis='x', center=(0, sy * 5.25, sz * 5.25), segs=16))
    # évidements des coins entre les deux brides (on garde une coque ronde de 3 mm)
    recesses = []
    rc = BORE + 0.3
    for k in range(4):
        a0 = math.radians(90 * k + 12.0)
        a1 = math.radians(90 * k + 78.0)
        pts = []
        n = 10
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            pts.append((rc * math.cos(a), rc * math.sin(a)))
        ac = math.radians(90 * k + 45)
        pts.append((9.0 * math.cos(ac), 9.0 * math.sin(ac)))
        # prisme le long de X entre les brides (épaisseur des brides : 0,38 cm)
        recesses.append(C.bm_prism(pts, DEPTH - 0.76, axis='x', offset=-d + 0.38))
    C.cut(frame, bore, *holes, *recesses)
    C.resmooth(frame, 40)
    frame.location = (cx, cy, cz)

    parts = [frame]
    # --- Croisillons + boîtier moteur (face de sortie -X)
    motor = C.add(prefix + '_motor', C.bm_cylinder(HUB_R, 0.34, axis='x', center=(cx - d + 0.17, cy, cz), segs=40), frame_mat, smooth=40)
    parts.append(motor)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        r0, r1 = HUB_R - 0.1, BORE + 0.1
        bm = C.bm_box(0.3, r1 - r0, 0.36, center=(0, (r0 + r1) / 2, 0))
        C.bm_rotate(bm, math.degrees(a), 'x')
        C.bm_translate(bm, (cx - d + 0.16, cy, cz))
        parts.append(C.add(f'{prefix}_strut{k}', bm, frame_mat))
    sticker = C.add(prefix + '_sticker_back', C.bm_cylinder(1.55, 0.02, axis='x', center=(cx - d - 0.005, cy, cz), segs=40), 'plastic_grey', smooth=40)
    parts.append(sticker)

    rotor = None
    if with_rotor:
        rotor_parts = []
        # moyeu bombé (profil de révolution) : de x = -0.85 à +1.0
        hub = C.bm_lathe([(0.0, 1.05), (1.2, 1.03), (1.75, 0.98), (1.98, 0.88), (HUB_R, 0.7), (HUB_R, -0.85), (0.0, -0.85)],
                         axis='x', segs=48)
        rotor_parts.append(C.add(rotor_name + '_hub', hub, blade_mat, smooth=40))
        label = C.bm_cylinder(1.25, 0.02, axis='x', center=(1.062, 0, 0), segs=40)
        rotor_parts.append(C.add(rotor_name + '_label', label, 'plastic_grey', smooth=40))
        ring = C.bm_ring(1.32, 1.22, 0.025, axis='x', center=(1.07, 0, 0), segs=40)
        rotor_parts.append(C.add(rotor_name + '_ring', ring, 'accent', smooth=40))
        for b in range(N_BLADES):
            rotor_parts.append(C.add(f'{rotor_name}_blade{b}', _blade_bm(360.0 * b / N_BLADES), blade_mat, smooth=50))
        rotor = C.merge(rotor_name, rotor_parts, origin=(0, 0, 0))
        rotor.location = (cx, cy, cz)
    return parts, rotor


def build():
    parts, rotor = build_fan_parts('fan', (0, 0, 0), 'fan_rotor')
    C.keep(rotor, spin='x')
    # point de sortie du câble (coin du cadre, côté sortie d'air)
    C.anchor('anchor_fan_cable', (-0.9, -5.4, -5.4))
    C.INFO['airflow'] = 'de +X vers -X'
    C.INFO['size_cm'] = [DEPTH, SIZE, SIZE]
    return dict(preview_view=(1.0, 0.45, 0.75), preview_fov=26)


if __name__ == '__main__':
    C.run(build, 'fan')
