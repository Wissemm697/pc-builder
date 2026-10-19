/**
 * prefs.js : préférences d'affichage, chargé dans le <head> AVANT l'affichage de la page
 * (script classique, non différé) pour éviter un « flash » de mauvais thème.
 *
 * 1. Thème : clair ou sombre. Par défaut, celui du système ; le bouton de la barre du haut
 *    enregistre un choix explicite (localStorage, clé « pc-builder:theme »).
 * 2. Langue : si la personne a déjà choisi une langue, on l'envoie sur la bonne version.
 *    Lors d'une toute première visite sur la version française, un navigateur réglé
 *    uniquement dans d'autres langues est envoyé vers la version anglaise.
 *
 * Fichier externe (et non script intégré) pour respecter la politique de sécurité (CSP).
 */
(function () {
  var root = document.documentElement;
  function read(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // ------------------------------------------------------------------ thème
  var stored = read('pc-builder:theme');
  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;
  var theme = stored === 'light' || stored === 'dark' ? stored : (media && media.matches ? 'light' : 'dark');
  root.setAttribute('data-theme', theme);

  // ------------------------------------------------------------------ langue
  // chaque page déclare sa langue (lang="fr" / lang="en") et l'adresse des autres versions
  // dans <link rel="alternate" hreflang="…">
  var pageLang = (root.getAttribute('lang') || 'fr').slice(0, 2);
  var wanted = read('pc-builder:lang');
  if (!wanted && pageLang === 'fr') {
    var langs = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || 'fr'];
    var speaksFrench = false;
    for (var i = 0; i < langs.length; i++) {
      if (String(langs[i]).toLowerCase().indexOf('fr') === 0) speaksFrench = true;
    }
    if (!speaksFrench) wanted = 'en';
  }
  if (wanted && wanted !== pageLang) {
    var alt = document.querySelector('link[rel="alternate"][hreflang="' + wanted + '"]');
    if (alt) {
      var url = new URL(alt.getAttribute('href'), location.href);
      url.hash = location.hash;
      // signale à main.js de ne rien charger : la page est en train d'être remplacée
      window.__pcBuilderRedirect = true;
      location.replace(url.href);
    }
  }
})();
