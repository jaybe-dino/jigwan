"""브이월드(V-World) 데이터 API 수집기 — 도로·하천·건물 폴리곤.

문서: https://www.vworld.kr/dev/v4dv_2ddataguide2_s001.do
요청: GET https://api.vworld.kr/req/data?service=data&request=GetFeature
      &data={레이어ID}&geomFilter=POINT(lon lat)&buffer={m}&format=json&key=...
응답: response.result.featureCollection (GeoJSON) → features[].geometry

레이어 ID는 서비스 버전에 따라 달라질 수 있어 상수로 노출한다(운영 시 조정).
"""

from __future__ import annotations

from typing import Callable, List, Optional

from engine.geo import facing_from_footprint
from engine.models import LatLon, RoadSegment, StreamSegment
from pipeline.collectors.http import get_json

DATA_URL = "https://api.vworld.kr/req/data"

# 기본 레이어 ID (운영 환경에서 확인·조정)
LAYER_ROAD = "LT_L_MOCTLINK"   # 도로 링크
LAYER_STREAM = "LT_C_WKMSTRM"  # 하천(중심선)
LAYER_BUILDING = "LT_C_SPBD"   # 건물 통합


def _line_to_points(geom: dict) -> List[List[LatLon]]:
    """GeoJSON LineString/MultiLineString → 폴리라인들."""
    t = geom.get("type")
    coords = geom.get("coordinates") or []
    if t == "LineString":
        rings = [coords]
    elif t == "MultiLineString":
        rings = coords
    else:
        return []
    return [[LatLon(lat=c[1], lon=c[0]) for c in ring] for ring in rings]


def _polygon_ring(geom: dict) -> List[LatLon]:
    coords = geom.get("coordinates") or []
    t = geom.get("type")
    ring = coords[0] if t == "Polygon" else (coords[0][0] if t == "MultiPolygon" and coords else [])
    return [LatLon(lat=c[1], lon=c[0]) for c in ring]


class VWorldClient:
    def __init__(self, key: str, http: Callable = get_json):
        self._key = key
        self._http = http

    def _features(self, layer: str, center: LatLon, radius_m: float) -> List[dict]:
        data = self._http(
            DATA_URL,
            params={
                "service": "data", "request": "GetFeature", "version": "2.0",
                "data": layer, "format": "json", "crs": "EPSG:4326",
                "geomFilter": f"POINT({center.lon} {center.lat})",
                "buffer": int(radius_m), "size": 100, "key": self._key,
            },
        )
        fc = (((data or {}).get("response") or {}).get("result") or {}).get("featureCollection") or {}
        return fc.get("features") or []

    def roads(self, center: LatLon, radius_m: float) -> List[RoadSegment]:
        out: List[RoadSegment] = []
        for f in self._features(LAYER_ROAD, center, radius_m):
            props = f.get("properties") or {}
            for pts in _line_to_points(f.get("geometry") or {}):
                if len(pts) >= 2:
                    out.append(RoadSegment(
                        points=pts,
                        width_m=float(props.get("width") or props.get("ROAD_BT") or 6),
                        name=props.get("road_name") or props.get("RN"),
                    ))
        return out

    def streams(self, center: LatLon, radius_m: float) -> List[StreamSegment]:
        out: List[StreamSegment] = []
        for f in self._features(LAYER_STREAM, center, radius_m):
            props = f.get("properties") or {}
            for pts in _line_to_points(f.get("geometry") or {}):
                if len(pts) >= 2:
                    out.append(StreamSegment(points=pts, name=props.get("HRIVER_NM") or props.get("name")))
        return out

    def building_facing(self, center: LatLon, toward: Optional[LatLon] = None) -> Optional[float]:
        """대상 좌표를 포함/최근접하는 건물 폴리곤에서 좌향(향) 추정."""
        feats = self._features(LAYER_BUILDING, center, 40)
        if not feats:
            return None
        ring = _polygon_ring(feats[0].get("geometry") or {})
        if len(ring) < 3:
            return None
        pts = [p.as_tuple() for p in ring]
        return facing_from_footprint(pts, toward.as_tuple() if toward else None)
