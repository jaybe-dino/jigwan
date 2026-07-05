"""R03 환포수/반궁수 — 배점 10. (룰북 §3)

가장 가까운 하천의 곡류에 대해 건물이 안쪽(환포·길)인지 바깥쪽(반궁·흉)인지.
"""

from __future__ import annotations

from typing import Optional, Tuple

from engine.geo import clamp, inside_of_arc, point_to_segment
from engine.models import CATEGORY_HYEONGGI, LatLon, RuleResult, SiteFeatures, StreamSegment

MAX_SCORE = 10.0
CODE, NAME = "R03", "환포반궁수"
THEORY = "형기론 · 득수(得水)"

MAX_INFLUENCE_M = 500.0


def _nearest_on_stream(
    loc: LatLon, s: StreamSegment
) -> Tuple[float, LatLon, int, LatLon]:
    """하천 폴리라인에서 최근접 수선거리·최근접점·세그먼트 시작정점 인덱스."""
    p = loc.as_tuple()
    best = (float("inf"), None, 0, None)
    for i in range(len(s.points) - 1):
        a = s.points[i].as_tuple()
        b = s.points[i + 1].as_tuple()
        d, cpt, _t = point_to_segment(p, a, b)
        if d < best[0]:
            best = (d, cpt, i, (a, b))
    d, cpt, i, ab = best
    return d, LatLon(cpt[0], cpt[1]), i, ab


def _embrace_sign(loc: LatLon, s: StreamSegment, seg_i: int) -> float:
    """건물이 곡류 안쪽(+1 환포)인지 바깥쪽(-1 반궁)인지, 직선이면 0.

    최근접 세그먼트를 감싸는 하천 정점 3개로 호(弧)를 잡고, 건물이 그 호의
    오목한 안쪽에 있으면 환포(+1)다. (외접원 곡률 중심 기준)
    """
    pts = s.points
    n = len(pts)
    if n < 3:
        return 0.0
    # 최근접 세그먼트(seg_i, seg_i+1)를 브래킷하는 세 정점
    j = min(max(seg_i, 1), n - 2)
    a = pts[j - 1].as_tuple()
    b = pts[j].as_tuple()
    c = pts[j + 1].as_tuple()
    inside = inside_of_arc(loc.as_tuple(), a, b, c)
    if inside is None:
        return 0.0
    return 1.0 if inside else -1.0


def rule_hwanpo_bangung(f: SiteFeatures) -> RuleResult:
    loc = f.building.location
    if not f.streams:
        return RuleResult(
            code=CODE, name=NAME, category=CATEGORY_HYEONGGI,
            max_score=MAX_SCORE, score=MAX_SCORE * 0.5, applicable=True,
            evidence="가까운 수계가 없어 물의 길흉은 중립입니다.",
            theory=THEORY, tier="수계 없음", metrics={},
        )

    # 가장 가까운 하천 선택
    best: Optional[Tuple[float, StreamSegment, int]] = None
    for s in f.streams:
        d, _cpt, seg_i, _ab = _nearest_on_stream(loc, s)
        if best is None or d < best[0]:
            best = (d, s, seg_i)
    dist, stream, seg_i = best

    sign = _embrace_sign(loc, stream, seg_i)
    w = clamp(1.0 - dist / MAX_INFLUENCE_M, 0.0, 1.0)
    ratio = clamp(0.5 + sign * 0.5 * w, 0.0, 1.0)
    name = stream.name or "물길"

    if sign > 0:
        evidence = f"{round(dist)}m 앞 {name}이(가) 이 터를 감싸 안습니다 — 재물이 모이는 환포수입니다."
        tier = "환포수(길)"
    elif sign < 0:
        evidence = f"{round(dist)}m {name}이(가) 등을 돌린 반궁수 — 기운이 새는 형국(비보 대상)입니다."
        tier = "반궁수(흉)"
    else:
        evidence = f"{round(dist)}m {name}이(가) 곧게 흘러 길흉은 중립입니다."
        tier = "직류(중립)"

    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_HYEONGGI,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier=tier,
        metrics={"dist_m": round(dist, 1), "embrace_sign": sign, "weight": round(w, 2)},
    )
