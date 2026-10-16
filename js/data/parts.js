/**
 * parts.js — Configuration de chaque pièce pour les visionneuses et la vue éclatée.
 *
 * - label / section : nom affiché et section de la page correspondante
 * - basis  : orientation de PRÉSENTATION dans la visionneuse (images des axes x, y, z
 *            du modèle). Les modèles sont créés dans leur orientation « montée dans le PC » ;
 *            pour les montrer seuls, on en tourne certains (la RAM à plat, le ventirad debout…).
 * - view   : direction d'où regarde la caméra au départ
 * - hotspots : repères numérotés (positions en cm dans le repère du modèle, normale pour
 *            masquer un repère quand on regarde l'autre face)
 * - actions : boutons spécifiques de la visionneuse
 */
export const PARTS = {
  cpu: {
    label: 'Processeur',
    section: 'cpu',
    view: [0.5, 0.45, 1],
    hotspots: [
      { p: [0.6, 0.95, 0.5], n: [0, 0, 1], t: 'Capot (IHS)', d: 'Répartit la chaleur de la puce vers le ventirad.' },
      { p: [-1.8, -1.8, 0.13], n: [0, 0, 1], t: 'Triangle doré', d: 'À aligner avec le triangle du socket.' },
      { p: [1.55, 0.8, 0.16], n: [0, 0, 1], t: 'Condensateurs', d: 'Stabilisent l\'alimentation de la puce.' },
      { p: [0.9, -0.9, -0.01], n: [0, 0, -1], t: 'Pastilles dorées', d: 'Environ 1 700 contacts qui touchent les broches du socket.' },
      { p: [-0.7, 1.98, 0.06], n: [0, 1, 0.4], t: 'Substrat', d: 'Petit circuit vert qui relie la puce aux pastilles.' },
    ],
    actions: [{ id: 'flip', label: 'Voir le dessous', active: 'Voir le dessus' }],
  },
  motherboard: {
    label: 'Carte mère',
    section: 'carte-mere',
    view: [0.25, 0.15, 1],
    hotspots: [
      { p: [-3.5, 6.25, 0.62], n: [0, 0, 1], t: 'Socket AM5', d: 'Accueille le processeur. Ses broches sont très fragiles.' },
      { p: [-8.15, 4.8, 2.9], n: [0, 0, 1], t: 'VRM', d: 'Fabrique la tension du processeur, sous des dissipateurs.' },
      { p: [4.9, 9.5, 0.95], n: [0, 0, 1], t: 'Slots DDR5', d: 'A1, A2, B1, B2. Avec 2 barrettes : A2 et B2 (en gris clair).' },
      { p: [-6.15, -4.58, 1.35], n: [0, 0, 1], t: 'Slot PCIe x16', d: 'Pour la carte graphique, renforcé par du métal.' },
      { p: [-5.0, -1.6, 0.55], n: [0, 0, 1], t: 'Slot M.2_1', d: 'Pour le SSD NVMe, relié directement au processeur.' },
      { p: [-5.0, -10.6, 0.95], n: [0, 0, 1], t: 'Slot M.2_2', d: 'Second slot M.2, sous un dissipateur.' },
      { p: [5.8, -9.3, 1.2], n: [0, 0, 1], t: 'Chipset', d: 'Gère une partie des ports (USB, SATA, slots secondaires).' },
      { p: [11.1, 6.1, 1.25], n: [0, 0, 1], t: '24 broches ATX', d: 'Alimentation principale de la carte mère.' },
      { p: [-5.1, 14.0, 1.25], n: [0, 0, 1], t: '8 broches EPS', d: 'Alimentation du processeur (câble « CPU »).' },
      { p: [-12.7, 8.0, 3.2], n: [-1, 0, 0.6], t: 'Ports arrière (I/O)', d: 'USB, réseau, audio, boutons BIOS.' },
      { p: [11.7, -8.65, 1.35], n: [1, 0, 0.6], t: 'Ports SATA', d: 'Pour SSD 2,5" et disques durs.' },
      { p: [7.5, -14.35, 0.95], n: [0, 0, 1], t: 'F_PANEL', d: 'Bouton d\'allumage et LED du boîtier.' },
      { p: [-6.2, -7.0, 0.55], n: [0, 0, 1], t: 'Pile CMOS', d: 'Garde l\'heure et les réglages du BIOS.' },
      { p: [10.05, 9.55, 0.35], n: [0, 0, 1], t: 'LED de diagnostic', d: 'CPU, DRAM, VGA, BOOT : indiquent ce qui bloque au démarrage.' },
    ],
    actions: [{ id: 'socket', label: 'Ouvrir le socket', active: 'Fermer le socket' }],
  },
  ram: {
    label: 'Barrette DDR5 16 Go',
    section: 'ram',
    basis: [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
    view: [0.15, 0.3, 1],
    hotspots: [
      { p: [0.12, -4.1, 1.75], n: [1, 0, 0], t: 'Puces mémoire', d: '8 puces de 2 Go : 16 Go au total.' },
      { p: [0.12, 0, 1.25], n: [1, 0, 0], t: 'PMIC', d: 'Régulateur de tension embarqué, une nouveauté de la DDR5.' },
      { p: [0.08, -3.2, 0.16], n: [1, 0, 0], t: 'Contacts', d: '288 contacts dorés (144 par face).' },
      { p: [0.0, -0.35, 0.05], n: [1, 0, 0.2], t: 'Encoche', d: 'Détrompeur : impossible de l\'insérer à l\'envers ou dans un slot DDR4.' },
      { p: [0, 6.67, 1.75], n: [0, 1, 0], t: 'Encoche latérale', d: 'Le loquet du slot s\'y accroche (« clic »).' },
      { p: [-0.09, 0.2, 2.0], n: [-1, 0, 0], t: 'Étiquette', d: 'Capacité, génération et organisation des puces.' },
    ],
  },
  ssd: {
    label: 'SSD NVMe M.2',
    section: 'stockage',
    view: [0.2, 0.5, 1],
    hotspots: [
      { p: [1.62, 0, 0.22], n: [0, 0, 1], t: 'Contrôleur', d: 'Le cerveau du SSD : il répartit les données entre les puces.' },
      { p: [2.87, 0, 0.19], n: [0, 0, 1], t: 'Cache DRAM', d: 'Petite mémoire tampon qui accélère le SSD.' },
      { p: [5.4, 0.2, 0.24], n: [0, 0, 1], t: 'Mémoire flash NAND', d: 'Sous l\'étiquette : c\'est là que sont gardées les données.' },
      { p: [0.2, 0.45, 0.09], n: [0, 0, 1], t: 'Contacts + clé M', d: 'Se branchent dans le slot M.2 ; l\'encoche évite les erreurs.' },
      { p: [7.95, 0, 0.09], n: [0, 0, 1], t: 'Demi-lune', d: 'Passage de la petite vis de fixation.' },
    ],
  },
  gpu: {
    label: 'Carte graphique',
    section: 'gpu',
    basis: [[1, 0, 0], [0, 0, -1], [0, 1, 0]],
    view: [0.3, 0.3, 1],
    hotspots: [
      { p: [1.0, -4.55, 6.8], n: [0, -1, 0], t: 'Ventilateurs', d: 'Aspirent l\'air par en dessous et le poussent dans le radiateur.' },
      { p: [17.6, -2.0, 11.95], n: [0, 0, 1], t: 'Radiateur', d: 'Ailettes en aluminium qui dissipent la chaleur.' },
      { p: [4.0, -1.8, 12.3], n: [0, 0, 1], t: 'Caloducs', d: 'Transportent la chaleur du GPU vers les ailettes.' },
      { p: [13.85, -0.63, 12.25], n: [0, 0, 1], t: 'Prise 8 broches', d: 'Alimentation PCIe : jusqu\'à 150 W.' },
      { p: [0.0, 0.0, 0.3], n: [0, 0, -1], t: 'Contacts PCIe x16', d: 'S\'enfichent dans le slot PCIe x16 de la carte mère.' },
      { p: [-7.25, -0.8, 4.5], n: [-1, 0, 0], t: 'Sorties vidéo', d: '3 DisplayPort + 1 HDMI : l\'écran se branche ici.' },
      { p: [8.0, 0.5, 6.0], n: [0, 1, 0], t: 'Backplate', d: 'Plaque arrière qui rigidifie la carte.' },
    ],
  },
  psu: {
    label: 'Alimentation 750 W',
    section: 'alimentation',
    view: [0.65, 0.4, 1],
    hotspots: [
      { p: [0.4, -4.45, 0], n: [0, -1, 0], t: 'Ventilateur', d: 'Aspire l\'air frais (ici par le dessous du boîtier).' },
      { p: [-7.15, 1.8, 4.45], n: [-1, 0, 0], t: 'Prise secteur', d: 'Pour le câble d\'alimentation 230 V.' },
      { p: [-7.25, -1.6, 4.45], n: [-1, 0, 0], t: 'Interrupteur', d: 'I = sous tension, O = coupé.' },
      { p: [-7.05, -1.2, -3.0], n: [-1, 0, 0], t: 'Grille arrière', d: 'L\'air chaud sort par ici.' },
      { p: [7.2, 0.75, 1.6], n: [1, 0, 0], t: 'Panneau modulaire', d: 'Câbles PCIe et SATA, branchés selon les besoins.' },
      { p: [9.6, 2.5, -4.4], n: [1, 0, 0.3], t: 'Câbles fixes', d: '24 broches et EPS, toujours attachés (semi-modulaire).' },
      { p: [0, 1.15, 7.53], n: [0, 0, 1], t: 'Étiquette', d: 'Puissance, certification 80 PLUS, norme ATX.' },
    ],
  },
  cooler: {
    label: 'Ventirad',
    section: 'refroidissement',
    basis: [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
    view: [0.7, 0.32, 1],
    hotspots: [
      { p: [0, -2.05, 0.8], n: [0, -1, 0], t: 'Base', d: 'En contact avec le processeur, avec la pâte thermique.' },
      { p: [-1.35, -4.6, 3.0], n: [0, -1, 0.1], t: 'Caloducs', d: '4 tubes de cuivre nickelé qui font monter la chaleur.' },
      { p: [-2.3, 0, 9.0], n: [-1, 0, 0], t: 'Ailettes', d: 'Une grande surface d\'échange avec l\'air.' },
      { p: [4.8, 0, 9.5], n: [1, 0, 0], t: 'Ventilateur 120 mm', d: 'Pousse l\'air à travers les ailettes, vers l\'arrière.' },
      { p: [0, 4.45, 2.2], n: [0, 0.3, 1], t: 'Vis à ressort', d: 'Fixation : serrer en croix, progressivement.' },
    ],
    actions: [{ id: 'swap', label: 'Voir un ventilateur de boîtier', active: 'Voir le ventirad', alt: 'fan' }],
  },
  fan: {
    label: 'Ventilateur 120 mm',
    section: 'refroidissement',
    basis: [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],
    view: [0.5, 0.3, 1],
    hotspots: [
      { p: [1.0, 3.6, 0], n: [1, 0, 0], t: 'Pales', d: '7 pales incurvées : l\'air entre de ce côté.' },
      { p: [-1.3, 0, 0], n: [-1, 0, 0], t: 'Moteur et croisillons', d: 'Côté sortie de l\'air (des flèches sur le cadre l\'indiquent).' },
      { p: [1.3, 5.25, 5.25], n: [1, 0, 0], t: 'Trou de fixation', d: '4 vis pour le fixer au boîtier ou au radiateur.' },
    ],
  },
  case: {
    label: 'Boîtier',
    section: 'boitier',
    view: [0.75, 0.42, 1],
    hotspots: [
      { p: [6.0, 30, 11.4], n: [0, 0, 1], t: 'Vitre en verre trempé', d: 'Amovible, tenue par 4 vis à main.' },
      { p: [22.55, 30, 3], n: [1, 0, 0], t: 'Façade mesh', d: 'Laisse entrer l\'air des 3 ventilateurs avant.' },
      { p: [0, 48.05, 1], n: [0, 1, 0], t: 'Grille supérieure', d: 'Emplacements pour d\'autres ventilateurs.' },
      { p: [19.4, 48.3, -2.0], n: [0, 1, 0], t: 'Façade I/O', d: 'Bouton d\'allumage, USB-A, USB-C, prise casque.' },
      { p: [-22.6, 37, 2.5], n: [-1, 0, 0], t: 'Ventilateur arrière', d: 'Emplacement 120 mm : il expulse l\'air chaud.' },
      { p: [-22.6, 35, -6.0], n: [-1, 0, 0], t: 'Ouverture I/O', d: 'Les ports arrière de la carte mère passent ici.' },
      { p: [-22.6, 20, -2.5], n: [-1, 0, 0], t: 'Caches PCIe', d: 'À retirer en face de la carte graphique.' },
      { p: [-4, 11.05, 9.5], n: [0, 1, 0.4], t: 'Cache-alimentation', d: 'Cache l\'alimentation et le surplus de câbles.' },
      { p: [-8.95, 43.6, -8.35], n: [0, 0, 1], t: 'Entretoises', d: '9 colonnettes dorées sous la carte mère.' },
      { p: [5.05, 34.5, -8.9], n: [0, 0, 1], t: 'Passe-câbles', d: 'Pour faire passer les câbles derrière le plateau.' },
    ],
    actions: [{ id: 'glass', label: 'Retirer la vitre', active: 'Remettre la vitre' }],
  },
};

/** Nom et section de chaque pièce pour la vue éclatée et le montage. */
export const PART_LABELS = Object.fromEntries(Object.entries(PARTS).map(([k, v]) => [k, { label: v.label, section: v.section }]));
