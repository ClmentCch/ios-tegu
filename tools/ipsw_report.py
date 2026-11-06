#!/usr/bin/env python3
"""iOS-tegu :: ipsw_report.py

Turn the raw output of ``ipsw_fetch.py`` into a factual, publishable report about
an IPSW, without redistributing any Apple component.

Inputs
------
  --entries   JSON produced by ``ipsw_fetch.py list --json``
  --metadata  directory holding entries extracted locally (BuildManifest.plist,
              Restore.plist, kernelcache head, ...). Optional.
  --out       JSON report path
  --source    free-form label of the firmware source (e.g. "Apple CDN 27.2")

Output
------
A JSON document with:
  * product identity (version, build, supported product types, board map)
  * component inventory classified by role, with sizes and CRC-32 values
  * kernelcache IM4P header fields (type, description, payload size)
  * encryption status inferred from file names/magics (never bypassed)
  * SHA-256 of every locally extracted entry (content is *not* included)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import struct
import sys


def classify(name: str) -> str:
    lower = name.lower()
    base = os.path.basename(lower)
    if name.endswith("/"):
        return "directory"
    if lower.endswith((".plist", ".plist.sig")):
        return "metadata-plist"
    if base.endswith((".root_hash", ".trustcache", ".mtree", ".integrity_catalog")):
        return "integrity-sidecar"
    if base.startswith("kernelcache"):
        return "kernel"
    if base.endswith(".aea"):
        return "filesystem-encrypted-aea"
    if base.endswith(".dmg"):
        return "filesystem-dmg"
    if lower.startswith("firmware/") or lower.endswith((".im4p", ".img4", ".im4m", ".bbfw", ".ftab")):
        return "firmware-image"
    if "iboot" in base or "devicetree" in base or "trustcache" in base or "sep" in base:
        return "secure-boot-component"
    if base.endswith((".tip", ".nand", ".nor")):
        return "storage-image"
    return "other"


def parse_im4p(blob: bytes) -> dict | None:
    """Minimal DER reader for the IMG4 IM4P container header."""
    if len(blob) < 12:
        return None
    try:
        pos = 0
        tag, length, pos = _tlv(blob, pos)
        if tag != 0x30:
            return None
        tag, length, pos = _tlv(blob, pos)
        if tag != 0x16:
            return None
        magic = blob[pos : pos + length]
        pos += length
        tag, length, pos = _tlv(blob, pos)  # type
        im4p_type = blob[pos : pos + length].decode("ascii", "replace")
        pos += length
        tag, length, pos = _tlv(blob, pos)  # description
        description = blob[pos : pos + length].decode("ascii", "replace")
        pos += length
        tag, length, pos = _tlv(blob, pos)  # payload
        payload_len = length
        payload_start = pos
        return {
            "container": magic.decode("ascii", "replace"),
            "type": im4p_type,
            "description": description,
            "payload_bytes": payload_len,
            "payload_offset": payload_start,
            "header_bytes": payload_start,
            "payload_entropy_note": "payload is encrypted/compressed; no key material is used",
        }
    except Exception:  # noqa: BLE001
        return None


def _tlv(buf: bytes, pos: int) -> tuple[int, int, int]:
    tag = buf[pos]
    first = buf[pos + 1]
    if first < 0x80:
        return tag, first, pos + 2
    count = first & 0x7F
    length = int.from_bytes(buf[pos + 2 : pos + 2 + count], "big")
    return tag, length, pos + 2 + count


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a publishable IPSW report (iOS-tegu)")
    ap.add_argument("--entries", required=True)
    ap.add_argument("--metadata", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", default="unspecified")
    args = ap.parse_args()

    listing = json.load(open(args.entries, encoding="utf-8"))
    entries = listing["entries"]
    report: dict = {
        "tool": "iOS-tegu/ipsw_report",
        "source": args.source,
        "archive": {
            "url": listing.get("url"),
            "size_bytes": listing.get("size_bytes"),
            "entry_count": len(entries),
            "total_uncompressed_bytes": sum(e["uncompressed_size"] for e in entries),
        },
        "components": [],
    }

    by_category: dict[str, dict] = {}
    for entry in entries:
        category = classify(entry["name"])
        bucket = by_category.setdefault(category, {"count": 0, "bytes": 0})
        bucket["count"] += 1
        bucket["bytes"] += entry["uncompressed_size"]
        report["components"].append(
            {
                "name": entry["name"],
                "category": category,
                "uncompressed_size": entry["uncompressed_size"],
                "crc32": entry["crc32"],
                "method": entry["method"],
            }
        )
    report["categories"] = by_category

    # -- product identity from extracted metadata --------------------------
    metadata_dir = args.metadata
    report["extracted_entries"] = []
    report["product"] = {}
    if metadata_dir and os.path.isdir(metadata_dir):
        manifest_path = os.path.join(metadata_dir, "BuildManifest.plist")
        restore_path = os.path.join(metadata_dir, "Restore.plist")
        if os.path.exists(manifest_path):
            manifest = plistlib.load(open(manifest_path, "rb"))
            report["product"].update(
                {
                    "product_version": manifest.get("ProductVersion"),
                    "product_build": manifest.get("ProductBuildVersion"),
                    "supported_product_types": manifest.get("SupportedProductTypes"),
                    "manifest_version": manifest.get("ManifestVersion"),
                    "build_identities": [
                        {
                            "device_class": identity.get("Info", {}).get("DeviceClass"),
                            "variant": identity.get("Info", {}).get("Variant"),
                            "components": len(identity.get("Manifest", {})),
                        }
                        for identity in manifest.get("BuildIdentities", [])
                    ],
                }
            )
        if os.path.exists(restore_path):
            restore = plistlib.load(open(restore_path, "rb"))
            report["product"].update(
                {
                    "restore_product_version": restore.get("ProductVersion"),
                    "restore_product_build": restore.get("ProductBuildVersion"),
                    "device_map": restore.get("DeviceMap"),
                    "system_restore_file_systems": restore.get("SystemRestoreImageFileSystems"),
                }
            )
        for name in sorted(os.listdir(metadata_dir)):
            path = os.path.join(metadata_dir, name)
            if not os.path.isfile(path):
                continue
            item = {"file": name, "bytes": os.path.getsize(path), "sha256": sha256_file(path)}
            if name.startswith("kernelcache") and name.endswith(".head"):
                item["im4p"] = parse_im4p(open(path, "rb").read())
            report["extracted_entries"].append(item)

    report["redistribution"] = {
        "committed_to_repository": False,
        "reason": "Apple firmware components are proprietary; only derived metadata, "
        "file names, sizes, CRC-32 and SHA-256 values are published.",
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(json.dumps(report, indent=2, ensure_ascii=False))
    print(
        json.dumps(
            {
                "out": args.out,
                "entries": len(entries),
                "categories": {k: v["count"] for k, v in report["categories"].items()},
                "product": report["product"].get("product_version"),
                "build": report["product"].get("product_build"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
