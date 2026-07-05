"""엔진 데모 — 샘플 터를 감정하고 근거 문장을 출력한다.

    python3 -m engine.demo
"""

from __future__ import annotations

import json

from engine.samples import biboji_site, myeongdang_site
from engine.scoring import SiteAssessment, assess_site


def _print(a: SiteAssessment) -> None:
    print("=" * 64)
    print(f"📍 {a.address}")
    print(f"   터 점수 {a.site_score}점  ·  등급 「{a.grade.value}」")
    g = a.gauges
    print(f"   재물 {g['재물']} · 건강 {g['건강']} · 관계 {g['관계']} · 명예 {g['명예']}")
    if a.needs_bibo:
        print("   ⚠ 비보지 — 반드시 비보 처방과 함께 표시 (낙인 방지)")
    print("-" * 64)
    for r in a.results:
        flag = " " if r.applicable else "×"
        print(f" [{r.code}]{flag}{r.name:<8} {r.score:5.1f}/{r.max_score:<4.0f} {r.evidence}")
    print()


def main() -> None:
    for builder in (myeongdang_site, biboji_site):
        a = assess_site(builder())
        _print(a)

    # 마지막 하나는 구조화 JSON(=LLM 입력)으로도 출력
    a = assess_site(myeongdang_site())
    print("── 구조화 JSON (LLM 리포트 생성용 입력) ──")
    print(json.dumps(a.to_dict(), ensure_ascii=False, indent=2)[:900] + " ...")


if __name__ == "__main__":
    main()
