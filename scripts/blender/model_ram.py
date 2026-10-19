"""
model_ram.py : Barrette de mémoire DDR5 16 Go (format DIMM 288 broches, 133,35 x 31,25 mm).

Une barrette de 16 Go DDR5 « simple face » porte 8 puces mémoire sur une seule face,
un petit circuit de gestion de l'alimentation (PMIC, nouveauté de la DDR5) et un hub SPD.

Orientation (une fois enfoncée dans le slot) : longueur selon Y, hauteur selon +Z
(elle « sort » de la carte mère), puces sur la face +X. Origine = milieu du bord à contacts.

    blender -b -P scripts/blender/model_ram.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402

import common as C  # noqa: E402
import layout as L  # noqa: E402

LEN = 13.335
HGT = 3.125
PCB_T = 0.127
FING = 0.32          # hauteur de la bande de contacts dorés
KEY = L.DDR5_KEY_OFFSET
TW, TH = 1024, 240


def tex():
    """Face du circuit : vernis vert, pistes, composants CMS, 144 contacts dorés par face."""
    rng = random.Random(3)
    cv = C.Canvas(TW, TH, C.srgb('#1e5631'))

    def X(y):            # position le long de la barrette (cm) -> pixel
        return (y + LEN / 2) / LEN * TW

    def Y(z):            # hauteur (cm) -> pixel (haut de l'image = haut de la barrette)
        return (HGT - z) / HGT * TH

    for _ in range(140):
        y = rng.uniform(-LEN / 2, LEN / 2)
        z0 = rng.uniform(0.4, 2.9)
        cv.line(X(y), Y(z0), X(y), Y(max(0.35, z0 - rng.uniform(0.2, 1.0))), 1.0, C.srgb('#256b3c'))
    for k in range(60):
        z = 2.2 + (k % 6) * 0.1
        y0 = -6.0 + (k // 6) * 1.2
        cv.line(X(y0), Y(z), X(y0 + 0.9), Y(z), 1.0, C.srgb('#256b3c'))
    # contacts : 144 par face, séparés par l'encoche
    pitch = 0.085
    gold = C.srgb('#d9b45c')
    n_left = 72
    for i in range(144):
        if i < n_left:
            y = KEY - 0.25 - (n_left - 1 - i) * pitch
        else:
            y = KEY + 0.25 + (i - n_left) * pitch
        if abs(y) > LEN / 2 - 0.25:
            continue
        cv.rect(X(y - pitch * 0.36), Y(FING), X(y + pitch * 0.36), Y(0.02), gold, r=1.0)
    # petits composants CMS au-dessus des contacts
    for k in range(48):
        y = -6.2 + k * 0.26
        if abs(y - KEY) < 0.4:
            continue
        cv.rect(X(y) - 4, Y(0.62), X(y) + 4, Y(0.48), C.srgb('#5a4630'))
        cv.rect(X(y) - 4, Y(0.62), X(y) - 2, Y(0.48), C.srgb('#c8c8cc'))
        cv.rect(X(y) + 2, Y(0.62), X(y) + 4, Y(0.48), C.srgb('#c8c8cc'))
    # sérigraphie
    cv.rect(X(-6.4), Y(3.0), X(6.4), Y(0.75), C.srgb('#d8d8d8', 0.35), stroke=1.2)
    cv.noise(0.004, seed=8)
    return cv.save('ram_pcb')


def label_tex():
    w, h = 512, 160
    cv = C.Canvas(w, h, C.srgb('#e9eaec'))
    cv.rect(0, 0, w, 26, C.srgb('#22d3ee'))
    rng = random.Random(5)
    x = 300
    while x < 490:
        bw = rng.choice((2, 3, 4, 6))
        cv.rect(x, 100, x + bw, 145, C.srgb('#111111'))
        x += bw + rng.choice((2, 3, 4))
    return cv.save('ram_label')


def build():
    img = tex()
    pcb_mat = C.textured_mat('ram_pcb', img, roughness=0.4)
    bm = C.bm_box(PCB_T, LEN, HGT, center=(0, 0, HGT / 2), bevel=0.01)
    side = [f for f in bm.faces if abs(f.normal.x) > 0.9]
    C.uv_project(bm, rect=(-LEN / 2, 0, LEN / 2, HGT), faces=[f for f in side if f.normal.x > 0], flip_u=True, axes=('y', 'z'))
    C.uv_project(bm, rect=(-LEN / 2, 0, LEN / 2, HGT), faces=[f for f in side if f.normal.x < 0], axes=('y', 'z'))
    C.uv_constant(bm, 0.5, 0.6, faces=[f for f in bm.faces if f not in side])
    pcb = C.add('ram_pcb', bm, pcb_mat)
    # encoche de détrompage (DDR5) + encoches latérales pour les loquets
    cutters = [C.bm_box(1.0, 0.2, 0.84, center=(0, KEY, 0.0))]
    for sy in (-1, 1):
        cutters.append(C.bm_cylinder(0.16, 1.0, axis='x', center=(0, sy * LEN / 2, 1.75), segs=16))
        cutters.append(C.bm_box(1.0, 0.36, 0.5, center=(0, sy * LEN / 2, 0.0)))
    C.cut(pcb, *cutters)
    C.resmooth(pcb, 35)

    # 8 puces DRAM (face +X), en deux groupes de 4 (un par sous-canal)
    xf = PCB_T / 2
    for k, y in enumerate((-5.45, -4.1, -2.75, -1.4, 1.4, 2.75, 4.1, 5.45)):
        C.add(f'dram{k}', C.bm_box_minmax(xf, y - 0.5, 1.15, xf + 0.1, y + 0.5, 2.35, bevel=0.012), 'chip')
        C.add(f'dram_dot{k}', C.bm_cylinder(0.04, 0.004, axis='x', center=(xf + 0.101, y - 0.38, 2.2), segs=12), 'plastic_grey', smooth=40)
    # PMIC (régulateur de tension embarqué) + bobines, hub SPD
    C.add('pmic', C.bm_box_minmax(xf, -0.35, 0.95, xf + 0.08, 0.35, 1.55), 'chip')
    for k, y in enumerate((-0.25, 0.25)):
        C.add(f'pmic_ind{k}', C.bm_box_minmax(xf, y - 0.17, 1.75, xf + 0.12, y + 0.17, 2.1, bevel=0.01), 'ferrite')
    C.add('spd_hub', C.bm_box_minmax(xf, -0.2, 2.45, xf + 0.06, 0.2, 2.75), 'chip')
    rng = random.Random(9)
    for k in range(26):
        y = rng.uniform(-6.2, 6.2)
        z = rng.choice((0.85, 2.6, 2.75))
        if abs(y) < 0.6 and z > 2:
            continue
        C.add(f'smd{k}', C.bm_box_minmax(xf, y - 0.05, z - 0.025, xf + 0.035, y + 0.05, z + 0.025), 'ceramic')

    # étiquette au dos (face -X)
    lab = label_tex()
    lab_mat = C.textured_mat('ram_label', lab, roughness=0.55)
    lb = C.bm_box_minmax(-PCB_T / 2 - 0.012, -2.6, 1.2, -PCB_T / 2, 2.6, 2.75)
    face = [f for f in lb.faces if f.normal.x < -0.9]
    C.uv_project(lb, rect=(-2.6, 1.2, 2.6, 2.75), faces=face, axes=('y', 'z'), flip_u=True)
    C.uv_constant(lb, 0.1, 0.5, faces=[f for f in lb.faces if f not in face])
    C.add('ram_label', lb, lab_mat)
    # texte lisible depuis -X : lecture vers -Y, haut vers +Z
    C.text('ram_txt1', '16GB DDR5', 0.34, (-PCB_T / 2 - 0.016, 1.15, 2.05), 'chip', rot=[(90, 'x'), (-90, 'z')])
    C.text('ram_txt2', '1Rx8  UDIMM', 0.2, (-PCB_T / 2 - 0.016, 1.15, 1.62), 'chip', rot=[(90, 'x'), (-90, 'z')])

    C.anchor('anchor_ram_top', (0, 0, HGT))
    C.INFO['size_cm'] = [PCB_T, LEN, HGT]
    return dict(preview_view=(1.0, 0.25, 0.5), preview_fov=22, preview_up=(0, 0, 1))


if __name__ == '__main__':
    C.run(build, 'ram')
