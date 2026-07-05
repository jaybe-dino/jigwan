"""수집기 팩토리 — 키가 있으면 실 API, 없으면 픽스처로 폴백.

    from pipeline.collectors.factory import make_collectors
    collectors, live = make_collectors()      # live=True면 실 API
"""

from __future__ import annotations

from typing import Optional, Tuple

from pipeline.collectors.dem import ElevationAt
from pipeline.collectors.fixture import fixture_for
from pipeline.config import Config, load_config


def make_collectors(
    address: str = "명당",
    config: Optional[Config] = None,
    elevation_at: Optional[ElevationAt] = None,
):
    """(collectors, live) 반환. Kakao 키가 없으면 픽스처로 폴백."""
    config = config or load_config()
    if config.has_kakao:
        from pipeline.collectors.api import ApiCollectors

        return ApiCollectors(config, elevation_at=elevation_at), True
    return fixture_for(address), False
