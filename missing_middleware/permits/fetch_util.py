"""Small HTTP and manifest helpers shared by permit adapters (stdlib only)."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "missing-middleware research (public records; contact via repository)"


def opener(cookies: bool = True) -> urllib.request.OpenerDirector:
    handlers = []
    if cookies:
        import http.cookiejar

        handlers.append(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op = urllib.request.build_opener(*handlers)
    op.addheaders = [("User-Agent", USER_AGENT)]
    return op


def get(url: str, params: dict | None = None, op=None, data: bytes | None = None,
        timeout: int = 300, tries: int = 4) -> bytes:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    op = op or opener(cookies=False)
    last = None
    for attempt in range(tries):
        try:
            with op.open(url, data=data, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:  # network errors are retried, then re-raised
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {url[:120]}: {last}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_manifest(path: Path, entries: list[dict], meta: dict) -> None:
    path.write_text(json.dumps({**meta, "files": entries}, indent=2) + "\n")


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"files": []}
