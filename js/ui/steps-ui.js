/**
 * steps-ui.js : Panneau du montage pas à pas (texte, pastilles d'étapes, boutons).
 *
 * Le contenu des étapes est écrit dans le HTML (#steps-source) : il reste lisible sans
 * JavaScript. Ce module l'affiche une étape à la fois et prévient la scène 3D (si elle est
 * chargée) à chaque changement d'étape. Il fonctionne même si la 3D est indisponible.
 */
import { t } from '../i18n.js';

export function initStepsUI() {
  const source = document.getElementById('steps-source');
  const content = document.getElementById('step-content');
  const dots = document.getElementById('step-dots');
  const count = document.getElementById('step-count');
  const prev = document.getElementById('step-prev');
  const next = document.getElementById('step-next');
  const replay = document.getElementById('step-replay');
  if (!source || !content || !dots) return null;

  const items = [...source.querySelectorAll(':scope > li[data-step]')];
  const total = items.length;
  source.classList.add('is-enhanced');
  let current = 1;
  let maxSeen = 1;
  const listeners = new Set();

  const dotEls = items.map((li, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'step-dot';
    b.setAttribute('role', 'tab');
    b.textContent = String(i + 1);
    const title = li.querySelector('h3')?.textContent || `${t('step')} ${i + 1}`;
    b.setAttribute('aria-label', `${t('step')} ${i + 1} : ${title}`);
    b.addEventListener('click', () => go(i + 1));
    dots.append(b);
    return b;
  });
  dots.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') { e.preventDefault(); go(Math.min(total, current + 1)); dotEls[current - 1].focus(); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(Math.max(1, current - 1)); dotEls[current - 1].focus(); }
  });

  function render() {
    const li = items[current - 1];
    content.replaceChildren(...[...li.childNodes].map((n) => n.cloneNode(true)));
    content.scrollTop = 0;
    count.textContent = `${t('step')} ${current} / ${total}`;
    dotEls.forEach((d, i) => {
      d.setAttribute('aria-selected', String(i + 1 === current));
      d.tabIndex = i + 1 === current ? 0 : -1;
      d.classList.toggle('is-done', i + 1 < current || i + 1 <= maxSeen - 1);
    });
    prev.disabled = current === 1;
    next.textContent = current === total ? t('restart') : t('nextStep');
  }

  function go(k, opts = {}) {
    current = Math.min(total, Math.max(1, k));
    maxSeen = Math.max(maxSeen, current);
    render();
    for (const fn of listeners) fn(current, opts);
  }

  prev.addEventListener('click', () => go(current - 1));
  next.addEventListener('click', () => go(current === total ? 1 : current + 1));
  replay.addEventListener('click', () => go(current, { replay: true }));
  render();

  return {
    get current() { return current; },
    total,
    go,
    /** Abonnement aux changements d'étape ; renvoie la fonction de désabonnement. */
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
