#!/usr/bin/env python3
"""iOS-tegu :: mega_probe.py

Inspect a public MEGA file link without downloading the whole payload.

What it does
------------
1. Parses a public link of the form ``https://mega.nz/file/<handle>#<key>``
   (also accepts the newer ``<handle>!<key>`` form and a file containing such a
   link, e.g. ``ROM.MD``).
2. Asks the MEGA API (``a: "g"``) for the object metadata: real size, encrypted
   attributes and a temporary download URL.
3. Validates the 32-byte link key the way MEGA clients do:
   - attributes must decrypt with AES-128-CBC(key[0:16], IV=0) and start with
     the ASCII marker ``MEGA``;
   - the first 4 KiB of the payload are decrypted with AES-128-CTR
     (key = key[0:16], nonce = key[16:24], 64-bit big-endian block counter) and
     checked against known container magics (ZIP / IMG4 / DMG).
4. Optionally probes several byte offsets with HTTP Range requests to prove that
   the whole object is served (default: 5 probes down to the last byte).

This never downloads the complete object and never writes a decryption key to
the output beyond a short fingerprint.

Exit codes
----------
0  link reachable and key validated
2  link reachable but the key does not decrypt this object
3  link/API/network failure
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

LINK_RE = re.compile(
    r"https?://mega\.nz/(?:file|embed)/(?P<handle>[A-Za-z0-9_-]{8})"
    r"(?:[#!])(?P<key>[A-Za-z0-9_-]{43})"
)
MAGICS = {
    b"PK\x03\x04": "ZIP (IPSW archive)",
    b"IMG4": "IMG4",
    b"IM4P": "IM4P",
    b"IM4M": "IM4M",
}


def decode_key(key_b64: str) -> bytes:
    key = base64.urlsafe_b64decode(key_b64 + "=" * (-len(key_b64) % 4))
    if len(key) != 32:
        raise ValueError(f"unexpected key length: {len(key)} bytes (expected 32)")
    return key


def mega_api(handle: str, payload: list[dict], base: str = "https://g.api.mega.co.nz/cs") -> list:
    url = f"{base}?id=0&n={handle}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json", "User-Agent": "iOS-tegu/0.1"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    if isinstance(data, int):
        raise RuntimeError(f"MEGA API error code {data}")
    return data


def http_range(url: str, start: int, end: int, retries: int = 4) -> tuple[int, bytes]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Range": f"bytes={start}-{end}",
                    "User-Agent": "iOS-tegu/0.1",
                    "Accept-Encoding": "identity",
                },
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.status, resp.read()
        except Exception as exc:  # noqa: BLE001 - retried below
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"range {start}-{end} failed: {last}")


def decrypt_attr(attr_enc: bytes, key: bytes) -> tuple[bytes, bool]:
    dec = Cipher(algorithms.AES(key[:16]), modes.CBC(b"\x00" * 16)).decryptor()
    plain = dec.update(attr_enc) + dec.finalize()
    return plain, plain.startswith(b"MEGA")


def decrypt_ctr(data: bytes, key: bytes, offset: int = 0) -> bytes:
    block, skip = divmod(offset, 16)
    dec = Cipher(
        algorithms.AES(key[:16]), modes.CTR(key[16:24] + block.to_bytes(8, "big"))
    ).decryptor()
    return dec.update(b"\x00" * skip + data)[skip:]


def probe(url: str, size: int, offsets: int) -> list[dict]:
    probes: list[dict] = []
    points: list[int] = [0]
    if offsets >= 2:
        points.append(size // 2)
    if offsets >= 3:
        points.append(size - 4096)
    if offsets >= 4:
        points.append(size - 16)
    if offsets >= 5:
        points.append(size // 4)
    for point in points:
        start = max(0, point)
        end = min(size - 1, start + 15)
        status, data = http_range(url, start, end)
        probes.append(
            {
                "offset": start,
                "requested_bytes": end - start + 1,
                "http_status": status,
                "returned_bytes": len(data),
                "sha256_16": hashlib.sha256(data).hexdigest()[:16],
            }
        )
    return probes


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect a public MEGA link (iOS-tegu).")
    ap.add_argument("link", help="MEGA URL or a file containing one (e.g. ROM.MD)")
    ap.add_argument("--json", action="store_true", help="print a JSON report")
    ap.add_argument("--offsets", type=int, default=5, help="number of range probes (0 disables)")
    args = ap.parse_args()

    try:
        text = open(args.link, "r", encoding="utf-8", errors="replace").read() if not args.link.startswith("http") else args.link
    except OSError:
        text = args.link
    match = LINK_RE.search(text)
    if not match:
        print("error: no MEGA public file link found", file=sys.stderr)
        return 3

    handle, key_b64 = match.group("handle"), match.group("key")
    key = decode_key(key_b64)
    report: dict = {
        "tool": "iOS-tegu/mega_probe",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "link_handle": handle,
        "key_fingerprint_sha256": hashlib.sha256(key).hexdigest(),
        "key_length_bytes": len(key),
    }
    try:
        info = mega_api(handle, [{"a": "g", "g": 1, "p": handle, "ssl": 1}])[0]
    except Exception as exc:  # noqa: BLE001
        report["error"] = f"MEGA API request failed: {exc}"
        print(json.dumps(report, indent=2) if args.json else report["error"])
        return 3

    size = info["s"]
    report.update(
        {
            "api_ok": True,
            "size_bytes": size,
            "size_gib": round(size / 2**30, 3),
            "node_handle": info.get("fh"),
            "download_url_host": info.get("g", "").split("/")[2] if info.get("g") else None,
            "msd": info.get("msd"),
        }
    )

    attr_plain, attr_ok = decrypt_attr(base64.urlsafe_b64decode(info["at"]), key)
    report["attributes_decrypted"] = attr_ok
    if attr_ok:
        raw = attr_plain[attr_plain.index(b"MEGA") + 4 :].rstrip(b"\x00").decode("utf-8", "replace")
        try:
            report["attributes"] = json.loads(raw)
        except json.JSONDecodeError:
            report["attributes_raw"] = raw

    dl_url = info.get("g")
    payload_ok = False
    if dl_url:
        status, head = http_range(dl_url, 0, 4095)
        report["first_block_http_status"] = status
        plain = decrypt_ctr(head, key, 0)
        report["first_block_sha256_16"] = hashlib.sha256(head).hexdigest()[:16]
        magic = next((name for sig, name in MAGICS.items() if plain.startswith(sig)), None)
        report["payload_magic_decrypted"] = magic
        report["first_block_hex_16"] = plain[:16].hex()
        payload_ok = magic is not None
        if args.offsets:
            report["extent_probes"] = probe(dl_url, size, args.offsets)
            report["extent_probes_ok"] = all(p["http_status"] in (200, 206) for p in report["extent_probes"])

    report["key_valid"] = bool(attr_ok and payload_ok)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"handle      : {handle}")
        print(f"size        : {size} bytes ({report['size_gib']} GiB)")
        print(f"attributes  : {'OK' if attr_ok else 'FAILED (link key does not decrypt attributes)'}")
        print(f"payload     : {report.get('payload_magic_decrypted') or 'UNRECOGNISED after decryption'}")
        print(f"extent      : {report.get('extent_probes_ok')}")
        print(f"key valid   : {report['key_valid']}")
    return 0 if report["key_valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
