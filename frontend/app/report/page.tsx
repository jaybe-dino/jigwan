import Link from "next/link";
import { assessAddress } from "@/lib/engine";
import { Report } from "@/components/Report";

// 요청 시점에 엔진(python)을 실행하므로 동적 렌더
export const dynamic = "force-dynamic";

export default async function ReportPage({
  searchParams,
}: {
  searchParams: Promise<{ address?: string }>;
}) {
  const { address } = await searchParams;

  if (!address) {
    return (
      <section className="pad">
        <Link href="/" className="backlink">‹ 홈으로</Link>
        <p className="muted">주소가 없습니다. 홈에서 주소를 입력하세요.</p>
      </section>
    );
  }

  let error: string | null = null;
  let report = null;
  try {
    report = await assessAddress(address);
  } catch (e) {
    error = (e as Error).message;
  }

  if (error || !report) {
    return (
      <section className="pad">
        <Link href="/" className="backlink">‹ 홈으로</Link>
        <h2 style={{ marginTop: 12 }}>감정할 수 없습니다</h2>
        <p className="muted">{error ?? "알 수 없는 오류"}</p>
      </section>
    );
  }

  return <Report data={report} />;
}
