# Analyse du firmware iOS 27.2 (24B119)

Ce document décrit **ce qui a réellement été lu, extrait, mesuré et vérifié** sur
l'IPSW analysé, et ce qui ne l'a pas été.

## 1. Source et intégrité

| Champ | Valeur |
|---|---|
| Fichier | `iPhone17,3_27.2_24B119_Restore.ipsw` |
| URL | `https://updates.cdn-apple.com/2026FallFCS/c6c0afa0-c002-45b9-ad4c-d2db3bfa30ac/iPhone17,3_27.2_24B119_Restore.ipsw` |
| Taille | 12 883 623 203 octets |
| SHA-256 attendu | `62158ad39a22fca5620deeb407cf367cab1775cf1c2fbbdf627321383af78f8b` |
| SHA-256 recalculé | identique |
| Méthode | `tools/ipsw_stream_verify.py` : 12,9 Go relus en une passe, hachés en mémoire, sans copie disque (espace utile 9,7 Gio) |
| Durée / débit | 150,1 s / 85,8 Mo/s |
| Entrées ZIP64 | 141 (113 fichiers, 28 répertoires) |
| Total décompressé | 13 088 874 633 octets |

La même procédure a été exécutée en contrôle sur `iPhone18,1_27.2_24B119`
(iPhone 17 Pro) : 13 172 779 665 octets, SHA-256
`ac4eb036593386164d55b90886b192cccbda3f05fcf0df21bd5faa7da157693f` → identique
à la valeur publiée. L'outillage est donc validé sur deux images réelles.

**Ce que cela prouve :** le fichier analysé est exactement l'image publiée par
Apple, non corrompue, non tronquée. **Ce que cela ne prouve pas :** que le blob
MEGA de `ROM.MD` soit identique (voir `docs/mega-rom-link.md`, § 4).

## 2. Identité produit (lue dans `BuildManifest.plist` et `Restore.plist`)

| Champ | Valeur |
|---|---|
| Produit | iPhone 16 (`iPhone17,3`) |
| Version | iOS 27.2 |
| Build | `24B119` |
| Build train | `RaveB` |
| `Ap,OSLongVersion` | `24.2.119.0.0,0` |
| `RestoreVersion` | `24.2.119.0.0` |
| Device class | `d47ap` |
| Cible | `D47AP`, type `d47`, image `D47RestoreIPSW` |
| `ApBoardID` / `ApChipID` | `0x08` / `0x8140` (t8140, famille A18) |
| Security domain | `0x01` |
| Baseband | `Mav24-3.02.03.Release.bbfw` (114 158 444 o) |
| Encodage du contenu | `aea` |
| Taille image OS | 9 832 Mo (`OSDiskImageSize`) |
| Partition système minimale | 9 289 Mo |
| `Cryptex1,SystemOS` / `AppOS` | 6 026 Mo / 16 Mo |
| Restauration | `Erase`, `RequiresNonceSlot: true`, `RequiresUIDMode: true`, `RestoreAttestationMode: 8` |

Variantes d'installation déclarées (5 identités) : *Customer Erase Install*,
*Customer Upgrade Install*, *Research Customer Erase Install*, *Research Customer
Upgrade Install*, *Recovery Customer Install*. 103 composants par identité
complète, 30 pour la variante récupération.

## 3. Inventaire de l'archive

| Famille | Nombre | Octets |
|---|---|---|
| Archives chiffrées `.dmg.aea` | 4 | 12 192 841 728 |
| Images micrologiciel `Firmware/**` | 63 | 294 523 602 |
| Fichiers d'intégrité (`.root_hash`, `.trustcache`, `.mtree`, `.integrity_catalog`) | 15 | 43 152 930 |
| Métadonnées `.plist` | 26 | 1 275 019 |
| Noyaux (`kernelcache.*`) | 2 | 47 473 364 |
| DMG non chiffrés | 3 | 509 607 990 |
| Répertoires | 28 | — |

Les 4 archives `.aea` représentent **93 %** du contenu décompressé. C'est la
première constatation importante : l'essentiel du système n'est pas dans l'IPSW
sous forme lisible, mais dans des conteneurs *Apple Encrypted Archive* dont la
clé est délivrée par la personnalisation Apple.

### Les 4 archives AEA

| Fichier | Taille | Rôle (déduit du manifeste) |
|---|---|---|
| `141-10071-217.dmg.aea` | 8 992 587 776 o | volume `OS` (système principal) |
| `141-10680-227.dmg.aea` | 2 415 919 104 o | `Cryptex1,SystemOS` |
| `141-10014-240.dmg.aea` | 528 482 304 o | `Ap,ExclaveOS` |
| `141-10542-237.dmg.aea` | 255 852 544 o | volume système secondaire |

Chacune est accompagnée de son `.root_hash`, `.trustcache`, `.mtree` et/ou
`.integrity_catalog` (dont un `.mtree` de 40 037 031 o pour le volume OS).

### Les 3 DMG non chiffrés

`RestoreRamDisk` (`141-10399-240.dmg`, 245 366 811 o), `141-09491-242.dmg`
(247 463 963 o), `141-08824-244.dmg` (16 777 216 o). Ils sont identifiés mais
n'ont pas été montés : leur contenu reste du logiciel Apple, non publiable.

## 4. Noyau

| Champ | Valeur |
|---|---|
| Fichiers | `kernelcache.release.d47` (23 736 643 o), `kernelcache.research.d47` (23 736 721 o) |
| Conteneur | `IM4P`, type `krnl` |
| Description | `KernelManagement_host-514.40.8` |
| En-tête | 56 octets (DER : `IM4P`, type, description, charge utile) |
| Charge utile | 23 736 240 octets |
| Entropie mesurée sur les 65 480 premiers octets de charge utile | **7,983 bit/octet** (maximum 8,0) |

Une entropie aussi proche du maximum sur un échantillon de 64 Kio est la
signature d'une charge utile **chiffrée ou compressée de façon opaque**. Aucun
en-tête Mach-O (`0xfeedfacf`) n'apparaît. Conclusion : **le code du noyau n'est pas
lisible dans l'IPSW** ; il nécessite les clés Apple (personnalisation/TSS).

Conséquence directe pour le projet : on ne peut pas, à partir de ce firmware,
étudier le désassemblage de XNU, ses symboles ou ses extensions. Toute étude du
noyau doit se faire sur les **sources ouvertes de XNU** (Apple open source), pas
sur ce binaire.

## 5. Composants déclarés dans le manifeste

Les 103 composants de l'identité d'installation décrivent la chaîne complète :

* **Démarrage / sécurité** : `LLB`, `iBoot`, `iBSS`, `iBEC`, `iBootData`,
  `DeviceTree`, `RestoreDeviceTree`, `RestoreSEP`, `SEP`, `SepStage1`,
  `StaticTrustCache`, `RestoreTrustCache`, `Ap,SecurePageTableMonitor`,
  `Ap,TrustedExecutionMonitor`, `Ap,ExclaveOS` (+ intégrité et volume),
  `Yonkers` (patches), `Savage` (patchs B0/B2/BA/BE/BF), `ftap`, `rfts` ;
* **Noyaux** : `KernelCache`, `RestoreKernelCache` ;
* **Système** : `OS`, `SystemVolume`, `Cryptex1,SystemOS`, `Cryptex1,AppOS`,
  `Cryptex1,SystemVolume`, `Cryptex1,AppVolume`, `SystemVolume` ;
* **Périphériques** : `DCP` (affichage), `Multitouch`, `Liquid`, `LeapHaptics`,
  `MtpFirmware`, `AVE`, `ISP`, `GFX`, `ANE`, `AOP`, `AOP2`, `PMP`, `SIO`, `ANS`,
  `BMU` (baseband), `eUICC`, `USBPortController1`, `WCHFirmwareUpdater`,
  `AppleLogo`, `AudioBootChime` ;
* **Médias / récupération** : `RestoreRamDisk`, `RestoreLogo`, `RecoveryMode`.

Chaque composant porte un `Digest` SHA-1, un indicateur `Trusted`, un
`Personalize` et, pour beaucoup, un `RestoreRequestRules` décrivant les
conditions de personnalisation (mode production, `ApRequiresImage4`, ESEC/EPRO).
Ces valeurs sont reproduites dans
`firmware/metadata/iphone17,3-27.2-24B119.json`.

## 6. Ce qui a été extrait — et ce qui ne l'a pas été

**Extrait, CRC-32 vérifié :**

| Fichier | Octets | SHA-256 |
|---|---|---|
| `BuildManifest.plist` | 859 708 | `7e2a5ae21a7c857211e12d025f55deb1646f9a8cf1bc88085c5ae2408eb28320` |
| `Restore.plist` | 1 090 | `c51048c01f5e82b03923950b72f22dfb976f3f38cf465e8256aa0068a347e240` |
| `RestoreVersion.plist` | 360 | `01eb568727dc318f5850552d2919cd2bc3505ad0c90ff29ae10d140ec7ff3e5a` |
| `SystemVersion.plist` | 490 | `99efb3418ec2ece8c5501bcd27dd5808f53539abb71be7fd6399630e7272caba` |

**Extrait partiellement (lecture partielle assumée, CRC non vérifiable) :**
`kernelcache.release.d47`, 65 536 premiers octets, SHA-256
`27b0f7cecc2dc4d5f90fdf6f063c3c33859ed4d60ec148b6638b30146ea73a74`.

**Non extrait :**

* le contenu des 4 `.aea` (chiffrement AEA, clé de restauration Apple) ;
* la charge utile des 63 images `Firmware/**` et des 2 kernelcaches (IMG4/IM4P
  chiffrés) ;
* le contenu des 3 DMG (non montés, non publiables) ;
* les micrologiciels SEP/SPTM/TXM/ExclaveOS (signés, non extractibles).

Aucune de ces barrières n'a été contournée. Aucune clé n'a été recherchée, ni
utilisée, ni publiée.

## 7. Ce que l'analyse permet d'affirmer pour le projet

1. Le système iOS 27.2 tient dans ~9,8 Go de volume OS + 6 Go de cryptex, dont
   l'IPSW ne contient que la forme chiffrée : **un portage ne peut pas partir de
   ce contenu**.
2. La chaîne de démarrage Apple est entièrement personnalisée (`Personalize:
   true`, `ApRequiresImage4`, nonce slot, UID mode) : ces images ne démarreront
   que sur un SoC Apple avec un ticket TSS valide. Elles sont **inutilisables**
   sur un Tensor G4, même déchiffrées.
3. Le noyau lui-même est le seul élément conceptuellement portable, et il doit
   être reconstruit depuis les **sources XNU**, pas extrait d'un IPSW.
4. Les seuls éléments réutilisables sans clé Apple sont les **métadonnées** :
   versions, noms de composants, tailles, digests, règles de restauration. C'est
   exactement ce que publie ce dépôt.

## 8. Reproduire

```bash
URL=https://updates.cdn-apple.com/2026FallFCS/c6c0afa0-c002-45b9-ad4c-d2db3bfa30ac/iPhone17,3_27.2_24B119_Restore.ipsw
python3 tools/ipsw_fetch.py list --url "$URL" --json out/entries.json
python3 tools/ipsw_fetch.py extract --url "$URL" --name BuildManifest.plist --out-dir out/entries
python3 tools/ipsw_report.py --entries out/entries.json --metadata out/entries --out out/analysis.json
```
