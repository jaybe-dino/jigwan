"""실 API 수집기 파싱·팩토리 검증 — HTTP는 모킹(네트워크 없이)."""

from engine.geo import angle_diff, facing_from_footprint, principal_axis_deg
from engine.models import LatLon
from engine.samples import offset
from pipeline.collectors.building import BuildingRegistryClient
from pipeline.collectors.dem import sample_fan
from pipeline.collectors.factory import make_collectors
from pipeline.collectors.kakao import KakaoClient
from pipeline.collectors.vworld import VWorldClient
from pipeline.config import Config


def _stub(response):
    """호출을 기록하고 고정 응답을 주는 http 스텁."""
    calls = []

    def http(url, params=None, headers=None, timeout=10.0):
        calls.append({"url": url, "params": params, "headers": headers})
        return response(calls) if callable(response) else response

    http.calls = calls
    return http


# --- Kakao 지오코딩 ---
def test_kakao_geocode_parses_coords():
    http = _stub({"documents": [{"x": "126.9010", "y": "37.5650"}]})
    c = KakaoClient("KEY", http=http)
    info = c.geocode("서울 마포구 월드컵로 212")
    assert abs(info.location.lat - 37.5650) < 1e-6
    assert abs(info.location.lon - 126.9010) < 1e-6
    assert http.calls[0]["headers"]["Authorization"] == "KakaoAK KEY"


def test_kakao_geocode_no_result_raises():
    c = KakaoClient("KEY", http=_stub({"documents": []}))
    try:
        c.geocode("없는주소")
        assert False
    except ValueError:
        pass


def test_kakao_pois_maps_categories():
    def resp(calls):
        q = calls[-1]["params"]["query"]
        if q == "공원":
            return {"documents": [{"x": "127.0", "y": "37.5", "place_name": "근린공원"}]}
        return {"documents": []}

    c = KakaoClient("KEY", http=_stub(resp))
    pois = c.pois(LatLon(37.5, 127.0), 500)
    parks = [p for p in pois if p.category == "park"]
    assert len(parks) == 1 and parks[0].name == "근린공원"


# --- VWorld 파싱 ---
def test_vworld_roads_parses_linestring():
    fc = {"response": {"result": {"featureCollection": {"features": [
        {"properties": {"ROAD_BT": 12, "RN": "월드컵로"},
         "geometry": {"type": "LineString", "coordinates": [[127.0, 37.5], [127.001, 37.5]]}}
    ]}}}}
    c = VWorldClient("KEY", http=_stub(fc))
    roads = c.roads(LatLon(37.5, 127.0), 200)
    assert len(roads) == 1 and roads[0].width_m == 12 and roads[0].name == "월드컵로"
    assert len(roads[0].points) == 2


def test_vworld_building_facing_from_polygon():
    # 남북으로 긴 직사각형 → 장축 남북(0°) → 향은 동/서(90/270) 후보
    fc = {"response": {"result": {"featureCollection": {"features": [
        {"geometry": {"type": "Polygon", "coordinates": [[
            [127.0000, 37.5000], [127.0002, 37.5000],
            [127.0002, 37.5010], [127.0000, 37.5010], [127.0000, 37.5000]]]}}
    ]}}}}
    c = VWorldClient("KEY", http=_stub(fc))
    facing = c.building_facing(LatLon(37.5005, 127.0001))
    assert facing is not None
    assert min(angle_diff(facing, 90), angle_diff(facing, 270)) < 5


# --- facing_from_footprint ---
def test_principal_axis_ns_rectangle():
    o = LatLon(37.5, 127.0)
    ring = [o.as_tuple(), offset(o, 100, 0).as_tuple(),
            offset(o, 100, 0).as_tuple(), o.as_tuple()]  # 남북 방향
    # 남북으로 긴 폴리곤
    pts = [offset(o, 0, 0).as_tuple(), offset(o, 100, 0).as_tuple(),
           offset(o, 100, 0.02).as_tuple()]
    ax = principal_axis_deg(pts)
    assert min(angle_diff(ax, 0), angle_diff(ax, 180)) < 15


def test_facing_toward_bias():
    o = LatLon(37.5, 127.0)
    # 동서로 긴 건물 → 향 후보 남/북. toward를 남쪽에 두면 남향 선택.
    pts = [offset(o, 0, 90).as_tuple(), offset(o, 60, 90).as_tuple(),
           offset(o, 60, 91).as_tuple()]
    south = offset(o, 200, 180)
    facing = facing_from_footprint(pts, toward=south.as_tuple())
    assert angle_diff(facing, 180) < 60


# --- DEM 팬 샘플러 ---
def test_dem_sample_fan_uses_elevation_fn():
    center = LatLon(37.5, 127.0)
    # 북쪽만 높은 합성 고도 함수
    def elev(lat, lon):
        return 50.0 if lat > center.lat + 0.001 else 0.0

    samples = sample_fan(center, elev, bearings=[0, 180], distances=[500, 1000])
    assert len(samples) == 4
    north = [s for s in samples if s.point.lat > center.lat]
    assert all(s.elevation_m == 50.0 for s in north)


# --- 건축물대장 파싱 ---
def test_building_floors_parses():
    resp = {"response": {"body": {"items": {"item": [{"grndFlrCnt": "15"}]}}}}
    c = BuildingRegistryClient("KEY", http=_stub(resp))
    assert c.floors("11440", "10800", "212") == 15


# --- 팩토리 폴백 ---
def test_factory_falls_back_to_fixture_without_keys():
    collectors, live = make_collectors("명당", config=Config())
    assert live is False
    # 픽스처는 Collectors 계약을 만족 → building() 동작
    info = collectors.building("명당")
    assert info.location is not None


def test_factory_uses_api_with_kakao_key():
    collectors, live = make_collectors("주소", config=Config(kakao_key="KEY"))
    assert live is True
    assert collectors.__class__.__name__ == "ApiCollectors"
