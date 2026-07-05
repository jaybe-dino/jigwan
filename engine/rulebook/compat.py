"""궁합(11a/11b) — 인터페이스 + 근거문 템플릿만 (룰북 §11).

만세력 계산·본명궁 산출은 M3. 여기서는 M2/M3가 채울 계약(시그니처)과
근거문 템플릿을 확정해 둔다. 터 점수와 독립적으로 궁합%를 산출한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from engine.geo import clamp
from engine.models import RuleResult, SajuProfile, SiteFeatures


@dataclass
class CompatResult:
    percent: float           # 궁합% 0~100
    ohaeng_delta: float      # 11a ±30
    sect_delta: float        # 11b ±20
    ohaeng_evidence: str
    sect_evidence: str


def compute_ohaeng_match(saju: SajuProfile, site: SiteFeatures) -> RuleResult:
    """11a 오행 매칭 (±30). 만세력 용신 ↔ 터·건물 오행 상생상극.

    M3 구현 예정. 현재는 NotImplemented 계약만 노출한다.
    근거문 템플릿:
      "용신 {용신}이 이 터의 {터오행} 기운과 상생 — 재물 궁합 +{n}"
    """
    raise NotImplementedError("오행 매칭은 만세력 엔진(M3)에서 구현")


def compute_sect_match(saju: SajuProfile, site: SiteFeatures) -> RuleResult:
    """11b 동/서사택 × 본명궁 (±20).

    R08의 사택 계열과 생년 본명궁 일치 여부.
    근거문 템플릿:
      "본명궁 {구성}은 {동/서}사택 사람 — 이 집의 {사택}과 {일치/불일치}"
    """
    raise NotImplementedError("본명궁 매칭은 명리 엔진(M3)에서 구현")


def compatibility_percent(ohaeng_delta: float, sect_delta: float) -> float:
    """궁합% = clamp(50 + 11a + 11b, 0, 100). (룰북 §11)"""
    return clamp(50.0 + ohaeng_delta + sect_delta, 0.0, 100.0)
