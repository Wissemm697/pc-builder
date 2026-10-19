/**
 * nav.js : Navigation fixe : sommaire (panneau latéral), section active,
 * barre de progression de lecture et nom de la section courante.
 */
export function initNav() {
  const toc = document.getElementById('toc');
  const toggle = document.getElementById('toc-toggle');
  const bar = document.getElementById('reading-progress-bar');
  const current = document.getElementById('topbar-current');
  const links = [...toc.querySelectorAll('a[href^="#"]')];
  const sections = links
    .map((a) => document.getElementById(a.getAttribute('href').slice(1)))
    .filter(Boolean);

  // ouverture / fermeture du sommaire (mobile et tablette)
  const setOpen = (open) => {
    toc.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
  };
  toggle.addEventListener('click', () => setOpen(!toc.classList.contains('is-open')));
  links.forEach((a) => a.addEventListener('click', () => setOpen(false)));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
  document.addEventListener('click', (e) => {
    if (toc.classList.contains('is-open') && !toc.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
  });

  // section active : la dernière dont le haut est passé sous la barre de navigation
  let ticking = false;
  function update() {
    ticking = false;
    const doc = document.documentElement;
    const max = doc.scrollHeight - window.innerHeight;
    const ratio = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
    bar.style.transform = `scaleX(${ratio.toFixed(4)})`;
    const line = 120;
    let active = sections[0];
    for (const s of sections) {
      if (s.getBoundingClientRect().top - line <= 0) active = s;
    }
    if (window.innerHeight + window.scrollY >= doc.scrollHeight - 4) active = sections[sections.length - 1];
    links.forEach((a) => {
      const on = a.getAttribute('href') === `#${active.id}`;
      a.classList.toggle('is-active', on);
      if (on) {
        a.setAttribute('aria-current', 'true');
        if (current) current.textContent = a.textContent;
      } else {
        a.removeAttribute('aria-current');
      }
    });
  }
  const onScroll = () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  update();
}
