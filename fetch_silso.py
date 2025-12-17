#!/usr/bin/env python3
"""
Download SILSO CSV and update data/<TARGET_FILENAME> when it changes.
"""
from __future__ import annotations
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except Exception:
    print("requests not found. Install with: pip install requests", file=sys.stderr)
    sys.exit(2)

SILSO_URL = os.getenv("SILSO_URL", "https://www.sidc.be/silso/INFO/sndtotcsv.php")
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

_raw_target = os.getenv("TARGET_FILENAME", "Sunspot-Daily")
TARGET_FILENAME = _raw_target if Path(_raw_target).suffix else f"{_raw_target}.csv"
TARGET_PATH = DATA_DIR / TARGET_FILENAME

ARCHIVE_DIR = os.getenv("ARCHIVE_DIR", "")
TIMEOUT = int(os.getenv("TIMEOUT_SECONDS", "30"))

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def write_bytes_safe(path: Path, b: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b)

def main() -> int:
    try:
        resp = requests.get(SILSO_URL, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to download {SILSO_URL}: {e}", file=sys.stderr)
        return 1

    content = resp.content
    if not content:
        print("Downloaded content is empty.", file=sys.stderr)
        return 1

    if TARGET_PATH.exists():
        existing = TARGET_PATH.read_bytes()
        if sha256_bytes(existing) == sha256_bytes(content):
            print(f"No change: {TARGET_PATH} is up-to-date.")
            return 0

    if ARCHIVE_DIR and TARGET_PATH.exists():
        try:
            archive_base = Path(ARCHIVE_DIR)
            archive_base.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).date().isoformat()
            archive_name = f"{TARGET_PATH.stem}-{stamp}{TARGET_PATH.suffix}"
            archive_path = archive_base / archive_name
            if not archive_path.exists():
                archive_path.write_bytes(TARGET_PATH.read_bytes())
                print(f"Archived previous file to {archive_path}")
            else:
                stamp_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
                archive_name = f"{TARGET_PATH.stem}-{stamp_ts}{TARGET_PATH.suffix}"
                archive_path = archive_base / archive_name
                archive_path.write_bytes(TARGET_PATH.read_bytes())
                print(f"Archived previous file to {archive_path}")
        except Exception as e:
            print(f"Warning: failed to archive previous file: {e}", file=sys.stderr)

    try:
        write_bytes_safe(TARGET_PATH, content)
        print(f"Wrote updated file: {TARGET_PATH}")
    except Exception as e:
        print(f"Failed to write {TARGET_PATH}: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
