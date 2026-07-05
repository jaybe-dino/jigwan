// 서버 전용 — 리포지토리 루트의 engine_cli.py 를 호출해 감정 결과를 받는다.
// 판정·점수의 단일 진실원은 Python 룰북 엔진(engine/). 프론트는 렌더만 한다.
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import type { SiteReport } from "./types";

const pexec = promisify(execFile);
// frontend/ 의 상위(리포지토리 루트)에서 python 실행
const REPO_ROOT = path.join(process.cwd(), "..");

async function run(args: string[]): Promise<SiteReport> {
  const { stdout } = await pexec("python3", ["engine_cli.py", ...args], {
    cwd: REPO_ROOT,
    maxBuffer: 8 * 1024 * 1024,
    env: process.env,
  });
  const data = JSON.parse(stdout);
  if (data && data.error) throw new Error(data.error);
  return data as SiteReport;
}

export function assessAddress(address: string): Promise<SiteReport> {
  return run([address]);
}

export function assessCoord(lat: number, lon: number): Promise<SiteReport> {
  return run(["--coord", String(lat), String(lon)]);
}
