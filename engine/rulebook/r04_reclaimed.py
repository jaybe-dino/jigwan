"""R04 매립지·구하도 — 배점 5 (살 성격). (룰북 §4)

과거 하천·논·습지·매립이었던 필지 감점.
"""

from __future__ import annotations

from engine.models import CATEGORY_HYEONGGI, RuleResult, SiteFeatures

MAX_SCORE = 5.0
CODE, NAME = "R04", "매립구하도"
THEORY = "형기론 · 지기(地氣)·지반"

# 과거 지목별 감점 계수 (1.0 = 최대 감점)
TYPE_COEF = {
    "하천": 1.0, "구하도": 1.0,
    "습지": 0.9, "갯벌": 0.9,
    "매립": 0.8,
    "논": 0.6, "답": 0.6,
    "저수지": 0.9, "연못": 0.85,
}


def rule_reclaimed(f: SiteFeatures) -> RuleResult:
    past = f.historical.past_types if f.historical else []
    hits = [(t, TYPE_COEF[t]) for t in past if t in TYPE_COEF]

    if not hits:
        return RuleResult(
            code=CODE, name=NAME, category=CATEGORY_HYEONGGI,
            max_score=MAX_SCORE, score=MAX_SCORE, applicable=True,
            evidence="과거에도 마른 땅이었습니다 — 지반이 안정된 터입니다.",
            theory=THEORY, tier="지반 안정", metrics={"past_types": past},
        )

    worst_type, coef = max(hits, key=lambda kv: kv[1])
    ratio = 1.0 - 0.8 * coef  # 계수 1.0이면 0.2까지 감점
    evidence = (
        f"이 필지는 과거 '{worst_type}'이었습니다 — 지반·수맥이 약한 터"
        f"(현대적으로도 침수·연약지반에 유의)입니다."
    )
    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_HYEONGGI,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier=f"과거 {worst_type}",
        metrics={"past_types": past, "worst_type": worst_type, "coef": coef},
    )
