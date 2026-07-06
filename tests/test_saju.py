"""실제 사주(만세력) + 궁합 검증. korean_lunar_calendar 없으면 스킵."""

try:
    import korean_lunar_calendar  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False


def test_saju_pillars_real():
    if not HAVE:
        return
    from engine.saju import compute_saju
    s = compute_saju(1990, 5, 15, is_male=True, hour=14)
    assert s.pillars["년"] == "경오"  # KARI 만세력 기준
    assert s.pillars["일"] == "경진"
    assert s.ilgan_oh in ("목", "화", "토", "금", "수")
    assert s.sect in ("동사택", "서사택")


def test_compat_deterministic_and_bounded():
    if not HAVE:
        return
    from engine.rulebook.compat import compute_compat
    r = compute_compat(170, "동사택", 1990, 5, 15, True, 14)
    assert 4 <= r.percent <= 97
    # 결정적: 같은 입력 → 같은 결과
    r2 = compute_compat(170, "동사택", 1990, 5, 15, True, 14)
    assert r.percent == r2.percent
    # 다른 생일 → 다른 사주
    r3 = compute_compat(170, "동사택", 1985, 1, 1, False, None)
    assert r3.saju_pillars != r.saju_pillars
