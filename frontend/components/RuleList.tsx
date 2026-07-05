import type { RuleResult } from "@/lib/types";

function trackColor(pct: number): string {
  if (pct >= 80) return "var(--good)";
  if (pct >= 55) return "var(--warn)";
  return "var(--bad)";
}

export function RuleList({ results }: { results: RuleResult[] }) {
  return (
    <div className="rules">
      {results.map((r) => {
        const pct = r.max_score ? Math.round((r.score / r.max_score) * 100) : 0;
        return (
          <div key={r.code} className={"rule" + (r.applicable ? "" : " na")}>
            <div className="rh">
              <span className="code">{r.code}</span>
              <span className="nm">{r.name}</span>
              <span className="pts tnum">
                {r.score.toFixed(1)}
                <small>/{r.max_score}</small>
              </span>
            </div>
            <div className="track">
              <i style={{ width: `${pct}%`, background: trackColor(pct) }} />
            </div>
            <div className="ev">{r.evidence}</div>
            <div className="th">
              ▪ {r.theory}
              {r.tier ? ` · ${r.tier}` : ""}
            </div>
          </div>
        );
      })}
    </div>
  );
}
