"""
model_psu.py — Alimentation ATX 750 W, 80 PLUS Gold, semi-modulaire (15 x 8,6 x 14 cm).

Semi-modulaire : les câbles indispensables (24 broches carte mère, 8 broches EPS du
processeur) sont fixés à l'alimentation ; les autres (PCIe, SATA) se branchent à la
demande sur le panneau modulaire.

Orientation (une fois installée en bas du boîtier) : face arrière (prise secteur,
interrupteur, grille en nid d'abeille) vers -X, ventilateur vers le bas (-Y),
panneau modulaire vers +X, étiquette vers +Z (vitre). Origine = centre du boîtier.

    blender -b -P scripts/blender/model_psu.py
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

DX, DY, DZ = L.PSU_SIZE          # 14 x 8.6 x 15
hx, hy, hz = DX / 2, DY / 2, DZ / 2


def honeycomb_tex(w, h, r, name, color='#1a1b1e'):
    """Tôle perforée en nid d'abeille : les trous sont transparents (alpha = 0)."""
    cv = C.Canvas(w, h, C.srgb(color))
    dx = r * math.sqrt(3) + r * 0.45
    dy = dx * math.sqrt(3) / 2
    row = 0
    y = r
    while y < h + r:
        x = (dx / 2 if row % 2 else 0) + r * 0.9
        while x < w + r:
            pts = [(x + r * math.cos(math.radians(30 + 60 * k)), y + r * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
            cv.polygon(pts, (0, 0, 0, 1), hole=True)
            x += dx
        y += dy
        row += 1
    return cv.save(name)


def label_tex():
    w, h = 1024, 512
    cv = C.Canvas(w, h, C.srgb('#202227'))
    cv.rect(0, 0, w, 40, C.srgb('#22d3ee'))
    for k in range(6):                       # tableau des tensions / intensités
        y = 300 + k * 30
        cv.rect(60, y, 960, y + 2, C.srgb('#6b7079'))
    for k in range(7):
        x = 60 + k * 150
        cv.rect(x, 300, x + 2, 450, C.srgb('#6b7079'))
    return cv.save('psu_label')


def fan(name):
    parts = []
    hub = C.bm_lathe([(0, 0.85), (1.3, 0.83), (2.0, 0.72), (2.15, 0.55), (2.15, -0.8), (0, -0.8)], axis='x', segs=40)
    parts.append(C.add(name + '_hub', hub, 'plastic_dark', smooth=40))
    parts.append(C.add(name + '_lab', C.bm_cylinder(1.5, 0.02, axis='x', center=(0.865, 0, 0), segs=36), 'plastic_grey', smooth=40))
    for b in range(9):
        bm = _blade_bm(360.0 * b / 9, r_hub=2.1, r_tip=5.65, x_lead=0.7, x_trail=-0.65, width_hub=34, width_tip=38,
                       sweep=24, thick=0.09)
        parts.append(C.add(f'{name}_b{b}', bm, 'plastic_black', smooth=50))
    rot = C.merge(name, parts)
    rot.data.transform(Matrix.Rotation(math.radians(-90), 4, 'Z'))      # axe X -> axe -Y
    rot.location = (0.4, -hy + 1.3, 0.0)
    C.keep(rot, spin='y', extras={'spinDir': -1})


def build():
    # --- carter en acier noir, avec logements pour le ventilateur et la grille arrière
    box = C.add('psu_case', C.bm_box(DX, DY, DZ, bevel=0.18, segs=2), 'steel_black')
    C.cut(box, C.bm_cylinder(5.95, 5.0, axis='y', center=(0.4, -hy, 0.0), segs=72),
          C.bm_box_minmax(-hx - 1, -hy + 0.7, -hz + 0.7, -hx + 1.4, hy - 0.7, 1.2))
    C.resmooth(box, 35)
    # fines rainures décoratives sur le dessus
    for k in range(3):
        C.add(f'groove{k}', C.bm_box_minmax(-hx + 1.0, hy - 0.01, -hz + 2.0 + k * 0.35, hx - 1.0, hy + 0.01, -hz + 2.15 + k * 0.35), 'plastic_black')

    # --- ventilateur (aspire l'air par le bas) + grille
    fan('psu_fan_rotor')
    for r in (1.6, 2.9, 4.2, 5.45):
        C.add(f'grill_r{r}', C.bm_ring(r + 0.07, r - 0.07, 0.1, axis='y', center=(0.4, -hy - 0.02, 0), segs=64), 'steel_black', smooth=40)
    for k in range(4):
        bm = C.bm_box(0.14, 0.1, 11.7, center=(0, 0, 0))
        C.bm_rotate(bm, 45 + 90 * k, 'y')
        C.bm_translate(bm, (0.4, -hy - 0.02, 0))
        C.add(f'grill_s{k}', bm, 'steel_black')
    C.add('grill_center', C.bm_cylinder(1.25, 0.1, axis='y', center=(0.4, -hy - 0.03, 0), segs=40), 'steel_black', smooth=40)
    C.add('grill_center_ring', C.bm_ring(0.95, 0.85, 0.02, axis='y', center=(0.4, -hy - 0.085, 0), segs=40), 'accent', smooth=40)

    # --- face arrière : grille nid d'abeille, prise secteur C14, interrupteur
    hc = honeycomb_tex(512, 512, 9.0, 'psu_honeycomb')
    hc_mat = C.textured_mat('psu_honeycomb', hc, metallic=0.5, roughness=0.45, mask=True)
    z0, z1, y0, y1 = -hz + 0.7, 1.2, -hy + 0.7, hy - 0.7
    pl = C.bm_box_minmax(-hx - 0.004, y0, z0, -hx + 0.03, y1, z1)
    fa = [f for f in pl.faces if abs(f.normal.x) > 0.9]
    C.uv_project(pl, rect=(z0, y0, z1, y1), faces=fa, axes=('z', 'y'))
    C.uv_constant(pl, 0.0, 0.0, faces=[f for f in pl.faces if f not in fa])
    C.add('honeycomb', pl, hc_mat)
    C.add('inlet', C.bm_box_minmax(-hx - 0.12, 0.5, 2.6, -hx + 0.3, 3.1, 6.3, bevel=0.06), 'plastic_black')
    inl = C.bm_prism([(-0.95, -0.65), (0.95, -0.65), (0.95, 0.35), (0.6, 0.7), (-0.6, 0.7), (-0.95, 0.35)], 0.3, axis='x', offset=-hx - 0.13)
    C.add('inlet_hole', inl, 'chip', location=(0, 1.8, 4.45))
    for (dz, dy) in ((-0.42, -0.1), (0.42, -0.1), (0.0, 0.35)):
        C.add(f'inlet_pin{dz}{dy}', C.bm_box_minmax(-hx - 0.12, 1.8 + dy - 0.17, 4.45 + dz - 0.06, -hx + 0.1, 1.8 + dy + 0.17, 4.45 + dz + 0.06), 'steel')
    C.add('switch_frame', C.bm_box_minmax(-hx - 0.1, -2.6, 3.4, -hx + 0.3, -0.6, 5.5, bevel=0.05), 'plastic_black')
    sw = C.add('psu_switch', C.bm_box_minmax(-hx - 0.2, -2.45, 3.55, -hx - 0.02, -0.75, 5.35, bevel=0.06), 'plastic_dark')
    C.keep(sw, pivot=(-hx - 0.1, -1.6, 4.45))
    C.text('sw_I', 'I', 0.45, (-hx - 0.205, -1.25, 4.45), 'silk', rot=[(-90, 'y')])   # lisible depuis -X
    C.text('sw_O', 'O', 0.42, (-hx - 0.205, -2.0, 4.45), 'silk', rot=[(-90, 'y')])
    for (yy, zz) in ((-hy + 0.45, -hz + 0.45), (hy - 0.45, -hz + 0.45), (-hy + 0.45, hz - 0.45), (hy - 0.45, hz - 0.45)):
        C.add(f'mount{yy}{zz}', C.bm_cylinder(0.22, 0.03, axis='x', center=(-hx - 0.005, yy, zz), segs=16), 'chip', smooth=40)

    # --- face avant : panneau modulaire + passe-câble des câbles fixes
    C.add('mod_panel', C.bm_box_minmax(hx - 0.02, -3.0, -2.6, hx + 0.08, 1.7, 6.6, bevel=0.04), 'plastic_black')
    sockets = [('pcie', -1.6, 0.75), ('pcie', 0.55, 0.75), ('pcie', 2.7, 0.75), ('pcie', 4.85, 0.75),
               ('sata', -1.6, -1.45), ('sata', 0.2, -1.45), ('sata', 2.0, -1.45)]
    for i, (kind, zc, yc) in enumerate(sockets):
        cols = 4 if kind == 'pcie' else 3
        wz = cols * 0.42 + 0.22
        C.add(f'sock{i}', C.bm_box_minmax(hx + 0.05, yc - 0.52, zc - wz / 2, hx + 0.2, yc + 0.52, zc + wz / 2, bevel=0.03), 'plastic_dark')
        for a in range(cols):
            for b in range(2):
                cz = zc - wz / 2 + 0.11 + (a + 0.5) * 0.42
                cy = yc - 0.42 + (b + 0.5) * 0.42
                C.add(f'sock{i}_h{a}{b}', C.bm_box_minmax(hx + 0.19, cy - 0.15, cz - 0.15, hx + 0.21, cy + 0.15, cz + 0.15), 'chip')
    C.text('lab_pcie', 'CPU / PCIe', 0.26, (hx + 0.09, 1.38, 1.6), 'silk', rot=[(90, 'y')])   # lisible depuis +X
    C.text('lab_sata', 'SATA', 0.26, (hx + 0.09, -2.55, 0.2), 'silk', rot=[(90, 'y')])
    C.add('grommet', C.bm_ring(1.25, 0.95, 0.25, axis='x', center=(hx + 0.1, 2.35, -4.4), segs=40), 'rubber', smooth=40)

    # --- câbles fixes (24 broches et EPS 8 broches) : objet séparé, masqué par le site
    #     quand il dessine les câbles en entier pendant le montage
    cab = []
    p24 = C.fillet_path([(hx, 2.55, -4.85), (hx + 3.0, 2.55, -4.85), (hx + 4.2, 2.55, -4.85), (hx + 4.2, -2.6, -4.85)], 1.3, n=10)
    cab.append(C.tube('cab24', p24, 0.62, 'rubber', bevel_res=4))
    cab.append(C.add('head24', C.bm_box_minmax(hx + 3.45, -4.2, -6.2, hx + 4.95, -2.4, -3.5, bevel=0.06), 'plastic_black'))
    peps = C.fillet_path([(hx, 2.15, -3.8), (hx + 1.6, 2.15, -3.8), (hx + 2.4, 2.15, -3.8), (hx + 2.4, -1.9, -3.8)], 0.9, n=10)
    cab.append(C.tube('cabeps', peps, 0.38, 'rubber', bevel_res=3))
    cab.append(C.add('headeps', C.bm_box_minmax(hx + 1.85, -3.5, -4.75, hx + 2.95, -1.7, -2.85, bevel=0.05), 'plastic_black'))
    fixed = C.merge('psu_fixed_cables', cab)
    C.keep(fixed)

    # --- étiquette latérale (côté vitre)
    lt = label_tex()
    lmat = C.textured_mat('psu_label', lt, roughness=0.55)
    lb = C.bm_box_minmax(-hx + 1.2, -hy + 1.0, hz - 0.004, hx - 1.2, hy - 1.0, hz + 0.012)
    fa = [f for f in lb.faces if f.normal.z > 0.9]
    C.uv_project(lb, rect=(-hx + 1.2, -hy + 1.0, hx - 1.2, hy - 1.0), faces=fa, axes=('x', 'y'))
    C.uv_constant(lb, 0.5, 0.5, faces=[f for f in lb.faces if f not in fa])
    C.add('psu_label', lb, lmat)
    zt = hz + 0.016
    C.text('lab_w', '750 W', 1.15, (-1.6, 1.15, zt), 'silk')
    C.add('badge', C.bm_box_minmax(1.55, 0.25, zt - 0.002, 4.95, 2.05, zt + 0.002, bevel=0.0), 'plastic_yellow')
    C.text('lab_80', '80 PLUS', 0.42, (3.25, 1.4, zt + 0.005), 'chip')
    C.text('lab_gold', 'GOLD', 0.42, (3.25, 0.82, zt + 0.005), 'chip')
    C.text('lab_atx', 'ATX 3.1  ·  SEMI-MODULAR', 0.3, (-1.6, -0.15, zt), C.mat('accent'))

    # ancres : points de départ des câbles pour le montage
    C.anchor('anchor_psu_out_24', (hx + 0.2, 2.55, -4.85))
    C.anchor('anchor_psu_out_eps', (hx + 0.2, 2.15, -3.8))
    C.anchor('anchor_psu_pcie', (hx + 0.2, 0.75, -1.6))
    C.anchor('anchor_psu_sata', (hx + 0.2, -1.45, -1.6))
    C.anchor('anchor_psu_switch', (-hx - 0.2, -1.6, 4.45))
    C.INFO['size_cm'] = [DX, DY, DZ]
    return dict(preview_view=(-0.8, 0.55, 1.0), preview_fov=28)


if __name__ == '__main__':
    C.run(build, 'psu')
