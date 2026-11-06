# iOS-tegu — outils

Tous les outils sont en Python 3 (≥ 3.10) et n'utilisent que la bibliothèque
standard, à l'exception de `mega_probe.py` qui requiert `cryptography`.

| Outil | Rôle | Réseau |
|---|---|---|
| `mega_probe.py` | Interroge un lien MEGA public, récupère la taille réelle, tente le déchiffrement des attributs et du premier bloc, vérifie que l'objet est servi sur toute sa longueur. Ne télécharge jamais l'objet entier. | MEGA |
| `ipsw_fetch.py` | Lecteur ZIP/ZIP64 distant : `info`, `list`, `extract` par requêtes HTTP Range. Vérifie le CRC-32 de chaque entrée récupérée intégralement. | CDN Apple |
| `ipsw_stream_verify.py` | Calcule le SHA-256 d'un IPSW en flux, sans le stocker, avec reprise au bon octet après coupure, puis compare taille et empreinte attendues. | CDN Apple |
| `ipsw_report.py` | Transforme l'inventaire + les métadonnées extraites en rapport JSON publiable (identité produit, inventaire classé, en-tête IM4P, empreintes). | aucun |

## Exemples

```bash
# 1. Diagnostic du lien fourni par ROM.MD
python3 tools/mega_probe.py ROM.MD --json

# 2. Inventaire d'un IPSW sans le télécharger (12-13 Go)
python3 tools/ipsw_fetch.py info  --url "$IPSW_URL"
python3 tools/ipsw_fetch.py list  --url "$IPSW_URL" --json out/entries.json

# 3. Extraction ciblée + vérification CRC-32
python3 tools/ipsw_fetch.py extract --url "$IPSW_URL" \
        --name BuildManifest.plist --out-dir out/entries
python3 tools/ipsw_fetch.py extract --url "$IPSW_URL" \
        --name kernelcache.release.d47 --out-dir out/entries \
        --out-name kernelcache.head --head 65536

# 4. Vérification d'intégrité complète (aucune copie disque)
python3 tools/ipsw_stream_verify.py --url "$IPSW_URL" \
        --expected-size 12883623203 \
        --expected-sha256 62158ad39a22fca5620deeb407cf367cab1775cf1c2fbbdf627321383af78f8b \
        --log out/logs/verify.log --report out/verify.json

# 5. Rapport publiable
python3 tools/ipsw_report.py --entries out/entries.json \
        --metadata out/entries --out out/analysis.json
```

## Portée et limites

* Les outils ne déchiffrent rien : ni AEA, ni IM4P, ni le keybag. Ils lisent ce
  qui est lisible et signalent le reste.
* `--head N` récupère les N premiers octets décompressés d'une entrée ; le CRC-32
  n'est alors pas vérifiable et le rapport l'indique explicitement (`partial`).
* Aucun outil n'écrit sur le serveur distant, ne signe ni ne flashe quoi que ce
  soit.
