"""R10 주변 POI 길흉 — 배점 15. (룰북 §10)

반경별 혐오시설 감점 / 길 요소 가점. tanh 정규화.
"""

from __future__ import annotations

import math

from engine.geo import clamp, haversine
from engine.models import CATEGORY_ENVIRONMENT, RuleResult, SiteFeatures

MAX_SCORE = 15.0
CODE, NAME = "R10", "주변POI"
THEORY = "형기론+환경 · 사(砂)의 길흉"

# 카테고리: (부호, 가중, 영향반경 m, 표시명). 부호 +길 / -흉.
CATEGORY_WEIGHTS = {
    # 흉
    "funeral": (-1.0, 1.0, 300, "장례식장"),
    "power_tower": (-1.0, 0.9, 250, "송전탑"),
    "nightlife": (-1.0, 0.6, 200, "유흥시설"),
    "waste": (-1.0, 0.8, 300, "쓰레기처리장"),
    "prison": (-1.0, 0.7, 400, "교정시설"),
    "gas_station": (-1.0, 0.3, 120, "주유소"),
    # 길
    "park": (+1.0, 0.7, 400, "공원"),
    "school": (+1.0, 0.6, 400, "학교"),
    "library": (+1.0, 0.5, 400, "도서관"),
    "hospital": (+1.0, 0.4, 400, "종합병원"),
    "water": (+1.0, 0.6, 500, "물(강·호수)"),
    "subway": (+1.0, 0.5, 400, "지하철역"),
}


def rule_poi(f: SiteFeatures) -> RuleResult:
    o = f.building.location.as_tuple()
    total = 0.0
    contribs = []  # (abs_contrib, signed_contrib, dist, disp, sign)
    for poi in f.pois:
        spec = CATEGORY_WEIGHTS.get(poi.category)
        if spec is None:
            continue
        sign, weight, radius, disp = spec
        d = haversine(o, poi.point.as_tuple())
        if d > radius:
            continue
        decay = clamp(1.0 - d / radius, 0.0, 1.0)
        c = sign * weight * decay
        total += c
        contribs.append((abs(c), c, d, poi.name or disp, sign))

    ratio = 0.5 + 0.5 * math.tanh(total)

    if not contribs:
        evidence = "반경 내 뚜렷한 길흉 시설이 없어 주변 환경은 무난합니다."
        tier = "중립"
    else:
        contribs.sort(reverse=True)
        _, c, d, disp, sign = contribs[0]
        kind = "길(吉)" if sign > 0 else "흉(凶)"
        if total > 0.3:
            summary = "전반적으로 길한 환경"
        elif total < -0.3:
            summary = "전반적으로 흉한 기운(비보 권장)"
        else:
            summary = "길흉이 엇비슷한 환경"
        evidence = f"{round(d)}m {disp}이(가) {kind}으로 작용 — {summary}입니다."
        tier = summary

    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_ENVIRONMENT,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier=tier,
        metrics={"net_score": round(total, 3), "n_poi": len(contribs)},
    )
