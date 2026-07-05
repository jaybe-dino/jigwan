"""쉬운 해석 레이어 — 전문 판정(RuleResult)을 일반인 언어로 풀어쓴다.

원칙(사용자 요구): 점수·전문용어가 아니라 "이게 나에게 무슨 뜻인지"가 중요하다.
- 전문용어는 쓰더라도 그 자리에서 한 번 쉬운 말로 풀어준다.
- 좋으면 왜 좋은지, 아쉬우면 무엇을 하면 되는지(생활 팁)까지 한 문장으로.

engine.scoring.assess_site가 각 RuleResult에 이 텍스트를 채운다(annotate_plain).
"""

from __future__ import annotations

from engine.models import RuleResult

# 전문용어 → 한 줄 쉬운 풀이 (UI 용어사전에도 노출)
GLOSSARY = {
    "현무": "집 뒤를 받쳐주는 산·언덕",
    "좌청룡·우백호": "집 양옆을 감싸는 언덕",
    "안산": "집 앞을 마주보는 나지막한 산",
    "환포수": "집을 감싸 안듯 흐르는 물 (좋게 봄)",
    "반궁수": "집을 등지고 휘어 나가는 물 (아쉽게 봄)",
    "직충살": "집 정면으로 곧게 찔러 들어오는 도로",
    "반궁살": "휜 도로의 바깥쪽에 놓인 자리",
    "좌향": "집이 앉은 방향과 바라보는 방향",
    "동사택·서사택": "집 방향의 두 계열 (사람과의 궁합을 볼 때 씀)",
    "양택삼요": "현관·안방·주방의 배치를 보는 법",
    "오행": "물·불·나무·쇠·흙 다섯 기운",
}

_DIR8 = ["북", "북동", "동", "남동", "남", "남서", "서", "북서"]


def _dir_ko(deg: float) -> str:
    return _DIR8[round((deg % 360) / 45) % 8]


def _ratio(r: RuleResult) -> float:
    return r.score / r.max_score if r.max_score else 0.0


def _r01(r):  # 배산임수
    if r.metrics.get("max_gain_m", 0) >= 20:
        return "집 뒤쪽을 산·언덕이 든든하게 받쳐줘요. 등 뒤가 허전하지 않아 안정감 있고, 오래 기대어 살기 좋은 자리예요."
    return "집 뒤에 기댈 언덕이 거의 없어요. 뒤가 트여 허전할 수 있으니, 뒤쪽 벽에 큰 가구나 그림으로 '등받이'를 만들어 주면 좋아요."


def _r02(r):  # 사신사
    if _ratio(r) >= 0.6:
        return "집 양옆을 언덕이 감싸줘서 아늑해요. 좌우가 뻥 뚫리지 않아 포근한 느낌의 자리예요."
    return "집 양옆이 트여 있어 감싸주는 느낌이 약해요. 창가에 화분이나 키 큰 화초로 아늑함을 더하면 좋아요."


def _r03(r):  # 환포/반궁수
    s = r.metrics.get("embrace_sign", 0)
    if s > 0:
        return "집 앞으로 흐르는 물이 집을 감싸 안듯 흘러요. 예부터 '재물이 모이는 자리'로 보는 좋은 물길이에요."
    if s < 0:
        return "물길이 집을 등지고 바깥으로 휘어 나가요. 기운이 빠져나간다고 보는 자리라, 앞쪽에 밝은 조명이나 화분으로 기운을 붙잡아 주면 좋아요."
    return "가까이 물길이 없어, 물의 좋고 나쁨은 크게 따질 게 없는 자리예요."


def _r04(r):  # 매립·구하도
    if _ratio(r) >= 0.99:
        return "옛날부터 마른 땅이었어요. 땅이 단단해 안심할 수 있는 자리예요."
    t = r.metrics.get("worst_type", "물가")
    return f"이 땅은 예전에 '{t}'였어요. 땅이 무르거나 습할 수 있으니, 습기 관리와 밝은 조명이 도움돼요."


def _r05(r):  # 직충살
    if _ratio(r) >= 0.99:
        return "집 정면으로 곧게 들이치는 도로가 없어요. 앞이 편안한 자리예요."
    return ("집 정면으로 도로가 곧게 찔러 들어와요(이런 걸 '직충살'이라 해요). "
            "차·바람·시선이 정면으로 들이쳐 부담될 수 있으니, 현관 앞에 가림막이나 큰 화분을 두면 한결 편해져요.")


def _r06(r):  # 반궁살
    if _ratio(r) >= 0.99:
        return "도로가 등을 떠미는 자리가 아니에요. 편안한 편이에요."
    return "휘어진 도로의 바깥쪽에 집이 있어요. 도로가 등을 미는 느낌이라, 그쪽 창에 커튼이나 화분으로 완충해 주면 좋아요."


def _r07(r):  # 고가·철로
    if _ratio(r) >= 0.99:
        return "가까이 고가도로나 철로가 없어요. 조용하고 안정된 자리예요."
    return "가까이 고가도로나 철로가 있어요. 소음·진동·시선이 있을 수 있으니, 이중창이나 두꺼운 커튼이 도움돼요."


def _r08(r):  # 좌향
    deg = r.metrics.get("facing_deg", 180)
    sect = r.metrics.get("sect", "동사택")
    return (f"집이 바라보는 방향은 {_dir_ko(deg)}쪽이에요. 이 방향은 '{sect}'이라는 계열에 속하는데, "
            "나와 잘 맞는 방향인지는 '궁합'에서 생년월일로 확인할 수 있어요.")


_OHAENG_PLAIN = {
    "수": "물처럼 재물과 흐름의 기운", "화": "불처럼 활동적이고 이름을 알리는 기운",
    "목": "나무처럼 자라나는 건강·성장의 기운", "금": "쇠처럼 야무진 결실·재정의 기운",
    "토": "흙처럼 든든한 안정·중심의 기운",
}


def _r09(r):  # 층수·동
    if not r.applicable:
        return "동·호수를 입력하면 층수와 동 배치까지 자세히 봐드려요."
    oh = r.metrics.get("ohaeng", "토")
    fl = r.metrics.get("floors", "")
    return f"{fl}층은 오행(다섯 기운)으로 보면 {_OHAENG_PLAIN.get(oh, '중심의 기운')}과 어울리는 층이에요."


def _r10(r):  # 주변 POI
    net = r.metrics.get("net_score", 0)
    if net > 0.3:
        return "가까이 공원·학교·물처럼 기분 좋은 시설이 있어 환경이 쾌적해요."
    if net < -0.3:
        return "가까이 꺼리는 시설(장례식장·유흥가 등)이 있어요. 신경 쓰이면 그쪽 창을 자주 열지 않는 것도 방법이에요."
    return "주변에 특별히 좋거나 나쁜 시설이 도드라지지 않아 무난해요."


_PLAIN = {
    "R01": _r01, "R02": _r02, "R03": _r03, "R04": _r04, "R05": _r05,
    "R06": _r06, "R07": _r07, "R08": _r08, "R09": _r09, "R10": _r10,
}


def annotate_plain(result: RuleResult) -> RuleResult:
    """RuleResult.plain 을 쉬운 해석으로 채운다."""
    fn = _PLAIN.get(result.code)
    if fn is not None:
        result.plain = fn(result)
    return result
