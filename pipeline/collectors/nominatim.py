"""주소 → 좌표 — OpenStreetMap Nominatim (무료·키 불필요).

문서: https://nominatim.org/  · 이용정책상 User-Agent 필수, 1req/sec.
카카오/브이월드 키가 있으면 그쪽이 국내 주소에 더 정확하지만, 키 없이도 동작한다.
"""

from __future__ import annotations

from engine.models import LatLon
from pipeline.collectors.base import BuildingInfo
from pipeline.collectors.http import get_json

API = "https://nominatim.openstreetmap.org/search"
UA = "jigwan/0.1 (feng-shui service; contact via github jaybe-dino/jigwan)"


class NominatimGeocoder:
    def __init__(self, http=get_json):
        self._http = http

    def geocode(self, address: str) -> BuildingInfo:
        data = self._http(
            API,
            params={"q": address, "format": "json", "limit": 1,
                    "countrycodes": "kr", "accept-language": "ko"},
            headers={"User-Agent": UA},
            timeout=8,
        )
        if not data:
            raise ValueError(f"주소를 찾을 수 없습니다: {address}")
        d = data[0]
        return BuildingInfo(
            location=LatLon(lat=float(d["lat"]), lon=float(d["lon"])),
            facing_deg=180.0, ground_elevation_m=0.0,
        )
