# Diagnostic du lien MEGA fourni par `ROM.MD`

**Conclusion courte : le lien fonctionne, l'objet est entièrement servi, mais la
clé de déchiffrement contenue dans l'URL ne correspond pas à cet objet. Aucun
contenu IPSW n'a donc pu être obtenu. Il manque la clé MEGA correcte.**

## 1. Ce que contient `ROM.MD`

```
https://mega.nz/file/k7gATJDD#xG_UVSlwEcgcw2kNzzZyxGUm0KJyT8BEgMLFP7DOTFI
```

* handle public : `k7gATJDD`
* clé : 32 octets (43 caractères base64 URL-safe), empreinte SHA-256
  `75f31ab63773bb423fec7bf181dd21a1fcde1a55e6a54876fe86a367c470b218`

L'URL du fichier n'a pas été modifiée dans le dépôt.

## 2. Ce qui fonctionne

| Test | Résultat |
|---|---|
| Résolution DNS + HTTPS vers `mega.nz` | OK |
| API MEGA `a: "g"` sur le handle `k7gATJDD` | OK |
| Taille annoncée par l'API | **12 883 623 203 octets** (11,999 Gio) |
| Handle de nœud renvoyé | `O0AOSBSnoHc` |
| URL de téléchargement temporaire | délivrée, hôte `gfs208n111.userstorage.mega.co.nz` |
| `HEAD` sur l'URL | `200`, `Content-Length: 12883623203` |
| Requêtes `Range` à 0 %, 25 %, 50 %, fin−4096, fin−16 | **5/5 en `206`**, octets renvoyés conformes |

Autrement dit : l'objet existe bien, il est complet côté serveur, et un
téléchargement intégral serait techniquement possible.

## 3. Ce qui échoue

MEGA chiffre deux choses distinctes : les **attributs** (nom, type) et la
**charge utile**. Les deux sont dérivées de la clé de 32 octets du lien.

| Variante testée | Résultat |
|---|---|
| Attributs : AES-128-CBC, clé `key[0:16]`, IV nul | échec — aucune occurrence du marqueur ASCII `MEGA{` |
| Attributs : AES-128-CBC, clé `key[0:16]`, IV `key[16:32]` | échec |
| Attributs : AES-256-CBC, clé complète, IV nul | échec |
| Charge utile : AES-128-CTR, nonce `key[16:24]`, compteur BE | 16 premiers octets `1e94bdaba02bf671…` → aucun magic connu |
| Charge utile : AES-128-CTR, compteur LE | identique à l'échec ci-dessus |
| Charge utile : AES-128-CTR, IV = `key[16:32]` | échec |
| Charge utile : AES-256-CTR, IV nul | échec |
| Charge utile : AES-128/256-CBC (au cas où) | échec |
| Octets bruts (non déchiffrés) | `08665ec10e356be9…` → aucun `PK\x03\x04` |

Un IPSW est une archive ZIP : ses quatre premiers octets sont nécessairement
`PK\x03\x04`. Après déchiffrement avec la clé du lien, on obtient du bruit. Les
attributs, eux, devraient commencer par `MEGA` ; ils ne le font pas non plus.

**Diagnostic : la clé du fragment d'URL n'est pas la clé de ce fichier.** MEGA ne
vérifie pas la clé lorsqu'il délivre une URL : un lien dont la clé est tronquée,
recopiée ou remplacée renvoie donc une URL valide vers un flux indéchiffrable.

## 4. Indice fort sur l'objet attendu

La taille annoncée, `12 883 623 203` octets, correspond **à l'octet près** à
l'IPSW public `iPhone17,3_27.2_24B119_Restore.ipsw` (iPhone 16, iOS 27.2, build
24B119). Cette correspondance exacte est très improbable par hasard.

Cela reste une **présomption fondée sur la taille**, pas une preuve : un
re-conditionnement de l'archive, un autre build ou un fichier arbitraire de même
taille ne peuvent pas être exclus sans la clé.

C'est cette présomption qui a conduit à analyser l'IPSW officiel correspondant,
intégralement vérifié par SHA-256 (voir `docs/firmware-analysis.md`).

## 5. Ce qui manque précisément pour débloquer

Une seule chose : **la clé MEGA correcte pour le handle `k7gATJDD`**, c'est-à-dire
une URL du type

```
https://mega.nz/file/k7gATJDD#<43 caractères base64 URL-safe>
```

dont la clé déchiffre réellement l'objet. Comment la vérifier en une commande :

```bash
python3 tools/mega_probe.py ROM.MD --json | jq '.key_valid, .payload_magic_decrypted'
```

Attendu en cas de succès : `key_valid: true` et
`payload_magic_decrypted: "ZIP (IPSW archive)"`. Tant que ce n'est pas le cas,
aucune analyse du firmware d'origine n'est possible — et aucune n'est simulée ici.

Remarques :

* aucune autorisation, aucun compte, aucune confirmation MEGA n'est demandée par
  le lien : le blocage est purement une question de clé ;
* le téléchargement complet (12,0 Gio) n'a pas été lancé : il aurait produit
  12 Gio de données indéchiffrables, pour un espace disque utile de 9,7 Gio dans
  l'environnement d'analyse. Le débit mesuré sur ce lien était par ailleurs de
  l'ordre de 0,7 Mo/s, soit environ 5 heures de transfert inutile ;
* l'objet n'a pas été supprimé, modifié ni réuploadé.

## 6. Reproduire le diagnostic

```bash
python3 tools/mega_probe.py ROM.MD --json
```

Le rapport complet, y compris les empreintes des sondes d'étendue, est archivé
dans `firmware/metadata/mega-rom-link.json`.
