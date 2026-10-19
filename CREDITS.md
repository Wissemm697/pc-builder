# Crédits et licences

## Modèles 3D : 100 % faits maison

Les **9 modèles** du dossier `models/` sont des créations originales de ce projet. Aucun modèle n'a été téléchargé. Ils sont entièrement générés par les scripts Python Blender du dossier `scripts/blender/`, à partir de formes simples (boîtes, cylindres, profils, booléens) et de textures dessinées par le code (motifs de PCB, contacts dorés, grilles, étiquettes).

| Fichier | Pièce | Script source | Origine |
|---|---|---|---|
| `models/cpu.glb` | Processeur (format AM5, sans broches) | `scripts/blender/model_cpu.py` | création originale |
| `models/motherboard.glb` | Carte mère ATX (4 slots DDR5, 2 M.2, 1 PCIe x16) | `scripts/blender/model_motherboard.py` | création originale |
| `models/ram.glb` | Barrette DDR5 (DIMM) | `scripts/blender/model_ram.py` | création originale |
| `models/ssd.glb` | SSD NVMe M.2 2280 | `scripts/blender/model_ssd.py` | création originale |
| `models/cooler.glb` | Ventirad tour 120 mm | `scripts/blender/model_cooler.py` | création originale |
| `models/fan.glb` | Ventilateur 120 mm | `scripts/blender/model_fan.py` | création originale |
| `models/gpu.glb` | Carte graphique double ventilateur | `scripts/blender/model_gpu.py` | création originale |
| `models/psu.glb` | Alimentation ATX semi-modulaire | `scripts/blender/model_psu.py` | création originale |
| `models/case.glb` | Boîtier moyen tour ATX à vitre | `scripts/blender/model_case.py` | création originale |

Les textes gravés sur les modèles (« 1TB », « 750 W », « 80 PLUS GOLD », repères de la carte mère…) sont **génériques**. Aucun modèle ne reproduit un produit, une marque ou un logo réel.

Les images d'attente (`img/previews/*.webp`) sont des rendus de ces mêmes modèles, faits avec Blender (moteur Cycles).

## Ressources tierces

| Ressource | Utilisation | Auteur | Licence |
|---|---|---|---|
| [three.js](https://github.com/mrdoob/three.js) 0.160.0 (`js/vendor/three/`) : moteur, `OrbitControls`, `GLTFLoader`, `RoomEnvironment`, `BufferGeometryUtils` | Affichage 3D dans le navigateur | three.js authors | MIT (voir `js/vendor/three/LICENSE`) |
| [meshoptimizer](https://github.com/zeux/meshoptimizer), décodeur (`js/vendor/three/addons/libs/meshopt_decoder.module.js`) | Décompression des modèles dans le navigateur | Arseny Kapoulkine | MIT (mention en tête du fichier) |
| HDRI « Interior », livrée avec Blender (d'après [Hotel Room](https://polyhaven.com/a/hotel_room), Poly Haven) | Éclairage des rendus d'aperçu uniquement. Le fichier n'est pas inclus dans le site. | Greg Zaal (Poly Haven) | CC0 |

### Outils utilisés pour produire les fichiers (non inclus dans le site)

| Outil | Rôle | Licence |
|---|---|---|
| [Blender](https://www.blender.org) 5.2 (module Python `bpy`) | Modélisation, export glTF et rendus d'aperçu | GPL v3 (la licence ne s'applique pas aux fichiers produits) |
| [glTF Transform](https://gltf-transform.dev) 4.5 | Compression meshopt, nettoyage, textures WebP | MIT |
| [sharp](https://sharp.pixelplumbing.com) | Conversion des textures et des aperçus en WebP | Apache 2.0 |

## Polices et icônes

Il n'y a aucune police externe : le site utilise les polices déjà présentes sur l'appareil (`system-ui`, `ui-monospace`…). Les icônes et les schémas (connecteurs USB, HDMI, DisplayPort…) sont des SVG dessinés à la main directement dans les pages HTML (`index.html` et `en/index.html`).
