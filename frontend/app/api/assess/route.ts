import { NextRequest, NextResponse } from "next/server";
import { assessAddress, assessCoord } from "@/lib/engine";

// child_process 사용 → Node 런타임 + 동적 실행
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const lat = sp.get("lat");
  const lon = sp.get("lon");
  const address = sp.get("address");
  try {
    let report;
    if (lat && lon) {
      report = await assessCoord(parseFloat(lat), parseFloat(lon));
    } else if (address) {
      report = await assessAddress(address);
    } else {
      return NextResponse.json({ error: "주소나 좌표가 필요합니다" }, { status: 400 });
    }
    return NextResponse.json(report);
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 });
  }
}
