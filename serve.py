#!/usr/bin/env python3
"""
serve.py : lance le site en local, sans rien installer (Python 3.8 ou plus récent).

    python serve.py            ->  http://localhost:8000  (le navigateur s'ouvre tout seul)
    python serve.py 8080       ->  autre port
    python serve.py --lan      ->  accessible aussi depuis un téléphone sur le même Wi-Fi
    python serve.py --no-open  ->  sans ouvrir le navigateur

Pourquoi un serveur ? Le site charge des modules JavaScript et des fichiers .glb :
pour des raisons de sécurité, les navigateurs refusent de le faire depuis un fichier
ouvert par double-clic (adresse file://). Il faut donc passer par http://.

Ce serveur fixe lui-même les types MIME (.js, .glb, .webp…) : sous Windows, le
serveur Python de base les lit dans le registre, qui est parfois faux (.js servi en
« text/plain »), ce qui empêche le site de démarrer.
"""
import functools
import http.server
import os
import socket
import sys
import threading
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))

TYPES = {
    '': 'application/octet-stream',
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.mjs': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.md': 'text/markdown; charset=utf-8',
    '.txt': 'text/plain; charset=utf-8',
    '.glb': 'model/gltf-binary',
    '.gltf': 'model/gltf+json',
    '.bin': 'application/octet-stream',
    '.webp': 'image/webp',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.wasm': 'application/wasm',
}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **TYPES}

    def end_headers(self):
        # pas de cache : une modification des fichiers est visible au simple rechargement
        self.send_header('Cache-Control', 'no-cache')
        # en-têtes de sécurité (la politique de contenu complète est dans chaque page HTML)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "frame-ancestors 'none'")
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=(), usb=()')
        super().end_headers()

    def log_message(self, fmt, *args):
        # on n'affiche que les erreurs (404, 500…), pas chaque fichier servi
        if len(args) > 1 and str(args[1])[:1] in ('4', '5'):
            sys.stderr.write('  [%s] %s\n' % (args[1], args[0]))


def local_ip():
    """Adresse de l'ordinateur sur le réseau local (pour l'ouvrir depuis un téléphone)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))  # aucune donnée envoyée : sert juste à choisir l'interface
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


def main():
    args = sys.argv[1:]
    lan = '--lan' in args
    open_browser = '--no-open' not in args
    ports = [a for a in args if a.isdigit()]
    port = int(ports[0]) if ports else 8000
    host = '0.0.0.0' if lan else '127.0.0.1'
    handler = functools.partial(Handler, directory=ROOT)

    httpd = None
    for p in range(port, port + 10):          # si le port est pris, on essaie les suivants
        try:
            httpd = http.server.ThreadingHTTPServer((host, p), handler)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        sys.exit(f'Impossible d\'ouvrir un port entre {port} et {port + 9}.')

    url = f'http://localhost:{port}/'
    print(f'\n  Site lancé : {url}')
    if lan:
        print(f'  Depuis un téléphone (même Wi-Fi) : http://{local_ip()}:{port}/')
    print('  Ctrl+C pour arrêter.\n')
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n  Serveur arrêté.')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
