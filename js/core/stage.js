/**
 * stage.js — Création d'une scène 3D prête à l'emploi : moteur de rendu WebGL,
 * caméra, contrôles (souris ET tactile), éclairage propre et ombres légères.
 *
 * Éclairage : une lumière ambiante (hémisphérique), une lumière directionnelle principale
 * qui projette des ombres douces, un léger contre-jour, et une carte d'environnement
 * (RoomEnvironment) pour que les métaux aient des reflets crédibles.
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

/** Vrai si le navigateur sait créer un contexte WebGL 2. */
export function webglAvailable() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGL2RenderingContext && c.getContext('webgl2'));
  } catch {
    return false;
  }
}

export const isCoarsePointer = () => window.matchMedia('(pointer: coarse)').matches;
export const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/**
 * @param {HTMLElement} container  élément .viewer qui recevra le <canvas>
 * @param {object} [o]
 * @param {number} [o.fov=32]
 * @param {boolean} [o.controls=true]
 * @param {boolean} [o.shadows=true]
 * @param {number} [o.maxDpr=1.75]   limite la résolution sur les écrans très denses (performances)
 */
export function createStage(container, o = {}) {
  const opts = { fov: 32, controls: true, shadows: true, maxDpr: 1.75, exposure: 1.0, ...o };
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, opts.maxDpr));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = opts.exposure;
  renderer.shadowMap.enabled = opts.shadows;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0x000000, 0);
  const canvas = renderer.domElement;
  canvas.setAttribute('aria-hidden', 'true');
  container.prepend(canvas);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envRT = pmrem.fromScene(new RoomEnvironment(renderer), 0.04);
  scene.environment = envRT.texture;
  pmrem.dispose();

  // lumière ambiante (ciel froid / sol sombre) + principale avec ombres + contre-jour
  const hemi = new THREE.HemisphereLight(0xd6e6ff, 0x0b0f14, 0.55);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffffff, 1.7);
  key.castShadow = opts.shadows;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.bias = -0.0004;
  key.shadow.normalBias = 0.02;
  key.shadow.radius = 4;
  scene.add(key);
  scene.add(key.target);
  const rim = new THREE.DirectionalLight(0x9edcff, 0.45);
  scene.add(rim);

  // sol invisible qui ne reçoit que les ombres (ombres légères)
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.ShadowMaterial({ color: 0x000000, opacity: 0.32 }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  ground.visible = opts.shadows;
  scene.add(ground);

  const camera = new THREE.PerspectiveCamera(opts.fov, 1, 0.5, 5000);

  let controls = null;
  if (opts.controls) {
    controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.rotateSpeed = 0.8;
    controls.zoomSpeed = 0.9;
    controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
    // laisse la page défiler verticalement au doigt ; un glissé horizontal fait tourner la pièce
    canvas.style.touchAction = 'pan-y';
  }

  /**
   * Cadre la lumière et l'ombre sur un objet (boîte englobante en cm).
   * @param {THREE.Box3} box
   */
  function fitLights(box) {
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const r = Math.max(size.length() / 2, 1);
    key.position.copy(center).add(new THREE.Vector3(-0.55, 1.15, 0.85).normalize().multiplyScalar(r * 3));
    key.target.position.copy(center);
    const cam = key.shadow.camera;
    cam.left = -r * 1.2; cam.right = r * 1.2; cam.top = r * 1.2; cam.bottom = -r * 1.2;
    cam.near = r * 0.5; cam.far = r * 6;
    cam.updateProjectionMatrix();
    rim.position.copy(center).add(new THREE.Vector3(0.8, 0.5, -1).normalize().multiplyScalar(r * 3));
    ground.position.set(center.x, box.min.y - 0.02, center.z);
    ground.scale.setScalar(r * 8);
  }

  let width = 0;
  let height = 0;
  function resize() {
    const w = Math.max(1, container.clientWidth);
    const h = Math.max(1, container.clientHeight);
    if (w === width && h === height) return false;
    width = w;
    height = h;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    return true;
  }
  resize();
  const ro = new ResizeObserver(() => resize());
  ro.observe(container);

  function render() {
    renderer.render(scene, camera);
  }

  function dispose() {
    ro.disconnect();
    if (controls) controls.dispose();
    envRT.texture.dispose();
    envRT.dispose();
    ground.geometry.dispose();
    ground.material.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
    canvas.remove();
  }

  return { renderer, scene, camera, controls, canvas, key, rim, hemi, ground, fitLights, resize, render, dispose,
    get size() { return { width, height }; } };
}

/**
 * Place la caméra pour que la boîte englobante remplisse l'image au plus juste,
 * vue depuis la direction `dir` (on projette les 8 coins dans le repère de la caméra).
 */
export function frameBox(camera, controls, box, dir = [0.6, 0.45, 1], margin = 1.12) {
  const center = box.getCenter(new THREE.Vector3());
  const radius = box.getSize(new THREE.Vector3()).length() / 2;
  const d = new THREE.Vector3().fromArray(dir).normalize();
  const f = d.clone().negate();
  const worldUp = Math.abs(f.y) > 0.98 ? new THREE.Vector3(0, 0, -1) : new THREE.Vector3(0, 1, 0);
  const r = new THREE.Vector3().crossVectors(f, worldUp).normalize();
  const u = new THREE.Vector3().crossVectors(r, f).normalize();
  const tv = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) / margin;
  const th = tv * camera.aspect;
  let dist = 0;
  const o = new THREE.Vector3();
  for (let i = 0; i < 8; i++) {
    o.set(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z).sub(center);
    const x = Math.abs(o.dot(r));
    const y = Math.abs(o.dot(u));
    const z = o.dot(f);
    dist = Math.max(dist, x / th - z, y / tv - z);
  }
  dist = Math.max(dist, radius * 0.8);
  camera.position.copy(center).addScaledVector(d, dist);
  camera.near = Math.max(0.1, (dist - radius) * 0.25);
  camera.far = dist + radius * 30;
  camera.updateProjectionMatrix();
  if (controls) {
    controls.target.copy(center);
    controls.minDistance = Math.max(radius * 0.45, dist * 0.35);
    controls.maxDistance = dist * 2.4;
    controls.update();
  }
  return { center, radius, dist };
}

/** Fonctions d'interpolation. */
export const ease = {
  inOut: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  out: (t) => 1 - Math.pow(1 - t, 3),
  in: (t) => t * t * t,
  outBack: (t) => { const c1 = 1.4; const c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
};
export const clamp01 = (t) => Math.min(1, Math.max(0, t));
