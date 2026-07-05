"""수집기 계약(Protocol) — 실제 공공 API 구현이 따라야 할 인터페이스.

기획안 §10 외부 데이터 소스 대응:
  DEM(국토지리정보원) · 하천망(WAMIS) · 도로망(도로명주소 전자지도)
  · 철도/고가 · POI(카카오 로컬) · 옛 지형도(국토정보플랫폼)
  · 건축물대장(좌향·층수)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol

from engine.models import (
    ElevationSample,
    HistoricalLand,
    LatLon,
    POI,
    RailOverpass,
    RoadSegment,
    StreamSegment,
)


@dataclass
class BuildingInfo:
    """건축물대장 + 지적도에서 얻는 건물 기본 정보."""

    location: LatLon
    facing_deg: float
    ground_elevation_m: float = 0.0
    floors: Optional[int] = None
    building_id: Optional[str] = None


class DemCollector(Protocol):
    def fetch(self, center: LatLon, radius_m: float) -> List[ElevationSample]: ...


class StreamCollector(Protocol):
    def fetch(self, center: LatLon, radius_m: float) -> List[StreamSegment]: ...


class RoadCollector(Protocol):
    def fetch(self, center: LatLon, radius_m: float) -> List[RoadSegment]: ...


class RailOverpassCollector(Protocol):
    def fetch(self, center: LatLon, radius_m: float) -> List[RailOverpass]: ...


class PoiCollector(Protocol):
    def fetch(self, center: LatLon, radius_m: float) -> List[POI]: ...


class HistoricalCollector(Protocol):
    def fetch(self, location: LatLon) -> Optional[HistoricalLand]: ...


class GeocoderBuildingCollector(Protocol):
    """주소 → 건물 기본 정보(좌표·좌향·층수)."""

    def fetch(self, address: str) -> BuildingInfo: ...


class Collectors(Protocol):
    """assemble_features 가 소비하는 수집기 묶음 계약.

    FixtureCollectors(픽스처)와 ApiCollectors(실 API)가 모두 이 형태를 만족한다.
    """

    def building(self, address: str) -> BuildingInfo: ...
    def dem(self, center: LatLon, radius_m: float) -> List[ElevationSample]: ...
    def streams(self, center: LatLon, radius_m: float) -> List[StreamSegment]: ...
    def roads(self, center: LatLon, radius_m: float) -> List[RoadSegment]: ...
    def rails_overpasses(self, center: LatLon, radius_m: float) -> List[RailOverpass]: ...
    def pois(self, center: LatLon, radius_m: float) -> List[POI]: ...
    def historical(self, location: LatLon) -> Optional[HistoricalLand]: ...
