"""룰북 v1 — 개별 판정 룰 모음.

각 룰은 `SiteFeatures`를 받아 `RuleResult`(점수 + 근거문)를 돌려주는 함수다.
`ALL_RULES`는 R01~R10을 배점 순서대로 담는다. 스코어링은 engine.scoring 참조.
"""

from engine.rulebook.r01_baesan_imsu import rule_baesan_imsu
from engine.rulebook.r02_sasinsa import rule_sasinsa
from engine.rulebook.r03_hwanpo import rule_hwanpo_bangung
from engine.rulebook.r04_reclaimed import rule_reclaimed
from engine.rulebook.r05_jikchung import rule_jikchung_sal
from engine.rulebook.r06_bangung_road import rule_bangung_sal
from engine.rulebook.r07_rail_overpass import rule_rail_overpass
from engine.rulebook.r08_orientation import rule_orientation
from engine.rulebook.r09_floor_dong import rule_floor_dong
from engine.rulebook.r10_poi import rule_poi

ALL_RULES = [
    rule_baesan_imsu,   # R01 배산임수 15
    rule_sasinsa,       # R02 사신사 10
    rule_hwanpo_bangung,  # R03 환포/반궁수 10
    rule_reclaimed,     # R04 매립·구하도 5
    rule_jikchung_sal,  # R05 직충살 8
    rule_bangung_sal,   # R06 도로 반궁살 7
    rule_rail_overpass,  # R07 고가·철로 5
    rule_orientation,   # R08 좌향 24방위 15
    rule_floor_dong,    # R09 층수·동배치 10
    rule_poi,           # R10 주변 POI 15
]

__all__ = ["ALL_RULES"]
