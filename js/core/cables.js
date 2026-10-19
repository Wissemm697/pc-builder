/**
 * cables.js : Câbles du montage, dessinés en Three.js (tubes le long d'une courbe).
 *
 * Chaque câble a deux tracés de même nombre de points :
 *   - `messy` : branché « à la va-vite », bien visible devant la carte mère ;
 *   - `tidy`  : rangé derrière le plateau (cable management).
 * On peut animer son apparition (le tube « pousse » jusqu'au connecteur) et le faire
 * passer d'un tracé à l'autre (morphing des points de contrôle).
 */
import * as THREE from 'three';

const RADIAL = 8;
const SEGMENTS = 72;

export class Cable {
  /**
   * @param {object} o
   * @param {string} o.name
   * @param {THREE.Vector3[]} o.messy
   * @param {THREE.Vector3[]} o.tidy
   * @param {number} o.radius
   * @param {number} o.color
   * @param {number[]} o.head   taille du connecteur [largeur, hauteur, profondeur] (cm)
   * @param {number[]} [o.up]   axe « haut » du connecteur (oriente sa largeur/hauteur)
   */
  constructor(o) {
    this.name = o.name;
    this.messy = o.messy;
    this.tidy = o.tidy;
    this.radius = o.radius;
    this.mix = 0;           // 0 = tracé désordonné, 1 = tracé rangé
    this.progress = 0;      // 0..1 : part du câble dessinée
    this.group = new THREE.Group();
    this.group.name = `cable:${o.name}`;
    this.material = new THREE.MeshStandardMaterial({ color: o.color, roughness: 0.55, metalness: 0.05 });
    this.headMat = new THREE.MeshStandardMaterial({ color: 0x15171a, roughness: 0.5 });
    this.mesh = new THREE.Mesh(new THREE.BufferGeometry(), this.material);
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
    this.group.add(this.mesh);
    this.head = new THREE.Mesh(new THREE.BoxGeometry(o.head[0], o.head[1], o.head[2]), this.headMat);
    this.head.castShadow = true;
    this.head.up.fromArray(o.up || [0, 1, 0]);
    this.headDepth = o.head[2];
    this.group.add(this.head);
    this.rebuild();
  }

  points() {
    const k = this.mix;
    return this.messy.map((p, i) => p.clone().lerp(this.tidy[i], k));
  }

  rebuild() {
    const curve = new THREE.CatmullRomCurve3(this.points(), false, 'centripetal');
    const geo = new THREE.TubeGeometry(curve, SEGMENTS, this.radius, RADIAL, false);
    this.mesh.geometry.dispose();
    this.mesh.geometry = geo;
    this.curve = curve;
    this.applyProgress();
    // connecteur au bout, aligné sur la dernière tangente
    const end = curve.getPoint(1);
    const tan = curve.getTangent(1).normalize();
    this.head.position.copy(end).addScaledVector(tan, -(this.headDepth * 0.5 - 0.25));
    this.head.lookAt(this.head.position.clone().add(tan));
  }

  applyProgress() {
    const total = this.mesh.geometry.index ? this.mesh.geometry.index.count : 0;
    const per = RADIAL * 6;
    const n = Math.round(THREE.MathUtils.clamp(this.progress, 0, 1) * SEGMENTS) * per;
    this.mesh.geometry.setDrawRange(0, Math.min(total, n));
    this.mesh.visible = this.progress > 0.001;
    this.head.visible = this.progress >= 0.999;
  }

  setProgress(p) {
    this.progress = p;
    this.applyProgress();
  }

  setMix(k) {
    this.mix = k;
    this.rebuild();
  }

  dispose() {
    this.mesh.geometry.dispose();
    this.head.geometry.dispose();
    this.material.dispose();
    this.headMat.dispose();
  }
}

/** Ré-échantillonne une polyligne en `n` points régulièrement espacés (pour le morphing). */
export function resample(points, n) {
  const pts = points.map((p) => (p.isVector3 ? p : new THREE.Vector3().fromArray(p)));
  const lens = [0];
  for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + pts[i].distanceTo(pts[i - 1]));
  const total = lens[lens.length - 1];
  const out = [];
  for (let k = 0; k < n; k++) {
    const d = (k / (n - 1)) * total;
    let i = 1;
    while (i < lens.length - 1 && lens[i] < d) i++;
    const seg = lens[i] - lens[i - 1] || 1;
    out.push(pts[i - 1].clone().lerp(pts[i], (d - lens[i - 1]) / seg));
  }
  return out;
}
