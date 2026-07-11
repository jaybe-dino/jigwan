"""터 점수 집계·등급·4축 게이지 (룰북 §0.3, §12 / 기획안 §4.5, §4).

assess_site(features) → SiteAssessment(터점수, 등급, 요소별 결과, 4축 게이지).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List

from engine.calibration import DEFAULT, Calibration
from engine.models import RuleResult, SiteFeatures
from engine.plain import annotate_plain
from engine.rulebook import ALL_RULES


class Grade(str, Enum):
    CHEONHA = "천하명당"  # 95+
    MYEONGDANG = "명당"   # 85~94
    GILJI = "길지"        # 70~84
    PYEONGJI = "평지"     # 50~69
    BIBOJI = "비보지"     # <50

    @classmethod
    def of(cls, score: float) -> "Grade":
        if score >= 95:
            return cls.CHEONHA
        if score >= 85:
            return cls.MYEONGDANG
        if score >= 70:
            return cls.GILJI
        if score >= 50:
            return cls.PYEONGJI
        return cls.BIBOJI


# 4축 게이지: 각 룰의 (score/max) 기여를 축에 분배. 재물이 메인(기획안 §2).
# 값은 축 가중(합이 1이 아니어도 됨 — 축별 정규화).
AXIS_WEIGHTS: Dict[str, Dict[str, float]] = {
    "R01": {"건강": 0.6, "재물": 0.4},
    "R02": {"관계": 0.6, "건강": 0.4},
    "R03": {"재물": 1.0},
    "R04": {"건강": 0.7, "재물": 0.3},
    "R05": {"재물": 0.6, "건강": 0.4},
    "R06": {"재물": 0.5, "관계": 0.5},
    "R07": {"건강": 1.0},
    "R08": {"명예": 0.7, "재물": 0.3},
    "R09": {"명예": 0.5, "재물": 0.5},
    "R10": {"재물": 0.4, "건강": 0.3, "관계": 0.2, "명예": 0.1},
}
AXES = ["재물", "건강", "관계", "명예"]


@dataclass
class SiteAssessment:
    address: str
    site_score: int          # 0~100
    grade: Grade
    raw_score: float         # 캘리브레이션 전 원점수
    gauges: Dict[str, int]   # 축 → 0~100
    results: List[RuleResult] = field(default_factory=list)
    coord: tuple = (0.0, 0.0)  # (lat, lon) — 지도 중심
    landmarks: Dict[str, str] = field(default_factory=dict)  # 실제 지형지물 이름
    sources: Dict[str, int] = field(default_factory=dict)   # 실측 데이터 개수(투명성)
    section: List[dict] = field(default_factory=list)       # 배산임수 표고 단면(앞←집→뒤)
    factors: List[dict] = field(default_factory=list)       # 지도용 풍수 영향 요인(아이콘·좌표·길흉)

    @property
    def needs_bibo(self) -> bool:
        return self.grade == Grade.BIBOJI

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "site_score": self.site_score,
            "grade": self.grade.value,
            "raw_score": round(self.raw_score, 2),
            "gauges": self.gauges,
            "results": [r.to_dict() for r in self.results],
        }


def _compute_gauges(results: List[RuleResult]) -> Dict[str, int]:
    acc = {a: 0.0 for a in AXES}
    wsum = {a: 0.0 for a in AXES}
    for r in results:
        if not r.applicable or r.max_score <= 0:
            continue
        frac = r.score / r.max_score
        for axis, w in AXIS_WEIGHTS.get(r.code, {}).items():
            acc[axis] += frac * w
            wsum[axis] += w
    return {
        a: int(round(100 * acc[a] / wsum[a])) if wsum[a] > 0 else 50
        for a in AXES
    }


def assess_site(
    features: SiteFeatures, calibration: Calibration = DEFAULT
) -> SiteAssessment:
    results = [annotate_plain(rule(features), features.landmarks) for rule in ALL_RULES]

    num = 0.0
    den = 0.0
    for r in results:
        if not r.applicable:
            continue
        w = calibration.weight(r.code)
        num += r.score * w
        den += r.max_score * w
    raw = (100.0 * num / den) if den > 0 else 0.0
    final = calibration.map_score(raw)
    score_int = int(round(final))

    loc = features.building.location
    sources = {
        "고도점": len(features.dem), "하천": len(features.streams),
        "도로": len(features.roads), "주변시설": len(features.pois),
        "산·강이름": len(features.landmarks or {}),
    }
    return SiteAssessment(
        address=features.address,
        site_score=score_int,
        grade=Grade.of(score_int),
        raw_score=raw,
        gauges=_compute_gauges(results),
        results=results,
        coord=(loc.lat, loc.lon),
        landmarks=features.landmarks or {},
        sources=sources,
        section=_elev_section(features),
        factors=_map_factors(features),
    )


# 풍수 영향 요인 → (아이콘, 길흉 +1/0/-1, 한줄 이유)
_POI_FACTOR = {
    "park": ("🌳", 1, "녹지·생기"), "school": ("🏫", 1, "문곡성·학군"),
    "library": ("📚", 1, "문창"), "hospital": ("🏥", 0, "의료 인접"),
    "subway": ("🚇", 1, "교통 편의"), "funeral": ("⚰️", -1, "음기(장례)"),
    "power_tower": ("⚡", -1, "전자기 살"), "gas_station": ("⛽", -1, "화기·인화"),
    "nightlife": ("🍸", -1, "야간 소란"),
}


def _map_factors(features: SiteFeatures) -> List[dict]:
    """지도에 아이콘으로 찍을 실제 풍수 영향 요인(주변 시설·물길·철로)."""
    from engine.geo import haversine

    o = features.building.location
    out: List[dict] = []
    for poi in (features.pois or []):
        ic = _POI_FACTOR.get(poi.category)
        if not ic:
            continue
        dist = haversine(o.as_tuple(), poi.point.as_tuple())
        out.append({"lat": poi.point.lat, "lon": poi.point.lon, "icon": ic[0],
                    "effect": ic[1], "kind": "poi", "why": ic[2],
                    "label": (poi.name or ic[2]), "dist": int(round(dist))})
    # 물길 최근접점
    best = None
    for s in (features.streams or []):
        for p in s.points:
            dd = haversine(o.as_tuple(), p.as_tuple())
            if best is None or dd < best[0]:
                best = (dd, p, s.name)
    if best and best[0] <= 700:
        out.append({"lat": best[1].lat, "lon": best[1].lon, "icon": "💧", "effect": 1,
                    "kind": "water", "why": "득수(재물)", "label": best[2] or "물길", "dist": int(best[0])})
    # 철로/고가 최근접
    for r in (features.rails_overpasses or [])[:1]:
        dd = haversine(o.as_tuple(), r.nearest.as_tuple())
        out.append({"lat": r.nearest.lat, "lon": r.nearest.lon, "icon": "🚆", "effect": -1,
                    "kind": "rail", "why": "철로 충살", "label": "철로·고가", "dist": int(dd)})
    # 거리순 상위 24개만
    out.sort(key=lambda x: x["dist"])
    return out[:24]


def _elev_section(features: SiteFeatures) -> List[dict]:
    """앞←집→뒤 방향 표고 단면(배산임수 시각화용). DEM 샘플을 좌향축에 투영.

    t: 집 기준 축 위치(m, 뒤=+/앞=−), e: 표고(m). 능선을 보이게 같은 t는 최고값.
    """
    from engine.geo import angle_diff, bearing, haversine

    b = features.building
    back_deg = (b.facing_deg + 180.0) % 360.0
    o = b.location.as_tuple()
    agg: Dict[int, float] = {0: round(b.ground_elevation_m, 1)}
    for s in features.dem or []:
        p = s.point.as_tuple()
        d = haversine(o, p)
        brg = bearing(o, p)
        if angle_diff(brg, back_deg) <= 32:      # 뒤쪽
            t = int(round(d))
        elif angle_diff(brg, b.facing_deg) <= 32:  # 앞쪽
            t = -int(round(d))
        else:
            continue
        e = round(s.elevation_m, 1)
        if t not in agg or e > agg[t]:
            agg[t] = e
    return [{"t": t, "e": agg[t]} for t in sorted(agg)]
