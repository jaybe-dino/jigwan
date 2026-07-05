"""수집기 팩토리 — 기본은 무료 실데이터(OSM+OpenTopoData), 전국 실측.

    from pipeline.collectors.factory import make_collectors
    collectors, live = make_collectors(address)

- 기본: OsmCollectors (실제 DEM·산·강·도로, 키 불필요) → '가짜' 아님.
- JIGWAN_FIXTURE=1 이면 픽스처(오프라인 데모/테스트).
- 카카오/브이월드 키가 있으면 지오코딩 정확도 향상에 쓸 수 있음(선택).
"""

from __future__ import annotations

import os
from typing import Optional

from pipeline.collectors.fixture import fixture_for
from pipeline.config import Config, load_config


def make_collectors(address: str = "", config: Optional[Config] = None):
    """(collectors, live) 반환. 기본은 실데이터, JIGWAN_FIXTURE면 픽스처."""
    config = config or load_config()
    if os.environ.get("JIGWAN_FIXTURE"):
        return fixture_for(address), False
    from pipeline.collectors.osm import OsmCollectors

    return OsmCollectors(), True
