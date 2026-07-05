"""스코어링·등급·게이지·파이프라인 조립 검증."""

from engine.models import Building, LatLon, SiteFeatures
from engine.scoring import Grade, assess_site
from engine.samples import biboji_site, myeongdang_site
from pipeline.assemble import assess_address
from pipeline.collectors.fixture import fixture_for


def test_grade_thresholds():
    assert Grade.of(96) == Grade.CHEONHA
    assert Grade.of(88) == Grade.MYEONGDANG
    assert Grade.of(75) == Grade.GILJI
    assert Grade.of(60) == Grade.PYEONGJI
    assert Grade.of(40) == Grade.BIBOJI


def test_score_bounds_and_axes():
    a = assess_site(myeongdang_site())
    assert 0 <= a.site_score <= 100
    assert set(a.gauges.keys()) == {"재물", "건강", "관계", "명예"}
    for v in a.gauges.values():
        assert 0 <= v <= 100


def test_myeongdang_beats_biboji():
    good = assess_site(myeongdang_site())
    bad = assess_site(biboji_site())
    assert good.site_score > bad.site_score
    assert good.grade in (Grade.GILJI, Grade.MYEONGDANG, Grade.CHEONHA)
    assert bad.needs_bibo  # 비보지는 비보 세트 필요


def test_applicable_excluded_from_denominator():
    # 층수 없는 터: R09 applicable=False → 분모에서 제외되어도 점수 산출
    f = SiteFeatures(address="t", building=Building(LatLon(37.5, 127.0), 180.0, 10.0, None))
    a = assess_site(f)
    r09 = next(r for r in a.results if r.code == "R09")
    assert r09.applicable is False
    assert 0 <= a.site_score <= 100


def test_pipeline_assembly_matches_engine():
    # 파이프라인 경로(수집기→조립→엔진)와 직접 엔진 호출 결과 일치.
    # 비보형은 정밀감정 입력(dong_position)이 없어 두 경로가 동일한 피처를 만든다.
    # (명당형은 dong_position="center"가 Lv.3 사용자 입력이라 주소만으론 재현 불가 —
    #  R09가 달라지므로 등가 비교 대상이 아니다.)
    direct = assess_site(biboji_site())
    via_pipeline = assess_address("(샘플·비보형)", fixture_for("비보"))
    assert direct.site_score == via_pipeline.site_score


def test_all_evidence_nonempty():
    a = assess_site(myeongdang_site())
    assert len(a.results) == 10
    for r in a.results:
        assert r.evidence and len(r.evidence) > 5
