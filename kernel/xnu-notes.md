# XNU sur Tensor G4 : analyse de portabilité

Ce document décrit les dépendances réelles de XNU, ce qui manque sur un Pixel 9a,
et ce qui relève de l'impossible à court terme. Il ne présente aucune étape comme
réalisée.

## 1. Ce qu'est XNU

XNU est le noyau de Darwin, macOS et iOS : un hybride **Mach 3 + BSD** avec
IOKit pour les pilotes. Il est publié en sources ouvertes par Apple
(`apple-oss-distributions/xnu`), sous licence APSL 2.0. Il supporte `arm64` et
`arm64e` — mais la variante utilisée par iOS dépend fortement de la plateforme
Apple.

## 2. Dépendances de plateforme de XNU (arm64)

| Dépendance | Ce que XNU attend | Sur Pixel 9a | État |
|---|---|---|---|
| Platform expert | `pexpert/arm64` : initialisation Apple, `AppleARMPlatform` | n'existe pas | **à écrire** |
| Device tree | arbre aplati fourni par iBoot, bindings Apple (`arm-io`, `aic`, …) | DTB Linux (`vendor_boot`) | **traduction/adaptation requise** |
| Interruptions | **AIC** (Apple Interrupt Controller) | **GICv3** (standard ARM) | **pilote absent des deux côtés** |
| Timers | ARM generic timer | ARM generic timer | compatible |
| MMU | pages 16 Kio, `pmap` Apple | 4 Kio/16 Kio supportés | compatible avec adaptation |
| Console | UART Apple (`AppleS5L…`) | UART du SoC Google | **pilote à écrire** |
| Horloges / PMIC | PMGR, SMC Apple | horloges Google, PMIC | **à écrire** |
| Stockage | NVMe/ANS Apple | UFS 3.1 | **à écrire** |
| Affichage | DCP (coprocesseur d'affichage) | DDIC + Mali | **à écrire** |
| Accélération | ANE, ISP, GFX Apple | ISP Google, Mali-G715 | **aucun pilote** |
| Démarrage sécurisé | AMFI, trustcache, SEP | Titan M2, AVB | **modèle différent** |

XNU n'a **aucun** pilote GICv3, aucun pilote UFS, aucun pilote Mali, aucun
pilote de PMIC Google. Ce ne sont pas des options de compilation : ce sont des
composants à concevoir.

## 3. Le point dur : l'espace utilisateur iOS

Un noyau qui démarre ne fait pas « iOS ». L'espace utilisateur iOS dépend de :

1. **APFS chiffré** : le volume système de l'IPSW est dans une archive `.aea`
   (4 archives, 12,19 Go, soit 93 % du contenu décompressé), déchiffrée lors de
   la restauration avec une clé liée à l'appareil ;
2. **SEP** (Secure Enclave) : keybags, Data Protection, déverrouillage, clés
   dérivées du matériel ;
3. **AMFI / trustcache** : validation de la signature de chaque binaire au
   chargement ;
4. **personnalisation TSS** : les images sont liées au SoC et au nonce.

Sur un Tensor G4, aucun de ces quatre piliers n'existe. Il n'y a donc pas de
« chemin » pour exécuter les binaires iOS de l'IPSW : ce n'est pas un problème de
pilotes mais d'ancrage matériel de confiance.

**Conséquence assumée du projet :** l'objectif réaliste est un **XNU/Darwin de
recherche**, avec un espace utilisateur compilé à partir de sources ouvertes
(libSystem, launchd, shell), et **non** iOS tel quel.

## 4. Ce qui est réellement portable

| Élément | Portable ? | Commentaire |
|---|---|---|
| Sources XNU (`osfmk`, `bsd`, `libkern`, `iokit`) | **oui** | compilables pour `arm64` générique |
| Platform expert | non tel quel | nouvelle implémentation GICv3/UART/timer |
| Pilotes IOKit Apple | non | dépendants de registres Apple |
| Kexts Apple | non | liés à SEP/AMFI |
| Espace utilisateur iOS | non | APFS + AMFI + SEP |
| Outils de recherche (dtc, QEMU, lldb) | oui | standard |

## 5. Séquence de travail proposée (vérifiable à chaque étape)

**Étape 1 — QEMU (`virt`, GICv3, PL011).**
Compiler XNU `arm64` avec un platform expert minimal, obtenir la bannière XNU sur
la console série. Critère de succès : message de démarrage XNU reproductible.

**Étape 2 — Platform expert « tegu ».**
Remplacer PL011 par le vrai UART, GICv3 par les adresses réelles du Pixel,
ajouter le timer et une table mémoire issue du DTB. Critère : XNU atteint
`printf` sur le matériel réel, sans écrire en partition.

**Étape 3 — Mémoire et interruptions.**
Piloter le watchdog, gérer les IRQ du timer, vérifier la stabilité. Critère :
XNU survit 60 s avec des interruptions périodiques.

**Étape 4 — Stockage.**
Pilote UFS minimal en lecture (lecture seule d'une partition de test). Critère :
lire un secteur et vérifier son empreinte.

**Étape 5 — Espace utilisateur Darwin.**
Bâtir un userland minimal (libSystem, launchd, shell) pour `arm64` générique.
Critère : shell interactif sur console série.

## 6. Ce qui ne sera pas fait

* Aucun contournement de signature Apple, aucune extraction de clé, aucun
  déchiffrement d'IM4P ou d'AEA.
* Aucun flash d'appareil physique, aucune modification du Pixel 9a.
* Aucune revendication de « iOS fonctionnel » sans preuve reproductible.
* Aucun copier-coller de pilotes Linux GPL dans XNU : la compatibilité de licence
  (APSL 2.0 vs GPL-2.0) l'interdit ; les pilotes seront écrits à partir des
  spécifications et des données du device tree.

## 7. Estimation honnête

Le bring-up XNU sur Tensor G4 est un travail de plusieurs années-homme pour une
équipe, avec un résultat de type « noyau de recherche avec console et stockage en
lecture seule ». Un iOS utilisable sur Pixel 9a n'est pas atteignable : il
faudrait réimplémenter SEP, AMFI, APFS et toute la couche de confiance Apple.

Le projet a donc de la valeur comme **plateforme de recherche et de
documentation**, pas comme produit.
