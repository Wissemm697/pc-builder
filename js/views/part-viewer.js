/**
 * part-viewer.js — Visionneuse d'une pièce SEULE.
 *
 * - Rotation et zoom à la souris ou au doigt (OrbitControls), rotation automatique
 *   lente jusqu'à la première interaction.
 * - Repères numérotés (hotspots) qui suivent le modèle et se masquent quand on regarde
 *   l'autre face.
 * - Boutons spécifiques : retourner le CPU, ouvrir le socket, retirer la vitre…
 * Créée par viewport-manager.js uniquement quand elle devient visible.
 */
import * as THREE from 'three';
import { createStage, frameBox, ease, prefersReducedMotion, isCoarsePointer } from '../core/stage.js';
import { getPart, spinRotors } from '../core/loader.js';
import { Tweens } from '../core/anim.js';
import { PARTS } from '../data/parts.js';

const tmpV = new THREE.Vector3();
const tmpN = new THREE.Vector3();
const tmpC = new THREE.Vector3();

export async function createPartViewer(el) {
  const initial = el.dataset.part;
  const stage = createStage(el, { fov: 30 });
  const { scene, camera, controls } = stage;
  const tweens = new Tweens();
  const holder = new THREE.Group();      // groupe retourné par le bouton « voir le dessous »
  scene.add(holder);

  /** @type {{name:string, conf:object, part:object, pres:THREE.Group, box:THREE.Box3}|null} */
  let current = null;
  let hotspotsOn = true;
  let hotItems = [];
  let running = false;
  let raf = 0;
  let last = 0;
  let needsFrame = true;

  controls.autoRotate = !prefersReducedMotion();
  controls.autoRotateSpeed = 1.2;
  const onStart = () => {
    controls.autoRotate = false;
    el.classList.add('has-interacted');
  };
  controls.addEventListener('start', onStart);

  // ---------------------------------------------------------------- interface (boutons, aide, repères)
  const ui = document.createElement('div');
  ui.className = 'viewer-ui';
  const hint = document.createElement('p');
  hint.className = 'viewer-hint';
  hint.textContent = isCoarsePointer() ? 'Glisser pour tourner · pincer pour zoomer' : 'Glisser pour tourner · molette pour zoomer';
  const hotLayer = document.createElement('div');
  hotLayer.className = 'hotspots';
  el.append(ui, hint, hotLayer);

  function button(label, onClick, pressed = null) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'vbtn';
    b.textContent = label;
    if (pressed !== null) b.setAttribute('aria-pressed', String(pressed));
    b.addEventListener('click', onClick);
    ui.append(b);
    return b;
  }

  const btnHot = button('Repères', () => {
    hotspotsOn = !hotspotsOn;
    btnHot.setAttribute('aria-pressed', String(hotspotsOn));
    hotLayer.hidden = !hotspotsOn;
    needsFrame = true;
  }, true);
  button('Recentrer', () => {
    if (current) frameBox(camera, controls, current.box, current.conf.view, 1.12);
    needsFrame = true;
  });

  // boutons propres à la pièce
  const actionButtons = [];
  function buildActions(conf) {
    actionButtons.forEach((b) => b.remove());
    actionButtons.length = 0;
    for (const a of (PARTS[initial].actions || [])) {
      let on = false;
      const b = button(a.label, () => {
        on = !on;
        b.textContent = on ? a.active : a.label;
        b.setAttribute('aria-pressed', String(on));
        runAction(a, on);
      }, false);
      actionButtons.push(b);
    }
    return conf;
  }

  function runAction(a, on) {
    if (!current) return;
    const pv = current.part.pivots;
    if (a.id === 'flip') {
      const from = holder.rotation.y;
      const to = on ? Math.PI : 0;
      tweens.to({ duration: 0.9, update: (k) => { holder.rotation.y = from + (to - from) * k; } });
    } else if (a.id === 'socket') {
      const lever = pv.socket_lever;
      const plate = pv.socket_loadplate;
      if (!lever || !plate) return;
      const L0 = lever.rotation.y;
      const P0 = plate.rotation.y;
      const L1 = on ? THREE.MathUtils.degToRad(-100) : 0;
      const P1 = on ? THREE.MathUtils.degToRad(-115) : 0;
      if (on) {
        tweens.to({ duration: 0.6, update: (k) => { lever.rotation.y = L0 + (L1 - L0) * k; } })
          .then(() => tweens.to({ duration: 0.8, update: (k) => { plate.rotation.y = P0 + (P1 - P0) * k; } }));
      } else {
        tweens.to({ duration: 0.8, update: (k) => { plate.rotation.y = P0 + (P1 - P0) * k; } })
          .then(() => tweens.to({ duration: 0.6, update: (k) => { lever.rotation.y = L0 + (L1 - L0) * k; } }));
      }
    } else if (a.id === 'swap') {
      show(on ? a.alt : initial);
    } else if (a.id === 'glass') {
      const g = pv.case_glass;
      if (!g) return;
      const z0 = g.position.z;
      const base = g.userData.baseZ ?? (g.userData.baseZ = z0);
      if (!on) g.visible = true;
      const z1 = on ? base + 30 : base;
      tweens.to({ duration: 0.9, update: (k) => { g.position.z = z0 + (z1 - z0) * k; }, done: () => { if (on) g.visible = false; } });
    }
    needsFrame = true;
  }

  // ---------------------------------------------------------------- repères
  function buildHotspots(list) {
    hotLayer.replaceChildren();
    hotItems = (list || []).map((h, i) => {
      const wrap = document.createElement('div');
      wrap.className = 'hotspot is-hidden';
      const dot = document.createElement('button');
      dot.type = 'button';
      dot.className = 'hotspot-dot';
      dot.textContent = String(i + 1);
      dot.setAttribute('aria-label', `${h.t} : ${h.d}`);
      const lab = document.createElement('div');
      lab.className = 'hotspot-label';
      lab.innerHTML = `<strong></strong><span></span>`;
      lab.querySelector('strong').textContent = h.t;
      lab.querySelector('span').textContent = h.d;
      dot.addEventListener('click', (e) => {
        e.stopPropagation();
        const open = !wrap.classList.contains('is-open');
        hotItems.forEach((it) => it.el.classList.remove('is-open'));
        wrap.classList.toggle('is-open', open);
      });
      wrap.append(dot, lab);
      hotLayer.append(wrap);
      return { el: wrap, p: new THREE.Vector3().fromArray(h.p), n: new THREE.Vector3().fromArray(h.n).normalize() };
    });
  }
  el.addEventListener('pointerdown', () => hotItems.forEach((it) => it.el.classList.remove('is-open')));

  function updateHotspots() {
    if (!current || !hotspotsOn || !hotItems.length) return;
    const { width, height } = stage.size;
    const root = current.part.root;
    const m = root.matrixWorld;
    const nm = new THREE.Matrix3().getNormalMatrix(m);
    for (const it of hotItems) {
      tmpV.copy(it.p).applyMatrix4(m);
      tmpN.copy(it.n).applyMatrix3(nm).normalize();
      tmpC.copy(camera.position).sub(tmpV).normalize();
      const facing = tmpN.dot(tmpC) > 0.05;
      tmpV.project(camera);
      const inView = tmpV.z < 1 && Math.abs(tmpV.x) < 1.05 && Math.abs(tmpV.y) < 1.05;
      const show = facing && inView;
      it.el.classList.toggle('is-hidden', !show);
      if (show) {
        const x = (tmpV.x * 0.5 + 0.5) * width;
        const y = (-tmpV.y * 0.5 + 0.5) * height;
        it.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -50%)`;
      }
    }
  }

  // ---------------------------------------------------------------- affichage d'une pièce
  async function show(name) {
    const conf = PARTS[name];
    const part = await getPart(name);
    if (current) {
      holder.remove(current.pres);
    }
    holder.rotation.set(0, 0, 0);
    const pres = new THREE.Group();
    pres.add(part.root);
    if (conf.basis) {
      const [a, b, c] = conf.basis.map((v) => new THREE.Vector3().fromArray(v));
      pres.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(a, b, c));
    }
    holder.add(pres);
    holder.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(pres);
    pres.position.sub(box.getCenter(new THREE.Vector3()));
    holder.updateMatrixWorld(true);
    box.setFromObject(pres);
    stage.fitLights(box);
    frameBox(camera, controls, box, conf.view, 1.12);
    current = { name, conf, part, pres, box };
    buildHotspots(conf.hotspots);
    el.querySelector('.viewer-fallback-note')?.remove();
    if (part.fallback) {
      const note = document.createElement('p');
      note.className = 'viewer-fallback-note';
      note.textContent = 'Modèle simplifié (fichier 3D indisponible)';
      el.append(note);
    }
    needsFrame = true;
  }

  // ---------------------------------------------------------------- boucle de rendu
  function frame(tms) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    const t = tms / 1000;
    const dt = Math.min(0.05, last ? t - last : 0.016);
    last = t;
    tweens.update(t);
    const moved = controls.update(dt);
    const spinning = current && current.part.rotors.length > 0;
    if (spinning) spinRotors(current.part.rotors, dt, 0.5);
    if (moved || spinning || tweens.busy || controls.autoRotate || needsFrame) {
      stage.render();
      updateHotspots();
      needsFrame = false;
    }
  }

  buildActions(PARTS[initial]);
  await show(initial);

  return {
    start() {
      if (running) return;
      running = true;
      last = 0;
      needsFrame = true;
      raf = requestAnimationFrame(frame);
    },
    stop() {
      running = false;
      cancelAnimationFrame(raf);
    },
    dispose() {
      this.stop();
      tweens.cancelAll();
      controls.removeEventListener('start', onStart);
      stage.dispose();
      ui.remove();
      hint.remove();
      hotLayer.remove();
      el.querySelector('.viewer-fallback-note')?.remove();
      el.classList.remove('has-interacted');
    },
  };
}
