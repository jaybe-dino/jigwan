# 지관 단일 컨테이너 — Next.js(웹) + Python(풍수 엔진) 한 서버.
# Railway / Render / Fly.io 등 Docker 지원 호스팅에 그대로 배포.
# API 키는 코드가 아니라 호스팅 대시보드의 "환경변수"로 주입한다(KAKAO_REST_KEY, VWORLD_KEY ...).

FROM node:20-bookworm-slim

# 풍수 엔진용 Python (표준 라이브러리만 사용 → pip 설치 불필요)
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && ln -sf /usr/bin/python3 /usr/local/bin/python3 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 프론트 빌드
WORKDIR /app/frontend
RUN npm ci && npm run build

ENV NODE_ENV=production
# Railway/Render가 PORT 환경변수를 주입 → next start가 자동 사용
EXPOSE 3000
CMD ["npm", "start"]
