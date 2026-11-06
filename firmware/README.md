# Firmware — politique et contenu

## Ce que contient ce dossier

Uniquement des **métadonnées** : identité du firmware, inventaire des entrées,
empreintes, cartographie des composants, diagnostic du lien MEGA.

| Fichier | Contenu |
|---|---|
| `metadata/iphone17,3-27.2-24B119.json` | identité produit, statistiques d'archive, 103 composants (chemin, `Personalize`, `Trusted`, digest SHA-1), informations de noyau, archives chiffrées |
| `metadata/ipsw-entries.json` | les 141 entrées de l'archive : nom, taille, CRC-32, méthode de compression |
| `metadata/mega-rom-link.json` | résultat du diagnostic du lien MEGA (tailles, sondes, `key_valid`) |

## Ce que ce dossier ne contient pas — volontairement

* Aucun binaire Apple, aucune image, aucun DMG, aucun kernelcache complet.
* Aucun `.plist` Apple tel quel.
* Aucune clé, aucun secret, aucun ticket de personnalisation.

Raison : les composants du firmware sont propriétaires et leur redistribution
n'est pas autorisée. Voir `docs/legal-and-redistribution.md`.

## Vérifier soi-même

```bash
# Recalcule le SHA-256 de l'archive complète et le compare à la valeur publiée
python3 tools/ipsw_stream_verify.py \
  --url "$IPSW_URL" \
  --expected-size 12883623203 \
  --expected-sha256 62158ad39a22fca5620deeb407cf367cab1775cf1c2fbbdf627321383af78f8b

# Compare l'inventaire local aux empreintes du dépôt
jq -r '.source.sha256' firmware/metadata/iphone17,3-27.2-24B119.json
```

## Provenance

| Champ | Valeur |
|---|---|
| Origine analysée | CDN public Apple, image de restauration `iPhone17,3_27.2_24B119_Restore.ipsw` |
| Origine demandée par le cahier des charges | lien MEGA de `ROM.MD` — **inexploitable** (clé invalide) |
| Lien entre les deux | même taille exacte (12 883 623 203 o) : présomption, pas preuve |

Le détail du blocage et la procédure de déblocage figurent dans
`docs/mega-rom-link.md`.
