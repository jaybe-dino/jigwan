"""수집기 → SiteFeatures 조립 → 판정 엔진 호출.

파이프라인의 최종 조립 단계. 수집기 묶음(FixtureCollectors 또는 실제 API 구현)을
받아 한 주소의 SiteFeatures를 만들고 assess_site로 넘긴다.
"""

from __future__ import annotations

from engine.models import Building, Precision, SiteFeatures
from engine.scoring import SiteAssessment, assess_site
from pipeline.collectors.fixture import FixtureCollectors

DEFAULT_RADIUS_M = 1500.0  # 현무/사신사 최대 반경에 맞춤


def assemble_features(
    address: str, collectors: FixtureCollectors, radius_m: float = DEFAULT_RADIUS_M
) -> SiteFeatures:
    info = collectors.building(address)
    loc = info.location
    return SiteFeatures(
        address=address,
        building=Building(
            location=loc,
            facing_deg=info.facing_deg,
            ground_elevation_m=info.ground_elevation_m,
            floors=info.floors,
        ),
        dem=collectors.dem(loc, radius_m),
        streams=collectors.streams(loc, radius_m),
        roads=collectors.roads(loc, 200.0),
        rails_overpasses=collectors.rails_overpasses(loc, 500.0),
        pois=collectors.pois(loc, 500.0),
        historical=collectors.historical(loc),
        precision=Precision(dong_position=None),
    )


def assess_address(address: str, collectors: FixtureCollectors) -> SiteAssessment:
    return assess_site(assemble_features(address, collectors))
