"""룰 공통 헬퍼 — 배면 부채꼴 최대 고도차 등."""

from __future__ import annotations

from typing import List, Optional, Tuple

from engine.geo import angle_diff, bearing, haversine
from engine.models import ElevationSample, LatLon

# 배면/사신사 부채꼴 반경(m)과 반각(도)
RIDGE_MIN_M = 200.0
RIDGE_MAX_M = 1500.0
SECTOR_HALF_DEG = 22.5


def max_elev_gain_in_sector(
    origin: LatLon,
    ground_elev: float,
    dem: List[ElevationSample],
    center_deg: float,
    half_width_deg: float = SECTOR_HALF_DEG,
    r_min: float = RIDGE_MIN_M,
    r_max: float = RIDGE_MAX_M,
) -> Tuple[float, Optional[float], Optional[float]]:
    """부채꼴(center_deg±half, r_min~r_max) 안 DEM 중 최대 고도차.

    Returns: (max_gain_m, dist_m_of_max, bearing_of_max). 없으면 (0, None, None).
    """
    o = origin.as_tuple()
    best_gain = 0.0
    best_d: Optional[float] = None
    best_b: Optional[float] = None
    for s in dem:
        p = s.point.as_tuple()
        d = haversine(o, p)
        if d < r_min or d > r_max:
            continue
        b = bearing(o, p)
        if angle_diff(b, center_deg) > half_width_deg:
            continue
        gain = s.elevation_m - ground_elev
        if gain > best_gain:
            best_gain = gain
            best_d = d
            best_b = b
    return best_gain, best_d, best_b


DIRECTION_KO = [
    (0, "북"), (45, "북동"), (90, "동"), (135, "남동"),
    (180, "남"), (225, "남서"), (270, "서"), (315, "북서"), (360, "북"),
]


def bearing_to_ko(deg: float) -> str:
    """방위각 → 한글 8방위."""
    best = min(DIRECTION_KO, key=lambda kv: abs(((deg - kv[0] + 180) % 360) - 180))
    return best[1]
