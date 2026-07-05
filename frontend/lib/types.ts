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
  evidence: string;
  theory: string;
  tier: string | null;
}

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
}

export const AXES: { key: AxisKey; el: string; cls: string }[] = [
  { key: "재물", el: "金", cls: "jae" },
  { key: "건강", el: "木", cls: "gun" },
  { key: "관계", el: "水", cls: "gwan" },
  { key: "명예", el: "火", cls: "myeong" },
];
