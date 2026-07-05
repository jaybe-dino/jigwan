"""건축물대장 수집기 — 공공데이터포털 건축물대장 표제부(층수 등).

문서: https://www.data.go.kr/data/15044713/openapi.do (건축물대장정보 서비스)
GET http://apis.data.go.kr/1613000/BldRgstService_v2/getBrTitleInfo
    ?serviceKey=...&sigunguCd=&bjdongCd=&bun=&ji=&_type=json&numOfRows=10

주소 → 법정동코드·번지 변환은 주소기반산업지원서비스(juso.go.kr)가 필요하다.
여기서는 코드가 주어졌을 때 층수를 조회하는 부분을 구현한다(운영 시 juso 연동 추가).
"""

from __future__ import annotations

from typing import Callable, Optional

from pipeline.collectors.http import get_json

TITLE_URL = "http://apis.data.go.kr/1613000/BldRgstService_v2/getBrTitleInfo"


class BuildingRegistryClient:
    def __init__(self, service_key: str, http: Callable = get_json):
        self._key = service_key
        self._http = http

    def floors(self, sigungu_cd: str, bjdong_cd: str, bun: str, ji: str = "0") -> Optional[int]:
        """지상 층수(grndFlrCnt). 조회 실패 시 None."""
        data = self._http(
            TITLE_URL,
            params={
                "serviceKey": self._key, "_type": "json", "numOfRows": 10,
                "sigunguCd": sigungu_cd, "bjdongCd": bjdong_cd,
                "bun": bun.zfill(4), "ji": ji.zfill(4),
            },
        )
        items = (
            (((data or {}).get("response") or {}).get("body") or {}).get("items") or {}
        ).get("item")
        if not items:
            return None
        if isinstance(items, dict):
            items = [items]
        try:
            return int(items[0].get("grndFlrCnt"))
        except (TypeError, ValueError):
            return None
