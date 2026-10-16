"""
model_ssd.py — SSD NVMe M.2 2280 (22 x 80 mm), 1 To.

Orientation (une fois posé dans le slot M.2 de la carte mère) : à plat dans le plan XY,
composants vers +Z, connecteur (contacts dorés, encoche « M ») côté X = 0, demi-lune
de vissage à l'autre bout (X = 8). Origine = milieu du bord à contacts, face inférieure.

    blender -b -P scripts/blender/model_ssd.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402

import common as C  # noqa: E402
import layout as L  # noqa: E402

LEN = L.M2_LEN
W = L.M2_W
T = 0.08
KEY_Y = -0.67
TW, TH = 1024, 288


def pcb_tex():
    rng = random.Random(4)
    cv = C.Canvas(TW, TH, C.srgb('#131518'))

    def X(x):
        return x / LEN * TW

    def Y(y):
        return (W / 2 - y) / W * TH

    for _ in range(90):
        x = rng.uniform(0.6, 7.6)
        y = rng.uniform(-1.0, 1.0)
        cv.line(X(x), Y(y), X(x + rng.uniform(0.2, 1.2)), Y(y), 1.0, C.srgb('#1d2025'))
    gold = C.srgb('#d8b35d')
    y = -W / 2 + 0.12
    while y < W / 2 - 0.1:
        if abs(y - KEY_Y) > 0.12:
            cv.rect(X(0.02), Y(y + 0.018), X(0.4), Y(y - 0.018), gold, r=1.0)
        y += 0.05
    for k in range(14):                      # composants passifs près du connecteur
        yy = -0.9 + k * 0.13
        cv.rect(X(0.55), Y(yy + 0.03), X(0.68), Y(yy - 0.03), C.srgb('#5b4732'))
    cv.circle(X(LEN - 0.17), Y(0), 26, C.srgb('#c9c9cc'))     # pastille de masse autour du trou
    cv.noise(0.004, seed=2)
    return cv.save('ssd_pcb')


def label_tex():
    w, h = 512, 220
    cv = C.Canvas(w, h, C.srgb('#141619'))
    cv.rect(0, 0, 14, h, C.srgb('#22d3ee'))
    rng = random.Random(6)
    for i in range(21):                      # petit QR code
        for j in range(21):
            corner = (i < 7 and j < 7) or (i > 13 and j < 7) or (i < 7 and j > 13)
            on = rng.random() < 0.5
            if corner:
                on = (i % 6 == 0 or j % 6 == 0 or (2 <= i % 14 <= 4 and 2 <= j % 14 <= 4)) if i < 7 or i > 13 else on
            if on:
                cv.rect(420 + i * 4, 120 + j * 4, 424 + i * 4, 124 + j * 4, C.srgb('#d9dce1'))
    for k in range(3):
        cv.rect(40, 178 + k * 12, 260 - k * 40, 183 + k * 12, C.srgb('#4a4f57'))
    return cv.save('ssd_label')


def build():
    img = pcb_tex()
    pcb_mat = C.textured_mat('ssd_pcb', img, roughness=0.42)
    bm = C.bm_box(LEN, W, T, center=(LEN / 2, 0, T / 2), bevel=0.008)
    tops = [f for f in bm.faces if abs(f.normal.z) > 0.9]
    C.uv_project(bm, 'z', rect=(0, -W / 2, LEN, W / 2), faces=[f for f in tops if f.normal.z > 0])
    C.uv_project(bm, 'z', rect=(0, -W / 2, LEN, W / 2), faces=[f for f in tops if f.normal.z < 0], flip_v=True)
    C.uv_constant(bm, 0.5, 0.5, faces=[f for f in bm.faces if f not in tops])
    pcb = C.add('ssd_pcb', bm, pcb_mat)
    C.cut(pcb, C.bm_box(0.72, 0.12, 1.0, center=(0.0, KEY_Y, 0)),
          C.bm_cylinder(0.175, 1.0, axis='z', center=(LEN, 0, 0), segs=24))
    C.resmooth(pcb, 35)

    # contrôleur, cache DRAM, 2 boîtiers de mémoire flash NAND
    C.add('ctrl', C.bm_box_minmax(1.0, -0.62, T, 2.24, 0.62, T + 0.12, bevel=0.015), 'chip')
    C.add('ctrl_lid', C.bm_box_minmax(1.12, -0.5, T + 0.12, 2.12, 0.5, T + 0.135, bevel=0.01), 'nickel')
    C.add('dram', C.bm_box_minmax(2.5, -0.55, T, 3.25, 0.55, T + 0.1), 'chip')
    for k, x0 in enumerate((3.6, 5.45)):
        C.add(f'nand{k}', C.bm_box_minmax(x0, -0.85, T, x0 + 1.55, 0.85, T + 0.12, bevel=0.012), 'chip')
    for k in range(6):
        y = -0.8 + k * 0.32
        C.add(f'cap{k}', C.bm_box_minmax(0.75, y - 0.06, T, 0.88, y + 0.06, T + 0.07), 'ceramic')

    # étiquette (au-dessus des puces mémoire)
    lab = label_tex()
    lab_mat = C.textured_mat('ssd_label', lab, roughness=0.5)
    zl = T + 0.12
    lb = C.bm_box_minmax(2.42, -1.02, zl, 7.1, 1.02, zl + 0.012)
    top = [f for f in lb.faces if f.normal.z > 0.9]
    C.uv_project(lb, 'z', rect=(2.42, -1.02, 7.1, 1.02), faces=top)
    C.uv_constant(lb, 0.5, 0.05, faces=[f for f in lb.faces if f not in top])
    C.add('ssd_label', lb, lab_mat)
    zt = zl + 0.016
    C.text('ssd_t1', '1TB', 0.5, (3.25, 0.45, zt), 'silk', align='LEFT')
    C.text('ssd_t2', 'NVMe  M.2 2280', 0.17, (3.27, -0.12, zt), 'silk', align='LEFT')
    C.text('ssd_t3', 'PCIe 4.0 x4', 0.15, (3.27, -0.4, zt), C.mat('accent'), align='LEFT')

    C.anchor('anchor_ssd_screw', (LEN, 0, T))
    C.INFO['size_cm'] = [LEN, W, T]
    return dict(preview_view=(0.25, -0.55, 1.0), preview_fov=24)


if __name__ == '__main__':
    C.run(build, 'ssd')
