/**
 * main.js — Point d'entrée du site.
 *
 * 1. Initialise l'interface (navigation, infobulles, glossaire, checklist, BIOS, graphiques,
 *    panneau du montage). Chaque module est isolé : une erreur dans l'un ne casse pas les autres.
 * 2. Enregistre les visionneuses 3D auprès du gestionnaire de fenêtres d'affichage : elles ne
 *    sont créées (import dynamique du code + contexte WebGL) que lorsqu'elles deviennent visibles.
 */
import { initNav } from './ui/nav.js';
import { initTooltips } from './ui/tooltips.js';
import { initGlossary } from './ui/glossary.js';
import { initChecklist } from './ui/checklist.js';
import { initBios } from './ui/bios.js';
import { initCharts } from './ui/charts.js';
import { initStepsUI } from './ui/steps-ui.js';
import { ViewportManager } from './core/viewport-manager.js';
import { webglAvailable } from './core/stage.js';
import { preload } from './core/loader.js';

function safe(fn, name) {
  try {
    return fn();
  } catch (err) {
    console.error(`[pc-builder] Erreur dans le module « ${name} » :`, err);
    return null;
  }
}

safe(initNav, 'navigation');
safe(initTooltips, 'infobulles');
safe(initGlossary, 'glossaire');
safe(initChecklist, 'checklist');
safe(initBios, 'BIOS');
safe(initCharts, 'graphiques');
const stepsUI = safe(initStepsUI, 'montage');

const viewers = document.querySelectorAll('[data-viewer]');
if (!webglAvailable()) {
  viewers.forEach((el) => {
    el.classList.add('is-error');
    const status = el.querySelector('.viewer-status');
    if (status) status.textContent = 'La 3D n\'est pas disponible sur ce navigateur : image fixe affichée.';
  });
} else {
  const factories = {
    hero: (el) => import('./views/hero-view.js').then((m) => m.createHeroView(el)),
    part: (el) => import('./views/part-viewer.js').then((m) => m.createPartViewer(el)),
    exploded: (el) => import('./views/exploded-view.js').then((m) => m.createExplodedView(el)),
    assembly: (el) => import('./views/assembly-view.js').then((m) => m.createAssemblyView(el, stepsUI)),
  };
  const manager = new ViewportManager();
  viewers.forEach((el) => {
    const factory = factories[el.dataset.viewer];
    if (factory) manager.register(el, factory);
  });
  // les modèles sont légers (~1,2 Mo au total) : on les précharge pendant que la page s'affiche
  preload(['case', 'motherboard', 'cpu', 'cooler', 'ram', 'ssd', 'gpu', 'psu', 'fan']);
}
