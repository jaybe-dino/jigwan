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
VIRAL_TEMPLATE = ROOT / "viral.template.html"
VIRAL_OUT = ROOT / "dist" / "v.html"

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


def _compass(deg) -> str:
    if deg is None:
        return ""
    names = ["북", "북동", "동", "남동", "남", "남서", "서", "북서"]
    return names[int(((deg % 360) + 22.5) // 45) % 8]


_SAN_HANJA = {"자": "子", "계": "癸", "축": "丑", "간": "艮", "인": "寅", "갑": "甲",
              "묘": "卯", "을": "乙", "진": "辰", "손": "巽", "사": "巳", "병": "丙",
              "오": "午", "정": "丁", "미": "未", "곤": "坤", "신": "申", "경": "庚",
              "유": "酉", "술": "戌", "건": "乾", "해": "亥", "임": "壬"}


def _hanja(k) -> str:
    return f"{k}({_SAN_HANJA[k]})" if k in _SAN_HANJA else (k or "")


def _region(addr: str) -> str:
    """주소에서 시·구·동을 뽑아 지역명으로. (예: '종로구 평창동')"""
    toks = (addr or "").replace(",", " ").split()
    gu = next((t for t in toks if t.endswith(("구", "군")) and len(t) >= 2), "")
    if not gu:
        gu = next((t for t in toks if t.endswith("시") and len(t) >= 2), "")
    dong = next((t for t in toks if t.endswith(("동", "읍", "면", "리", "가")) and len(t) >= 2), "")
    return " ".join(x for x in [gu, dong] if x) or "이 지역"


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


# ── 다중 스케일 지형지물 지식베이스(고도화) ────────────────────────────────
# 실제 산·강 이름 → (오행, 산세/특성 해설, 개운 처방). 신빙성 있는 구체 서술.
_LORE = {
    "관악산": ("화(火)", "불꽃처럼 솟은 바위산(화체·火體)으로 기세가 매우 강합니다. 문필·시험·명예운을 크게 북돋우나 화기가 세, 조선 왕조도 경복궁 화재를 막으려 해태상과 연못으로 이 산의 화기를 눌렀을 정도입니다.", "창가에 물그릇·수경식물을 두고 붉은 조명을 피해 화기를 물로 다스리세요."),
    "삼성산": ("화(火)", "관악산 자락의 바위 명산으로 세 성인의 전설이 깃든 문필의 산입니다. 학업·수행의 기운이 서립니다.", "책상을 이 산 방향으로 두면 집중과 성취에 좋습니다."),
    "장군봉": ("금(金)", "우뚝한 근봉으로 무(武)·결단·추진의 기운을 줍니다. 뾰족하고 굳센 봉우리는 강한 리더십을 상징합니다.", "결단이 필요할 때 이 봉우리가 보이는 창가에서 계획을 세우세요."),
    "북한산": ("금(金)", "서울의 조종산(祖宗山)인 바위 명산(삼각산). 우뚝한 석산은 귀(貴)와 기상을 세워 큰 인물을 배출하는 기운입니다.", "높고 귀한 산 기운을 등지면 자존과 명예가 섭니다."),
    "북악산": ("목(木)", "경복궁의 주산(백악). 단정하게 솟아 반듯한 귀인·관운의 기운을 세웁니다.", "등 뒤로 두면 신뢰와 지위가 안정됩니다."),
    "인왕산": ("금(金)", "바위 기운이 웅장한 서울의 우백호. 재물과 예술·기예의 기운이 함께 서립니다.", "오른쪽에 두면 실리와 재능이 살아납니다."),
    "남산": ("목(木)", "서울 도심의 안산(案山)이자 목멱산. 단정한 앞산은 명예와 조망을 열어줍니다.", "앞으로 두면 손님과 기회가 모입니다."),
    "아차산": ("목(木)", "한강을 굽어보는 완만한 육산으로 온화한 생기를 품습니다.", "부드러운 산 기운은 건강과 화합에 좋습니다."),
    "대모산": ("토(土)", "강남의 완만한 흙산으로 넉넉한 재물·안정의 토(土) 기운을 줍니다.", "안정과 저축의 기운 — 재물 자리를 밝게 두세요."),
    "우면산": ("토(土)", "서초를 받치는 육산으로 두터운 안정감을 줍니다.", "든든한 배경 — 등 뒤를 비우지 마세요."),
    "청계산": ("목(木)", "울창한 육산으로 맑고 곧은 생기를 품은 명산입니다.", "맑은 산 기운 — 건강과 정직의 자리."),
    "한라산": ("토(火)", "제주를 이룬 거대한 화산으로 웅혼한 지기의 원천입니다.", "큰 산의 기운 — 큰 뜻을 품기 좋습니다."),
    "지리산": ("토(土)", "백두대간 남단의 어머니 산으로 두텁고 넉넉한 기운을 품습니다.", "넓은 품의 산 — 안정과 포용의 자리."),
    "무등산": ("토(土)", "광주를 감싸는 넉넉한 육산으로 평온한 기운을 줍니다.", "온화한 기운 — 관계와 건강에 좋습니다."),
    "팔공산": ("금(金)", "대구의 진산으로 웅장한 바위 기운이 귀함을 세웁니다.", "귀한 산을 등지면 명예가 섭니다."),
    "금정산": ("금(金)", "부산의 진산으로 바위 기세가 강건합니다.", "굳센 산 기운 — 추진과 결단의 자리."),
    "계룡산": ("목(火)", "예로부터 신령한 기운으로 이름난 바위 명산입니다.", "영기가 강한 산 — 수행·집중에 좋습니다."),
    # 강·하천
    "한강": ("수(水)", "서울을 크게 감싸 흐르는 외수(客水)이자 큰 명당수. 큰물이 멀리서 감싸면 대재물·교류·물류의 큰 기운이 모입니다.", "큰 물이 앞을 두르면 재물의 그릇이 커집니다."),
    "도림천": ("수(水)", "관악·삼성산에서 발원해 안양천을 거쳐 한강으로 드는 내수(內水). 집 앞을 감싸 흐르면(환포) 재물이 고입니다.", "앞을 흐르는 개천이 감싸면 알뜰히 모이는 재물운."),
    "안양천": ("수(水)", "서남부를 흐르는 지류로 재물의 통로가 됩니다.", "물길을 등지지 말고 마주 보게 두세요."),
    "중랑천": ("수(水)", "동북부를 흐르는 큰 지류로 재물·교류의 기운입니다.", "감싸 흐르는 쪽이 길합니다."),
    "청계천": ("수(水)", "도심을 흐르는 물길로 재물과 소통의 기운을 되살린 하천입니다.", "물가 가까이는 활기와 재물이 돕니다."),
    "탄천": ("수(水)", "분당·강남을 흐르는 지류로 재물의 흐름을 만듭니다.", "물을 마주 보는 향이 좋습니다."),
    "양재천": ("수(水)", "강남을 완만히 감싸 흐르는 물길로 알뜰한 재물운입니다.", "감싸 흐르는 안쪽이 명당입니다."),
    "낙동강": ("수(水)", "영남을 관통하는 큰 강으로 큰 재물·물류의 기운입니다.", "큰 물이 감싸면 그릇이 커집니다."),
    "금강": ("수(水)", "충청을 감아 도는 큰 강으로 넉넉한 재물수입니다.", "물을 앞에 두면 재물이 모입니다."),
    "영산강": ("수(水)", "호남을 흐르는 큰 강으로 풍요의 물길입니다.", "감싸 흐르는 쪽에 터가 길합니다."),
    "섬진강": ("수(水)", "맑기로 이름난 큰 강으로 청정한 재물·건강 기운입니다.", "맑은 물가 — 건강과 재물의 자리."),
}

# 오행 → 아이콘(불꽃·바위·흙 등 형상 반영)
_OHAENG_ICON = {"화": "🔥", "금": "⛰️", "목": "🌲", "토": "🏔️", "수": "💧"}
# 스케일·종류별 지도/카드 아이콘
_KIND_ICON = {"josan": "🏔️", "peak": "⛰️", "sasin_back": "⛰️", "sasin_left": "🐉",
              "sasin_right": "🐯", "sasin_front": "🏞️", "river": "🌊", "stream": "💧"}
# 사신사 역할 라벨
_SASIN = {"back": ("현무·주산(뒷산)", "🐢"), "left": ("청룡·좌산", "🐉"),
          "right": ("백호·우산", "🐯"), "front": ("주작·안산(앞산)", "🏞️")}

# 지역(구/동/시) → 큰 물(대수·객수). 창수·객수는 멀어도 국세를 좌우한다.
_MACRO_RIVER = {
    "관악": "한강", "동작": "한강", "영등포": "한강", "구로": "한강", "금천": "안양천",
    "마포": "한강", "용산": "한강", "성동": "한강", "광진": "한강", "강동": "한강",
    "송파": "한강", "강남": "한강", "서초": "양재천", "양천": "안양천", "강서": "한강",
    "은평": "한강", "서대문": "홍제천", "종로": "청계천", "중구": "청계천", "성북": "정릉천",
    "강북": "우이천", "도봉": "중랑천", "노원": "중랑천", "중랑": "중랑천", "동대문": "중랑천",
    "성남": "탄천", "분당": "탄천", "대구": "낙동강", "부산": "낙동강", "대전": "금강",
    "광주": "영산강", "제주": "한라산",
}
# 서울 권역 → 조산(祖山·큰 산). OSM에 큰 산이 안 잡혀도 국세를 세운다.
_MACRO_JOSAN = {
    "관악": "관악산", "동작": "관악산", "금천": "관악산", "구로": "관악산",
    "서초": "우면산", "강남": "대모산", "송파": "남한산", "강동": "아차산", "광진": "아차산",
    "종로": "북한산", "성북": "북한산", "강북": "북한산", "도봉": "도봉산", "노원": "수락산",
    "은평": "북한산", "서대문": "안산", "마포": "와우산", "용산": "남산", "중구": "남산",
    "성남": "청계산", "분당": "청계산",
}


def _match_lore(name: str):
    if not name:
        return None
    for key, val in _LORE.items():
        if key in name:
            return val
    return None


def _sector_of(facing, brg):
    """향(facing) 기준 방위 → 사신사 구역(back/left/right/front)."""
    from engine.geo import angle_diff
    for key, cdeg in (("back", (facing + 180) % 360), ("front", facing % 360),
                      ("left", (facing + 90) % 360), ("right", (facing - 90) % 360)):
        if angle_diff(brg, cdeg) <= 45:
            return key
    return "front"


def _scale_of(kind, dist):
    """거리·종류로 풍수 스케일 판정. 대(큰 국세)/중(사신사)/소(가까운 봉·개천)."""
    if kind in ("river",):
        return "대"
    if kind == "josan":
        return "대"
    if dist is None:
        return "중"
    if kind == "stream":
        return "소" if dist <= 900 else "중"
    # 산봉우리
    if dist <= 800:
        return "소"
    if dist <= 2500:
        return "중"
    return "대"


def _terrain(a: SiteAssessment, R, lm: dict) -> dict:
    """다중 스케일 지형지물 해설 — 큰 산줄기·큰 물(대) / 주산·사신사(중) / 가까운 봉·개천(소).

    실제 이름과 오행·산세·거리·방위를 결합해 '단순 뒷산'이 아니라 '뒤에 어떤 산'을 설명한다.
    반환: {"items": [...], "note": 국세 한 줄}
    """
    from engine.geo import angle_diff
    r01 = R["R01"].metrics if "R01" in R else {}
    r03 = R["R03"].metrics if "R03" in R else {}
    facing = (R["R08"].metrics.get("facing_deg", 180.0) if "R08" in R else 180.0)
    region = _region(a.address)
    items = []
    seen = set()

    def emit(name, kind, role, dist, ele, brg, good, note_bits, lat=None, lon=None):
        if not name or name in seen:
            return
        seen.add(name)
        lore = _match_lore(name)
        oh = lore[0] if lore else None
        if kind == "river":
            icon = "🌊"
        elif kind == "stream":
            icon = "💧"
        else:  # 산 — 오행 형상 아이콘(화=🔥·금=⛰️·목=🌲·토=🏔️) 우선
            icon = (_OHAENG_ICON.get(oh[0]) if oh else None) or _KIND_ICON.get(kind, "⛰️")
        mean = (lore[1] if lore else _role_mean(kind, role))
        tip = lore[2] if lore else ""
        detail = " · ".join([b for b in note_bits if b])
        items.append({
            "name": name, "kind": kind, "role": role, "scale": _scale_of(kind, dist),
            "icon": icon, "ohaeng": oh, "dist": dist, "ele": ele,
            "dir": _compass(brg) if brg is not None else "",
            "mean": mean, "tip": tip, "detail": detail, "good": good,
            "lat": lat, "lon": lon,
        })

    # 1) 실측 사신사(landmarks) — 역할·수치 결합 (중 스케일 기본)
    if lm.get("back"):
        d = int(r01["dist_m"]) if r01.get("dist_m") else None
        g = int(r01.get("max_gain_m", 0) or 0)
        emit(lm["back"], "sasin_back", "현무·주산(뒷산)", d, None,
             r01.get("bearing_deg"), (r01.get("max_gain_m", 0) or 0) > 0,
             [f"{_compass(r01.get('bearing_deg'))}쪽 {d}m" if d else "", f"표고 +{g}m" if g else ""])
    for key in ("left", "right", "front"):
        if lm.get(key):
            role, _ic = _SASIN[key]
            emit(lm[key], "sasin_" + key, role, None, None, None, True, [])
    # 물(내수)
    if lm.get("water"):
        emb = r03.get("embrace_sign", 0)
        d = int(r03["dist_m"]) if r03.get("dist_m") is not None else None
        emit(lm["water"], "stream", "득수·물길", d, None, None, emb >= 0,
             [f"{d}m" if d else "", ("환포(감싸 흐름·길)" if emb >= 0 else "반궁(등지고 흐름·흉)")])

    # 2) OSM 실측 지형지물(a.terrain) — 근봉(장군봉 등)·먼 조산까지 스케일별로
    for t in (a.terrain or []):
        nm = t.get("name")
        if not nm or nm in seen:
            continue
        kind = "river" if t.get("kind") == "river" else (
            "stream" if t.get("kind") in ("water", "stream") else "peak")
        dist = t.get("dist")
        brg = t.get("bearing")
        sec = _sector_of(facing, brg) if brg is not None else "front"
        role = {"back": "현무 방향 봉우리", "left": "청룡 방향 봉우리",
                "right": "백호 방향 봉우리", "front": "안산 방향 봉우리"}.get(sec, "주변 봉우리")
        if kind in ("stream", "river"):
            role = "득수·물길"
        ele = t.get("ele")
        emit(nm, kind, role, dist, ele, brg, True,
             [f"{_compass(brg)}쪽 {int(dist)}m" if dist else "", f"해발 {int(ele)}m" if ele else ""],
             lat=t.get("lat"), lon=t.get("lon"))

    # 3) 큰 산줄기·큰 물(대 스케일) — OSM에 안 잡혀도 국세를 세운다
    josan = _pick_region(region, _MACRO_JOSAN)
    daesu = _pick_region(region, _MACRO_RIVER)
    if josan and josan not in seen:
        emit(josan, "josan", "조산(祖山)·큰 산줄기", None, None, None, True,
             ["이 고을을 세운 큰 산"])
    if daesu and daesu not in seen:
        kind = "river" if daesu in ("한강", "낙동강", "금강", "영산강", "섬진강") else "stream"
        emit(daesu, kind, "대수(大水)·큰 물", None, None, None, True, ["국세를 감싸는 큰 물"])

    note = _terrain_note(region, lm, josan, daesu, r03)
    # 대→중→소, 같은 스케일 내 거리순
    order = {"대": 0, "중": 1, "소": 2}
    items.sort(key=lambda x: (order.get(x["scale"], 3), x["dist"] if x["dist"] is not None else 9999))
    return {"items": items, "note": note}


def _role_mean(kind, role):
    if kind.startswith("sasin_") or kind in ("josan", "peak"):
        base = {
            "sasin_back": "이 터의 등을 받치는 주산. 든든할수록 재물이 쌓이고 건강·안정이 좋아집니다.",
            "sasin_left": "왼쪽을 감싸는 청룡. 남자·명예·귀인의 기운을 북돋웁니다.",
            "sasin_right": "오른쪽을 감싸는 백호. 여자·재물·실리의 기운을 관장합니다.",
            "sasin_front": "앞에서 마주보는 안산. 손님·기회·명예를 맞이합니다.",
            "josan": "이 고을의 큰 산줄기가 내려온 조산. 국세의 크기를 정합니다.",
            "peak": "터 주변의 봉우리로 산세를 이룹니다.",
        }
        return base.get(kind, "산세를 이루는 봉우리입니다.")
    return "앞을 흐르는 물. 감싸 흐르면(환포) 재물이 고이고, 등지면(반궁) 새어나갑니다."


def _pick_region(region, table):
    for key, val in table.items():
        if key in (region or ""):
            return val
    return None


def _terrain_note(region, lm, josan, daesu, r03):
    back = lm.get("back") or josan
    water = lm.get("water") or daesu
    parts = [region]
    if josan:
        parts.append(f"{josan} 자락")
    bits = []
    if back:
        bits.append(f"뒤로 {back}이(가) 받치고")
    if lm.get("water"):
        emb = r03.get("embrace_sign", 0)
        bits.append(f"앞을 {lm['water']}이(가) {'감싸 흐르며' if emb >= 0 else '스치며'}")
    if daesu and daesu != lm.get("water"):
        bits.append(f"멀리 {daesu}이(가) 국세를 두르는")
    head = " ".join(p for p in parts if p)
    body = ", ".join(bits)
    if body:
        return f"{head} — {body} 국세입니다."
    return f"{head}의 지형을 실제 산·강 이름으로 풀었습니다."


def _facing_guide(a: SiteAssessment, R, lm: dict) -> dict:
    """창(주된 개구부)이 향하는 방위별 풍수 조언. 뒷산 오행과 겹쳐 구체화한다."""
    facing = (R["R08"].metrics.get("facing_deg", 180.0) if "R08" in R else 180.0)
    d8 = _compass(facing)
    base = {
        "남": ("남향 — 볕이 가득한 양명(陽明)의 향", "하루 종일 볕이 들어 건강·화합·재물이 두루 좋은 으뜸 향입니다. 거실·침실을 이 창 쪽에 두세요."),
        "남동": ("남동향 — 아침볕과 생기의 향", "아침 햇살이 들어 성장·시작·자녀운이 좋습니다. 재물이 자라는 방위라 초록 식물을 두면 좋습니다."),
        "동": ("동향 — 떠오르는 기운의 향", "아침 기운이 강해 건강·성장·새 출발에 좋습니다. 아침에 창을 활짝 여세요."),
        "남서": ("남서향 — 오후볕과 관계의 향", "따뜻한 오후볕으로 관계·화합에 좋으나 볕이 셀 수 있어 발(블라인드)로 조절하세요."),
        "서": ("서향 — 노을과 결실의 향", "오후볕이 강해 재물의 결실을 뜻하나 화기가 셀 수 있습니다. 여름 햇빛은 가리고 수경식물로 식혀주세요."),
        "북서": ("북서향 — 안정과 권위의 향", "차분한 빛으로 집중·권위에 좋습니다. 다소 서늘하니 따뜻한 색 조명으로 온기를 더하세요."),
        "북": ("북향 — 그윽하고 차분한 향", "직사광이 적어 서늘합니다. 밝은 조명과 따뜻한 색, 물 대신 나무 기운(초록)으로 보완하세요."),
        "북동": ("북동향 — 이른 기운의 향", "이른 아침 빛이 잠깐 듭니다. 습을 조심하고 환기·채광을 자주 하세요."),
    }
    title, body = base.get(d8, ("향 정보", "창의 방향을 실제 좌향으로 풀었습니다."))
    # 뒷산 오행이 화(火)면(관악산 등) 화기 비보 조언 강화
    lore = _match_lore(lm.get("back") or "")
    tip = "창가에 초록 식물이나 물그릇을 두어 기운을 부드럽게 하세요."
    if lore and lore[0].startswith("화"):
        tip = f"뒤의 {lm.get('back')}은 화기가 강한 산이라, 창가에 수경식물·물그릇을 두어 화기를 물로 눌러 다스리세요(경복궁이 관악산 화기를 물로 비보한 이치)."
    elif d8 in ("서", "남서"):
        tip = "오후 햇빛이 세니 얇은 커튼으로 가리고, 창가에 수경식물을 두어 화기를 식히세요."
    return {"dir": d8, "deg": round(facing), "title": title, "body": body, "tip": tip}


def _breakdown(code: str, m: dict, applicable: bool) -> list:
    """각 판정을 세부 항목으로 분해(복합 점수 체계). 항목: {label, pct(0~100), note}."""
    if not applicable or not m:
        return []
    b = []

    def add(label, pct, note):
        b.append({"label": label, "pct": int(round(max(0, min(100, pct)))), "note": note})

    if code == "R01":  # 배산임수
        g = m.get("max_gain_m", 0) or 0
        d = m.get("dist_m")
        add("능선 높이", _clamp01(g / 50) * 100, f"+{int(g)}m")
        if d is not None:
            add("근접성", _clamp01(1 - (d - 200) / 1300) * 100, f"{int(d)}m")
    elif code == "R02":  # 사신사
        lg = m.get("left_gain_m", 0) or 0
        rg = m.get("right_gain_m", 0) or 0
        bal = m.get("balance", 0) or 0
        add("청룡(좌)", _clamp01(lg / 30) * 100, f"+{int(lg)}m")
        add("백호(우)", _clamp01(rg / 30) * 100, f"+{int(rg)}m")
        add("좌우 균형", bal * 100, f"{int(bal * 100)}%")
    elif code == "R03":  # 물길
        d = m.get("dist_m")
        w = m.get("weight", 0) or 0
        emb = m.get("embrace_sign", 0)
        if d is not None:
            add("근접성", w * 100, f"{int(d)}m")
            add("환포/반궁", 100 if emb >= 0 else 25, "환포(길)" if emb >= 0 else "반궁(흉)")
    elif code == "R05":  # 직충살
        d = m.get("dist_m")
        st = m.get("strength", 0) or 0
        if d is not None:
            add("직충 회피", (1 - st) * 100, f"{int(d)}m · 강도 {round(st, 2)}")
    elif code == "R06":  # 반궁살
        d = m.get("dist_m")
        st = m.get("strength", 0) or 0
        if d is not None:
            add("반궁 회피", (1 - st) * 100, f"{int(d)}m")
    elif code == "R08":  # 좌향
        off = m.get("off_cardinal_deg")
        if off is not None:
            add("좌향 정격", _clamp01(1 - off / 22.5) * 100, f"정방위 편차 {round(off, 1)}°")
    elif code == "R10":  # 주변환경
        ns = m.get("net_score", 0) or 0
        add("주변 길흉 균형", _clamp01(0.5 + ns) * 100, f"시설 {m.get('n_poi', 0)}곳")
    return b


def _confidence(sources: dict) -> dict:
    keys = ["고도점", "하천", "도로", "주변시설", "산·강이름"]
    got = sum(1 for k in keys if (sources.get(k, 0) or 0) > 0)
    tier = "높음" if got >= 4 else ("보통" if got >= 2 else "낮음")
    return {"tier": tier, "pct": int(got / len(keys) * 100), "got": got, "total": len(keys)}


def _profile(a: SiteAssessment, R, lm: dict) -> list:
    """실측 프로필 — 실제 측정 수치·지형지물 이름으로 '전문 감정'다운 신뢰감을 준다.
    각 항목: {k: 요소, v: 핵심값, d: 세부수치, ok: 길흉(1/0/-1)}"""
    r01 = R["R01"].metrics if "R01" in R else {}
    r02 = R["R02"].metrics if "R02" in R else {}
    r03 = R["R03"].metrics if "R03" in R else {}
    r05 = R["R05"].metrics if "R05" in R else {}
    r08 = R["R08"].metrics if "R08" in R else {}
    out = []

    # 좌향 — 24산(한자 병기)
    if "facing_deg" in r08:
        fd = r08["facing_deg"]
        out.append({"k": "좌향(坐向)", "v": f"{_hanja(r08.get('jwa',''))}좌 {_hanja(r08.get('hyang',''))}향",
                    "d": f"{_compass(fd)}향 {round(fd)}° · 24산 · {r08.get('sect','')}", "ok": 1})

    # 현무 — 뒷산
    if (r01.get("max_gain_m", 0) or 0) > 0:
        out.append({"k": "현무(뒷산)", "v": lm.get("back") or "뒤 능선",
                    "d": f"{_compass(r01.get('bearing_deg'))}쪽 {int(r01.get('dist_m',0))}m · 표고 +{int(r01.get('max_gain_m',0))}m",
                    "ok": 1})
    else:
        out.append({"k": "현무(뒷산)", "v": "받침 약함", "d": "등 뒤를 받치는 능선이 뚜렷하지 않음", "ok": -1})

    # 청룡·백호
    lg = int(r02.get("left_gain_m", 0) or 0)
    rg = int(r02.get("right_gain_m", 0) or 0)
    if lg or rg or lm.get("left") or lm.get("right"):
        out.append({"k": "청룡·백호", "v": f"좌 {lm.get('left','—')} / 우 {lm.get('right','—')}",
                    "d": f"좌 +{lg}m · 우 +{rg}m", "ok": 1 if (lg and rg) else 0})

    # 득수 — 물길
    if r03.get("dist_m") is not None:
        emb = r03.get("embrace_sign", 0)
        word = "환포(감싸 안음·길)" if emb >= 0 else "반궁(등짐·흉)"
        out.append({"k": "득수(물길)", "v": lm.get("water") or "물길",
                    "d": f"{int(r03['dist_m'])}m · {word}", "ok": 1 if emb >= 0 else -1})
    else:
        out.append({"k": "득수(물길)", "v": "미확인",
                    "d": "가까운 하천 데이터가 잡히지 않음(없음 아님)", "ok": 0})

    # 정면 도로 — 직충살
    if r05.get("dist_m") is not None:
        out.append({"k": "정면 도로", "v": "직충살 감지",
                    "d": f"{int(r05['dist_m'])}m 앞 · 폭 {int(r05.get('width_m',0))}m", "ok": -1})
    else:
        out.append({"k": "정면 도로", "v": "곧은 충 없음", "d": "정면으로 찔러드는 도로 없음", "ok": 1})

    # 주변 실측 개수
    s = a.sources or {}
    out.append({"k": "주변 실측", "v": f"시설 {s.get('주변시설',0)}곳",
                "d": f"도로 {s.get('도로',0)} · 하천 {s.get('하천',0)} · 산/강이름 {s.get('산·강이름',0)}", "ok": 0})
    return out


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
        "profile": _profile(a, R, a.landmarks or {}),  # 실측 프로필(수치·지형지물)
        "terrain": _terrain(a, R, a.landmarks or {}),    # 다중 스케일 지형지물(대/중/소)
        "facingGuide": _facing_guide(a, R, a.landmarks or {}),  # 창 방향별 풍수 조언
        "section": a.section,                            # 배산임수 표고 단면
        "factors": a.factors,                            # 지도용 풍수 영향 요인(아이콘)
        "region": _region(a.address),                    # 지역명(구·동)
        "confidence": _confidence(a.sources),            # 데이터 충실도(신뢰도)
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
                "metrics": r.get("metrics", {}),  # 실측 수치(신빙성)
                "breakdown": _breakdown(r["code"], r.get("metrics", {}), r["applicable"]),  # 세부 배점
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
    # OSM(하천·도로·시설)이 실제로 잡힌 경우에만 캐시. 전부 0이면 Overpass 실패로
    # 보고 저장하지 않음(고도만 있는 반쪽 결과가 굳어 '물길 없음'으로 남는 것 방지).
    src = d.get("sources", {})
    osm_ok = ((src.get("하천", 0) or 0) + (src.get("도로", 0) or 0) + (src.get("주변시설", 0) or 0)) > 0
    if osm_ok:
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

    # 바이럴 전용 페이지(/v) — 기본 서비스와 별개. 지도 데이터 주입 불필요.
    if VIRAL_TEMPLATE.exists():
        vhtml = VIRAL_TEMPLATE.read_text(encoding="utf-8").replace("__NAVER_KEY__", naver_key)
        VIRAL_OUT.write_text(vhtml, encoding="utf-8")

    return OUT


if __name__ == "__main__":
    p = render()
    print(f"✓ 생성 완료: {p}  ({p.stat().st_size:,} bytes)")
