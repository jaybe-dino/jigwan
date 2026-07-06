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

from engine.interpret import summarize
from engine.samples import biboji_site, myeongdang_site
from engine.scoring import SiteAssessment, assess_site

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "app.template.html"
OUT = ROOT / "dist" / "index.html"

# 등급 → 인장에 새길 짧은 글자
GRADE_SEAL = {"천하명당": "최고", "명당": "명당", "길지": "좋음", "평지": "보통", "비보지": "주의"}

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


# ── 터BTI: 집을 한 유형의 '캐릭터'로 (공유용) ──────────────────────────────
TERBTI = {
    "geumgo": {"emoji": "🏦", "name": "금고집", "tag": "돈이 새지 않는 터",
               "desc": "뒤가 든든하고 재물 기운이 고여, 통장이 지켜지는 자리예요."},
    "river":  {"emoji": "🌊", "name": "강가집", "tag": "기회가 흘러드는 터",
               "desc": "물길이 감싸 재물과 기회가 자연스레 들어오는 자리예요."},
    "screen": {"emoji": "🛡️", "name": "병풍집", "tag": "든든하게 지켜주는 터",
               "desc": "뒷산이 병풍처럼 받쳐 안정감이 큰 자리예요."},
    "sun":    {"emoji": "☀️", "name": "햇살집", "tag": "볕과 이름이 드는 터",
               "desc": "좌향이 좋아 볕이 잘 들고 명예 기운이 사는 자리예요."},
    "forest": {"emoji": "🌳", "name": "숲속집", "tag": "건강이 자라는 터",
               "desc": "주변 생기·녹지가 좋아 몸과 마음이 편해지는 자리예요."},
    "harbor": {"emoji": "⛵", "name": "나루터집", "tag": "사람이 오가는 터",
               "desc": "길과 맞닿아 사람·재물의 왕래가 활발한 자리예요."},
    "beacon": {"emoji": "🗼", "name": "등대집", "tag": "이름이 빛나는 터",
               "desc": "명예·인정의 기운이 도드라지는 자리예요."},
    "fort":   {"emoji": "🏔️", "name": "요새집", "tag": "안정 최강의 터",
               "desc": "사방이 감싸 흔들림 없이 안정된 자리예요."},
    "wind":   {"emoji": "🍃", "name": "바람집", "tag": "탁 트인 개방형 터",
               "desc": "시원하게 열렸지만 기운이 흩어지기 쉬워 비보가 필요한 자리예요."},
    "gem":    {"emoji": "💎", "name": "원석집", "tag": "다듬으면 빛나는 터",
               "desc": "지금은 약하나 비보로 다스리면 살아나는 잠재력의 자리예요."},
}


def _ratio(R, code):
    r = R.get(code)
    if not r or not r.applicable or r.max_score <= 0:
        return None
    return r.score / r.max_score


def _terbti(a: SiteAssessment, R) -> dict:
    g = a.gauges
    grade = a.grade.value
    r01, r03, r05, r08 = _ratio(R, "R01"), _ratio(R, "R03"), _ratio(R, "R05"), _ratio(R, "R08")
    back = r01 is not None and r01 >= 0.6
    water = r03 is not None and r03 >= 0.6
    top = max(g, key=g.get)
    if grade == "비보지":
        code = "gem"
    elif grade == "평지" and (r01 is None or r01 < 0.4) and not water:
        code = "wind"
    elif water and top == "재물":
        code = "river"
    elif back and water:
        code = "fort"
    elif back and top == "재물":
        code = "geumgo"
    elif top == "명예" and (r08 is not None and r08 >= 0.6):
        code = "beacon"
    elif r08 is not None and r08 >= 0.7:
        code = "sun"
    elif top == "건강":
        code = "forest"
    elif r05 is not None and r05 >= 0.6:
        code = "harbor"
    elif back:
        code = "screen"
    else:
        code = "sun"
    t = dict(TERBTI[code])
    t["code"] = code
    t["stats"] = g
    return t


def _advice(a: SiteAssessment, R) -> list:
    """집의 약점·강점에 맞춘 구체적 개운 처방(비보). 실천 가능한 한 문장 액션."""
    g = a.gauges
    grade = a.grade.value
    r01, r03, r05 = _ratio(R, "R01"), _ratio(R, "R03"), _ratio(R, "R05")
    tips = []

    def add(icon, title, action, why):
        tips.append({"icon": icon, "title": title, "action": action, "why": why})

    if r03 is None or r03 < 0.5:
        add("🪴", "창가에 나무를 두세요",
            "창가에 키 큰 화분이나 물꽂이(수경) 식물을 두기.",
            "가까이 물길이 약할 때, 창가의 물·초록이 부족한 재물 기운을 대신 불러옵니다.")
    if r01 is not None and r01 < 0.5:
        add("🛏️", "등 뒤를 든든하게",
            "침대·책상 머리를 벽에 딱 붙이고, 등 뒤가 창이면 블라인드·높은 가구로 막기.",
            "뒤가 허하면 불안·소모가 커요. 등을 받치면 안정과 집중이 살아납니다.")
    if r05 is not None and r05 < 0.5:
        add("🌿", "현관 기운을 부드럽게",
            "현관 안쪽에 화분이나 가림막(파티션)을 두기.",
            "곧게 들이치는 도로 기운을 초록이 흩어 부드럽게 바꿉니다.")
    if g.get("재물", 50) < 58:
        add("💡", "재물 자리를 밝히세요",
            "집의 남동쪽 모서리에 밝은 조명 + 잎 넓은 초록 식물 두기.",
            "남동은 재물이 자라는 방위 — 빛과 생기가 돈 기운을 키웁니다.")
    if g.get("건강", 50) < 58:
        add("🌅", "아침 기운을 들이세요",
            "동쪽 창을 자주 열어 아침 햇빛·바람을 들이고 초록 식물 두기.",
            "동쪽의 아침 기운이 몸의 생기를 돌립니다.")
    if g.get("관계", 50) < 58:
        add("🖼️", "관계에 온기를 더하세요",
            "거실 남서쪽에 가족·연인 사진과 따뜻한 색 조명 두기.",
            "남서는 관계·화합의 방위 — 온기가 사이를 데웁니다.")
    if grade in ("천하명당", "명당", "길지"):
        add("✨", "좋은 기운을 지키세요",
            "현관을 밝고 깨끗하게, 신발은 정리해 두기.",
            "좋은 터일수록 입구가 깨끗해야 기운이 그대로 머뭅니다.")
    # 기본 개운 루틴(항상 하나)
    add("🧂", "기본 개운 루틴",
        "현관 모서리에 굵은소금 한 접시, 주 1회 전체 환기.",
        "묵은 기운을 걷어내는 가장 쉬운 비보예요.")
    return tips[:4]


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


def _extract_dong(address: str) -> str:
    for tok in address.replace(",", " ").split():
        if tok.endswith("동") and len(tok) >= 2:
            return tok
    return "이곳"


def shape_assessment(a: SiteAssessment, up: bool, share_dong: str, accuracy: int) -> dict:
    """SiteAssessment → UI 데이터 계약(dict). 프론트(웹·Next.js)의 유일한 입력."""
    d = a.to_dict()
    grade = a.grade.value
    R = {r.code: r for r in a.results}
    r08m = R["R08"].metrics if "R08" in R else {}
    return {
        # 궁합 계산에 쓰는 실제 집의 좌향·사택 (없으면 기본값)
        "facing": r08m.get("facing_deg", 180.0),
        "houseSect": r08m.get("sect", "동사택"),
        # 터BTI(집 유형) + 구체 풍수 조언(개운 처방)
        "terbti": _terbti(a, R),
        "advice": _advice(a, R),
        # 리포트에는 아주 구체적인 주소(도로명+동·호수)를 그대로 노출 — 전문 감정.
        # 공유 카드(addrShort)만 §11 낙인방지로 행정동까지 마스킹.
        "addr": a.address,
        "addrShort": f"{share_dong}의 어느 터",
        "precise": accuracy >= 75,  # 「정밀 감정」 배지
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
                "plain": r.get("plain", ""),  # 쉬운 해석 (메인 노출)
            }
            for r in d["results"]
        ],
        "interp": summarize(a),  # 종합 쉬운 해석 (강점·아쉬운 점)
        "map": _map_hints(a),
        "legend": _map_hints(a)["legend"],
        "coord": [a.coord[0], a.coord[1]],  # 지도 중심 (실좌표)
        "landmarks": a.landmarks,             # 실제 산·강 이름
        "sources": a.sources,                 # 실측 데이터 개수(투명성)
        "bibo": _bibo(a),
        "liner": LINER.get(grade, ""),
    }


def build_site(builder, up: bool, share_dong: str) -> dict:
    """샘플 빌더 → UI 데이터. 동·호수(정밀) 여부로 정확도를 정한다."""
    feats = builder()
    a = assess_site(feats)
    has_unit = feats.precision is not None and feats.precision.dong_position is not None
    return shape_assessment(a, up=up, share_dong=share_dong, accuracy=75 if has_unit else 62)


def build_from_address(address: str) -> dict:
    """임의 주소 → UI 데이터 (팩토리: 실데이터). Next.js API/engine_cli 진입점."""
    from pipeline.assemble import assess_address_auto

    a = assess_address_auto(address)
    return shape_assessment(a, up=True, share_dong=_extract_dong(address), accuracy=62)


def build_compat(facing: float, house_sect: str, year: int, month: int, day: int,
                 is_male: bool, hour=None) -> dict:
    """실제 사주(만세력) 기반 궁합 — 데모 아님."""
    from engine.rulebook.compat import compute_compat

    r = compute_compat(facing, house_sect, year, month, day, is_male, hour)
    return {
        "percent": r.percent, "caption": r.caption,
        "ohaeng_delta": r.ohaeng_delta, "sect_delta": r.sect_delta,
        "house_element": r.house_element, "yongsin": r.yongsin,
        "user_sect": r.user_sect, "house_sect": r.house_sect,
        "match_sect": r.match_sect, "pillars": r.saju_pillars, "time_known": r.time_known,
    }


COORD_CACHE = ROOT / "coord_cache.json"


def build_from_coord(lat: float, lon: float) -> dict:
    """지도에서 찍은 좌표 → UI 데이터. 전국 어디든 탭하면 그 자리 풍수.
    같은 자리(≈11m) 재조회는 파일 캐시로 즉시 반환(속도·부하 절감)."""
    from pipeline.assemble import assess_coord_auto

    key = f"{lat:.4f},{lon:.4f}"

    def _read_cache():
        try:
            return json.loads(COORD_CACHE.read_text(encoding="utf-8")) if COORD_CACHE.exists() else {}
        except Exception:
            return {}

    cache = _read_cache()
    if key in cache:
        return cache[key]

    a = assess_coord_auto(lat, lon)
    d = shape_assessment(a, up=True, share_dong="이 자리", accuracy=55)
    try:
        cache = _read_cache()
        cache[key] = d
        COORD_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return d


# 전국 명당(名堂) — 예로부터 풍수 좋기로 이름난 실제 터. 빌드 시 실제 지형으로 실측해 랭킹을 미리 축적.
HOTSPOTS = [
    {"name": "평창동", "sub": "서울 종로", "why": "북한산 배산임수", "lat": 37.6119, "lon": 126.9740},
    {"name": "성북동", "sub": "서울 성북", "why": "북악·응봉 감쌈", "lat": 37.5957, "lon": 126.9985},
    {"name": "부암동", "sub": "서울 종로", "why": "인왕산 자락", "lat": 37.5926, "lon": 126.9660},
    {"name": "한남동", "sub": "서울 용산", "why": "남산 남향·한강", "lat": 37.5340, "lon": 127.0000},
    {"name": "남연군 묘", "sub": "예산 덕산", "why": "가야산 대명당", "lat": 36.6689, "lon": 126.8430},
    {"name": "하회마을", "sub": "안동", "why": "낙동강 물돌이", "lat": 36.5390, "lon": 128.5180},
    {"name": "양동마을", "sub": "경주", "why": "설창산 물(勿)자형", "lat": 35.9987, "lon": 129.2559},
    {"name": "닭실마을", "sub": "봉화", "why": "금계포란형", "lat": 36.9430, "lon": 128.7360},
    {"name": "회룡포", "sub": "예천", "why": "내성천 물돌이", "lat": 36.5860, "lon": 128.2760},
    {"name": "선교장", "sub": "강릉", "why": "시루봉 배산", "lat": 37.7870, "lon": 128.8840},
    {"name": "외암마을", "sub": "아산", "why": "설화산 배산임수", "lat": 36.7360, "lon": 126.9160},
    {"name": "한옥마을", "sub": "전주", "why": "승암산·전주천", "lat": 35.8150, "lon": 127.1530},
]

# 실측 결과 캐시 — 한 번 계산하면 재빌드 시 재사용(무료 API 부하·빌드시간 절감)
RANK_CACHE = ROOT / "hotspots_cache.json"


def build_ranking() -> list:
    """전국 명당을 실제 지형(산·강·도로)으로 실측 → 점수순 랭킹을 '미리' 만든다.
    빌드 시 1회 계산해 캐시. 개별 실패는 건너뛰고 부분 결과라도 반환(빌드는 절대 실패 안 함)."""
    import os

    if os.environ.get("JIGWAN_SKIP_RANKING"):
        return []

    cache: Dict[str, Any] = {}
    if RANK_CACHE.exists():
        try:
            cache = json.loads(RANK_CACHE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    import time

    from pipeline.assemble import assess_coord_auto

    budget_s = float(os.environ.get("JIGWAN_RANK_BUDGET", "360"))  # 빌드 시 최대 소요(초)
    t0 = time.time()

    out = []
    for h in HOTSPOTS:
        key = f"{h['lat']:.4f},{h['lon']:.4f}"
        d = cache.get(key)
        if d is None:
            if time.time() - t0 > budget_s:
                print("  · 시간 예산 초과 — 나머지 명당 실측 생략(다음 빌드에서 이어감)")
                break
            try:
                a = assess_coord_auto(h["lat"], h["lon"])
                d = shape_assessment(a, up=True, share_dong=h["name"], accuracy=58)
                cache[key] = d
                print(f"  ✓ 명당 실측 {h['name']}: {d['site_score']}점")
            except Exception as e:  # 네트워크·데이터 실패 → 건너뜀
                print(f"  · 명당 실측 건너뜀 {h['name']}: {e}")
                continue
        d = dict(d)
        d["rankName"], d["rankSub"], d["why"] = h["name"], h["sub"], h.get("why", "")
        out.append(d)

    try:
        RANK_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    out.sort(key=lambda x: x.get("site_score", 0), reverse=True)
    return out


def build_data() -> dict:
    data = {
        "myeongdang": build_site(myeongdang_site, up=True, share_dong="성산동"),
        "biboji": build_site(biboji_site, up=False, share_dong="전농동"),
        "hotspots": HOTSPOTS,
    }
    try:
        data["ranking"] = build_ranking()
    except Exception as e:
        print("랭킹 빌드 실패:", e)
        data["ranking"] = []
    return data


def render() -> Path:
    import os

    naver_key = os.environ.get("NAVER_MAP_CLIENT_ID") or "f3uixmqkl0"
    data = build_data()
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__NAVER_KEY__", naver_key)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = render()
    print(f"✓ 생성 완료: {p}  ({p.stat().st_size:,} bytes)")
