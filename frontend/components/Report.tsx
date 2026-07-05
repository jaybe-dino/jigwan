import Link from "next/link";
import { AXES, type SiteReport } from "@/lib/types";
import { ScoreSeal } from "./ScoreSeal";
import { Gauge } from "./Gauge";
import { RuleList } from "./RuleList";

export function Report({ data }: { data: SiteReport }) {
  return (
    <section className="report">
      <div className="rep-hero">
        <Link href="/" className="backlink">‹ 지도로</Link>
        <div className="rep-head">
          <ScoreSeal seal={data.gradeSeal} />
          <div className="who">
            <div className="addr">{data.addr}</div>
            <div className="score tnum">
              {data.site_score}
              <small>점</small>
            </div>
            <div className="badgerow">
              <span className="grade">「{data.grade}」</span>
              {data.precise && <span className="precise">✦ 정밀 감정</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="hd">
          <h3>감정 정확도</h3>
          <span className="sub">정밀 감정 시스템</span>
        </div>
        <div className="acc">
          <div className="bar">
            <i style={{ width: `${data.accuracy}%` }} />
          </div>
          <div className="pct tnum">{data.accuracy}%</div>
        </div>
        <p className="acc-note">
          ＋동·호수 입력 시 <b>75%</b> · 집 내부 3문항까지 <b>90%</b>로 정밀해집니다
        </p>
      </div>

      <div className="card">
        <div className="hd">
          <h3>기운 4축</h3>
          <span className="sub">재물운 중심</span>
        </div>
        <div className="gauges">
          {AXES.map((a, i) =>
            i === 0 ? (
              <div key={a.key} className="gauge main">
                <Gauge value={data.gauges[a.key]} cls={a.cls} />
                <div className="lab">
                  가장 중요한 <b>재물운</b> <span className="el">{a.el}</span>
                  <div className="faint">저점 매수, 이 터의 재물 기운으로 확신을</div>
                </div>
              </div>
            ) : (
              <div key={a.key} className="gauge small">
                <Gauge value={data.gauges[a.key]} cls={a.cls} size={42} />
                <div className="lab">
                  {a.key}
                  <span className="el">{a.el}</span>
                </div>
              </div>
            )
          )}
        </div>
      </div>

      <div className="card">
        <div className="hd">
          <h3>왜 이 결과일까?</h3>
          <span className="sub">근거 레이어 · {data.legend}</span>
        </div>
        <RuleList results={data.results} />
      </div>

      {data.bibo && (
        <div className="bibo">
          <div className="k">오늘의 비보 · 裨補</div>
          <h3>{data.bibo.title}</h3>
          <p>{data.bibo.body}</p>
          <div className="do">✦ {data.bibo.action}</div>
        </div>
      )}

      <p className="notice">
        본 서비스는 전통 풍수지리·명리 이론에 기반한 <b>참고·오락 목적</b> 콘텐츠로, 부동산 투자
        권유·자문이 아닙니다.
      </p>
    </section>
  );
}
