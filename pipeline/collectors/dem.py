"""DEM 수집 — 배산임수·사신사 판정에 쓸 부채꼴 고도 샘플.

DEM(국토지리정보원 5m)은 단순 REST가 아니라 격자/래스터다. 여기서는
풍수 판정에 필요한 '샘플 지오메트리'(건물 중심 부채꼴 격자)를 생성하는 부분을
재사용 가능하게 구현하고, 실제 고도값은 주입식 `elevation_at` 콜러블로 분리한다.

운영: elevation_at 을 NGII DEM 래스터 조회(rasterio) 또는 브이월드 수치표고
조회에 바인딩한다. 테스트/데모: 합성 고도 함수 또는 픽스처를 쓴다.
"""

from __future__ import annotations

import math
from typing import Callable, List

from engine.models import ElevationSample, LatLon

_LAT_M = 111_320.0

# 판정 반경(현무·사신사)에 맞춘 기본 샘플 격자
DEFAULT_BEARINGS = list(range(0, 360, 15))          # 24방위
DEFAULT_DISTANCES = [200, 350, 500, 750, 1000, 1300, 1500]

ElevationAt = Callable[[float, float], float]  # (lat, lon) -> 고도 m


def _offset(origin: LatLon, dist_m: float, bearing_deg: float) -> LatLon:
    b = math.radians(bearing_deg)
    dlat = dist_m * math.cos(b) / _LAT_M
    dlon = dist_m * math.sin(b) / (_LAT_M * math.cos(math.radians(origin.lat)))
    return LatLon(origin.lat + dlat, origin.lon + dlon)


def sample_fan(
    center: LatLon,
    elevation_at: ElevationAt,
    bearings=DEFAULT_BEARINGS,
    distances=DEFAULT_DISTANCES,
) -> List[ElevationSample]:
    """건물 중심 기준 방위×거리 격자의 고도 샘플을 만든다."""
    out: List[ElevationSample] = []
    for b in bearings:
        for d in distances:
            p = _offset(center, d, b)
            out.append(ElevationSample(point=p, elevation_m=elevation_at(p.lat, p.lon)))
    return out


def ground_elevation(center: LatLon, elevation_at: ElevationAt) -> float:
    return elevation_at(center.lat, center.lon)
