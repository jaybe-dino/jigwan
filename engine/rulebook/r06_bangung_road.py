"""R06 도로 반궁살(反弓煞) — 배점 7 (살 성격). (룰북 §6)

반경 100m 내 곡률 도로에서 건물이 곡선 바깥쪽 & 폭 8m 이상 = 성립.
"""

from __future__ import annotations

from engine.geo import clamp, cross_sign, haversine, menger_curvature, point_to_segment
from engine.models import CATEGORY_ROAD, RoadSegment, RuleResult, SiteFeatures

MAX_SCORE = 7.0
CODE, NAME = "R06", "반궁살"
THEORY = "형기론 · 도로살(反弓)"

RANGE_M = 100.0
WIDTH_MIN_M = 8.0
CURV_FULL = 0.01  # 1/100m 곡률에서 폭 가중 만점


def _outside_and_curv(loc, r: RoadSegment):
    """도로가 곡선이고 건물이 바깥쪽일 때 (dist, 곡률, outside) 반환, 아니면 None."""
    p = loc.as_tuple()
    # 최근접 세그먼트와 그 주변 곡률
    best = None
    for i in range(len(r.points) - 1):
        a = r.points[i].as_tuple()
        b = r.points[i + 1].as_tuple()
        d, _cpt, _t = point_to_segment(p, a, b)
        if best is None or d < best[0]:
            best = (d, i)
    dist, seg_i = best
    if dist > RANGE_M:
        return None
    # 곡률: seg_i 주변 세 정점
    if len(r.points) < 3:
        return None
    j = clamp(seg_i, 1, len(r.points) - 2)
    j = int(j)
    curv = menger_curvature(
        r.points[j - 1].as_tuple(), r.points[j].as_tuple(), r.points[j + 1].as_tuple()
    )
    if curv == 0.0:
        return None
    # 굽은 방향 부호와 건물 위치 좌우 비교 → 바깥쪽이면 반대 부호
    bend = cross_sign(
        r.points[j].as_tuple(), r.points[j - 1].as_tuple(), r.points[j + 1].as_tuple()
    )
    side = cross_sign(r.points[j - 1].as_tuple(), r.points[j].as_tuple(), p)
    outside = (bend != 0.0) and (side != bend)
    return (dist, curv, outside)


def rule_bangung_sal(f: SiteFeatures) -> RuleResult:
    worst = None
    for r in f.roads:
        if r.width_m < WIDTH_MIN_M:
            continue
        res = _outside_and_curv(f.building.location, r)
        if res is None:
            continue
        dist, curv, outside = res
        if not outside:
            continue
        wc = clamp(curv / CURV_FULL, 0.0, 1.0)
        ww = clamp((r.width_m - WIDTH_MIN_M) / (16.0 - WIDTH_MIN_M) + 0.5, 0.0, 1.0)
        wa = clamp(1.0 - dist / RANGE_M, 0.0, 1.0)
        strength = wc * ww * wa
        if worst is None or strength > worst[0]:
            worst = (strength, dist, r)

    if worst is None or worst[0] <= 0:
        return RuleResult(
            code=CODE, name=NAME, category=CATEGORY_ROAD,
            max_score=MAX_SCORE, score=MAX_SCORE, applicable=True,
            evidence="활처럼 등을 미는 곡선도로가 없어 반궁살은 없습니다.",
            theory=THEORY, tier="반궁살 없음", metrics={},
        )

    strength, dist, r = worst
    ratio = 1.0 - strength
    evidence = (
        f"{round(dist)}m 곡선도로(폭 {round(r.width_m)}m)가 활처럼 등을 밀어냅니다 "
        f"— 도로 반궁살입니다."
    )
    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_ROAD,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier="반궁살",
        metrics={"dist_m": round(dist, 1), "width_m": r.width_m, "strength": round(strength, 2)},
    )
