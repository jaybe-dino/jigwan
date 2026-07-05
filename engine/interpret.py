"""종합 해석 — 요소별 판정을 묶어 일반인용 '한눈에 보는 해석'을 만든다.

사용자 요구: 점수가 아니라 해석이 핵심. 이 모듈이 리포트 맨 위에 올릴
친근한 요약(강점·아쉬운 점·등급의 뜻)을 생성한다.
"""

from __future__ import annotations

from typing import Any, Dict

# 코드 → 친근한 짧은 이름 (전문용어 대신)
FRIENDLY = {
    "R01": "뒷산의 받침", "R02": "양옆의 감쌈", "R03": "물길", "R04": "땅의 단단함",
    "R05": "정면 도로", "R06": "휜 도로", "R07": "고가·철로", "R08": "집의 방향",
    "R09": "층수 기운", "R10": "주변 환경",
}

GRADE_MEANING = {
    "천하명당": "백 곳 중 한 곳 나올까 말까 한, 손꼽히는 명당이에요.",
    "명당": "여러 조건이 두루 좋아 자랑할 만한 자리예요.",
    "길지": "크게 흠잡을 데 없이 살기 좋은, 안정된 자리예요.",
    "평지": "무난한 자리예요. 몇 가지만 보완하면 훨씬 좋아져요.",
    "비보지": "지금은 아쉬운 점이 있지만, 간단한 방법으로 충분히 좋아질 수 있는 자리예요.",
}


def _ratio(r) -> float:
    return r.score / r.max_score if r.max_score else 0.0


def _josa_eun(word: str) -> str:
    """받침 유무로 은/는 선택."""
    last = word[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "는" if (code - 0xAC00) % 28 == 0 else "은"
    return "은"


# 살(煞) 요소 — '없는 게 기본'이라 강점(highlight)으로는 세우지 않는다.
_SAL = {"R05", "R06", "R07"}


def summarize(assessment) -> Dict[str, Any]:
    results = [r for r in assessment.results if r.applicable]
    ranked = sorted(results, key=_ratio, reverse=True)
    strengths = [r for r in ranked if _ratio(r) >= 0.75 and r.code not in _SAL][:2]
    cautions = [r for r in reversed(ranked) if _ratio(r) < 0.55][:2]

    # 친근한 본문 구성 (조사 문제 피하려 '', '' 로 나열)
    parts = [GRADE_MEANING.get(assessment.grade.value, "")]
    if strengths:
        names = "', '".join(FRIENDLY.get(r.code, r.name) for r in strengths)
        parts.append(f"특히 '{names}' 쪽이 좋아요.")
    if cautions:
        c = cautions[0]
        nm = FRIENDLY.get(c.code, c.name)
        parts.append(f"다만 '{nm}'{_josa_eun(nm)} 조금 아쉬운데 — " + _tip(c))
    body = " ".join(p for p in parts if p)

    return {
        "grade_meaning": GRADE_MEANING.get(assessment.grade.value, ""),
        "body": body,
        "strengths": [{"name": FRIENDLY.get(r.code, r.name), "plain": r.plain} for r in strengths],
        "cautions": [{"name": FRIENDLY.get(r.code, r.name), "plain": r.plain} for r in cautions],
    }


def _tip(r) -> str:
    """아쉬운 요소의 plain에서 '~하면/두면 좋아요' 팁 문장만 뽑아 짧게."""
    plain = r.plain or ""
    for sep in ("니, ", "라, ", "으니, ", "예요. ", "어요. "):
        if sep in plain:
            tail = plain.split(sep, 1)[1]
            return tail if tail.endswith(("요.", "요")) else tail
    return "간단한 비보로 보완할 수 있어요."
