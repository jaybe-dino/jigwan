import Link from "next/link";
import { AddressForm } from "@/components/AddressForm";

const SAMPLES = [
  { addr: "서울특별시 마포구 월드컵로 212", sub: "성산시영아파트 3동 1204호" },
  { addr: "서울특별시 동대문구 왕산로 220", sub: "청솔빌라 301호" },
];

export default function Home() {
  return (
    <section className="home">
      <header className="topbar">
        <div className="brand">
          <span className="mark">智</span>
          <div>
            <b>지관</b>
            <span>AI 풍수 감정</span>
          </div>
        </div>
      </header>

      <div className="hero">
        <p className="eyebrow">숫자는 다 보셨잖아요</p>
        <h1>이제, 터를 보세요.</h1>
        <p className="muted">
          지번·도로명에 <b>동·호수</b>까지 넣을수록 그 집 한 채를 정밀하게 감정합니다.
        </p>
      </div>

      <AddressForm />

      <div className="samples">
        <p className="eyebrow">예시 주소</p>
        {SAMPLES.map((s) => (
          <Link key={s.addr} href={`/report?address=${encodeURIComponent(s.addr)}`} className="addrrow">
            <span className="ico">🔍</span>
            <span className="a">
              <b>{s.addr}</b>
              <small>{s.sub}</small>
            </span>
            <span className="go">›</span>
          </Link>
        ))}
      </div>
      <p className="demo-note">
        판정은 룰북 엔진(M1)의 실제 출력 · 키가 없으면 데모 샘플로 폴백합니다
      </p>
    </section>
  );
}
