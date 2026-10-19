/**
 * hero-view.js : Le PC complet assemblé, qui tourne lentement (section d'accueil).
 * On peut aussi le faire tourner à la souris ou au doigt (sans zoom, pour ne pas gêner
 * le défilement de la page).
 */
import * as THREE from 'three';
import { createStage, frameBox, prefersReducedMotion } from '../core/stage.js';
import { buildPC } from '../core/pc-rig.js';

export async function createHeroView(el) {
  const stage = createStage(el, { fov: 28, maxDpr: 1.5 });
  const { scene, camera, controls } = stage;
  const pc = await buildPC();
  scene.add(pc.rig);

  const box = pc.caseBox();
  stage.fitLights(box);
  frameBox(camera, controls, box, [0.62, 0.32, 1], 1.02);
  controls.enableZoom = false;
  controls.minPolarAngle = THREE.MathUtils.degToRad(55);
  controls.maxPolarAngle = THREE.MathUtils.degToRad(95);
  controls.autoRotate = !prefersReducedMotion();
  controls.autoRotateSpeed = 1.1;
  const onStart = () => el.classList.add('has-interacted');
  controls.addEventListener('start', onStart);

  let running = false;
  let raf = 0;
  let last = 0;
  function frame(tms) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    const t = tms / 1000;
    const dt = Math.min(0.05, last ? t - last : 0.016);
    last = t;
    controls.update(dt);
    if (!prefersReducedMotion()) pc.spin(dt, 0.9);
    stage.render();
  }

  return {
    start() { if (!running) { running = true; last = 0; raf = requestAnimationFrame(frame); } },
    stop() { running = false; cancelAnimationFrame(raf); },
    dispose() {
      this.stop();
      controls.removeEventListener('start', onStart);
      stage.dispose();
    },
  };
}
