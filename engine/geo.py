"""경위도 기반 지오메트리 유틸 — 의존성 없는 순수 파이썬.

풍수 판정에 필요한 최소 연산만 구현한다. 국지(수 km) 범위에서만 쓰므로
구면 근사(haversine)와 초기방위각으로 충분하다. PostGIS 연산과의 정합성은
pipeline/spatial 및 tests/test_spatial.py에서 교차 검증한다.
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

EARTH_R = 6_371_000.0  # 지구 평균 반경(m)

Point = Tuple[float, float]  # (lat, lon)


def haversine(a: Point, b: Point) -> float:
    """두 (위도, 경도) 점 사이의 대권 거리(m)."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_R * math.asin(min(1.0, math.sqrt(h)))


def bearing(a: Point, b: Point) -> float:
    """a에서 b를 바라보는 초기 방위각(도, 0=정북, 시계방향, 0~360)."""
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlon = math.radians(b[1] - a[1])
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def angle_diff(a_deg: float, b_deg: float) -> float:
    """두 방위각의 최소 차이(0~180)."""
    d = abs((a_deg - b_deg) % 360.0)
    return min(d, 360.0 - d)


def in_sector(target_deg: float, center_deg: float, half_width_deg: float) -> bool:
    """target_deg가 center_deg를 중심으로 ±half_width_deg 부채꼴 안에 있는가."""
    return angle_diff(target_deg, center_deg) <= half_width_deg


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def local_xy(origin: Point, p: Point) -> Point:
    """origin을 원점으로 한 국지 평면 좌표(m). (east=x, north=y)."""
    lat0 = math.radians(origin[0])
    x = math.radians(p[1] - origin[1]) * EARTH_R * math.cos(lat0)
    y = math.radians(p[0] - origin[0]) * EARTH_R
    return (x, y)


def point_to_segment(p: Point, a: Point, b: Point) -> Tuple[float, Point, float]:
    """점 p에서 선분 a-b까지의 수선거리(m), 최근접점, 선분상 파라미터 t(0~1).

    origin=p 기준 국지 평면으로 투영해 계산한다(국지 범위 오차 무시 수준).
    """
    ax, ay = local_xy(p, a)
    bx, by = local_xy(p, b)
    # p는 원점(0,0)
    dx, dy = bx - ax, by - ay
    seg_len2 = dx * dx + dy * dy
    if seg_len2 == 0.0:
        t = 0.0
    else:
        t = clamp((-ax * dx - ay * dy) / seg_len2, 0.0, 1.0)
    cx, cy = ax + t * dx, ay + t * dy
    dist = math.hypot(cx, cy)
    # 최근접점을 다시 위경도로 환산
    lat0 = math.radians(p[0])
    clat = p[0] + math.degrees(cy / EARTH_R)
    clon = p[1] + math.degrees(cx / (EARTH_R * math.cos(lat0)))
    return dist, (clat, clon), t


def cross_sign(o: Point, a: Point, b: Point) -> float:
    """o를 원점으로 벡터 (o→a)×(o→b)의 z부호. +면 b가 a의 좌측(반시계)."""
    ax, ay = local_xy(o, a)
    bx, by = local_xy(o, b)
    z = ax * by - ay * bx
    return 1.0 if z > 0 else (-1.0 if z < 0 else 0.0)


def polyline_curvature_sign(points: Sequence[Point], idx: int) -> float:
    """폴리라인 정점 idx에서의 굽은 방향 부호.

    +1: 좌회전(반시계) 볼록, -1: 우회전(시계) 볼록, 0: 직선/양끝.
    이전-현재-다음 세 점의 외적 부호를 쓴다.
    """
    if idx <= 0 or idx >= len(points) - 1:
        return 0.0
    prev, cur, nxt = points[idx - 1], points[idx], points[idx + 1]
    px, py = local_xy(cur, prev)
    nx, ny = local_xy(cur, nxt)
    # (cur→prev) × (cur→next)
    z = px * ny - py * nx
    return 1.0 if z > 0 else (-1.0 if z < 0 else 0.0)


def circumcircle(origin: Point, a: Point, b: Point, c: Point):
    """origin 국지 평면에서 세 점의 외접원 (중심_xy, 반지름). 공선이면 None."""
    ax, ay = local_xy(origin, a)
    bx, by = local_xy(origin, b)
    cx, cy = local_xy(origin, c)
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    r = math.hypot(ux - ax, uy - ay)
    return (ux, uy), r


def inside_of_arc(origin: Point, a: Point, b: Point, c: Point):
    """origin(건물)이 세 점이 그리는 호의 오목한 안쪽에 있는가.

    Returns True(안쪽/환포), False(바깥/반궁), None(직선·판정불가).
    건물에서 곡률 중심까지 거리가 반지름보다 작으면 안쪽이다.
    """
    cc = circumcircle(origin, a, b, c)
    if cc is None:
        return None
    (ux, uy), r = cc
    return math.hypot(ux, uy) < r


def menger_curvature(a: Point, b: Point, c: Point) -> float:
    """세 점을 지나는 원의 곡률(1/m). 직선이면 0.

    Menger curvature = 4·area / (|ab|·|bc|·|ca|).
    """
    ab = haversine(a, b)
    bc = haversine(b, c)
    ca = haversine(c, a)
    if ab == 0 or bc == 0 or ca == 0:
        return 0.0
    # 국지 평면에서의 부호있는 면적
    ax, ay = local_xy(a, a)  # (0,0)
    bx, by = local_xy(a, b)
    cx, cy = local_xy(a, c)
    area2 = abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay))  # 2×area
    return (2.0 * area2) / (ab * bc * ca)
