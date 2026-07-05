"""R01 배산임수 — 배점 15. (룰북 §1)

배면 45° 부채꼴, 200m~1.5km 내 고도차 +20m 이상 능선 = 현무 성립.
"""

from __future__ import annotations

from engine.models import CATEGORY_HYEONGGI, RuleResult, SiteFeatures
from engine.rulebook.base import bearing_to_ko, max_elev_gain_in_sector

MAX_SCORE = 15.0
CODE, NAME = "R01", "배산임수"
THEORY = "형기론 · 현무(玄武)"


def _tier(gain: float) -> tuple[float, str]:
    """4단계 → (비율, 등급어)."""
    if gain >= 50:
        return 1.00, "든든한"
    if gain >= 20:
        return 0.80, "안정된"
    if gain >= 10:
        return 0.50, "다소 약한"
    return 0.20, "허(虛)한"


def rule_baesan_imsu(f: SiteFeatures) -> RuleResult:
    b = f.building
    back_deg = (b.facing_deg + 180.0) % 360.0
    gain, dist, brg = max_elev_gain_in_sector(
        b.location, b.ground_elevation_m, f.dem, back_deg
    )

    if gain <= 0 or dist is None:
        return RuleResult(
            code=CODE, name=NAME, category=CATEGORY_HYEONGGI,
            max_score=MAX_SCORE, score=MAX_SCORE * 0.20, applicable=True,
            evidence="배면에 의지할 능선이 없어 바람을 등지지 못하는 형국입니다.",
            theory=THEORY, tier="현무 허함",
            metrics={"back_deg": round(back_deg, 1), "max_gain_m": 0.0},
        )

    ratio, word = _tier(gain)
    ko = bearing_to_ko(brg)
    evidence = (
        f"{ko} {round(dist)}m, +{round(gain)}m 능선이 등을 받칩니다 "
        f"— 현무가 {word} 형국입니다."
    )
    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_HYEONGGI,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier=f"현무 {word}",
        metrics={
            "back_deg": round(back_deg, 1),
            "max_gain_m": round(gain, 1),
            "dist_m": round(dist, 1),
            "bearing_deg": round(brg, 1),
        },
    )
