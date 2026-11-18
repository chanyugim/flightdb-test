-- 항공편 검색·좌석 선택·분석 시연용 가상 데이터임. 실제 운항편·운임이 아님.
-- MySQL 8.0에서 schema.sql과 seed_reference.sql 적용 후 실행함.
-- 출발 기간: 2026-11-12 ~ 2027-01-31, 모든 시각은 한국 표준시임.
-- 14편 × 81일 = 1,134편, 가상 좌석 총 191,808개를 추가함.
-- 지정한 일반 여객 공항만 사용하며 공항 전체에서 무작위 추출하지 않음.
-- 기존 항공편·좌석·예약을 수정하거나 삭제하지 않음.
-- 같은 항공사·출발/도착 공항·출발 시각이 있으면 해당 편을 건너뜀.
-- 관리자 계정 또는 CREATE TEMPORARY TABLES 권한이 있는 설치 계정으로 실행함.
-- 앱의 항공편 등록 작업을 중지한 상태에서 파일 전체를 한 연결에서 실행함.
-- 오류 발생 시 실행을 중단하고 ROLLBACK 후 연결을 종료함. 오류를 무시하고 계속 실행하지 않음.

USE airline_reservation;
SET NAMES utf8mb4;
SET time_zone = '+09:00';
SET @flight_demo_start = DATE('2026-11-12');
SET @flight_demo_end = DATE('2027-01-31');
SET @flight_demo_lock = GET_LOCK('airline_reservation.flight_demo_202611', 10);

DROP TEMPORARY TABLE IF EXISTS demo_flight_routes;
DROP TEMPORARY TABLE IF EXISTS demo_flight_stage;
DROP TEMPORARY TABLE IF EXISTS demo_flight_resolved;
DROP TEMPORARY TABLE IF EXISTS demo_flight_new;
DROP TEMPORARY TABLE IF EXISTS demo_flight_inserted;

CREATE TEMPORARY TABLE demo_flight_routes (
    route_no INT PRIMARY KEY,
    airline_code CHAR(2) NOT NULL,
    dep_code CHAR(3) NOT NULL,
    arr_code CHAR(3) NOT NULL,
    departure_time TIME NOT NULL,
    duration_minutes INT NOT NULL,
    price_floor INT NOT NULL,
    economy_only BOOLEAN NOT NULL
);

-- 김포·제주·인천·나리타·하네다·간사이·창이·수완나품·타오위안·홍콩·샤를드골 공항만 사용함.
-- 저비용 항공사 편은 이코노미 144석, 나머지는 기존 가상 배치인 176석을 사용함.
INSERT INTO demo_flight_routes VALUES
(1,'KE','GMP','CJU','07:40:00',70,65000,FALSE),
(2,'7C','GMP','CJU','10:10:00',70,39000,TRUE),
(3,'KE','CJU','GMP','20:20:00',70,60000,FALSE),
(4,'KE','ICN','NRT','09:10:00',150,190000,FALSE),
(5,'OZ','ICN','NRT','11:35:00',150,175000,FALSE),
(6,'LJ','ICN','NRT','14:20:00',150,110000,TRUE),
(7,'KE','NRT','ICN','18:20:00',160,180000,FALSE),
(8,'OZ','ICN','HND','08:25:00',140,210000,FALSE),
(9,'7C','ICN','KIX','10:45:00',110,95000,TRUE),
(10,'SQ','ICN','SIN','16:15:00',390,380000,FALSE),
(11,'KE','ICN','BKK','19:05:00',365,290000,FALSE),
(12,'OZ','ICN','TPE','12:30:00',170,155000,FALSE),
(13,'KE','ICN','HKG','13:50:00',240,230000,FALSE),
(14,'KE','ICN','CDG','09:50:00',850,780000,FALSE);

CREATE TEMPORARY TABLE demo_flight_stage AS
SELECT r.*,
       TIMESTAMP(DATE_ADD(@flight_demo_start, INTERVAL d.n DAY), r.departure_time) AS departure_at,
       TIMESTAMPADD(MINUTE, r.duration_minutes,
           TIMESTAMP(DATE_ADD(@flight_demo_start, INTERVAL d.n DAY), r.departure_time)) AS arrival_at,
       r.price_floor + MOD(d.n + r.route_no, 7) * 5000
           + CASE WHEN WEEKDAY(DATE_ADD(@flight_demo_start, INTERVAL d.n DAY)) >= 5
                  THEN 15000 ELSE 0 END AS base_price,
       CASE WHEN MOD(d.n * 14 + r.route_no, 47) = 0 THEN '결항'
            WHEN MOD(d.n * 14 + r.route_no, 17) = 0 THEN '지연'
            ELSE '예정' END AS flight_status
FROM demo_flight_routes r
CROSS JOIN (
    SELECT tens.n * 10 + ones.n AS n
    FROM (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
          UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
          UNION ALL SELECT 8) tens
    CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
          UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
          UNION ALL SELECT 8 UNION ALL SELECT 9) ones
) d
WHERE DATE_ADD(@flight_demo_start, INTERVAL d.n DAY) <= @flight_demo_end;

CREATE TEMPORARY TABLE demo_flight_resolved AS
SELECT x.*, a.airline_id, dep.airport_id AS departure_airport_id,
       arr.airport_id AS arrival_airport_id
FROM demo_flight_stage x
JOIN airline a ON a.iata_code = x.airline_code
JOIN airport dep ON dep.iata_code = x.dep_code
JOIN airport arr ON arr.iata_code = x.arr_code;

-- 참조 코드 하나라도 없으면 전체 추가를 생략하며 마지막 결과에서 원인을 표시함.
SET @flight_demo_expected = (SELECT COUNT(*) FROM demo_flight_stage);
SET @flight_demo_resolved = (SELECT COUNT(*) FROM demo_flight_resolved);
SET @flight_demo_ready = (@flight_demo_lock = 1
    AND @flight_demo_expected = 1134 AND @flight_demo_resolved = @flight_demo_expected);

START TRANSACTION;
CREATE TEMPORARY TABLE demo_flight_new AS
SELECT x.*
FROM demo_flight_resolved x
WHERE @flight_demo_ready = 1
  AND NOT EXISTS (
      SELECT 1 FROM flight f
      WHERE f.airline_id = x.airline_id
        AND f.departure_airport_id = x.departure_airport_id
        AND f.arrival_airport_id = x.arrival_airport_id
        AND f.departure_at = x.departure_at
  );

INSERT INTO flight (airline_id, departure_airport_id, arrival_airport_id,
                    flight_status, departure_at, arrival_at, base_price, remaining_seats)
SELECT airline_id, departure_airport_id, arrival_airport_id,
       flight_status, departure_at, arrival_at, base_price,
       CASE WHEN economy_only THEN 144 ELSE 176 END
FROM demo_flight_new
ORDER BY departure_at, route_no;
SET @flight_demo_added = ROW_COUNT();

CREATE TEMPORARY TABLE demo_flight_inserted AS
SELECT f.flight_id, x.economy_only
FROM demo_flight_new x
JOIN flight f ON f.airline_id = x.airline_id
    AND f.departure_airport_id = x.departure_airport_id
    AND f.arrival_airport_id = x.arrival_airport_id
    AND f.departure_at = x.departure_at;

-- 이번 실행에서 추가한 항공편의 좌석만 생성함.
INSERT INTO seat (flight_id, seat_no, seat_class, is_available)
SELECT f.flight_id, CONCAT(r.row_no, c.letter),
       CASE WHEN r.row_no <= 2 THEN '퍼스트'
            WHEN r.row_no <= 8 THEN '비즈니스' ELSE '이코노미' END,
       TRUE
FROM demo_flight_inserted f
CROSS JOIN (
    SELECT tens.n * 10 + ones.n AS row_no
    FROM (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) tens
    CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
          UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
          UNION ALL SELECT 8 UNION ALL SELECT 9) ones
) r
CROSS JOIN (SELECT 'A' letter UNION ALL SELECT 'B' UNION ALL SELECT 'C'
            UNION ALL SELECT 'D' UNION ALL SELECT 'E' UNION ALL SELECT 'F') c
WHERE (r.row_no BETWEEN 10 AND 33)
   OR (f.economy_only = FALSE AND r.row_no BETWEEN 1 AND 8 AND c.letter IN ('A','B','C','D'));
SET @flight_demo_seats_added = ROW_COUNT();
COMMIT;

SELECT CASE WHEN @flight_demo_lock IS NULL OR @flight_demo_lock <> 1 THEN '잠금을 얻지 못해 추가하지 않음'
            WHEN @flight_demo_ready <> 1 THEN '참조 공항/항공사 또는 생성 건수 확인이 필요함'
            ELSE '완료' END AS result,
       @flight_demo_expected AS planned_flights,
       @flight_demo_resolved AS resolved_flights,
       @flight_demo_added AS added_flights,
       @flight_demo_seats_added AS added_seats;

SELECT f.flight_status, COUNT(*) AS added_flights,
       MIN(f.base_price) AS min_price, MAX(f.base_price) AS max_price
FROM demo_flight_inserted x JOIN flight f ON f.flight_id = x.flight_id
GROUP BY f.flight_status;

DO RELEASE_LOCK('airline_reservation.flight_demo_202611');
DROP TEMPORARY TABLE demo_flight_inserted;
DROP TEMPORARY TABLE demo_flight_new;
DROP TEMPORARY TABLE demo_flight_resolved;
DROP TEMPORARY TABLE demo_flight_stage;
DROP TEMPORARY TABLE demo_flight_routes;
