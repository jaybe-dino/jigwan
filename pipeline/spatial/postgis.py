"""PostGIS 실행부 — spatial.sql 함수를 호출한다.

psycopg(2/3)가 있고 JIGWAN_DATABASE_URL 이 설정된 경우에만 동작한다.
없으면 connect()가 None을 돌려주고, 호출부는 순수 파이썬 경로로 폴백한다.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from engine.models import ElevationSample, LatLon

try:  # psycopg3 우선, 없으면 psycopg2
    import psycopg as _pg  # type: ignore

    _V = 3
except ImportError:  # pragma: no cover
    try:
        import psycopg2 as _pg  # type: ignore

        _V = 2
    except ImportError:
        _pg = None
        _V = 0


def available() -> bool:
    return _pg is not None and bool(os.environ.get("JIGWAN_DATABASE_URL"))


def connect():
    if not available():
        return None
    return _pg.connect(os.environ["JIGWAN_DATABASE_URL"])


def load_dem(conn, samples: List[ElevationSample]) -> None:
    """DEM 샘플을 dem_point 에 적재(검증용, 기존 데이터는 지우고 재적재)."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM dem_point")
        for s in samples:
            cur.execute(
                "INSERT INTO dem_point (geom, elev_m) "
                "VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)",
                (s.point.lon, s.point.lat, s.elevation_m),
            )
    conn.commit()


def sector_max_gain(
    conn,
    origin: LatLon,
    ground: float,
    center_deg: float,
    half_deg: float,
    r_min: float,
    r_max: float,
) -> Tuple[float, Optional[float], Optional[float]]:
    """jigwan_sector_max_gain 호출 → (max_gain, dist_m, azimuth_deg)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT max_gain, dist_m, azimuth_deg FROM "
            "jigwan_sector_max_gain("
            "ST_SetSRID(ST_MakePoint(%s,%s),4326), %s, %s, %s, %s, %s)",
            (origin.lon, origin.lat, ground, center_deg, half_deg, r_min, r_max),
        )
        row = cur.fetchone()
    if row is None:
        return 0.0, None, None
    return float(row[0]), float(row[1]), float(row[2])
