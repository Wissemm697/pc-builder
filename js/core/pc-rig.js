/**
 * pc-rig.js — Assemble le PC complet à partir des ancres des modèles.
 * Utilisé par le héros, la vue éclatée et le montage pas à pas (mêmes modèles, mêmes règles).
 *
 * Hiérarchie (unités : cm, repère du boîtier : X = avant, Y = haut, Z = vitre) :
 *   rig
 *   ├─ case                         (origine)
 *   ├─ mbGroup  @ case.anchor_motherboard
 *   │   ├─ motherboard
 *   │   ├─ cpu      @ mb.anchor_cpu
 *   │   ├─ cooler   @ mb.anchor_cooler
 *   │   ├─ ram ×2   @ mb.anchor_ram_A2 / anchor_ram_B2   (dual channel)
 *   │   └─ ssd      @ mb.anchor_m2_1
 *   ├─ gpu      @ mbGroup + mb.anchor_pcie_x16
 *   ├─ psu      @ case.anchor_psu
 *   └─ fans ×4  @ case.anchor_fan_front_1..3 + anchor_fan_rear
 */
import * as THREE from 'three';
import { getPart, spinRotors } from './loader.js';
import { PART_LABELS } from '../data/parts.js';

/**
 * @param {{cloneMaterials?: boolean}} [opts]
 */
export async function buildPC(opts = {}) {
  const o = { cloneMaterials: !!opts.cloneMaterials };
  const names = ['case', 'motherboard', 'cpu', 'cooler', 'ram', 'ram', 'ssd', 'gpu', 'psu', 'fan', 'fan', 'fan', 'fan'];
  const [pcCase, mb, cpu, cooler, ramA, ramB, ssd, gpu, psu, f1, f2, f3, fr] = await Promise.all(names.map((n) => getPart(n, o)));

  const rig = new THREE.Group();
  rig.name = 'pc-rig';
  const mbGroup = new THREE.Group();
  mbGroup.name = 'mbGroup';

  rig.add(pcCase.root);
  rig.add(mbGroup);
  mbGroup.position.copy(pcCase.anchors.anchor_motherboard);
  mbGroup.add(mb.root);

  const A = mb.anchors;
  cpu.root.position.copy(A.anchor_cpu);
  cooler.root.position.copy(A.anchor_cooler);
  ramA.root.position.copy(A.anchor_ram_A2);
  ramB.root.position.copy(A.anchor_ram_B2);
  ssd.root.position.copy(A.anchor_m2_1);
  mbGroup.add(cpu.root, cooler.root, ramA.root, ramB.root, ssd.root);

  gpu.root.position.copy(mbGroup.position).add(A.anchor_pcie_x16);
  psu.root.position.copy(pcCase.anchors.anchor_psu);
  const fans = [f1, f2, f3, fr];
  ['anchor_fan_front_1', 'anchor_fan_front_2', 'anchor_fan_front_3', 'anchor_fan_rear'].forEach((k, i) => {
    fans[i].root.position.copy(pcCase.anchors[k]);
  });
  rig.add(gpu.root, psu.root, ...fans.map((f) => f.root));

  // la carte graphique occupe les positions 2 et 3 : leurs caches sont retirés
  for (const k of ['slot_cover_2', 'slot_cover_3']) {
    if (pcCase.pivots[k]) pcCase.pivots[k].visible = false;
  }
  // câbles fixes de l'alimentation : cachés dans le PC assemblé (ils seraient sous le cache)
  if (psu.pivots.psu_fixed_cables) psu.pivots.psu_fixed_cables.visible = false;

  // identification des pièces (survol, clic)
  const tag = (part, key, sub) => {
    part.root.userData.partKey = key;
    part.root.userData.label = PART_LABELS[key]?.label || key;
    part.root.userData.section = PART_LABELS[key]?.section;
    if (sub) part.root.userData.sub = sub;
  };
  tag(pcCase, 'case');
  tag(mb, 'motherboard');
  tag(cpu, 'cpu');
  tag(cooler, 'cooler');
  tag(ramA, 'ram', 'A2');
  tag(ramB, 'ram', 'B2');
  tag(ssd, 'ssd');
  tag(gpu, 'gpu');
  tag(psu, 'psu');
  fans.forEach((f, i) => tag(f, 'fan', i < 3 ? 'avant' : 'arrière'));

  const parts = { case: pcCase, motherboard: mb, cpu, cooler, ram: [ramA, ramB], ssd, gpu, psu, fans };
  const all = [pcCase, mb, cpu, cooler, ramA, ramB, ssd, gpu, psu, ...fans];
  const rotors = all.flatMap((p) => p.rotors);

  // positions « assemblé » mémorisées (pour les vues qui déplacent les pièces)
  const home = new Map();
  for (const p of [...all.map((x) => x.root), mbGroup]) {
    home.set(p, { position: p.position.clone(), quaternion: p.quaternion.clone() });
  }

  return {
    rig,
    mbGroup,
    parts,
    all,
    rotors,
    home,
    materials: all.flatMap((p) => p.materials),
    fallback: all.some((p) => p.fallback),
    /** Fait tourner les ventilateurs (tours/s). */
    spin(dt, speed) { spinRotors(rotors, dt, speed); },
    /** Boîte englobante du boîtier (pour cadrer la caméra). */
    caseBox() {
      rig.updateMatrixWorld(true);
      return new THREE.Box3().setFromObject(pcCase.root);
    },
  };
}

/** Remonte la hiérarchie jusqu'à la racine d'une pièce (porteuse de userData.partKey). */
export function findPartRoot(obj) {
  let o = obj;
  while (o) {
    if (o.userData && o.userData.partKey) return o;
    o = o.parent;
  }
  return null;
}
