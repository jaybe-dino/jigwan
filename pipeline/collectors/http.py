"""표준 라이브러리만 쓰는 소형 HTTP JSON 클라이언트.

외부 의존성(requests 등) 없이 공공 API를 호출한다. 프록시(HTTPS_PROXY)와
CA 번들은 환경이 이미 설정하므로 urllib이 그대로 따른다.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class HttpError(RuntimeError):
    def __init__(self, status: int, url: str, body: str = ""):
        super().__init__(f"HTTP {status} for {url}: {body[:200]}")
        self.status = status
        self.url = url


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
) -> Any:
    """GET 요청 후 JSON 파싱. 4xx/5xx면 HttpError."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        raise HttpError(e.code, url, e.read().decode("utf-8", "ignore")) from e
    return json.loads(raw)
