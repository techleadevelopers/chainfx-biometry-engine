from __future__ import annotations

import os
import tempfile
from pathlib import Path

import requests


def fetch_file(url: str, suffix: str, timeout_sec: int = 25, max_bytes: int = 70 * 1024 * 1024) -> Path | None:
    if not url:
        return None
    with requests.get(url, timeout=timeout_sec, stream=True) as resp:
        resp.raise_for_status()
        fd, name = tempfile.mkstemp(suffix=suffix)
        total = 0
        try:
            with os.fdopen(fd, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError("kyc media exceeds max size")
                    f.write(chunk)
            return Path(name)
        except Exception:
            try:
                Path(name).unlink(missing_ok=True)
            finally:
                raise


def cleanup(paths: list[Path | None]) -> None:
    for path in paths:
        if not path:
            continue
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
