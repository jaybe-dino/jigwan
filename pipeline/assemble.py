"""수집기 → SiteFeatures 조립 → 판정 엔진 호출.

파이프라인의 최종 조립 단계. 수집기 묶음(FixtureCollectors 또는 실제 API 구현)을
받아 한 주소의 SiteFeatures를 만들고 assess_site로 넘긴다.
"""

from __future__ import annotations

from engine.models import Building, Precision, SiteFeatures
from engine.scoring import SiteAssessment, assess_site
from pipeline.collectors.base import Collectors

DEFAULT_RADIUS_M = 1500.0  # 현무/사신사 최대 반경에 맞춤


def assemble_features(
    address: str, collectors: Collectors, radius_m: float = DEFAULT_RADIUS_M
) -> SiteFeatures:
    info = collectors.building(address)
    loc = info.location
    # 실제 지형지물 이름(산·강) — 수집기가 제공하면 해석에 반영
    landmarks = None
    lm_fn = getattr(collectors, "landmarks", None)
    if callable(lm_fn):
        try:
            landmarks = lm_fn(loc)
        except Exception:
            landmarks = None
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
        landmarks=landmarks,
    )


def assemble_at(lat: float, lon: float, collectors, radius_m: float = DEFAULT_RADIUS_M) -> SiteFeatures:
    """지오코딩 없이 좌표(지도 탭)로 SiteFeatures 조립 — 전국 어디든."""
    from engine.models import LatLon

    loc = LatLon(lat, lon)
    get_at = getattr(collectors, "building_at", None)
    info = get_at(loc) if callable(get_at) else collectors.building("")
    loc = info.location
    landmarks = None
    lm_fn = getattr(collectors, "landmarks", None)
    if callable(lm_fn):
        try:
            landmarks = lm_fn(loc)
        except Exception:
            landmarks = None
    return SiteFeatures(
        address="지도에서 선택한 자리",
        building=Building(loc, info.facing_deg, info.ground_elevation_m, info.floors),
        dem=collectors.dem(loc, radius_m),
        streams=collectors.streams(loc, radius_m),
        roads=collectors.roads(loc, 200.0),
        rails_overpasses=collectors.rails_overpasses(loc, 500.0),
        pois=collectors.pois(loc, 500.0),
        historical=collectors.historical(loc),
        precision=Precision(dong_position=None),
        landmarks=landmarks,
    )


def assess_address(address: str, collectors: Collectors) -> SiteAssessment:
    return assess_site(assemble_features(address, collectors))


def assess_at(lat: float, lon: float, collectors) -> SiteAssessment:
    return assess_site(assemble_at(lat, lon, collectors))


def assess_coord_auto(lat: float, lon: float) -> SiteAssessment:
    """좌표 → 실데이터 감정(팩토리)."""
    from pipeline.collectors.factory import make_collectors

    collectors, _live = make_collectors("")
    return assess_at(lat, lon, collectors)


def assess_address_auto(address: str) -> SiteAssessment:
    """키가 있으면 실 API로, 없으면 픽스처로 감정(팩토리 위임)."""
    from pipeline.collectors.factory import make_collectors

    collectors, _live = make_collectors(address)
    return assess_address(address, collectors)
