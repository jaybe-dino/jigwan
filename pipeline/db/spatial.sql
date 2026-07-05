-- 지관 PostGIS 공간연산 함수 (M1) — 기획안 §10 "부채꼴 고도 프로파일·도로 각도/곡률·버퍼"
-- 판정 엔진(engine.geo)의 순수 파이썬 연산과 동일한 결과를 내야 한다.
-- 정합성은 pipeline/validate.py 및 tests/test_spatial.py에서 교차 검증.
--
--   psql "$JIGWAN_DATABASE_URL" -f pipeline/db/spatial.sql

-- 두 방위각(도)의 최소차(0~180). (% 연산자는 double precision에 없어 floor 사용)
CREATE OR REPLACE FUNCTION jigwan_angle_diff(x double precision, y double precision)
RETURNS double precision LANGUAGE sql IMMUTABLE AS $$
  SELECT LEAST(d, 360 - d)
  FROM (SELECT abs(x - y) - floor(abs(x - y) / 360) * 360 AS d) t;
$$;

-- 배면/사신사 부채꼴 최대 고도차 (버퍼 + 방위각 부채꼴 + 고도차)
--   origin: 건물점(4326), ground: 기준고도, center_deg: 부채꼴 중심방위,
--   half_deg: 반각, r_min/r_max: 반경(m)
CREATE OR REPLACE FUNCTION jigwan_sector_max_gain(
    origin geometry, ground double precision,
    center_deg double precision, half_deg double precision,
    r_min double precision, r_max double precision)
RETURNS TABLE(max_gain double precision, dist_m double precision, azimuth_deg double precision)
LANGUAGE sql STABLE AS $$
  SELECT d.elev_m - ground AS max_gain,
         ST_Distance(origin::geography, d.geom::geography) AS dist_m,
         degrees(ST_Azimuth(origin, d.geom)) AS azimuth_deg
  FROM dem_point d
  WHERE ST_DWithin(origin::geography, d.geom::geography, r_max)              -- 버퍼(r_max)
    AND ST_Distance(origin::geography, d.geom::geography) >= r_min
    AND jigwan_angle_diff(degrees(ST_Azimuth(origin, d.geom)), center_deg)   -- 부채꼴
        <= half_deg
    AND d.elev_m - ground > 0
  ORDER BY d.elev_m - ground DESC
  LIMIT 1;
$$;

-- 반경 내 최근접 하천까지 수선거리(m)와 하천 id (버퍼 + 최근접)
CREATE OR REPLACE FUNCTION jigwan_nearest_stream(origin geometry, r_max double precision)
RETURNS TABLE(stream_id bigint, dist_m double precision)
LANGUAGE sql STABLE AS $$
  SELECT s.id, ST_Distance(origin::geography, s.geom::geography) AS dist_m
  FROM stream s
  WHERE ST_DWithin(origin::geography, s.geom::geography, r_max)
  ORDER BY dist_m ASC
  LIMIT 1;
$$;

-- 반경 내 POI를 카테고리별 거리감쇠 가중합 (R10 순수파이썬과 동일 식)
--   부호·가중·반경은 애플리케이션(engine.rulebook.r10_poi)에서 주입한다.
--   여기서는 거리만 계산해 돌려주고 가중은 파이썬에서 적용(단일 진실원 유지).
CREATE OR REPLACE FUNCTION jigwan_pois_within(origin geometry, r_max double precision)
RETURNS TABLE(poi_id bigint, category text, name text, dist_m double precision)
LANGUAGE sql STABLE AS $$
  SELECT p.id, p.category, p.name,
         ST_Distance(origin::geography, p.geom::geography) AS dist_m
  FROM poi p
  WHERE ST_DWithin(origin::geography, p.geom::geography, r_max)
  ORDER BY dist_m ASC;
$$;

-- 폴리라인 정점에서의 접근 방위각(도) — 도로 각도 해석용
CREATE OR REPLACE FUNCTION jigwan_segment_azimuth(line geometry, i integer)
RETURNS double precision LANGUAGE sql IMMUTABLE AS $$
  SELECT degrees(ST_Azimuth(ST_PointN(line, i), ST_PointN(line, i + 1)));
$$;

-- 현재 필지가 과거 지목 폴리곤과 겹치는지 (R04)
CREATE OR REPLACE FUNCTION jigwan_historical_types(origin geometry)
RETURNS TABLE(past_type text) LANGUAGE sql STABLE AS $$
  SELECT DISTINCT h.past_type
  FROM historical_land h
  WHERE ST_Intersects(h.geom, origin);
$$;
