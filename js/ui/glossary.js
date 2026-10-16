/**
 * glossary.js — Recherche instantanée dans le glossaire (insensible aux accents et à la casse).
 */
const normalize = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

export function initGlossary() {
  const input = document.getElementById('glossary-search');
  const list = document.getElementById('glossary');
  const empty = document.getElementById('glossary-empty');
  const count = document.getElementById('glossary-count');
  if (!input || !list) return;
  const items = [...list.querySelectorAll('.g-item')].map((el) => ({
    el,
    dt: el.querySelector('dt'),
    text: normalize(el.textContent),
    title: normalize(el.querySelector('dt').textContent),
    original: el.querySelector('dt').textContent,
  }));
  const total = items.length;

  function update() {
    const q = normalize(input.value.trim());
    let shown = 0;
    for (const it of items) {
      const match = !q || it.text.includes(q);
      it.el.hidden = !match;
      if (match) shown += 1;
      // surligne la partie du titre qui correspond
      if (q && it.title.includes(q)) {
        const i = it.title.indexOf(q);
        const o = it.original;
        it.dt.replaceChildren(document.createTextNode(o.slice(0, i)), Object.assign(document.createElement('mark'), { textContent: o.slice(i, i + q.length) }), document.createTextNode(o.slice(i + q.length)));
      } else {
        it.dt.textContent = it.original;
      }
    }
    empty.hidden = shown > 0;
    count.textContent = q ? `${shown} terme${shown > 1 ? 's' : ''} sur ${total}` : `${total} termes`;
  }
  input.addEventListener('input', update);
  update();
}
