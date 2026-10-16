/**
 * viewport-manager.js — Cycle de vie des visionneuses 3D.
 *
 * Les navigateurs limitent le nombre de contextes WebGL simultanés (souvent 16, parfois
 * beaucoup moins sur mobile). Ce module :
 *   1. n'initialise une visionneuse que lorsqu'elle approche de l'écran (IntersectionObserver) ;
 *   2. met en pause sa boucle de rendu quand elle sort de l'écran ;
 *   3. libère (détruit) les visionneuses hors écran au-delà d'un nombre maximal de contextes,
 *      ou après un certain temps hors écran ;
 *   4. met tout en pause quand l'onglet est caché.
 * Une visionneuse détruite est recréée à la demande : les modèles restent en cache (loader.js),
 * donc la recréation est rapide.
 */
import { isCoarsePointer } from './stage.js';

const MAX_ACTIVE = isCoarsePointer() ? 3 : 5;
const IDLE_DISPOSE_MS = 45000;

/**
 * @typedef {{start: Function, stop: Function, dispose: Function}} ViewerInstance
 * @typedef {{el: HTMLElement, factory: (el: HTMLElement) => Promise<ViewerInstance>,
 *   instance: ViewerInstance|null, creating: Promise|null, visible: boolean, lastSeen: number, timer: number}} Slot
 */

export class ViewportManager {
  constructor() {
    /** @type {Slot[]} */
    this.slots = [];
    this.observer = new IntersectionObserver((entries) => this.onIntersect(entries), {
      rootMargin: '160px 0px 160px 0px',
      threshold: [0, 0.01],
    });
    document.addEventListener('visibilitychange', () => {
      for (const s of this.slots) {
        if (!s.instance) continue;
        if (document.hidden) s.instance.stop();
        else if (s.visible) s.instance.start();
      }
    });
  }

  /** Enregistre une visionneuse : `factory(el)` crée l'instance (asynchrone). */
  register(el, factory) {
    const slot = { el, factory, instance: null, creating: null, visible: false, lastSeen: 0, timer: 0 };
    this.slots.push(slot);
    el.__viewerSlot = slot;
    this.observer.observe(el);
    return slot;
  }

  onIntersect(entries) {
    for (const entry of entries) {
      const slot = entry.target.__viewerSlot;
      if (!slot) continue;
      slot.visible = entry.isIntersecting;
      slot.lastSeen = performance.now();
      if (slot.visible) {
        clearTimeout(slot.timer);
        this.activate(slot);
      } else if (slot.instance) {
        slot.instance.stop();
        clearTimeout(slot.timer);
        slot.timer = setTimeout(() => {
          if (!slot.visible) this.release(slot);
        }, IDLE_DISPOSE_MS);
      }
    }
  }

  async activate(slot) {
    if (!slot.instance && !slot.creating) {
      this.enforceLimit(slot);
      slot.el.classList.add('is-loading');
      slot.creating = slot.factory(slot.el)
        .then((inst) => {
          slot.instance = inst;
          slot.el.classList.remove('is-loading');
          slot.el.classList.add('is-ready');
          if (slot.visible && !document.hidden) inst.start();
          return inst;
        })
        .catch((err) => {
          console.error('[pc-builder] Visionneuse 3D indisponible :', err);
          slot.el.classList.remove('is-loading');
          slot.el.classList.add('is-error');
          const status = slot.el.querySelector('.viewer-status');
          if (status) status.textContent = "La 3D n'a pas pu démarrer : image fixe affichée.";
        })
        .finally(() => { slot.creating = null; });
      return;
    }
    if (slot.instance && !document.hidden) slot.instance.start();
  }

  /** Si trop de contextes WebGL sont actifs, libère les visionneuses hors écran les plus anciennes. */
  enforceLimit(except) {
    const active = this.slots.filter((s) => s.instance || s.creating);
    if (active.length < MAX_ACTIVE) return;
    const candidates = active
      .filter((s) => s !== except && !s.visible && s.instance)
      .sort((a, b) => a.lastSeen - b.lastSeen);
    let excess = active.length - MAX_ACTIVE + 1;
    for (const s of candidates) {
      if (excess <= 0) break;
      this.release(s);
      excess -= 1;
    }
  }

  release(slot) {
    if (!slot.instance) return;
    try {
      slot.instance.dispose();
    } catch (err) {
      console.warn('[pc-builder] Erreur à la libération d\'une visionneuse', err);
    }
    slot.instance = null;
    slot.el.classList.remove('is-ready');
  }
}
