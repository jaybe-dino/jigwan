# 배포 가이드 — URL 발급 & V-World 신청

## 요약: 순서

1. **정적 프로토타입(`web/dist`)을 먼저 배포** → 서비스URL 확보 (5분)
2. 그 URL로 **V-World 인증키 신청**
3. 발급받은 키를 `.env`/호스팅 환경변수에 넣기 (`VWORLD_KEY`, `KAKAO_REST_KEY`)
4. (나중에) 엔진이 붙는 정식 앱(`frontend/`)은 별도 호스팅

---

## 1. URL 먼저 — 정적 프로토타입 배포

> ⚠️ **중요**: `frontend/`(Next.js)는 서버에서 Python 엔진을 `child_process`로
> 실행한다. **Vercel 서버리스에서는 Python 실행이 안 되므로** 정식 앱은 Vercel에
> 그대로 못 올린다. 반면 `web/dist/index.html`은 **의존성 없는 정적 파일**이라
> 어디든 바로 올라간다. V-World 신청용 URL은 이걸로 만드는 게 가장 빠르다.

### 방법 A — Vercel (이 저장소 그대로)

리포지토리 루트의 `vercel.json`이 정적 프로토타입만 배포하도록 설정돼 있다.

1. https://vercel.com → **Add New → Project** → 이 GitHub 저장소 import
2. Framework Preset: **Other** (vercel.json이 자동 적용)
3. Deploy → `https://<프로젝트>.vercel.app` 발급
   - 빌드: `python3 -m web.render` → `web/dist` 를 서빙 (Vercel 빌드 이미지에 python 포함)

### 방법 B — Netlify 드래그앤드롭 (설정 0)

`web/dist` 폴더를 https://app.netlify.com/drop 에 끌어다 놓으면 즉시 URL.

### 방법 C — GitHub Pages

`web/dist`를 gh-pages로 배포. (Actions 또는 수동)

→ 어느 방법이든 나온 URL을 V-World 서비스URL에 넣으면 된다.

---

## 2. V-World 인증키 신청 폼 작성

https://www.vworld.kr → 오픈API → 인증키 발급신청

| 항목 | 입력 |
|---|---|
| 서비스명 | 지관 |
| 서비스분류 | 교육 (또는 생활·기타 — 큰 영향 없음) |
| 서비스유형 | **웹사이트** ✓ |
| 서비스URL | 1단계에서 발급한 URL (예: `https://jigwan.vercel.app`) |
| 서비스설명 | 개요/대상/목적 (아래 예시) |
| 활용 API | **2D 지도 API · 배경지도 API · WMS/WFS API · 2D데이터 API · 지오코더 API · 검색 API** 체크 |
| 사용기관 | 민간 + 회사/개인명 |
| 활용사례공개 | 선택 |

**서비스설명 예시**
```
- 개요 : 주소 입력 시 지형·도로·건물 공간데이터로 풍수지리를 감정하는 웹 서비스
- 서비스대상 : 이사·매수를 앞둔 일반 사용자
- 목적 : 도로·하천·건물 배치 데이터를 활용한 터의 형기·좌향 분석 및 시각화
```

> **활용 API 매핑** (우리 파이프라인 기준)
> - `2D데이터 API` = WFS GetFeature → 도로·하천·건물 폴리곤 (`pipeline/collectors/vworld.py`)
> - `지오코더 API` = 주소→좌표 (현재는 카카오 사용, V-World로도 대체 가능)
> - `2D 지도 API`·`배경지도 API` = 지도 타일(프론트 표시용)

---

## 3. 발급 키를 코드에 넣기

`.env.example`을 `.env`로 복사 후 채운다. (`.env`는 커밋 금지 — `.gitignore` 처리됨)

```bash
KAKAO_REST_KEY=발급받은_카카오_REST_키
VWORLD_KEY=발급받은_브이월드_인증키
DATA_GO_KR_KEY=공공데이터포털_키   # 건축물대장·실거래가(선택)
```

- 키가 있으면 `pipeline/collectors/factory.py`가 **자동으로 실 API 수집기**로 전환.
- 키가 없으면 픽스처(데모 샘플)로 폴백하므로, 지금도 앱은 돈다.
- 호스팅(Vercel/Railway 등)에서는 이 값들을 **환경변수**로 등록.

---

## 4. 정식 앱(엔진 포함) 호스팅 — 나중 단계

`frontend/`(Next.js)는 요청 시 Python 엔진을 실행한다. Vercel 서버리스에선 불가하므로:

- **권장**: 엔진을 `FastAPI` 서비스로 분리해 **Railway / Render / Fly.io**에 배포
  (Python 런타임 지원). `frontend/lib/engine.ts`의 `child_process` 호출을 그 API
  `fetch`로 바꾸면 프론트는 Vercel, 엔진은 Railway로 분리 가능.
- 지금 단계에선 1~3만으로 V-World 키 발급 + 데모 URL 확보가 목적.
