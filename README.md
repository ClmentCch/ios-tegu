# iOS-tegu

**Recherche sur un portage expérimental de XNU / de l'environnement système iOS
vers le Google Pixel 9a (`tegu`, Google Tensor G4).**

> Ce projet n'est ni un launcher Android, ni un thème, ni une imitation visuelle
> d'iOS. Il étudie la possibilité de faire tourner un véritable noyau de la
> famille Darwin/XNU sur le matériel du Pixel 9a, et documente honnêtement ce qui
> est possible, ce qui ne l'est pas, et pourquoi.

## État actuel — phase 0 (analyse)

| Élément | État vérifié |
|---|---|
| Outillage d'analyse (MEGA, IPSW distant, vérification d'intégrité) | **fonctionnel et testé** |
| Firmware source `ROM.MD` (MEGA) | **lien accessible, clé de déchiffrement invalide** → aucun contenu exploitable (voir [docs/mega-rom-link.md](docs/mega-rom-link.md)) |
| Firmware iOS 27 analysé | **oui**, sur l'IPSW officiel identifié par empreinte de taille : iOS 27.2 / 24B119 / iPhone17,3 |
| Extraction de composants Apple (noyau, DMG, SEP…) | **non** : conteneurs chiffrés/signés, aucune protection contournée |
| Portage XNU sur Pixel 9a | **non commencé** : analyse de faisabilité uniquement |
| Modification d'un appareil physique | **aucune**, jamais |

Aucune fonctionnalité n'est présentée comme opérationnelle sans preuve dans ce
dépôt. Les sections «mesuré», «vérifié» et «non réalisé» sont distinguées partout.

## Objectif technique

Faire exécuter, à terme, un noyau **XNU** (Mach + BSD, base de Darwin/iOS) sur le
SoC **Tensor G4** du Pixel 9a, avec :

1. une chaîne de démarrage maîtrisée (bootloader déverrouillé → payload → XNU) ;
2. un *platform expert* XNU adapté au matériel Google (GICv3, UART, timers,
   MMU, device tree du Pixel) ;
3. des pilotes IOKit minimaux (console série, stockage, affichage, tactile) ;
4. un espace utilisateur **Darwin**, et non des binaires iOS signés par Apple.

Le point 4 est la limite dure du projet : l'espace utilisateur iOS dépend du SEP,
d'AMFI et de l'APFS chiffré Apple, qui n'existent pas sur un Pixel. Cette
distinction est détaillée dans [kernel/xnu-notes.md](kernel/xnu-notes.md).

## Matériel cible

| Champ | Valeur |
|---|---|
| Appareil | Google Pixel 9a |
| Nom de code | `tegu` (device tree AOSP `android_device_google_tegu`) |
| SoC | Google Tensor G4, nom de code «Zuma Pro» (S5P9875) |
| CPU | 1 × Cortex-X4 3,1 GHz + 3 × Cortex-A720 2,6 GHz + 4 × Cortex-A520 1,92 GHz (ARMv8-A, aarch64) |
| GPU | ARM Mali-G715 MP7 |
| RAM | 8 Go LPDDR5X |
| Stockage | 128/256 Go UFS 3.1 |
| Écran | P-OLED 6,3" 1080 × 2424, 120 Hz |
| Sécurité | Titan M2, Trusty TEE, Android Verified Boot 2.0 |
| Système d'origine | Android 15 → 16, noyau Linux 6.1 |

Détails et sources : [docs/pixel9a-hardware.md](docs/pixel9a-hardware.md) et
[device/tegu/specs.json](device/tegu/specs.json).

## Firmware analysé

**iPhone 16 (iPhone17,3) — iOS 27.2 — build 24B119**

| Champ | Valeur vérifiée |
|---|---|
| Fichier | `iPhone17,3_27.2_24B119_Restore.ipsw` |
| Taille | 12 883 623 203 octets (11,999 Gio) |
| SHA-256 | `62158ad39a22fca5620deeb407cf367cab1775cf1c2fbbdf627321383af78f8b` |
| Vérification | flux complet relu une fois, SHA-256 recalculé **en mémoire** et comparé à la valeur publiée → **identique** |
| Archive | ZIP64, 141 entrées (113 fichiers, 28 répertoires), 13 088 874 633 octets décompressés |
| Identité | `iPhone17,3`, `DeviceClass d47ap`, `ApBoardID 0x08`, `ApChipID 0x8140` (t8140), `SDOM 1` |
| Build train | `RaveB`, `Ap,OSLongVersion 24.2.119.0.0,0`, `RestoreVersion 24.2.119.0.0` |
| Noyau | `kernelcache.release.d47` / `kernelcache.research.d47`, conteneur IM4P `krnl`, description `KernelManagement_host-514.40.8`, charge utile 23 736 240 octets, **chiffrée** (entropie 7,983 bit/octet) |

**Pourquoi ce firmware et pas directement celui de `ROM.MD` ?** Le lien MEGA de
`ROM.MD` fonctionne (objet servi intégralement, 12 883 623 203 octets) mais la clé
de 32 octets qu'il contient ne déchiffre ni les attributs ni la charge utile :
le lien est inutilisable en l'état. Or la taille de l'objet MEGA est **exactement**
celle de l'IPSW public iPhone17,3 / 27.2 / 24B119 : c'est une empreinte forte,
mais une **présomption**, pas une preuve de contenu. L'analyse a donc été menée
sur cet IPSW officiel, intégralement vérifié. Le blocage MEGA et la procédure de
déblocage sont documentés dans [docs/mega-rom-link.md](docs/mega-rom-link.md).

Rapport complet : [docs/firmware-analysis.md](docs/firmware-analysis.md).

## Structure du dépôt

```
iOS-tegu/
├── README.md                     ce document
├── ROM.MD                        lien MEGA fourni (source d'origine, inchangé)
├── Prompt.md                     cahier des charges initial (inchangé)
├── firmware/
│   ├── README.md                 politique de publication du firmware
│   └── metadata/                 FAITS seulement : identité, inventaire, empreintes
│       ├── iphone17,3-27.2-24B119.json
│       ├── ipsw-entries.json
│       └── mega-rom-link.json
├── kernel/xnu-notes.md           analyse de portabilité XNU ↔ Tensor G4
├── boot/boot-chain-tegu.md       chaîne de démarrage du Pixel 9a face à iBoot
├── drivers/driver-matrix.md      matrice des pilotes à écrire
├── device/tegu/specs.json        matériel du Pixel 9a (sourcé)
├── tools/                        outils d'analyse (voir tools/README.md)
├── docs/
│   ├── mission-report.md         rapport final de mission (10 points)
│   ├── firmware-analysis.md      analyse détaillée du firmware
│   ├── mega-rom-link.md          diagnostic du lien MEGA
│   ├── pixel9a-hardware.md       matériel et chaîne de démarrage
│   ├── roadmap.md                feuille de route par phases
│   └── legal-and-redistribution.md
└── checksums/                    SHA-256 des artefacts du dépôt
```

## Composants réellement extraits et analysés

**Extraits et vérifiés (CRC-32 ZIP validé) :**

| Élément | Taille | SHA-256 |
|---|---|---|
| `BuildManifest.plist` | 859 708 o | `7e2a5ae21a7c857211e12d025f55deb1646f9a8cf1bc88085c5ae2408eb28320` |
| `Restore.plist` | 1 090 o | `c51048c01f5e82b03923950b72f22dfb976f3f38cf465e8256aa0068a347e240` |
| `RestoreVersion.plist` | 360 o | `01eb568727dc318f5850552d2919cd2bc3505ad0c90ff29ae10d140ec7ff3e5a` |
| `SystemVersion.plist` | 490 o | `99efb3418ec2ece8c5501bcd27dd5808f53539abb71be7fd6399630e7272caba` |

**Extrait partiellement :** en-tête IM4P du kernelcache (64 Kio, lecture
partielle assumée) → type `krnl`, description `KernelManagement_host-514.40.8`,
taille de charge utile, entropie.

**Inventorié sans extraction :** les 141 entrées de l'archive (noms, tailles,
CRC-32) et les 103 composants de l'identité d'installation.

**Non extrait — et pourquoi :**

* 4 archives `.dmg.aea` (12 192 841 728 o, 93 % du contenu) : *Apple Encrypted
  Archive*, clé fournie par la personnalisation Apple (TSS) ; aucun déchiffrement
  tenté.
* 63 images `Firmware/**` + 2 kernelcaches : conteneurs IMG4/IM4P **signés et
  chiffrés** ; la charge utile n'est pas lisible sans les clés Apple.
* 3 DMG non chiffrés (509 607 990 o) : identifiés (`RestoreRamDisk` entre autres)
  mais non montés ; leur contenu reste du logiciel Apple.
* SEP, SPTM, TXM, ExclaveOS : micrologiciels signés, non extractibles.

## Éléments manquants

1. La **clé MEGA correcte** (ou un fichier IPSW lisible) pour analyser le firmware
   exact de `ROM.MD`.
2. Les **clés de déchiffrement Apple** (IM4P) et les **tickets AEA** — hors de
   portée et volontairement non contournés.
3. Un **accès physique** à un Pixel 9a pour relever le device tree réel, les
   adresses de l'UART, du GIC et les vecteurs de démarrage.
4. Un **platform expert XNU** pour Tensor G4 (n'existe pas).
5. Un **espace utilisateur Darwin** non signé, bâti sur les sources ouvertes.

## Difficultés de compatibilité (résumé)

| Sujet | Apple (iPhone 16) | Pixel 9a | Écart |
|---|---|---|---|
| Amorçage | Boot ROM → iBoot (IMG4, TSS) | Boot ROM → XBL → ABL (UEFI, AVB 2.0) | formats et politiques incompatibles : iBoot ne s'exécute pas sur Tensor |
| Description matériel | device tree fourni par iBoot, bindings Apple | DTB du `vendor_boot`, bindings Linux | platform expert XNU à réécrire |
| Interruptions | Apple AIC/AIC2 | ARM GICv3 | pilote AIC absent côté Pixel, GIC absent côté XNU |
| Noyau | XNU arm64, pages 16 Kio, kexts signés | Linux 6.1 GKI | XNU n'a aucun pilote pour les périphériques Tensor |
| Sécurité | SEP, AMFI, keybags, APFS chiffré | Titan M2, Trusty, AVB | l'espace utilisateur iOS ne peut pas s'initialiser sans SEP |
| GPU / ISP / ANE | DCP, GFX, ISP, ANE (Apple) | Mali-G715, ISP Google | aucun pilote, aucun blob utilisable |

Analyse complète : [kernel/xnu-notes.md](kernel/xnu-notes.md),
[boot/boot-chain-tegu.md](boot/boot-chain-tegu.md),
[drivers/driver-matrix.md](drivers/driver-matrix.md).

## Travaux réalisés

* Diagnostic complet du lien MEGA (API, clé, attributs, charge utile, étendue).
* Outillage réutilisable : lecture ZIP64 distante par *Range*, extraction ciblée
  avec vérification CRC-32, vérification SHA-256 en flux avec reprise, génération
  de métadonnées publiables.
* Vérification d'intégrité de deux IPSW iOS 27.2 (iPhone17,3 et iPhone18,1) :
  tailles et SHA-256 conformes aux valeurs publiées.
* Inventaire et classification des 141 entrées, cartographie des 103 composants.
* Analyse de l'en-tête IM4P du noyau et constat de chiffrement.
* Documentation de faisabilité XNU/Tensor G4 et de la chaîne de démarrage Pixel.

## Prochaines étapes

Voir [docs/roadmap.md](docs/roadmap.md). Priorités immédiates :

1. obtenir la clé MEGA valide ou un IPSW lisible pour le firmware de `ROM.MD` ;
2. relever le device tree réel du Pixel 9a (`fastboot getvar`, `dtc` sur le DTB
   de `vendor_boot`) — sans flasher ;
3. prototyper un *platform expert* XNU minimal (GICv3, UART, timer) sous QEMU ;
4. écrire un chargeur de test (payload fastboot) qui n'écrit rien en partition
   système et n'est pas un portage iOS complet.

## Outils

```bash
python3 tools/mega_probe.py ROM.MD --json          # diagnostic du lien MEGA
python3 tools/ipsw_fetch.py info --url "$IPSW_URL" # inventaire d'un IPSW distant
python3 tools/ipsw_stream_verify.py --url "$IPSW_URL" \
    --expected-size 12883623203 \
    --expected-sha256 62158ad39a22fca5620deeb407cf367cab1775cf1c2fbbdf627321383af78f8b \
    --log out/logs/verify.log
```

Voir [tools/README.md](tools/README.md).

## Limites légales

Aucun composant Apple n'est redistribué : ni binaire, ni image, ni clé. Seuls des
faits techniques (noms de fichiers, tailles, empreintes, versions) sont publiés.
Aucune protection cryptographique ni signature n'a été contournée. Voir
[docs/legal-and-redistribution.md](docs/legal-and-redistribution.md).

## Empreintes

`checksums/SHA256SUMS` couvre l'ensemble des fichiers publiés de ce dépôt ;
`checksums/firmware-entries.sha256` couvre les entrées de firmware réellement
extraites (référence uniquement, contenu non redistribué).
