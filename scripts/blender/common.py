"""
common.py — Boîte à outils partagée par tous les scripts de modélisation Blender.

Lancement d'un script de pièce (deux façons équivalentes) :
    blender -b -P scripts/blender/model_fan.py
    python3 scripts/blender/model_fan.py          (si le module « bpy » est installé : pip install bpy)

CONVENTION DE COORDONNÉES (très importante pour comprendre les scripts)
-----------------------------------------------------------------------
On modélise directement dans l'« espace du site » (three.js), en CENTIMÈTRES :
    X = vers l'avant du boîtier (à droite quand on regarde la vitre)
    Y = vers le haut
    Z = vers la vitre latérale, donc vers la personne qui regarde
Chaque pièce est modélisée dans l'orientation qu'elle a une fois montée dans le PC
(la carte mère est verticale, le GPU est horizontal, etc.). Les ancres (empties)
n'ont donc besoin que d'une position.

Au moment de l'export, `finalize()` convertit tout en espace Blender (Z vers le haut,
mètres). L'exporteur glTF reconvertit en « Y vers le haut » : dans three.js on
retrouve exactement nos coordonnées, divisées par 100 (le glTF est en mètres).
Le site applique donc un facteur ×100 à tous les modèles au chargement.

Aucun objet ne porte de rotation : les rotations sont « cuites » dans les sommets.
Les objets à animer (rotor de ventilateur, levier du socket…) gardent leur ORIGINE
sur leur pivot, ce qui permet de les faire tourner simplement dans three.js.
"""
import bpy
import bmesh
import math
import os
import sys
import json
import time
import numpy as np
from mathutils import Vector, Matrix

# --------------------------------------------------------------------------
# Chemins
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
BUILD_DIR = os.path.join(ROOT, '.build')
RAW_DIR = os.path.join(BUILD_DIR, 'raw')            # .glb non compressés
PREVIEW_DIR = os.path.join(BUILD_DIR, 'previews')   # rendus PNG d'aperçu
TEX_DIR = os.path.join(BUILD_DIR, 'textures')       # textures générées
MANIFEST_DIR = os.path.join(BUILD_DIR, 'manifest')  # ancres et cotes (JSON)
for _d in (RAW_DIR, PREVIEW_DIR, TEX_DIR, MANIFEST_DIR):
    os.makedirs(_d, exist_ok=True)

BLENDER_DATAFILES = None
for _cand in [os.path.join(os.path.dirname(bpy.app.binary_path or ''), f'{bpy.app.version[0]}.{bpy.app.version[1]}', 'datafiles'),
              os.path.join(os.path.dirname(os.path.dirname(bpy.utils.resource_path('LOCAL'))), 'datafiles'),
              os.path.join(bpy.utils.resource_path('LOCAL'), 'datafiles')]:
    if os.path.isdir(_cand):
        BLENDER_DATAFILES = _cand
        break

# Registres remplis pendant la modélisation d'une pièce
KEEP = {}        # nom d'objet -> pivot (objets laissés séparés)
ANCHORS = {}     # nom d'ancre -> position (cm, espace site)
INFO = {}        # métadonnées libres pour le manifeste


def reset():
    """Repart d'une scène vide (appelé au début de chaque pièce)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()          # les matériaux de la pièce précédente n'existent plus
    KEEP.clear()
    ANCHORS.clear()
    INFO.clear()


def V(*a):
    if len(a) == 1:
        return Vector(a[0])
    return Vector(a)


# --------------------------------------------------------------------------
# Matériaux PBR (palette commune pour un style cohérent entre les pièces)
# Les couleurs sont en valeurs LINÉAIRES (convention glTF / Blender).
# --------------------------------------------------------------------------
PALETTE = {
    'pcb_black':     dict(color=(0.012, 0.014, 0.017), roughness=0.42),
    'pcb_green':     dict(color=(0.010, 0.085, 0.032), roughness=0.40),
    'gold':          dict(color=(0.95, 0.70, 0.30), metallic=1.0, roughness=0.24),
    'alu':           dict(color=(0.72, 0.73, 0.75), metallic=1.0, roughness=0.30),
    'alu_fin':       dict(color=(0.78, 0.79, 0.81), metallic=1.0, roughness=0.36),
    'alu_dark':      dict(color=(0.075, 0.080, 0.088), metallic=0.85, roughness=0.38),
    'alu_grey':      dict(color=(0.22, 0.23, 0.25), metallic=0.9, roughness=0.34),
    'nickel':        dict(color=(0.70, 0.70, 0.71), metallic=1.0, roughness=0.16),
    'copper':        dict(color=(0.93, 0.55, 0.38), metallic=1.0, roughness=0.24),
    'steel':         dict(color=(0.56, 0.57, 0.59), metallic=1.0, roughness=0.34),
    'steel_black':   dict(color=(0.016, 0.016, 0.018), metallic=0.45, roughness=0.42),
    'plastic_black': dict(color=(0.018, 0.018, 0.020), roughness=0.55),
    'plastic_dark':  dict(color=(0.040, 0.042, 0.046), roughness=0.50),
    'plastic_grey':  dict(color=(0.18, 0.18, 0.19), roughness=0.50),
    'plastic_white': dict(color=(0.70, 0.70, 0.70), roughness=0.50),
    'plastic_blue':  dict(color=(0.010, 0.090, 0.42), roughness=0.42),
    'plastic_red':   dict(color=(0.42, 0.015, 0.015), roughness=0.45),
    'plastic_yellow': dict(color=(0.75, 0.50, 0.02), roughness=0.45),
    'chip':          dict(color=(0.020, 0.020, 0.023), roughness=0.30),
    'silk':          dict(color=(0.78, 0.78, 0.78), roughness=0.60),
    'rubber':        dict(color=(0.025, 0.025, 0.025), roughness=0.85),
    'brass':         dict(color=(0.80, 0.56, 0.24), metallic=1.0, roughness=0.32),
    'ferrite':       dict(color=(0.070, 0.070, 0.075), roughness=0.65),
    'ceramic':       dict(color=(0.42, 0.30, 0.18), roughness=0.55),
    'solder':        dict(color=(0.70, 0.70, 0.72), metallic=1.0, roughness=0.30),
    'accent':        dict(color=(0.016, 0.651, 0.847), roughness=0.35),   # #22d3ee, couleur d'accent du site
    'glass':         dict(color=(0.045, 0.05, 0.058), roughness=0.05, alpha=0.24),   # verre trempé fumé
    'led':           dict(color=(0.03, 0.03, 0.03), roughness=0.3),
    'thermal':       dict(color=(0.45, 0.46, 0.48), roughness=0.75),
}
_MATS = {}


def mat(key, **override):
    """Renvoie (en le créant au besoin) le matériau de la palette nommé `key`."""
    if key in _MATS and not override:
        return _MATS[key]
    spec = dict(PALETTE.get(key, {}))
    spec.update(override)
    m = bpy.data.materials.new(key)
    _setup_principled(m, **spec)
    if not override:
        _MATS[key] = m
    return m


def _bsdf(m):
    if hasattr(m, 'use_nodes'):
        try:
            m.use_nodes = True
        except Exception:
            pass
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    if b is None:
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = nt.nodes.get('Material Output') or nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(b.outputs[0], out.inputs[0])
    return nt, b


def _setup_principled(m, color=(0.5, 0.5, 0.5), metallic=0.0, roughness=0.5, alpha=1.0,
                      emission=None, emission_strength=0.0):
    nt, b = _bsdf(m)
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = roughness
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'):
            m.surface_render_method = 'BLENDED'
        m.use_backface_culling = False
    if emission is not None:
        b.inputs['Emission Color'].default_value = (*emission, 1.0)
        b.inputs['Emission Strength'].default_value = emission_strength
    if alpha >= 1.0:
        m.use_backface_culling = True    # exporté en glTF « doubleSided: false »
    m.diffuse_color = (*color, alpha)
    m.metallic = metallic
    m.roughness = roughness


def textured_mat(name, image, metallic=0.0, roughness=0.5, mask=False, color_mult=None):
    """Matériau dont la couleur vient d'une image. `mask=True` : les zones à alpha=0
    deviennent des trous (glTF alphaMode MASK, idéal pour les grilles et le mesh)."""
    m = bpy.data.materials.new(name)
    nt, b = _bsdf(m)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Linear'
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = roughness
    m.use_backface_culling = not mask
    if mask:
        rnd = nt.nodes.new('ShaderNodeMath')
        rnd.operation = 'ROUND'          # l'exporteur glTF y reconnaît un alphaMode MASK (seuil 0,5)
        nt.links.new(tex.outputs['Alpha'], rnd.inputs[0])
        nt.links.new(rnd.outputs[0], b.inputs['Alpha'])
        if hasattr(m, 'surface_render_method'):
            m.surface_render_method = 'DITHERED'
        m.use_backface_culling = False
    return m


# --------------------------------------------------------------------------
# Textures procédurales (numpy) — dessinées en coordonnées pixel, origine en haut à gauche
# --------------------------------------------------------------------------
def srgb(hexstr, a=1.0):
    h = hexstr.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


class Canvas:
    """Petite toile RGBA anti-crénelée (distances signées) pour générer des textures."""

    def __init__(self, w, h, bg=(0, 0, 0, 1)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.float32)
        self.a[:] = bg

    def _region(self, x0, y0, x1, y1, pad=2):
        ix0 = max(int(math.floor(x0)) - pad, 0)
        iy0 = max(int(math.floor(y0)) - pad, 0)
        ix1 = min(int(math.ceil(x1)) + pad, self.w)
        iy1 = min(int(math.ceil(y1)) + pad, self.h)
        if ix1 <= ix0 or iy1 <= iy0:
            return None
        yy, xx = np.mgrid[iy0:iy1, ix0:ix1].astype(np.float32)
        return (slice(iy0, iy1), slice(ix0, ix1)), xx + 0.5, yy + 0.5

    def _paint(self, sl, cover, color):
        c = np.asarray(color, np.float32)
        al = np.clip(cover, 0, 1) * c[3]
        sub = self.a[sl]
        sub[..., :3] = sub[..., :3] * (1 - al[..., None]) + c[:3] * al[..., None]
        sub[..., 3] = sub[..., 3] * (1 - al) + al

    def cut(self, sl, cover):
        """Perce (alpha -> 0) proportionnellement à `cover`."""
        sub = self.a[sl]
        sub[..., 3] = sub[..., 3] * (1 - np.clip(cover, 0, 1))

    def rect(self, x0, y0, x1, y1, color, r=0.0, hole=False, stroke=None):
        reg = self._region(x0, y0, x1, y1)
        if reg is None:
            return
        sl, xx, yy = reg
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = abs(x1 - x0) / 2, abs(y1 - y0) / 2
        qx = np.abs(xx - cx) - (hx - r)
        qy = np.abs(yy - cy) - (hy - r)
        d = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r
        if stroke is not None:
            d = np.abs(d) - stroke / 2
        cover = np.clip(0.5 - d, 0, 1)
        if hole:
            self.cut(sl, cover)
        else:
            self._paint(sl, cover, color)

    def circle(self, cx, cy, rad, color, hole=False, stroke=None):
        reg = self._region(cx - rad, cy - rad, cx + rad, cy + rad)
        if reg is None:
            return
        sl, xx, yy = reg
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) - rad
        if stroke is not None:
            d = np.abs(d) - stroke / 2
        cover = np.clip(0.5 - d, 0, 1)
        if hole:
            self.cut(sl, cover)
        else:
            self._paint(sl, cover, color)

    def line(self, x0, y0, x1, y1, width, color):
        reg = self._region(min(x0, x1) - width, min(y0, y1) - width, max(x0, x1) + width, max(y0, y1) + width)
        if reg is None:
            return
        sl, xx, yy = reg
        px, py = xx - x0, yy - y0
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-6
        t = np.clip((px * dx + py * dy) / L2, 0, 1)
        d = np.sqrt((px - t * dx) ** 2 + (py - t * dy) ** 2) - width / 2
        self._paint(sl, np.clip(0.5 - d, 0, 1), color)

    def polygon(self, pts, color, hole=False):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        reg = self._region(min(xs), min(ys), max(xs), max(ys))
        if reg is None:
            return
        sl, xx, yy = reg
        inside = np.zeros(xx.shape, bool)
        n = len(pts)
        dmin = np.full(xx.shape, 1e9, np.float32)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            cond = ((ay > yy) != (by > yy))
            xint = (bx - ax) * (yy - ay) / ((by - ay) if by != ay else 1e-9) + ax
            inside ^= cond & (xx < xint)
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy or 1e-9
            t = np.clip(((xx - ax) * dx + (yy - ay) * dy) / L2, 0, 1)
            dmin = np.minimum(dmin, np.sqrt((xx - ax - t * dx) ** 2 + (yy - ay - t * dy) ** 2))
        d = np.where(inside, -dmin, dmin)
        cover = np.clip(0.5 - d, 0, 1)
        if hole:
            self.cut(sl, cover)
        else:
            self._paint(sl, cover, color)

    def noise(self, amount=0.03, seed=1):
        rng = np.random.default_rng(seed)
        n = rng.normal(0, amount, (self.h, self.w, 1)).astype(np.float32)
        self.a[..., :3] = np.clip(self.a[..., :3] + n, 0, 1)

    def save(self, name):
        """Écrit un PNG dans .build/textures et renvoie l'image Blender chargée."""
        path = os.path.join(TEX_DIR, name + '.png')
        img = bpy.data.images.new(name + '_gen', self.w, self.h, alpha=True)
        img.pixels.foreach_set(np.ascontiguousarray(self.a[::-1]).ravel())
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()
        bpy.data.images.remove(img)
        loaded = bpy.data.images.load(path, check_existing=False)
        loaded.name = name
        return loaded


# --------------------------------------------------------------------------
# Primitives bmesh (espace site, cm)
# --------------------------------------------------------------------------
def bm_box(sx, sy, sz, center=(0, 0, 0), bevel=0.0, segs=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        bv = min(bevel, sx / 2.05, sy / 2.05, sz / 2.05)
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=bv, offset_type='OFFSET',
                        segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return bm


def bm_box_minmax(x0, y0, z0, x1, y1, z1, bevel=0.0, segs=1):
    return bm_box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0),
                  center=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), bevel=bevel, segs=segs)


_AXIS_ROT = {
    'x': Matrix.Rotation(math.radians(90), 4, 'Y'),
    'y': Matrix.Rotation(math.radians(-90), 4, 'X'),
    'z': Matrix.Identity(4),
}


def bm_cylinder(r, depth, axis='z', center=(0, 0, 0), segs=32, r2=None, cap=True):
    """Cylindre (ou tronc de cône si r2) centré, d'axe x, y ou z."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segs,
                          radius1=r, radius2=(r if r2 is None else r2), depth=depth)
    bmesh.ops.transform(bm, matrix=_AXIS_ROT[axis], verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return bm


def bm_lathe(profile, axis='z', center=(0, 0, 0), segs=32, cap_start=True, cap_end=True):
    """Révolution d'un profil [(rayon, hauteur), ...] autour d'un axe."""
    bm = bmesh.new()
    rings = []
    for (r, h) in profile:
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), h)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((A[i], A[j], B[j], B[i]))
    if cap_start and profile[0][0] > 1e-6:
        bm.faces.new(list(reversed(rings[0])))
    if cap_end and profile[-1][0] > 1e-6:
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=_AXIS_ROT[axis], verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return bm


def bm_ring(r_out, r_in, depth, axis='z', center=(0, 0, 0), segs=48):
    """Anneau épais (tube court)."""
    bm = bmesh.new()
    h = depth / 2
    lo_o, hi_o, lo_i, hi_i = [], [], [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        c, s = math.cos(a), math.sin(a)
        lo_o.append(bm.verts.new((r_out * c, r_out * s, -h)))
        hi_o.append(bm.verts.new((r_out * c, r_out * s, h)))
        lo_i.append(bm.verts.new((r_in * c, r_in * s, -h)))
        hi_i.append(bm.verts.new((r_in * c, r_in * s, h)))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((lo_o[i], lo_o[j], hi_o[j], hi_o[i]))      # paroi extérieure
        bm.faces.new((hi_i[i], hi_i[j], lo_i[j], lo_i[i]))      # paroi intérieure
        bm.faces.new((hi_o[i], hi_o[j], hi_i[j], hi_i[i]))      # dessus
        bm.faces.new((lo_i[i], lo_i[j], lo_o[j], lo_o[i]))      # dessous
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=_AXIS_ROT[axis], verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return bm


def bm_prism(points, depth, axis='z', offset=0.0, bevel=0.0, segs=1):
    """Extrude un polygone 2D. points = [(u, v)] dans le plan perpendiculaire à `axis`
    (axis='z' : (x, y) ; axis='x' : (y, z) ; axis='y' : (x, z)).
    L'épaisseur va de `offset` à `offset + depth` le long de l'axe."""
    bm = bmesh.new()

    def P(u, v, w):
        if axis == 'z':
            return (u, v, w)
        if axis == 'x':
            return (w, u, v)
        return (u, w, v)   # axis == 'y'

    # sens trigonométrique pour des normales cohérentes
    area = 0.0
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % len(points)]
        area += x0 * y1 - x1 * y0
    pts = points if area > 0 else list(reversed(points))
    bottom = [bm.verts.new(P(u, v, offset)) for (u, v) in pts]
    top = [bm.verts.new(P(u, v, offset + depth)) for (u, v) in pts]
    n = len(pts)
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=bevel, offset_type='OFFSET',
                        segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    return bm


def rounded_rect_pts(w, h, r, segs=6, center=(0, 0)):
    cx, cy = center
    r = min(r, w / 2, h / 2)
    pts = []
    corners = [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)]
    for (ox, oy, a0) in corners:
        for k in range(segs + 1):
            a = math.radians(a0 + 90 * k / segs)
            pts.append((cx + ox + r * math.cos(a), cy + oy + r * math.sin(a)))
    return pts


def circle_pts(r, n=32, center=(0, 0), a0=0.0):
    return [(center[0] + r * math.cos(a0 + 2 * math.pi * i / n), center[1] + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def bm_transform(bm, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return bm


def bm_rotate(bm, deg, axis, pivot=(0, 0, 0)):
    pv = Vector(pivot)
    M = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(deg), 4, axis.upper()) @ Matrix.Translation(-pv)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm


def bm_translate(bm, vec):
    bmesh.ops.translate(bm, vec=Vector(vec), verts=bm.verts)
    return bm


def bm_join(*bms):
    """Fusionne plusieurs bmesh en un seul (pour un même objet)."""
    out = bmesh.new()
    tmp = bpy.data.meshes.new('_tmp_join')
    for b in bms:
        b.to_mesh(tmp)
        out.from_mesh(tmp)
        b.free()
    bpy.data.meshes.remove(tmp)
    return out


def uv_project(bm, axis='z', rect=None, faces=None, flip_u=False, flip_v=False, axes=None):
    """Projection UV planaire : rect=(u0, v0, u1, v1) en coordonnées du plan (cm).
    axis='z' : (x, y) ; axis='x' : (z, y) ; axis='y' : (x, z).
    axes=('y', 'z') force explicitement les coordonnées utilisées pour (u, v)."""
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    faces = faces if faces is not None else bm.faces
    if axes is not None:
        ia, ib = 'xyz'.index(axes[0]), 'xyz'.index(axes[1])
        _pl = lambda co: (co[ia], co[ib])  # noqa: E731
    else:
        _pl = lambda co: _plane(co, axis)  # noqa: E731
    if rect is None:
        xs, ys = [], []
        for f in faces:
            for l in f.loops:
                a, b = _pl(l.vert.co)
                xs.append(a)
                ys.append(b)
        rect = (min(xs), min(ys), max(xs), max(ys))
    u0, v0, u1, v1 = rect
    for f in faces:
        for l in f.loops:
            a, b = _pl(l.vert.co)
            u = (a - u0) / ((u1 - u0) or 1)
            v = (b - v0) / ((v1 - v0) or 1)
            l[uv].uv = (1 - u if flip_u else u, 1 - v if flip_v else v)
    return bm


def _plane(co, axis):
    if axis == 'z':
        return co.x, co.y
    if axis == 'x':
        return co.z, co.y
    return co.x, co.z


def uv_constant(bm, u=0.0, v=0.0, faces=None):
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for f in (faces if faces is not None else bm.faces):
        for l in f.loops:
            l[uv].uv = (u, v)
    return bm


def faces_facing(bm, direction, tol=0.9):
    d = Vector(direction).normalized()
    bm.normal_update()
    return [f for f in bm.faces if f.normal.dot(d) > tol]


def auto_smooth(bm, angle=35.0):
    """Lissage avec arêtes vives au-delà de `angle` degrés (équivalent « Auto Smooth »)."""
    bm.normal_update()
    lim = math.cos(math.radians(angle))
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) != 2:
            e.smooth = False
        else:
            e.smooth = e.link_faces[0].normal.dot(e.link_faces[1].normal) > lim
    return bm


# --------------------------------------------------------------------------
# Création d'objets
# --------------------------------------------------------------------------
def add(name, bm, material, location=(0, 0, 0), smooth=None, face_mats=None):
    """Crée un objet maillé. `material` : clé de palette, matériau, ou liste de matériaux
    (avec `face_mats(bm)` qui affecte les index). `smooth` : angle d'auto-lissage ou None (facettes)."""
    if smooth is not None:
        auto_smooth(bm, smooth)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    mats = material if isinstance(material, (list, tuple)) else [material]
    for m in mats:
        if m is None:
            continue
        me.materials.append(mat(m) if isinstance(m, str) else m)
    obj.location = Vector(location)
    return obj


def keep(obj, pivot=None, spin=None, extras=None):
    """Garde l'objet séparé à l'export (pour l'animer ou le masquer dans le site).
    pivot : nouvelle origine (cm). spin : axe de rotation continue ('x', 'y' ou 'z')."""
    if pivot is not None:
        set_origin(obj, pivot)
    KEEP[obj.name] = list(obj.location)
    if spin:
        obj['spinAxis'] = spin
    if extras:
        for k, v in extras.items():
            obj[k] = v
    return obj


def set_origin(obj, pivot):
    pivot = Vector(pivot)
    delta = pivot - obj.location
    obj.data.transform(Matrix.Translation(-delta))
    obj.location = pivot


def anchor(name, pos):
    """Ancre = empty nommé exporté dans le glTF (lu par le site pour placer les pièces)."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 1.0
    e.location = Vector(pos)
    bpy.context.scene.collection.objects.link(e)
    ANCHORS[name] = [round(float(c), 4) for c in pos]
    return e


def merge(name, objs, origin=(0, 0, 0)):
    """Fusionne des objets (multi-matériaux) en un seul, origine = `origin`."""
    mats = []
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        local = [s.material for s in o.material_slots] or [None]
        mapping = []
        for m in local:
            if m not in mats:
                mats.append(m)
            mapping.append(mats.index(m))
        n = len(me.polygons)
        if n:
            idx = np.zeros(n, np.int32)
            me.polygons.foreach_get('material_index', idx)
            idx = np.array(mapping, np.int32)[np.clip(idx, 0, len(mapping) - 1)]
            me.polygons.foreach_set('material_index', idx)
        me.transform(Matrix.Translation(Vector(o.location) - Vector(origin)))
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    out = bpy.data.meshes.new(name)
    bm.to_mesh(out)
    bm.free()
    for m in mats:
        out.materials.append(m)
    for o in objs:
        old = o.data
        bpy.data.objects.remove(o)
        if old.users == 0:
            bpy.data.meshes.remove(old)
    ob = bpy.data.objects.new(name, out)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(origin)
    return ob


def instance(src, name, location):
    """Copie (données partagées) d'un objet à une autre position."""
    o = bpy.data.objects.new(name, src.data)
    o.location = Vector(location)
    bpy.context.scene.collection.objects.link(o)
    return o


def cut(target, *cutters, solver='EXACT'):
    """Booléen DIFFÉRENCE immédiat : target -= cutters (bmesh dans le même repère que target.location=0)."""
    cbm = bm_join(*cutters) if len(cutters) > 1 else cutters[0]
    cme = bpy.data.meshes.new('_cutter')
    cbm.to_mesh(cme)
    cbm.free()
    cob = bpy.data.objects.new('_cutter', cme)
    bpy.context.scene.collection.objects.link(cob)
    cob.location = target.location
    mod = target.modifiers.new('cut', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = solver
    mod.object = cob
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    old = target.data
    target.modifiers.clear()
    target.data = new
    new.name = target.name
    bpy.data.objects.remove(cob)
    bpy.data.meshes.remove(cme)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return target


def resmooth(obj, angle=35.0):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    auto_smooth(bm, angle)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def tube(name, points, radius, material, bevel_res=3, smooth=60.0, caps=True):
    """Tube le long d'une polyligne (points cm). Les coudes doivent être pré-arrondis."""
    cu = bpy.data.curves.new(name + '_crv', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = caps
    sp = cu.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
    ob = bpy.data.objects.new(name + '_crv', cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return add(name, bm, material, smooth=smooth)


def arc_path(p0, p1, center, n=12):
    """Points d'un arc de cercle de p0 à p1 autour de `center` (même rayon)."""
    c = Vector(center)
    a = Vector(p0) - c
    b = Vector(p1) - c
    r = a.length
    axis = a.cross(b)
    if axis.length < 1e-9:
        return [Vector(p0), Vector(p1)]
    axis.normalize()
    ang = a.angle(b)
    pts = []
    for i in range(n + 1):
        q = Matrix.Rotation(ang * i / n, 3, axis) @ a
        pts.append(c + q.normalized() * r)
    return pts


def fillet_path(pts, radius, n=8):
    """Arrondit les angles d'une polyligne (coudes de caloducs, câbles...)."""
    P = [Vector(p) for p in pts]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        A, B, Q = P[i - 1], P[i + 1], P[i]
        u = (A - Q)
        v = (B - Q)
        if u.length < 1e-9 or v.length < 1e-9:
            continue
        u.normalize()
        v.normalize()
        ang = u.angle(v)
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(Q)
            continue
        d = radius / math.tan(ang / 2)
        d = min(d, (A - Q).length * 0.49, (B - Q).length * 0.49)
        rr = d * math.tan(ang / 2)
        t1 = Q + u * d
        t2 = Q + v * d
        c = Q + (u + v).normalized() * (rr / math.sin(ang / 2))
        out.extend(arc_path(t1, t2, c, n))
    out.append(P[-1])
    return [tuple(p) for p in out]


def text(name, body, size, location, material, rot=None, align='CENTER', extrude=0.0, valign='CENTER'):
    """Texte maillé (plan XY, face vers +Z). `rot` : liste de (degrés, axe) appliqués dans l'ordre."""
    cu = bpy.data.curves.new(name + '_txt', 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = valign
    cu.extrude = extrude
    cu.resolution_u = 3
    ob = bpy.data.objects.new(name + '_txt', cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    for (deg, axis) in (rot or []):
        bm_rotate(bm, deg, axis)
    return add(name, bm, material, location=location)


# --------------------------------------------------------------------------
# Finalisation : fusion, conversion, export, aperçu, manifeste
# --------------------------------------------------------------------------
TO_BLENDER = Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Scale(0.01, 4)


def _mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def _tri_count(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


def finalize(model, preview_view=(1.0, 0.7, 1.4), preview_target=None, preview_fov=30.0,
             render=True, samples=40, resolution=(1000, 750), extra=None, preview_up=None, preview_name=None,
             preview_radius=None):
    t0 = time.time()
    # 1) Applique les éventuels modificateurs restants
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for o in _mesh_objects():
        if o.modifiers:
            new = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            o.modifiers.clear()
            o.data = new

    # 2) Boîte englobante (espace site, cm) et fusion des objets non gardés
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for o in _mesh_objects():
        for v in o.data.vertices:
            p = v.co + o.location
            mins = Vector((min(mins.x, p.x), min(mins.y, p.y), min(mins.z, p.z)))
            maxs = Vector((max(maxs.x, p.x), max(maxs.y, p.y), max(maxs.z, p.z)))
    body = [o for o in _mesh_objects() if o.name not in KEEP]
    if body:
        merge(model + '_body', body)

    # pivots finaux des objets gardés
    keep_info = {}
    for name in list(KEEP.keys()):
        o = bpy.data.objects.get(name)
        if o is None:
            continue
        vs = [v.co + o.location for v in o.data.vertices] if o.type == 'MESH' else [Vector(o.location)]
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        keep_info[name] = dict(pivot=[round(c, 4) for c in o.location],
                               spin=o.get('spinAxis'),
                               center=[round(c, 3) for c in (lo + hi) / 2],
                               size=[round(c, 3) for c in (hi - lo)])

    objs = _mesh_objects()
    tris = _tri_count(objs)

    # 3) Conversion espace site (cm, Y haut) -> Blender (m, Z haut)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.data.transform(TO_BLENDER)
        o.location = TO_BLENDER @ Vector(o.location)

    # 4) Export glTF binaire
    path = os.path.join(RAW_DIR, model + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False,
                              export_apply=True, export_yup=True, export_extras=True,
                              export_animations=False, export_cameras=False, export_lights=False,
                              export_texcoords=True, export_normals=True, export_tangents=False,
                              export_vertex_color='NONE', export_image_format='AUTO')
    size_kb = os.path.getsize(path) / 1024

    # 5) Manifeste (lu par le site pour les modèles de secours)
    manifest = dict(model=model, bbox_min=[round(c, 3) for c in mins], bbox_max=[round(c, 3) for c in maxs],
                    anchors=dict(ANCHORS), keep=keep_info, triangles=tris, info=dict(INFO))
    if extra:
        manifest.update(extra)
    with open(os.path.join(MANIFEST_DIR, model + '.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print(f'[{model}] export {size_kb:.0f} Ko, {tris} triangles, {len(ANCHORS)} ancres, '
          f'{len(keep_info)} objets animables ({time.time() - t0:.1f}s)')

    # 6) Rendu d'aperçu
    if render:
        render_preview(preview_name or model, mins, maxs, preview_view, preview_target, preview_fov, samples, resolution,
                       preview_up, preview_radius)
    return manifest


def _site_to_blender_dir(v):
    v = Vector(v)
    return Vector((v.x, -v.z, v.y))


def render_preview(model, mins, maxs, view=(1.0, 0.7, 1.4), target=None, fov=30.0, samples=40,
                   resolution=(1000, 750), up=None, radius=None):
    sc = bpy.context.scene
    center_site = (mins + maxs) / 2 if target is None else Vector(target)
    radius = (maxs - mins).length / 2 if radius is None else radius
    center = TO_BLENDER @ center_site
    rad_m = radius * 0.01
    cam_data = bpy.data.cameras.new('preview_cam')
    cam_data.lens_unit = 'FOV'
    cam_data.angle = math.radians(fov)
    cam_data.clip_start = 0.001
    cam_data.clip_end = 100
    cam = bpy.data.objects.new('preview_cam', cam_data)
    sc.collection.objects.link(cam)
    d = _site_to_blender_dir(view).normalized()
    aspect = resolution[0] / resolution[1]
    half = math.radians(fov) / 2
    if aspect < 1:
        half = math.atan(math.tan(half) * aspect)
    dist = rad_m / math.sin(half) * 1.04
    cam.location = center + d * dist
    upv = _site_to_blender_dir(up) if up else Vector((0, 0, 1))
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y' if upv.z > 0.5 else 'Z').to_euler()
    if up:
        # oriente le haut de l'image selon `up`
        fwd = (center - cam.location).normalized()
        right = fwd.cross(upv).normalized()
        true_up = right.cross(fwd).normalized()
        rot = Matrix((right, true_up, -fwd)).transposed()
        cam.rotation_euler = rot.to_euler()
    sc.camera = cam

    world = bpy.data.worlds.new('preview_world')
    sc.world = world
    if hasattr(world, 'use_nodes'):
        world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get('Background')
    hdr = None
    if BLENDER_DATAFILES:
        cand = os.path.join(BLENDER_DATAFILES, 'studiolights', 'world', 'interior.exr')
        if os.path.exists(cand):
            hdr = cand
    if hdr:
        env = nt.nodes.new('ShaderNodeTexEnvironment')
        env.image = bpy.data.images.load(hdr)
        nt.links.new(env.outputs['Color'], bg.inputs['Color'])
        bg.inputs['Strength'].default_value = 0.45
    else:
        bg.inputs['Color'].default_value = (0.3, 0.32, 0.35, 1)
    # lumière principale douce (en haut à gauche, côté caméra)
    ld = bpy.data.lights.new('key', 'AREA')
    ld.size = rad_m * 3
    # puissance choisie pour ~3 W/m² d'éclairement sur l'objet (exposition « normale »)
    ld.energy = 3.0 * math.pi * (dist * 1.1) ** 2
    lo = bpy.data.objects.new('key', ld)
    sc.collection.objects.link(lo)
    kdir = _site_to_blender_dir((-0.6, 1.2, 1.0)).normalized()
    lo.location = center + kdir * dist * 1.1
    lo.rotation_euler = (center - lo.location).to_track_quat('-Z', 'Y').to_euler()
    rd = bpy.data.lights.new('rim', 'AREA')
    rd.size = rad_m * 2
    rd.energy = 1.6 * math.pi * dist ** 2
    ro = bpy.data.objects.new('rim', rd)
    sc.collection.objects.link(ro)
    rdir = _site_to_blender_dir((0.8, 0.6, -1.0)).normalized()
    ro.location = center + rdir * dist
    ro.rotation_euler = (center - ro.location).to_track_quat('-Z', 'Y').to_euler()

    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = resolution
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    try:
        sc.view_settings.view_transform = 'AgX'
    except Exception:
        pass
    sc.render.filepath = os.path.join(PREVIEW_DIR, model + '.png')
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f'[{model}] aperçu rendu en {time.time() - t:.1f}s -> {sc.render.filepath}')


def run(build_fn, model, **finalize_kwargs):
    """Point d'entrée commun : scène vide -> build() -> finalize()."""
    reset()
    kw = build_fn() or {}
    kw.update(finalize_kwargs)
    if '--no-render' in sys.argv:
        kw['render'] = False
    if '--quick' in sys.argv:          # aperçu rapide pendant la mise au point
        kw['samples'] = 12
        kw['resolution'] = (700, 525)
    if '--view' in sys.argv:           # point de vue de contrôle : --view x,y,z (espace site)
        kw['preview_view'] = tuple(float(c) for c in sys.argv[sys.argv.index('--view') + 1].split(','))
        kw['preview_name'] = model + '_alt'
    if '--target' in sys.argv:         # zoom de contrôle : --target x,y,z --radius r (cm)
        kw['preview_target'] = tuple(float(c) for c in sys.argv[sys.argv.index('--target') + 1].split(','))
        kw['preview_radius'] = float(sys.argv[sys.argv.index('--radius') + 1])
        kw['preview_name'] = model + '_zoom'
    return finalize(model, **kw)
