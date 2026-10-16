"""
layout.py — Cotes partagées entre les scripts (source unique de vérité).

Toutes les valeurs sont en centimètres, dans l'espace du site (voir common.py) :
X = avant du boîtier, Y = haut, Z = vers la vitre.

Repère de la CARTE MÈRE : origine au centre de la face arrière du PCB,
bord arrière (côté ports I/O) en X = -12,2 ; bord supérieur en Y = +15,25 ;
les composants sont du côté +Z.

Repère du BOÎTIER : origine au centre de l'empreinte au sol.
"""

# ---------------------------------------------------------------- carte mère ATX
MB_W = 24.4          # profondeur (X) — format ATX 305 x 244 mm
MB_H = 30.5          # hauteur (Y)
MB_T = 0.16          # épaisseur du PCB

# Socket du processeur (type LGA : les broches sont sur la carte mère)
SOCKET_C = (-3.5, 6.25)          # centre (x, y)
CPU_SIZE = 4.0                   # boîtier du processeur 40 x 40 mm
CPU_SEAT_Z = MB_T + 0.25         # plan où reposent les pastilles du CPU
CPU_SUBSTRATE_T = 0.12           # épaisseur du substrat (circuit vert)
CPU_IHS_T = 0.38                 # épaisseur du capot métallique (IHS)
COOLER_Z = CPU_SEAT_Z + CPU_SUBSTRATE_T + CPU_IHS_T   # dessus de l'IHS = base du ventirad

# Slots de RAM (A1 est le plus proche du processeur)
DIMM_X = {'A1': 3.7, 'A2': 4.5, 'B1': 5.3, 'B2': 6.1}
DIMM_Y = 5.0                     # centre des slots en Y
DIMM_SLOT_LEN = 14.2
DIMM_SLOT_W = 0.62
DIMM_SLOT_H = 0.75
RAM_SEAT_Z = MB_T + 0.15         # bas de la barrette une fois enfoncée

# Slots d'extension : 7 positions espacées de 0,8 pouce (2,032 cm)
SLOT_PITCH = 2.032


def slot_y(k):
    """Y (repère carte mère) du plan du PCB d'une carte dans la position k (1 = en haut)."""
    return MB_H / 2 - (17.8 + (k - 1) * SLOT_PITCH)


PCIE_X16_POS = 2                 # le slot x16 principal est en 2e position
PCIE_X16_Y = slot_y(PCIE_X16_POS)
PCIE_X16_X0, PCIE_X16_X1 = -10.6, -1.7    # longueur 8,9 cm
PCIE_X16_XC = (PCIE_X16_X0 + PCIE_X16_X1) / 2
PCIE_SEAT_Z = MB_T + 0.15        # bas des contacts dorés de la carte une fois enfoncée
PCIE_SLOT_H = 1.1

# Slots M.2 (le SSD se pose à plat, connecteur côté arrière)
M2 = {
    'M2_1': dict(conn_x=-9.0, y=-1.6, z=MB_T + 0.25),
    'M2_2': dict(conn_x=-9.0, y=-10.6, z=MB_T + 0.25),
}
M2_LEN = 8.0                     # format 2280 : 22 x 80 mm
M2_W = 2.2

# Connecteurs d'alimentation et en-têtes (repère carte mère)
ATX24 = dict(x0=10.6, x1=11.6, y0=3.4, y1=8.8)          # 24 broches, vertical
EPS8 = dict(x0=-6.2, x1=-4.0, y0=13.45, y1=14.55)        # 8 broches CPU (EPS 12 V)
CPU_FAN = (1.2, 13.9)
SYS_FAN = [(-9.0, -14.45), (11.45, 1.3)]
F_PANEL = dict(x0=6.4, x1=8.6, y0=-14.75, y1=-13.95)     # boutons/LED du boîtier
USB3_HDR = dict(x0=10.5, x1=11.5, y0=-5.2, y1=-2.6)      # USB 3 (19 broches)
USBC_HDR = dict(x0=10.6, x1=11.5, y0=-1.6, y1=-0.6)
HD_AUDIO = dict(x0=-10.6, x1=-8.6, y0=-14.75, y1=-13.95)

# 9 trous de fixation ATX (où se vissent les entretoises)
HOLES = [
    (-11.25, 14.35), (-0.15, 14.35), (11.35, 14.35),
    (-11.25, -0.25), (0.85, -0.25), (11.35, -0.25),
    (-11.25, -14.3), (0.85, -14.3), (11.35, -14.3),
]

# Zone des ports arrière (I/O)
IO_Y0, IO_Y1 = -1.0, 13.3
IO_Z1 = MB_T + 4.4

# ---------------------------------------------------------------- boîtier moyen tour
CASE_L = 45.0        # profondeur (X)
CASE_W = 22.0        # largeur (Z)
CASE_H = 48.0        # hauteur (Y)
WALL = 0.1           # tôle d'acier
FEET_H = 1.5         # hauteur des pieds
FLOOR_Y = 2.0        # dessus du plancher intérieur
REAR_X = -CASE_L / 2          # face arrière extérieure
REAR_IN_X = REAR_X + 0.5      # face intérieure du panneau arrière
TRAY_Z = -9.0                 # plateau de la carte mère
STANDOFF_H = 0.6              # entretoises
MB_BACK_Z = TRAY_Z + STANDOFF_H
MB_CENTER = (-8.8, 29.25)     # centre de la carte mère dans le boîtier (x, y)
SHROUD_TOP = 11.0             # dessus du cache-alimentation
SHROUD_X1 = 14.0              # extrémité avant du cache-alimentation
GLASS_Z = 10.9                # face intérieure de la vitre

# Alimentation ATX : 15 (largeur) x 8,6 (hauteur) x 14 (profondeur) cm
PSU_SIZE = (14.0, 8.6, 15.0)  # (X, Y, Z) une fois installée
PSU_CENTER = (REAR_IN_X + 7.0, FLOOR_Y + 4.3 + 0.05, -0.5)

# Ventilateurs 120 mm : 3 en façade (aspiration), 1 à l'arrière (extraction)
FAN_FRONT = [(20.0, 12.5, 0.2), (20.0, 24.5, 0.2), (20.0, 36.5, 0.2)]
FAN_REAR = (-20.65, 37.0, 2.5)


def mb_to_case(x, y, z=0.0):
    """Repère carte mère -> repère boîtier."""
    return (MB_CENTER[0] + x, MB_CENTER[1] + y, MB_BACK_Z + z)


# ---------------------------------------------------------------- carte graphique
# Repère du GPU : origine au milieu du bord inférieur des contacts dorés (PCIe x16),
# le PCB est dans le plan Y = 0, les ventilateurs regardent vers -Y (vers le bas).
GPU_FINGER_HALF = 4.45
GPU_BRACKET_X = -GPU_FINGER_HALF - 2.6      # équerre (côté arrière du boîtier)
GPU_LEN = 28.0
GPU_FRONT_X = GPU_BRACKET_X + GPU_LEN
GPU_TOP_Z = 12.4
GPU_THICK_DOWN = 4.4                        # épaisseur sous le PCB (radiateur + ventilateurs)
GPU_THICK_UP = 0.6                          # épaisseur au-dessus (backplate)

# Détrompeur des slots DDR5 (décalé par rapport au centre ; il est ailleurs en DDR4,
# ce qui empêche d'insérer une barrette du mauvais type)
DDR5_KEY_OFFSET = -0.35
