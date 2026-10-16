/**
 * scroll.js — Défilement vers une section, avec repli : si le défilement doux n'a pas
 * démarré (certains navigateurs ou réglages le désactivent), on saute directement.
 */
export function scrollToId(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const y0 = window.scrollY;
  el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  if (!reduce) {
    setTimeout(() => {
      const stillThere = Math.abs(window.scrollY - y0) < 2;
      const notArrived = Math.abs(el.getBoundingClientRect().top) > 120;
      if (stillThere && notArrived) el.scrollIntoView({ behavior: 'auto', block: 'start' });
    }, 450);
  }
}
