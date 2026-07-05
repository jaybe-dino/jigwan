"""개별 판정 룰 검증 — 근거문에 숫자가 박히는지, 판정 방향이 맞는지."""

import re

from engine.models import (
    Building,
    HistoricalLand,
    LatLon,
    POI,
    RailOverpass,
    RoadSegment,
    SiteFeatures,
    StreamSegment,
)
from engine.rulebook.r01_baesan_imsu import rule_baesan_imsu
from engine.rulebook.r03_hwanpo import rule_hwanpo_bangung
from engine.rulebook.r04_reclaimed import rule_reclaimed
from engine.rulebook.r05_jikchung import rule_jikchung_sal
from engine.rulebook.r07_rail_overpass import rule_rail_overpass
from engine.rulebook.r08_orientation import rule_orientation
from engine.rulebook.r09_floor_dong import rule_floor_dong
from engine.rulebook.r10_poi import rule_poi
from engine.samples import biboji_site, myeongdang_site, offset

HAS_DIGIT = re.compile(r"\d")


def _base(loc=LatLon(37.5, 127.0), facing=180.0, floors=None):
    return SiteFeatures(address="t", building=Building(loc, facing, 10.0, floors))


# --- R01 배산임수 ---
def test_r01_hyeonmu_detected():
    r = rule_baesan_imsu(myeongdang_site())
    assert r.metrics["max_gain_m"] >= 20
    assert r.score >= r.max_score * 0.8
    assert HAS_DIGIT.search(r.evidence)  # 숫자 박힌 근거문


def test_r01_no_ridge_low_score():
    r = rule_baesan_imsu(_base())  # DEM 없음
    assert r.score <= r.max_score * 0.2


# --- R03 환포/반궁 ---
def test_r03_embrace_is_good():
    r = rule_hwanpo_bangung(myeongdang_site())
    assert r.metrics["embrace_sign"] == 1.0
    assert r.score > r.max_score * 0.5
    assert "환포수" in r.evidence


def test_r03_no_stream_neutral():
    r = rule_hwanpo_bangung(_base())
    assert r.score == r.max_score * 0.5


# --- R04 매립·구하도 ---
def test_r04_clean_full_score():
    f = _base()
    f.historical = HistoricalLand(past_types=[])
    assert rule_reclaimed(f).score == 5.0


def test_r04_reclaimed_penalized():
    f = _base()
    f.historical = HistoricalLand(past_types=["하천"])
    r = rule_reclaimed(f)
    assert r.score < 5.0 and "하천" in r.evidence


# --- R05 직충살 ---
def test_r05_jikchung_penalized():
    r = rule_jikchung_sal(biboji_site())
    assert r.score < r.max_score
    assert "직충살" in r.evidence and HAS_DIGIT.search(r.evidence)


def test_r05_no_road_full():
    assert rule_jikchung_sal(_base()).score == 8.0


# --- R07 고가·철로 ---
def test_r07_near_overpass_penalized():
    r = rule_rail_overpass(biboji_site())
    assert r.score < r.max_score


def test_r07_none_full():
    assert rule_rail_overpass(_base()).score == 5.0


# --- R08 좌향 ---
def test_r08_cardinal_orientation():
    r = rule_orientation(_base(facing=180.0))  # 정남(오향)
    assert "오향" in r.evidence
    assert r.metrics["sect"] in ("동사택", "서사택")


# --- R09 층수·동 ---
def test_r09_applicable_only_with_floors():
    assert rule_floor_dong(_base(floors=None)).applicable is False
    assert rule_floor_dong(_base(floors=12)).applicable is True


# --- R10 POI ---
def test_r10_hyung_poi_lowers_score():
    r = rule_poi(biboji_site())
    assert r.score < r.max_score * 0.5


def test_r10_gil_poi_raises_score():
    r = rule_poi(myeongdang_site())
    assert r.score > r.max_score * 0.5
