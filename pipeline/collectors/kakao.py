"""카카오 로컬 API 수집기 — 주소 지오코딩 + 주변 POI.

문서: https://developers.kakao.com/docs/latest/ko/local/dev-guide
헤더: Authorization: KakaoAK {REST_KEY}
"""

from __future__ import annotations

from typing import Callable, List

from engine.models import POI, LatLon
from pipeline.collectors.base import BuildingInfo
from pipeline.collectors.http import get_json

ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

# 풍수 카테고리 → 카카오 키워드 (반경 내 검색)
POI_QUERIES = [
    ("장례식장", "funeral"),
    ("송전탑", "power_tower"),
    ("유흥주점", "nightlife"),
    ("쓰레기처리장", "waste"),
    ("주유소", "gas_station"),
    ("공원", "park"),
    ("학교", "school"),
    ("도서관", "library"),
    ("종합병원", "hospital"),
    ("지하철역", "subway"),
    ("하천", "water"),
]


class KakaoClient:
    def __init__(self, rest_key: str, http: Callable = get_json):
        self._headers = {"Authorization": f"KakaoAK {rest_key}"}
        self._http = http

    # --- 주소 → 좌표 ---
    def geocode(self, address: str) -> BuildingInfo:
        data = self._http(ADDRESS_URL, params={"query": address}, headers=self._headers)
        docs = data.get("documents") or []
        if not docs:
            raise ValueError(f"주소를 찾을 수 없습니다: {address}")
        d = docs[0]
        loc = LatLon(lat=float(d["y"]), lon=float(d["x"]))
        # 좌향(배치각)·층수는 건축물대장/건물 폴리곤에서 채운다. 여기선 좌표만.
        return BuildingInfo(location=loc, facing_deg=0.0, ground_elevation_m=0.0)

    # --- 주변 POI ---
    def pois(self, center: LatLon, radius_m: float) -> List[POI]:
        out: List[POI] = []
        for query, category in POI_QUERIES:
            data = self._http(
                KEYWORD_URL,
                params={
                    "query": query,
                    "x": center.lon,
                    "y": center.lat,
                    "radius": int(min(radius_m, 20000)),
                    "sort": "distance",
                    "size": 15,
                },
                headers=self._headers,
            )
            for doc in data.get("documents") or []:
                out.append(
                    POI(
                        point=LatLon(lat=float(doc["y"]), lon=float(doc["x"])),
                        category=category,
                        name=doc.get("place_name"),
                    )
                )
        return out
