"""공간연산 검증 하네스 자체 테스트 (pipeline.validate)."""

from pipeline.validate import selfcheck_geo


def test_selfcheck_geo_passes():
    assert selfcheck_geo() is True
