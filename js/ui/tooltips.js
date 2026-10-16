/**
 * tooltips.js — Définition des termes techniques au survol, au focus clavier ou au toucher.
 * Les définitions sont lues dans le glossaire (source unique) : <div id="g-xxx"><dt/><dd/></div>.
 */
export function initTooltips() {
  const tip = document.getElementById('term-tooltip');
  if (!tip) return;
  const terms = [...document.querySelectorAll('.term[data-g]')];
  let openFor = null;

  terms.forEach((t) => {
    t.setAttribute('tabindex', '0');
    t.setAttribute('role', 'button');
    t.setAttribute('aria-describedby', 'term-tooltip');
  });

  function show(el) {
    const item = document.getElementById(`g-${el.dataset.g}`);
    if (!item) return;
    const title = item.querySelector('dt')?.textContent || '';
    const def = item.querySelector('dd')?.textContent || '';
    tip.replaceChildren();
    const strong = document.createElement('strong');
    strong.textContent = title;
    tip.append(strong, document.createTextNode(def));
    tip.hidden = false;
    position(el);
    openFor = el;
  }
  function hide() {
    tip.hidden = true;
    openFor = null;
  }
  function position(el) {
    const r = el.getBoundingClientRect();
    const tw = tip.offsetWidth;
    const th = tip.offsetHeight;
    let x = r.left + r.width / 2 - tw / 2;
    x = Math.max(12, Math.min(window.innerWidth - tw - 12, x));
    let y = r.top - th - 10;
    if (y < 70) y = r.bottom + 10;
    tip.style.left = `${x}px`;
    tip.style.top = `${y}px`;
  }

  const fine = window.matchMedia('(hover: hover)').matches;
  terms.forEach((t) => {
    if (fine) {
      t.addEventListener('mouseenter', () => show(t));
      t.addEventListener('mouseleave', hide);
    }
    t.addEventListener('focus', () => show(t));
    t.addEventListener('blur', hide);
    t.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (openFor === t) hide();
      else show(t);
    });
    t.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { hide(); t.blur(); }
      if (e.key === 'Enter') {
        // Entrée : aller à la définition dans le glossaire
        const item = document.getElementById(`g-${t.dataset.g}`);
        if (item) {
          item.scrollIntoView({ block: 'center' });
          item.classList.add('is-flash');
          setTimeout(() => item.classList.remove('is-flash'), 1800);
        }
      }
    });
  });
  document.addEventListener('click', () => { if (openFor) hide(); });
  window.addEventListener('scroll', () => { if (openFor) position(openFor); }, { passive: true });
}
