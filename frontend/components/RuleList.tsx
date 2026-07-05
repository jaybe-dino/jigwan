import { FRIENDLY, type RuleResult } from "@/lib/types";

function verdict(r: RuleResult): { cls: string; label: string } {
  if (!r.applicable) return { cls: "na", label: "해당 없음" };
  const pct = r.max_score ? r.score / r.max_score : 0;
  if (pct < 0.55) return { cls: "bad", label: "아쉬워요" };
  if (pct < 0.75) return { cls: "ok", label: "보통" };
  return { cls: "good", label: "좋아요" };
}

export function RuleList({ results }: { results: RuleResult[] }) {
  return (
    <div className="rules">
      {results.map((r) => {
        const v = verdict(r);
        return (
          <div key={r.code} className={"rule" + (r.applicable ? "" : " na")}>
            <div className="rh">
              <span className="nm">{FRIENDLY[r.code] ?? r.name}</span>
              <span className={`verdict ${v.cls}`}>{v.label}</span>
            </div>
            <div className="plain">{r.plain || r.evidence}</div>
            <details className="proof">
              <summary>전문 근거·수치 보기</summary>
              <div className="ev">
                {r.evidence}
                <span className="th">
                  ▪ {r.theory}
                  {r.tier ? ` · ${r.tier}` : ""}
                </span>
              </div>
            </details>
          </div>
        );
      })}
    </div>
  );
}
