"""
build_all.py — Génère TOUS les modèles d'un coup (et leurs aperçus PNG).

    blender -b -P scripts/blender/build_all.py                 # tous les modèles + aperçus
    blender -b -P scripts/blender/build_all.py -- --no-render  # sans les rendus (rapide)
    python3 scripts/blender/build_all.py --no-render           # variante avec le module bpy

Ensuite : `npm run optimize` (compression gltf-transform -> dossier models/).
"""
import importlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401

import common as C  # noqa: E402

MODELS = ['fan', 'cpu', 'motherboard', 'ram', 'ssd', 'cooler', 'gpu', 'psu', 'case']


def main():
    only = [a for a in sys.argv if a in MODELS]
    t0 = time.time()
    for name in (only or MODELS):
        mod = importlib.import_module('model_' + name)
        C.run(mod.build, name)
    print(f'Terminé : {len(only or MODELS)} modèles en {time.time() - t0:.0f} s')


if __name__ == '__main__':
    main()
