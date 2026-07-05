"""공간연산 — PostGIS 실행부(postgis)와 순수 파이썬 기준(engine.geo)의 정합성 계층.

판정에 쓰는 공간연산의 '단일 진실원'은 engine.geo 이며, PostGIS는 대량 배치·
색인 성능을 위한 동일 연산의 구현이다. validate 로 두 결과의 일치를 검증한다.
"""
