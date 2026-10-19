"""
model_motherboard.py : Carte mère ATX (30,5 x 24,4 cm), socket AM5, 4 slots DDR5,
2 slots M.2, 1 slot PCIe x16 principal (+ un x1 et un x16 « long » câblé en x4).

Orientation : la carte est verticale (plan XY), composants vers +Z, ports arrière
(I/O) sur le bord X = -12,2. Origine = centre de la face arrière du PCB.

    blender -b -P scripts/blender/model_motherboard.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402

import common as C  # noqa: E402
import layout as L  # noqa: E402

T = L.MB_T
SX, SY = L.SOCKET_C
TEX_W, TEX_H = 820, 1024        # même rapport que la carte (24,4 x 30,5)


def px(x):
    return (x + L.MB_W / 2) / L.MB_W * TEX_W


def py(y):
    return (L.MB_H / 2 - y) / L.MB_H * TEX_H


def box(name, x0, y0, z0, x1, y1, z1, m, bevel=0.0, segs=1, smooth=None):
    return C.add(name, C.bm_box_minmax(x0, y0, z0, x1, y1, z1, bevel=bevel, segs=segs), m, smooth=smooth)


def silk(name, body, x, y, size=0.22, rot=0, z=None, m='silk', align='CENTER'):
    return C.text('silk_' + name, body, size, (x, y, (T + 0.006) if z is None else z), m,
                  rot=[(rot, 'z')] if rot else None, align=align)


# --------------------------------------------------------------------------- textures
def pcb_texture():
    rng = random.Random(42)
    cv = C.Canvas(TEX_W, TEX_H, C.srgb('#15171b'))
    trace = C.srgb('#1d2026')
    trace2 = C.srgb('#22262d')
    # bus de pistes parallèles : socket -> slots mémoire
    for k in range(26):
        y = py(SY + 3.2 - k * 0.26)
        cv.line(px(SX + 3.2), y, px(3.2), y + rng.uniform(-3, 3), 1.2, trace)
    # socket -> slot PCIe x16 (vertical) puis coude à 45°
    for k in range(18):
        x = px(SX - 2.2 + k * 0.25)
        y0, y1 = py(SY - 3.2), py(L.PCIE_X16_Y + 0.6)
        cv.line(x, y0, x, y1 - 8, 1.1, trace)
    # chipset -> M.2 / SATA
    for k in range(14):
        y = py(-7.0 - k * 0.3)
        cv.line(px(8.6), y, px(10.8), y, 1.0, trace2)
    for k in range(10):
        x = px(3.0 + k * 0.4)
        cv.line(x, py(-6.4), x - 20, py(-3.0), 1.0, trace2)
    # pistes aléatoires « Manhattan » discrètes
    for _ in range(260):
        x, y = rng.uniform(0, TEX_W), rng.uniform(0, TEX_H)
        L1 = rng.uniform(10, 60)
        if rng.random() < 0.5:
            cv.line(x, y, x + L1, y, 1.0, trace)
            cv.line(x + L1, y, x + L1 + 8, y + 8, 1.0, trace)
        else:
            cv.line(x, y, x, y + L1, 1.0, trace)
    # vias
    for _ in range(500):
        cv.circle(rng.uniform(0, TEX_W), rng.uniform(0, TEX_H), 1.4, C.srgb('#2a2e35'))
    # sérigraphie : contours des composants
    sk = C.srgb('#9a9ea6', 0.85)
    for (x0, y0, x1, y1) in [
        (SX - 3.1, SY - 3.8, SX + 3.1, SY + 3.8),
        (L.ATX24['x0'] - 0.15, L.ATX24['y0'] - 0.15, L.ATX24['x1'] + 0.15, L.ATX24['y1'] + 0.15),
        (L.EPS8['x0'] - 0.15, L.EPS8['y0'] - 0.15, L.EPS8['x1'] + 0.15, L.EPS8['y1'] + 0.15),
        (3.0, -12.2, 8.6, -6.4),
    ]:
        cv.rect(px(x0), py(y1), px(x1), py(y0), sk, stroke=1.4)
    for xc in L.DIMM_X.values():
        cv.rect(px(xc - 0.4), py(L.DIMM_Y + 7.3), px(xc + 0.4), py(L.DIMM_Y - 7.3), sk, stroke=1.2)
    # repères des trous de fixation (zone dégagée)
    for (hx, hy) in L.HOLES:
        cv.circle(px(hx), py(hy), 13, C.srgb('#1a1c21'))
        cv.circle(px(hx), py(hy), 13, sk, stroke=1.3)
    # séparation de la zone audio (isolation des pistes, très reconnaissable)
    pts = [(px(-12.2), py(-4.6)), (px(-10.7), py(-4.6)), (px(-10.7), py(-12.6)), (px(-12.2), py(-12.6))]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        cv.line(a[0], a[1], b[0], b[1], 1.6, C.srgb('#c2b48a', 0.7))
    # motif décoratif discret (lignes obliques) en bas à droite
    for k in range(16):
        x0 = px(8.0) + k * 9
        cv.line(x0, py(-12.6), x0 + 40, py(-15.0), 1.2, C.srgb('#22d3ee', 0.18))
    cv.noise(0.003, seed=5)
    return cv.save('mb_pcb')


def pins_texture():
    n = 512
    cv = C.Canvas(n, n, C.srgb('#101113'))
    grid = 44
    p = n / grid
    for i in range(grid):
        for j in range(grid):
            ci, cj = i - (grid - 1) / 2, j - (grid - 1) / 2
            if abs(ci) < 8 and abs(cj) < 8:
                continue
            cv.circle((i + 0.5) * p, (j + 0.5) * p, p * 0.24, C.srgb('#b38d45'))
            cv.circle((i + 0.42) * p, (j + 0.42) * p, p * 0.09, C.srgb('#f5dc9a'))
    return cv.save('socket_pins')


# --------------------------------------------------------------------------- composants
def pin_header(name, x0, y0, cols, rows, pitch=0.254, base='plastic_black', missing=(), pin_h=0.6, shroud=None):
    w, h = cols * pitch, rows * pitch
    box(name + '_base', x0, y0, T, x0 + w, y0 + h, T + 0.25, base)
    for i in range(cols):
        for j in range(rows):
            if (i, j) in missing:
                continue
            cx, cy = x0 + (i + 0.5) * pitch, y0 + (j + 0.5) * pitch
            box(f'{name}_p{i}_{j}', cx - 0.032, cy - 0.032, T + 0.25, cx + 0.032, cy + 0.032, T + 0.25 + pin_h, 'gold')
    if shroud:
        m = 0.08
        zt = T + 0.25 + pin_h + 0.02
        for (a, b, c, d) in [(x0 - m, y0 - m, x0 + w + m, y0), (x0 - m, y0 + h, x0 + w + m, y0 + h + m),
                             (x0 - m, y0, x0, y0 + h), (x0 + w, y0, x0 + w + m, y0 + h)]:
            box(f'{name}_sh{a:.2f}{b:.2f}', a, b, T, c, d, zt, shroud)


def power_header(name, x0, y0, x1, y1, cols, rows, height=1.0):
    """Connecteur d'alimentation (Mini-Fit) : boîtier noir et trous carrés avec contacts."""
    box(name + '_housing', x0, y0, T, x1, y1, T + height, 'plastic_black', bevel=0.03)
    pw, ph = (x1 - x0) / cols, (y1 - y0) / rows
    zt = T + height
    for i in range(cols):
        for j in range(rows):
            cx, cy = x0 + (i + 0.5) * pw, y0 + (j + 0.5) * ph
            s = min(pw, ph) * 0.38
            box(f'{name}_h{i}_{j}', cx - s, cy - s, zt - 0.02, cx + s, cy + s, zt + 0.006, 'chip')
            g = s * 0.35
            box(f'{name}_g{i}_{j}', cx - g, cy - g, zt - 0.02, cx + g, cy + g, zt + 0.011, 'gold')
    return zt


def fan_header(name, x, y):
    """En-tête 4 broches (PWM) avec détrompeur."""
    box(name + '_base', x - 0.5, y - 0.22, T, x + 0.5, y + 0.22, T + 0.12, 'plastic_black')
    box(name + '_wall', x - 0.5, y + 0.14, T, x + 0.5, y + 0.22, T + 0.62, 'plastic_black')
    for k in range(4):
        cx = x - 0.381 + k * 0.254
        box(f'{name}_p{k}', cx - 0.032, y - 0.032, T + 0.12, cx + 0.032, y + 0.032, T + 0.62, 'gold')


def dimm_slot(key, xc):
    y0 = L.DIMM_Y - L.DIMM_SLOT_LEN / 2
    y1 = L.DIMM_Y + L.DIMM_SLOT_LEN / 2
    w, h = L.DIMM_SLOT_W, L.DIMM_SLOT_H
    n = 'dimm_' + key
    sm = 'plastic_grey' if key in ('A2', 'B2') else 'plastic_dark'   # slots prioritaires d'une autre couleur
    box(n + '_bot', xc - w / 2, y0, T, xc + w / 2, y1, T + 0.15, sm)
    box(n + '_l', xc - w / 2, y0, T, xc - 0.09, y1, T + h, sm, bevel=0.02)
    box(n + '_r', xc + 0.09, y0, T, xc + w / 2, y1, T + h, sm, bevel=0.02)
    box(n + '_end', xc - w / 2, y0 - 0.35, T, xc + w / 2, y0 + 0.02, T + h + 0.12, sm, bevel=0.03)
    ky = L.DIMM_Y + L.DDR5_KEY_OFFSET
    box(n + '_key', xc - 0.09, ky - 0.06, T, xc + 0.09, ky + 0.06, T + 0.42, 'plastic_dark')
    # loquet (côté haut) : pièce animable, pivot à sa base
    lat = C.bm_box_minmax(xc - w / 2 - 0.02, y1, T, xc + w / 2 + 0.02, y1 + 0.42, T + h + 0.35, bevel=0.04)
    tab = C.bm_box_minmax(xc - w / 2 - 0.02, y1 + 0.3, T + h + 0.1, xc + w / 2 + 0.02, y1 + 0.62, T + h + 0.35, bevel=0.04)
    latch = C.add('dimm_latch_' + key, C.bm_join(lat, tab), 'plastic_white' if key in ('A2', 'B2') else 'plastic_grey')
    C.keep(latch, pivot=(xc, y1 + 0.21, T + 0.05))


def pcie_slot(name, x0, x1, yc, armor=False, latch=False, h=L.PCIE_SLOT_H):
    w = 0.75
    box(name + '_bot', x0, yc - w / 2, T, x1, yc + w / 2, T + 0.2, 'plastic_dark')
    box(name + '_a', x0, yc - w / 2, T, x1, yc - 0.1, T + h, 'plastic_dark', bevel=0.02)
    box(name + '_b', x0, yc + 0.1, T, x1, yc + w / 2, T + h, 'plastic_dark', bevel=0.02)
    box(name + '_e0', x0 - 0.15, yc - w / 2, T, x0, yc + w / 2, T + h, 'plastic_dark')
    if x1 - x0 > 3:
        kx = x0 + 1.165       # détrompeur après les 11 premiers contacts
        box(name + '_key', kx - 0.08, yc - 0.1, T, kx + 0.08, yc + 0.1, T + h - 0.15, 'plastic_dark')
    if armor:   # renfort métallique des slots x16 (supporte le poids des cartes graphiques)
        g = 0.03
        box(name + '_arm_a', x0 - 0.05, yc - w / 2 - g, T, x1 + 0.05, yc - w / 2, T + h + 0.03, 'steel')
        box(name + '_arm_b', x0 - 0.05, yc + w / 2, T, x1 + 0.05, yc + w / 2 + g, T + h + 0.03, 'steel')
        box(name + '_arm_ta', x0 - 0.05, yc - w / 2 - g, T + h, x1 + 0.05, yc - 0.12, T + h + 0.03, 'steel')
        box(name + '_arm_tb', x0 - 0.05, yc + 0.12, T + h, x1 + 0.05, yc + w / 2 + g, T + h + 0.03, 'steel')
    if latch:
        lb = C.bm_box_minmax(x1, yc - w / 2, T, x1 + 0.55, yc + w / 2, T + h + 0.15, bevel=0.04)
        lt = C.bm_box_minmax(x1 + 0.35, yc - w / 2, T + h, x1 + 0.9, yc + w / 2, T + h + 0.3, bevel=0.04)
        lat = C.add(name + '_latch', C.bm_join(lb, lt), 'plastic_grey')
        C.keep(lat, pivot=(x1 + 0.1, yc, T + 0.1))


def m2_slot(key, conf, heatsink=False):
    cx, yc, z = conf['conn_x'], conf['y'], conf['z']
    box(key + '_conn', cx - 0.55, yc - 1.3, T, cx + 0.4, yc + 1.3, T + 0.5, 'plastic_black', bevel=0.02)
    box(key + '_slit', cx + 0.4, yc - 1.15, z - 0.01, cx + 0.405, yc + 1.15, z + 0.1, 'chip')
    sx = cx + L.M2_LEN
    st = C.bm_cylinder(0.22, z - T, axis='z', center=(sx, yc, (T + z) / 2), segs=6)
    C.add(key + '_standoff', st, 'brass', smooth=20)
    if heatsink:
        box(key + '_hs', cx - 0.7, yc - 1.4, T + 0.05, sx + 0.45, yc + 1.4, T + 0.75, 'alu_grey', bevel=0.08, segs=2)
        for k in range(7):
            yy = yc - 1.05 + k * 0.35
            box(f'{key}_hsf{k}', cx + 0.2, yy - 0.06, T + 0.75, sx - 0.6, yy + 0.06, T + 0.88, 'alu_dark', bevel=0.02)
        for e in (cx - 0.35, sx + 0.12):
            C.add(f'{key}_hs_screw{e:.1f}', C.bm_cylinder(0.2, 0.1, axis='z', center=(e, yc, T + 0.8), segs=20), 'steel', smooth=40)
        silk(key + '_hs', 'M.2_2', (cx + sx) / 2 + 2.6, yc - 1.15, size=0.2, z=T + 0.755, m='plastic_grey')
    else:
        # vis M.2 (animable) : tête cruciforme au-dessus du SSD
        head = C.bm_lathe([(0.0, 0.11), (0.22, 0.10), (0.28, 0.06), (0.28, 0.0), (0.09, 0.0), (0.09, -0.25), (0.0, -0.25)], axis='z', segs=28)
        x1 = C.bm_box(0.36, 0.06, 0.03, center=(0, 0, 0.102))
        x2 = C.bm_box(0.06, 0.36, 0.03, center=(0, 0, 0.102))
        screw = C.add('m2_screw', head, 'steel', smooth=40)
        cross = C.add('m2_screw_x', C.bm_join(x1, x2), 'chip')
        sc = C.merge('m2_screw', [screw, cross], origin=(0, 0, 0))
        sc.location = (sx, yc, z + 0.08)
        C.keep(sc, spin=None)


def polymer_cap(name, x, y, r=0.3, h=0.75):
    C.add(name, C.bm_cylinder(r, h - 0.06, axis='z', center=(x, y, T + (h - 0.06) / 2), segs=24), 'alu', smooth=40)
    C.add(name + '_top', C.bm_cylinder(r * 0.96, 0.06, axis='z', center=(x, y, T + h - 0.03), segs=24), 'plastic_black', smooth=40)


# --------------------------------------------------------------------------- I/O arrière
def io_ports():
    xb = -L.MB_W / 2           # bord de la carte
    xf = xb - 0.85             # face des ports (dans l'ouverture du boîtier)
    xr = xb + 2.3              # fond des ports
    zc = [T + 1.25, T + 3.1]   # deux colonnes de ports (hauteur au-dessus de la carte)
    # plaque I/O intégrée (tôle noire)
    box('io_plate', xf + 0.12, L.IO_Y0, T + 0.05, xf + 0.2, L.IO_Y1, L.IO_Z1, 'steel_black')

    def usb_a(name, y, z, color):
        box(name + '_shell', xf - 0.03, y - 0.36, z - 0.75, xr, y + 0.36, z + 0.75, 'steel', bevel=0.02)
        box(name + '_hole', xf - 0.04, y - 0.29, z - 0.66, xf + 0.4, y + 0.29, z + 0.66, 'chip')
        box(name + '_tongue', xf - 0.05, y - 0.06, z - 0.6, xf + 0.4, y + 0.14, z + 0.6, color)

    def usb_c(name, y, z):
        box(name + '_shell', xf - 0.03, y - 0.2, z - 0.48, xr, y + 0.2, z + 0.48, 'steel', bevel=0.12, segs=3)
        box(name + '_hole', xf - 0.04, y - 0.13, z - 0.4, xf + 0.3, y + 0.13, z + 0.4, 'chip', bevel=0.08, segs=2)
        box(name + '_tongue', xf - 0.05, y - 0.04, z - 0.3, xf + 0.3, y + 0.04, z + 0.3, 'plastic_black')

    # boutons Flash BIOS / Clear CMOS
    for k, z in enumerate(zc):
        C.add(f'io_btn{k}', C.bm_cylinder(0.3, 0.5, axis='x', center=(xf + 0.1, 12.6, z), segs=24), 'plastic_dark', smooth=40)
        C.add(f'io_btnr{k}', C.bm_ring(0.38, 0.3, 0.06, axis='x', center=(xf - 0.03, 12.6, z), segs=24), 'steel', smooth=40)
    # USB-A noirs (USB 2.0)
    for j, y in enumerate((11.55, 10.75)):
        for k, z in enumerate(zc):
            usb_a(f'io_usb2_{j}{k}', y, z, 'plastic_black')
    # HDMI + DisplayPort (sorties vidéo du processeur, inutilisées avec une carte graphique)
    y = 9.6
    box('io_hdmi_shell', xf - 0.03, y - 0.42, zc[0] - 0.85, xr, y + 0.42, zc[0] + 0.85, 'steel', bevel=0.02)
    C.add('io_hdmi_hole', C.bm_prism([(-0.7, 0.3), (0.7, 0.3), (0.7, 0.0), (0.45, -0.3), (-0.45, -0.3), (-0.7, 0.0)], 0.4,
                                     axis='x', offset=xf - 0.04), 'chip', location=(0, y, zc[0]))
    box('io_dp_shell', xf - 0.03, y - 0.42, zc[1] - 0.9, xr, y + 0.42, zc[1] + 0.9, 'steel', bevel=0.02)
    C.add('io_dp_hole', C.bm_prism([(-0.8, 0.3), (0.8, 0.3), (0.8, -0.05), (0.55, -0.3), (-0.8, -0.3)], 0.4,
                                   axis='x', offset=xf - 0.04), 'chip', location=(0, y, zc[1]))
    # USB-A bleus (USB 5 Gbit/s) puis rouges (10 Gbit/s)
    for j, y in enumerate((8.35, 7.55)):
        for k, z in enumerate(zc):
            usb_a(f'io_usb5_{j}{k}', y, z, 'plastic_blue')
    for j, y in enumerate((6.4, 5.6)):
        usb_a(f'io_usb10_{j}', y, zc[0], 'plastic_red')
        usb_c(f'io_usbc_{j}', y, zc[1])
    # Ethernet RJ45 + connecteurs d'antennes Wi-Fi
    y = 3.95
    box('io_rj45', xf - 0.03, y - 0.75, zc[0] - 0.85, xr, y + 0.75, zc[0] + 0.85, 'steel', bevel=0.03)
    box('io_rj45_hole', xf - 0.04, y - 0.55, zc[0] - 0.62, xf + 0.8, y + 0.5, zc[0] + 0.62, 'chip')
    box('io_rj45_led1', xf - 0.04, y + 0.52, zc[0] - 0.75, xf, y + 0.68, zc[0] - 0.5, 'plastic_yellow')
    box('io_rj45_led2', xf - 0.04, y + 0.52, zc[0] + 0.5, xf, y + 0.68, zc[0] + 0.75, C.mat('accent'))
    for k, yy in enumerate((4.45, 3.35)):
        C.add(f'io_sma{k}', C.bm_cylinder(0.32, 0.9, axis='x', center=(xf - 0.4, yy, zc[1]), segs=6), 'gold', smooth=20)
        C.add(f'io_sma_pin{k}', C.bm_cylinder(0.12, 0.92, axis='x', center=(xf - 0.41, yy, zc[1]), segs=12), 'chip', smooth=40)
    # prises audio (jack 3,5 mm) + sortie optique
    colors = [C.mat('plastic_blue'), C.mat('plastic_yellow'), C.mat('plastic_red')]
    for k, yy in enumerate((2.3, 1.2, 0.1)):
        box(f'io_jack_body{k}', xf, yy - 0.5, zc[0] - 0.5, xr - 0.8, yy + 0.5, zc[0] + 0.5, 'plastic_black', bevel=0.03)
        C.add(f'io_jack_ring{k}', C.bm_ring(0.38, 0.2, 0.08, axis='x', center=(xf - 0.03, yy, zc[0]), segs=24), colors[k], smooth=40)
        C.add(f'io_jack_hole{k}', C.bm_cylinder(0.2, 0.05, axis='x', center=(xf - 0.04, yy, zc[0]), segs=20), 'chip', smooth=40)
    for k, yy in enumerate((1.75, 0.6)):
        box(f'io_jack2_body{k}', xf, yy - 0.5, zc[1] - 0.5, xr - 0.8, yy + 0.5, zc[1] + 0.5, 'plastic_black', bevel=0.03)
        C.add(f'io_jack2_ring{k}', C.bm_ring(0.38, 0.2, 0.08, axis='x', center=(xf - 0.03, yy, zc[1]), segs=24), 'plastic_grey', smooth=40)
        C.add(f'io_jack2_hole{k}', C.bm_cylinder(0.2, 0.05, axis='x', center=(xf - 0.04, yy, zc[1]), segs=20), 'chip', smooth=40)
    box('io_spdif', xf - 0.03, -0.85, zc[1] - 0.42, xr - 0.8, -0.15, zc[1] + 0.42, 'plastic_black', bevel=0.03)
    box('io_spdif_door', xf - 0.04, -0.72, zc[1] - 0.25, xf, -0.28, zc[1] + 0.25, 'plastic_grey')

    # cache plastique au-dessus des ports (« I/O cover »), avec un liseré d'accent
    cover = C.bm_prism([(-12.25, 13.35), (-9.3, 13.35), (-9.3, 6.0), (-10.2, 4.6), (-12.25, 4.6)], 4.0 - 0.0, axis='z',
                       offset=T + 0.02, bevel=0.12, segs=2)
    C.add('io_cover', cover, 'plastic_black')
    acc = C.bm_prism([(-12.0, 12.9), (-11.75, 12.9), (-11.75, 6.2), (-12.0, 6.2)], 0.02, axis='z', offset=T + 4.14)
    C.add('io_cover_accent', acc, 'accent')


# --------------------------------------------------------------------------- socket
def socket():
    # cadre de renfort (acier) + vis
    outer = C.rounded_rect_pts(6.0, 7.4, 0.35, segs=3, center=(SX, SY))
    frame = C.add('socket_frame', C.bm_prism(outer, 0.12, axis='z', offset=T, bevel=0.03), 'steel')
    C.cut(frame, C.bm_box(4.75, 4.75, 1.0, center=(SX, SY, T)))
    C.resmooth(frame, 35)
    for sx in (-1, 1):
        for sy in (-1, 1):
            C.add(f'socket_screw{sx}{sy}', C.bm_lathe([(0, 0.2), (0.22, 0.19), (0.27, 0.12), (0.27, 0.0), (0, 0.0)], axis='z', center=(SX + sx * 2.62, SY + sy * 3.32, T + 0.12), segs=24), 'steel', smooth=40)
            C.add(f'socket_screwx{sx}{sy}', C.bm_box(0.28, 0.05, 0.03, center=(SX + sx * 2.62, SY + sy * 3.32, T + 0.315)), 'chip')
    # corps du socket (plastique noir) avec cavité ; fond texturé (broches)
    body = C.add('socket_body', C.bm_box_minmax(SX - 2.3, SY - 2.3, T, SX + 2.3, SY + 2.3, T + 0.37, bevel=0.03), 'plastic_black')
    C.cut(body, C.bm_box_minmax(SX - 2.02, SY - 2.02, T + 0.17, SX + 2.02, SY + 2.02, T + 0.6))
    C.resmooth(body, 35)
    pins_img = pins_texture()
    pins_mat = C.textured_mat('socket_pins', pins_img, metallic=0.5, roughness=0.35)
    floor = C.bm_box_minmax(SX - 2.02, SY - 2.02, T + 0.16, SX + 2.02, SY + 2.02, T + 0.175)
    top = C.faces_facing(floor, (0, 0, 1), 0.99)
    C.uv_project(floor, 'z', rect=(SX - 2.02, SY - 2.02, SX + 2.02, SY + 2.02), faces=top)
    C.uv_constant(floor, 0.01, 0.01, faces=[f for f in floor.faces if f not in top])
    C.add('socket_pins', floor, pins_mat)
    # clés d'alignement (correspondent aux encoches du processeur)
    for sx in (-1, 1):
        C.add(f'socket_key{sx}', C.bm_cylinder(0.09, 0.2, axis='z', center=(SX + sx * 1.97, SY + 0.75, T + 0.27), segs=12), 'plastic_black', smooth=40)
    # triangle de repérage sur le socket (coin inférieur gauche)
    tri = C.bm_prism([(SX - 2.25, SY - 2.25), (SX - 1.75, SY - 2.25), (SX - 2.25, SY - 1.75)], 0.004, axis='z', offset=T + 0.37)
    C.add('socket_triangle', tri, 'gold')
    silk('am5', 'AM5', SX + 1.7, SY - 2.17, size=0.16, z=T + 0.373, m='plastic_grey')

    # cadre de maintien (« load plate ») : charnière côté gauche, languette sous le levier
    zp = L.CPU_SEAT_Z + L.CPU_SUBSTRATE_T
    plate_outline = [(-2.45, -2.45), (2.3, -2.45), (2.3, -0.55), (2.95, -0.45), (2.95, 0.45), (2.3, 0.55), (2.3, 2.45), (-2.45, 2.45)]
    plate = C.add('socket_loadplate', C.bm_prism([(SX + x, SY + y) for (x, y) in plate_outline], 0.07, axis='z', offset=zp, bevel=0.02), 'steel')
    C.cut(plate, C.bm_box(3.86, 3.86, 1.0, center=(SX, SY, zp)))
    C.resmooth(plate, 35)
    parts = [plate]
    for yy in (-1.8, 1.8):   # charnières roulées
        parts.append(C.add(f'lp_hinge{yy}', C.bm_cylinder(0.11, 0.7, axis='y', center=(SX - 2.55, SY + yy, zp + 0.04), segs=16), 'steel', smooth=40))
        parts.append(C.add(f'lp_hingeb{yy}', C.bm_box_minmax(SX - 2.6, SY + yy - 0.35, zp, SX - 2.4, SY + yy + 0.35, zp + 0.07), 'steel'))
    lp = C.merge('socket_loadplate', parts)
    C.keep(lp, pivot=(SX - 2.55, SY, zp + 0.04))

    # levier (fil d'acier) : tige pivot le long du bord droit + poignée
    xr = SX + 2.8
    zr = L.CPU_SEAT_Z + L.CPU_SUBSTRATE_T + 0.13
    for yy in (SY - 3.3, SY + 3.25):   # paliers du levier
        box(f'lever_bearing{yy:.1f}', xr - 0.22, yy - 0.2, T, xr + 0.22, yy + 0.2, zr + 0.08, 'steel', bevel=0.03)
    rod = C.tube('lever_rod', [(xr, SY - 3.3, zr), (xr, SY + 3.25, zr)], 0.075, 'steel', smooth=60)
    # coude + poignée qui pointe vers +X quand le levier est fermé (couché sur la carte)
    pts = [(xr, SY - 3.3, zr)]
    pts += [tuple(p) for p in C.arc_path((xr, SY - 3.3, zr), (xr + 0.35, SY - 3.65, zr), (xr + 0.35, SY - 3.3, zr), n=6)][1:]
    pts += [(xr + 1.6, SY - 3.65, zr)]
    handle = C.tube('lever_handle', pts, 0.075, 'steel', smooth=60)
    grip = C.add('lever_grip', C.bm_cylinder(0.12, 0.7, axis='x', center=(xr + 1.3, SY - 3.65, zr), segs=16), 'plastic_black', smooth=40)
    lever = C.merge('socket_lever', [rod, handle, grip])
    C.keep(lever, pivot=(xr, SY, zr))
    # crochet de retenue du levier
    box('lever_hook', xr + 0.75, SY - 4.0, T, xr + 1.1, SY - 3.77, zr + 0.12, 'steel', bevel=0.02)


# --------------------------------------------------------------------------- construction
def build():
    # PCB (dessus texturé)
    pcb_img = pcb_texture()
    pcb_mat = C.textured_mat('mb_pcb', pcb_img, roughness=0.45)
    bm = C.bm_box(L.MB_W, L.MB_H, T, center=(0, 0, T / 2), bevel=0.02)
    top = C.faces_facing(bm, (0, 0, 1), 0.99)
    for f in top:
        f.material_index = 1
    C.uv_project(bm, 'z', rect=(-L.MB_W / 2, -L.MB_H / 2, L.MB_W / 2, L.MB_H / 2), faces=top)
    C.uv_constant(bm, 0.02, 0.98, faces=[f for f in bm.faces if f not in top])
    C.add('pcb', bm, ['pcb_black', pcb_mat])
    # anneaux des trous de fixation
    for i, (hx, hy) in enumerate(L.HOLES):
        C.add(f'hole_ring{i}', C.bm_ring(0.45, 0.2, 0.02, axis='z', center=(hx, hy, T + 0.005), segs=28), 'solder', smooth=40)
        C.add(f'hole{i}', C.bm_cylinder(0.2, 0.02, axis='z', center=(hx, hy, T + 0.004), segs=20), 'chip', smooth=40)
        C.anchor(f'anchor_hole_{i + 1}', (hx, hy, T))

    socket()

    # étage d'alimentation du CPU (VRM) : dissipateurs à ailettes
    box('vrm_left', -9.3, -0.4, T, -7.0, 10.0, T + 2.7, 'alu_grey', bevel=0.12, segs=2)
    for k in range(9):
        yy = 0.2 + k * 1.1
        box(f'vrm_left_groove{k}', -9.32, yy, T + 0.8, -6.98, yy + 0.35, T + 2.72, 'plastic_black')
    box('vrm_top', -9.3, 10.9, T, -0.6, 13.15, T + 2.5, 'alu_grey', bevel=0.12, segs=2)
    for k in range(7):
        xx = -8.6 + k * 1.15
        box(f'vrm_top_groove{k}', xx, 10.88, T + 0.8, xx + 0.4, 13.17, T + 2.52, 'plastic_black')
    box('vrm_top_accent', -9.0, 12.8, T + 2.5, -1.0, 12.95, T + 2.53, 'accent')
    C.add('vrm_heatpipe', C.bm_cylinder(0.3, 2.0, axis='y', center=(-8.2, 10.4, T + 0.45), segs=16), 'nickel', smooth=40)

    # mémoire
    for key, xc in L.DIMM_X.items():
        dimm_slot(key, xc)
        silk('dimm_' + key, key, xc, L.DIMM_Y + L.DIMM_SLOT_LEN / 2 + 0.95, size=0.24)
    silk('ddr5', 'DDR5', 4.9, L.DIMM_Y - L.DIMM_SLOT_LEN / 2 - 0.9, size=0.26)

    # slots PCIe
    pcie_slot('pcie_x16', L.PCIE_X16_X0, L.PCIE_X16_X1, L.PCIE_X16_Y, armor=True, latch=True)
    silk('pcie1', 'PCIEX16_1', -5.0, L.PCIE_X16_Y - 0.8, size=0.24)
    pcie_slot('pcie_x1', L.PCIE_X16_X0, L.PCIE_X16_X0 + 2.5, L.slot_y(4))
    silk('pcie2', 'PCIEX1_1', -7.0, L.slot_y(4) - 0.05, size=0.2)
    pcie_slot('pcie_x4', L.PCIE_X16_X0, L.PCIE_X16_X1, L.slot_y(6))
    silk('pcie3', 'PCIEX16_2 (x4)', -5.0, L.slot_y(6) - 0.8, size=0.22)

    # M.2
    m2_slot('M2_1', L.M2['M2_1'])
    silk('m21', 'M.2_1', -5.0, L.M2['M2_1']['y'] + 1.5, size=0.24)
    m2_slot('M2_2', L.M2['M2_2'], heatsink=True)

    # chipset (dissipateur)
    box('chipset_hs', 3.0, -12.2, T, 8.6, -6.4, T + 0.9, 'alu_grey', bevel=0.15, segs=2)
    C.add('chipset_plate', C.bm_prism([(3.6, -11.6), (8.0, -11.6), (8.0, -8.2), (6.3, -7.0), (3.6, -7.0)], 0.12, axis='z',
                                      offset=T + 0.9, bevel=0.04), 'plastic_dark')
    C.add('chipset_accent', C.bm_prism([(6.0, -7.25), (6.45, -7.25), (8.0, -8.45), (8.0, -8.9)], 0.02, axis='z', offset=T + 1.02), 'accent')

    # connecteurs d'alimentation
    z24 = power_header('atx24', L.ATX24['x0'], L.ATX24['y0'], L.ATX24['x1'], L.ATX24['y1'], 2, 12, height=1.0)
    box('atx24_clip', L.ATX24['x0'] - 0.15, 5.7, T + 0.3, L.ATX24['x0'], 6.5, T + 0.95, 'plastic_black')
    silk('atx', 'ATX_24P', 10.0, 6.1, size=0.22, rot=90)
    zeps = power_header('eps8', L.EPS8['x0'], L.EPS8['y0'], L.EPS8['x1'], L.EPS8['y1'], 4, 2, height=1.0)
    silk('eps', 'EPS_12V', L.EPS8['x1'] + 0.25, 14.0, size=0.2, align='LEFT')

    # en-têtes : ventilateurs, façade, USB, audio
    fan_header('cpu_fan', *L.CPU_FAN)
    silk('cpufan', 'CPU_FAN', L.CPU_FAN[0], L.CPU_FAN[1] - 0.55, size=0.18)
    for i, (fx, fy) in enumerate(L.SYS_FAN):
        fan_header(f'sys_fan{i + 1}', fx, fy)
        silk(f'sysfan{i}', f'SYS_FAN{i + 1}', fx, fy + 0.55, size=0.16)
    pin_header('f_panel', L.F_PANEL['x0'] + 0.3, L.F_PANEL['y0'] + 0.15, 5, 2, missing=((4, 1),))
    silk('fpanel', 'F_PANEL', 7.5, -13.45, size=0.2)
    pin_header('usb2a', 1.4, -14.6, 5, 2, missing=((4, 0),))
    pin_header('usb2b', -1.8, -14.6, 5, 2, missing=((4, 0),))
    silk('usb2', 'USB2', 0.5, -13.75, size=0.18)
    pin_header('hd_audio', L.HD_AUDIO['x0'] + 0.3, L.HD_AUDIO['y0'] + 0.15, 5, 2, missing=((3, 1),))
    silk('aud', 'HD_AUDIO', -9.6, -13.45, size=0.18)
    u = L.USB3_HDR
    box('usb3_shroud', u['x0'], u['y0'], T, u['x1'], u['y1'], T + 0.85, 'plastic_blue', bevel=0.02)
    box('usb3_cavity', u['x0'] + 0.12, u['y0'] + 0.12, T + 0.3, u['x1'] - 0.12, u['y1'] - 0.12, T + 0.86, 'chip')
    box('usb3_key', u['x1'] - 0.12, (u['y0'] + u['y1']) / 2 - 0.2, T + 0.3, u['x1'] - 0.02, (u['y0'] + u['y1']) / 2 + 0.2, T + 0.86, 'chip')
    for i in range(2):
        for j in range(10):
            if (i, j) == (1, 9):
                continue
            cx = u['x0'] + 0.37 + i * 0.25
            cy = u['y0'] + 0.17 + j * 0.25
            box(f'usb3_p{i}_{j}', cx - 0.03, cy - 0.03, T + 0.3, cx + 0.03, cy + 0.03, T + 0.75, 'gold')
    silk('usb3', 'USB3_1', 9.8, -3.9, size=0.18, rot=90)
    c = L.USBC_HDR
    box('usbc_hdr', c['x0'], c['y0'], T, c['x1'], c['y1'], T + 0.8, 'plastic_black', bevel=0.03)
    box('usbc_hdr_slot', c['x0'] + 0.25, c['y0'] + 0.2, T + 0.78, c['x1'] - 0.25, c['y1'] - 0.2, T + 0.81, 'chip')
    silk('usbc', 'USB_C', 9.8, -1.1, size=0.16, rot=90)
    # ports SATA (coudés, vers l'avant de la carte)
    for i, yy in enumerate((-8.0, -9.3)):
        for j, zz in enumerate((T, T + 0.62)):
            box(f'sata{i}{j}', 11.0, yy - 0.55, zz, 12.25, yy + 0.55, zz + 0.6, 'plastic_black', bevel=0.02)
            box(f'sata_h{i}{j}', 12.0, yy - 0.42, zz + 0.12, 12.26, yy + 0.42, zz + 0.27, 'chip')
            box(f'sata_l{i}{j}', 12.0, yy - 0.42, zz + 0.12, 12.26, yy - 0.27, zz + 0.48, 'chip')
    silk('sata', 'SATA6G', 10.3, -8.65, size=0.18, rot=90)

    # pile de sauvegarde du BIOS (CR2032)
    C.add('cmos_holder', C.bm_ring(1.15, 1.0, 0.3, axis='z', center=(-6.2, -7.0, T + 0.15), segs=40), 'plastic_black', smooth=40)
    C.add('cmos_bat', C.bm_cylinder(1.0, 0.32, axis='z', center=(-6.2, -7.0, T + 0.18), segs=40), 'steel', smooth=40)
    C.add('cmos_bat_top', C.bm_cylinder(0.85, 0.02, axis='z', center=(-6.2, -7.0, T + 0.345), segs=40), 'alu', smooth=40)
    silk('bat', 'BAT', -4.6, -7.0, size=0.2)

    # condensateurs polymères sous le socket
    for k in range(6):
        polymer_cap(f'pcap{k}', -6.0 + k * 0.9, 0.95)
    for k in range(3):
        polymer_cap(f'pcap_r{k}', 8.35, 9.6 + k * 0.85, r=0.28, h=0.65)
    # puce audio sous blindage + condensateurs audio
    box('audio_shield', -12.0, -6.4, T, -10.85, -5.15, T + 0.18, 'steel', bevel=0.03)
    for k in range(5):
        C.add(f'acap{k}', C.bm_cylinder(0.3, 0.6, axis='z', center=(-11.45, -7.4 - k * 0.95, T + 0.3), segs=24), 'plastic_yellow', smooth=40)
        C.add(f'acap_t{k}', C.bm_cylinder(0.28, 0.02, axis='z', center=(-11.45, -7.4 - k * 0.95, T + 0.61), segs=24), 'alu', smooth=40)
    # quelques puces (contrôleurs réseau, super I/O)
    box('chip_lan', 6.0, 11.3, T, 7.0, 12.3, T + 0.12, 'chip')
    box('chip_sio', 7.8, -4.6, T, 9.0, -3.4, T + 0.12, 'chip')
    box('chip_bios', 9.0, -12.9, T, 9.6, -12.3, T + 0.15, 'chip')

    # LED de diagnostic (s'allument au démarrage en cas de problème)
    leds = []
    names = ['CPU', 'DRAM', 'VGA', 'BOOT']
    for k, nm in enumerate(names):
        y = 10.3 - k * 0.5
        leds.append(C.add(f'led_{nm}', C.bm_box_minmax(9.9, y - 0.1, T, 10.2, y + 0.1, T + 0.12), 'led'))
        silk('led_' + nm, nm, 9.7, y, size=0.16, align='RIGHT')
    led = C.merge('debug_leds', leds)
    C.keep(led)

    io_ports()

    # ancres utilisées par le site
    C.anchor('anchor_cpu', (SX, SY, L.CPU_SEAT_Z))
    C.anchor('anchor_cooler', (SX, SY, L.COOLER_Z))
    C.anchor('anchor_socket_triangle', (SX - 2.1, SY - 2.1, T + 0.38))
    for key, xc in L.DIMM_X.items():
        C.anchor('anchor_ram_' + key, (xc, L.DIMM_Y, L.RAM_SEAT_Z))
    for key, conf in L.M2.items():
        C.anchor('anchor_' + key.lower().replace('m2_', 'm2_'), (conf['conn_x'], conf['y'], conf['z']))
    C.anchor('anchor_m2_screw', (L.M2['M2_1']['conn_x'] + L.M2_LEN, L.M2['M2_1']['y'], L.M2['M2_1']['z'] + 0.08))
    C.anchor('anchor_pcie_x16', (L.PCIE_X16_XC, L.PCIE_X16_Y, L.PCIE_SEAT_Z))
    C.anchor('anchor_atx24', ((L.ATX24['x0'] + L.ATX24['x1']) / 2, (L.ATX24['y0'] + L.ATX24['y1']) / 2, z24))
    C.anchor('anchor_eps8', ((L.EPS8['x0'] + L.EPS8['x1']) / 2, (L.EPS8['y0'] + L.EPS8['y1']) / 2, zeps))
    C.anchor('anchor_cpu_fan', (L.CPU_FAN[0], L.CPU_FAN[1], T + 0.62))
    for i, (fx, fy) in enumerate(L.SYS_FAN):
        C.anchor(f'anchor_sys_fan_{i + 1}', (fx, fy, T + 0.62))
    C.anchor('anchor_f_panel', ((L.F_PANEL['x0'] + L.F_PANEL['x1']) / 2, (L.F_PANEL['y0'] + L.F_PANEL['y1']) / 2, T + 0.85))
    C.anchor('anchor_usb3', ((u['x0'] + u['x1']) / 2, (u['y0'] + u['y1']) / 2, T + 0.85))
    C.anchor('anchor_hd_audio', ((L.HD_AUDIO['x0'] + L.HD_AUDIO['x1']) / 2, (L.HD_AUDIO['y0'] + L.HD_AUDIO['y1']) / 2, T + 0.85))
    C.anchor('anchor_io', (-L.MB_W / 2 - 0.85, (L.IO_Y0 + L.IO_Y1) / 2, T + 2.2))
    C.anchor('anchor_debug_leds', (10.05, 9.55, T + 0.12))
    C.INFO['size_cm'] = [L.MB_W, L.MB_H, T]
    return dict(preview_view=(0.35, 0.25, 1.0), preview_fov=30)


if __name__ == '__main__':
    C.run(build, 'motherboard')
