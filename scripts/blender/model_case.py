"""
model_case.py — Boîtier moyen tour ATX (45 x 22 x 48 cm) : panneau latéral en verre
trempé, alimentation en bas sous un cache, façade en mesh pour 3 ventilateurs de 120 mm,
emplacement de 120 mm à l'arrière, 7 slots d'extension, plateau avec passe-câbles.

Les ventilateurs, la carte mère, l'alimentation… ne font PAS partie de ce modèle :
le site les place sur les ancres (empties) nommées anchor_*.

Orientation : avant du boîtier vers +X, vitre vers +Z. Origine = centre de l'empreinte au sol.

    blender -b -P scripts/blender/model_case.py
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

HX, HZ, H = L.CASE_L / 2, L.CASE_W / 2, L.CASE_H
REAR, REAR_IN = L.REAR_X, L.REAR_IN_X          # -22.5 / -22.0
FRONT_IN = 21.3                                # support des ventilateurs avant


def box(name, x0, y0, z0, x1, y1, z1, m, bevel=0.0, segs=1):
    return C.add(name, C.bm_box_minmax(x0, y0, z0, x1, y1, z1, bevel=bevel, segs=segs), m)


def perforated_tex(w, h, pitch, r, name, color='#141518'):
    """Tôle perforée (trous ronds en quinconce), trous transparents."""
    cv = C.Canvas(w, h, C.srgb(color))
    dy = pitch * math.sqrt(3) / 2
    row = 0
    y = r + 1
    while y < h - r:
        x = r + 1 + (pitch / 2 if row % 2 else 0)
        while x < w - r:
            cv.circle(x, y, r, (0, 0, 0, 1), hole=True)
            x += pitch
        y += dy
        row += 1
    return cv.save(name)


def mesh_plane(name, mat_, axis, rect, at, flip_u=False):
    """Plaque fine texturée (mesh) : axis = normale ('x', 'y' ou 'z'), rect dans le plan."""
    a0, b0, a1, b1 = rect
    t = 0.03
    if axis == 'x':
        bm = C.bm_box_minmax(at - t / 2, b0, a0, at + t / 2, b1, a1)
        axes = ('z', 'y')
    elif axis == 'y':
        bm = C.bm_box_minmax(a0, at - t / 2, b0, a1, at + t / 2, b1)
        axes = ('x', 'z')
    else:
        bm = C.bm_box_minmax(a0, b0, at - t / 2, a1, b1, at + t / 2)
        axes = ('x', 'y')
    big = [f for f in bm.faces if abs(f.normal['xyz'.index(axis)]) > 0.9]
    C.uv_project(bm, rect=(a0, b0, a1, b1), faces=big, axes=axes, flip_u=flip_u)
    C.uv_constant(bm, 0.0, 0.0, faces=[f for f in bm.faces if f not in big])
    return C.add(name, bm, mat_)


def build():
    s_k = [L.MB_CENTER[1] + L.slot_y(k) for k in range(1, 8)]   # plan PCB de chaque position de slot

    # ------------------------------------------------------------------ châssis
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        x0 = sx * (HX - 1.0) - (4.5 if sx > 0 else 0)
        box(f'foot{sx}{sz}', x0, 0.0, sz * (HZ - 2.0) - 1.6, x0 + 4.5, L.FEET_H, sz * (HZ - 2.0) + 1.6, 'plastic_black', bevel=0.3, segs=2)
        box(f'foot_pad{sx}{sz}', x0 + 0.4, -0.02, sz * (HZ - 2.0) - 1.2, x0 + 4.1, 0.15, sz * (HZ - 2.0) + 1.2, 'rubber', bevel=0.05)
    bottom = box('bottom', REAR, L.FEET_H, -HZ, HX, L.FLOOR_Y, HZ, 'steel_black', bevel=0.1)
    # entrée d'air de l'alimentation sous le boîtier (son ventilateur aspire par le bas),
    # protégée par un filtre à poussière amovible qui se tire par l'arrière
    pcx, pcz = L.PSU_CENTER[0] + 0.4, L.PSU_CENTER[2]           # axe du ventilateur de l'alimentation
    ox0, ox1, oz0, oz1 = pcx - 6.2, pcx + 6.2, pcz - 6.2, pcz + 6.2
    C.cut(bottom, C.bm_box_minmax(ox0, L.FEET_H - 1, oz0, ox1, L.FLOOR_Y + 1, oz1, bevel=0.6, segs=3))
    flt = perforated_tex(256, 256, 6.0, 2.3, 'case_bottom_filter', color='#101113')
    flt_mat = C.textured_mat('case_bottom_filter', flt, metallic=0.2, roughness=0.6, mask=True)
    mesh_plane('psu_filter_mesh', flt_mat, 'y', (ox0 - 0.2, oz0 - 0.2, ox1 + 0.2, oz1 + 0.2), L.FEET_H - 0.12)
    frame = box('psu_filter_frame', REAR + 0.4, L.FEET_H - 0.25, oz0 - 0.6, ox1 + 0.6, L.FEET_H - 0.02, oz1 + 0.6, 'plastic_black', bevel=0.08)
    C.cut(frame, C.bm_box_minmax(ox0, L.FEET_H - 1, oz0, ox1, L.FEET_H + 1, oz1, bevel=0.5, segs=2))
    box('psu_filter_tab', REAR - 0.35, L.FEET_H - 0.25, pcz - 2.0, REAR + 0.5, L.FEET_H + 0.15, pcz + 2.0, 'plastic_black', bevel=0.1)

    # panneau droit (opaque) et plateau de la carte mère
    # panneau droit (opaque) : objet séparé pour pouvoir l'ouvrir pendant le montage (cable management)
    pr = box('case_panel_right', REAR, L.FLOOR_Y, -HZ, HX - 0.6, H - 0.5, -HZ + 0.12, 'steel_black', bevel=0.05)
    C.keep(pr, pivot=(0.0, H / 2, -HZ + 0.06))
    tray = box('tray', REAR_IN, L.SHROUD_TOP, L.TRAY_Z - 0.1, 17.5, H - 1.0, L.TRAY_Z, 'steel_black')
    mbx, mby = L.MB_CENTER
    cutters = [
        C.bm_box_minmax(4.4, 16.5, -20, 5.7, 26.5, 20, bevel=0.5, segs=3),          # passe-câbles droite (bas)
        C.bm_box_minmax(4.4, 28.5, -20, 5.7, 40.5, 20, bevel=0.5, segs=3),          # passe-câbles droite (haut)
        C.bm_box_minmax(-17.6, 45.3, -20, -10.6, 46.7, 20, bevel=0.5, segs=3),      # passage du câble EPS (en haut)
        C.bm_box_minmax(mbx - 8.0, mby + 1.3, -20, mbx + 1.6, mby + 11.0, 20, bevel=0.6, segs=3),  # découpe derrière le socket
    ]
    C.cut(tray, *cutters)
    for i, (x0, y0, x1, y1) in enumerate(((4.4, 16.5, 5.7, 26.5), (4.4, 28.5, 5.7, 40.5), (-17.6, 45.3, -10.6, 46.7))):
        g = C.add(f'grommet{i}', C.bm_box_minmax(x0 - 0.25, y0 - 0.25, L.TRAY_Z - 0.15, x1 + 0.25, y1 + 0.25, L.TRAY_Z + 0.08, bevel=0.2, segs=2), 'rubber')
        C.cut(g, C.bm_box_minmax(x0 + 0.05, y0 + 0.05, -20, x1 - 0.05, y1 - 0.05, 20, bevel=0.4, segs=2))
        # fente dans la membrane caoutchouc
        box(f'grommet_slit{i}', (x0 + x1) / 2 - 0.04, y0 + 0.2, L.TRAY_Z - 0.06, (x0 + x1) / 2 + 0.04, y1 - 0.2, L.TRAY_Z - 0.04, 'chip')
        box(f'grommet_mem{i}', x0, y0, L.TRAY_Z - 0.07, x1, y1, L.TRAY_Z - 0.05, 'rubber')

    # montants et traverses visibles derrière la vitre
    box('rail_top', REAR, H - 1.6, HZ - 1.1, HX - 0.6, H - 0.5, HZ - 0.15, 'steel_black', bevel=0.05)
    box('rail_bottom', REAR, L.FLOOR_Y, HZ - 1.1, HX - 0.6, L.FLOOR_Y + 1.0, HZ - 0.15, 'steel_black', bevel=0.05)
    fr = C.add('post_front_plate', C.bm_box_minmax(FRONT_IN, L.FLOOR_Y, -HZ + 0.3, FRONT_IN + 0.2, H - 0.6, HZ - 0.3), 'steel_black')
    C.cut(fr, *[C.bm_cylinder(5.8, 2, axis='x', center=(FRONT_IN, fy, fz), segs=64) for (_, fy, fz) in L.FAN_FRONT])

    # ------------------------------------------------------------------ face arrière
    rear = box('rear', REAR, L.FLOOR_Y, -HZ + 0.1, REAR_IN, H - 0.5, HZ - 0.1, 'steel_black')
    io_y0, io_y1 = mby + L.IO_Y0 - 0.1, mby + L.IO_Y1 + 0.1
    io_z0, io_z1 = L.MB_BACK_Z + L.MB_T + 0.02, L.MB_BACK_Z + L.IO_Z1 + 0.05
    psu_c = L.PSU_CENTER
    psu_y0, psu_y1 = psu_c[1] - L.PSU_SIZE[1] / 2 + 0.15, psu_c[1] + L.PSU_SIZE[1] / 2 - 0.15
    psu_z0, psu_z1 = psu_c[2] - L.PSU_SIZE[2] / 2 + 0.15, psu_c[2] + L.PSU_SIZE[2] / 2 - 0.15
    sl_y0, sl_y1 = s_k[6] - 1.75, s_k[0] + 0.42
    sl_z0, sl_z1 = -8.7, 3.6
    fr_y, fr_z = L.FAN_REAR[1], L.FAN_REAR[2]
    C.cut(rear,
          C.bm_box_minmax(REAR - 1, io_y0, io_z0, REAR_IN + 1, io_y1, io_z1),
          C.bm_box_minmax(REAR - 1, psu_y0, psu_z0, REAR_IN + 1, psu_y1, psu_z1),
          C.bm_box_minmax(REAR - 1, sl_y0, sl_z0, REAR_IN + 1, sl_y1, sl_z1),
          C.bm_cylinder(5.75, 3, axis='x', center=(REAR, fr_y, fr_z), segs=64))
    hc = perforated_tex(256, 256, 11.0, 4.2, 'case_rear_vent')
    hc_mat = C.textured_mat('case_rear_vent', hc, metallic=0.45, roughness=0.45, mask=True)
    mesh_plane('rear_vent', hc_mat, 'x', (fr_z - 5.75, fr_y - 5.75, fr_z + 5.75, fr_y + 5.75), REAR + 0.25, flip_u=True)
    # vis de fixation du ventilateur arrière
    for (dy, dz) in ((-5.25, -5.25), (-5.25, 5.25), (5.25, -5.25), (5.25, 5.25)):
        C.add(f'rfan_screw{dy}{dz}', C.bm_cylinder(0.3, 0.12, axis='x', center=(REAR - 0.05, fr_y + dy, fr_z + dz), segs=16), 'steel', smooth=40)
    # caches des slots d'extension (amovibles : on retire ceux qu'occupe la carte graphique)
    for k in range(7):
        y0, y1 = s_k[k] - 1.68, s_k[k] + 0.35
        cov = C.add(f'slot_cover_{k + 1}', C.bm_box_minmax(REAR + 0.05, y0 + 0.04, sl_z0 + 0.1, REAR + 0.15, y1 - 0.04, sl_z1 - 0.05), 'steel')
        C.cut(cov, *[C.bm_box_minmax(REAR - 1, (y0 + y1) / 2 - 0.35, -7.2 + j * 2.2, REAR + 1, (y0 + y1) / 2 + 0.35, -6.1 + j * 2.2) for j in range(5)])
        C.keep(cov)
    box('slot_bar', REAR - 0.12, sl_y0, sl_z1 - 0.1, REAR + 0.05, sl_y1, sl_z1 + 1.1, 'steel_black', bevel=0.04)
    for k in range(7):
        C.add(f'slot_screw{k}', C.bm_lathe([(0, -0.3), (0.3, -0.28), (0.36, -0.18), (0.36, 0.0), (0, 0.0)], axis='x',
                                           center=(REAR - 0.12, s_k[k] - 0.66, sl_z1 + 0.5), segs=20), 'steel_black', smooth=40)
    # vis à main du panneau droit
    for yy in (8.0, 40.0):
        C.add(f'thumb{yy}', C.bm_cylinder(0.55, 0.5, axis='x', center=(REAR - 0.25, yy, -HZ + 0.7), segs=24), 'steel_black', smooth=40)

    # ------------------------------------------------------------------ façade mesh
    fm = perforated_tex(512, 1024, 9.0, 3.3, 'case_front_mesh')
    fm_mat = C.textured_mat('case_front_mesh', fm, metallic=0.4, roughness=0.5, mask=True)
    frame_out = C.add('front_frame', C.bm_box_minmax(HX - 0.6, L.FEET_H, -HZ, HX, H, HZ, bevel=0.25, segs=2), 'plastic_black')
    C.cut(frame_out, C.bm_box_minmax(HX - 2, 3.4, -HZ + 1.3, HX + 2, H - 1.4, HZ - 1.3, bevel=0.4, segs=2))
    mesh_plane('front_mesh', fm_mat, 'x', (-HZ + 1.3, 3.4, HZ - 1.3, H - 1.4), HX - 0.25)
    box('front_accent', HX - 0.05, 3.6, HZ - 0.95, HX + 0.01, H - 1.6, HZ - 0.8, 'accent')

    # ------------------------------------------------------------------ dessus : mesh + façade I/O
    top = box('top', REAR, H - 0.5, -HZ, HX - 0.55, H, HZ, 'steel_black', bevel=0.12)
    C.cut(top, C.bm_box_minmax(-17.0, H - 2, -6.5, 15.0, H + 2, 8.5, bevel=0.3, segs=2))
    tm = perforated_tex(1024, 512, 10.0, 3.6, 'case_top_mesh')
    tm_mat = C.textured_mat('case_top_mesh', tm, metallic=0.4, roughness=0.5, mask=True)
    mesh_plane('top_mesh', tm_mat, 'y', (-17.0, -6.5, 15.0, 8.5), H - 0.1)
    # façade I/O sur le dessus, à l'avant : bouton, USB-A x2, USB-C, prise casque, reset
    ix = 19.4
    btn = C.add('case_power_button', C.bm_lathe([(0, H + 0.32), (0.55, H + 0.31), (0.68, H + 0.25), (0.7, H), (0, H)], axis='y', center=(ix, 0, -5.2), segs=40), 'plastic_dark', smooth=40)
    C.keep(btn, pivot=(ix, H, -5.2))
    led = C.add('case_power_led', C.bm_ring(0.92, 0.76, 0.06, axis='y', center=(ix, H + 0.02, -5.2), segs=40), 'led', smooth=40)
    C.keep(led)
    for k, zc in enumerate((-2.9, -1.2)):
        box(f'fio_usb{k}', ix - 0.32, H - 0.3, zc - 0.7, ix + 0.32, H + 0.02, zc + 0.7, 'steel', bevel=0.02)
        box(f'fio_usb_h{k}', ix - 0.26, H - 0.3, zc - 0.62, ix + 0.26, H + 0.025, zc + 0.62, 'chip')
        box(f'fio_usb_t{k}', ix - 0.05, H - 0.3, zc - 0.55, ix + 0.15, H + 0.03, zc + 0.55, 'plastic_blue')
    box('fio_usbc', ix - 0.2, H - 0.3, 0.1, ix + 0.2, H + 0.02, 1.1, 'steel', bevel=0.12, segs=2)
    box('fio_usbc_h', ix - 0.13, H - 0.3, 0.18, ix + 0.13, H + 0.025, 1.02, 'chip', bevel=0.08, segs=2)
    C.add('fio_jack', C.bm_cylinder(0.3, 0.05, axis='y', center=(ix, H + 0.01, 2.2), segs=24), 'chip', smooth=40)
    C.add('fio_jack_ring', C.bm_ring(0.42, 0.3, 0.04, axis='y', center=(ix, H + 0.02, 2.2), segs=24), 'steel', smooth=40)
    C.add('fio_reset', C.bm_cylinder(0.28, 0.08, axis='y', center=(ix, H + 0.02, 3.4), segs=24), 'plastic_dark', smooth=40)

    # ------------------------------------------------------------------ cache-alimentation (PSU shroud)
    st = L.SHROUD_TOP
    shroud_top = box('shroud_top', REAR_IN, st - 0.12, L.TRAY_Z, L.SHROUD_X1, st, L.GLASS_Z - 0.55, 'steel_black', bevel=0.04)
    C.cut(shroud_top, C.bm_box_minmax(-4.5, st - 2, L.TRAY_Z + 0.4, 2.5, st + 2, L.TRAY_Z + 2.4, bevel=0.4, segs=2))
    box('shroud_side', REAR_IN, L.FLOOR_Y, L.GLASS_Z - 0.67, L.SHROUD_X1, st, L.GLASS_Z - 0.55, 'steel_black', bevel=0.04)
    box('shroud_end', L.SHROUD_X1 - 0.12, L.FLOOR_Y, L.TRAY_Z, L.SHROUD_X1, st, L.GLASS_Z - 0.55, 'steel_black', bevel=0.04)
    box('shroud_accent', -18.0, st - 0.9, L.GLASS_Z - 0.53, 10.0, st - 0.75, L.GLASS_Z - 0.51, 'accent')
    # aération au-dessus des ventilateurs avant, sur le cache
    for k in range(6):
        box(f'shroud_vent{k}', L.SHROUD_X1 - 4.0 + k * 0.6, st - 0.15, -4.0, L.SHROUD_X1 - 3.7 + k * 0.6, st + 0.005, 6.0, 'chip')

    # ------------------------------------------------------------------ entretoises (vissées dans le plateau)
    for i, (hx, hy) in enumerate(L.HOLES):
        x, y, _ = L.mb_to_case(hx, hy)
        st_bm = C.bm_cylinder(0.32, L.STANDOFF_H, axis='z', center=(0, 0, L.TRAY_Z + L.STANDOFF_H / 2), segs=6)
        thread = C.bm_cylinder(0.14, 0.02, axis='z', center=(0, 0, L.MB_BACK_Z + 0.005), segs=12)
        so = C.add(f'standoff_{i + 1}', st_bm, 'brass', smooth=20)
        th = C.add(f'standoff_hole_{i + 1}', thread, 'chip')
        so = C.merge(f'standoff_{i + 1}', [so, th])
        so.location = (x, y, 0)
        C.keep(so, pivot=(x, y, L.TRAY_Z))

    # ------------------------------------------------------------------ panneau en verre trempé (amovible)
    gz0 = L.GLASS_Z + 0.05
    glass = C.add('glass_slab', C.bm_box_minmax(REAR + 0.15, L.FLOOR_Y + 0.1, gz0, HX - 0.65, H - 0.6, gz0 + 0.4, bevel=0.06), 'glass')
    parts = [glass]
    fw = 1.3
    for (x0, y0, x1, y1) in ((REAR + 0.15, L.FLOOR_Y + 0.1, HX - 0.65, L.FLOOR_Y + 0.1 + fw),
                             (REAR + 0.15, H - 0.6 - fw, HX - 0.65, H - 0.6),
                             (REAR + 0.15, L.FLOOR_Y + 0.1, REAR + 0.15 + fw, H - 0.6),
                             (HX - 0.65 - fw, L.FLOOR_Y + 0.1, HX - 0.65, H - 0.6)):
        parts.append(C.add(f'frit{x0}{y0}', C.bm_box_minmax(x0, y0, gz0 - 0.03, x1, y1, gz0 - 0.005), 'plastic_black'))
    for (x, y) in ((REAR + 0.9, L.FLOOR_Y + 0.85), (REAR + 0.9, H - 1.35), (HX - 1.4, L.FLOOR_Y + 0.85), (HX - 1.4, H - 1.35)):
        parts.append(C.add(f'gscrew{x}{y}', C.bm_lathe([(0, 0.55), (0.42, 0.52), (0.5, 0.4), (0.5, 0.0), (0, 0.0)], axis='z', center=(x, y, gz0 + 0.4), segs=24), 'steel_black', smooth=40))
    g = C.merge('case_glass', parts)
    C.keep(g, pivot=(0.0, H / 2, gz0 + 0.2))

    # ------------------------------------------------------------------ ancres
    C.anchor('anchor_motherboard', L.mb_to_case(0, 0, 0))
    C.anchor('anchor_psu', L.PSU_CENTER)
    for i, p in enumerate(L.FAN_FRONT):
        C.anchor(f'anchor_fan_front_{i + 1}', p)
    C.anchor('anchor_fan_rear', L.FAN_REAR)
    C.anchor('anchor_grommet_low', (5.05, 21.5, L.TRAY_Z))
    C.anchor('anchor_grommet_high', (5.05, 34.5, L.TRAY_Z))
    C.anchor('anchor_grommet_eps', (-14.1, 46.0, L.TRAY_Z))
    C.anchor('anchor_shroud_cutout', (-1.0, L.SHROUD_TOP, L.TRAY_Z + 1.4))
    C.anchor('anchor_front_io', (19.4, H - 1.0, -HZ + 1.0))
    C.anchor('anchor_power_button', (ix, H + 0.32, -5.2))
    for k in range(7):
        C.anchor(f'anchor_slot_{k + 1}', (REAR + 0.1, s_k[k], 0.0))
    C.INFO['size_cm'] = [L.CASE_L, L.CASE_H, L.CASE_W]
    C.INFO['gpu_max_len_cm'] = round(FRONT_IN - 2.5 - REAR_IN, 1)
    C.INFO['cooler_max_h_cm'] = round(L.GLASS_Z - (L.MB_BACK_Z + L.COOLER_Z) - 0.3, 1)
    return dict(preview_view=(0.75, 0.55, 1.0), preview_fov=30)


if __name__ == '__main__':
    C.run(build, 'case')
