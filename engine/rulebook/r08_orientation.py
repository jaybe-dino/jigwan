"""R08 좌향 24방위 — 배점 15. (룰북 §8)

건물 배치각(facing) → 24방위 좌향 판정, 동사택/서사택 분류.
이기론 해석(궁합)의 기준값. 방위 자체 길흉은 본명궁 결합 전까지 중립.
"""

from __future__ import annotations

from engine.geo import angle_diff
from engine.models import CATEGORY_BUILDING, RuleResult, SiteFeatures

MAX_SCORE = 15.0
CODE, NAME = "R08", "좌향24방위"
THEORY = "이기론 · 24방위 좌향·동서사택"

# 24방위(15°): 중심각과 이름. 0°=정북(子)에서 시계방향.
# 임자계 축간인 갑묘을 진손사 병오정 미곤신 경유신 술건해
MOUNTAINS = [
    (0, "자"), (15, "계"), (30, "축"), (45, "간"), (60, "인"), (75, "갑"),
    (90, "묘"), (105, "을"), (120, "진"), (135, "손"), (150, "사"), (165, "병"),
    (180, "오"), (195, "정"), (210, "미"), (225, "곤"), (240, "신"), (255, "경"),
    (270, "유"), (285, "신"), (300, "술"), (315, "건"), (330, "해"), (345, "임"),
]

# 팔괘 → 사택 계열. 동사택: 감·리·진·손 / 서사택: 건·곤·간·태
# 향(facing)이 속한 45° 팔괘궁으로 사택을 분류한다.
BAGUA = [
    (0, "감", "동사택"), (45, "간", "서사택"), (90, "진", "동사택"),
    (135, "손", "동사택"), (180, "리", "동사택"), (225, "곤", "서사택"),
    (270, "태", "서사택"), (315, "건", "서사택"),
]

# 정향(사정·사우) — 근접하면 격이 높다고 봄
CARDINAL = [0, 90, 180, 270, 45, 135, 225, 315]


def _mountain(deg: float) -> str:
    return min(MOUNTAINS, key=lambda m: angle_diff(deg, m[0]))[1]


def _bagua(deg: float) -> tuple[str, str]:
    g, name, sect = min(BAGUA, key=lambda b: angle_diff(deg, b[0]))
    return name, sect


def _boundary_penalty(deg: float) -> float:
    """24방위 경계(7.5° + 15k)에 ±3° 이내면 애매한 향 → 감점."""
    for k in range(24):
        edge = (7.5 + 15 * k) % 360
        if angle_diff(deg, edge) <= 3.0:
            return 0.1
    return 0.0


def rule_orientation(f: SiteFeatures) -> RuleResult:
    facing = f.building.facing_deg % 360.0
    sitting = (facing + 180.0) % 360.0
    hyang_mtn = _mountain(facing)  # 향
    jwa_mtn = _mountain(sitting)   # 좌
    _bagua_name, sect = _bagua(facing)

    ratio = 0.75
    # 사정·사우 정향 근접도 보정
    nearest_card = min(CARDINAL, key=lambda c: angle_diff(facing, c))
    off = angle_diff(facing, nearest_card)
    ratio += 0.15 * max(0.0, 1.0 - off / 15.0)
    ratio -= _boundary_penalty(facing)
    ratio = max(0.0, min(1.0, ratio))

    evidence = (
        f"건물은 {jwa_mtn}좌 {hyang_mtn}향({round(facing)}°) "
        f"— {sect}에 속하는 배치입니다."
    )
    return RuleResult(
        code=CODE, name=NAME, category=CATEGORY_BUILDING,
        max_score=MAX_SCORE, score=MAX_SCORE * ratio, applicable=True,
        evidence=evidence, theory=THEORY, tier=sect,
        metrics={
            "facing_deg": round(facing, 1),
            "jwa": jwa_mtn, "hyang": hyang_mtn,
            "sect": sect, "off_cardinal_deg": round(off, 1),
        },
    )
