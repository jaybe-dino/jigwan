"""쉬운 해석 레이어(plain) + 종합 해석(interpret) 검증."""

from engine.interpret import FRIENDLY, summarize
from engine.plain import GLOSSARY
from engine.samples import biboji_site, myeongdang_site
from engine.scoring import assess_site


def test_every_rule_has_plain():
    a = assess_site(myeongdang_site())
    for r in a.results:
        assert r.plain, f"{r.code} plain 비어있음"
        assert len(r.plain) > 10


def test_plain_avoids_raw_jargon_headword():
    # 쉬운 해석엔 '현무/좌청룡' 같은 생 전문용어가 그대로 튀지 않아야 한다
    a = assess_site(myeongdang_site())
    joined = " ".join(r.plain for r in a.results)
    for jargon in ("현무", "좌청룡", "우백호", "환포수", "반궁수"):
        assert jargon not in joined


def test_summarize_structure():
    a = assess_site(myeongdang_site())
    s = summarize(a)
    assert s["grade_meaning"]
    assert s["body"] and len(s["body"]) > 20
    assert isinstance(s["strengths"], list)
    # 친근한 이름만 노출 (코드 아님)
    for item in s["strengths"]:
        assert item["name"] in FRIENDLY.values()


def test_biboji_has_cautions():
    a = assess_site(biboji_site())
    s = summarize(a)
    assert len(s["cautions"]) >= 1  # 비보형은 아쉬운 점이 있어야


def test_josa_no_double_particle_error():
    # '고가·철로'(모음 끝) → '는' 이어야
    a = assess_site(biboji_site())
    body = summarize(a)["body"]
    assert "철로은" not in body


def test_glossary_present():
    assert "현무" in GLOSSARY and "직충살" in GLOSSARY
