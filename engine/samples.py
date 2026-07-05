"""샘플 터 — 데모/테스트 공용 픽스처.

실제 공공 API 연동 전까지 판정 로직을 검증하기 위한 합성 데이터.
좌표는 대략 서울 마포 일대. 파이프라인이 만들 SiteFeatures와 동일한 형태.
"""

from __future__ import annotations

import math
from typing import List

from engine.models import (
    Building,
    ElevationSample,
    HistoricalLand,
    LatLon,
    POI,
    Precision,
    RailOverpass,
    RoadSegment,
    SiteFeatures,
    StreamSegment,
)

_LAT_M = 111_320.0


def offset(origin: LatLon, dist_m: float, bearing_deg: float) -> LatLon:
    """origin에서 거리·방위로 떨어진 점(근사)."""
    b = math.radians(bearing_deg)
    dlat = dist_m * math.cos(b) / _LAT_M
    dlon = dist_m * math.sin(b) / (_LAT_M * math.cos(math.radians(origin.lat)))
    return LatLon(origin.lat + dlat, origin.lon + dlon)


def _ridge(origin, bearing, dist, gain, ground=20.0) -> ElevationSample:
    return ElevationSample(offset(origin, dist, bearing), ground + gain)


def myeongdang_site() -> SiteFeatures:
    """명당형 — 뒤에 든든한 현무, 청룡백호 균형, 환포수, 깨끗한 지반, 공원 인접."""
    loc = LatLon(37.5650, 126.9010)
    facing = 170.0  # 남향
    back = (facing + 180.0) % 360.0      # ≈ 350 (북)
    left = (facing + 90.0) % 360.0       # ≈ 260 (서)
    right = (facing - 90.0) % 360.0      # ≈ 80 (동)

    dem: List[ElevationSample] = [
        _ridge(loc, back, 380, 42),      # 현무: 북 380m +42m
        _ridge(loc, back - 10, 500, 38),
        _ridge(loc, left, 450, 24),      # 좌청룡
        _ridge(loc, right, 470, 22),     # 우백호
        _ridge(loc, facing, 600, 12),    # 안산(낮음)
        _ridge(loc, back, 100, 2),       # 가까운 평지(반경 밖 아님이지만 낮음)
    ]

    # 환포수: 건물을 곡률 중심으로 하는 호(弧) → 건물이 오목한 안쪽(환포)
    # 모든 점을 건물에서 등거리(300m)에 두면 곡률 중심이 곧 건물이 된다.
    stream_pts = [
        offset(loc, 300, 120),
        offset(loc, 300, 150),
        offset(loc, 300, 180),
        offset(loc, 300, 210),
        offset(loc, 300, 240),
    ]
    streams = [StreamSegment([LatLon(p.lat, p.lon) for p in stream_pts], name="샛강", width_m=20)]

    pois = [
        POI(offset(loc, 250, 90), "park", "근린공원"),
        POI(offset(loc, 300, 300), "school", "초등학교"),
        POI(offset(loc, 350, 60), "subway", "지하철역"),
    ]

    return SiteFeatures(
        address="서울특별시 마포구 월드컵로 212, 성산시영아파트 3동 1204호",
        building=Building(loc, facing_deg=facing, ground_elevation_m=20.0, floors=12),
        dem=dem,
        streams=streams,
        roads=[],
        rails_overpasses=[],
        pois=pois,
        historical=HistoricalLand(past_types=[]),
        precision=Precision(dong_position="center"),
    )


def biboji_site() -> SiteFeatures:
    """비보형 — 배산 없음, 직충살, 매립지, 흉 POI. (비보 처방 대상)"""
    loc = LatLon(37.5400, 126.9500)
    facing = 90.0  # 동향

    # 배면(서)에 능선 없음, 앞쪽만 낮은 언덕
    dem = [_ridge(loc, 90, 400, 8), _ridge(loc, 45, 500, 6)]

    # 직충살: 정면(동, 90°)에서 T자 도로 머리가 찔러옴
    road_head = offset(loc, 70, 90)
    jikchung = RoadSegment(
        points=[LatLon(road_head.lat, road_head.lon), offset(loc, 200, 90)],
        width_m=14.0, name="큰길", is_t_head=True,
    )

    pois = [
        POI(offset(loc, 120, 200), "funeral", "장례식장"),
        POI(offset(loc, 180, 300), "nightlife", "유흥가"),
    ]

    return SiteFeatures(
        address="서울특별시 동대문구 왕산로 220, 청솔빌라 301호",
        building=Building(loc, facing_deg=facing, ground_elevation_m=10.0, floors=3),
        dem=dem,
        streams=[],
        roads=[jikchung],
        rails_overpasses=[RailOverpass("overpass", offset(loc, 90, 300), height_diff_m=9.0)],
        pois=pois,
        historical=HistoricalLand(past_types=["논"]),
        precision=None,
    )
