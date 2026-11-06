#!/usr/bin/env python3
"""iOS-tegu :: ipsw_fetch.py

Read an IPSW archive remotely with HTTP Range requests (no 12-13 GB download).

IPSW files are plain ZIP archives (ZIP64 for anything above 4 GiB).  This tool
reads the end-of-central-directory record, the (ZIP64) central directory and
then only the bytes of the entries you ask for.  Every fully retrieved entry is
checked against the CRC-32 stored in the archive, so a corrupted transfer is
never silently accepted.

Subcommands
-----------
  info                       archive summary (size, entry count, ZIP64 usage)
  list                       full entry listing (JSON or table), optionally filtered
  extract --name NAME        fetch one entry into a directory
          [--head BYTES]     ... or only the first BYTES of its decompressed data

Examples
--------
  python3 tools/ipsw_fetch.py info  --url "$IPSW_URL"
  python3 tools/ipsw_fetch.py list  --url "$IPSW_URL" --json out/entries.json
  python3 tools/ipsw_fetch.py extract --url "$IPSW_URL" \
          --name BuildManifest.plist --out-dir out/ --head 65536

Notes
-----
* Read-only: nothing is ever written back to the remote host.
* Decompression is limited to the entries explicitly requested.
* Partial reads ("--head") are marked as such; their CRC cannot be verified.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
import urllib.request
import zlib

EOCD_SIG = b"PK\x05\x06"
ZIP64_LOCATOR_SIG = b"PK\x06\x07"
ZIP64_EOCD_SIG = b"PK\x06\x06"
CDH_SIG = b"PK\x01\x02"
LFH_SIG = b"PK\x03\x04"


def http_range(url: str, start: int, end: int, retries: int = 5, timeout: int = 120) -> bytes:
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
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            expected = end - start + 1
            if len(data) != expected:
                raise IOError(f"short read: got {len(data)} of {expected} bytes")
            return data
        except Exception as exc:  # noqa: BLE001 - retried
            last = exc
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"range {start}-{end} failed after retries: {last}")


def remote_size(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "iOS-tegu/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return int(resp.headers["Content-Length"])


class RemoteZip:
    def __init__(self, url: str, size: int | None = None):
        self.url = url
        self.size = size or remote_size(url)
        self.entries: list[dict] = []
        self.zip64 = False
        self.comment_len = 0
        self.cd_offset = 0
        self.cd_size = 0
        self._read_central_directory()

    # -- central directory -------------------------------------------------
    def _read_central_directory(self) -> None:
        tail_len = min(self.size, 66000)
        tail = http_range(self.url, self.size - tail_len, self.size - 1)
        pos = tail.rfind(EOCD_SIG)
        if pos < 0:
            raise RuntimeError("EOCD record not found: not a ZIP/IPSW archive")
        (_, _, _, _, total_entries, cd_size, cd_offset, self.comment_len) = struct.unpack(
            "<IHHHHIIH", tail[pos : pos + 22]
        )
        if total_entries == 0xFFFF or cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
            self.zip64 = True
            loc_pos = tail.rfind(ZIP64_LOCATOR_SIG, 0, pos)
            if loc_pos < 0:
                raise RuntimeError("ZIP64 locator not found")
            locator = tail[loc_pos : loc_pos + 20]
            _, _, zip64_eocd_offset, _ = struct.unpack("<IIQI", locator)
            rec = http_range(self.url, zip64_eocd_offset, zip64_eocd_offset + 55)
            if not rec.startswith(ZIP64_EOCD_SIG):
                raise RuntimeError("bad ZIP64 EOCD signature")
            (_, _, _, _, _, _, _, total_entries, cd_size, cd_offset) = struct.unpack(
                "<IQHHIIQQQQ", rec
            )
        self.cd_offset, self.cd_size, self.entry_count = cd_offset, cd_size, total_entries

        cd = http_range(self.url, cd_offset, cd_offset + cd_size - 1)
        self.entries = self._parse_cd(cd)

    @staticmethod
    def _parse_cd(cd: bytes) -> list[dict]:
        entries: list[dict] = []
        off = 0
        while off + 46 <= len(cd) and cd[off : off + 4] == CDH_SIG:
            (
                _sig,
                _vmade,
                _vneed,
                flags,
                method,
                mtime,
                mdate,
                crc,
                csize,
                usize,
                namelen,
                extralen,
                commentlen,
                _disk,
                _iattr,
                _eattr,
                lfh_offset,
            ) = struct.unpack("<IHHHHHHIIIHHHHHII", cd[off : off + 46])
            name = cd[off + 46 : off + 46 + namelen].decode("utf-8", "replace")
            extra = cd[off + 46 + namelen : off + 46 + namelen + extralen]
            # ZIP64 extended information extra field
            if 0xFFFFFFFF in (csize, usize, lfh_offset):
                usize, csize, lfh_offset = RemoteZip._apply_zip64(extra, usize, csize, lfh_offset)
            entries.append(
                {
                    "name": name,
                    "method": method,
                    "flags": flags,
                    "crc32": f"{crc:08x}",
                    "compressed_size": csize,
                    "uncompressed_size": usize,
                    "local_header_offset": lfh_offset,
                    "modified": f"{mdate >> 9}-{(mdate >> 5) & 0xF:02d}-{mdate & 0x1F:02d}T"
                    f"{(mtime >> 11) & 0x1F:02d}:{(mtime >> 5) & 0x3F:02d}:{(mtime & 0x1F) * 2:02d}",
                }
            )
            off += 46 + namelen + extralen + commentlen
        return entries

    @staticmethod
    def _apply_zip64(extra: bytes, usize: int, csize: int, lfh_offset: int):
        i = 0
        while i + 4 <= len(extra):
            tag, length = struct.unpack("<HH", extra[i : i + 4])
            data = extra[i + 4 : i + 4 + length]
            if tag == 0x0001:
                cursor = 0
                if usize == 0xFFFFFFFF:
                    usize = struct.unpack("<Q", data[cursor : cursor + 8])[0]
                    cursor += 8
                if csize == 0xFFFFFFFF:
                    csize = struct.unpack("<Q", data[cursor : cursor + 8])[0]
                    cursor += 8
                if lfh_offset == 0xFFFFFFFF:
                    lfh_offset = struct.unpack("<Q", data[cursor : cursor + 8])[0]
                break
            i += 4 + length
        return usize, csize, lfh_offset

    # -- entries -----------------------------------------------------------
    def find(self, name: str) -> dict:
        for entry in self.entries:
            if entry["name"] == name:
                return entry
        raise KeyError(name)

    def read_entry(self, name: str, head: int | None = None) -> tuple[bytes, dict]:
        entry = self.find(name)
        header = http_range(self.url, entry["local_header_offset"], entry["local_header_offset"] + 29)
        if not header.startswith(LFH_SIG):
            raise RuntimeError(f"bad local file header for {name}")
        namelen, extralen = struct.unpack("<HH", header[26:30])
        data_start = entry["local_header_offset"] + 30 + namelen + extralen
        csize = entry["compressed_size"]
        if head is None:
            blob = http_range(self.url, data_start, data_start + csize - 1)
            if entry["method"] == 0:
                payload = blob
            elif entry["method"] == 8:
                payload = zlib.decompress(blob, -15)
            else:
                raise RuntimeError(f"unsupported compression method {entry['method']} for {name}")
            crc = zlib.crc32(payload) & 0xFFFFFFFF
            entry = dict(entry, crc_verified=(f"{crc:08x}" == entry["crc32"]), partial=False)
            return payload, entry

        # Partial read: aim for `head` decompressed bytes; fetch in slices.
        want = min(head, entry["uncompressed_size"])
        chunk = max(65536, min(csize, max(65536, want * 2)))
        payload = b""
        fetched = 0
        dec = zlib.decompressobj(-15) if entry["method"] == 8 else None
        while fetched < csize and len(payload) < want:
            end = min(csize, fetched + chunk) - 1
            blob = http_range(self.url, data_start + fetched, data_start + end)
            fetched += len(blob)
            if dec is None:
                payload += blob
            else:
                payload += dec.decompress(blob, want - len(payload))
        entry = dict(entry, crc_verified=None, partial=True, bytes_fetched=fetched)
        return payload[:want], entry


def human(n: int) -> str:
    value = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{n} B"


def main() -> int:
    ap = argparse.ArgumentParser(description="Remote IPSW/ZIP reader (iOS-tegu)")
    ap.add_argument("command", choices=("info", "list", "extract"))
    ap.add_argument("--url", required=True)
    ap.add_argument("--json", help="write JSON output to this path")
    ap.add_argument("--name", help="entry name for extract")
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--out-name", help="output file name (default: entry basename)")
    ap.add_argument("--head", type=int, help="extract only the first N decompressed bytes")
    ap.add_argument("--filter", default=None, help="case-insensitive substring filter for list")
    args = ap.parse_args()

    try:
        archive = RemoteZip(args.url)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.command == "info":
        info = {
            "url": args.url,
            "size_bytes": archive.size,
            "size_human": human(archive.size),
            "zip64": archive.zip64,
            "entry_count": len(archive.entries),
            "central_directory_offset": archive.cd_offset,
            "central_directory_size": archive.cd_size,
            "comment_length": archive.comment_len,
            "top_level_entries": sorted({e["name"].split("/")[0] for e in archive.entries}),
        }
        print(json.dumps(info, indent=2, ensure_ascii=False))
        if args.json:
            open(args.json, "w", encoding="utf-8").write(json.dumps(info, indent=2, ensure_ascii=False))
        return 0

    if args.command == "list":
        entries = archive.entries
        if args.filter:
            needle = args.filter.lower()
            entries = [e for e in entries if needle in e["name"].lower()]
        if args.json:
            os.makedirs(os.path.dirname(os.path.abspath(args.json)) or ".", exist_ok=True)
            open(args.json, "w", encoding="utf-8").write(
                json.dumps({"url": args.url, "size_bytes": archive.size, "entries": entries}, indent=2)
            )
            print(f"wrote {args.json} ({len(entries)} entries)")
        else:
            for entry in entries:
                print(f'{entry["uncompressed_size"]:>13}  {entry["name"]}')
        return 0

    if not args.name:
        print("error: --name is required for extract", file=sys.stderr)
        return 3
    payload, entry = archive.read_entry(args.name, head=args.head)
    os.makedirs(args.out_dir, exist_ok=True)
    out_name = args.out_name or os.path.basename(args.name)
    out_path = os.path.join(args.out_dir, out_name)
    with open(out_path, "wb") as handle:
        handle.write(payload)
    print(
        json.dumps(
            {
                "entry": entry["name"],
                "out": out_path,
                "bytes_written": len(payload),
                "declared_size": entry["uncompressed_size"],
                "partial": entry["partial"],
                "crc32_declared": entry["crc32"],
                "crc_verified": entry["crc_verified"],
            },
            indent=2,
        )
    )
    if entry["crc_verified"] is False:
        print("error: CRC32 mismatch — entry corrupted", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
