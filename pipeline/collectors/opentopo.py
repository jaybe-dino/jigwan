"""실제 DEM 고도 — OpenTopoData (무료·키 불필요, 전 지구 SRTM).

문서: https://www.opentopodata.org/  · 배치 100점/요청, 공개 API 1req/sec.
배산임수·사신사 판정의 '진짜' 고도값을 제공한다(가짜 합성 금지).
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from engine.models import LatLon
from pipeline.collectors.http import get_json

# 데이터셋: srtm30m(30m 해상도, 전지구). 국내는 aster30m도 가능.
API = "https://api.opentopodata.org/v1/srtm30m"
BATCH = 100


class OpenTopoElevation:
    def __init__(self, http=get_json, url: str = API):
        self._http = http
        self._url = url
        self._cache: dict = {}

    def _fetch(self, pts: Sequence[Tuple[float, float]]) -> List[float]:
        loc = "|".join(f"{lat:.6f},{lon:.6f}" for lat, lon in pts)
        data = self._http(self._url, params={"locations": loc}, timeout=20)
        out = []
        for r in data.get("results") or []:
            e = r.get("elevation")
            out.append(float(e) if e is not None else 0.0)
        return out

    def elevations(self, points: Sequence[LatLon]) -> List[float]:
        """여러 점의 실제 고도(m). 배치 요청 + 캐시."""
        result: List[float] = [0.0] * len(points)
        todo: List[Tuple[int, Tuple[float, float]]] = []
        for i, p in enumerate(points):
            key = (round(p.lat, 5), round(p.lon, 5))
            if key in self._cache:
                result[i] = self._cache[key]
            else:
                todo.append((i, key))
        for k in range(0, len(todo), BATCH):
            chunk = todo[k:k + BATCH]
            elevs = self._fetch([c[1] for c in chunk])
            for (idx, key), e in zip(chunk, elevs):
                self._cache[key] = e
                result[idx] = e
        return result

    def at(self, lat: float, lon: float) -> float:
        return self.elevations([LatLon(lat, lon)])[0]
