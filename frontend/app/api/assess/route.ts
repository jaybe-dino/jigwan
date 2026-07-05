import { NextRequest, NextResponse } from "next/server";
import { assessAddress } from "@/lib/engine";

// child_process 사용 → Node 런타임 + 동적 실행
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const address = req.nextUrl.searchParams.get("address");
  if (!address) {
    return NextResponse.json({ error: "주소를 입력하세요" }, { status: 400 });
  }
  try {
    const report = await assessAddress(address);
    return NextResponse.json(report);
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 });
  }
}
