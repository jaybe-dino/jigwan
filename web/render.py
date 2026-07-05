"""터 리포트 UI 생성기 — 엔진 출력을 web/app.template.html 에 주입해 완성 HTML 생성.

    python3 -m web.render            # web/dist/index.html 생성

M1 엔진(engine.scoring)의 실제 판정 결과로 UI를 구동한다. 카카오맵 대신
지형 오버레이를 자체 Canvas로 그리므로 외부 의존성 없이 그대로 열린다.
실 서비스(M2)에서는 이 데이터 계약을 Next.js가 그대로 소비한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from engine.samples import biboji_site, myeongdang_site
from engine.scoring import SiteAssessment, assess_site

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "app.template.html"
OUT = ROOT / "dist" / "index.html"

# 등급 → 인장에 새길 짧은 글자
GRADE_SEAL = {"천하명당": "天下", "명당": "明堂", "길지": "吉", "평지": "平", "비보지": "裨補"}

# 등급별 한 줄 평 (공유 카드용)
LINER = {
    "천하명당": "백에 하나 나올까 말까 한 천하의 명당입니다.",
    "명당": "귀한 기운이 모이는 명당 — 자랑해도 좋습니다.",
    "길지": "기운이 안정된 길한 터. 살 만한 자리입니다.",
    "평지": "무난한 터 — 비보로 부족한 기운을 채워보세요.",
    "비보지": "지금은 약하나, 다스리면 살아나는 터입니다.",
}


def _rule(results, code) -> Optional[dict]:
    return next((r for r in results if r["code"] == code), None)


def _map_hints(a: SiteAssessment) -> Dict[str, Any]:
    """리포트 오버레이 캔버스가 그릴 지형 힌트."""
    R = {r.code: r for r in a.results}
    facing = R["R08"].metrics.get("facing_deg", 180.0)
    jwa = R["R08"].metrics.get("jwa", "")
    hyang = R["R08"].metrics.get("hyang", "")

    r01 = R["R01"].metrics
    ridge = {"bearing": r01.get("bearing_deg")} if r01.get("max_gain_m", 0) > 0 else None

    r02 = R["R02"].metrics
    dragon = (r02.get("left_gain_m", 0) > 0) or (r02.get("right_gain_m", 0) > 0)

    r03 = R["R03"].metrics
    water = {"embrace": r03.get("embrace_sign", 0)} if "embrace_sign" in r03 else None

    r05 = R["R05"].metrics
    road_sal = {"bearing": facing} if r05.get("dist_m") is not None else None

    legend_bits = []
    if ridge:
        legend_bits.append("현무 음영")
    if water:
        legend_bits.append("환포수" if water["embrace"] >= 0 else "반궁수")
    if road_sal:
        legend_bits.append("도로살")
    legend_bits.append("좌향 나침반")

    return {
        "facing": facing,
        "facingLabel": f"{jwa}좌{hyang}향",
        "ridge": ridge,
        "dragon": dragon,
        "water": water,
        "roadSal": road_sal,
        "legend": " · ".join(legend_bits),
    }


def _bibo(a: SiteAssessment) -> Optional[dict]:
    """비보 카드 — 비보지이거나 뚜렷한 살이 있을 때."""
    R = {r.code: r for r in a.results}
    if R["R05"].metrics.get("dist_m") is not None:  # 직충살
        return {
            "title": "현관 왼쪽에 붉은 소품을 두세요",
            "body": "정면으로 찔러드는 도로살이 재물 기운을 치고 들어옵니다. "
            "붉은 기운이 그 예기(銳氣)를 눌러 흩어줍니다.",
            "action": "현관 좌측 붉은 화병·매트 배치",
        }
    if a.grade.value == "비보지":
        return {
            "title": "빛과 화분으로 지기를 북돋우세요",
            "body": "약한 터일수록 밝은 빛과 생기 있는 화초가 땅의 기운을 끌어올립니다.",
            "action": "거실 남동쪽에 키 큰 화분 + 조명",
        }
    return None


def _price(seed: int, up: bool) -> dict:
    """데모용 실거래가 시계열(국토부 병기 자리)."""
    base = 9 + seed % 5
    series = []
    v = base
    for i in range(24):
        v += ((seed * (i + 3)) % 7 - 3) * 0.15 + (0.06 if up else -0.05)
        series.append(round(max(6.0, v), 2))
    now = series[-1]
    chg_pct = (series[-1] - series[0]) / series[0] * 100
    return {
        "now": f"{now:.1f}억",
        "chg": f"{'▲' if chg_pct>=0 else '▼'} {abs(chg_pct):.1f}% (24개월)",
        "dir": "up" if chg_pct >= 0 else "down",
        "series": series,
    }


def build_site(builder, up: bool, share_dong: str) -> dict:
    feats = builder()
    a = assess_site(feats)
    d = a.to_dict()
    grade = a.grade.value

    # 정확도: 주소만 62% → 동·호수(정밀) 75% → 집 내부 3문항 90% (기획안 §3)
    has_unit = feats.precision is not None and feats.precision.dong_position is not None
    accuracy = 75 if has_unit else 62

    return {
        # 리포트에는 아주 구체적인 주소(도로명+동·호수)를 그대로 노출 — 전문 감정.
        # 공유 카드(addrShort)만 §11 낙인방지로 행정동까지 마스킹.
        "addr": a.address,
        "addrShort": f"{share_dong}의 어느 터",
        "precise": has_unit,  # 「정밀 감정」 배지
        "site_score": a.site_score,
        "grade": grade,
        "gradeSeal": GRADE_SEAL.get(grade, grade[0]),
        "accuracy": accuracy,
        "gauges": d["gauges"],
        "results": [
            {
                "code": r["code"], "name": r["name"], "category": r["category"],
                "score": r["score"], "max_score": r["max_score"],
                "applicable": r["applicable"], "evidence": r["evidence"],
                "theory": r["theory"], "tier": r["tier"],
            }
            for r in d["results"]
        ],
        "map": _map_hints(a),
        "legend": _map_hints(a)["legend"],
        "price": _price(seed=a.site_score, up=up),
        "bibo": _bibo(a),
        "liner": LINER.get(grade, ""),
    }


def build_data() -> dict:
    return {
        "myeongdang": build_site(myeongdang_site, up=True, share_dong="성산동"),
        "biboji": build_site(biboji_site, up=False, share_dong="전농동"),
    }


def render() -> Path:
    data = build_data()
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = render()
    print(f"✓ 생성 완료: {p}  ({p.stat().st_size:,} bytes)")
