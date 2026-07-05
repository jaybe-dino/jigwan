"""지관 데이터 파이프라인 (M1).

외부 공공 데이터(DEM·도로망·하천망·건축물대장·POI) 수집 → PostGIS 공간연산
→ 판정 엔진 입력(SiteFeatures) 조립.

M1 범위:
- 수집기 인터페이스(collectors) + 픽스처 구현
- PostGIS 스키마(db/schema.sql) + 공간연산(spatial)
- 공간연산 검증(validate.py): 순수 파이썬 엔진 결과 ↔ PostGIS 결과 정합성
"""
