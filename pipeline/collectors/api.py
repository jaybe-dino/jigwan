"""실 API 수집기 묶음 — 카카오·브이월드·건축물대장·DEM을 조합.

Collectors 프로토콜을 만족한다. 키가 없는 소스는 빈 결과로 두어 파이프라인이
끊기지 않게 한다(예: DEM 소스 미바인딩 시 현무 판정만 약해짐).
"""

from __future__ import annotations

from typing import List, Optional

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
from pipeline.collectors.dem import ElevationAt, ground_elevation, sample_fan
from pipeline.collectors.kakao import KakaoClient
from pipeline.collectors.vworld import VWorldClient
from pipeline.config import Config


def _flat_elevation(lat: float, lon: float) -> float:
    """DEM 소스 미바인딩 시 기본(평지). 운영에서 NGII DEM/래스터로 교체."""
    return 0.0


class ApiCollectors:
    """공공 API 기반 수집기 묶음."""

    def __init__(self, config: Config, elevation_at: Optional[ElevationAt] = None):
        if not config.has_kakao:
            raise ValueError("KAKAO_REST_KEY가 필요합니다(주소 지오코딩).")
        self.kakao = KakaoClient(config.kakao_key)  # type: ignore[arg-type]
        self.vworld = VWorldClient(config.vworld_key) if config.has_vworld else None
        self.elevation_at: ElevationAt = elevation_at or _flat_elevation

    def building(self, address: str) -> BuildingInfo:
        info = self.kakao.geocode(address)
        # 좌향: 건물 폴리곤 주축에서 추정(브이월드), 없으면 남향 기본
        facing = None
        if self.vworld:
            facing = self.vworld.building_facing(info.location)
        info.facing_deg = facing if facing is not None else 180.0
        info.ground_elevation_m = ground_elevation(info.location, self.elevation_at)
        return info

    def dem(self, center: LatLon, radius_m: float) -> List[ElevationSample]:
        return sample_fan(center, self.elevation_at)

    def streams(self, center: LatLon, radius_m: float) -> List[StreamSegment]:
        return self.vworld.streams(center, radius_m) if self.vworld else []

    def roads(self, center: LatLon, radius_m: float) -> List[RoadSegment]:
        return self.vworld.roads(center, radius_m) if self.vworld else []

    def rails_overpasses(self, center: LatLon, radius_m: float) -> List[RailOverpass]:
        return []  # TODO(M2+): 철도·고가 레이어 연동

    def pois(self, center: LatLon, radius_m: float) -> List[POI]:
        return self.kakao.pois(center, radius_m)

    def historical(self, location: LatLon) -> Optional[HistoricalLand]:
        return None  # TODO(M2+): 국토정보플랫폼 옛 지형도 연동
