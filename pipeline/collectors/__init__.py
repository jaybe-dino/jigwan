"""외부 데이터 수집기.

각 수집기는 좌표(위경도)와 반경을 받아 해당 원천 데이터를 돌려주는 계약을
따른다. M1은 계약(Protocol)과 픽스처 구현만 제공하고, 실제 공공 API 연동은 M2.

    class DemCollector(Protocol):
        def fetch(self, center, radius_m) -> list[ElevationSample]: ...
"""

from pipeline.collectors.base import (
    BuildingInfo,
    DemCollector,
    HistoricalCollector,
    PoiCollector,
    RailOverpassCollector,
    RoadCollector,
    StreamCollector,
)
from pipeline.collectors.fixture import FixtureCollectors

__all__ = [
    "BuildingInfo",
    "DemCollector",
    "StreamCollector",
    "RoadCollector",
    "RailOverpassCollector",
    "PoiCollector",
    "HistoricalCollector",
    "FixtureCollectors",
]
