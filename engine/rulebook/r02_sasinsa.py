"""R02 사신사(四神砂) — 배점 10. (룰북 §2)

좌청룡(facing+90)·우백호(facing-90)·안산(facing) 방위의 능선 존재/균형.
"""

from __future__ import annotations

from engine.geo import clamp
from engine.models import CATEGORY_HYEONGGI, RuleResult, SiteFeatures
from engine.rulebook.base import max_elev_gain_in_sector

MAX_SCORE = 10.0
CODE, NAME = "R02", "사신사"
THEORY = "형기론 · 좌청룡·우백호·안산"


def _presence(f: SiteFeatures, center_deg: float) -> tuple[float, float]:
    """(존재도 0~1, 최대 고도차 m)."""
    gain, _dist, _brg = max_elev_gain_in_sector(
        f.building.location, f.building.ground_elevation_m, f.dem, center_deg
    )
    return clamp(gain / 30.0, 0.0, 1.0), gain


def rule_sasinsa(f: SiteFeatures) -> RuleResult:
    facing = f.building.facing_deg
    e_left, g_left = _presence(f, (facing + 90.0) % 360.0)   # 좌청룡
    e_right, g_right = _presence(f, (facing - 90.0) % 360.0)  # 우백호
    e_front, g_front = _presence(f, facing % 360.0)           # 안산

    balance = 1.0 - abs(e_left - e_right)
    ratio = 0.35 * e_left + 0.35 * e_right + 0.30 * balance

    both_weak = e_left < 0.17 and e_right < 0.17  # 둘 다 Δh<5m 수준
    if both_weak:
        bal_word = "청룡·백호가 모두 낮아 국세가 열린 형국"
    elif balance >= 0.8:
        bal_word = "청룡백호가 감싸 안는 균형"
    elif balance >= 0.5:
        bal_word = "한쪽으로 기운 국세"
    else:
        bal_word = "호위가 크게 치우친 형국"

    if g_front >= 15:
        front_word = "앞을 받쳐주는 안산이 뚜렷합니다"
    elif g_front >= 5:
        front_word = "낮은 안산이 앞을 감쌉니다"
    else:
        front_word = "안산이 트여 앞이 허합니다"

    evidence = (
        f"좌청룡 +{round(g_left)}m · 우백호 +{round(g_right)}m "
        f"— {bal_word}. {front_word}."
    )
    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_HYEONGGI,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier=bal_word,
        metrics={
            "left_gain_m": round(g_left, 1),
            "right_gain_m": round(g_right, 1),
            "front_gain_m": round(g_front, 1),
            "balance": round(balance, 2),
        },
    )
