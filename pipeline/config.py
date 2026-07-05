"""파이프라인 설정 — 외부 API 키를 환경변수에서 읽는다.

키가 없으면 해당 수집기는 비활성화되고 팩토리가 픽스처로 폴백한다.
실제 키는 절대 커밋하지 않는다(.env는 .gitignore).

    export KAKAO_REST_KEY=...          # 카카오 로컬(주소·POI)
    export VWORLD_KEY=...              # 브이월드(도로·하천·건물 피처)
    export DATA_GO_KR_KEY=...          # 공공데이터포털(건축물대장·실거래가)
    export JIGWAN_DATABASE_URL=...     # PostGIS
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    kakao_key: str | None = None
    vworld_key: str | None = None
    data_go_kr_key: str | None = None
    database_url: str | None = None

    @property
    def has_kakao(self) -> bool:
        return bool(self.kakao_key)

    @property
    def has_vworld(self) -> bool:
        return bool(self.vworld_key)

    @property
    def has_building(self) -> bool:
        return bool(self.data_go_kr_key)


def load_config() -> Config:
    return Config(
        kakao_key=os.environ.get("KAKAO_REST_KEY") or None,
        vworld_key=os.environ.get("VWORLD_KEY") or None,
        data_go_kr_key=os.environ.get("DATA_GO_KR_KEY") or None,
        database_url=os.environ.get("JIGWAN_DATABASE_URL") or None,
    )
