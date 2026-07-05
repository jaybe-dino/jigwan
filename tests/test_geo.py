"""공간연산 기초(engine.geo) 검증 — 해석적 기준값 대비."""

import math

from engine.geo import (
    angle_diff,
    bearing,
    circumcircle,
    haversine,
    in_sector,
    inside_of_arc,
    menger_curvature,
    point_to_segment,
)
from engine.models import LatLon
from engine.samples import offset


def test_haversine_known_distance():
    d = haversine((37.5, 127.0), (37.51, 127.0))  # 위도 0.01°
    assert abs(d - 1113.2) < 3.0


def test_bearing_cardinals():
    assert abs(bearing((37.5, 127.0), (37.6, 127.0))) < 0.5          # 북
    assert abs(bearing((37.5, 127.0), (37.5, 127.1)) - 90.0) < 0.5   # 동


def test_angle_diff_wraparound():
    assert angle_diff(350, 10) == 20
    assert angle_diff(10, 350) == 20
    assert angle_diff(0, 180) == 180


def test_in_sector():
    assert in_sector(target_deg=5, center_deg=0, half_width_deg=22.5)
    assert not in_sector(target_deg=30, center_deg=0, half_width_deg=22.5)


def test_point_to_segment_perpendicular():
    o = LatLon(37.5, 127.0)
    a = offset(o, 100, 90).as_tuple()   # 동 100m
    b = offset(o, 100, 270).as_tuple()  # 서 100m — 원점 지나는 선분
    d, _cpt, _t = point_to_segment(o.as_tuple(), a, b)
    assert d < 1.0  # 선분이 원점을 지남


def test_menger_curvature_circle():
    o = LatLon(37.5, 127.0)
    pts = [offset(o, 300, deg).as_tuple() for deg in (0, 30, 60)]
    k = menger_curvature(*pts)
    assert abs(k - 1 / 300) < 5e-5


def test_circumcircle_recovers_center():
    o = LatLon(37.5, 127.0)
    pts = [offset(o, 300, deg).as_tuple() for deg in (0, 30, 60)]
    (ux, uy), r = circumcircle(o.as_tuple(), *pts)
    assert abs(r - 300) < 2.0
    assert math.hypot(ux, uy) < 2.0


def test_inside_of_arc():
    o = LatLon(37.5, 127.0)
    pts = [offset(o, 300, deg).as_tuple() for deg in (0, 30, 60)]
    assert inside_of_arc(o.as_tuple(), *pts) is True                 # 중심=안쪽
    far = offset(o, 900, 30)
    assert inside_of_arc(far.as_tuple(), *pts) is False              # 밖=바깥


def test_circumcircle_collinear_none():
    o = LatLon(37.5, 127.0)
    a = offset(o, 100, 90).as_tuple()
    b = offset(o, 200, 90).as_tuple()
    c = offset(o, 300, 90).as_tuple()
    assert circumcircle(o.as_tuple(), a, b, c) is None
