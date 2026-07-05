"""픽스처 수집기 — 공공 API 연동(M2) 전까지 파이프라인을 돌리기 위한 구현.

engine.samples 의 합성 터를 그대로 반환한다. 실제 API 수집기는 이 계약을
동일하게 구현해 assemble_features() 를 재사용한다.
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
    SiteFeatures,
    StreamSegment,
)
from engine.samples import biboji_site, myeongdang_site
from pipeline.collectors.base import BuildingInfo


class FixtureCollectors:
    """하나의 SiteFeatures 픽스처를 원천별로 쪼개어 제공하는 수집기 묶음."""

    def __init__(self, features: SiteFeatures):
        self._f = features

    # 각 수집기는 radius 필터를 흉내만 낸다(픽스처는 이미 근방 데이터).
    def dem(self, center: LatLon, radius_m: float) -> List[ElevationSample]:
        return list(self._f.dem)

    def streams(self, center: LatLon, radius_m: float) -> List[StreamSegment]:
        return list(self._f.streams)

    def roads(self, center: LatLon, radius_m: float) -> List[RoadSegment]:
        return list(self._f.roads)

    def rails_overpasses(self, center: LatLon, radius_m: float) -> List[RailOverpass]:
        return list(self._f.rails_overpasses)

    def pois(self, center: LatLon, radius_m: float) -> List[POI]:
        return list(self._f.pois)

    def historical(self, location: LatLon) -> Optional[HistoricalLand]:
        return self._f.historical

    def landmarks(self, center: LatLon):
        return self._f.landmarks

    def building(self, address: str) -> BuildingInfo:
        b = self._f.building
        return BuildingInfo(
            location=b.location,
            facing_deg=b.facing_deg,
            ground_elevation_m=b.ground_elevation_m,
            floors=b.floors,
        )


def fixture_for(address: str) -> FixtureCollectors:
    """주소 문자열로 픽스처 선택 (데모/테스트용)."""
    src = biboji_site() if "비보" in address else myeongdang_site()
    return FixtureCollectors(src)
