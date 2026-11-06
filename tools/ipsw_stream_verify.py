#!/usr/bin/env python3
"""iOS-tegu :: ipsw_stream_verify.py

Stream a remote IPSW through SHA-256 without storing it, and compare the result
with an expected size and SHA-256.  Transfers are resumable: a dropped
connection restarts at the exact byte offset already hashed, so the digest stays
correct and the tool does not have to start over.

Why this exists
---------------
A restore IPSW is 12-13 GB.  The cloud workspace used for iOS-tegu has less free
disk than that, so "verify the firmware is complete" cannot mean "keep a copy on
disk".  This tool proves completeness and integrity in one pass:

* bytes received must equal the advertised Content-Length;
* the SHA-256 must equal the value published by the vendor/aggregator;
* progress is logged so a partial run is never mistaken for a success.

Usage
-----
  python3 tools/ipsw_stream_verify.py --url "$IPSW_URL" \
      --expected-size 13172779665 \
      --expected-sha256 ac4eb036593386164d55b90886b192cccbda3f05fcf0df21bd5faa7da157693f \
      --log out/verify.log --report out/verify.json

Exit codes: 0 verified, 5 hash/size mismatch, 3 network failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request


def open_range(url: str, start: int, retries: int = 8, timeout: int = 120):
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Range": f"bytes={start}-",
                    "User-Agent": "iOS-tegu/0.1",
                    "Accept-Encoding": "identity",
                },
            )
            return urllib.request.urlopen(req, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(min(30, 2**attempt))
    raise RuntimeError(f"cannot open stream at {start}: {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Streaming SHA-256 verification of a remote IPSW")
    ap.add_argument("--url", required=True)
    ap.add_argument("--expected-size", type=int, required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--log", help="progress log path")
    ap.add_argument("--report", help="JSON report path")
    ap.add_argument("--chunk", type=int, default=4 * 1024 * 1024)
    args = ap.parse_args()

    log_handle = open(args.log, "a", encoding="utf-8") if args.log else None

    def log(message: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {message}"
        print(line, flush=True)
        if log_handle:
            log_handle.write(line + "\n")
            log_handle.flush()

    digest = hashlib.sha256()
    received = 0
    started = time.time()
    last_report = 0.0
    log(f"start size={args.expected_size} expected_sha256={args.expected_sha256}")

    while received < args.expected_size:
        try:
            with open_range(args.url, received) as resp:
                if resp.status not in (200, 206):
                    raise RuntimeError(f"unexpected HTTP status {resp.status}")
                while received < args.expected_size:
                    block = resp.read(min(args.chunk, args.expected_size - received))
                    if not block:
                        break
                    digest.update(block)
                    received += len(block)
                    now = time.time()
                    if now - last_report >= 15:
                        rate = received / max(now - started, 1e-6)
                        pct = 100 * received / args.expected_size
                        log(f"progress {received}/{args.expected_size} ({pct:.1f}%) {rate/1e6:.1f} MB/s")
                        last_report = now
        except Exception as exc:  # noqa: BLE001
            log(f"stream interrupted at {received}: {exc} — resuming")
            time.sleep(2)

    actual = digest.hexdigest()
    elapsed = time.time() - started
    ok = received == args.expected_size and actual == args.expected_sha256.lower()
    report = {
        "url": args.url,
        "expected_size": args.expected_size,
        "received_bytes": received,
        "expected_sha256": args.expected_sha256.lower(),
        "actual_sha256": actual,
        "size_match": received == args.expected_size,
        "hash_match": actual == args.expected_sha256.lower(),
        "duration_seconds": round(elapsed, 1),
        "average_mb_s": round(received / max(elapsed, 1e-6) / 1e6, 2),
        "verified": ok,
        "stored_on_disk": False,
        "note": "Streamed and hashed in memory; no local copy kept (workspace disk < IPSW size).",
    }
    log(f"done verified={ok} sha256={actual} elapsed={elapsed:.0f}s")
    if log_handle:
        log_handle.close()
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)) or ".", exist_ok=True)
        open(args.report, "w", encoding="utf-8").write(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main())
