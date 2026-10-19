# Sécurité

## Ce que fait le site (et ce qu'il ne fait pas)

- Le site est **entièrement statique** : pas de serveur applicatif, pas de base de données, pas de compte, pas de formulaire envoyé.
- **Aucune donnée personnelle n'est collectée** : pas de cookie, pas de mesure d'audience, pas de ressource chargée depuis un autre site (polices, scripts, images : tout est inclus dans le dépôt).
- Le navigateur garde seulement trois réglages, en local (`localStorage`) : l'état de la checklist, le thème (clair/sombre) et la langue choisie. Ils ne quittent jamais l'appareil.

## Protections en place

- **Politique de sécurité du contenu (CSP)** dans chaque page : seuls les fichiers du site peuvent être chargés. Le seul script écrit dans le HTML (l'importmap de three.js) est autorisé par son empreinte SHA-256. Après toute modification de l'importmap, lancer `python scripts/update-csp.py`.
- `'wasm-unsafe-eval'` est nécessaire au décodeur des modèles 3D (meshopt, un petit module WebAssembly). Aucun `eval` JavaScript n'est utilisé.
- Les textes affichés par le JavaScript sont insérés avec `textContent`, jamais comme du HTML venant de l'extérieur.
- Le serveur local `serve.py` n'écoute que sur l'ordinateur lui-même (sauf option `--lan`) et ajoute des en-têtes de sécurité (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`).
- Les fins de ligne sont fixées en LF (`.gitattributes`), pour que l'empreinte de la CSP reste valable sur tous les systèmes.

## Signaler un problème

Si tu trouves une faille de sécurité, merci de **ne pas ouvrir d'issue publique**. Utilise plutôt l'onglet **Security → Report a vulnerability** du dépôt GitHub (signalement privé). Pour tout le reste (erreur dans le contenu, bug d'affichage), une issue classique est parfaite.
