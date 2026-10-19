/**
 * anim.js : Mini-moteur d'animations (interpolations dans le temps), sans dépendance.
 *
 *   const tw = new Tweens();
 *   await tw.to({ duration: 0.8, delay: 0.2, ease: ease.inOut, update: (k) => { ... } });
 *   // dans la boucle de rendu :
 *   tw.update(performance.now() / 1000);
 *
 * Chaque appel à `to()` renvoie une promesse : on peut scénariser des séquences avec
 * `await`. `cancelAll()` interrompt tout (les promesses en attente sont résolues).
 */
import { ease as E } from './stage.js';

export class Tweens {
  constructor() {
    this.items = [];
    this.now = performance.now() / 1000;
  }

  /**
   * @param {{duration?:number, delay?:number, ease?:(t:number)=>number,
   *   update:(k:number)=>void, done?:()=>void}} o
   * @returns {Promise<void>}
   */
  to(o) {
    return new Promise((resolve) => {
      this.items.push({
        start: performance.now() / 1000 + (o.delay || 0),
        duration: Math.max(0.0001, o.duration ?? 0.6),
        ease: o.ease || E.inOut,
        update: o.update,
        done: () => { if (o.done) o.done(); resolve(); },
      });
    });
  }

  /** Attend `seconds` (dans le temps de l'animation). */
  wait(seconds) {
    return this.to({ duration: seconds, update: () => {} });
  }

  /** Interrompt toutes les animations (leurs promesses sont résolues). */
  cancelAll() {
    const list = this.items;
    this.items = [];
    for (const it of list) it.done();
  }

  get busy() { return this.items.length > 0; }

  update(nowSeconds) {
    this.now = nowSeconds;
    if (!this.items.length) return;
    const list = this.items;
    this.items = []; // les animations créées pendant les callbacks iront ici
    for (const it of list) {
      if (nowSeconds < it.start) { this.items.push(it); continue; }
      const t = Math.min(1, (nowSeconds - it.start) / it.duration);
      it.update(it.ease(t));
      if (t >= 1) it.done();
      else this.items.push(it);
    }
  }
}

/** Interpolation linéaire de deux nombres. */
export const lerp = (a, b, t) => a + (b - a) * t;
