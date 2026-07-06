"""궁합(11a/11b) — 실제 사주(만세력) 기반. 데모값 아님.

- 11a 오행 매칭(±30): 사주 용신 ↔ 집의 방위 오행 상생상극
- 11b 동/서사택(±20): 본명궁(구성) 사택 ↔ 집 좌향 사택 일치
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from engine.geo import clamp
from engine.saju import GEUK, SAENG, compute_saju

# 8방위(집 향) → 방위 오행
_DIR_OH = [("북", "수"), ("북동", "토"), ("동", "목"), ("남동", "목"),
           ("남", "화"), ("남서", "토"), ("서", "금"), ("북서", "금")]


def _facing_element(facing_deg: float) -> str:
    i = round((facing_deg % 360) / 45) % 8
    return _DIR_OH[i][1]


@dataclass
class CompatResult:
    percent: int
    ohaeng_delta: int
    sect_delta: int
    house_element: str
    yongsin: str
    user_sect: str
    house_sect: str
    match_sect: bool
    saju_pillars: Dict[str, str]
    time_known: bool
    caption: str


def compute_compat(facing_deg: float, house_sect: str, year: int, month: int, day: int,
                   is_male: bool = True, hour: Optional[int] = None) -> CompatResult:
    saju = compute_saju(year, month, day, is_male, hour)
    house_el = _facing_element(facing_deg)

    # 11a: 집 방위 오행 → 용신 관계
    y = saju.yongsin
    if house_el == y:
        oh = 22
    elif SAENG.get(house_el) == y:      # 집오행이 용신을 생 → 최고
        oh = 30
    elif SAENG.get(y) == house_el:      # 용신이 집오행을 생(설기)
        oh = 8
    elif GEUK.get(house_el) == y:       # 집오행이 용신을 극 → 흉
        oh = -25
    elif GEUK.get(y) == house_el:       # 용신이 집오행을 극(재성)
        oh = 10
    else:
        oh = 0

    # 11b: 사택 일치
    match = (saju.sect == house_sect)
    sect_delta = 20 if match else -18

    pct = int(round(clamp(50 + oh + sect_delta, 4, 97)))
    if pct >= 80:
        cap = "아주 잘 맞는 집이에요"
    elif pct >= 60:
        cap = "제법 잘 맞는 집"
    elif pct >= 45:
        cap = "무난한 궁합"
    else:
        cap = "비보로 맞춰가면 좋아요"

    return CompatResult(
        percent=pct, ohaeng_delta=oh, sect_delta=sect_delta,
        house_element=house_el, yongsin=y, user_sect=saju.sect,
        house_sect=house_sect, match_sect=match, saju_pillars=saju.pillars,
        time_known=saju.time_known, caption=cap,
    )
