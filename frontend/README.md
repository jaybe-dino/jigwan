# frontend/ — 지관 정식 프론트 (Next.js App Router)

M1 룰북 엔진을 그대로 소비하는 Next.js 프론트 스캐폴드. 판정·점수의 단일
진실원은 Python 엔진(`engine/`)이고, 프론트는 **렌더만** 한다.

## 구조

```
frontend/
├── app/
│   ├── page.tsx              # 홈: 주소 입력·예시
│   ├── report/page.tsx       # 서버 컴포넌트 — 요청 시 엔진 실행 후 리포트 렌더
│   ├── api/assess/route.ts   # GET /api/assess?address= → 엔진 JSON
│   └── globals.css           # 웹 프로토타입과 동일한 디자인 토큰
├── lib/
│   ├── types.ts              # 데이터 계약(= web/render.py shape_assessment 출력)
│   └── engine.ts             # 서버: engine_cli.py 호출 브리지
└── components/               # ScoreSeal · Gauge · RuleList · Report · AddressForm
```

## 데이터 흐름

```
브라우저 → /report?address=  (서버 컴포넌트)
   → lib/engine.ts  → child_process: python3 engine_cli.py <주소>
      → web.render.build_from_address → pipeline.assess_address_auto
         → 키 있으면 실 API 수집, 없으면 픽스처 폴백
   → SiteReport(JSON) → React 컴포넌트 렌더
```

## 실행

리포지토리 루트에서 `python3` 가 실행 가능해야 한다(엔진 호출).

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
npm run build        # 프로덕션 빌드
npm run typecheck    # 타입 검사
```

## 남은 것 (M2 후속)

- 카카오맵 JS SDK 지형 오버레이(현재는 프로토타입 `web/`의 Canvas 오버레이 참고)
- 궁합·매물비교·마이지관·이달의 기별 페이지 이관(계약은 `web/`에 구현 완료)
- 엔진을 CLI 대신 FastAPI 서비스로 분리(고동시성 대비)
