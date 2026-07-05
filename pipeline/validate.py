"""공간연산 검증 (M1 산출물).

    python3 -m pipeline.validate

두 단계로 검증한다.
1) 순수 파이썬 공간연산(engine.geo)의 해석적 정확성 자체 검증 — DB 없이 항상 실행.
2) PostGIS 정합성 — JIGWAN_DATABASE_URL + psycopg + PostGIS가 있으면,
   동일 입력으로 SQL 함수를 돌려 순수 파이썬 결과와 오차범위 내 일치를 확인.
"""

from __future__ import annotations

import math
import sys

from engine.geo import (
    bearing,
    circumcircle,
    haversine,
    inside_of_arc,
    menger_curvature,
)
from engine.rulebook.base import max_elev_gain_in_sector
from engine.samples import myeongdang_site, offset
from engine.models import LatLon
from pipeline.spatial import postgis


def _check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name}" + (f"  ({detail})" if detail else ""))
    return ok


def selfcheck_geo() -> bool:
    print("[1] 순수 파이썬 공간연산 자체 검증 (해석적 기준값 대비)")
    ok = True

    # haversine: 위도 0.01° 차이 ≈ 1113.2m
    d = haversine((37.5, 127.0), (37.51, 127.0))
    ok &= _check("haversine 위도 0.01°", abs(d - 1113.2) < 3.0, f"{d:.1f}m")

    # bearing: 정북/정동
    bn = bearing((37.5, 127.0), (37.6, 127.0))
    be = bearing((37.5, 127.0), (37.5, 127.1))
    ok &= _check("bearing 정북≈0°", abs(bn) < 0.5, f"{bn:.2f}")
    ok &= _check("bearing 정동≈90°", abs(be - 90.0) < 0.5, f"{be:.2f}")

    # 부채꼴 최대 고도차: 명당형 배면(≈350°)에서 +42m 능선 검출
    f = myeongdang_site()
    back = (f.building.facing_deg + 180.0) % 360.0
    gain, dist, brg = max_elev_gain_in_sector(
        f.building.location, f.building.ground_elevation_m, f.dem, back
    )
    ok &= _check("부채꼴 최대 고도차 +42m 검출", abs(gain - 42.0) < 0.5, f"{gain:.1f}m@{dist:.0f}m")

    # 곡률: 반경 300m 원 위 세 점 → 곡률 ≈ 1/300
    o = LatLon(37.5, 127.0)
    a = offset(o, 300, 0).as_tuple()
    b = offset(o, 300, 30).as_tuple()
    c = offset(o, 300, 60).as_tuple()
    k = menger_curvature(a, b, c)
    ok &= _check("Menger 곡률 ≈ 1/300", abs(k - 1 / 300) < 5e-5, f"{k:.5f}")

    # 외접원 중심/반지름: 원 위 세 점 → 중심≈origin, R≈300
    cc = circumcircle(o.as_tuple(), a, b, c)
    if cc:
        (ux, uy), r = cc
        ok &= _check("외접원 반지름 ≈ 300m", abs(r - 300) < 2.0, f"R={r:.1f}")
        ok &= _check("외접원 중심 ≈ 원점", math.hypot(ux, uy) < 2.0, f"|c|={math.hypot(ux,uy):.2f}")

    # 환포/반궁: 원 중심(안쪽)=True, 원 밖 먼 점=False
    inside = inside_of_arc(o.as_tuple(), a, b, c)
    outside_pt = offset(o, 900, 30)  # 호 바깥
    outside = inside_of_arc(outside_pt.as_tuple(), a, b, c)
    ok &= _check("호 안쪽 판정(환포)", inside is True)
    ok &= _check("호 바깥 판정(반궁)", outside is False)

    return bool(ok)


def check_postgis() -> bool:
    print("\n[2] PostGIS 정합성 검증")
    if not postgis.available():
        print("  – 건너뜀: JIGWAN_DATABASE_URL 미설정 또는 psycopg 미설치")
        print("    (배포 시: docker compose up -d db && "
              "psql \"$JIGWAN_DATABASE_URL\" -f pipeline/db/schema.sql -f pipeline/db/spatial.sql)")
        return True  # 스킵은 실패가 아님

    f = myeongdang_site()
    back = (f.building.facing_deg + 180.0) % 360.0
    py_gain, py_dist, _ = max_elev_gain_in_sector(
        f.building.location, f.building.ground_elevation_m, f.dem, back
    )
    conn = postgis.connect()
    try:
        postgis.load_dem(conn, f.dem)
        pg_gain, pg_dist, _ = postgis.sector_max_gain(
            conn, f.building.location, f.building.ground_elevation_m,
            back, 22.5, 200.0, 1500.0,
        )
    finally:
        conn.close()

    ok = True
    ok &= _check("부채꼴 최대 고도차 py↔PostGIS 일치", abs(py_gain - pg_gain) < 0.1,
                 f"py={py_gain:.1f} pg={pg_gain:.1f}")
    ok &= _check("최근접 거리 py↔PostGIS 일치(±2m)", abs((py_dist or 0) - (pg_dist or 0)) < 2.0,
                 f"py={py_dist:.1f} pg={pg_dist:.1f}")
    return bool(ok)


def main() -> int:
    a = selfcheck_geo()
    b = check_postgis()
    print()
    if a and b:
        print("✅ 공간연산 검증 통과")
        return 0
    print("❌ 검증 실패")
    return 1


if __name__ == "__main__":
    sys.exit(main())
