# Matériel : Google Pixel 9a (`tegu`)

## 1. Fiche technique vérifiée

| Domaine | Valeur | Source |
|---|---|---|
| Nom commercial | Google Pixel 9a | Google / LineageOS |
| Nom de code | `tegu` | LineageOS, AOSP (`android_device_google_tegu`) |
| Références | GXQ96 (USA), GTF7P (international), G3Y12 (Japon) | GSMArena |
| Sortie | 10 avril 2025 | GSMArena |
| SoC | Google Tensor G4, nom de code «Zuma Pro» (S5P9875, Samsung GS401), gravure 4 nm | Wikipédia (Google Tensor G4) |
| CPU | 1 × Cortex-X4 @ 3,10 GHz, 3 × Cortex-A720 @ 2,60 GHz, 4 × Cortex-A520 @ 1,92 GHz | GSMArena, LineageOS |
| ISA | ARMv8-A, aarch64 (Armv8.2+ ; PAC disponible sur ces cœurs) | ARM |
| GPU | ARM Mali-G715 MP7 | GSMArena |
| RAM | 8 Go LPDDR5X | GSMArena, newmobile |
| Stockage | 128 / 256 Go UFS 3.1 | GSMArena |
| Écran | P-OLED 6,3", 1080 × 2424, 120 Hz, HDR10+ | GSMArena |
| Batterie | 5 100 mAh | GSMArena |
| Modem | Samsung Exynos 5300 (rapporté) | 9to5Google / Android Authority |
| Sécurité | Titan M2, Trusty TEE, Android Verified Boot 2.0 | Google |
| Système d'origine | Android 15, noyau Linux 6.1 (branche `android_kernel_google_gs-6.1`) | LineageOS |

Les valeurs marquées «rapporté» proviennent de la presse spécialisée et n'ont pas
été vérifiées sur un appareil par ce projet.

## 2. Ce que le projet doit encore relever sur l'appareil

Sans flasher ni modifier l'appareil, un Pixel 9a en mode fastboot permet déjà de
collecter des faits utiles :

```bash
fastboot getvar all            # slots, versions de bootloader, anti-rollback, secure state
fastboot oem device-info       # état de verrouillage
adb shell cat /proc/device-tree/...   # si Android démarre encore
```

Puis, côté logiciel : extraire le DTB de `vendor_boot.img` (`dtc -I dtb -O dts`)
pour obtenir les adresses de base du GIC, de l'UART de debug, du watchdog, des
contrôleurs mémoire et des horloges. **Aucune de ces informations n'est
présente dans ce dépôt pour l'instant** : elles nécessitent un accès physique.

## 3. Chaîne de démarrage

Voir [../boot/boot-chain-tegu.md](../boot/boot-chain-tegu.md).

Résumé : Boot ROM → XBL → ABL (UEFI, fastboot, AVB 2.0) → `boot.img` (Linux) +
`vendor_boot.img` (DTB, ramdisk vendor) + `init_boot.img`. Partitions A/B,
partitions dynamiques (`super`), `vbmeta`/`vbmeta_system`/`vbmeta_vendor`,
`dtbo`. Le déverrouillage passe par l'option OEM unlocking puis
`fastboot flashing unlock`.

## 4. Écarts structurants avec un iPhone

| Sujet | Pixel 9a | iPhone 16 (référence de l'IPSW analysé) |
|---|---|---|
| Amorçage | UEFI/ABL, AVB 2.0, fastboot | Boot ROM + iBoot, IMG4, tickets TSS |
| Description matériel | DTB Linux (bindings devicetree) | device tree Apple fourni par iBoot |
| Noyau | Linux 6.1 GKI | XNU arm64 |
| Sécurité | Titan M2, Trusty | SEP, AMFI, keybags |
| Système de fichiers | ext4/f2fs + partitions dynamiques | APFS chiffré |
| Espace utilisateur | Android (ART) | iOS (binaires signés) |

## 5. Pourquoi ce matériel reste un candidat intéressant

* CPU ARMv8-A standard, 8 Go de RAM : suffisant pour un noyau de recherche.
* Bootloader déverrouillable officiellement (OEM unlocking) : condition minimale
  pour exécuter un noyau non signé.
* ABL basé UEFI : un payload de type application UEFI est une voie d'expérience
  plus propre qu'un détournement de iBoot.
* Documentation AOSP et arbres de device publics : le device tree et les
  partitions sont connus.

Ces atouts ne rendent pas iOS portable ; ils rendent un **bring-up XNU
expérimental** envisageable, ce qui est l'objet réel du projet.
