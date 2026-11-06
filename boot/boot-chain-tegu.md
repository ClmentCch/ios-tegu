# Chaîne de démarrage du Pixel 9a face à celle d'un iPhone

## 1. Chaîne Apple (référence : l'IPSW analysé)

```
Boot ROM (SoC, immuable)
  └─ LLB              (Low-Level Bootloader, IMG4 signé)
      └─ iBoot        (IMG4 signé + personnalisé via TSS)
          ├─ DeviceTree (IM4P, fourni à XNU)
          ├─ SEP / SPTM / TXM
          └─ kernelcache  (IM4P chiffré, Mach-O XNU)
```

Caractéristiques lues dans le manifeste de l'IPSW iPhone17,3 / 27.2 / 24B119 :

* presque tous les composants portent `Personalize: true` ;
* les règles de restauration exigent `ApRequiresImage4` et un ticket de
  personnalisation (TSS) lié au nonce de l'appareil ;
* `RequiresNonceSlot: true`, `RequiresUIDMode: true`, `RestoreAttestationMode: 8` ;
* chaque image possède un `Digest` SHA-1 et un `Trusted` dans le manifeste ;
* le noyau lui-même est chiffré (entropie 7,983 bit/octet mesurée).

**Conséquence :** ces binaires ne sont pas seulement signés, ils sont
*personnalisés*. Même déchiffrés, ils refusent de s'exécuter sur un SoC qui n'est
pas celui pour lequel le ticket a été émis. Aucune manipulation côté Pixel ne
peut produire un tel ticket.

## 2. Chaîne Pixel 9a

```
Boot ROM (SoC Tensor G4, immuable)
  └─ XBL  (primary / secondary bootloader)
      └─ ABL  (Android Bootloader, base UEFI, fastboot, AVB 2.0)
          ├─ vbmeta / vbmeta_system / vbmeta_vendor  (vérification AVB)
          ├─ boot.img          (noyau Linux + ramdisk générique)
          ├─ init_boot.img     (ramdisk générique)
          ├─ vendor_boot.img   (DTB + ramdisk vendor)
          └─ dtbo              (overlays de device tree)
```

Points documentés publiquement :

* partitions **A/B** (deux slots) avec bascule automatique en cas d'échec ;
* **partitions dynamiques** dans `super` (`system`, `vendor`, `product`,
  `system_ext`, `system_dlkm`, `vendor_dlkm`) ;
* **AVB 2.0** : chaîne de confiance ancrée dans la Boot ROM, état vérifié
  (vert/jaune/orange), anti-rollback ;
* `fastboot flashing unlock` (après activation de l'option OEM unlocking)
  autorise l'exécution d'images non signées ;
* l'ABL implémente fastboot et charge `boot`/`vendor_boot` selon les règles AVB.

Ces éléments sont cohérents avec la documentation LineageOS/openphone du device
`tegu` et la documentation AOSP du bootloader.

## 3. Écart fondamental

| Étape | Apple | Pixel 9a | Compatibilité |
|---|---|---|---|
| Format d'image | IMG4/IM4P personnalisé | boot image Android (header v4), DTB | **aucune** |
| Vérification | TSS + nonce + SEP | AVB 2.0 + Titan M2 | **aucune** |
| Description matériel | device tree Apple fourni par iBoot | DTB Linux dans `vendor_boot` | **bindings différents** |
| Entrée du noyau | convention iBoot (x0 = DT, MMU déjà réglée) | convention Linux (x0 = DTB, EL1/EL2, MMU off) | **à réimplémenter** |
| Console de debug | UART Apple | UART du SoC Google | **pilote à écrire** |

iBoot ne s'exécute pas sur Tensor G4 (il est lié au SoC Apple, à ses registres et
à sa ROM). Il n'existe donc aucune voie « iBoot sur Pixel ».

## 4. Voies réellement envisageables

### Voie A — payload de type UEFI depuis ABL (recommandée pour l'expérience)

ABL étant basé UEFI, un payload peut être construit comme une application UEFI
qui :

1. est chargée par fastboot (`fastboot boot`) sans écrire de partition ;
2. initialise MMU, GICv3, UART de debug, timers ;
3. construit ou adapte un device tree ;
4. saute dans une image XNU de recherche compilée pour `arm64`.

Limites : l'appareil doit être déverrouillé ; AVB doit être neutralisé ; rien de
tout cela n'est un « démarrage d'iOS » — c'est un bring-up de noyau.

### Voie B — portage du noyau Linux puis XNU en second étage

Utiliser un noyau Linux (`kexec`-like) comme chargeur pour préparer la mémoire,
puis sauter dans XNU. Plus de travail, plus de risques, aucune garantie.

### Voie C — émulation d'abord

Faire tourner XNU sous QEMU (`virt`, GICv3, PL011) avec un platform expert
« générique ARM » : c'est la seule voie où l'on peut itérer vite, sans matériel,
et où chaque étape est vérifiable. **C'est par là que le projet doit commencer.**

## 5. Ce qu'il ne faut pas attendre

* Aucune image de l'IPSW ne démarrera sur le Pixel : la personnalisation TSS est
  liée au SoC Apple.
* Aucun « dual boot iOS/Android » n'est réaliste : il faudrait le noyau, les
  pilotes, l'espace utilisateur et la chaîne de confiance Apple.
* Le déverrouillage du bootloader Pixel n'apporte aucune capacité Apple : il
  autorise seulement du code *que nous écrivons*.

## 6. Prérequis matériels et logiciels pour la suite

1. Un Pixel 9a avec bootloader déverrouillable (aucune modification effectuée par
   ce projet à ce jour).
2. Le DTB réel extrait de `vendor_boot.img` (adresses GIC/UART/timers).
3. Une chaîne de compilation croisée `aarch64-none-elf` pour les payloads.
4. Un build XNU de recherche pour `arm64`, avec un platform expert de test.
5. Une console série (UART de debug) ou, à défaut, un log persistant en mémoire
   relu au redémarrage.
