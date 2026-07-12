"""판정 엔진 입출력 자료형.

SiteFeatures: 파이프라인이 외부 데이터를 공간연산해 만든 '구조화 피처'.
RuleResult:   개별 룰의 판정 결과(점수 + 숫자가 박힌 근거 문장).
SajuProfile:  궁합(11a/11b)용 사주 프로필 — 만세력 엔진은 M3, 여기선 자료형만.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

Coord = Tuple[float, float]  # (lat, lon)


# ---------------------------------------------------------------------------
# 입력 피처
# ---------------------------------------------------------------------------
@dataclass
class LatLon:
    lat: float
    lon: float

    def as_tuple(self) -> Coord:
        return (self.lat, self.lon)


@dataclass
class Building:
    """감정 대상 건물."""

    location: LatLon
    facing_deg: float  # 정면(向)이 바라보는 방위각. 0=N,90=E,180=S,270=W
    ground_elevation_m: float = 0.0
    floors: Optional[int] = None


@dataclass
class ElevationSample:
    """DEM 고도 샘플점."""

    point: LatLon
    elevation_m: float


@dataclass
class StreamSegment:
    """하천 중심선(폴리라인)."""

    points: List[LatLon]
    name: Optional[str] = None
    width_m: Optional[float] = None


@dataclass
class RoadSegment:
    """도로 중심선(폴리라인)."""

    points: List[LatLon]
    width_m: float = 6.0
    name: Optional[str] = None
    is_dead_end: bool = False  # 막다른 길
    is_t_head: bool = False  # T자 도로의 머리(정면 충돌 후보)


@dataclass
class RailOverpass:
    kind: str  # 'rail' | 'overpass'
    nearest: LatLon
    height_diff_m: float = 0.0


@dataclass
class POI:
    point: LatLon
    category: str  # 정규화 카테고리 (r10_poi.CATEGORY_WEIGHTS 키)
    name: Optional[str] = None


@dataclass
class HistoricalLand:
    """옛 지형도 기반 과거 지목."""

    past_types: List[str] = field(default_factory=list)  # 예: ['하천','논']


@dataclass
class Precision:
    """Lv.3 정밀 감정 입력(선택)."""

    dong_position: Optional[str] = None  # 'center' | 'edge' | None


@dataclass
class SiteFeatures:
    """엔진 입력 — 한 터의 구조화 피처 전체."""

    address: str
    building: Building
    dem: List[ElevationSample] = field(default_factory=list)
    streams: List[StreamSegment] = field(default_factory=list)
    roads: List[RoadSegment] = field(default_factory=list)
    rails_overpasses: List[RailOverpass] = field(default_factory=list)
    pois: List[POI] = field(default_factory=list)
    historical: Optional[HistoricalLand] = None
    precision: Optional[Precision] = None
    # 실제 지형지물 이름(뒷산·물길 등) — 있으면 해석에 그대로 반영
    landmarks: Optional[Dict[str, str]] = None
    # 다중 스케일 지형지물 상세(산봉우리·하천) — {name,kind,lat,lon,ele,dist,bearing}
    terrain: List[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------
CATEGORY_HYEONGGI = "형기"
CATEGORY_ROAD = "도로살"
CATEGORY_BUILDING = "건물"
CATEGORY_ENVIRONMENT = "환경"


@dataclass
class RuleResult:
    """개별 룰 판정 결과."""

    code: str  # 'R01'
    name: str  # '배산임수'
    category: str  # CATEGORY_*
    max_score: float
    score: float
    applicable: bool
    evidence: str  # 전문가용 근거 문장 (전문용어 + 숫자)
    theory: str  # 형기론/이기론 등 적용 이론
    tier: Optional[str] = None  # 등급어 (예: '현무 든든')
    metrics: Dict[str, Any] = field(default_factory=dict)
    plain: str = ""  # 일반인용 쉬운 해석 (전문용어 없이, engine.plain에서 채움)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 궁합(M3)용 — 자료형/인터페이스만
# ---------------------------------------------------------------------------
@dataclass
class SajuProfile:
    """사주 프로필. 만세력 계산은 M3에서 채운다."""

    birth_date: str  # 'YYYY-MM-DD'
    birth_hour: Optional[int] = None  # 0~23, 모르면 None
    hour_unknown: bool = False
    five_elements: Dict[str, float] = field(default_factory=dict)  # 오행 분포
    yongsin: Optional[str] = None  # 용신 오행
    bonmyeonggung: Optional[str] = None  # 본명궁(구성)
