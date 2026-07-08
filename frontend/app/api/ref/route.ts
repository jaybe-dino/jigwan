// 추천인(레퍼럴) 트래킹 — 누가 누굴 초대했는지 파일에 저장.
// 주의: Railway 컨테이너 파일시스템은 재배포 시 초기화됨. 영속화하려면
//       JIGWAN_REF_FILE 을 볼륨 경로로 지정하거나 외부 DB로 교체할 것.
import { NextRequest, NextResponse } from "next/server";
import fs from "node:fs";
import path from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const FILE =
  process.env.JIGWAN_REF_FILE || path.join(process.cwd(), "..", "data", "referrals.json");

type User = {
  code: string;
  invitedBy: string | null;
  terbti?: string;
  region?: string;
  ts: number;
};
type Store = { users: Record<string, User> };

function read(): Store {
  try {
    return JSON.parse(fs.readFileSync(FILE, "utf-8"));
  } catch {
    return { users: {} };
  }
}
function write(s: Store) {
  try {
    fs.mkdirSync(path.dirname(FILE), { recursive: true });
    fs.writeFileSync(FILE, JSON.stringify(s));
  } catch {
    /* 파일시스템 불가 시 조용히 무시(집계만 유실) */
  }
}
function clean(c: string): string {
  return (c || "").replace(/[^a-zA-Z0-9]/g, "").slice(0, 16);
}
function counts(store: Store): Record<string, number> {
  const c: Record<string, number> = {};
  Object.values(store.users).forEach((u) => {
    if (u.invitedBy) c[u.invitedBy] = (c[u.invitedBy] || 0) + 1;
  });
  return c;
}

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const store = read();

  if (sp.get("action") === "leaderboard") {
    const c = counts(store);
    const top = Object.entries(c)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([code, n], i) => ({
        rank: i + 1,
        code,
        count: n,
        terbti: store.users[code]?.terbti || null,
        region: store.users[code]?.region || null,
      }));
    return NextResponse.json({ leaderboard: top, totalUsers: Object.keys(store.users).length });
  }

  const code = clean(sp.get("code") || "");
  if (!code) return NextResponse.json({ error: "code 필요" }, { status: 400 });
  const invited = Object.values(store.users)
    .filter((u) => u.invitedBy === code)
    .sort((a, b) => b.ts - a.ts)
    .map((u) => ({ code: u.code, terbti: u.terbti || null, region: u.region || null, ts: u.ts }));
  const c = counts(store);
  const sorted = Object.entries(c).sort((a, b) => b[1] - a[1]);
  const rankIdx = sorted.findIndex(([cc]) => cc === code);
  return NextResponse.json({
    me: store.users[code] || null,
    invited,
    count: invited.length,
    rank: rankIdx >= 0 ? rankIdx + 1 : null,
    totalUsers: Object.keys(store.users).length,
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const code = clean(body.code);
  if (!code) return NextResponse.json({ error: "code 필요" }, { status: 400 });
  const invitedBy = clean(body.invitedBy);
  const store = read();
  const u: User = store.users[code] || { code, invitedBy: null, ts: Date.now() };
  if (body.terbti) u.terbti = String(body.terbti).slice(0, 16);
  if (body.region) u.region = String(body.region).slice(0, 40);
  if (!u.invitedBy && invitedBy && invitedBy !== code) u.invitedBy = invitedBy; // 초대자는 최초 1회만
  store.users[code] = u;
  write(store);
  return NextResponse.json({
    ok: true,
    count: Object.values(store.users).filter((x) => x.invitedBy === code).length,
    totalUsers: Object.keys(store.users).length,
  });
}
