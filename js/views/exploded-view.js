/**
 * exploded-view.js : Vue éclatée interactive.
 *
 * - Un curseur fait passer de « éclaté » (0) à « assemblé » (100) ; chaque pièce rejoint sa
 *   place à son tour (ordre de montage), avec une animation amortie.
 * - Au survol, la pièce s'illumine et une étiquette affiche son nom ; au clic (ou au toucher),
 *   la page défile jusqu'à la section de la pièce.
 */
import * as THREE from 'three';
import { createStage, frameBox, ease, clamp01, prefersReducedMotion } from '../core/stage.js';
import { buildPC, findPartRoot } from '../core/pc-rig.js';
import { Tweens } from '../core/anim.js';
import { scrollToId } from '../ui/scroll.js';
import { t } from '../i18n.js';

const ACCENT = new THREE.Color(0x22d3ee);

export async function createExplodedView(el) {
  const stage = createStage(el, { fov: 30, maxDpr: 1.6 });
  const { scene, camera, controls, canvas } = stage;
  const tweens = new Tweens();
  const pc = await buildPC({ cloneMaterials: true });
  scene.add(pc.rig);
  const P = pc.parts;
  const glass = P.case.pivots.case_glass;
  const glassMats = [];
  glass?.traverse((o) => { if (o.isMesh) [].concat(o.material).forEach((m) => { if (m.userData.isGlass) glassMats.push(m); }); });
  const glassOpacity = glassMats[0]?.opacity ?? 0.2;

  // décalages (cm) de chaque pièce en position éclatée, et ordre d'arrivée au montage
  const EX = [
    { node: pc.mbGroup, off: [0, 0, 16], order: 0 },
    { node: P.cpu.root, off: [0, 0, 9], order: 1 },
    { node: P.ram[0].root, off: [0, 0, 11], order: 2 },
    { node: P.ram[1].root, off: [0, 0, 13], order: 2.3 },
    { node: P.ssd.root, off: [-1, -2.5, 8], order: 3 },
    { node: P.cooler.root, off: [0, 17, 20], order: 4 },
    { node: P.psu.root, off: [-20, -1, 14], order: 5 },
    { node: P.gpu.root, off: [14, -8, 28], order: 6 },
    { node: P.fans[0].root, off: [16, 0, 0], order: 7 },
    { node: P.fans[1].root, off: [16, 0, 0], order: 7.2 },
    { node: P.fans[2].root, off: [16, 0, 0], order: 7.4 },
    { node: P.fans[3].root, off: [-15, 0, 0], order: 7.6 },
  ];
  if (glass) EX.push({ node: glass, off: [0, 0, 34], order: 8.6, glass: true });
  const SPAN = 0.36;
  const maxOrder = Math.max(...EX.map((e) => e.order));
  for (const e of EX) {
    e.base = e.node.position.clone();
    e.offset = new THREE.Vector3().fromArray(e.off);
    e.start = (e.order / maxOrder) * (1 - SPAN);
  }

  let tShown = 0;       // valeur affichée (amortie)
  let tTarget = 0;      // valeur demandée par le curseur
  function apply(t) {
    for (const e of EX) {
      const k = ease.inOut(clamp01((t - e.start) / SPAN));
      e.node.position.copy(e.base).addScaledVector(e.offset, 1 - k);
      if (e.glass) {
        for (const m of glassMats) m.opacity = glassOpacity * k;
        e.node.visible = k > 0.02;
      }
    }
  }

  // cadrage : on calcule la boîte englobante de la position éclatée
  apply(0);
  pc.rig.updateMatrixWorld(true);
  const box = new THREE.Box3();
  for (const e of EX) if (!e.glass) box.expandByObject(e.node);
  box.expandByObject(P.case.root);
  stage.fitLights(box);
  frameBox(camera, controls, box, [0.5, 0.38, 1], 1.0);
  controls.maxDistance *= 1.2;

  // ---------------------------------------------------------------- curseur et bouton
  const range = document.getElementById('explode-range');
  const play = document.getElementById('explode-play');
  const playLabel = play?.querySelector('span');
  const setFill = () => range && range.style.setProperty('--fill', `${range.value}%`);
  const onInput = () => {
    tweens.cancelAll();
    tTarget = Number(range.value) / 100;
    setFill();
    syncPlayLabel();
  };
  function syncPlayLabel() {
    if (playLabel) playLabel.textContent = tTarget > 0.5 ? t('explode') : t('assemble');
  }
  const onPlay = () => {
    const from = tTarget;
    const to = from > 0.5 ? 0 : 1;
    tweens.cancelAll();
    tweens.to({
      duration: prefersReducedMotion() ? 0.01 : 3.2,
      ease: (x) => x,
      update: (k) => {
        tTarget = from + (to - from) * k;
        if (range) { range.value = String(Math.round(tTarget * 100)); setFill(); }
      },
    }).then(syncPlayLabel);
  };
  range?.addEventListener('input', onInput);
  play?.addEventListener('click', onPlay);
  if (range) { tTarget = Number(range.value) / 100; setFill(); }
  syncPlayLabel();

  // ---------------------------------------------------------------- survol et clic
  const label = document.createElement('div');
  label.className = 'pick-label';
  el.append(label);
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let pointerInside = false;
  let pointerDirty = false;
  let hovered = null;
  let downPos = null;
  const pickables = [];
  pc.rig.traverse((o) => {
    if (o.isMesh && !(Array.isArray(o.material) ? o.material : [o.material]).some((m) => m.userData.isGlass)) pickables.push(o);
  });
  const partMats = new Map();
  for (const part of pc.all) {
    const mats = new Set();
    part.root.traverse((o) => { if (o.isMesh) [].concat(o.material).forEach((m) => { if (!m.userData.isGlass && m.emissive) mats.add(m); }); });
    partMats.set(part.root, [...mats].map((m) => ({ m, emissive: m.emissive.clone(), intensity: m.emissiveIntensity })));
  }

  function setHover(root, clientX, clientY) {
    if (hovered !== root) {
      if (hovered) for (const it of partMats.get(hovered) || []) { it.m.emissive.copy(it.emissive); it.m.emissiveIntensity = it.intensity; }
      hovered = root;
      if (hovered) for (const it of partMats.get(hovered) || []) { it.m.emissive.copy(ACCENT); it.m.emissiveIntensity = 0.28; }
      canvas.style.cursor = hovered ? 'pointer' : 'grab';
    }
    if (hovered) {
      const r = el.getBoundingClientRect();
      const sub = hovered.userData.sub ? ` (${hovered.userData.sub})` : '';
      label.innerHTML = '';
      label.append(document.createTextNode(hovered.userData.label + sub));
      const small = document.createElement('small');
      small.textContent = t('clickToOpen');
      label.append(small);
      label.style.transform = `translate(${(clientX - r.left).toFixed(0)}px, ${(clientY - r.top).toFixed(0)}px) translate(-50%, calc(-100% - 14px))`;
      label.classList.add('is-visible');
    } else {
      label.classList.remove('is-visible');
    }
  }

  let lastClient = [0, 0];
  const onMove = (e) => {
    const r = canvas.getBoundingClientRect();
    pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    lastClient = [e.clientX, e.clientY];
    pointerInside = true;
    pointerDirty = true;
  };
  const onLeave = () => { pointerInside = false; setHover(null); };
  const onDown = (e) => { downPos = [e.clientX, e.clientY]; };
  const onUp = (e) => {
    if (!downPos) return;
    const moved = Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]);
    downPos = null;
    if (moved > 7) return;
    onMove(e);
    const hit = pick();
    if (hit && hit.userData.section) scrollToId(hit.userData.section);
  };
  canvas.addEventListener('pointermove', onMove);
  canvas.addEventListener('pointerleave', onLeave);
  canvas.addEventListener('pointerdown', onDown);
  canvas.addEventListener('pointerup', onUp);

  function pick() {
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(pickables, false);
    for (const h of hits) {
      if (!h.object.visible) continue;
      let vis = true;
      h.object.traverseAncestors((a) => { if (!a.visible) vis = false; });
      if (!vis) continue;
      return findPartRoot(h.object);
    }
    return null;
  }

  // ---------------------------------------------------------------- boucle
  let running = false;
  let raf = 0;
  let last = 0;
  function frame(tms) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    const t = tms / 1000;
    const dt = Math.min(0.05, last ? t - last : 0.016);
    last = t;
    tweens.update(t);
    tShown += (tTarget - tShown) * (1 - Math.exp(-dt * 7));
    if (Math.abs(tTarget - tShown) < 0.0005) tShown = tTarget;
    apply(tShown);
    controls.update(dt);
    pc.spin(dt, tShown > 0.98 && !prefersReducedMotion() ? 0.8 : 0.15);
    if (pointerInside && pointerDirty && !downPos) {
      pointerDirty = false;
      setHover(pick(), lastClient[0], lastClient[1]);
    }
    stage.render();
  }

  return {
    start() { if (!running) { running = true; last = 0; raf = requestAnimationFrame(frame); } },
    stop() { running = false; cancelAnimationFrame(raf); setHover(null); },
    dispose() {
      this.stop();
      tweens.cancelAll();
      range?.removeEventListener('input', onInput);
      play?.removeEventListener('click', onPlay);
      canvas.removeEventListener('pointermove', onMove);
      canvas.removeEventListener('pointerleave', onLeave);
      canvas.removeEventListener('pointerdown', onDown);
      canvas.removeEventListener('pointerup', onUp);
      label.remove();
      for (const m of pc.materials) m.dispose();
      stage.dispose();
    },
  };
}
