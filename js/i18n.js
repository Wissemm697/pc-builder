/**
 * i18n.js : textes affichés par le JavaScript, en français et en anglais.
 *
 * Le contenu de la page est écrit directement dans chaque version HTML (index.html pour le
 * français, en/index.html pour l'anglais). Ce module ne gère que les quelques textes créés
 * par le code : boutons des visionneuses, BIOS simulé, graphiques, étapes du montage…
 *
 * Ajouter une langue (par exemple l'espagnol) : créer es/index.html (copie traduite de
 * en/index.html), ajouter un bloc « es » ici, un troisième texte à chaque appel L(…) de data/parts.js, puis ajouter la langue à
 * la liste LANGUAGES et aux balises <link rel="alternate"> de chaque page.
 */
export const LANGUAGES = [
  { code: 'fr', name: 'Français' },
  { code: 'en', name: 'English' },
];

const pageLang = (document.documentElement.lang || 'fr').slice(0, 2);
export const LANG = LANGUAGES.some((l) => l.code === pageLang) ? pageLang : 'fr';
export const LOCALE = LANG === 'en' ? 'en-GB' : 'fr-FR';

/** Choisit le texte de la langue courante, dans l'ordre de LANGUAGES : L('texte FR', 'English text'). */
const LANG_INDEX = LANGUAGES.findIndex((l) => l.code === LANG);
export const L = (...texts) => texts[LANG_INDEX] ?? texts[0];

const STRINGS = {
  fr: {
    // général
    moduleError: 'Erreur dans le module',
    noWebgl: 'La 3D n\'est pas disponible sur ce navigateur : image fixe affichée.',
    viewerFailed: 'La 3D n\'a pas pu démarrer : image fixe affichée.',
    fallbackNote: 'Modèle simplifié (fichier 3D indisponible)',
    // visionneuses
    hintTouch: 'Glisser pour tourner · pincer pour zoomer',
    hintMouse: 'Glisser pour tourner · molette pour zoomer',
    hotspots: 'Repères',
    recenter: 'Recentrer',
    // vue éclatée
    explode: 'Éclater',
    assemble: 'Assembler',
    clickToOpen: 'cliquer : voir la fiche',
    front: 'avant',
    rear: 'arrière',
    // montage
    step: 'Étape',
    nextStep: 'Étape suivante →',
    restart: 'Recommencer ↺',
    // thème et langue
    themeToLight: 'Passer au thème clair',
    themeToDark: 'Passer au thème sombre',
    language: 'Langue',
    // glossaire
    terms: (n) => `${n} termes`,
    termsOf: (n, total) => `${n} terme${n > 1 ? 's' : ''} sur ${total}`,
    // graphiques
    seeTable: 'Voir les valeurs en tableau',
  },
  en: {
    moduleError: 'Error in module',
    noWebgl: '3D isn\'t available in this browser, so a still image is shown instead.',
    viewerFailed: 'The 3D view couldn\'t start, so a still image is shown instead.',
    fallbackNote: 'Simplified model (3D file unavailable)',
    hintTouch: 'Drag to rotate · pinch to zoom',
    hintMouse: 'Drag to rotate · scroll to zoom',
    hotspots: 'Labels',
    recenter: 'Reset view',
    explode: 'Explode',
    assemble: 'Assemble',
    clickToOpen: 'click to open its page',
    front: 'front',
    rear: 'rear',
    step: 'Step',
    nextStep: 'Next step →',
    restart: 'Start again ↺',
    themeToLight: 'Switch to light theme',
    themeToDark: 'Switch to dark theme',
    language: 'Language',
    terms: (n) => `${n} terms`,
    termsOf: (n, total) => `${n} of ${total} term${total > 1 ? 's' : ''}`,
    seeTable: 'Show the values as a table',
  },
};

/** Texte traduit pour une clé ; les entrées sous forme de fonction reçoivent les arguments. */
export function t(key, ...args) {
  const v = STRINGS[LANG][key] ?? STRINGS.fr[key] ?? key;
  return typeof v === 'function' ? v(...args) : v;
}
