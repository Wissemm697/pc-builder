#!/usr/bin/env python3
"""
update-csp.py : met à jour la politique de sécurité (Content-Security-Policy) des pages.

La seule balise <script> écrite directement dans le HTML est l'« importmap » (la table qui
dit au navigateur où trouver three.js). La politique de sécurité n'autorise que ce script-là,
grâce à son empreinte SHA-256. Si tu modifies l'importmap d'une page, relance :

    python scripts/update-csp.py

Le script recalcule l'empreinte de chaque page (index.html, en/index.html…) et réécrit la
balise <meta http-equiv="Content-Security-Policy">.
"""
import base64
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = [ROOT / 'index.html'] + sorted(ROOT.glob('*/index.html'))

# Ce que la page a le droit de charger : uniquement ses propres fichiers.
#  - 'wasm-unsafe-eval' : le décodeur des modèles 3D (meshopt) est un petit module WebAssembly
#  - blob: / data:      : les textures sont extraites des fichiers .glb en mémoire
POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'wasm-unsafe-eval' {hash}; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "connect-src 'self' data: blob:; "
    "font-src 'self'; "
    "worker-src 'self' blob:; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)

IMPORTMAP = re.compile(r'<script type="importmap">(.*?)</script>', re.S)
META = re.compile(r'(<meta http-equiv="Content-Security-Policy" content=")[^"]*(">)')


def main():
    for page in PAGES:
        html = page.read_text(encoding='utf-8')
        m = IMPORTMAP.search(html)
        if not m:
            print(f'{page.relative_to(ROOT)} : pas d\'importmap, page ignorée')
            continue
        digest = base64.b64encode(hashlib.sha256(m.group(1).encode('utf-8')).digest()).decode()
        policy = POLICY.format(hash=f"'sha256-{digest}'")
        new, n = META.subn(lambda mm: mm.group(1) + policy + mm.group(2), html)
        if n != 1:
            raise SystemExit(f'{page.relative_to(ROOT)} : balise CSP introuvable')
        if new != html:
            page.write_text(new, encoding='utf-8')
        print(f'{page.relative_to(ROOT)} : sha256-{digest}')


if __name__ == '__main__':
    main()
