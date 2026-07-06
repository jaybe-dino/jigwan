"""실제 만세력(사주) — korean_lunar_calendar(KARI 기반) 사용, 데모 아님.

생년월일(+시) → 사주 4주(년월일시 간지) → 오행 분포 → 억부 용신 → 본명궁(구성).
궁합(engine.rulebook.compat)에서 소비한다.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

GAN_OH = {"갑": "목", "을": "목", "병": "화", "정": "화", "무": "토",
          "기": "토", "경": "금", "신": "금", "임": "수", "계": "수"}
JI_OH = {"자": "수", "축": "토", "인": "목", "묘": "목", "진": "토", "사": "화",
         "오": "화", "미": "토", "신": "금", "유": "금", "술": "토", "해": "수"}
# A가 B를 생(生)
SAENG = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
# A가 B를 극(剋)
GEUK = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}
GAN = "갑을병정무기경신임계"
JI = "자축인묘진사오미신유술해"

# 시두법: 일간 → 자시(子時) 천간 시작 인덱스
HOUR_GAN_START = {"갑": 0, "기": 0, "을": 2, "경": 2, "병": 4, "신": 4,
                  "정": 6, "임": 6, "무": 8, "계": 8}


@dataclass
class Saju:
    pillars: Dict[str, str]        # {'년':'경오','월':'신사','일':'경진','시':...}
    ilgan: str                     # 일간(천간)
    ilgan_oh: str                  # 일간 오행
    ohaeng: Dict[str, int]         # 오행 분포
    yongsin: str                   # 용신 오행
    strong: bool                   # 일간 신강 여부
    bonmyeong: int                 # 본명성(구성 1~9)
    sect: str                      # 동사택/서사택 (본명궁 계열)
    time_known: bool


def _hour_branch(hour: int) -> int:
    return ((hour + 1) // 2) % 12


def _digit_root(n: int) -> int:
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def _bonmyeong(year: int, is_male: bool) -> int:
    """본명성(구성 九星) — 입춘 기준 연도 수리. 1~9."""
    s = _digit_root(year)
    star = (11 - s) if is_male else (s + 4)
    while star > 9:
        star -= 9
    if star <= 0:
        star = 9
    return star


# 구성 → 동/서사택 (감1·진3·손4·리9=동, 곤2·건6·태7·간8=서, 5=서 계열)
_STAR_SECT = {1: "동사택", 9: "동사택", 3: "동사택", 4: "동사택",
              2: "서사택", 6: "서사택", 7: "서사택", 8: "서사택", 5: "서사택"}


def compute_saju(year: int, month: int, day: int,
                 is_male: bool = True, hour: Optional[int] = None) -> Saju:
    from korean_lunar_calendar import KoreanLunarCalendar

    cal = KoreanLunarCalendar()
    cal.setSolarDate(year, month, day)
    toks = cal.getGapJaString().split()  # ['경오년','신사월','경진일']
    ygz, mgz, dgz = toks[0][:2], toks[1][:2], toks[2][:2]

    pillars = {"년": ygz, "월": mgz, "일": dgz}
    counts: Dict[str, int] = defaultdict(int)
    for gz in (ygz, mgz, dgz):
        counts[GAN_OH[gz[0]]] += 1
        counts[JI_OH[gz[1]]] += 1

    time_known = hour is not None
    if time_known:
        hb = _hour_branch(hour)  # 지지 인덱스
        hg = (HOUR_GAN_START[dgz[0]] + hb) % 10  # 시두법
        sgz = GAN[hg] + JI[hb]
        pillars["시"] = sgz
        counts[GAN_OH[sgz[0]]] += 1
        counts[JI_OH[sgz[1]]] += 1

    ilgan = dgz[0]
    ilgan_oh = GAN_OH[ilgan]
    gen_of_ilgan = next(a for a, b in SAENG.items() if b == ilgan_oh)  # 나를 생하는 오행(印)
    strength = counts.get(ilgan_oh, 0) + counts.get(gen_of_ilgan, 0)
    total = sum(counts.values())
    strong = strength >= total / 2

    # 억부 용신: 신강이면 일간을 극하는 오행(관성), 신약이면 인성(생하는 오행)
    yongsin = next(a for a, b in GEUK.items() if b == ilgan_oh) if strong else gen_of_ilgan

    bm = _bonmyeong(year, is_male)
    return Saju(
        pillars=pillars, ilgan=ilgan, ilgan_oh=ilgan_oh, ohaeng=dict(counts),
        yongsin=yongsin, strong=strong, bonmyeong=bm, sect=_STAR_SECT[bm],
        time_known=time_known,
    )
