# 지관(智官) — AI 풍수지리 서비스

> 주소를 넣으면 AI가 실제 지형·도로·건물 데이터로 그 터의 풍수지리를 감정해주는 모바일 웹 서비스.
>
> *"숫자는 다 보셨잖아요. 이제 터를 보세요."*

기획안: [`docs/planning-v1.md`](docs/planning-v1.md) · 룰북: [`docs/rulebook-v1.md`](docs/rulebook-v1.md)

---

## 현재 단계: M1

M1 = **룰북 v1 상세화**(판정식·근거문 템플릿) + **데이터 파이프라인**(DEM·도로망·건축물대장 수집, PostGIS 연산 검증).

이 저장소의 M1 산출물:

| 구성 | 위치 | 설명 |
|---|---|---|
| 룰북 v1 명세 | `docs/rulebook-v1.md` | 10개 터 요소 + 궁합의 판정식·배점·근거문 템플릿 |
| 판정 엔진 | `engine/` | 구조화 피처 → 요소별 점수 + 근거 문장 자동 생성 |
| 데이터 파이프라인 | `pipeline/` | 수집기 인터페이스 + PostGIS 스키마 + 공간연산 |
| 검증 테스트 | `tests/` | 판정 로직·점수 집계·공간연산 검증 (픽스처 기반) |
| 터 리포트 UI | `web/` | 엔진 출력을 구동하는 모바일/PC 웹 프로토타입(전 화면) |
| 정식 프론트 | `frontend/` | Next.js(App Router) — 엔진 API 브리지로 SSR 리포트 |
| 실주소 수집기 | `pipeline/collectors/` | 카카오·브이월드·건축물대장(키 있으면 실 API, 없으면 픽스처) |

### 설계 원칙 (기획안 §4)

- **모든 판정은 숫자가 박힌 근거 문장을 자동 생성한다.**
  예: `"북서 380m, +42m 능선이 등을 받칩니다 — 현무가 든든한 형국"`
- **LLM은 점수를 매기지 않는다.** 룰북(엔진)이 판정·점수를 확정하고,
  LLM은 구조화 JSON을 받아 자연어 리포트만 생성한다 (일관성·신뢰성).
- 터 점수(객관 지형)와 궁합%(개인 사주)는 **독립 축**.

---

## 빠른 시작

```bash
# 1. 엔진 데모 — 샘플 터를 감정하고 근거 문장을 출력
python3 -m engine.demo

# 2. 테스트 (순수 파이썬, 의존성 없음)
python3 -m pytest tests/ -v          # pytest가 있으면
python3 tests/run.py                 # 없으면 내장 러너

# 3. 터 리포트 UI — 엔진 출력으로 구동되는 모바일 웹 프로토타입
python3 -m web.render                 # web/dist/index.html 생성 → 브라우저로 열기

# 4. PostGIS 파이프라인 (선택 — Docker 필요)
docker compose up -d db
psql "$JIGWAN_DATABASE_URL" -f pipeline/db/schema.sql -f pipeline/db/spatial.sql
python3 -m pipeline.validate          # 공간연산 py↔PostGIS 정합성 검증
```

## 아키텍처 (기획안 §10)

```
[수집기]  DEM · 도로망 · 하천망 · 건축물대장 · POI
   │  (외부 공공 API / 픽스처)
   ▼
[파이프라인]  PostGIS 공간연산 → 구조화 피처(SiteFeatures)
   │  부채꼴 고도 프로파일 · 도로 각도/곡률 · 버퍼
   ▼
[판정 엔진]  룰북 v1 → 요소별 RuleResult(점수 + 근거문)
   │
   ▼
[스코어링]  터 점수(100점) · 등급 · 4축 게이지
   │
   ▼
[LLM]  구조화 JSON → 자연어 리포트 (M2~)
```

M1은 위 파이프라인 중 **수집기 인터페이스 → 판정 엔진 → 스코어링**까지를
픽스처로 검증 가능한 형태로 완성한다. 실제 공공 API 연동과 프론트(S1~S4)는 M2다.
