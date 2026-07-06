import { NextRequest, NextResponse } from "next/server";
import { computeCompat } from "@/lib/engine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const need = ["facing", "sect", "y", "m", "d"];
  for (const k of need) {
    if (!sp.get(k)) return NextResponse.json({ error: `${k} 필요` }, { status: 400 });
  }
  try {
    const hourStr = sp.get("hour");
    const result = await computeCompat({
      facing: parseFloat(sp.get("facing")!),
      sect: sp.get("sect")!,
      y: parseInt(sp.get("y")!),
      m: parseInt(sp.get("m")!),
      d: parseInt(sp.get("d")!),
      male: sp.get("male") === "1",
      hour: hourStr ? parseInt(hourStr) : null,
    });
    return NextResponse.json(result);
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 500 });
  }
}
