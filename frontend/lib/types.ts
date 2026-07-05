// 지관 데이터 계약 — Python web/render.py shape_assessment() 출력과 1:1 일치.
// 웹 프로토타입(web/)과 이 Next.js 프론트가 공유하는 유일한 인터페이스.

export type Category = "형기" | "도로살" | "건물" | "환경";
export type AxisKey = "재물" | "건강" | "관계" | "명예";

export interface RuleResult {
  code: string;
  name: string;
  category: Category;
  score: number;
  max_score: number;
  applicable: boolean;
  evidence: string; // 전문가용 근거(전문용어+수치)
  theory: string;
  tier: string | null;
  plain: string; // 일반인용 쉬운 해석 (메인 노출)
}

export interface Interp {
  grade_meaning: string;
  body: string;
  strengths: { name: string; plain: string }[];
  cautions: { name: string; plain: string }[];
}

// 코드 → 친근한 이름 (engine.interpret.FRIENDLY와 일치)
export const FRIENDLY: Record<string, string> = {
  R01: "뒷산의 받침", R02: "양옆의 감쌈", R03: "물길", R04: "땅의 단단함", R05: "정면 도로",
  R06: "휜 도로", R07: "고가·철로", R08: "집의 방향", R09: "층수 기운", R10: "주변 환경",
};

export interface PriceTrend {
  now: string;
  chg: string;
  dir: "up" | "down";
  series: number[];
}

export interface BiboCard {
  title: string;
  body: string;
  action: string;
}

export interface SiteReport {
  addr: string;
  addrShort: string;
  precise: boolean;
  site_score: number;
  grade: string;
  gradeSeal: string;
  accuracy: number;
  gauges: Record<AxisKey, number>;
  results: RuleResult[];
  legend: string;
  price: PriceTrend;
  bibo: BiboCard | null;
  liner: string;
  interp: Interp;
}

export const AXES: { key: AxisKey; el: string; cls: string }[] = [
  { key: "재물", el: "金", cls: "jae" },
  { key: "건강", el: "木", cls: "gun" },
  { key: "관계", el: "水", cls: "gwan" },
  { key: "명예", el: "火", cls: "myeong" },
];
