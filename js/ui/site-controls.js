/**
 * site-controls.js : bouton clair/sombre et menu des langues (en haut à droite).
 *
 * - Le thème est appliqué très tôt par js/prefs.js ; ici on gère seulement le bouton.
 *   Un changement de thème émet l'événement « pc-builder:theme » sur document, écouté par
 *   les scènes 3D qui ont des couleurs propres (l'établi du montage par exemple).
 * - Le menu des langues est un simple <details> avec des liens : il marche sans JavaScript.
 *   Le script mémorise le choix et garde la section en cours (#ancre) en changeant de langue.
 */
import { t } from '../i18n.js';

const THEME_KEY = 'pc-builder:theme';
const LANG_KEY = 'pc-builder:lang';

function store(key, value) {
  try { localStorage.setItem(key, value); } catch { /* stockage indisponible : choix non mémorisé */ }
}
function read(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

export function initSiteControls() {
  const root = document.documentElement;

  // ------------------------------------------------------------------ thème
  const btn = document.getElementById('theme-toggle');
  const meta = document.querySelector('meta[name="theme-color"]');
  const apply = (theme, persist) => {
    root.setAttribute('data-theme', theme);
    if (persist) store(THEME_KEY, theme);
    if (btn) {
      const toLight = theme === 'dark';
      btn.setAttribute('aria-label', toLight ? t('themeToLight') : t('themeToDark'));
      btn.title = btn.getAttribute('aria-label');
      btn.setAttribute('aria-pressed', String(theme === 'light'));
    }
    if (meta) meta.setAttribute('content', theme === 'light' ? '#f6f7f9' : '#111317');
    document.dispatchEvent(new CustomEvent('pc-builder:theme', { detail: { theme } }));
  };
  apply(root.getAttribute('data-theme') === 'light' ? 'light' : 'dark', false);
  btn?.addEventListener('click', () => apply(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light', true));
  // sans choix enregistré, on suit le réglage du système s'il change
  const media = window.matchMedia('(prefers-color-scheme: light)');
  media.addEventListener?.('change', (e) => { if (!read(THEME_KEY)) apply(e.matches ? 'light' : 'dark', false); });

  // ------------------------------------------------------------------ langues
  const menu = document.getElementById('lang-menu');
  if (!menu) return;
  menu.querySelectorAll('a[hreflang]').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      store(LANG_KEY, a.getAttribute('hreflang'));
      const url = new URL(a.getAttribute('href'), location.href);
      url.hash = location.hash;
      location.href = url.href;
    });
  });
  // fermeture au clic à côté ou avec Échap
  document.addEventListener('click', (e) => { if (menu.open && !menu.contains(e.target)) menu.open = false; });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary')?.focus(); } });
}
