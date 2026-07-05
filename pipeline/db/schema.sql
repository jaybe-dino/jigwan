-- 지관 PostGIS 스키마 (M1) — 기획안 §10 데이터 모델
-- 좌표계: 저장은 WGS84(EPSG:4326), 거리·각도 연산은 UTM-K(EPSG:5179)로 변환해 수행.
--
--   psql "$JIGWAN_DATABASE_URL" -f pipeline/db/schema.sql

CREATE EXTENSION IF NOT EXISTS postgis;

-- ---------------------------------------------------------------------------
-- 원천 공간 데이터 (수집기가 적재)
-- ---------------------------------------------------------------------------

-- DEM 5m 고도 샘플점 (국토지리정보원)
CREATE TABLE IF NOT EXISTS dem_point (
    id       bigserial PRIMARY KEY,
    geom     geometry(Point, 4326) NOT NULL,
    elev_m   double precision NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dem_point_geom ON dem_point USING gist (geom);

-- 하천 중심선 (하천망도/WAMIS)
CREATE TABLE IF NOT EXISTS stream (
    id       bigserial PRIMARY KEY,
    name     text,
    width_m  double precision,
    geom     geometry(LineString, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stream_geom ON stream USING gist (geom);

-- 도로 중심선 (도로명주소 전자지도)
CREATE TABLE IF NOT EXISTS road (
    id         bigserial PRIMARY KEY,
    name       text,
    width_m    double precision NOT NULL DEFAULT 6,
    is_dead_end boolean NOT NULL DEFAULT false,
    is_t_head  boolean NOT NULL DEFAULT false,
    geom       geometry(LineString, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_road_geom ON road USING gist (geom);

-- 고가·철로
CREATE TABLE IF NOT EXISTS rail_overpass (
    id            bigserial PRIMARY KEY,
    kind          text NOT NULL CHECK (kind IN ('rail','overpass')),
    height_diff_m double precision NOT NULL DEFAULT 0,
    geom          geometry(LineString, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rail_overpass_geom ON rail_overpass USING gist (geom);

-- POI (카카오 로컬)
CREATE TABLE IF NOT EXISTS poi (
    id        bigserial PRIMARY KEY,
    category  text NOT NULL,   -- engine.rulebook.r10_poi.CATEGORY_WEIGHTS 키
    name      text,
    geom      geometry(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_poi_geom ON poi USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_poi_category ON poi (category);

-- 과거 지목 폴리곤 (국토정보플랫폼 옛 지형도)
CREATE TABLE IF NOT EXISTS historical_land (
    id        bigserial PRIMARY KEY,
    past_type text NOT NULL,   -- 하천/구하도/논/습지/매립 ...
    geom      geometry(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_historical_land_geom ON historical_land USING gist (geom);

-- ---------------------------------------------------------------------------
-- 도메인 테이블 (기획안 §10)
-- ---------------------------------------------------------------------------

-- 감정 대상 건물/터 (분석 결과 캐시 = 풍수 DB 자산)
CREATE TABLE IF NOT EXISTS site (
    id             bigserial PRIMARY KEY,
    address        text NOT NULL,
    building_id    text,                       -- 건축물대장 PK
    geom           geometry(Point, 4326) NOT NULL,
    facing_deg     double precision,           -- 좌향(향) 방위각
    ground_elev_m  double precision,
    floors         integer,
    features_json  jsonb,                       -- 조립된 SiteFeatures 스냅샷
    site_score     integer,
    grade          text,
    engine_version text,
    cached_at      timestamptz DEFAULT now(),
    UNIQUE (address)
);
CREATE INDEX IF NOT EXISTS idx_site_geom ON site USING gist (geom);

-- 조회 로그 (히트맵용 비식별 집계 — 기획안 §11)
CREATE TABLE IF NOT EXISTS query_log (
    id        bigserial PRIMARY KEY,
    dong_code text,             -- 행정동 코드 (개인 식별 금지)
    queried_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_query_log_dong ON query_log (dong_code);
