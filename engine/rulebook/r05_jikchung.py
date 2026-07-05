"""R05 직충살(直沖煞) — 배점 8 (살 성격). (룰북 §5)

T자 머리/막다른 길이 건물 정면 ±15°로 곧게 찔러 들어오면 성립.
"""

from __future__ import annotations

from engine.geo import angle_diff, bearing, clamp, haversine
from engine.models import CATEGORY_ROAD, RoadSegment, RuleResult, SiteFeatures

MAX_SCORE = 8.0
CODE, NAME = "R05", "직충살"
THEORY = "형기론 · 도로살(直沖)"

FRONT_TOL_DEG = 15.0
MAX_RANGE_M = 120.0
WIDTH_FULL_M = 12.0


def _road_end_toward_front(loc, facing, r: RoadSegment):
    """도로의 양 끝점 중 건물 정면 방향에 있는 끝점과 그 접근각·거리.

    T자 머리(is_t_head)/막다른 길(is_dead_end)만 직충 후보로 본다.
    Returns (dist, approach_align 0~1) or None.
    """
    if not (r.is_t_head or r.is_dead_end):
        return None
    o = loc.as_tuple()
    best = None
    for end in (r.points[0], r.points[-1]):
        p = end.as_tuple()
        d = haversine(o, p)
        if d > MAX_RANGE_M:
            continue
        b = bearing(o, p)  # 건물에서 도로 끝을 보는 방위
        off = angle_diff(b, facing)
        if off > FRONT_TOL_DEG:
            continue
        align = 1.0 - off / FRONT_TOL_DEG
        if best is None or d < best[0]:
            best = (d, align)
    return best


def rule_jikchung_sal(f: SiteFeatures) -> RuleResult:
    loc, facing = f.building.location, f.building.facing_deg
    worst = None  # (strength, dist, road)
    for r in f.roads:
        hit = _road_end_toward_front(loc, facing, r)
        if hit is None:
            continue
        dist, align = hit
        wv = clamp(r.width_m / WIDTH_FULL_M, 0.0, 1.0)
        wa = clamp(1.0 - dist / MAX_RANGE_M, 0.0, 1.0)
        strength = wv * wa * align
        if worst is None or strength > worst[0]:
            worst = (strength, dist, r)

    if worst is None or worst[0] <= 0:
        return RuleResult(
            code=CODE, name=NAME, category=CATEGORY_ROAD,
            max_score=MAX_SCORE, score=MAX_SCORE, applicable=True,
            evidence="정면으로 찔러드는 도로가 없어 직충살은 없습니다.",
            theory=THEORY, tier="직충살 없음", metrics={},
        )

    strength, dist, r = worst
    ratio = 1.0 - strength
    evidence = (
        f"정면 {round(dist)}m에서 폭 {round(r.width_m)}m 도로가 곧게 찔러 들어옵니다 "
        f"— 직충살(현관 방위 비보 권장)입니다."
    )
    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_ROAD,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier="직충살",
        metrics={"dist_m": round(dist, 1), "width_m": r.width_m, "strength": round(strength, 2)},
    )
