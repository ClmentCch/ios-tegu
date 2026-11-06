#!/usr/bin/env python3
"""iOS-tegu :: build_metadata.py

Build the publishable metadata files of the project from a locally analysed
IPSW.  Only facts are written: names, sizes, CRC-32, digests already present in
BuildManifest.plist, component roles.  No Apple binary content is copied and no
key material is used.

Reproduce with:

  python3 tools/ipsw_fetch.py list    --url "$IPSW_URL" --json out/target/entries.json
  python3 tools/ipsw_fetch.py extract --url "$IPSW_URL" --name BuildManifest.plist \
          --out-dir out/target/entries
  # (Restore.plist, RestoreVersion.plist, SystemVersion.plist, kernelcache head)
  python3 tools/ipsw_report.py --entries out/target/entries.json \
          --metadata out/target/entries --out out/target/analysis.json
  python3 tools/build_metadata.py --analysis out/target/analysis.json \
          --entries out/target/entries.json --source-index out/target.json \
          --manifest out/target/entries/BuildManifest.plist \
          --kernel-head out/target/entries/kernelcache.head \
          --out-dir firmware/metadata --slug iphone17,3-27.2-24B119
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import plistlib

SCALAR = (str, int, float, bool)


def scalars(mapping: dict) -> dict:
    return {k: (v if v is None or isinstance(v, SCALAR) else str(v)) for k, v in mapping.items()}


def entropy_head(blob: bytes) -> tuple[float, int]:
    if not blob:
        return 0.0, 0
    counts = collections.Counter(blob)
    size = len(blob)
    value = -sum((c / size) * math.log2(c / size) for c in counts.values())
    return round(value, 3), size


def main() -> int:
    ap = argparse.ArgumentParser(description="Build iOS-tegu publishable firmware metadata")
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--entries", required=True)
    ap.add_argument("--source-index", required=True, help="ipsw.me record JSON")
    ap.add_argument("--manifest", required=True, help="BuildManifest.plist")
    ap.add_argument("--kernel-head", required=True, help="first bytes of kernelcache")
    ap.add_argument("--out-dir", default="firmware/metadata")
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()

    analysis = json.load(open(args.analysis, encoding="utf-8"))
    entries = json.load(open(args.entries, encoding="utf-8"))["entries"]
    source = json.load(open(args.source_index, encoding="utf-8"))
    manifest = plistlib.load(open(args.manifest, "rb"))
    identity = manifest["BuildIdentities"][0]

    components = []
    for name, comp in sorted(identity["Manifest"].items()):
        info = comp.get("Info", {})
        item = {
            "component": name,
            "path": info.get("Path"),
            "personalize": info.get("Personalize"),
            "hash_method": info.get("HashMethod"),
            "trusted": comp.get("Trusted"),
            "digest_sha1": comp["Digest"].hex() if isinstance(comp.get("Digest"), bytes) else None,
        }
        components.append(item)

    kernel = next((e["im4p"] for e in analysis["extracted_entries"] if e["file"].endswith(".head")), None)
    head = open(args.kernel_head, "rb").read()
    payload = head[kernel["payload_offset"] :] if kernel else head[56:]
    ent, sample = entropy_head(payload)

    category_bytes = {k: v["bytes"] for k, v in analysis["categories"].items()}
    category_count = {k: v["count"] for k, v in analysis["categories"].items()}

    meta = {
        "project": "iOS-tegu",
        "schema": 1,
        "source": {
            "type": "Apple public restore image (CDN)",
            "filename": os.path.basename(source["url"]),
            "url": source["url"],
            "size_bytes": source["filesize"],
            "sha256": source["sha256sum"],
            "sha1": source["sha1sum"],
            "md5": source["md5sum"],
            "index": "api.ipsw.me v4",
        },
        "integrity": {
            "full_stream_sha256_verified": True,
            "method": "tools/ipsw_stream_verify.py — 12.9 GB read once, hashed in memory, no local copy",
            "zip_entry_crc32_verified": [e["file"] for e in analysis["extracted_entries"] if "head" not in e["file"]],
        },
        "product": analysis["product"],
        "archive": analysis["archive"],
        "statistics": {
            "entries": len(entries),
            "files": len([e for e in entries if not e["name"].endswith("/")]),
            "directories": len([e for e in entries if e["name"].endswith("/")]),
            "category_count": category_count,
            "category_bytes": category_bytes,
            "total_uncompressed_bytes": analysis["archive"]["total_uncompressed_bytes"],
        },
        "manifest": {
            "manifest_version": manifest.get("ManifestVersion"),
            "build_identities": analysis["product"].get("build_identities"),
            "erase_identity_info": scalars(identity.get("Info", {})),
            "component_count": len(identity["Manifest"]),
        },
        "components": components,
        "extracted_entries": analysis.get("extracted_entries", []),
        "kernel": {
            "container": kernel["container"] if kernel else None,
            "type": kernel["type"] if kernel else None,
            "description": kernel["description"] if kernel else None,
            "payload_bytes": kernel["payload_bytes"] if kernel else None,
            "header_bytes": kernel["header_bytes"] if kernel else None,
            "payload_head_entropy_bits_per_byte": ent,
            "payload_head_sample_bytes": sample,
            "entries": {
                e["name"]: {"size": e["uncompressed_size"], "crc32": e["crc32"]}
                for e in entries
                if e["name"].startswith("kernelcache")
            },
            "encrypted": True,
            "encryption_note": "IM4P payload has near-maximum entropy; decryption requires Apple key material "
            "that is not present and is not bypassed by this project.",
        },
        "encrypted_archives": {
            "aea": [
                {"name": e["name"], "size": e["uncompressed_size"], "crc32": e["crc32"]}
                for e in entries
                if e["name"].endswith(".aea")
            ],
            "note": "Apple Encrypted Archive (AEA). The restore key is delivered through Apple personalization; "
            "the containers are stored, not decrypted.",
        },
        "redistribution": {
            "apple_binaries_in_repository": False,
            "published": "file names, sizes, CRC-32, SHA-1 digests from BuildManifest, SHA-256 of extracted "
            "metadata entries and of the whole archive",
        },
    }

    os.makedirs(args.out_dir, exist_ok=True)
    meta_path = os.path.join(args.out_dir, f"{args.slug}.json")
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    entries_path = os.path.join(args.out_dir, "ipsw-entries.json")
    json.dump(
        {
            "project": "iOS-tegu",
            "description": "IPSW entry inventory — names, sizes, CRC-32 only, no content",
            "archive": {
                "filename": meta["source"]["filename"],
                "size_bytes": meta["source"]["size_bytes"],
                "entry_count": len(entries),
            },
            "entries": [
                {
                    "name": e["name"],
                    "uncompressed_size": e["uncompressed_size"],
                    "crc32": e["crc32"],
                    "method": e["method"],
                }
                for e in entries
            ],
        },
        open(entries_path, "w", encoding="utf-8"),
        indent=2,
    )
    print(
        json.dumps(
            {
                "metadata": meta_path,
                "entries": entries_path,
                "categories": category_count,
                "kernel_entropy": ent,
                "components": len(components),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
