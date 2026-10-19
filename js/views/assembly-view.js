/**
 * assembly-view.js : Montage pas à pas en 3D (11 étapes).
 *
 * Principe : chaque étape k a un « état final » (où est chaque pièce une fois l'étape
 * terminée). Pour jouer l'étape k, on place instantanément la scène dans l'état final de
 * l'étape k-1, puis on anime ce qui change. Aller en arrière, sauter une étape ou rejouer
 * fonctionnent donc toujours de la même façon.
 *
 * Unités : cm. Repère du boîtier (X = avant, Y = haut, Z = vitre). La table est en Y = 0.
 */
import * as THREE from 'three';
import { createStage, ease, prefersReducedMotion } from '../core/stage.js';
import { buildPC } from '../core/pc-rig.js';
import { Tweens } from '../core/anim.js';
import { Cable, resample } from '../core/cables.js';
import { L } from '../i18n.js';

const D2R = THREE.MathUtils.degToRad;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const ACCENT = 0x22d3ee;

function quatFromBasis(a, b, c) {
  const m = new THREE.Matrix4().makeBasis(V(...a), V(...b), V(...c));
  return new THREE.Quaternion().setFromRotationMatrix(m);
}

export async function createAssemblyView(el, stepsUI) {
  const stage = createStage(el, { fov: 34, maxDpr: 1.5 });
  const { scene, camera, controls } = stage;
  stage.key.shadow.mapSize.set(2048, 2048);
  stage.ground.visible = false;
  controls.minDistance = 8;
  controls.maxDistance = 260;
  const tweens = new Tweens();
  const reduced = prefersReducedMotion();
  const D = (s) => (reduced ? 0.01 : s); // durées (quasi nulles si l'utilisateur préfère moins d'animations)

  const pc = await buildPC({ cloneMaterials: true });
  scene.add(pc.rig);
  const P = pc.parts;
  const mbg = pc.mbGroup;
  const MB = P.motherboard.anchors;
  const CA = P.case.anchors;
  const mbPiv = P.motherboard.pivots;
  const casePiv = P.case.pivots;
  const psuPiv = P.psu.pivots;
  const disposables = [];
  const track = (o) => { disposables.push(o); return o; };

  // ------------------------------------------------------------------ établi
  const tableMat = track(new THREE.MeshStandardMaterial({ color: 0x131921, roughness: 0.92 }));
  const table = new THREE.Mesh(track(new THREE.BoxGeometry(150, 2, 105)), tableMat);
  table.position.set(8, -1.01, 18);
  table.receiveShadow = true;
  scene.add(table);
  const matMat = track(new THREE.MeshStandardMaterial({ color: 0x1a2430, roughness: 0.96 }));
  const mat = new THREE.Mesh(track(new THREE.PlaneGeometry(78, 52)), matMat);
  mat.rotation.x = -Math.PI / 2;
  mat.position.set(-4, 0.004, 40);
  mat.receiveShadow = true;
  scene.add(mat);
  // couleurs de l'établi selon le thème clair / sombre de la page
  const applyTheme = () => {
    const light = document.documentElement.getAttribute('data-theme') === 'light';
    tableMat.color.set(light ? 0xc9ced6 : 0x131921);
    matMat.color.set(light ? 0xaeb7c2 : 0x1a2430);
  };
  applyTheme();
  document.addEventListener('pc-builder:theme', applyTheme);
  // boîte de la carte mère (support isolant)
  const boxMat = track(new THREE.MeshStandardMaterial({ color: 0x3a332b, roughness: 0.85 }));
  const mbBox = new THREE.Mesh(track(new THREE.BoxGeometry(34, 6, 28)), boxMat);
  mbBox.position.set(-6, 3, 34);
  mbBox.castShadow = true;
  mbBox.receiveShadow = true;
  const stripe = new THREE.Mesh(track(new THREE.BoxGeometry(34.05, 0.6, 28.05)),
    track(new THREE.MeshStandardMaterial({ color: ACCENT, roughness: 0.5 })));
  stripe.position.set(-6, 1.2, 34);
  const boxGroup = new THREE.Group();   // rangée à la dernière étape (elle masquerait le PC)
  boxGroup.add(mbBox, stripe);
  scene.add(boxGroup);

  // ------------------------------------------------------------------ poses
  const POSE_BOX = { p: V(-6, 6.02, 34), q: new THREE.Quaternion().setFromAxisAngle(V(1, 0, 0), D2R(-90)) };
  const Qflat = POSE_BOX.q.clone();
  const Qram = quatFromBasis([0, 1, 0], [1, 0, 0], [0, 0, -1]);
  const home = (node) => ({ p: pc.home.get(node).position.clone(), q: pc.home.get(node).quaternion.clone() });
  /** Pose monde -> pose locale dans mbGroup (carte posée sur sa boîte). */
  const toBoxLocal = (p, q) => {
    const inv = POSE_BOX.q.clone().invert();
    return { p: p.clone().sub(POSE_BOX.p).applyQuaternion(inv), q: inv.clone().multiply(q) };
  };
  const nodes = {
    mbg,
    cpu: P.cpu.root,
    cooler: P.cooler.root,
    ram0: P.ram[0].root,
    ram1: P.ram[1].root,
    ssd: P.ssd.root,
    gpu: P.gpu.root,
    psu: P.psu.root,
  };
  const HOME = Object.fromEntries(Object.entries(nodes).map(([k, n]) => [k, home(n)]));
  const TABLE = {
    cpu: toBoxLocal(V(-30, 0.03, 30), Qflat),
    cooler: toBoxLocal(V(-34, 0.72, 45), Qflat),
    ram0: toBoxLocal(V(20, 0.07, 37), Qram),
    ram1: toBoxLocal(V(20, 0.07, 41.5), Qram),
    ssd: toBoxLocal(V(7, 0.03, 54), Qflat),
    gpu: { p: V(31, 4.45, 46), q: new THREE.Quaternion() },
    psu: { p: V(39, 4.32, 9), q: new THREE.Quaternion() },
  };
  const setPose = (node, pose) => { node.position.copy(pose.p); node.quaternion.copy(pose.q); };
  /** Anime un nœud d'une pose à une autre. */
  function moveTo(node, pose, duration, e = ease.inOut, delay = 0) {
    const p0 = node.position.clone();
    const q0 = node.quaternion.clone();
    return tweens.to({
      duration: D(duration), delay: reduced ? 0 : delay, ease: e,
      update: (k) => { node.position.lerpVectors(p0, pose.p, k); node.quaternion.slerpQuaternions(q0, pose.q, k); },
    });
  }
  /** Anime une propriété numérique (rotation d'un pivot, opacité…). */
  function animate(get, set, to, duration, e = ease.inOut, delay = 0) {
    const from = get();
    return tweens.to({ duration: D(duration), delay: reduced ? 0 : delay, ease: e, update: (k) => set(from + (to - from) * k) });
  }
  const offsetPose = (pose, dx, dy, dz) => ({ p: pose.p.clone().add(V(dx, dy, dz)), q: pose.q.clone() });

  // ------------------------------------------------------------------ accessoires
  const metalMat = track(new THREE.MeshStandardMaterial({ color: 0xb8bec6, metalness: 1, roughness: 0.3 }));
  const darkMat = track(new THREE.MeshStandardMaterial({ color: 0x1c2026, roughness: 0.5 }));
  const accentMat = track(new THREE.MeshStandardMaterial({ color: ACCENT, roughness: 0.4 }));
  function cylX(r, len, m) {
    const g = track(new THREE.CylinderGeometry(r, r, len, 20));
    g.rotateZ(Math.PI / 2);
    const mesh = new THREE.Mesh(g, m);
    mesh.castShadow = true;
    return mesh;
  }
  // tournevis cruciforme
  const screwdriver = new THREE.Group();
  const handle = cylX(1.35, 10, darkMat);
  const ring = cylX(1.4, 0.6, accentMat);
  ring.position.x = 4.2;
  const shaft = cylX(0.3, 9, metalMat);
  shaft.position.x = 9.5;
  const tipG = track(new THREE.ConeGeometry(0.3, 1.0, 12));
  tipG.rotateZ(-Math.PI / 2);
  const tip = new THREE.Mesh(tipG, metalMat);
  tip.position.x = 14.5;
  screwdriver.add(handle, ring, shaft, tip);
  screwdriver.position.set(-14, 1.35, 58);
  screwdriver.rotation.y = 0.25;
  scene.add(screwdriver);
  // seringue de pâte thermique
  const syringe = new THREE.Group();
  const body = cylX(0.65, 6.5, track(new THREE.MeshStandardMaterial({ color: 0xd9dde3, roughness: 0.35, transparent: true, opacity: 0.85 })));
  const paste = cylX(0.5, 5, track(new THREE.MeshStandardMaterial({ color: 0x8d949c, roughness: 0.7 })));
  const plunger = cylX(0.35, 2.5, darkMat);
  plunger.position.x = -4.2;
  syringe.add(body, paste, plunger);
  syringe.position.set(-28, 0.66, 55);
  syringe.rotation.y = -0.4;
  scene.add(syringe);
  // noisette de pâte thermique (sur l'IHS, dans le repère de la carte mère)
  const blob = new THREE.Mesh(track(new THREE.SphereGeometry(0.45, 20, 12)),
    track(new THREE.MeshStandardMaterial({ color: 0x9aa1a9, roughness: 0.65 })));
  blob.scale.set(1, 1, 0.5);
  blob.position.copy(MB.anchor_cooler).add(V(0, 0, 0.18));
  mbg.add(blob);
  // film de protection sous la base du ventirad
  const filmMat = track(new THREE.MeshStandardMaterial({ color: 0x7cc8ff, roughness: 0.15, transparent: true, opacity: 0.55, side: THREE.DoubleSide }));
  const film = new THREE.Mesh(track(new THREE.PlaneGeometry(4.6, 4.6)), filmMat);
  film.position.set(0, 0, -0.03);
  const filmTab = new THREE.Mesh(track(new THREE.PlaneGeometry(1.4, 1.0)), filmMat);
  filmTab.position.set(2.9, 0, -0.03);
  const filmGroup = new THREE.Group();
  filmGroup.add(film, filmTab);
  P.cooler.root.add(filmGroup);
  // vis de la carte mère (9) et de l'équerre du GPU
  const screwG = track(new THREE.CylinderGeometry(0.45, 0.45, 0.24, 18));
  screwG.rotateX(Math.PI / 2);
  const screwMat = track(new THREE.MeshStandardMaterial({ color: 0x2d3238, metalness: 0.8, roughness: 0.35 }));
  const mbScrews = [];
  for (let i = 1; i <= 9; i++) {
    const s = new THREE.Mesh(screwG, screwMat);
    s.position.copy(MB[`anchor_hole_${i}`]).add(V(0, 0, 0.28));
    s.castShadow = true;
    mbg.add(s);
    mbScrews.push(s);
  }
  const gpuScrew = new THREE.Mesh(screwG, screwMat);
  gpuScrew.position.copy(P.gpu.anchors.anchor_bracket_screw).add(V(0, 0, 0.15));
  P.gpu.root.add(gpuScrew);
  // LED de diagnostic allumables (CPU, DRAM, VGA, BOOT)
  const ledColors = [0xff4040, 0xffb020, 0xf2f4f7, 0x34d399];
  const leds = ledColors.map((c, i) => {
    const m = track(new THREE.MeshStandardMaterial({ color: 0x111111, emissive: c, emissiveIntensity: 0 }));
    const led = new THREE.Mesh(track(new THREE.BoxGeometry(0.32, 0.22, 0.1)), m);
    led.position.set(10.05, 10.3 - i * 0.5, 0.3);
    mbg.add(led);
    return led;
  });
  // anneaux lumineux de repérage (triangles, clics des loquets)
  const ringGeo = track(new THREE.RingGeometry(0.28, 0.5, 32));
  function makeRing(parent, pos, scale = 1) {
    const m = new THREE.MeshBasicMaterial({ color: ACCENT, transparent: true, opacity: 0, depthTest: false, side: THREE.DoubleSide });
    track(m);
    const r = new THREE.Mesh(ringGeo, m);
    r.position.copy(pos);
    r.scale.setScalar(scale);
    r.renderOrder = 10;
    r.visible = false;
    parent.add(r);
    return r;
  }
  const ringCpuTri = makeRing(P.cpu.root, P.cpu.anchors.anchor_triangle.clone().add(V(0, 0, 0.05)), 1.2);
  const ringSockTri = makeRing(P.motherboard.root, MB.anchor_socket_triangle.clone().add(V(0, 0, 0.05)), 1.2);
  const ringLatches = ['A2', 'B2'].map((k) => makeRing(P.motherboard.root, V(MB[`anchor_ram_${k}`].x, 12.6, 1.3), 1.4));
  function pulse(r, times = 3, duration = 0.5) {
    r.visible = true;
    let chain = Promise.resolve();
    for (let i = 0; i < times; i++) {
      chain = chain.then(() => tweens.to({
        duration: D(duration), ease: (x) => x,
        update: (k) => { r.material.opacity = Math.sin(k * Math.PI) * 0.95; r.scale.setScalar((1 + k * 1.2) * (r.userData.s || 1)); },
      }));
    }
    return chain.then(() => { r.visible = false; r.material.opacity = 0; });
  }
  [ringCpuTri, ringSockTri, ...ringLatches].forEach((r) => { r.userData.s = r.scale.x; });
  // attaches velcro (derrière le plateau)
  const strapMat = track(new THREE.MeshStandardMaterial({ color: 0x0e7490, roughness: 0.7 }));
  const straps = [V(5.6, 27, -10), V(-17.6, 30, -10), V(13.5, 37, -10), V(-2, 9.7, -9.8)].map((p, i) => {
    const t = new THREE.Mesh(track(new THREE.TorusGeometry(i === 3 ? 1.1 : 1.25, 0.22, 8, 24)), strapMat);
    t.position.copy(p);
    t.rotation.x = i === 3 ? 0 : Math.PI / 2;
    if (i === 3) t.rotation.y = Math.PI / 2;
    scene.add(t);
    return t;
  });
  // écran (dernière étape) : il s'allume sur l'interface du BIOS
  const monitor = new THREE.Group();
  const standBase = new THREE.Mesh(track(new THREE.CylinderGeometry(8, 9, 0.8, 32)), darkMat);
  standBase.position.y = 0.4;
  const neck = new THREE.Mesh(track(new THREE.BoxGeometry(3.2, 20, 1.6)), darkMat);
  neck.position.set(0, 10.5, -1.5);
  const panel = new THREE.Mesh(track(new THREE.BoxGeometry(54.5, 32, 2)), darkMat);
  panel.position.set(0, 26, 0);
  const screenTex = track(makeScreenTexture());
  const screenMat = track(new THREE.MeshBasicMaterial({ map: screenTex, color: 0x000000 }));
  const screen = new THREE.Mesh(track(new THREE.PlaneGeometry(52.5, 29.6)), screenMat);
  screen.position.set(0, 26.4, 1.01);
  [standBase, neck, panel].forEach((m) => { m.castShadow = true; m.receiveShadow = true; });
  monitor.add(standBase, neck, panel, screen);
  monitor.position.set(50, 0, -14);
  monitor.rotation.y = -0.5;
  scene.add(monitor);

  // ------------------------------------------------------------------ câbles
  const W = {};
  {
    const mbH = HOME.mbg.p;
    const mbW = (a) => a.clone().add(mbH);
    const psuW = (k) => P.psu.anchors[k].clone().add(HOME.psu.p);
    W.atx24 = mbW(MB.anchor_atx24);
    W.eps8 = mbW(MB.anchor_eps8);
    W.cpuFan = mbW(MB.anchor_cpu_fan);
    W.fpanel = mbW(MB.anchor_f_panel);
    W.usb3 = mbW(MB.anchor_usb3);
    W.audio = mbW(MB.anchor_hd_audio);
    W.sys1 = mbW(MB.anchor_sys_fan_1);
    W.out24 = psuW('anchor_psu_out_24');
    W.outEps = psuW('anchor_psu_out_eps');
    W.pcie = psuW('anchor_psu_pcie');
    W.gpuPwr = P.gpu.anchors.anchor_gpu_power.clone().add(HOME.gpu.p);
    W.coolerFan = P.cooler.anchors.anchor_fan_cable.clone().add(MB.anchor_cooler).add(mbH);
    W.rearFan = P.fans[3].anchors.anchor_fan_cable.clone().add(P.fans[3].root.position);
    W.gLow = CA.anchor_grommet_low;
    W.gHigh = CA.anchor_grommet_high;
    W.gEps = CA.anchor_grommet_eps;
    W.shroud = CA.anchor_shroud_cutout;
    W.front = CA.anchor_front_io;
  }
  const BZ = -10.0; // espace derrière le plateau
  const a = (v, x, y, z) => v.clone().add(V(x, y, z));
  const ROUTES = {
    atx24: {
      radius: 0.75, color: 0x1a1c20, head: [1.2, 5.5, 1.6],
      messy: [W.out24, a(W.out24, 2, 0.5, -2), a(W.shroud, -0.5, -0.8, 0), a(W.shroud, 0, 1.5, 0.3), V(W.shroud.x + 1.5, 17, 1.0),
        V(3.5, 24, 6.5), V(6.2, 30.5, 5), V(5.2, 35.4, 1.0), a(W.atx24, 0, 0, 2.4), W.atx24],
      tidy: [W.out24, a(W.out24, 2.4, 0.1, -3), V(W.gLow.x - 8.5, 9.6, BZ), V(W.gLow.x - 0.6, 14, BZ), V(W.gHigh.x + 0.6, W.gHigh.y - 4, BZ),
        V(W.gHigh.x + 0.3, W.gHigh.y, -9.6), V(W.gHigh.x - 0.1, W.gHigh.y + 0.6, -7.8), V(W.atx24.x + 1.4, W.atx24.y, -5.4), a(W.atx24, 0, 0, 2.4), W.atx24],
    },
    eps8: {
      radius: 0.45, color: 0x1a1c20, head: [2.3, 1.15, 1.6],
      messy: [W.outEps, a(W.outEps, 2, 0.8, -1.5), a(W.shroud, -1, -0.6, 0), a(W.shroud, -0.6, 1.6, 0.5), V(-3, 19, 3), V(-9, 30, 7),
        V(-15.5, 39, 6), V(-15, 44.5, 2), a(W.eps8, 0, 0.6, 2.0), W.eps8],
      tidy: [W.outEps, a(W.outEps, 1.5, 0.6, -4.2), V(-10, 10, BZ), V(-17.5, 16, BZ), V(-18.5, 38, BZ), V(W.gEps.x - 1.2, W.gEps.y - 0.2, BZ),
        V(W.gEps.x, W.gEps.y, -9.3), V(W.gEps.x + 0.1, W.gEps.y - 0.3, -7.6), a(W.eps8, 0, 0.6, 2.0), W.eps8],
    },
    cpuFan: {
      radius: 0.14, color: 0x111214, head: [1.0, 0.45, 0.8],
      messy: [W.coolerFan, a(W.coolerFan, 1.5, 0.2, 1.2), V(W.cpuFan.x + 1.2, W.cpuFan.y - 1.5, -2.2), a(W.cpuFan, 0, 0, 1.4), W.cpuFan],
      tidy: [W.coolerFan, a(W.coolerFan, 0.4, 0.7, -0.8), V(W.cpuFan.x - 0.9, W.cpuFan.y - 0.7, -5.6), a(W.cpuFan, 0, 0, 1.4), W.cpuFan],
    },
    fpanel: {
      radius: 0.2, color: 0x6b7480, head: [2.0, 0.7, 0.9],
      messy: [W.front, a(W.front, -1, -1.5, 4), V(17, 40, 6), V(13, 30, 7.5), V(8, 22, 6), V(4, 17.5, 3), V(1.5, 15.6, 0), V(0, 15.1, -3),
        a(W.fpanel, 0, 0, 1.2), W.fpanel],
      tidy: [W.front, a(W.front, -1.5, -2, 0), V(14, 34, BZ), V(8, 19, BZ), V(W.gLow.x + 0.4, W.gLow.y - 4, BZ), V(W.gLow.x, W.gLow.y - 4.4, -9.3),
        V(W.gLow.x - 0.6, W.gLow.y - 5, -7.6), V(W.fpanel.x + 1.8, W.fpanel.y + 0.2, -6.0), a(W.fpanel, 0, 0, 1.2), W.fpanel],
    },
    usb3: {
      radius: 0.32, color: 0x1d3a6e, head: [1.05, 2.7, 1.1],
      messy: [W.front, a(W.front, -0.8, -1.2, 3.5), V(16.5, 42, 5.5), V(12.5, 33, 7), V(8, 27.5, 5.5), V(5, 25.8, 2.5), V(3.5, 25.5, -0.5),
        V(2.7, 25.4, -3.5), a(W.usb3, 0, 0, 1.2), W.usb3],
      tidy: [W.front, a(W.front, -1.2, -1.6, 0), V(13, 38, BZ), V(7.5, 28, BZ), V(W.gLow.x + 0.4, W.gLow.y + 3, BZ), V(W.gLow.x, W.gLow.y + 3.5, -9.3),
        V(W.gLow.x - 0.6, W.gLow.y + 3.8, -7.6), V(W.usb3.x + 1.4, W.usb3.y, -5.6), a(W.usb3, 0, 0, 1.2), W.usb3],
    },
    audio: {
      radius: 0.22, color: 0x2a2d33, head: [0.6, 1.3, 0.9],
      messy: [W.front, a(W.front, -1, -1.8, 3), V(16, 38, 7), V(10, 25, 8), V(3, 17, 6.5), V(-6, 15.5, 4), V(-13, 15, 1), V(-17, 15, -2.5),
        a(W.audio, 0, -0.6, 1.0), W.audio],
      tidy: [W.front, a(W.front, -1.8, -2.2, 0), V(12, 28, BZ), V(4, 10, BZ), V(-0.5, 9.4, -9.4), a(W.shroud, -0.5, 0.6, 0), V(-6, 13, -7.9),
        V(-14, 13.4, -7.8), a(W.audio, 0, -0.6, 1.0), W.audio],
    },
    rearFan: {
      radius: 0.14, color: 0x111214, head: [1.0, 0.45, 0.8],
      messy: [W.rearFan, a(W.rearFan, 1.2, -1.5, 2.5), V(-19.5, 27, 4), V(-20, 21, 3), V(-19.6, 17, 0.5), V(-18.5, 15.5, -3), a(W.sys1, 0, 0, 1.2), W.sys1],
      tidy: [W.rearFan, a(W.rearFan, 0.4, -1, -2), V(-21.5, 28, -8), V(-21.55, 20, -8), V(-21.4, 15.6, -8), V(W.sys1.x - 1.5, W.sys1.y + 0.4, -7.2),
        a(W.sys1, 0, 0, 1.2), W.sys1],
    },
    pcie: {
      radius: 0.5, color: 0x1a1c20, head: [2.2, 1.1, 1.6],
      messy: [W.pcie, a(W.pcie, 2.3, 1.4, -4.4), a(W.shroud, -1.2, -0.8, 0), a(W.shroud, 0, 1.2, 0.2), V(0.5, 14.5, -2), V(1.2, 17.5, 4.5),
        V(0.6, 21, 7.2), V(-0.4, 23.6, 7.6), a(W.gpuPwr, 0, 0, 2.2), W.gpuPwr],
      tidy: [W.pcie, a(W.pcie, 2.3, 1.4, -4.4), a(W.shroud, -1.2, -0.8, 0), a(W.shroud, 0, 1.2, 0.2), V(0.4, 14.5, -3), V(0.6, 17, 3),
        V(0.2, 20.5, 5.6), V(-0.6, 23.4, 6.3), a(W.gpuPwr, 0, 0, 2.2), W.gpuPwr],
    },
  };
  const cables = {};
  for (const [name, r] of Object.entries(ROUTES)) {
    const n = 18;
    const c = new Cable({ name, radius: r.radius, color: r.color, head: r.head, messy: resample(r.messy, n), tidy: resample(r.tidy, n) });
    scene.add(c.group);
    cables[name] = c;
  }
  const STEP8_CABLES = ['atx24', 'eps8', 'cpuFan', 'fpanel', 'usb3', 'audio', 'rearFan'];

  // ------------------------------------------------------------------ état « après l'étape k »
  let fanSpeed = 0;
  const glassHome = casePiv.case_glass ? casePiv.case_glass.position.clone() : null;
  const panelHome = casePiv.case_panel_right ? casePiv.case_panel_right.position.clone() : null;
  const coverHome = ['slot_cover_2', 'slot_cover_3'].map((k) => casePiv[k]?.position.clone());
  const standoffHome = Array.from({ length: 9 }, (_, i) => casePiv[`standoff_${i + 1}`]?.position.clone());
  const screwPiv = mbPiv.m2_screw;
  const screwHome = screwPiv ? screwPiv.position.clone() : null;
  const ledMat = [];
  casePiv.case_power_led?.traverse((o) => { if (o.isMesh) [].concat(o.material).forEach((m) => ledMat.push(m)); });
  const btnHome = casePiv.case_power_button ? casePiv.case_power_button.position.clone() : null;

  function setPower(on) {
    for (const m of ledMat) {
      if (!m.emissive) continue;
      m.emissive.set(on ? ACCENT : 0x000000);
      m.emissiveIntensity = on ? 2.2 : 0;
    }
  }
  function setSwitch(on) {
    if (psuPiv.psu_switch) psuPiv.psu_switch.rotation.z = D2R(on ? -10 : 10);
  }

  function applyState(k) {
    setPose(mbg, k >= 6 ? HOME.mbg : POSE_BOX);
    setPose(nodes.cpu, k >= 2 ? HOME.cpu : TABLE.cpu);
    setPose(nodes.ram0, k >= 3 ? HOME.ram0 : TABLE.ram0);
    setPose(nodes.ram1, k >= 3 ? HOME.ram1 : TABLE.ram1);
    setPose(nodes.ssd, k >= 4 ? HOME.ssd : TABLE.ssd);
    setPose(nodes.cooler, k >= 5 ? HOME.cooler : TABLE.cooler);
    setPose(nodes.psu, k >= 7 ? HOME.psu : TABLE.psu);
    setPose(nodes.gpu, k >= 9 ? HOME.gpu : TABLE.gpu);
    // pièces mobiles de la carte mère
    if (mbPiv.socket_lever) mbPiv.socket_lever.rotation.set(0, 0, 0);
    if (mbPiv.socket_loadplate) mbPiv.socket_loadplate.rotation.set(0, 0, 0);
    for (const key of ['A1', 'A2', 'B1', 'B2']) mbPiv[`dimm_latch_${key}`]?.rotation.set(0, 0, 0);
    mbPiv.pcie_x16_latch?.rotation.set(0, 0, 0);
    if (screwPiv) { screwPiv.position.copy(screwHome); screwPiv.rotation.set(0, 0, 0); screwPiv.visible = true; }
    // accessoires
    filmGroup.visible = k < 5;
    filmGroup.position.set(0, 0, 0);
    filmMat.opacity = 0.55;
    blob.visible = false;
    blob.scale.set(1, 1, 0.5);
    mbScrews.forEach((s) => { s.visible = k >= 6; s.position.z = MB.anchor_hole_1.z + 0.28; });
    standoffHome.forEach((p, i) => { const s = casePiv[`standoff_${i + 1}`]; if (s && p) { s.position.copy(p); s.rotation.set(0, 0, 0); } });
    ['slot_cover_2', 'slot_cover_3'].forEach((n, i) => { const c = casePiv[n]; if (c) { c.visible = k < 9; c.position.copy(coverHome[i]); } });
    gpuScrew.visible = k >= 9;
    if (psuPiv.psu_fixed_cables) psuPiv.psu_fixed_cables.visible = k < 7;
    // câbles
    for (const [name, c] of Object.entries(cables)) {
      const shown = name === 'pcie' ? k >= 9 : k >= 8;
      c.mix = k >= 10 ? 1 : 0;
      c.rebuild();
      c.setProgress(shown ? 1 : 0);
    }
    straps.forEach((s) => { s.visible = k >= 10; s.scale.setScalar(1); });
    // panneaux du boîtier
    if (casePiv.case_glass) { casePiv.case_glass.visible = k >= 11; casePiv.case_glass.position.copy(glassHome); }
    if (casePiv.case_panel_right) { casePiv.case_panel_right.visible = true; casePiv.case_panel_right.position.copy(panelHome); }
    if (casePiv.case_power_button) casePiv.case_power_button.position.copy(btnHome);
    // alimentation électrique
    setSwitch(k >= 11);
    setPower(k >= 11);
    leds.forEach((l) => { l.material.emissiveIntensity = 0; });
    fanSpeed = k >= 11 ? 1.0 : 0;
    monitor.visible = k >= 11;
    boxGroup.visible = k < 11;
    boxGroup.position.set(0, 0, 0);
    screenMat.color.set(k >= 11 ? 0xffffff : 0x000000);
    [ringCpuTri, ringSockTri, ...ringLatches].forEach((r) => { r.visible = false; });
  }

  // ------------------------------------------------------------------ caméra
  const mbWorld = (local) => { mbg.updateMatrixWorld(true); return mbg.localToWorld(local.clone()); };
  /** Cadre une zone (boîte) depuis une direction, en tenant compte du format de la zone 3D. */
  function fitView(min, max, dir, margin = 1.05) {
    const box = new THREE.Box3(min, max);
    const center = box.getCenter(new THREE.Vector3());
    const d = V(...dir).normalize();
    const f = d.clone().negate();
    const r = new THREE.Vector3().crossVectors(f, V(0, 1, 0)).normalize();
    const u = new THREE.Vector3().crossVectors(r, f).normalize();
    const tv = Math.tan(D2R(camera.fov) / 2) / margin;
    const th = tv * camera.aspect;
    let dist = 1;
    for (let i = 0; i < 8; i++) {
      const o = V(i & 1 ? max.x : min.x, i & 2 ? max.y : min.y, i & 4 ? max.z : min.z).sub(center);
      dist = Math.max(dist, Math.abs(o.dot(r)) / th - o.dot(f), Math.abs(o.dot(u)) / tv - o.dot(f));
    }
    return { pos: center.clone().addScaledVector(d, dist), target: center };
  }
  const around = (c, h, dir, margin) => fitView(c.clone().sub(V(h, h, h)), c.clone().add(V(h, h, h)), dir, margin);
  function view(k) {
    switch (k) {
      case 1: return fitView(V(-44, 0, -12), V(62, 46, 62), [0.06, 0.95, 1], 1.0);
      case 2: return around(mbWorld(MB.anchor_cpu), 5.5, [0.3, 1.1, 0.9]);
      case 3: return around(mbWorld(MB.anchor_ram_A2.clone().lerp(MB.anchor_ram_B2, 0.5).add(V(0, 2.5, 1))), 8.5, [0.55, 1.0, 0.85]);
      case 4: return around(mbWorld(MB.anchor_m2_1.clone().add(V(4, 0, 0))), 6.5, [0.35, 1.1, 0.95]);
      case 5: return fitView(V(-40, 0, 26), V(2, 24, 50), [0.55, 0.75, 1]);
      case 6: return fitView(V(-24, 0, -11), V(24, 48, 46), [0.55, 0.42, 1]);
      case 7: return fitView(V(-50, 0, -11), V(46, 32, 20), [-0.55, 0.45, 1]);
      case 8: return fitView(V(-23, 8, -11), V(23, 47, 9), [0.42, 0.3, 1]);
      case 9: return fitView(V(-23, 0, -10), V(54, 30, 60), [0.45, 0.65, 1]);
      case 10: return fitView(V(-23, 2, -12), V(20, 47, -8), [-0.25, 0.25, -1]);
      case 11: return fitView(V(-23, 0, -28), V(75, 46, 12), [0.32, 0.28, 1], 1.02);
      // plans rapprochés utilisés en fin d'étape
      case 'psu': return fitView(V(-24, 0, -10), V(-6, 14, 9), [-1, 0.34, 0.55], 1.3);   // arrière : dos de l'alimentation
      case 'gpu': return fitView(V(-23, 8, -11), V(21, 36, 12), [0.42, 0.3, 1], 1.1);    // carte graphique en place
      default: return fitView(V(-44, 0, -12), V(62, 46, 62), [0.06, 0.95, 1], 1.0);
    }
  }
  function camTo(k, duration = 1.3) {
    const v = view(k);
    const p0 = camera.position.clone();
    const t0 = controls.target.clone();
    return tweens.to({
      duration: D(duration),
      update: (x) => { camera.position.lerpVectors(p0, v.pos, x); controls.target.lerpVectors(t0, v.target, x); },
    });
  }

  // ------------------------------------------------------------------ animations des étapes
  let token = 0;
  async function play(k) {
    const my = ++token;
    tweens.cancelAll();
    el.dataset.stepDone = '';
    applyState(k - 1);
    const alive = () => my === token;
    const step = STEPS[k];
    if (step) await step(alive);
    if (alive()) {
      applyState(k); // garantit l'état final exact
      el.dataset.stepDone = String(k); // étape terminée (utile pour les tests automatiques)
    }
  }

  const STEPS = {
    async 1(alive) {
      screwdriver.position.y = 8;
      syringe.position.y = 8;
      await camTo(1, 1.0);
      if (!alive()) return;
      await Promise.all([
        animate(() => screwdriver.position.y, (v) => { screwdriver.position.y = v; }, 1.35, 0.7, ease.out),
        animate(() => syringe.position.y, (v) => { syringe.position.y = v; }, 0.66, 0.7, ease.out, 0.15),
      ]);
    },
    async 2(alive) {
      await camTo(2);
      if (!alive()) return;
      const lever = mbPiv.socket_lever;
      const plate = mbPiv.socket_loadplate;
      await animate(() => lever.rotation.y, (v) => { lever.rotation.y = v; }, D2R(-100), 0.7);
      if (!alive()) return;
      await animate(() => plate.rotation.y, (v) => { plate.rotation.y = v; }, D2R(-115), 0.8);
      if (!alive()) return;
      const above = offsetPose(HOME.cpu, 0, 0, 6);
      await moveTo(nodes.cpu, above, 1.4);
      if (!alive()) return;
      await Promise.all([pulse(ringCpuTri, 2), pulse(ringSockTri, 2)]);
      if (!alive()) return;
      await moveTo(nodes.cpu, HOME.cpu, 0.9, ease.out);
      if (!alive()) return;
      await animate(() => plate.rotation.y, (v) => { plate.rotation.y = v; }, 0, 0.8);
      if (!alive()) return;
      await animate(() => lever.rotation.y, (v) => { lever.rotation.y = v; }, 0, 0.6);
    },
    async 3(alive) {
      await camTo(3);
      if (!alive()) return;
      const latches = ['A2', 'B2'].map((kk) => mbPiv[`dimm_latch_${kk}`]).filter(Boolean);
      await Promise.all(latches.map((l) => animate(() => l.rotation.x, (v) => { l.rotation.x = v; }, D2R(-32), 0.5)));
      if (!alive()) return;
      await Promise.all([
        moveTo(nodes.ram0, offsetPose(HOME.ram0, 0, 0, 7), 1.3),
        moveTo(nodes.ram1, offsetPose(HOME.ram1, 0, 0, 7), 1.3, ease.inOut, 0.25),
      ]);
      if (!alive()) return;
      await Promise.all([moveTo(nodes.ram0, HOME.ram0, 0.7, ease.in), moveTo(nodes.ram1, HOME.ram1, 0.7, ease.in, 0.15)]);
      if (!alive()) return;
      await Promise.all([
        ...latches.map((l) => animate(() => l.rotation.x, (v) => { l.rotation.x = v; }, 0, 0.25, ease.outBack)),
        ...ringLatches.map((r) => pulse(r, 1, 0.45)),
      ]);
    },
    async 4(alive) {
      await camTo(4);
      if (!alive()) return;
      if (screwPiv) {
        await tweens.to({ duration: D(0.9), update: (x) => { screwPiv.position.z = screwHome.z + 1.6 * x; screwPiv.rotation.z = -x * Math.PI * 4; } });
        if (!alive()) return;
        await animate(() => screwPiv.position.x, (v) => { screwPiv.position.x = v; }, screwHome.x + 3.5, 0.5);
      }
      if (!alive()) return;
      const tilt = new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), D2R(-30));
      const hover = { p: HOME.ssd.p.clone().add(V(1.6, 0, 1.1)), q: tilt.clone() };
      await moveTo(nodes.ssd, hover, 1.3);
      if (!alive()) return;
      await moveTo(nodes.ssd, { p: HOME.ssd.p.clone(), q: tilt.clone() }, 0.6);
      if (!alive()) return;
      await moveTo(nodes.ssd, HOME.ssd, 0.7);
      if (!alive()) return;
      if (screwPiv) {
        await animate(() => screwPiv.position.x, (v) => { screwPiv.position.x = v; }, screwHome.x, 0.5);
        if (!alive()) return;
        await tweens.to({ duration: D(1.0), update: (x) => { screwPiv.position.z = screwHome.z + 1.6 * (1 - x); screwPiv.rotation.z = -(1 - x) * Math.PI * 4; } });
      }
    },
    async 5(alive) {
      await camTo(5);
      if (!alive()) return;
      blob.visible = true;
      blob.scale.set(0.01, 0.01, 0.01);
      await tweens.to({ duration: D(0.6), ease: ease.outBack, update: (x) => { blob.scale.set(x, x, 0.5 * x); } });
      if (!alive()) return;
      // le ventirad se soulève (dans le repère de la carte posée, +Z = vers le haut) :
      // on voit le film plastique sous sa base, qu'on retire
      const lifted = { p: TABLE.cooler.p.clone().add(V(0, 0, 9)), q: TABLE.cooler.q.clone() };
      await moveTo(nodes.cooler, lifted, 0.8);
      if (!alive()) return;
      await tweens.to({ duration: D(0.9), update: (x) => { filmGroup.position.x = 7 * x; filmMat.opacity = 0.55 * (1 - x); } });
      filmGroup.visible = false;
      if (!alive()) return;
      await moveTo(nodes.cooler, offsetPose(HOME.cooler, 0, 0, 12), 1.5);
      if (!alive()) return;
      await moveTo(nodes.cooler, HOME.cooler, 0.9, ease.out);
      if (!alive()) return;
      await tweens.to({ duration: D(0.4), update: (x) => { blob.scale.set(1 + x * 1.6, 1 + x * 1.6, 0.5 * (1 - 0.8 * x)); } });
      blob.visible = false;
    },
    async 6(alive) {
      await camTo(6, 1.4);
      if (!alive()) return;
      // les entretoises se vissent dans le plateau
      const stand = standoffHome.map((p, i) => casePiv[`standoff_${i + 1}`]).filter(Boolean);
      await Promise.all(stand.map((s, i) => {
        const p = standoffHome[i];
        s.position.z = p.z + 2.5;
        return tweens.to({ duration: D(0.6), delay: reduced ? 0 : i * 0.07, update: (x) => { s.position.z = p.z + 2.5 * (1 - x); s.rotation.z = x * Math.PI * 3; } });
      }));
      if (!alive()) return;
      // la carte mère quitte sa boîte, se redresse et entre dans le boîtier
      const lift = { p: POSE_BOX.p.clone().add(V(0, 16, 0)), q: POSE_BOX.q.clone() };
      await moveTo(mbg, lift, 1.0);
      if (!alive()) return;
      const front = { p: HOME.mbg.p.clone().add(V(0, 2, 26)), q: HOME.mbg.q.clone() };
      await moveTo(mbg, front, 1.6);
      if (!alive()) return;
      await moveTo(mbg, offsetPose(HOME.mbg, -0.6, 0.6, 0), 1.0);
      if (!alive()) return;
      await moveTo(mbg, HOME.mbg, 0.5, ease.out);
      if (!alive()) return;
      mbScrews.forEach((s) => { s.visible = true; s.position.z = MB.anchor_hole_1.z + 2.8; });
      await Promise.all(mbScrews.map((s, i) => tweens.to({
        duration: D(0.5), delay: reduced ? 0 : i * 0.08, ease: ease.out,
        update: (x) => { s.position.z = MB.anchor_hole_1.z + 0.28 + 2.5 * (1 - x); s.rotation.z = x * 8; },
      })));
    },
    async 7(alive) {
      await camTo(7);
      if (!alive()) return;
      const behind = { p: HOME.psu.p.clone().add(V(-30, 2, 0)), q: HOME.psu.q.clone() };
      const up = { p: TABLE.psu.p.clone().add(V(0, 20, 0)), q: TABLE.psu.q.clone() };
      await moveTo(nodes.psu, up, 0.8);
      if (!alive()) return;
      await moveTo(nodes.psu, { p: V(behind.p.x, 30, behind.p.z), q: behind.q }, 1.4);
      if (!alive()) return;
      await moveTo(nodes.psu, behind, 0.7);
      if (psuPiv.psu_fixed_cables) psuPiv.psu_fixed_cables.visible = false;
      if (!alive()) return;
      await moveTo(nodes.psu, HOME.psu, 1.3, ease.out);
      if (!alive()) return;
      // gros plan sur l'arrière : prise secteur et interrupteur (laissé sur O)
      await camTo('psu', 1.4);
    },
    async 8(alive) {
      await camTo(8);
      if (!alive()) return;
      for (const name of STEP8_CABLES) {
        const c = cables[name];
        await animate(() => c.progress, (v) => c.setProgress(v), 1, name === 'atx24' || name === 'eps8' ? 1.3 : 0.9, ease.inOut);
        if (!alive()) return;
      }
    },
    async 9(alive) {
      await camTo(9);
      if (!alive()) return;
      const covers = ['slot_cover_2', 'slot_cover_3'].map((n) => casePiv[n]).filter(Boolean);
      await Promise.all(covers.map((c, i) => animate(() => c.position.x, (v) => { c.position.x = v; }, coverHome[i].x - 6, 0.7, ease.in, i * 0.15)));
      covers.forEach((c) => { c.visible = false; });
      if (!alive()) return;
      const latch = mbPiv.pcie_x16_latch;
      if (latch) await animate(() => latch.rotation.y, (v) => { latch.rotation.y = v; }, D2R(28), 0.4);
      if (!alive()) return;
      gpuScrew.visible = false;
      await moveTo(nodes.gpu, { p: TABLE.gpu.p.clone().add(V(0, 22, 0)), q: TABLE.gpu.q }, 0.8);
      if (!alive()) return;
      await moveTo(nodes.gpu, offsetPose(HOME.gpu, 0, 0, 20), 1.4);
      if (!alive()) return;
      // la caméra se rapproche pendant que la carte entre dans le slot
      await Promise.all([moveTo(nodes.gpu, HOME.gpu, 1.0, ease.inOut), camTo('gpu', 1.1)]);
      if (!alive()) return;
      if (latch) await animate(() => latch.rotation.y, (v) => { latch.rotation.y = v; }, 0, 0.25, ease.outBack);
      gpuScrew.visible = true;
      const sz = gpuScrew.position.z;
      gpuScrew.position.z = sz + 2.5;
      await tweens.to({ duration: D(0.6), ease: ease.out, update: (x) => { gpuScrew.position.z = sz + 2.5 * (1 - x); gpuScrew.rotation.z = x * 8; } });
      if (!alive()) return;
      await animate(() => cables.pcie.progress, (v) => cables.pcie.setProgress(v), 1, 1.3);
    },
    async 10(alive) {
      // on ouvre le panneau droit pour travailler derrière le plateau
      await camTo(10, 1.6);
      if (!alive()) return;
      const panel = casePiv.case_panel_right;
      if (panel) {
        await animate(() => panel.position.z, (v) => { panel.position.z = v; }, panelHome.z - 30, 0.9, ease.in);
        panel.visible = false;
      }
      if (!alive()) return;
      await tweens.to({ duration: D(2.2), update: (x) => { for (const c of Object.values(cables)) c.setMix(x); } });
      if (!alive()) return;
      straps.forEach((s) => { s.visible = true; s.scale.setScalar(0.01); });
      await Promise.all(straps.map((s, i) => tweens.to({ duration: D(0.4), delay: reduced ? 0 : i * 0.15, ease: ease.outBack, update: (x) => s.scale.setScalar(Math.max(0.01, x)) })));
      if (!alive()) return;
      await tweens.wait(D(0.6));
      if (panel) {
        panel.visible = true;
        await animate(() => panel.position.z, (v) => { panel.position.z = v; }, panelHome.z, 0.9, ease.out);
      }
      if (!alive()) return;
      await camTo(8, 1.6);
    },
    async 11(alive) {
      // on range la boîte de la carte mère pendant que la caméra recule
      await Promise.all([
        camTo(11, 1.4),
        animate(() => boxGroup.position.x, (v) => { boxGroup.position.x = v; }, -75, 1.1, ease.in),
      ]);
      boxGroup.visible = false;
      if (!alive()) return;
      const glass = casePiv.case_glass;
      monitor.visible = true;
      if (glass) {
        glass.visible = true;
        glass.position.z = glassHome.z + 30;
        await animate(() => glass.position.z, (v) => { glass.position.z = v; }, glassHome.z, 1.1, ease.out);
      }
      if (!alive()) return;
      const sw = psuPiv.psu_switch;
      if (sw) await animate(() => sw.rotation.z, (v) => { sw.rotation.z = v; }, D2R(-10), 0.3);
      if (!alive()) return;
      const btn = casePiv.case_power_button;
      if (btn) {
        await animate(() => btn.position.y, (v) => { btn.position.y = v; }, btnHome.y - 0.15, 0.15);
        await animate(() => btn.position.y, (v) => { btn.position.y = v; }, btnHome.y, 0.2);
      }
      if (!alive()) return;
      setPower(true);
      await animate(() => fanSpeed, (v) => { fanSpeed = v; }, 1.0, 1.4, ease.in);
      if (!alive()) return;
      // séquence des LED de diagnostic (la mémoire est la plus longue : entraînement DDR5)
      const durations = [0.5, 1.8, 0.5, 0.5];
      for (let i = 0; i < leds.length; i++) {
        leds[i].material.emissiveIntensity = 3;
        await tweens.wait(D(durations[i]));
        leds[i].material.emissiveIntensity = 0;
        if (!alive()) return;
      }
      await animate(() => 0, (v) => { screenMat.color.setScalar(v); }, 1, 0.8);
    },
  };

  // ------------------------------------------------------------------ boucle
  stage.fitLights(new THREE.Box3(V(-50, 0, -30), V(70, 50, 62)));
  applyState(stepsUI ? stepsUI.current - 1 : 0);
  const v0 = view(stepsUI ? stepsUI.current : 1);
  camera.position.copy(v0.pos);
  controls.target.copy(v0.target);
  controls.update();

  const unsubscribe = stepsUI ? stepsUI.subscribe((k) => play(k)) : () => {};
  let running = false;
  let raf = 0;
  let last = 0;
  let firstStart = true;
  function frame(tms) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    const t = tms / 1000;
    const dt = Math.min(0.05, last ? t - last : 0.016);
    last = t;
    tweens.update(t);
    controls.update(dt);
    if (fanSpeed > 0) pc.spin(dt, fanSpeed * (reduced ? 0.2 : 1.2));
    stage.render();
  }

  return {
    start() {
      if (running) return;
      running = true;
      last = 0;
      raf = requestAnimationFrame(frame);
      if (firstStart) {
        firstStart = false;
        play(stepsUI ? stepsUI.current : 1);
      }
    },
    stop() { running = false; cancelAnimationFrame(raf); },
    dispose() {
      this.stop();
      token += 1;
      tweens.cancelAll();
      unsubscribe();
      document.removeEventListener('pc-builder:theme', applyTheme);
      Object.values(cables).forEach((c) => c.dispose());
      for (const d of disposables) d.dispose?.();
      for (const m of pc.materials) m.dispose();
      stage.dispose();
    },
  };
}

/** Image affichée par l'écran au premier démarrage (dessinée dans un canvas 2D). */
function makeScreenTexture() {
  const c = document.createElement('canvas');
  c.width = 1024;
  c.height = 576;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, 576);
  grad.addColorStop(0, '#0a1633');
  grad.addColorStop(1, '#081027');
  g.fillStyle = grad;
  g.fillRect(0, 0, 1024, 576);
  g.fillStyle = '#0f2350';
  g.fillRect(0, 0, 1024, 64);
  g.fillStyle = '#ffffff';
  g.font = 'bold 30px system-ui, sans-serif';
  g.fillText(L('UEFI BIOS Utility · Mode simplifié', 'UEFI BIOS Utility · EZ Mode'), 30, 43);
  const rows = [
    [L('Processeur', 'Processor'), L('8 cœurs · 38 °C', '8 cores · 38 °C')],
    [L('Mémoire', 'Memory'), L('32 Go DDR5 (A2 + B2)', '32 GB DDR5 (A2 + B2)')],
    [L('Stockage', 'Storage'), L('SSD NVMe 1 To (M.2_1)', '1 TB NVMe SSD (M.2_1)')],
    [L('Carte graphique', 'Graphics card'), L('PCIe x16 détectée', 'PCIe x16 detected')],
    [L('Ventilateurs', 'Fans'), L('CPU_FAN 820 tr/min', 'CPU_FAN 820 RPM')],
  ];
  g.font = '28px system-ui, sans-serif';
  rows.forEach(([k, v], i) => {
    const y = 130 + i * 70;
    g.fillStyle = 'rgba(22,48,108,0.45)';
    g.fillRect(30, y - 40, 964, 56);
    g.fillStyle = '#9fb6ff';
    g.fillText(k, 54, y);
    g.fillStyle = '#6ee7b7';
    g.fillText(v, 470, y);
  });
  g.fillStyle = '#22d3ee';
  g.font = 'bold 26px system-ui, sans-serif';
  g.fillText(L('Tout est détecté : appuyez sur F10 pour enregistrer.', 'Everything detected. Press F10 to save.'), 30, 545);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
