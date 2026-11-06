# Licences, propriété intellectuelle et règle de publication

## 1. Principe appliqué

Le firmware Apple est **propriétaire**. Ce dépôt ne redistribue aucun composant
Apple : ni binaire, ni image, ni fragment de système de fichiers, ni clé.

Ce qui est publié :

* des **faits** : versions, noms de fichiers, tailles, CRC-32, digests SHA-1
  présents dans le manifeste, SHA-256 calculés par nos soins ;
* des **scripts originaux** écrits pour ce projet ;
* de la **documentation** originale.

Ce qui ne l'est pas : tout le reste du firmware.

## 2. Règle de publication du cahier des charges (§ 5)

La règle impose de choisir entre dépôt et Release selon la taille des fichiers
extraits **dont la redistribution est autorisée**.

Application :

1. Nombre de fichiers extraits dont la redistribution est autorisée : **0**.
   Les métadonnées extraites (`BuildManifest.plist`, `Restore.plist`,
   `RestoreVersion.plist`, `SystemVersion.plist`, en-tête de kernelcache) sont des
   fichiers Apple : elles ne sont pas publiées, seuls leurs faits et empreintes le
   sont.
2. Il n'existe donc **aucun fichier extrait publiable**. Le critère de taille de
   l'article 5 ne s'applique à aucun fichier.
3. Les seuls artefacts publiés sont les nôtres : scripts, documentation,
   métadonnées dérivées. Le plus gros fichier du dépôt fait moins de 40 Ko, très
   en dessous de la limite GitHub (avertissement 50 Mo, blocage 100 Mo).

**Méthode retenue : Cas A — publication dans le dépôt GitHub uniquement.**
Aucune GitHub Release n'est créée : il n'y a rien à y joindre qui ne soit pas déjà
dans le dépôt, et créer une Release vide serait trompeur.

Si un jour un fichier publiable (par exemple un payload compilé par le projet,
ou un noyau XNU compilé à partir des sources ouvertes d'Apple) dépasse la limite
du dépôt, la règle du cahier des charges s'appliquera : **une seule Release**,
aucun mélange.

## 3. Aucun contournement de protection

* Aucune clé Apple n'a été recherchée, utilisée ou publiée.
* Aucun déchiffrement IM4P, AEA, keybag ou APFS n'a été tenté.
* Aucune signature n'a été falsifiée.
* Le lien MEGA de `ROM.MD` n'a pas été contourné : son diagnostic est documenté.

Cette retenue est volontaire et conforme au cahier des charges.

## 4. Licences des composants tiers

| Composant | Licence | Usage dans ce dépôt |
|---|---|---|
| XNU (sources Apple) | APSL 2.0 | cité, non copié |
| Noyau Linux / pilotes Android | GPL-2.0 | **non copiés** (incompatibles avec APSL dans un même binaire) |
| Documentation AOSP | CC BY 2.5 / Apache 2.0 | citée |
| Outils du projet | code original | voir ci-dessous |

## 5. Licence du code original de ce dépôt

Les scripts et la documentation originales sont publiés à des fins de recherche
et de reproduction. Aucune licence permissive n'est accordée à ce stade : toute
réutilisation doit être discutée avec l'auteur du dépôt. Cette mention sera
remplacée par une licence explicite lorsque le projet sera stabilisé.

## 6. Marques

« Apple », « iPhone », « iOS », « XNU », « Darwin » sont des marques d'Apple Inc.
« Google », « Pixel », « Tensor » sont des marques de Google LLC. Ce projet n'est
ni affilié, ni approuvé, ni sponsorisé par l'une ou l'autre société.

## 7. Usage responsable

* Aucune opération de flash n'a été réalisée et aucune ne doit être réalisée sans
  sauvegarde et sans acceptation explicite du risque de brique.
* Aucun appareil n'a été modifié.
* Le contournement d'AVB ou d'un verrouillage constructeur n'entre pas dans le
  périmètre de ce dépôt.
