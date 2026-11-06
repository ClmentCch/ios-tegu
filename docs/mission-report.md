# Rapport final de mission — iOS-tegu

Ce rapport répond point par point aux dix questions du cahier des charges. Il
distingue systématiquement ce qui a été **vérifié**, ce qui est **déduit** et ce
qui **n'a pas été fait**.

## 1. Le lien MEGA a-t-il fonctionné ?

**Partiellement : l'objet est accessible, mais son contenu est indéchiffrable.**

* Le handle `k7gATJDD` est résolu par l'API MEGA ; la taille réelle est
  **12 883 623 203 octets** (11,999 Gio).
* L'URL de téléchargement est délivrée ; le serveur répond `206` sur toute
  l'étendue du fichier (sondes à 0 %, 25 %, 50 %, fin−4096, fin−16 : 5/5).
* **La clé de 32 octets contenue dans l'URL ne déchiffre pas l'objet.** Les
  attributs ne contiennent pas le marqueur `MEGA{`, et la charge utile déchiffrée
  ne commence ni par `PK\x03\x04` (ZIP) ni par un magic IMG4.
* Huit variantes de dérivation (AES-128/256, CBC/CTR, IV nul ou `key[16:32]`,
  compteur BE/LE) ont été testées : toutes échouent.

**Ce qui manque précisément : la clé MEGA correcte pour le handle `k7gATJDD`.**
Aucune autorisation, aucun compte, aucune confirmation n'est demandé par le lien :
le blocage est uniquement une question de clé. Voir `docs/mega-rom-link.md`.

## 2. Le firmware IPSW a-t-il été téléchargé intégralement ?

**Non — et il ne pouvait pas l'être de façon utile.** Deux raisons factuelles :

1. le flux MEGA est indéchiffrable (point 1), donc le télécharger ne produirait
   aucun firmware ;
2. l'espace disque utile de l'environnement d'analyse est de 9,7 Gio pour un objet
   de 12,0 Gio ; le débit mesuré sur ce lien (~0,7 Mo/s) imposerait environ
   5 heures de transfert pour un résultat inexploitable.

En revanche, l'IPSW correspondant **le plus probablement** visé a été
intégralement vérifié depuis le CDN public d'Apple :

* `iPhone17,3_27.2_24B119_Restore.ipsw` — 12 883 623 203 octets, **taille
  identique à l'octet près** à celle de l'objet MEGA ;
* SHA-256 recalculé sur le flux complet : `62158ad3…8f8b` → **identique** à la
  valeur publiée ;
* aucune copie disque conservée (contrainte d'espace), mais lecture complète et
  hachage en une passe.

Un second IPSW (iPhone 18,1 / 27.2 / 24B119) a servi de contrôle :
13 172 779 665 octets, SHA-256 conforme. L'outillage est donc validé deux fois.

## 3. Modèle d'iPhone, version iOS et build identifiés

| Champ | Valeur | Niveau de preuve |
|---|---|---|
| Modèle | **iPhone 16 (`iPhone17,3`)** | lu dans `BuildManifest.plist`/`Restore.plist` de l'IPSW vérifié |
| Version | **iOS 27.2** | lu (`ProductVersion`) |
| Build | **24B119** | lu (`ProductBuildVersion`) |
| Build train | `RaveB` | lu (`Info.BuildTrain`) |
| Plateforme | `t8140`, board `d47ap`, CPID `0x8140`, BDID `0x08`, SDOM `1` | lu |
| Restore version | `24.2.119.0.0` | lu (`RestoreVersion.plist`) |

**Réserve importante :** ces valeurs sont celles de l'IPSW officiel dont la
taille coïncide exactement avec celle du blob MEGA. Elles ne sont **pas** issues
du déchiffrement du blob MEGA, qui reste impossible. La correspondance est une
empreinte forte, pas une preuve de contenu.

## 4. Éléments réellement extraits et analysés

**Extraits, avec CRC-32 ZIP vérifié :**

| Fichier | Octets | SHA-256 |
|---|---|---|
| `BuildManifest.plist` | 859 708 | `7e2a5ae21a7c857211e12d025f55deb1646f9a8cf1bc88085c5ae2408eb28320` |
| `Restore.plist` | 1 090 | `c51048c01f5e82b03923950b72f22dfb976f3f38cf465e8256aa0068a347e240` |
| `RestoreVersion.plist` | 360 | `01eb568727dc318f5850552d2919cd2bc3505ad0c90ff29ae10d140ec7ff3e5a` |
| `SystemVersion.plist` | 490 | `99efb3418ec2ece8c5501bcd27dd5808f53539abb71be7fd6399630e7272caba` |

**Extrait partiellement :** en-tête IM4P de `kernelcache.release.d47` (64 Kio) →
conteneur `IM4P`, type `krnl`, description `KernelManagement_host-514.40.8`,
charge utile 23 736 240 octets, entropie 7,983 bit/octet (chiffrée).

**Inventoriés et analysés sans extraction :** les 141 entrées de l'archive
(noms, tailles, CRC-32) et les 103 composants de l'identité d'installation
(chemin, `Personalize`, `Trusted`, digest SHA-1, règles de restauration).

**Non extraits, avec justification :**

| Bloc | Taille | Raison |
|---|---|---|
| 4 archives `.dmg.aea` | 12 192 841 728 o (93 % du total) | chiffrement AEA, clé de restauration Apple |
| 63 images `Firmware/**` | 294 523 602 o | IMG4/IM4P signés et chiffrés |
| 2 kernelcaches | 47 473 364 o | charge utile chiffrée |
| 3 DMG non chiffrés | 509 607 990 o | contenu Apple, non publiable ; non montés |
| SEP / SPTM / TXM / ExclaveOS | — | micrologiciels signés, non extractibles |

Aucune protection n'a été contournée, aucune clé Apple utilisée.

## 5. Structure créée pour iOS-tegu

```
iOS-tegu/
├── README.md
├── ROM.MD                              (inchangé)
├── Prompt.md                           (inchangé)
├── .gitignore
├── firmware/README.md
│   └── metadata/
│       ├── iphone17,3-27.2-24B119.json
│       ├── ipsw-entries.json
│       └── mega-rom-link.json
├── kernel/xnu-notes.md
├── boot/boot-chain-tegu.md
├── drivers/driver-matrix.md
├── device/tegu/specs.json
├── tools/
│   ├── README.md
│   ├── mega_probe.py
│   ├── ipsw_fetch.py
│   ├── ipsw_stream_verify.py
│   ├── ipsw_report.py
│   └── build_metadata.py
├── docs/
│   ├── mission-report.md
│   ├── firmware-analysis.md
│   ├── mega-rom-link.md
│   ├── pixel9a-hardware.md
│   ├── roadmap.md
│   └── legal-and-redistribution.md
└── checksums/
    ├── SHA256SUMS
    └── firmware-entries.sha256
```

Aucun dossier vide, aucun fichier fictif.

## 6. Fichiers publiés et emplacement

Tous les fichiers ci-dessus sont publiés **dans le dépôt GitHub** `iOS-tegu`
(branche `main`). Ils sont soit originaux (scripts, documentation), soit des
métadonnées factuelles dérivées du firmware (versions, tailles, empreintes).

Aucun binaire Apple n'est publié, ni dans le dépôt, ni en pièce jointe.

## 7. Méthode de publication utilisée

**Cas A du cahier des charges : dépôt GitHub uniquement. Aucune Release.**

Justification : le nombre de fichiers extraits dont la redistribution est
autorisée est **zéro**. Il n'existe donc aucun fichier extrait à placer dans le
dépôt ou dans une Release. Les artefacts du projet (scripts, docs, métadonnées)
sont tous très en dessous des limites GitHub (le plus gros fichier fait moins de
40 Ko, contre un avertissement à 50 Mo et un blocage à 100 Mo).

Aucune Release n'a été créée : une Release sans contenu publiable serait
trompeuse. La règle « une seule Release » reste applicable si un futur artefact
publiable (par exemple un payload compilé par le projet) dépasse la limite du
dépôt.

## 8. Fichiers non publiés et raisons

| Fichier | Raison de non-publication |
|---|---|
| `BuildManifest.plist`, `Restore.plist`, `RestoreVersion.plist`, `SystemVersion.plist` | fichiers Apple propriétaires ; seuls leurs faits et empreintes sont publiés |
| en-tête de `kernelcache.release.d47` | contenu Apple ; seule la description IM4P est publiée |
| 4 `.dmg.aea`, 63 images `Firmware/**`, 3 DMG, 2 kernelcaches | propriété intellectuelle Apple + chiffrement/signature |
| le blob MEGA lui-même | indéchiffrable (clé invalide) et non redistribuable |
| journaux bruts de téléchargement | volumineux et sans valeur ajoutée ; les résultats sont résumés dans les métadonnées |

## 9. Analyses de compatibilité avec le Pixel 9a

**Conclusion : iOS n'est pas portable sur Pixel 9a ; XNU/Darwin l'est
partiellement, au prix d'un travail de plusieurs années.**

| Verrou | Détail | Verdict |
|---|---|---|
| Personnalisation TSS | images liées au SoC Apple et au nonce (`ApRequiresImage4`, `RequiresNonceSlot`) | **impossible** sur Tensor |
| SEP/AMFI | keybags, Data Protection, validation de signature | **impossible** sans équivalent matériel |
| APFS chiffré | volume OS livré en `.aea` (93 % du contenu) | **impossible** sans clé Apple |
| Chaîne de démarrage | iBoot/IMG4 vs ABL/AVB 2.0 | **incompatible** ; iBoot ne s'exécute pas sur Tensor |
| Interruptions | AIC Apple vs GICv3 | pilote à écrire des deux côtés |
| Device tree | bindings Apple vs DTB Linux | platform expert à réécrire |
| Pilotes | DCP, ANE, ISP, NVMe Apple vs DDIC, Mali, ISP Google, UFS | aucun pilote commun |
| CPU/ISA | ARMv8-A de part et d'autre | **compatible** (arm64, PAC disponible) |
| Timers | ARM generic timer | **compatible** |

Détails : `kernel/xnu-notes.md`, `boot/boot-chain-tegu.md`,
`drivers/driver-matrix.md`.

## 10. Prochaines étapes techniques

1. **Débloquer la source** : obtenir la clé MEGA valide, vérifiée par
   `tools/mega_probe.py` (`key_valid: true`).
2. **Relever le matériel** du Pixel 9a sans le modifier : `fastboot getvar all`,
   extraction et décompilation du DTB de `vendor_boot.img` (UART, GIC, watchdog,
   timers, UFS).
3. **Bring-up XNU sous QEMU** (`virt`, GICv3, PL011) : bannière XNU reproductible.
4. **Platform expert « tegu »** : UART réel, GICv3, timer, watchdog, carte mémoire.
5. **Stockage UFS en lecture seule** comme première preuve non triviale.
6. **Espace utilisateur Darwin** minimal (libSystem, launchd, shell).
7. À chaque étape : preuve archivée, aucune revendication sans mesure.

## Annexes — vérifications exécutées

| Vérification | Résultat |
|---|---|
| SHA-256 complet iPhone17,3 27.2 24B119 | conforme (`62158ad3…`) |
| SHA-256 complet iPhone18,1 27.2 24B119 | conforme (`ac4eb036…`) |
| CRC-32 des 4 plists extraits | conformes |
| Lecture d'en-tête IM4P | conforme, charge utile chiffrée |
| Sondes d'étendue MEGA | 5/5 en `206` |
| Déchiffrement MEGA (8 variantes) | échec → `key_valid: false` |
| Compilation des scripts Python | `python3 -m py_compile` OK |
| Validité JSON des métadonnées | `jq` OK |
