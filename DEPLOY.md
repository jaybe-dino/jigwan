# 배포 가이드

목표: **서버 한 곳에 통째로 올리고, API 키는 그 서버 대시보드(환경변수)로 관리.**
로컬에 `.env` 만들 필요 없음.

우리 앱은 웹(Next.js) + 풍수 엔진(Python)이 한 몸이라 **Node·Python 둘 다 되는 호스팅**이
필요하다(Vercel/Netlify 같은 서버리스는 Python이 안 돌아 부적합). 그래서 **Docker 한 컨테이너**로
묶어서 **Railway**(권장) 또는 Render/Fly.io에 올린다. 리포지토리 루트의 `Dockerfile`이 그 설정이다.

---

## A. Railway — 추천 (제일 간단, 키 대시보드 관리)

1. https://railway.app → **New Project → Deploy from GitHub repo** → `jaybe-dino/jigwan`
2. 브랜치를 배포 브랜치로 지정 (예: `claude/m1-implementation-plan-l9qhqv` 또는 main 머지 후 main)
3. Railway가 루트 **`Dockerfile`을 자동 감지**해서 빌드 (Node+Python 이미지, 프론트 빌드 포함)
4. **Variables 탭**에서 키 등록 (← 여기서 키 관리, 코드엔 안 들어감):
   ```
   KAKAO_REST_KEY = 카카오_REST_키
   VWORLD_KEY     = 브이월드_인증키
   DATA_GO_KR_KEY = 공공데이터포털_키   (선택: 건축물대장·실거래가)
   ```
5. **Settings → Networking → Generate Domain** → `https://jigwan-production.up.railway.app` 발급
6. 끝. 그 URL이 곧 서비스 URL이자 웹사이트.

- 키를 나중에 바꾸면 Variables만 수정 → 재배포. 코드 수정 없음.
- 키가 비어 있어도 앱은 뜬다(데모 픽스처로 폴백). 키를 채우면 자동으로 실 API 감정으로 전환.

## B. Render — 대안

1. https://render.com → **New → Web Service** → GitHub 저장소 연결
2. Environment: **Docker** (루트 Dockerfile 자동 사용)
3. **Environment 탭**에서 위와 동일하게 `KAKAO_REST_KEY`·`VWORLD_KEY` 등록
4. Create → `https://jigwan.onrender.com` 발급

## C. Fly.io — 대안

`fly launch` (Dockerfile 감지) → `fly secrets set VWORLD_KEY=... KAKAO_REST_KEY=...` → `fly deploy`

---

## V-World 서비스URL은?

- 위에서 발급된 도메인(예: `https://jigwan-production.up.railway.app`)을 V-World 신청서
  **서비스URL**에 넣으면 된다.
- 아직 배포 전이라 URL이 없다면: V-World 신청 시 임시로 이 도메인을 예정 값으로 적어도 되고,
  배포 후 마이페이지에서 URL/도메인을 수정할 수 있다.

### V-World 신청서 요약

| 항목 | 값 |
|---|---|
| 서비스명 | 지관 |
| 서비스분류 | 교육(무방) · 서비스유형 웹사이트 |
| 서비스URL | 배포 도메인 |
| 활용 API | 2D데이터 · WMS/WFS · 배경지도 · 2D지도 · 지오코더 · 검색 |
| 사용기관 | 민간 + 회사/개인명 |

---

## 키만 빨리 받고 싶고, URL만 있으면 될 때 (엔진 없이)

정적 프로토타입(`web/dist/index.html`)만 어디든 올려 URL을 먼저 확보해도 된다.
- **Netlify drop**: `web/dist` 폴더를 https://app.netlify.com/drop 에 드래그 → 즉시 URL
- 단, 이건 데모 화면만 뜨고 실주소 감정은 안 된다(엔진 미포함). 키 발급용 URL 확보 목적.

---

## 아키텍처 메모

```
브라우저 → Next.js(/report) → child_process → python3 engine_cli.py
   → pipeline.assess_address_auto
       → 환경변수 키 있으면 카카오·브이월드 실 API 수집
       → 없으면 픽스처 폴백
   → 룰북 엔진 판정 → SSR 리포트
```
키 주입 지점은 **호스팅 환경변수 → process.env → (child) os.environ → pipeline.config**.
즉 대시보드에 키를 넣으면 자동으로 실 API가 켜진다.

트래픽이 커지면 엔진을 별도 FastAPI 서비스로 분리(`engine_cli` → HTTP)하는 것을 권장.
