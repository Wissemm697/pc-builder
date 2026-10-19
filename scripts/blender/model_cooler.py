"""
model_cooler.py : Ventirad « tour » (12,5 x 7 x 15,5 cm) : base en contact avec le
processeur, 4 caloducs (heatpipes) en U, empilement d'ailettes en aluminium et un
ventilateur de 120 mm qui pousse l'air de l'avant (+X) vers l'arrière (-X).

Orientation (une fois monté sur le processeur) : la hauteur du ventirad est selon +Z
(il « sort » de la carte mère vers la vitre). Origine = centre de la face de contact.

    blender -b -P scripts/blender/model_cooler.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402

import common as C  # noqa: E402
from model_fan import build_fan_parts  # noqa: E402

FIN_D = 4.5          # profondeur des ailettes (X)
FIN_W = 12.5         # largeur (Y), adaptée à un ventilateur de 120 mm
Z0, Z1 = 3.5, 15.0   # bas et haut de l'empilement
PITCH = 0.24
FIN_T = 0.035
FAN_C = (FIN_D / 2 + 1.25, 0.0, Z0 + 6.0)
PIPES = [(-1.35, 4.6), (-0.45, 1.15), (0.45, 3.45), (1.35, 2.3)]   # (x, demi-écartement en Y)
PIPE_R = 0.3
ZB = 0.62            # hauteur des caloducs dans la base


def fin_outline():
    d, w = FIN_D / 2, FIN_W / 2
    return [(-d + 0.15, -w), (d, -w), (d, -w + 0.9), (d - 0.32, -1.2), (d - 0.32, 1.2), (d, w - 0.9), (d, w),
            (-d + 0.15, w), (-d, w - 0.15), (-d, w - 1.6), (-d + 0.2, w - 1.9), (-d + 0.2, -w + 1.9), (-d, -w + 1.6),
            (-d, -w + 0.15)]


def pipe_path(x, s):
    top = Z1 + 0.05
    if s < 1.9:
        pts = [(x, -s, top), (x, -s, ZB), (x, s, ZB), (x, s, top)]
        return C.fillet_path(pts, 0.7, n=10)
    zb = 2.4 + 0.15 * s
    pts = [(x, -s, top), (x, -s, zb), (x, -1.75, ZB), (x, 1.75, ZB), (x, s, zb), (x, s, top)]
    return C.fillet_path(pts, 1.1, n=10)


def build():
    # --- base : plaque de contact nickelée + bloc aluminium + barrette de fixation
    C.add('base_plate', C.bm_box_minmax(-2.0, -2.0, 0.0, 2.0, 2.0, 0.3, bevel=0.04), 'nickel')
    C.add('base_block', C.bm_box_minmax(-2.15, -2.0, 0.3, 2.15, 2.0, 1.25, bevel=0.08, segs=2), 'alu')
    for k in range(5):
        y = -1.6 + k * 0.8
        C.add(f'base_fin{k}', C.bm_box_minmax(-2.15, y - 0.12, 1.25, 2.15, y + 0.12, 1.65, bevel=0.03), 'alu')
    C.add('mount_bar', C.bm_box_minmax(-0.45, -4.65, 1.25, 0.45, 4.65, 1.47, bevel=0.05), 'steel')
    for sy in (-1, 1):
        y = sy * 4.45
        C.add(f'screw{sy}', C.bm_cylinder(0.14, 2.5, axis='z', center=(0, y, 0.6), segs=16), 'steel', smooth=40)
        C.add(f'screw_head{sy}', C.bm_lathe([(0, 2.15), (0.28, 2.13), (0.32, 2.05), (0.32, 1.78), (0.0, 1.78)], axis='z',
                                              center=(0, y, 0), segs=24), 'steel', smooth=40)
        coil = []
        for i in range(0, 4 * 24 + 1):
            a = i / 24 * 6.2832
            coil.append((0.24 * C.math.cos(a), y + 0.24 * C.math.sin(a), 1.48 + 0.3 * i / (4 * 24)))
        C.tube(f'spring{sy}', coil, 0.035, 'steel', bevel_res=1)

    # --- caloducs (cuivre nickelé) : en U, ils montent de la base jusqu'en haut des ailettes
    for i, (x, s) in enumerate(PIPES):
        C.tube(f'pipe{i}', pipe_path(x, s), PIPE_R, 'nickel', bevel_res=4)
        for sy in (-1, 1):
            C.add(f'pipe_cap{i}{sy}', C.bm_lathe([(0, Z1 + 0.32), (0.16, Z1 + 0.3), (0.27, Z1 + 0.22), (PIPE_R, Z1 + 0.08), (PIPE_R, Z1 + 0.0), (0, Z1)],
                                                  axis='z', center=(x, sy * s, 0), segs=20), 'nickel', smooth=50)

    # --- ailettes en aluminium
    outline = fin_outline()
    n = int((Z1 - Z0) / PITCH) + 1
    for k in range(n):
        z = Z0 + k * PITCH
        t = 0.09 if k == n - 1 else FIN_T
        C.add(f'fin{k}', C.bm_prism(outline, t, axis='z', offset=z), 'alu_fin')

    # --- ventilateur 120 mm (le même que les ventilateurs du boîtier) fixé par 4 clips
    parts, rotor = build_fan_parts('cfan', FAN_C, 'cooler_fan_rotor')
    C.keep(rotor, spin='x')
    fx = FAN_C[0] + 1.25
    for sy in (-1, 1):
        for (zh, zo) in ((FAN_C[2] + 5.25, Z1 + 0.62), (FAN_C[2] - 5.25, Z0 - 0.45)):
            up = 1 if zo > zh else -1
            pts = [(fx - 0.25, sy * 5.25, zh), (fx + 0.12, sy * 5.25, zh), (fx + 0.12, sy * 5.25, zo),
                   (FIN_D / 2 - 1.6, sy * 5.25, zo), (FIN_D / 2 - 1.6, sy * 5.25, zo - up * 0.4)]
            C.tube(f'clip{sy}{up}', C.fillet_path(pts, 0.15, n=4), 0.055, 'steel', bevel_res=2)

    C.anchor('anchor_fan_cable', (FAN_C[0] - 0.9, 5.6, Z0 + 0.4))
    C.anchor('anchor_cooler_top', (0, 0, 15.5))
    C.INFO['size_cm'] = [FIN_D / 2 + FAN_C[0] + 1.25 - 0.0, FIN_W, 15.5]
    return dict(preview_view=(1.0, -0.65, 0.5), preview_fov=28, preview_up=(0, 0, 1))


if __name__ == '__main__':
    C.run(build, 'cooler')
