"""
model_cpu.py — Processeur de bureau grand public (format AMD AM5 : boîtier 40 x 40 mm).

Le socket AM5 est de type LGA : les ~1 700 broches sont dans le socket de la carte
mère, le processeur n'a que des pastilles dorées en dessous.

Orientation (une fois monté sur la carte mère verticale) : pastilles vers -Z,
capot métallique (IHS) vers +Z. Origine = centre du plan des pastilles.

    blender -b -P scripts/blender/model_cpu.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402

import common as C  # noqa: E402
import layout as L  # noqa: E402

S = L.CPU_SIZE
T = L.CPU_SUBSTRATE_T
H = L.CPU_IHS_T


def pads_texture():
    """Dessous du processeur : grille de pastilles dorées + zone centrale de composants."""
    n = 1024
    cv = C.Canvas(n, n, C.srgb('#1d4a2c'))
    grid = 44
    pitch = n / grid
    gold = C.srgb('#d8b25e')
    rng = __import__('random').Random(7)
    for i in range(grid):
        for j in range(grid):
            ci, cj = i - (grid - 1) / 2, j - (grid - 1) / 2
            if abs(ci) < 8 and abs(cj) < 8:      # zone centrale sans pastilles
                continue
            if (i in (0, grid - 1)) and (j in (0, grid - 1)):
                continue
            x = (i + 0.5) * pitch
            y = (j + 0.5) * pitch
            cv.circle(x, y, pitch * 0.33, gold)
            cv.circle(x - pitch * 0.08, y - pitch * 0.08, pitch * 0.12, (1, 0.93, 0.7, 0.35))
    # composants CMS au centre
    c0 = n / 2 - 7.5 * pitch
    for k in range(70):
        x = c0 + rng.random() * 15 * pitch
        y = c0 + rng.random() * 15 * pitch
        w, h = (pitch * 0.9, pitch * 0.45) if rng.random() < 0.5 else (pitch * 0.45, pitch * 0.9)
        cv.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, C.srgb('#6b5236'))
        if w > h:
            cv.rect(x - w / 2, y - h / 2, x - w / 2 + w * 0.22, y + h / 2, C.srgb('#c9c9cc'))
            cv.rect(x + w / 2 - w * 0.22, y - h / 2, x + w / 2, y + h / 2, C.srgb('#c9c9cc'))
        else:
            cv.rect(x - w / 2, y - h / 2, x + w / 2, y - h / 2 + h * 0.22, C.srgb('#c9c9cc'))
            cv.rect(x - w / 2, y + h / 2 - h * 0.22, x + w / 2, y + h / 2, C.srgb('#c9c9cc'))
    # triangle doré de repérage (coin inférieur gauche vu de dessus = coin inférieur gauche miroir vu de dessous)
    cv.polygon([(n - 6, n - 6), (n - 6 - 70, n - 6), (n - 6, n - 6 - 70)], gold)
    cv.noise(0.004, seed=3)
    return cv.save('cpu_pads')


def build():
    # --- Substrat (circuit vert) : dessous texturé avec les pastilles
    pads_img = pads_texture()
    pads_mat = C.textured_mat('cpu_pads', pads_img, metallic=0.0, roughness=0.35)
    bm = C.bm_box(S, S, T, center=(0, 0, T / 2), bevel=0.02)
    bottom = C.faces_facing(bm, (0, 0, -1), 0.99)
    for f in bottom:
        f.material_index = 1
    C.uv_project(bm, 'z', rect=(-S / 2, -S / 2, S / 2, S / 2), faces=bottom, flip_u=True)
    C.uv_constant(bm, 0.5, 0.5, faces=[f for f in bm.faces if f not in bottom])
    sub = C.add('cpu_substrate', bm, ['pcb_green', pads_mat])
    # encoches de détrompage sur deux bords (elles correspondent aux clés du socket)
    notches = [C.bm_cylinder(0.11, T + 0.2, axis='z', center=(sx * S / 2, 0.75, T / 2), segs=16) for sx in (-1, 1)]
    C.cut(sub, *notches)

    # --- Capot métallique (IHS) à « pattes », typique des processeurs AM5
    w = 1.86
    nd = 0.55
    outline = [(-w, -w), (w, -w), (w, -1.25), (w - nd, -1.25), (w - nd, -0.35), (w, -0.35), (w, 0.35), (w - nd, 0.35),
               (w - nd, 1.25), (w, 1.25), (w, w), (-w, w), (-w, 1.25), (-w + nd, 1.25), (-w + nd, 0.35), (-w, 0.35),
               (-w, -0.35), (-w + nd, -0.35), (-w + nd, -1.25), (-w, -1.25)]
    ihs_mat = C.mat('nickel', roughness=0.27)
    ihs_mat.name = 'ihs_nickel'
    ihs = C.bm_prism(outline, H, axis='z', offset=T, bevel=0.025)
    C.add('cpu_ihs', ihs, ihs_mat, smooth=30)
    # marquage gravé (générique, sans marque)
    etch = C.mat('plastic_grey', roughness=0.6)
    etch.name = 'ihs_etch'
    C.text('cpu_txt1', 'DESKTOP PROCESSOR', 0.21, (0, 0.55, T + H + 0.003), etch)
    C.text('cpu_txt2', '8 CORES  |  16 THREADS', 0.17, (0, 0.18, T + H + 0.003), etch)
    C.text('cpu_txt3', 'LGA 1718', 0.15, (0, -0.25, T + H + 0.003), etch)
    # petit code 2D (datamatrix) en bas à droite
    rng = __import__('random').Random(11)
    for i in range(10):
        for j in range(10):
            if i in (0,) or j in (0,) or rng.random() < 0.45:
                x = 0.75 + i * 0.05
                y = -1.55 + j * 0.05
                C.add(f'dm_{i}_{j}', C.bm_box(0.045, 0.045, 0.004, center=(x, y, T + H + 0.002)), etch)

    # --- Condensateurs CMS visibles dans les échancrures
    for sx in (-1, 1):
        for (y0, y1) in ((-1.25, -0.35), (0.35, 1.25)):
            k = 0
            for row in range(2):
                for col in range(5):
                    cx = sx * (w - nd / 2 - 0.13 + row * 0.24)
                    cy = y0 + 0.11 + col * ((y1 - y0 - 0.22) / 4)
                    body = C.bm_box(0.13, 0.065, 0.05, center=(cx, cy, T + 0.025))
                    C.add(f'cap_{sx}_{y0}_{k}', body, 'ceramic')
                    for e in (-1, 1):
                        C.add(f'capend_{sx}_{y0}_{k}_{e}', C.bm_box(0.025, 0.068, 0.052, center=(cx + e * 0.055, cy, T + 0.026)), 'solder')
                    k += 1

    # --- Triangle doré de repérage (à aligner avec celui du socket)
    tri = C.bm_prism([(-S / 2 + 0.06, -S / 2 + 0.06), (-S / 2 + 0.55, -S / 2 + 0.06), (-S / 2 + 0.06, -S / 2 + 0.55)],
                     0.004, axis='z', offset=T)
    C.add('cpu_triangle', tri, 'gold')

    C.anchor('anchor_triangle', (-S / 2 + 0.2, -S / 2 + 0.2, T + 0.01))
    C.anchor('anchor_ihs_top', (0, 0, T + H))
    C.INFO['size_cm'] = [S, S, T + H]
    return dict(preview_view=(0.55, -0.35, 1.0), preview_fov=24)


if __name__ == '__main__':
    C.run(build, 'cpu')
