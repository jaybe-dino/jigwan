/** @type {import('next').NextConfig} */
const nextConfig = {
  // 엔진(Python)은 리포지토리 루트에서 호출하므로 프로젝트 루트를 상위로 인식
  outputFileTracingRoot: process.cwd() + "/..",
  // '/'에서 전체 프로토타입(public/index.html)을 서빙. /api·/report는 그대로.
  async rewrites() {
    return [{ source: "/", destination: "/index.html" }];
  },
};

export default nextConfig;
