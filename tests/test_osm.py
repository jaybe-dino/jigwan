"""무료 실데이터 수집기(OSM·OpenTopoData·Nominatim) 파싱 검증 — HTTP 모킹."""

from engine.models import LatLon
from pipeline.collectors.nominatim import NominatimGeocoder
from pipeline.collectors.opentopo import OpenTopoElevation
from pipeline.collectors.overpass import OverpassClient
from pipeline.collectors.osm import OsmCollectors


def stub(resp):
    def http(url, params=None, headers=None, timeout=10):
        return resp(url, params) if callable(resp) else resp
    return http


def test_opentopo_batches_and_caches():
    calls = []
    def http(url, params=None, headers=None, timeout=10):
        calls.append(params["locations"])
        n = params["locations"].count("|") + 1
        return {"results": [{"elevation": 100.0 + i} for i in range(n)]}
    e = OpenTopoElevation(http=http)
    vals = e.elevations([LatLon(37.5, 127.0), LatLon(37.6, 127.1)])
    assert vals == [100.0, 101.0]
    # 캐시: 같은 점 재요청 시 HTTP 추가 호출 없음
    e.elevations([LatLon(37.5, 127.0)])
    assert len(calls) == 1


def test_nominatim_parses():
    g = NominatimGeocoder(http=stub([{"lat": "37.6119", "lon": "126.974"}]))
    info = g.geocode("서울 종로구 평창동")
    assert abs(info.location.lat - 37.6119) < 1e-6


def test_overpass_waterways_and_peaks():
    fc = {"elements": [
        {"type": "way", "tags": {"waterway": "river", "name": "홍제천"},
         "geometry": [{"lat": 37.61, "lon": 126.97}, {"lat": 37.611, "lon": 126.971}]},
    ]}
    c = OverpassClient(http=stub(fc))
    ways = c.waterways(LatLon(37.61, 126.97), 800)
    assert len(ways) == 1 and ways[0].name == "홍제천"

    pc = OverpassClient(http=stub({"elements": [
        {"type": "node", "lat": 37.658, "lon": 126.977, "tags": {"natural": "peak", "name": "북한산", "ele": "836"}}
    ]}))
    peaks = pc.peaks(LatLon(37.61, 126.97), 4000)
    assert peaks and peaks[0][1] == "북한산" and peaks[0][2] == 836.0


def test_overpass_mirror_fallback_recovers():
    """첫 미러가 실패해도 다음 미러로 하천을 찾아낸다(‘조용한 실패→물길 없음’ 방지)."""
    calls = []
    def http(url, params=None, headers=None, timeout=10):
        calls.append(url)
        if "overpass-api.de" in url:
            raise RuntimeError("timeout")
        return {"elements": [
            {"type": "way", "id": 1, "tags": {"waterway": "stream", "name": "신림천"},
             "geometry": [{"lat": 37.48, "lon": 126.92}, {"lat": 37.481, "lon": 126.921}]}
        ]}
    c = OverpassClient(http=http)
    ways = c.waterways(LatLon(37.48, 126.92), 1500)
    assert len(calls) == 2 and ways and ways[0].name == "신림천"


def test_overpass_waterways_include_area_water():
    """면(natural=water)으로 매핑된 물도 하천으로 잡는다."""
    resp = {"elements": [
        {"type": "way", "id": 9, "tags": {"natural": "water", "name": "호수"},
         "geometry": [{"lat": 37.5, "lon": 127.0}, {"lat": 37.5, "lon": 127.001},
                      {"lat": 37.501, "lon": 127.001}]}
    ]}
    c = OverpassClient(http=stub(resp))
    ways = c.waterways(LatLon(37.5, 127.0), 800)
    assert len(ways) == 1 and ways[0].name == "호수"


def test_osm_landmarks_assigns_back_mountain():
    # 남향(180) 집 → 배면=북(0°). 북쪽 봉우리가 back에 배정돼야.
    peak_resp = {"elements": [
        {"type": "node", "lat": 37.66, "lon": 126.974, "tags": {"natural": "peak", "name": "북한산 보현봉"}}
    ]}
    osm = OsmCollectors()
    osm.overpass = OverpassClient(http=stub(peak_resp))
    osm._facing = 180.0
    lm = osm.landmarks(LatLon(37.6119, 126.974))
    assert lm.get("back") == "북한산 보현봉"
