/**
 * fallbacks.js : Modèles de SECOURS construits directement en Three.js.
 *
 * Utilisés uniquement si un fichier .glb ne peut pas être chargé (fichier absent,
 * serveur mal configuré…). Ils sont simplifiés mais respectent les mêmes dimensions,
 * les mêmes ancres et les mêmes noms de pièces animables que les vrais modèles
 * (données lues dans js/data/manifest.js) : toutes les vues continuent de fonctionner.
 * Unité : le centimètre (pas de facteur ×100 à appliquer).
 */
import * as THREE from 'three';
import { MANIFEST } from '../data/manifest.js';

const M = {
  pcbBlack: new THREE.MeshStandardMaterial({ color: 0x0b0d10, roughness: 0.5 }),
  pcbGreen: new THREE.MeshStandardMaterial({ color: 0x12391f, roughness: 0.45 }),
  black: new THREE.MeshStandardMaterial({ color: 0x15171a, roughness: 0.6 }),
  dark: new THREE.MeshStandardMaterial({ color: 0x24282d, roughness: 0.5 }),
  grey: new THREE.MeshStandardMaterial({ color: 0x5b6470, roughness: 0.5 }),
  alu: new THREE.MeshStandardMaterial({ color: 0xc9ccd1, metalness: 1, roughness: 0.35 }),
  steel: new THREE.MeshStandardMaterial({ color: 0x9aa0a8, metalness: 1, roughness: 0.4 }),
  gold: new THREE.MeshStandardMaterial({ color: 0xd9b25b, metalness: 1, roughness: 0.3 }),
  brass: new THREE.MeshStandardMaterial({ color: 0xc9953f, metalness: 1, roughness: 0.35 }),
  chip: new THREE.MeshStandardMaterial({ color: 0x0f1012, roughness: 0.35 }),
  accent: new THREE.MeshStandardMaterial({ color: 0x22d3ee, roughness: 0.4 }),
  label: new THREE.MeshStandardMaterial({ color: 0xd8dbe0, roughness: 0.6 }),
  glass: new THREE.MeshStandardMaterial({ name: 'glass', color: 0x0d1116, roughness: 0.05, transparent: true, opacity: 0.2 }),
  led: new THREE.MeshStandardMaterial({ name: 'led', color: 0x111111, roughness: 0.3 }),
};

/** Boîte définie par ses coins min/max (cm). */
function box(parent, x0, y0, z0, x1, y1, z1, mat, name) {
  const g = new THREE.BoxGeometry(Math.abs(x1 - x0), Math.abs(y1 - y0), Math.abs(z1 - z0));
  const m = new THREE.Mesh(g, mat);
  m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
  if (name) m.name = name;
  parent.add(m);
  return m;
}

/** Cylindre d'axe 'x', 'y' ou 'z'. */
function cyl(parent, r, h, axis, c, mat, name, seg = 24) {
  const g = new THREE.CylinderGeometry(r, r, h, seg);
  if (axis === 'x') g.rotateZ(Math.PI / 2);
  if (axis === 'z') g.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(g, mat);
  m.position.set(c[0], c[1], c[2]);
  if (name) m.name = name;
  parent.add(m);
  return m;
}

/** Objet animable : un groupe nommé placé sur le pivot indiqué dans le manifeste. */
function keepGroup(parent, model, name) {
  const g = new THREE.Group();
  g.name = name;
  const info = MANIFEST[model]?.keep?.[name];
  if (info) g.position.fromArray(info.pivot);
  parent.add(g);
  return g;
}

/** Objet animable générique : une boîte aux dimensions et à la position notées dans le manifeste. */
function keepBox(parent, model, name, mat) {
  const g = keepGroup(parent, model, name);
  const info = MANIFEST[model]?.keep?.[name];
  if (info && info.center && info.size) {
    const c = new THREE.Vector3().fromArray(info.center).sub(g.position);
    const s = info.size.map((v) => Math.max(v, 0.02));
    box(g, c.x - s[0] / 2, c.y - s[1] / 2, c.z - s[2] / 2, c.x + s[0] / 2, c.y + s[1] / 2, c.z + s[2] / 2, mat);
  }
  return g;
}

/** Ajoute les ancres du manifeste (empties). */
function anchors(root, model) {
  const a = MANIFEST[model]?.anchors || {};
  for (const [name, p] of Object.entries(a)) {
    const o = new THREE.Object3D();
    o.name = name;
    o.position.fromArray(p);
    root.add(o);
  }
}

function fanRotor(parent, name, axis, r = 5.6) {
  // pales simplifiées autour de l'axe X, puis réorientées si besoin
  const rotor = new THREE.Group();
  const hub = cyl(rotor, r * 0.35, 1.8, 'x', [0, 0, 0], M.dark);
  hub.name = `${name}_hub`;
  for (let i = 0; i < 7; i++) {
    const blade = new THREE.Mesh(new THREE.BoxGeometry(0.15, r * 0.62, r * 0.36), M.dark);
    blade.position.set(0, r * 0.66, 0);
    blade.rotation.y = 0.5;
    const holder = new THREE.Group();
    holder.rotation.x = (i / 7) * Math.PI * 2;
    holder.add(blade);
    rotor.add(holder);
  }
  if (axis === 'y') rotor.rotation.z = -Math.PI / 2;
  parent.add(rotor);
  return rotor;
}

const BUILDERS = {
  fan(root) {
    const frame = new THREE.Mesh(new THREE.TorusGeometry(6.0, 0.3, 8, 48), M.black);
    frame.rotation.y = Math.PI / 2;
    root.add(frame);
    box(root, -1.25, -6, -6, 1.25, -5.6, 6, M.black);
    box(root, -1.25, 5.6, -6, 1.25, 6, 6, M.black);
    box(root, -1.25, -6, -6, 1.25, 6, -5.6, M.black);
    box(root, -1.25, -6, 5.6, 1.25, 6, 6, M.black);
    const k = keepGroup(root, 'fan', 'fan_rotor');
    k.userData.spinAxis = 'x';
    fanRotor(k, 'fan_rotor', 'x');
  },
  cpu(root) {
    box(root, -2, -2, 0, 2, 2, 0.12, M.pcbGreen);
    box(root, -1.86, -1.86, 0.12, 1.86, 1.86, 0.5, M.alu);
  },
  motherboard(root) {
    box(root, -12.2, -15.25, 0, 12.2, 15.25, 0.16, M.pcbBlack);
    box(root, -5.8, 3.95, 0.16, -1.2, 8.55, 0.53, M.black);
    box(root, -9.3, -0.4, 0.16, -7.0, 10.0, 2.86, M.grey);
    box(root, -9.3, 10.9, 0.16, -0.6, 13.15, 2.66, M.grey);
    box(root, -12.2, 4.6, 0.16, -9.3, 13.35, 4.2, M.black);
    for (const x of [3.7, 4.5, 5.3, 6.1]) box(root, x - 0.31, -2.1, 0.16, x + 0.31, 12.1, 0.91, M.dark);
    box(root, -10.6, -4.96, 0.16, -1.7, -4.2, 1.26, M.steel);
    box(root, 3.0, -12.2, 0.16, 8.6, -6.4, 1.06, M.grey);
    box(root, 10.6, 3.4, 0.16, 11.6, 8.8, 1.16, M.black);
    for (const name of Object.keys(MANIFEST.motherboard?.keep || {})) {
      keepBox(root, 'motherboard', name, name === 'debug_leds' ? M.led : M.steel);
    }
  },
  ram(root) {
    box(root, -0.064, -6.67, 0, 0.064, 6.67, 3.125, M.pcbGreen);
    box(root, -0.07, -6.4, 0, 0.07, 6.4, 0.32, M.gold);
    for (const y of [-5.45, -4.1, -2.75, -1.4, 1.4, 2.75, 4.1, 5.45]) box(root, 0.064, y - 0.5, 1.15, 0.164, y + 0.5, 2.35, M.chip);
  },
  ssd(root) {
    box(root, 0, -1.1, 0, 8, 1.1, 0.08, M.pcbBlack);
    box(root, 0, -1.05, 0, 0.4, 1.05, 0.085, M.gold);
    box(root, 1.0, -0.62, 0.08, 2.24, 0.62, 0.2, M.chip);
    box(root, 2.42, -1.02, 0.2, 7.1, 1.02, 0.215, M.label);
  },
  cooler(root) {
    box(root, -2, -2, 0, 2, 2, 1.25, M.alu);
    box(root, -2.25, -6.25, 3.5, 2.25, 6.25, 15.0, M.alu);
    for (const s of [-1.35, -0.45, 0.45, 1.35]) cyl(root, 0.3, 14, 'z', [s, 0, 8], M.steel, null, 12);
    box(root, 2.25, -6, 3.5, 4.75, 6, 15.5, M.black);
    const k = keepGroup(root, 'cooler', 'cooler_fan_rotor');
    k.userData.spinAxis = 'x';
    fanRotor(k, 'cooler_fan_rotor', 'x');
    k.children[0].position.x = 0.3;
  },
  gpu(root) {
    box(root, -7.0, -0.08, 0.85, 15, 0.08, 11.1, M.pcbBlack);
    box(root, -4.45, -0.09, 0, 4.45, 0.09, 0.85, M.gold);
    box(root, -6.9, -4.4, 1.2, 20.95, -2.9, 12.4, M.black);
    box(root, -6.9, 0.2, 0.95, 20.95, 0.45, 12.4, M.grey);
    box(root, -7.15, -3.7, -1, -7.05, 0.36, 12, M.steel);
    for (const n of ['gpu_fan_rotor_1', 'gpu_fan_rotor_2']) {
      const k = keepGroup(root, 'gpu', n);
      k.userData.spinAxis = 'y';
      k.userData.spinDir = -1;
      fanRotor(k, n, 'y', 4.4);
    }
  },
  psu(root) {
    box(root, -7, -4.3, -7.5, 7, 4.3, 7.5, M.black);
    box(root, -7.01, 1.0, 2.6, -6.9, 3.0, 6.2, M.dark);
    box(root, -5, -1, 7.5, 5, 2.4, 7.52, M.label);
    const k = keepGroup(root, 'psu', 'psu_fan_rotor');
    k.userData.spinAxis = 'y';
    k.userData.spinDir = -1;
    fanRotor(k, 'psu_fan_rotor', 'y', 5.6);
    keepBox(root, 'psu', 'psu_switch', M.dark);
    keepBox(root, 'psu', 'psu_fixed_cables', M.black);
  },
  case(root) {
    box(root, -22.5, 1.5, -11, 22.5, 2, 11, M.black);
    box(root, -22.5, 47.5, -11, 22.5, 48, 11, M.black);
    box(root, -22.5, 2, -11, -22, 47.5, 11, M.black);
    box(root, 21.9, 1.5, -11, 22.5, 48, 11, M.dark);
    box(root, -22.5, 2, -11, 22, 47.5, -10.88, M.black);
    box(root, -22, 11, -9.1, 17.5, 47, -9.0, M.black);
    box(root, -22, 10.88, -9, 14, 11, 10.35, M.black);
    for (const name of Object.keys(MANIFEST.case?.keep || {})) {
      let mat = M.dark;
      if (name === 'case_glass') mat = M.glass;
      else if (name.startsWith('standoff')) mat = M.brass;
      else if (name.startsWith('slot_cover')) mat = M.steel;
      else if (name === 'case_power_led') mat = M.led;
      keepBox(root, 'case', name, mat);
    }
  },
};

/** Construit le modèle de secours d'une pièce (unités : cm). */
export function buildFallback(name) {
  const root = new THREE.Group();
  root.name = `fallback:${name}`;
  root.userData.fallback = true;
  (BUILDERS[name] || BUILDERS.cpu)(root);
  anchors(root, name);
  return root;
}
