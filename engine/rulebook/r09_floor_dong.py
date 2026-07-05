"""R09 층수·동 배치 (정밀 감정) — 배점 10. (룰북 §9)

층수 오행 해석 + (Lv.3) 단지 내 동 위치의 국세.
동·호수 미입력이면 층수만으로도 부분 판정하되, 층수조차 없으면 applicable=False.
"""

from __future__ import annotations

from engine.models import CATEGORY_BUILDING, RuleResult, SiteFeatures

MAX_SCORE = 10.0
CODE, NAME = "R09", "층수동배치"
THEORY = "이기론 · 층수 오행·국세"

# 층수 끝자리 오행 (하도수: 1·6水 2·7火 3·8木 4·9金 5·0土)
FLOOR_OHAENG = {
    1: "수", 6: "수", 2: "화", 7: "화", 3: "목", 8: "목",
    4: "금", 9: "금", 5: "토", 0: "토",
}
OHAENG_DESC = {
    "수": "재물·유통의 기운(수)",
    "화": "명예·활동의 기운(화)",
    "목": "성장·건강의 기운(목)",
    "금": "결실·재정의 기운(금)",
    "토": "안정·중심의 기운(토)",
}

DONG_DESC = {
    "center": "단지 중심에 자리해 바람을 갈무리하는 길한 국세",
    "edge": "단지 외곽이라 바람길에 노출된 국세(비보로 보완 권장)",
}


def rule_floor_dong(f: SiteFeatures) -> RuleResult:
    floors = f.building.floors
    dong_pos = f.precision.dong_position if f.precision else None

    if floors is None:
        return RuleResult(
            code=CODE, name=NAME, category=CATEGORY_BUILDING,
            max_score=MAX_SCORE, score=0.0, applicable=False,
            evidence="층수·동 정보가 없어 정밀 감정 대상에서 제외됩니다(동·호수를 입력하면 열립니다).",
            theory=THEORY, tier="미입력", metrics={},
        )

    last = floors % 10
    ohaeng = FLOOR_OHAENG[last]
    ratio = 0.6  # 층수 오행 자체는 중립 기준
    parts = [f"{floors}층은 오행상 '{ohaeng}' — {OHAENG_DESC[ohaeng]}입니다"]

    if dong_pos in DONG_DESC:
        ratio += 0.2 if dong_pos == "center" else -0.1
        parts.append(DONG_DESC[dong_pos])
    ratio = max(0.0, min(1.0, ratio))

    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_BUILDING,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=". ".join(parts) + ".",
        theory=THEORY, tier=f"{ohaeng} 층",
        metrics={"floors": floors, "ohaeng": ohaeng, "dong_position": dong_pos},
    )
