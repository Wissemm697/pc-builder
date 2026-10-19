/**
 * parts.js : Configuration de chaque pièce pour les visionneuses et la vue éclatée.
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
import { L } from '../i18n.js';

export const PARTS = {
  cpu: {
    label: L('Processeur', 'Processor'),
    section: 'cpu',
    view: [0.5, 0.45, 1],
    hotspots: [
      { p: [0.6, 0.95, 0.5], n: [0, 0, 1], t: L('Capot (IHS)', 'Heat spreader (IHS)'), d: L('Répartit la chaleur de la puce vers le ventirad.', 'Spreads the chip\'s heat out towards the cooler.') },
      { p: [-1.8, -1.8, 0.13], n: [0, 0, 1], t: L('Triangle doré', 'Gold triangle'), d: L('À aligner avec le triangle du socket.', 'Line it up with the triangle on the socket.') },
      { p: [1.55, 0.8, 0.16], n: [0, 0, 1], t: L('Condensateurs', 'Capacitors'), d: L('Stabilisent l\'alimentation de la puce.', 'Keep the chip\'s power supply steady.') },
      { p: [0.9, -0.9, -0.01], n: [0, 0, -1], t: L('Pastilles dorées', 'Gold pads'), d: L('Environ 1 700 contacts qui touchent les broches du socket.', 'Around 1,700 contacts that press against the socket pins.') },
      { p: [-0.7, 1.98, 0.06], n: [0, 1, 0.4], t: L('Substrat', 'Substrate'), d: L('Petit circuit vert qui relie la puce aux pastilles.', 'The small green board that connects the chip to the pads.') },
    ],
    actions: [{ id: 'flip', label: L('Voir le dessous', 'Show the underside'), active: L('Voir le dessus', 'Show the top') }],
  },
  motherboard: {
    label: L('Carte mère', 'Motherboard'),
    section: 'carte-mere',
    view: [0.25, 0.15, 1],
    hotspots: [
      { p: [-3.5, 6.25, 0.62], n: [0, 0, 1], t: L('Socket AM5', 'AM5 socket'), d: L('Accueille le processeur. Ses broches sont très fragiles.', 'Holds the processor. Its pins are very fragile.') },
      { p: [-8.15, 4.8, 2.9], n: [0, 0, 1], t: 'VRM', d: L('Fabrique la tension du processeur, sous des dissipateurs.', 'Produces the processor\'s voltage, hidden under heatsinks.') },
      { p: [4.9, 9.5, 0.95], n: [0, 0, 1], t: L('Slots DDR5', 'DDR5 slots'), d: L('A1, A2, B1, B2. Avec 2 barrettes : A2 et B2 (en gris clair).', 'A1, A2, B1, B2. With two sticks, use A2 and B2 (light grey).') },
      { p: [-6.15, -4.58, 1.35], n: [0, 0, 1], t: L('Slot PCIe x16', 'PCIe x16 slot'), d: L('Pour la carte graphique, renforcé par du métal.', 'For the graphics card, reinforced with metal.') },
      { p: [-5.0, -1.6, 0.55], n: [0, 0, 1], t: L('Slot M.2_1', 'M.2_1 slot'), d: L('Pour le SSD NVMe, relié directement au processeur.', 'For the NVMe SSD, wired straight to the processor.') },
      { p: [-5.0, -10.6, 0.95], n: [0, 0, 1], t: L('Slot M.2_2', 'M.2_2 slot'), d: L('Second slot M.2, sous un dissipateur.', 'A second M.2 slot, under a heatsink.') },
      { p: [5.8, -9.3, 1.2], n: [0, 0, 1], t: 'Chipset', d: L('Gère une partie des ports (USB, SATA, slots secondaires).', 'Runs some of the ports (USB, SATA, secondary slots).') },
      { p: [11.1, 6.1, 1.25], n: [0, 0, 1], t: L('24 broches ATX', '24-pin ATX'), d: L('Alimentation principale de la carte mère.', 'The motherboard\'s main power input.') },
      { p: [-5.1, 14.0, 1.25], n: [0, 0, 1], t: L('8 broches EPS', '8-pin EPS'), d: L('Alimentation du processeur (câble « CPU »).', 'Powers the processor (the cable marked “CPU”).') },
      { p: [-12.7, 8.0, 3.2], n: [-1, 0, 0.6], t: L('Ports arrière (I/O)', 'Rear ports (I/O)'), d: L('USB, réseau, audio, boutons BIOS.', 'USB, networking, audio and BIOS buttons.') },
      { p: [11.7, -8.65, 1.35], n: [1, 0, 0.6], t: L('Ports SATA', 'SATA ports'), d: L('Pour SSD 2,5" et disques durs.', 'For 2.5" SSDs and hard drives.') },
      { p: [7.5, -14.35, 0.95], n: [0, 0, 1], t: 'F_PANEL', d: L('Bouton d\'allumage et LED du boîtier.', 'The case\'s power button and LEDs.') },
      { p: [-6.2, -7.0, 0.55], n: [0, 0, 1], t: L('Pile CMOS', 'CMOS battery'), d: L('Garde l\'heure et les réglages du BIOS.', 'Keeps the clock and BIOS settings.') },
      { p: [10.05, 9.55, 0.35], n: [0, 0, 1], t: L('LED de diagnostic', 'Diagnostic LEDs'), d: L('CPU, DRAM, VGA, BOOT : indiquent ce qui bloque au démarrage.', 'CPU, DRAM, VGA, BOOT: they show what\'s holding up the boot.') },
    ],
    actions: [{ id: 'socket', label: L('Ouvrir le socket', 'Open the socket'), active: L('Fermer le socket', 'Close the socket') }],
  },
  ram: {
    label: L('Barrette DDR5 16 Go', '16 GB DDR5 stick'),
    section: 'ram',
    basis: [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
    view: [0.15, 0.3, 1],
    hotspots: [
      { p: [0.12, -4.1, 1.75], n: [1, 0, 0], t: L('Puces mémoire', 'Memory chips'), d: L('8 puces de 2 Go : 16 Go au total.', 'Eight 2 GB chips, 16 GB in total.') },
      { p: [0.12, 0, 1.25], n: [1, 0, 0], t: 'PMIC', d: L('Régulateur de tension embarqué, une nouveauté de la DDR5.', 'An on-board voltage regulator, new with DDR5.') },
      { p: [0.08, -3.2, 0.16], n: [1, 0, 0], t: L('Contacts', 'Contacts'), d: L('288 contacts dorés (144 par face).', '288 gold contacts (144 on each side).') },
      { p: [0.0, -0.35, 0.05], n: [1, 0, 0.2], t: L('Encoche', 'Notch'), d: L('Détrompeur : impossible de l\'insérer à l\'envers ou dans un slot DDR4.', 'A key: it can\'t go in backwards or into a DDR4 slot.') },
      { p: [0, 6.67, 1.75], n: [0, 1, 0], t: L('Encoche latérale', 'Side notch'), d: L('Le loquet du slot s\'y accroche (« clic »).', 'The slot\'s latch clips in here (that\'s the “click”).') },
      { p: [-0.09, 0.2, 2.0], n: [-1, 0, 0], t: L('Étiquette', 'Label'), d: L('Capacité, génération et organisation des puces.', 'Capacity, generation and chip layout.') },
    ],
  },
  ssd: {
    label: L('SSD NVMe M.2', 'M.2 NVMe SSD'),
    section: 'stockage',
    view: [0.2, 0.5, 1],
    hotspots: [
      { p: [1.62, 0, 0.22], n: [0, 0, 1], t: L('Contrôleur', 'Controller'), d: L('Le cerveau du SSD : il répartit les données entre les puces.', 'The SSD\'s brain: it spreads data across the chips.') },
      { p: [2.87, 0, 0.19], n: [0, 0, 1], t: L('Cache DRAM', 'DRAM cache'), d: L('Petite mémoire tampon qui accélère le SSD.', 'A small buffer that speeds the SSD up.') },
      { p: [5.4, 0.2, 0.24], n: [0, 0, 1], t: L('Mémoire flash NAND', 'NAND flash'), d: L('Sous l\'étiquette : c\'est là que sont gardées les données.', 'Under the label. This is where your data lives.') },
      { p: [0.2, 0.45, 0.09], n: [0, 0, 1], t: L('Contacts + clé M', 'Contacts + M key'), d: L('Se branchent dans le slot M.2 ; l\'encoche évite les erreurs.', 'They plug into the M.2 slot. The notch stops it going in the wrong way.') },
      { p: [7.95, 0, 0.09], n: [0, 0, 1], t: L('Demi-lune', 'Half-moon cut-out'), d: L('Passage de la petite vis de fixation.', 'Where the tiny mounting screw goes.') },
    ],
  },
  gpu: {
    label: L('Carte graphique', 'Graphics card'),
    section: 'gpu',
    basis: [[1, 0, 0], [0, 0, -1], [0, 1, 0]],
    view: [0.3, 0.3, 1],
    hotspots: [
      { p: [1.0, -4.55, 6.8], n: [0, -1, 0], t: L('Ventilateurs', 'Fans'), d: L('Aspirent l\'air par en dessous et le poussent dans le radiateur.', 'Pull air in from below and push it through the heatsink.') },
      { p: [17.6, -2.0, 11.95], n: [0, 0, 1], t: L('Radiateur', 'Heatsink'), d: L('Ailettes en aluminium qui dissipent la chaleur.', 'Aluminium fins that get rid of the heat.') },
      { p: [4.0, -1.8, 12.3], n: [0, 0, 1], t: L('Caloducs', 'Heat pipes'), d: L('Transportent la chaleur du GPU vers les ailettes.', 'Carry heat from the GPU to the fins.') },
      { p: [13.85, -0.63, 12.25], n: [0, 0, 1], t: L('Prise 8 broches', '8-pin socket'), d: L('Alimentation PCIe : jusqu\'à 150 W.', 'PCIe power: up to 150 W.') },
      { p: [0.0, 0.0, 0.3], n: [0, 0, -1], t: L('Contacts PCIe x16', 'PCIe x16 contacts'), d: L('S\'enfichent dans le slot PCIe x16 de la carte mère.', 'Slot into the motherboard\'s PCIe x16 slot.') },
      { p: [-7.25, -0.8, 4.5], n: [-1, 0, 0], t: L('Sorties vidéo', 'Video outputs'), d: L('3 DisplayPort + 1 HDMI : l\'écran se branche ici.', '3 DisplayPort + 1 HDMI. Your monitor plugs in here.') },
      { p: [8.0, 0.5, 6.0], n: [0, 1, 0], t: 'Backplate', d: L('Plaque arrière qui rigidifie la carte.', 'A rear plate that stiffens the card.') },
    ],
  },
  psu: {
    label: L('Alimentation 750 W', '750 W power supply'),
    section: 'alimentation',
    view: [0.65, 0.4, 1],
    hotspots: [
      { p: [0.4, -4.45, 0], n: [0, -1, 0], t: L('Ventilateur', 'Fan'), d: L('Aspire l\'air frais (ici par le dessous du boîtier).', 'Draws in cool air (here, through the bottom of the case).') },
      { p: [-7.15, 1.8, 4.45], n: [-1, 0, 0], t: L('Prise secteur', 'Mains inlet'), d: L('Pour le câble d\'alimentation 230 V.', 'For the 230 V power cable.') },
      { p: [-7.25, -1.6, 4.45], n: [-1, 0, 0], t: L('Interrupteur', 'Power switch'), d: L('I = sous tension, O = coupé.', 'I = on, O = off.') },
      { p: [-7.05, -1.2, -3.0], n: [-1, 0, 0], t: L('Grille arrière', 'Rear grille'), d: L('L\'air chaud sort par ici.', 'Warm air comes out here.') },
      { p: [7.2, 0.75, 1.6], n: [1, 0, 0], t: L('Panneau modulaire', 'Modular panel'), d: L('Câbles PCIe et SATA, branchés selon les besoins.', 'PCIe and SATA cables, plugged in as needed.') },
      { p: [9.6, 2.5, -4.4], n: [1, 0, 0.3], t: L('Câbles fixes', 'Fixed cables'), d: L('24 broches et EPS, toujours attachés (semi-modulaire).', '24-pin and EPS, always attached (semi-modular).') },
      { p: [0, 1.15, 7.53], n: [0, 0, 1], t: L('Étiquette', 'Label'), d: L('Puissance, certification 80 PLUS, norme ATX.', 'Wattage, 80 PLUS rating, ATX standard.') },
    ],
  },
  cooler: {
    label: L('Ventirad', 'CPU cooler'),
    section: 'refroidissement',
    basis: [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
    view: [0.7, 0.32, 1],
    hotspots: [
      { p: [0, -2.05, 0.8], n: [0, -1, 0], t: L('Base', 'Base'), d: L('En contact avec le processeur, avec la pâte thermique.', 'Sits on the processor, with thermal paste in between.') },
      { p: [-1.35, -4.6, 3.0], n: [0, -1, 0.1], t: L('Caloducs', 'Heat pipes'), d: L('4 tubes de cuivre nickelé qui font monter la chaleur.', 'Four nickel-plated copper pipes that carry the heat upwards.') },
      { p: [-2.3, 0, 9.0], n: [-1, 0, 0], t: L('Ailettes', 'Fins'), d: L('Une grande surface d\'échange avec l\'air.', 'A large surface for the air to pick up heat.') },
      { p: [4.8, 0, 9.5], n: [1, 0, 0], t: L('Ventilateur 120 mm', '120 mm fan'), d: L('Pousse l\'air à travers les ailettes, vers l\'arrière.', 'Pushes air through the fins, towards the back.') },
      { p: [0, 4.45, 2.2], n: [0, 0.3, 1], t: L('Vis à ressort', 'Spring-loaded screws'), d: L('Fixation : serrer en croix, progressivement.', 'Tighten them a little at a time, in a criss-cross pattern.') },
    ],
    actions: [{ id: 'swap', label: L('Voir un ventilateur de boîtier', 'Show a case fan'), active: L('Voir le ventirad', 'Show the CPU cooler'), alt: 'fan' }],
  },
  fan: {
    label: L('Ventilateur 120 mm', '120 mm fan'),
    section: 'refroidissement',
    basis: [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],
    view: [0.5, 0.3, 1],
    hotspots: [
      { p: [1.0, 3.6, 0], n: [1, 0, 0], t: L('Pales', 'Blades'), d: L('7 pales incurvées : l\'air entre de ce côté.', 'Seven curved blades. Air comes in on this side.') },
      { p: [-1.3, 0, 0], n: [-1, 0, 0], t: L('Moteur et croisillons', 'Motor and struts'), d: L('Côté sortie de l\'air (des flèches sur le cadre l\'indiquent).', 'The side the air leaves from (arrows on the frame show it).') },
      { p: [1.3, 5.25, 5.25], n: [1, 0, 0], t: L('Trou de fixation', 'Mounting hole'), d: L('4 vis pour le fixer au boîtier ou au radiateur.', 'Four screws hold it to the case or a radiator.') },
    ],
  },
  case: {
    label: L('Boîtier', 'Case'),
    section: 'boitier',
    view: [0.75, 0.42, 1],
    hotspots: [
      { p: [6.0, 30, 11.4], n: [0, 0, 1], t: L('Vitre en verre trempé', 'Tempered glass panel'), d: L('Amovible, tenue par 4 vis à main.', 'Removable, held on by four thumbscrews.') },
      { p: [22.55, 30, 3], n: [1, 0, 0], t: L('Façade mesh', 'Mesh front panel'), d: L('Laisse entrer l\'air des 3 ventilateurs avant.', 'Lets the three front fans pull air in.') },
      { p: [0, 48.05, 1], n: [0, 1, 0], t: L('Grille supérieure', 'Top grille'), d: L('Emplacements pour d\'autres ventilateurs.', 'Room for extra fans.') },
      { p: [19.4, 48.3, -2.0], n: [0, 1, 0], t: L('Façade I/O', 'Front I/O'), d: L('Bouton d\'allumage, USB-A, USB-C, prise casque.', 'Power button, USB-A, USB-C and headphone jack.') },
      { p: [-22.6, 37, 2.5], n: [-1, 0, 0], t: L('Ventilateur arrière', 'Rear fan'), d: L('Emplacement 120 mm : il expulse l\'air chaud.', '120 mm mount. This fan blows the hot air out.') },
      { p: [-22.6, 35, -6.0], n: [-1, 0, 0], t: L('Ouverture I/O', 'I/O cut-out'), d: L('Les ports arrière de la carte mère passent ici.', 'The motherboard\'s rear ports poke through here.') },
      { p: [-22.6, 20, -2.5], n: [-1, 0, 0], t: L('Caches PCIe', 'PCIe slot covers'), d: L('À retirer en face de la carte graphique.', 'Remove the ones lined up with the graphics card.') },
      { p: [-4, 11.05, 9.5], n: [0, 1, 0.4], t: L('Cache-alimentation', 'PSU shroud'), d: L('Cache l\'alimentation et le surplus de câbles.', 'Hides the power supply and spare cables.') },
      { p: [-8.95, 43.6, -8.35], n: [0, 0, 1], t: L('Entretoises', 'Standoffs'), d: L('9 colonnettes dorées sous la carte mère.', 'Nine small brass posts under the motherboard.') },
      { p: [5.05, 34.5, -8.9], n: [0, 0, 1], t: L('Passe-câbles', 'Grommets'), d: L('Pour faire passer les câbles derrière le plateau.', 'Route cables through to the back of the tray.') },
    ],
    actions: [{ id: 'glass', label: L('Retirer la vitre', 'Remove the glass'), active: L('Remettre la vitre', 'Put the glass back') }],
  },
};

/** Nom et section de chaque pièce pour la vue éclatée et le montage. */
export const PART_LABELS = Object.fromEntries(Object.entries(PARTS).map(([k, v]) => [k, { label: v.label, section: v.section }]));
