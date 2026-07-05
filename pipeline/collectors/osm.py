"""무료 실데이터 수집기 묶음 — 키 없이 전국 실제 지형으로 풍수 분석.

OpenTopoData(실제 DEM) + OSM Overpass(실제 산·강·도로·시설) + Nominatim(지오코딩).
Collectors 프로토콜을 만족하며, 실제 산·강 이름을 landmarks로 뽑아 해석에 반영한다.
가짜 합성 데이터를 쓰지 않는다.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from engine.geo import angle_diff, bearing, facing_from_footprint, haversine
from engine.models import (
    ElevationSample,
    HistoricalLand,
    LatLon,
    POI,
    RailOverpass,
    RoadSegment,
    StreamSegment,
)
from pipeline.collectors.base import BuildingInfo
from pipeline.collectors.dem import fan_points
from pipeline.collectors.nominatim import NominatimGeocoder
from pipeline.collectors.opentopo import OpenTopoElevation
from pipeline.collectors.overpass import OverpassClient


class OsmCollectors:
    """무료 오픈데이터 기반 실측 수집기."""

    def __init__(self):
        self.geocoder = NominatimGeocoder()
        self.elev = OpenTopoElevation()
        self.overpass = OverpassClient()
        self._facing = 180.0

    def building(self, address: str) -> BuildingInfo:
        info = self.geocoder.geocode(address)
        loc = info.location
        # 좌향: 실제 건물 외곽선 주축 → 도로 쪽을 향하도록
        try:
            ring = self.overpass.building_footprint(loc)
            if len(ring) >= 3:
                roads = self.overpass.roads(loc, 60)
                toward = roads[0].points[len(roads[0].points) // 2].as_tuple() if roads else None
                info.facing_deg = facing_from_footprint([p.as_tuple() for p in ring], toward)
        except Exception:
            pass
        try:
            info.ground_elevation_m = self.elev.at(loc.lat, loc.lon)
        except Exception:
            info.ground_elevation_m = 0.0
        self._facing = info.facing_deg
        return info

    def dem(self, center: LatLon, radius_m: float) -> List[ElevationSample]:
        pts = fan_points(center)
        try:
            elevs = self.elev.elevations(pts)
        except Exception:
            return []
        return [ElevationSample(point=p, elevation_m=e) for p, e in zip(pts, elevs)]

    def streams(self, center: LatLon, radius_m: float) -> List[StreamSegment]:
        return self.overpass.waterways(center, radius_m)

    def roads(self, center: LatLon, radius_m: float) -> List[RoadSegment]:
        return self.overpass.roads(center, radius_m)

    def rails_overpasses(self, center: LatLon, radius_m: float) -> List[RailOverpass]:
        return self.overpass.rails(center, radius_m)

    def pois(self, center: LatLon, radius_m: float) -> List[POI]:
        return self.overpass.pois(center, radius_m)

    def historical(self, location: LatLon) -> Optional[HistoricalLand]:
        return None

    def landmarks(self, center: LatLon) -> Dict[str, str]:
        """실제 산봉우리·하천 이름을 방위별로 배정 (해석에 그대로 노출)."""
        out: Dict[str, str] = {}
        try:
            peaks = self.overpass.peaks(center, 4000)
        except Exception:
            peaks = []
        f = self._facing
        sectors = {"back": (f + 180) % 360, "left": (f + 90) % 360,
                   "right": (f - 90) % 360, "front": f % 360}
        for key, cdeg in sectors.items():
            best = None
            for loc, name, _ele in peaks:
                b = bearing(center.as_tuple(), loc.as_tuple())
                if angle_diff(b, cdeg) <= 45:
                    d = haversine(center.as_tuple(), loc.as_tuple())
                    if best is None or d < best[0]:
                        best = (d, name)
            if best:
                out[key] = best[1]
        try:
            waters = self.overpass.waterways(center, 800)
            named = [w for w in waters if w.name]
            if named:
                nearest = min(named, key=lambda w: min(
                    haversine(center.as_tuple(), p.as_tuple()) for p in w.points))
                out["water"] = nearest.name
        except Exception:
            pass
        return out
