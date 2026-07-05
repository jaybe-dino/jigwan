"""R07 고가·철로 인접 — 배점 5 (살 성격). (룰북 §7)

최근접 고가/철로 거리·높이차 기준 3단계 감점.
"""

from __future__ import annotations

from engine.geo import haversine
from engine.models import CATEGORY_ROAD, RuleResult, SiteFeatures

MAX_SCORE = 5.0
CODE, NAME = "R07", "고가철로"
THEORY = "형기론 · 충살(고가·철로)"

KIND_KO = {"rail": "철로", "overpass": "고가도로"}


def _tier(dist: float, dz: float) -> tuple[float, str]:
    if dist < 50:
        base = 0.0
    elif dist < 150:
        base = 0.4
    elif dist < 300:
        base = 0.7
    else:
        return 1.0, "무해"
    # 높이차가 크면(≥8m) 한 단계 더 감점
    if abs(dz) >= 8:
        base = max(0.0, base - 0.2)
    word = {0.0: "강한 충살", 0.2: "강한 충살", 0.4: "중간 충살",
            0.5: "중간 충살", 0.7: "약한 충살"}.get(round(base, 1), "충살")
    return base, word


def rule_rail_overpass(f: SiteFeatures) -> RuleResult:
    if not f.rails_overpasses:
        return RuleResult(
            code=CODE, name=NAME, category=CATEGORY_ROAD,
            max_score=MAX_SCORE, score=MAX_SCORE, applicable=True,
            evidence="인접한 고가·철로가 없어 충살이 없습니다.",
            theory=THEORY, tier="무해", metrics={},
        )

    o = f.building.location.as_tuple()
    nearest = min(
        f.rails_overpasses, key=lambda r: haversine(o, r.nearest.as_tuple())
    )
    dist = haversine(o, nearest.nearest.as_tuple())
    ratio, word = _tier(dist, nearest.height_diff_m)
    kind = KIND_KO.get(nearest.kind, nearest.kind)

    if ratio >= 1.0:
        evidence = f"가장 가까운 {kind}가 {round(dist)}m로 충분히 떨어져 무해합니다."
    else:
        evidence = (
            f"{kind}가 {round(dist)}m·높이차 {round(nearest.height_diff_m)}m로 인접 "
            f"— 기류·소음이 터를 흔드는 형국입니다."
        )
    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_ROAD,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier=word,
        metrics={"kind": nearest.kind, "dist_m": round(dist, 1),
                 "height_diff_m": nearest.height_diff_m},
    )
