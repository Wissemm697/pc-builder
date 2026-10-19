"""
model_gpu.py : Carte graphique milieu de gamme, double ventilateur
(28 x 12 x 5 cm), connecteur PCIe x16 et une prise d'alimentation PCIe 8 broches.

Orientation (une fois enfichée dans le slot PCIe x16 de la carte mère verticale) :
la carte est horizontale ; sa longueur va de l'équerre (côté arrière du boîtier, X négatif)
vers l'avant (+X) ; sa « hauteur » va des contacts dorés (Z = 0) vers la vitre (+Z) ;
les ventilateurs regardent vers le bas (-Y) et aspirent l'air par en dessous.
Origine = milieu du bord inférieur des contacts dorés.

    blender -b -P scripts/blender/model_gpu.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Matrix  # noqa: E402

import common as C  # noqa: E402
import layout as L  # noqa: E402
from model_fan import _blade_bm  # noqa: E402

BX = L.GPU_BRACKET_X       # -7.05
FX = L.GPU_FRONT_X         # 20.95
ZT = L.GPU_TOP_Z           # 12.4
YD = -L.GPU_THICK_DOWN     # -4.4
YU = L.GPU_THICK_UP        # 0.6
ZS0 = 1.2                  # bas du carénage
FANS = [1.0, 12.6]         # centres des ventilateurs (X)
FAN_Z = (ZS0 + ZT) / 2
FAN_R = 4.75
FAN_Y = -3.9
PCB_END = 15.0
PWR = dict(x0=12.9, x1=14.8, y0=-1.15, y1=-0.11, z0=10.4, z1=12.2)


def fingers_tex():
    w, h = 1024, 96
    cv = C.Canvas(w, h, C.srgb('#141619'))
    n = 82
    for i in range(n):
        x0 = 6 + i * (w - 12) / n
        cv.rect(x0 + 1.5, 4, x0 + (w - 12) / n - 1.5, h - 2, C.srgb('#d8b35d'), r=1.0)
    return cv.save('gpu_fingers')


def fan_rotor(name, xc):
    """Rotor de ventilateur GPU : moyeu + 11 pales fines. Axe -Y (aspiration par le bas)."""
    parts = []
    hub = C.bm_lathe([(0, 0.62), (1.0, 0.6), (1.45, 0.52), (1.58, 0.4), (1.6, -0.55), (0, -0.55)], axis='x', segs=40)
    parts.append(C.add(name + '_hub', hub, 'plastic_dark', smooth=40))
    parts.append(C.add(name + '_lab', C.bm_cylinder(1.05, 0.02, axis='x', center=(0.635, 0, 0), segs=36), 'plastic_grey', smooth=40))
    parts.append(C.add(name + '_ring', C.bm_ring(1.12, 1.04, 0.025, axis='x', center=(0.64, 0, 0), segs=36), 'accent', smooth=40))
    for b in range(11):
        bm = _blade_bm(360.0 * b / 11, r_hub=1.58, r_tip=4.5, x_lead=0.42, x_trail=-0.42, width_hub=24, width_tip=30,
                       sweep=30, thick=0.07, ns=8, nc=10)
        parts.append(C.add(f'{name}_b{b}', bm, 'plastic_black', smooth=50))
    rot = C.merge(name, parts)
    # axe X (modèle du ventilateur de boîtier) -> axe -Y : l'air est poussé vers +Y (vers le radiateur)
    rot.data.transform(Matrix.Rotation(math.radians(-90), 4, 'Z'))
    rot.location = (xc, FAN_Y, FAN_Z)
    C.keep(rot, spin='y', extras={'spinDir': -1})
    return rot


def build():
    # --- circuit imprimé et contacts PCIe x16
    k0 = -L.GPU_FINGER_HALF + 1.165       # encoche entre la partie « x1 » et le reste
    outline = [(BX + 0.05, 0.85), (-L.GPU_FINGER_HALF - 0.15, 0.85), (-L.GPU_FINGER_HALF - 0.05, 0.0), (k0 - 0.1, 0.0),
               (k0 - 0.1, 0.62), (k0 + 0.1, 0.62), (k0 + 0.1, 0.0), (L.GPU_FINGER_HALF, 0.0), (L.GPU_FINGER_HALF + 0.12, 0.12),
               (L.GPU_FINGER_HALF + 0.12, 0.55), (L.GPU_FINGER_HALF + 0.55, 0.55), (L.GPU_FINGER_HALF + 0.55, 0.85),
               (PCB_END, 0.85), (PCB_END, 11.1), (BX + 0.05, 11.1)]
    C.add('gpu_pcb', C.bm_prism(outline, 0.16, axis='y', offset=-0.08), 'pcb_black')
    fimg = fingers_tex()
    fmat = C.textured_mat('gpu_fingers', fimg, metallic=0.6, roughness=0.3)
    for side in (-1, 1):
        for (a, b) in ((-L.GPU_FINGER_HALF + 0.05, k0 - 0.12), (k0 + 0.12, L.GPU_FINGER_HALF - 0.05)):
            bm = C.bm_box_minmax(a, side * 0.08 - 0.004, 0.06, b, side * 0.08 + 0.004, 0.72)
            fa = [f for f in bm.faces if abs(f.normal.y) > 0.9]
            C.uv_project(bm, rect=(a, 0.06, b, 0.72), faces=fa, axes=('x', 'z'))
            C.uv_constant(bm, 0.01, 0.5, faces=[f for f in bm.faces if f not in fa])
            C.add(f'fingers{side}{a:.1f}', bm, fmat)

    # --- équerre métallique (côté arrière du boîtier) avec les sorties vidéo
    br = C.add('bracket', C.bm_box_minmax(BX - 0.1, -3.7, -1.0, BX, 0.36, 12.0), 'steel')
    vents = []
    for k in range(9):
        z = 8.4 + k * 0.38
        vents.append(C.bm_box_minmax(BX - 0.5, -3.3, z, BX + 0.5, -1.9, z + 0.2))
    for k in range(7):
        z = 1.2 + k * 0.95
        vents.append(C.bm_box_minmax(BX - 0.5, -3.4, z, BX + 0.5, -2.0, z + 0.55))
    ports = [('dp', 1.6), ('dp', 3.6), ('hdmi', 5.6), ('dp', 7.4)]
    for (kind, zc) in ports:   # ouvertures des prises dans l'équerre
        vents.append(C.bm_box_minmax(BX - 0.5, -1.28, zc - 0.9, BX + 0.5, -0.32, zc + 0.9))
    C.cut(br, *vents)
    C.add('bracket_tab', C.bm_box_minmax(BX - 1.0, -3.7, 11.92, BX, 0.36, 12.02), 'steel')
    C.add('bracket_tongue', C.bm_box_minmax(BX - 0.1, -1.1, -1.65, BX, -0.1, -0.95), 'steel')
    for (kind, zc) in ports:
        C.add(f'port_shell_{zc}', C.bm_box_minmax(BX - 0.12, -1.22, zc - 0.85, BX + 1.6, -0.38, zc + 0.85, bevel=0.03), 'steel')
        if kind == 'dp':
            pts = [(-0.27, -0.8), (0.27, -0.8), (0.27, 0.55), (0.05, 0.8), (-0.27, 0.8)]
        else:   # HDMI : trapèze
            pts = [(-0.05, -0.7), (0.24, -0.7), (0.24, 0.7), (-0.05, 0.7), (-0.24, 0.48), (-0.24, -0.48)]
        hole = C.bm_prism([(y - 0.8, z) for (y, z) in pts], 0.5, axis='x', offset=BX - 0.13)
        C.add(f'port_hole_{zc}', hole, 'chip', location=(0, 0, zc))
        C.add(f'port_tongue_{zc}', C.bm_box_minmax(BX - 0.14, -0.86, zc - 0.55, BX + 0.3, -0.74, zc + 0.55), 'plastic_black')

    # --- radiateur : ailettes en aluminium + caloducs visibles sur la tranche
    x = BX + 0.6
    k = 0
    while x < FX - 0.6:
        z1 = 11.9
        if PWR['x0'] - 0.3 < x < PWR['x1'] + 0.3:
            z1 = 9.8
        y1 = 0.15 if x > PCB_END + 0.1 else -0.4
        C.add(f'gfin{k}', C.bm_box_minmax(x, -3.5, 1.6, x + 0.035, y1, z1), 'alu_fin')
        x += 0.19
        k += 1
    for i, yy in enumerate((-1.0, -1.8, -2.6)):
        xa, xb = -1.5 + i * 0.8, 9.5 - i * 0.9
        pts = [(xa, yy, 9.6), (xa, yy, 12.0), (xb, yy, 12.0), (xb, yy, 9.6)]
        C.tube(f'gpipe{i}', C.fillet_path(pts, 0.9, n=10), 0.3, 'nickel', bevel_res=3)

    # --- carénage (plastique noir) avec les deux ouvertures de ventilateurs
    sh_out = [(BX + 0.15, ZS0), (FX - 0.6, ZS0), (FX, ZS0 + 0.6), (FX, ZT - 0.6), (FX - 0.6, ZT), (BX + 0.15, ZT)]
    shroud = C.add('shroud', C.bm_prism(sh_out, 0.8, axis='y', offset=YD, bevel=0.06), 'plastic_black')
    C.cut(shroud, *[C.bm_cylinder(FAN_R, 3.0, axis='y', center=(fx, YD, FAN_Z), segs=72) for fx in FANS])
    C.resmooth(shroud, 35)
    C.add('shroud_lip_top', C.bm_box_minmax(BX + 0.15, YD + 0.7, ZT - 0.35, FX - 0.45, -2.9, ZT, bevel=0.05), 'plastic_black')
    C.add('shroud_lip_bot', C.bm_box_minmax(BX + 0.15, YD + 0.7, ZS0, FX - 0.45, -2.9, ZS0 + 0.35, bevel=0.05), 'plastic_black')
    C.add('shroud_end', C.bm_box_minmax(FX - 0.45, YD + 0.2, ZS0 + 0.2, FX, YU - 0.15, ZT - 0.2, bevel=0.08), 'plastic_black')
    for fx in FANS:
        C.add(f'bezel{fx}', C.bm_ring(FAN_R + 0.22, FAN_R, 0.08, axis='y', center=(fx, YD - 0.02, FAN_Z), segs=72), 'alu_grey', smooth=40)
    # décor : insert métallique en chevron entre les ventilateurs + liserés d'accent
    mid = (FANS[0] + FANS[1]) / 2
    chev = [(mid - 0.35, ZS0 + 0.5), (mid + 0.35, ZS0 + 0.5), (mid + 1.0, FAN_Z), (mid + 0.35, ZT - 0.5), (mid - 0.35, ZT - 0.5), (mid + 0.3, FAN_Z)]
    C.add('chevron', C.bm_prism(chev, 0.06, axis='y', offset=YD - 0.05), 'alu_grey')
    C.add('accent_a', C.bm_box_minmax(FANS[1] + FAN_R + 0.6, YD - 0.03, ZS0 + 0.9, FX - 0.9, YD, ZS0 + 1.05), 'accent')
    C.add('accent_b', C.bm_box_minmax(BX + 0.6, YD - 0.03, ZT - 1.05, FANS[0] - FAN_R - 0.4, YD, ZT - 0.9), 'accent')
    C.add('accent_top', C.bm_box_minmax(0.0, YD + 0.25, ZT, 11.0, YD + 0.5, ZT + 0.03), 'accent')

    for i, fx in enumerate(FANS):
        fan_rotor(f'gpu_fan_rotor_{i + 1}', fx)

    # --- plaque arrière (backplate) avec fenêtre « flow-through » au bout
    bp_out = [(BX + 0.1, 0.95), (FX - 0.5, 0.95), (FX, 1.45), (FX, ZT - 0.5), (FX - 0.5, ZT), (BX + 0.1, ZT)]
    bp = C.add('backplate', C.bm_prism(bp_out, 0.22, axis='y', offset=0.22, bevel=0.04), 'alu_dark')
    C.cut(bp, C.bm_box_minmax(PCB_END + 0.4, -1, 2.6, FX - 0.8, 2, 11.2, bevel=0.3, segs=3))
    C.resmooth(bp, 35)
    for (dx, dz) in ((-1.6, -1.6), (1.6, -1.6), (-1.6, 1.6), (1.6, 1.6)):
        C.add(f'bp_screw{dx}{dz}', C.bm_cylinder(0.22, 0.06, axis='y', center=(2.0 + dx, 0.47, 6.3 + dz), segs=20), 'steel', smooth=40)
    C.add('bp_accent', C.bm_box_minmax(BX + 1.0, 0.44, ZT - 0.9, PCB_END - 1.0, 0.47, ZT - 0.75), 'accent')
    C.text('bp_txt', 'GRAPHICS', 0.55, (6.0, 0.465, 9.6), 'plastic_grey', rot=[(-90, 'x')])

    # --- prise d'alimentation PCIe 8 broches (sur la tranche supérieure)
    p = PWR
    C.add('pwr_housing', C.bm_box_minmax(p['x0'], p['y0'], p['z0'], p['x1'], p['y1'], p['z1'], bevel=0.03), 'plastic_black')
    pw, ph = (p['x1'] - p['x0']) / 4, (p['y1'] - p['y0']) / 2
    for i in range(4):
        for j in range(2):
            cx, cy = p['x0'] + (i + 0.5) * pw, p['y0'] + (j + 0.5) * ph
            C.add(f'pwr_h{i}{j}', C.bm_box_minmax(cx - 0.16, cy - 0.16, p['z1'] - 0.02, cx + 0.16, cy + 0.16, p['z1'] + 0.006), 'chip')
            C.add(f'pwr_g{i}{j}', C.bm_box_minmax(cx - 0.06, cy - 0.06, p['z1'] - 0.02, cx + 0.06, cy + 0.06, p['z1'] + 0.011), 'gold')
    C.add('pwr_latch', C.bm_box_minmax((p['x0'] + p['x1']) / 2 - 0.25, p['y0'] - 0.15, p['z1'] - 0.6, (p['x0'] + p['x1']) / 2 + 0.25, p['y0'], p['z1'] - 0.1), 'plastic_black')

    C.anchor('anchor_gpu_power', ((p['x0'] + p['x1']) / 2, (p['y0'] + p['y1']) / 2, p['z1']))
    C.anchor('anchor_bracket_screw', (BX - 0.6, -1.67, 12.02))
    C.INFO['size_cm'] = [L.GPU_LEN, L.GPU_TOP_Z, L.GPU_THICK_DOWN + L.GPU_THICK_UP]
    return dict(preview_view=(0.45, -0.75, 1.0), preview_fov=28)


if __name__ == '__main__':
    C.run(build, 'gpu')
