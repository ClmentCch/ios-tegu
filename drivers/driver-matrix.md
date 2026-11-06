# Matrice des pilotes à écrire

Aucun de ces pilotes n'existe. Aucune ligne de ce tableau ne doit être lue comme
« fait ». La colonne « prérequis » indique l'information minimale à relever avant
d'écrire quoi que ce soit.

| Sous-système | Matériel Pixel 9a | Côté Apple (référence) | Pilote XNU disponible | Prérequis avant écriture |
|---|---|---|---|---|
| Console de debug | UART du SoC Tensor G4 | UART Apple | non | adresse de base + horloge (device tree) |
| Interruptions | ARM GICv3 (GICD/GICR) | Apple AIC/AIC2 | non | adresses GICD/GICR, INTIDs du DTB |
| Timers | ARM generic timer | ARM generic timer | oui (partiel) | fréquence, IRQ |
| Watchdog | watchdog du SoC | Apple WDT | non | adresse, procédure de refresh |
| Mémoire | contrôleur DDR + LPDDR5X | Apple AMC | non | carte mémoire du DTB, réservations |
| Stockage | UFS 3.1 | NVMe/ANS Apple | non | base UFS, horloges, PHY, géométrie |
| Affichage | DDIC + dalle P-OLED 1080×2424 | DCP Apple | non | type de DDIC, séquence d'init, DSI |
| Tactile | contrôleur tactile (à confirmer) | AppleMultitouch | non | bus (I2C/SPI), IRQ, protocole |
| Alimentation | PMIC + chargeur | Apple PMGR/SMC | non | adresses, registres, séquence |
| USB-C | contrôleur USB + PD | Apple USB | non | base, PHY, PD |
| Wi-Fi / BT | combo (à confirmer) | Broadcom Apple | non | modèle exact, firmware |
| Modem | Exynos 5300 (rapporté) | baseband Apple | non | interfaces, protocole |
| Audio | codec + amplis | Apple audio | non | I2S, horloges, DAPM |
| Capteurs | accéléromètre, baromètre, boussole | Apple sensors | non | bus, IRQ |
| GPU | Mali-G715 MP7 | GFX Apple | non | firmware Mali, interface |
| ISP / caméra | ISP Google + capteurs | ISP Apple | non | pipeline, formats |
| Haptique | moteur linéaire | LeapHaptics Apple | non | driver IC, séquence |
| Chargement sécurisé | Titan M2 / AVB | SEP / AMFI | non | hors périmètre XNU |

## Priorité de travail

1. **Console + GICv3 + timer** — sans cela, rien n'est observable. C'est l'étape 1
   et 2 de `kernel/xnu-notes.md`.
2. **Watchdog** — sans refresh, le SoC redémarre avant tout diagnostic.
3. **Stockage en lecture seule** — première preuve de fonctionnement non trivial.
4. **Affichage** — nécessaire pour un retour visuel, mais plus complexe (DSI,
   DDIC, séquence d'initialisation).
5. Le reste suit l'ordre des dépendances.

## Règles de conception

* Chaque pilote doit venir d'une **spécification ou d'un relevé de device tree**,
  pas d'une copie de code GPL Linux (incompatibilité de licence avec l'APSL 2.0 de
  XNU).
* Aucun pilote ne doit écrire dans une partition système du téléphone.
* Tout pilote doit être testable hors appareil (QEMU) avant tout essai matériel.
