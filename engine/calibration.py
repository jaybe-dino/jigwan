"""점수 분포 캘리브레이션 손잡이 (룰북 §13 / 기획안 §4.4).

목표: 평균 62~68점, 90+ 상위 3% 이내.
M1은 판정식만 확정하고, 실제 분포 튜닝은 표본 감정 후 M5.
아래 파라미터는 그 튜닝 지점을 한곳에 모아둔 것.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Calibration:
    # 요소별 가중(기본 1.0). 분포 조정 시 배점을 건드리지 않고 여기서 스케일.
    rule_weights: Dict[str, float] = field(default_factory=dict)
    # 원점수(0~100)를 최종 표기 점수로 매핑하는 선형 보정.
    # 초기값은 항등(무보정). M5에서 표본 분포 보고 조정.
    offset: float = 0.0
    slope: float = 1.0

    def weight(self, code: str) -> float:
        return self.rule_weights.get(code, 1.0)

    def map_score(self, raw: float) -> float:
        return max(0.0, min(100.0, self.slope * raw + self.offset))


DEFAULT = Calibration()
