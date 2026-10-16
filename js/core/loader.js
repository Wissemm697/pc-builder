/**
 * loader.js — Module de chargement PARTAGÉ par toutes les vues.
 *
 * - Charge chaque .glb UNE seule fois (cache de promesses) avec le décodeur meshopt.
 * - Corrige quelques matériaux une fois pour toutes (vitre, grilles perforées, LED).
 * - Fournit des CLONES légers : géométries et textures sont partagées entre les clones,
 *   seuls les nœuds sont dupliqués (et les matériaux si on le demande, pour la surbrillance).
 * - Les .glb sont en mètres (convention glTF) : on applique ×100 pour travailler en cm.
 * - Expose les ancres (positions en cm), les pivots des pièces animables et les rotors.
 * - Si un modèle ne se charge pas, renvoie un modèle de secours construit en Three.js :
 *   le site ne casse jamais.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { MANIFEST } from '../data/manifest.js';
import { buildFallback } from './fallbacks.js';

const MODEL_DIR = new URL('../../models/', import.meta.url);
const GLTF_TO_CM = 100;

const gltfLoader = new GLTFLoader();
gltfLoader.setMeshoptDecoder(MeshoptDecoder);

/** @type {Map<string, Promise<{template: THREE.Object3D, fallback: boolean}>>} */
const cache = new Map();

/** Charge (une seule fois) le gabarit d'un modèle. */
function loadTemplate(name) {
  if (!cache.has(name)) {
    const url = new URL(`${name}.glb`, MODEL_DIR).href;
    const promise = gltfLoader.loadAsync(url)
      .then((gltf) => {
        prepareTemplate(gltf.scene);
        return { template: gltf.scene, fallback: false };
      })
      .catch((err) => {
        console.warn(`[pc-builder] ${name}.glb n'a pas pu être chargé : modèle simplifié utilisé.`, err);
        const template = buildFallback(name);
        prepareTemplate(template);
        return { template, fallback: true };
      });
    cache.set(name, promise);
  }
  return cache.get(name);
}

/** Précharge une liste de modèles (sans attendre). */
export function preload(names) {
  names.forEach((n) => loadTemplate(n));
}

/** Réglages appliqués une fois sur le gabarit (donc partagés par tous les clones). */
function prepareTemplate(root) {
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    let isGlass = false;
    for (const m of mats) {
      fixMaterial(m);
      if (m.userData.isGlass) isGlass = true;
    }
    obj.castShadow = !isGlass;
    obj.receiveShadow = !isGlass;
    if (isGlass) obj.renderOrder = 5;
  });
}

function fixMaterial(m) {
  if (!m || m.userData.fixed) return;
  m.userData.fixed = true;
  const name = (m.name || '').toLowerCase();
  if (name.startsWith('glass')) {
    // verre trempé fumé : transparent, sans écriture de profondeur, reflets marqués
    m.userData.isGlass = true;
    m.transparent = true;
    m.opacity = 0.2;
    m.depthWrite = false;
    m.roughness = 0.04;
    m.metalness = 0;
    m.envMapIntensity = 1.8;
    m.side = THREE.FrontSide;
  }
  if (m.alphaTest > 0) {
    // tôles perforées (alphaMode MASK) : bords lissés grâce à l'antialiasing
    m.alphaToCoverage = true;
    m.side = THREE.DoubleSide;
  }
  if (name === 'led') {
    m.emissive = new THREE.Color(0x000000);
  }
  if (!m.userData.isGlass) {
    // reflets de l'environnement : plus discrets sur les métaux polis (sinon ils paraissent blancs)
    m.envMapIntensity = m.metalness > 0.5 ? 0.62 : 0.9;
  }
  if (m.map) m.map.anisotropy = 4;
}

/** Clone profond des matériaux d'une instance (pour modifier couleur/émission sans toucher aux autres). */
export function cloneMaterials(root) {
  const seen = new Map();
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const swap = (m) => {
      if (!seen.has(m)) {
        const c = m.clone();
        c.userData = { ...m.userData, source: m };
        seen.set(m, c);
      }
      return seen.get(m);
    };
    obj.material = Array.isArray(obj.material) ? obj.material.map(swap) : swap(obj.material);
  });
  return [...seen.values()];
}

/**
 * Renvoie une instance prête à l'emploi d'une pièce.
 * @param {string} name  nom du modèle (fan, cpu, motherboard, ram, ssd, cooler, gpu, psu, case)
 * @param {{cloneMaterials?: boolean}} [opts]
 * @returns {Promise<{name:string, root:THREE.Group, anchors:Object<string,THREE.Vector3>,
 *   pivots:Object<string,THREE.Group>, rotors:Array, materials:THREE.Material[], fallback:boolean}>}
 */
export async function getPart(name, opts = {}) {
  const { template, fallback } = await loadTemplate(name);
  const inner = template.clone(true);
  const materials = opts.cloneMaterials ? cloneMaterials(inner) : [];
  inner.scale.setScalar(fallback ? 1 : GLTF_TO_CM);

  const root = new THREE.Group();
  root.name = `part:${name}`;
  root.add(inner);
  root.updateMatrixWorld(true);

  // ancres : positions en cm dans le repère de la pièce
  const anchors = {};
  const tmp = new THREE.Vector3();
  inner.traverse((o) => {
    if (o.name && o.name.startsWith('anchor_')) {
      anchors[o.name] = root.worldToLocal(o.getWorldPosition(tmp.clone()));
    }
  });

  // pivots : chaque objet animable est rattaché à un groupe placé sur son pivot
  const pivots = {};
  const rotors = [];
  const keep = (MANIFEST[name] && MANIFEST[name].keep) || {};
  for (const [keepName, info] of Object.entries(keep)) {
    const obj = inner.getObjectByName(keepName);
    if (!obj) continue;
    const pivot = new THREE.Group();
    pivot.name = `pivot:${keepName}`;
    pivot.position.fromArray(info.pivot);
    root.add(pivot);
    root.updateMatrixWorld(true);
    pivot.attach(obj);
    pivots[keepName] = pivot;
    const spin = obj.userData.spinAxis || info.spin;
    if (spin) {
      rotors.push({ pivot, axis: spin, dir: obj.userData.spinDir || 1 });
    }
  }
  root.userData.partName = name;
  return { name, root, anchors, pivots, rotors, materials, fallback };
}

/** Fait tourner les rotors (ventilateurs). speed en tours par seconde. */
export function spinRotors(rotors, dt, speed = 1) {
  const a = dt * speed * Math.PI * 2;
  for (const r of rotors) r.pivot.rotation[r.axis] += a * r.dir;
}

/** Libère les matériaux clonés d'une instance (les géométries/textures partagées restent). */
export function disposeMaterials(materials) {
  for (const m of materials) m.dispose();
}
