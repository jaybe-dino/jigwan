"""수집기 → SiteFeatures 조립 → 판정 엔진 호출.

파이프라인의 최종 조립 단계. 수집기 묶음(FixtureCollectors 또는 실제 API 구현)을
받아 한 주소의 SiteFeatures를 만들고 assess_site로 넘긴다.
"""

from __future__ import annotations

import os
import time

from engine.models import Building, Precision, SiteFeatures
from engine.scoring import SiteAssessment, assess_site
from pipeline.collectors.base import Collectors

DEFAULT_RADIUS_M = 1500.0  # 현무/사신사 최대 반경에 맞춤


def _deadline() -> float:
    # 실측 총 시간 예산(초). 초과하면 남은 수집은 건너뛰고 부분 데이터로 즉시 응답.
    return time.time() + float(os.environ.get("JIGWAN_ASSESS_BUDGET", "30"))


def _within(deadline: float, fn, default):
    """예산 안이면 수집을 시도하고, 초과했거나 실패하면 기본값(빈 데이터)."""
    if time.time() > deadline:
        return default
    try:
        return fn()
    except Exception:
        return default


def assemble_features(
    address: str, collectors: Collectors, radius_m: float = DEFAULT_RADIUS_M
) -> SiteFeatures:
    info = collectors.building(address)  # 주소 지오코딩 실패는 그대로 전파(잘못된 주소 알림)
    loc = info.location
    dl = _deadline()
    lm_fn = getattr(collectors, "landmarks", None)
    return SiteFeatures(
        address=address,
        building=Building(
            location=loc,
            facing_deg=info.facing_deg,
            ground_elevation_m=info.ground_elevation_m,
            floors=info.floors,
        ),
        # 핵심 형기(물길·지형)를 먼저 확보 — 예산 초과 시 덜 중요한 것부터 생략
        streams=_within(dl, lambda: collectors.streams(loc, radius_m), []),
        dem=_within(dl, lambda: collectors.dem(loc, radius_m), []),
        roads=_within(dl, lambda: collectors.roads(loc, 200.0), []),
        pois=_within(dl, lambda: collectors.pois(loc, 500.0), []),
        rails_overpasses=_within(dl, lambda: collectors.rails_overpasses(loc, 500.0), []),
        historical=_within(dl, lambda: collectors.historical(loc), None),
        precision=Precision(dong_position=None),
        landmarks=_within(dl, lambda: lm_fn(loc) if callable(lm_fn) else None, None),
    )


def assemble_at(lat: float, lon: float, collectors, radius_m: float = DEFAULT_RADIUS_M) -> SiteFeatures:
    """지오코딩 없이 좌표(지도 탭)로 SiteFeatures 조립 — 전국 어디든."""
    from engine.models import LatLon

    loc = LatLon(lat, lon)
    dl = _deadline()
    get_at = getattr(collectors, "building_at", None)
    info = _within(dl, lambda: get_at(loc) if callable(get_at) else collectors.building(""), None)
    if info is None:  # 건물 정보 실패/지연 → 기본값으로라도 진행
        from pipeline.collectors.base import BuildingInfo
        info = BuildingInfo(location=loc, facing_deg=180.0, ground_elevation_m=0.0)
    loc = info.location
    lm_fn = getattr(collectors, "landmarks", None)
    return SiteFeatures(
        address="지도에서 선택한 자리",
        building=Building(loc, info.facing_deg, info.ground_elevation_m, info.floors),
        # 핵심 형기(물길·지형)를 먼저 확보 — 예산 초과 시 덜 중요한 것부터 생략
        streams=_within(dl, lambda: collectors.streams(loc, radius_m), []),
        dem=_within(dl, lambda: collectors.dem(loc, radius_m), []),
        roads=_within(dl, lambda: collectors.roads(loc, 200.0), []),
        pois=_within(dl, lambda: collectors.pois(loc, 500.0), []),
        rails_overpasses=_within(dl, lambda: collectors.rails_overpasses(loc, 500.0), []),
        historical=_within(dl, lambda: collectors.historical(loc), None),
        precision=Precision(dong_position=None),
        landmarks=_within(dl, lambda: lm_fn(loc) if callable(lm_fn) else None, None),
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
