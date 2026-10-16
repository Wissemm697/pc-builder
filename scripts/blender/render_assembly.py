"""
render_assembly.py — Assemble le PC complet à partir des .glb et de leurs ancres,
puis en fait un rendu. Sert à VÉRIFIER que les pièces s'emboîtent (mêmes règles de
placement que le site) et produit l'image d'attente du héros (img/hero-poster.webp).

    blender -b -P scripts/blender/render_assembly.py
    blender -b -P scripts/blender/render_assembly.py -- --no-glass --view 0.2,0.25,1
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import common as C  # noqa: E402


def manifest(name):
    with open(os.path.join(C.MANIFEST_DIR, name + '.json'), encoding='utf-8') as f:
        return json.load(f)


def site_to_blender(p):
    return Vector((p[0], -p[2], p[1])) * 0.01


def import_model(name, offset_site, hide=()):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(C.RAW_DIR, name + '.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    off = site_to_blender(offset_site)
    for o in roots:
        o.location = o.location + off
    for o in new:
        if o.type == 'EMPTY':
            o.hide_render = True
        if o.name.split('.')[0] in hide:
            o.hide_render = True
    return new


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    case = manifest('case')
    mb = manifest('motherboard')
    A = case['anchors']
    B = mb['anchors']
    mbo = A['anchor_motherboard']

    def on_mb(key):
        return [mbo[i] + B[key][i] for i in range(3)]

    hide_case = ['slot_cover_2', 'slot_cover_3']
    if '--no-glass' in argv:
        hide_case.append('case_glass')
    import_model('case', (0, 0, 0), hide=hide_case)
    import_model('motherboard', mbo)
    import_model('cpu', on_mb('anchor_cpu'))
    import_model('cooler', on_mb('anchor_cooler'))
    import_model('ram', on_mb('anchor_ram_A2'))
    import_model('ram', on_mb('anchor_ram_B2'))
    import_model('ssd', on_mb('anchor_m2_1'))
    import_model('gpu', on_mb('anchor_pcie_x16'))
    import_model('psu', A['anchor_psu'], hide=['psu_fixed_cables'])
    for k in ('anchor_fan_front_1', 'anchor_fan_front_2', 'anchor_fan_front_3', 'anchor_fan_rear'):
        import_model('fan', A[k])

    view = (0.55, 0.32, 1.0)
    if '--view' in argv:
        view = tuple(float(c) for c in argv[argv.index('--view') + 1].split(','))
    name = 'assembly' + ('_noglass' if '--no-glass' in argv else '')
    mins = Vector(case['bbox_min'])
    maxs = Vector(case['bbox_max'])
    samples = 12 if '--quick' in argv else 64
    res = (800, 600) if '--quick' in argv else (1400, 1050)
    C.render_preview(name, mins, maxs, view=view, fov=28, samples=samples, resolution=res)


if __name__ == '__main__':
    main()
