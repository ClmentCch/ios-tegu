# Feuille de route

Chaque phase a un critère de sortie **vérifiable**. Une phase non vérifiée reste
« ouverte », même si du code a été écrit.

## Phase 0 — Socle d'analyse (terminée)

| Tâche | État | Preuve |
|---|---|---|
| Diagnostic du lien MEGA | terminé | `firmware/metadata/mega-rom-link.json` : `key_valid: false` |
| Outil de lecture ZIP64 distante | terminé | `tools/ipsw_fetch.py`, testé sur 2 IPSW |
| Vérification SHA-256 en flux | terminé | 2 IPSW vérifiés, tailles et empreintes conformes |
| Inventaire du firmware | terminé | `firmware/metadata/ipsw-entries.json` (141 entrées) |
| Cartographie des composants | terminé | 103 composants, `firmware/metadata/iphone17,3-27.2-24B119.json` |
| Analyse du noyau | terminé (constat) | IM4P `krnl`, charge utile chiffrée, entropie 7,983 |
| Documentation de faisabilité | terminé | `kernel/xnu-notes.md`, `boot/boot-chain-tegu.md` |

## Phase 1 — Déblocage de la source (ouverte)

* **Bloquant actuel** : clé MEGA invalide. Action : obtenir une URL MEGA dont la
  clé déchiffre l'objet, ou fournir l'IPSW autrement.
* Critère de sortie : `tools/mega_probe.py` renvoie `key_valid: true` **et**
  `payload_magic_decrypted: "ZIP (IPSW archive)"`.
* À défaut : documenter l'écart entre le blob MEGA et l'IPSW public (taille
  identique, contenu non prouvé).

## Phase 2 — Relevé matériel du Pixel 9a (sans modification)

* Collecter `fastboot getvar all`, l'état de verrouillage, les slots.
* Extraire le DTB de `vendor_boot.img` et le décompiler (`dtc -I dtb -O dts`).
* Identifier : UART de debug, GICD/GICR, watchdog, timers, UFS, PMIC.
* Critère de sortie : un fichier `device/tegu/dtb-notes.md` avec adresses et
  IRQ, issu d'un relevé réel (pas d'estimation).

## Phase 3 — Bring-up XNU sous QEMU

* Compiler XNU `arm64` avec un platform expert de test (GICv3 + PL011).
* Obtenir la bannière XNU et un `printf` reproductible.
* Critère de sortie : log de démarrage archivé + commande de reproduction.

## Phase 4 — Platform expert « tegu »

* Remplacer PL011 par l'UART réel, brancher le GICv3 sur les adresses relevées.
* Ajouter le timer, le watchdog, la carte mémoire du DTB.
* Critère de sortie : XNU affiche ses messages sur le matériel, sans écrire en
  partition ; le watchdog est rafraîchi.

## Phase 5 — Stockage et preuve de vie

* Pilote UFS en lecture seule sur une zone neutre.
* Lire un secteur, vérifier son empreinte, redémarrer proprement.
* Critère de sortie : lecture reproductible + empreinte identique à chaque boot.

## Phase 6 — Espace utilisateur Darwin

* Porter un userland minimal (libSystem, launchd, shell) pour `arm64` générique.
* Critère de sortie : shell interactif sur console série.

## Phase 7 — Documentation et publication

* Rapport par phase, empreintes, limites.
* Aucune Release tant qu'aucun artefact publiable ne dépasse la limite du dépôt.

## Ce qui n'est pas dans la feuille de route

* Faire démarrer les binaires iOS de l'IPSW : impossible sans SEP/AMFI/APFS Apple.
* Contourner la personnalisation TSS : hors périmètre et hors la loi.
* Flasher un appareil : aucune opération de ce type n'est prévue par ce dépôt.
