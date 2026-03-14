from __future__ import annotations

import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def add_miniapp_cache_buster(url: str) -> str:
    """Append/update ``appv`` query parameter to bypass stale Telegram WebView cache."""
    raw = (url or '').strip()
    if not raw or not (raw.startswith('http://') or raw.startswith('https://')):
        return raw

    parsed = urlparse(raw)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key != 'appv']
    query.append(('appv', str(int(time.time()))))
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
