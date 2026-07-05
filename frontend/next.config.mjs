/** @type {import('next').NextConfig} */
const nextConfig = {
  // 엔진(Python)은 리포지토리 루트에서 호출하므로 프로젝트 루트를 상위로 인식
  outputFileTracingRoot: process.cwd() + "/..",
};

export default nextConfig;
