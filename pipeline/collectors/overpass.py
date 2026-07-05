"""실제 지형지물 — OpenStreetMap Overpass API (무료·키 불필요).

실제 하천·도로·산봉우리·주변시설·건물 외곽선을 가져와 풍수 판정에 쓴다.
문서: https://wiki.openstreetmap.org/wiki/Overpass_API
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from engine.geo import haversine
from engine.models import LatLon, POI, RailOverpass, RoadSegment, StreamSegment
from pipeline.collectors.http import get_json

ENDPOINT = "https://overpass-api.de/api/interpreter"

# OSM 태그 → 풍수 POI 카테고리
POI_TAGS = [
    ('amenity=funeral_hall', 'funeral'), ('shop=funeral_directors', 'funeral'),
    ('power=tower', 'power_tower'), ('amenity=nightclub', 'nightlife'),
    ('amenity=fuel', 'gas_station'), ('leisure=park', 'park'),
    ('amenity=school', 'school'), ('amenity=library', 'library'),
    ('amenity=hospital', 'hospital'), ('railway=station', 'subway'),
]


def _post(query: str, http=get_json) -> dict:
    # Overpass는 POST가 표준이나 get_json은 GET. data 파라미터로 GET 허용됨.
    return http(ENDPOINT, params={"data": query}, timeout=30)


def _center(el: dict) -> Optional[LatLon]:
    if "lat" in el and "lon" in el:
        return LatLon(el["lat"], el["lon"])
    c = el.get("center")
    if c:
        return LatLon(c["lat"], c["lon"])
    return None


def _line(el: dict) -> List[LatLon]:
    geom = el.get("geometry") or []
    return [LatLon(g["lat"], g["lon"]) for g in geom]


class OverpassClient:
    def __init__(self, http=get_json):
        self._http = http

    def _q(self, body: str) -> List[dict]:
        try:
            data = _post(f"[out:json][timeout:25];({body});out geom center 200;", self._http)
            return data.get("elements") or []
        except Exception:
            return []  # 네트워크/타임아웃 시 판정을 끊지 않고 빈 결과

    def waterways(self, c: LatLon, r: float) -> List[StreamSegment]:
        els = self._q(f'way[waterway~"river|stream|canal"](around:{int(r)},{c.lat},{c.lon});')
        out = []
        for e in els:
            pts = _line(e)
            if len(pts) >= 2:
                out.append(StreamSegment(points=pts, name=(e.get("tags") or {}).get("name")))
        return out

    def roads(self, c: LatLon, r: float) -> List[RoadSegment]:
        els = self._q(f'way[highway~"motorway|trunk|primary|secondary|tertiary|residential"](around:{int(r)},{c.lat},{c.lon});')
        out = []
        for e in els:
            pts = _line(e)
            if len(pts) < 2:
                continue
            tags = e.get("tags") or {}
            lanes = tags.get("lanes")
            width = float(tags.get("width")) if tags.get("width", "").replace(".", "").isdigit() \
                else (int(lanes) * 3.0 if (lanes or "").isdigit() else 6.0)
            out.append(RoadSegment(points=pts, width_m=width, name=tags.get("name")))
        return out

    def rails(self, c: LatLon, r: float) -> List[RailOverpass]:
        els = self._q(f'way[railway~"rail|light_rail|subway"](around:{int(r)},{c.lat},{c.lon});')
        out = []
        for e in els:
            pts = _line(e)
            if pts:
                near = min(pts, key=lambda p: haversine(c.as_tuple(), p.as_tuple()))
                out.append(RailOverpass(kind="rail", nearest=near, height_diff_m=0.0))
        return out

    def pois(self, c: LatLon, r: float) -> List[POI]:
        parts = []
        for tag, _cat in POI_TAGS:
            k, v = tag.split("=")
            parts.append(f'nwr[{k}~"{v}"](around:{int(r)},{c.lat},{c.lon});')
        els = self._q("".join(parts))
        out = []
        for e in els:
            loc = _center(e)
            if not loc:
                continue
            tags = e.get("tags") or {}
            cat = _match_cat(tags)
            if cat:
                out.append(POI(point=loc, category=cat, name=tags.get("name")))
        return out

    def peaks(self, c: LatLon, r: float) -> List[Tuple[LatLon, str, float]]:
        """실제 산봉우리 (natural=peak) → (좌표, 이름, 고도)."""
        els = self._q(f'node[natural~"peak|hill"](around:{int(r)},{c.lat},{c.lon});')
        out = []
        for e in els:
            loc = _center(e)
            tags = e.get("tags") or {}
            if loc and tags.get("name"):
                ele = float(tags["ele"]) if (tags.get("ele", "").replace(".", "").isdigit()) else 0.0
                out.append((loc, tags["name"], ele))
        return out

    def building_footprint(self, c: LatLon) -> List[LatLon]:
        els = self._q(f'way[building](around:12,{c.lat},{c.lon});')
        if not els:
            return []
        return _line(els[0])


def _match_cat(tags: dict) -> Optional[str]:
    for tag, cat in POI_TAGS:
        k, v = tag.split("=")
        if tags.get(k) == v or (v in (tags.get(k) or "")):
            return cat
    return None
