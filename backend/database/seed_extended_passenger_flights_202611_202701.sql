-- ===========================================================================
-- 한국 출·도착 확장형 가상 여객 항공편 + 좌석 시드 / MySQL 8.0+
-- 실제 운항편, 기종, 운임이 아닌 검색·예약 기능 테스트를 위한 가상 데이터.
--
-- 선행: schema.sql 및 업로드된 seed_reference(1).sql 적용.
-- 업로드된 seed_demo(1).sql, seed_flights_202611_202701.sql과 병행 가능.
-- 사용 테이블: airline, airport, flight, seat. 예약/회원/프로모션은 변경하지 않음.
-- 기본 기간: 2026-11-17 ~ 2027-01-31 (76일).
-- 140개 노선, 항공편 7,823건, 좌석 1,292,048석 (중복편이 없을 때).
-- 국가·지역 42곳 (참조 airport.country 기준), 항공사 34개 코드 사용.
-- 실행 전에 반드시 DB 백업; 대용량이므로 테스트 DB에서 사용 권장.
-- 파일 전체를 한 MySQL 연결로 실행하며 항공편 추가 앱 작업은 중지할 것.
-- 실행 도중 SQL 오류 시 즉시 중단, ROLLBACK 후 연결을 종료할 것.
-- 이미 존재하는 동일 항공사/출발지/도착지/출발시각 편은 건너뜀.
-- 해당 기존 편의 좌석·예약·요금·상태를 덮어쓰지 않음.
-- 참조 공항 또는 항공사 미등록 시 전체 삽입을 건너뛰고 오류 코드를 표시.
--
-- 좌석 모델: E=이코노미 10~33열 A~F (144석)
--            M=퍼스트 1~2열 A~D(8), 비즈니스 3~8열 A~D(24),
--              이코노미 10~33열 A~F(144), 합계 176석.
-- 모든 신규 좌석은 예약 기록이 없으므로 is_available=TRUE.
-- 모든 출발/도착 시각은 한국시간 KST(+09:00) 기준으로 통일.
-- 요일 마스크는 월~일, 1=운항, 0=미운항.
-- ===========================================================================
USE airline_reservation;
SET NAMES utf8mb4;
SET time_zone = '+09:00';

-- 기간 변경 가능(양끝 포함 최대 181일). 작은 시드가 필요하면 종료일을 줄이세요.
SET @ext_start = DATE('2026-11-17');
SET @ext_end = DATE('2027-01-31');
SET @ext_lock = GET_LOCK('airline_reservation.extended_passenger_seed_v1', 15);

DROP TEMPORARY TABLE IF EXISTS ext_passenger_routes;
DROP TEMPORARY TABLE IF EXISTS ext_passenger_dates;
DROP TEMPORARY TABLE IF EXISTS ext_passenger_stage;
DROP TEMPORARY TABLE IF EXISTS ext_passenger_resolved;
DROP TEMPORARY TABLE IF EXISTS ext_passenger_new;
DROP TEMPORARY TABLE IF EXISTS ext_passenger_inserted;

CREATE TEMPORARY TABLE ext_passenger_routes (
 route_no INT PRIMARY KEY,
 airline_code CHAR(2) NOT NULL,
 dep_code CHAR(3) NOT NULL,
 arr_code CHAR(3) NOT NULL,
 departure_time TIME NOT NULL,
 duration_minutes INT NOT NULL,
 price_floor INT NOT NULL,
 cabin_mode CHAR(1) NOT NULL,
 weekday_mask CHAR(7) NOT NULL
);

INSERT INTO ext_passenger_routes
(route_no,airline_code,dep_code,arr_code,departure_time,duration_minutes,
 price_floor,cabin_mode,weekday_mask) VALUES
    -- 국내
    (1,'KE','GMP','CJU','06:30:00',70,68000,'M','1111111'),
    (2,'OZ','CJU','GMP','19:20:00',70,68000,'M','1111111'),
    (3,'BX','PUS','CJU','08:30:00',60,45000,'E','1111111'),
    (4,'BX','CJU','PUS','18:40:00',60,45000,'E','1111111'),
    (5,'LJ','GMP','PUS','09:30:00',55,62000,'E','1111111'),
    (6,'KE','PUS','GMP','20:10:00',55,65000,'M','1111111'),
    (7,'7C','CJJ','CJU','11:00:00',65,39000,'E','1111111'),
    (8,'7C','CJU','CJJ','16:20:00',65,39000,'E','1111111'),
    (9,'LJ','TAE','CJU','08:50:00',65,49000,'E','1010101'),
    (10,'LJ','CJU','TAE','17:20:00',65,48000,'E','1010101'),
    -- 일본
    (11,'KE','ICN','NRT','07:45:00',150,220000,'M','1111111'),
    (12,'JL','NRT','ICN','18:10:00',160,205000,'M','1111111'),
    (13,'NH','GMP','HND','08:00:00',135,240000,'M','1111111'),
    (14,'KE','HND','GMP','19:30:00',145,225000,'M','1111111'),
    (15,'7C','PUS','KIX','09:15:00',95,120000,'E','1111111'),
    (16,'BX','KIX','PUS','18:00:00',100,115000,'E','1111111'),
    (17,'LJ','ICN','FUK','07:20:00',90,105000,'E','1111111'),
    (18,'LJ','FUK','ICN','17:40:00',95,105000,'E','1111111'),
    (19,'KE','ICN','CTS','09:25:00',165,210000,'M','1111111'),
    (20,'7C','ICN','OKA','11:00:00',155,135000,'E','1111111'),
    (21,'BX','PUS','NRT','09:10:00',125,145000,'E','1111111'),
    (22,'BX','NRT','PUS','18:15:00',135,145000,'E','1111111'),
    (23,'7C','CJJ','KIX','13:05:00',110,105000,'E','1010101'),
    (24,'7C','TAE','FUK','10:25:00',90,99000,'E','0101010'),
    (25,'KE','ICN','NGO','11:40:00',120,190000,'M','1010101'),
    -- 중국
    (26,'KE','ICN','PVG','08:20:00',125,180000,'M','1111111'),
    (27,'MU','PVG','ICN','19:15:00',125,170000,'M','1111111'),
    (28,'OZ','GMP','SHA','09:55:00',120,210000,'M','1111111'),
    (29,'MU','SHA','GMP','17:40:00',130,190000,'M','1111111'),
    (30,'KE','ICN','PEK','10:15:00',125,225000,'M','1111111'),
    (31,'MU','ICN','TAO','12:10:00',100,165000,'M','1111111'),
    (32,'7C','PUS','TAO','11:05:00',115,119000,'E','1010101'),
    (33,'7C','TAE','YNJ','10:05:00',165,145000,'E','0010010'),
    (34,'OZ','ICN','CAN','08:00:00',215,250000,'M','1111111'),
    (35,'KE','ICN','SZX','09:25:00',210,250000,'M','0101010'),
    (36,'LJ','CJJ','PVG','13:05:00',140,125000,'E','1010101'),
    (37,'KE','ICN','DLC','07:55:00',105,175000,'M','1010101'),
    (38,'OZ','ICN','HGH','15:15:00',135,190000,'M','1010101'),
    -- 대만·홍콩·마카오
    (39,'KE','ICN','TPE','11:20:00',165,185000,'M','1111111'),
    (40,'CI','TPE','ICN','17:45:00',175,185000,'M','1111111'),
    (41,'7C','PUS','TPE','12:20:00',150,135000,'E','1111111'),
    (42,'BX','TPE','PUS','19:10:00',165,130000,'E','1111111'),
    (43,'7C','ICN','KHH','14:05:00',180,145000,'E','0101010'),
    (44,'CX','ICN','HKG','09:30:00',230,260000,'M','1111111'),
    (45,'KE','HKG','ICN','19:45:00',220,255000,'M','1111111'),
    (46,'7C','CJU','HKG','14:35:00',220,145000,'E','0101010'),
    (47,'LJ','ICN','MFM','13:50:00',235,145000,'E','0010010'),
    -- 몽골
    (48,'OM','ICN','UBN','10:35:00',215,255000,'M','1010101'),
    (49,'KE','UBN','ICN','18:15:00',205,250000,'M','1010101'),
    -- 베트남
    (50,'KE','ICN','HAN','08:15:00',285,290000,'M','1111111'),
    (51,'VN','HAN','ICN','23:05:00',265,275000,'M','1111111'),
    (52,'LJ','ICN','DAD','18:00:00',290,145000,'E','1111111'),
    (53,'7C','PUS','DAD','20:00:00',270,135000,'E','1111111'),
    (54,'VJ','DAD','PUS','23:40:00',270,135000,'E','0101010'),
    (55,'KE','ICN','SGN','17:10:00',330,300000,'M','1111111'),
    (56,'VN','SGN','ICN','22:40:00',310,290000,'M','1111111'),
    (57,'7C','CJJ','CXR','19:25:00',320,140000,'E','0101010'),
    (58,'LJ','ICN','PQC','19:50:00',340,155000,'E','1010101'),
    -- 태국
    (59,'TG','ICN','BKK','10:30:00',345,325000,'M','1111111'),
    (60,'KE','BKK','ICN','23:10:00',335,310000,'M','1111111'),
    (61,'7C','PUS','BKK','18:20:00',360,180000,'E','1111111'),
    (62,'LJ','ICN','HKT','19:15:00',375,195000,'E','1010101'),
    (63,'7C','ICN','CNX','17:30:00',335,180000,'E','0101010'),
    -- 필리핀
    (64,'PR','ICN','MNL','08:50:00',255,260000,'M','1111111'),
    (65,'5J','MNL','ICN','19:05:00',245,155000,'E','1111111'),
    (66,'7C','PUS','CEB','21:00:00',260,155000,'E','1111111'),
    (67,'LJ','ICN','CRK','20:20:00',245,135000,'E','0101010'),
    -- 싱가포르
    (68,'SQ','ICN','SIN','09:30:00',390,390000,'M','1111111'),
    (69,'SQ','SIN','ICN','23:20:00',390,380000,'M','1111111'),
    -- 말레이시아
    (70,'D7','ICN','KUL','19:40:00',390,245000,'E','1111111'),
    (71,'MH','KUL','ICN','23:45:00',395,345000,'M','1111111'),
    (72,'7C','PUS','BKI','18:25:00',330,175000,'E','1010101'),
    -- 인도네시아
    (73,'KE','ICN','CGK','15:35:00',420,390000,'M','1111111'),
    (74,'GA','CGK','ICN','22:10:00',420,390000,'M','1010101'),
    (75,'7C','ICN','DPS','18:10:00',450,245000,'E','1010101'),
    (76,'GA','DPS','ICN','22:50:00',420,425000,'M','1010101'),
    -- 캄보디아·라오스
    (77,'7C','ICN','SAI','19:15:00',310,190000,'E','1010101'),
    (78,'LJ','ICN','VTE','18:35:00',315,200000,'E','0101010'),
    -- 인도·네팔·스리랑카
    (79,'KE','ICN','DEL','13:50:00',525,525000,'M','1010101'),
    (80,'KE','DEL','ICN','22:35:00',510,520000,'M','1010101'),
    (81,'KE','ICN','KTM','10:15:00',480,510000,'M','0101010'),
    (82,'KE','ICN','CMB','09:00:00',485,500000,'M','0010010'),
    -- 우즈베키스탄·카자흐스탄
    (83,'KE','ICN','TAS','11:15:00',440,420000,'M','1010101'),
    (84,'HY','TAS','ICN','22:40:00',435,390000,'M','1010101'),
    (85,'KC','ICN','ALA','10:20:00',425,420000,'M','0101010'),
    (86,'KE','ICN','NQZ','12:15:00',480,460000,'M','0010010'),
    -- 중동·튀르키예
    (87,'EK','ICN','DXB','23:45:00',585,670000,'M','1111111'),
    (88,'EK','DXB','ICN','03:15:00',525,665000,'M','1111111'),
    (89,'EY','ICN','AUH','23:20:00',585,675000,'M','1010101'),
    (90,'QR','ICN','DOH','01:15:00',600,690000,'M','1111111'),
    (91,'QR','DOH','ICN','02:45:00',525,675000,'M','1111111'),
    (92,'OZ','ICN','IST','09:50:00',680,720000,'M','1010101'),
    -- 유럽
    (93,'KE','ICN','CDG','12:15:00',860,920000,'M','1010101'),
    (94,'AF','CDG','ICN','20:05:00',690,915000,'M','1010101'),
    (95,'KE','ICN','FRA','10:25:00',805,855000,'M','1010101'),
    (96,'KE','FRA','ICN','18:45:00',680,850000,'M','1010101'),
    (97,'KL','ICN','AMS','10:10:00',805,870000,'M','0101010'),
    (98,'BA','ICN','LHR','12:20:00',855,980000,'M','1010101'),
    (99,'KE','ICN','FCO','13:05:00',825,880000,'M','0010010'),
    (100,'KE','ICN','BCN','11:30:00',870,930000,'M','0101010'),
    (101,'KE','ICN','MAD','12:45:00',890,945000,'M','0010010'),
    (102,'AY','ICN','HEL','11:40:00',780,815000,'M','1010101'),
    (103,'KE','ICN','PRG','12:15:00',800,840000,'M','0010010'),
    (104,'LO','ICN','WRO','11:50:00',800,820000,'M','0010010'),
    (105,'KE','ICN','VIE','10:20:00',795,835000,'M','0010010'),
    (106,'KE','ICN','ZRH','10:05:00',815,900000,'M','1010101'),
    (107,'KE','ICN','BUD','11:50:00',825,840000,'M','0101010'),
    (108,'KE','ICN','CPH','10:10:00',805,845000,'M','0010010'),
    (109,'KE','ICN','LIS','11:00:00',920,975000,'M','0010010'),
    (110,'KE','ICN','MUC','12:00:00',810,850000,'M','0010010'),
    (111,'KE','ICN','MXP','11:10:00',850,895000,'M','0101010'),
    -- 미국·캐나다
    (112,'KE','ICN','LAX','14:45:00',690,940000,'M','1111111'),
    (113,'KE','LAX','ICN','11:20:00',805,945000,'M','1111111'),
    (114,'OZ','ICN','SFO','17:20:00',660,905000,'M','1111111'),
    (115,'UA','SFO','ICN','12:05:00',770,880000,'M','1111111'),
    (116,'KE','ICN','JFK','10:30:00',825,1180000,'M','1111111'),
    (117,'KE','JFK','ICN','01:00:00',950,1170000,'M','1111111'),
    (118,'DL','ICN','SEA','16:15:00',635,895000,'M','1111111'),
    (119,'DL','SEA','ICN','14:05:00',715,890000,'M','1111111'),
    (120,'KE','ICN','ORD','10:40:00',770,1140000,'M','1010101'),
    (121,'KE','ICN','DFW','13:15:00',760,1130000,'M','1010101'),
    (122,'AC','ICN','YVR','19:15:00',615,895000,'M','1111111'),
    (123,'KE','YVR','ICN','14:10:00',685,895000,'M','1111111'),
    (124,'KE','ICN','YYZ','10:20:00',805,1140000,'M','1010101'),
    (125,'KE','ICN','HNL','21:10:00',475,625000,'M','1010101'),
    -- 호주·뉴질랜드·괌·사이판
    (126,'KE','ICN','SYD','18:50:00',630,735000,'M','1111111'),
    (127,'QF','SYD','ICN','11:40:00',640,745000,'M','1010101'),
    (128,'OZ','ICN','MEL','20:20:00',650,740000,'M','0101010'),
    (129,'KE','ICN','BNE','19:10:00',625,750000,'M','1010101'),
    (130,'KE','ICN','AKL','17:00:00',690,810000,'M','1010101'),
    (131,'KE','AKL','ICN','11:35:00',710,815000,'M','1010101'),
    (132,'7C','ICN','GUM','09:20:00',270,170000,'E','1111111'),
    (133,'7C','GUM','ICN','16:25:00',300,165000,'E','1111111'),
    (134,'LJ','PUS','SPN','20:10:00',295,180000,'E','0101010'),
    -- 기타 일부 테스트용 노선
    (135,'KE','ICN','WRO','09:45:00',820,825000,'M','0010010'),
    (136,'KE','ICN','GUM','12:25:00',275,250000,'M','1010101'),
    (137,'BX','PUS','FUK','08:20:00',70,95000,'E','1111111'),
    (138,'BX','FUK','PUS','18:20:00',75,95000,'E','1111111'),
    (139,'7C','CJJ','TPE','11:05:00',160,140000,'E','0101010'),
    (140,'LJ','TAE','DAD','20:50:00',285,160000,'E','0010010');

-- 숫자 0~180을 날짜 offset으로 사용. 시작일~종료일을 모두 포함.
CREATE TEMPORARY TABLE ext_passenger_dates AS
SELECT DATE_ADD(@ext_start, INTERVAL nums.n DAY) AS flight_date,
       nums.n AS day_offset
FROM (
 SELECT h.n*100+t.n*10+o.n AS n
 FROM (SELECT 0 n UNION ALL SELECT 1) h
 CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2
             UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
             UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
             UNION ALL SELECT 9) t
 CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2
             UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
             UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
             UNION ALL SELECT 9) o
) nums
WHERE nums.n BETWEEN 0 AND 180
  AND DATE_ADD(@ext_start, INTERVAL nums.n DAY) <= @ext_end;

-- 주말, 날짜순환, 연말 성수기 변동을 반영한 가상 요금.
-- 가상 상태: 예정보다 소량의 지연 및 결항을 섞어서 테스트 용도 제공.
CREATE TEMPORARY TABLE ext_passenger_stage AS
SELECT r.route_no,r.airline_code,r.dep_code,r.arr_code,r.cabin_mode,
       TIMESTAMP(d.flight_date,r.departure_time) AS departure_at,
       TIMESTAMPADD(MINUTE,r.duration_minutes,
           TIMESTAMP(d.flight_date,r.departure_time)) AS arrival_at,
       (r.price_floor
          + MOD(d.day_offset*11+r.route_no*7,9)
            * CASE WHEN r.price_floor>=700000 THEN 18000
                   WHEN r.price_floor>=350000 THEN 9000 ELSE 4000 END
          + CASE WHEN WEEKDAY(d.flight_date)>=4
                 THEN CEIL(r.price_floor*0.07/1000)*1000 ELSE 0 END
          + CASE WHEN d.flight_date BETWEEN '2026-12-24' AND '2027-01-03'
                 THEN CEIL(r.price_floor*0.12/1000)*1000 ELSE 0 END
       ) AS base_price,
       CASE WHEN MOD(d.day_offset*17+r.route_no*31,97)=0 THEN '결항'
            WHEN MOD(d.day_offset*19+r.route_no*13,41)=0 THEN '지연'
            ELSE '예정' END AS flight_status
FROM ext_passenger_routes r
CROSS JOIN ext_passenger_dates d
WHERE SUBSTRING(r.weekday_mask,WEEKDAY(d.flight_date)+1,1)='1';

CREATE TEMPORARY TABLE ext_passenger_resolved AS
SELECT x.*,a.airline_id, dep.airport_id AS departure_airport_id,
       arr.airport_id AS arrival_airport_id
FROM ext_passenger_stage x
JOIN airline a ON a.iata_code=x.airline_code
JOIN airport dep ON dep.iata_code=x.dep_code
JOIN airport arr ON arr.iata_code=x.arr_code;

SET @ext_planned = (SELECT COUNT(*) FROM ext_passenger_stage);
SET @ext_resolved = (SELECT COUNT(*) FROM ext_passenger_resolved);
SET @ext_unique = (
 SELECT COUNT(DISTINCT airline_code,dep_code,arr_code,departure_at)
 FROM ext_passenger_stage
);
SET @ext_span = DATEDIFF(@ext_end,@ext_start);
SET @ext_ready = IF(
 @ext_lock=1 AND @ext_span BETWEEN 0 AND 180
 AND @ext_planned>0
 AND @ext_planned=@ext_resolved
 AND @ext_planned=@ext_unique,
 1,0
);

START TRANSACTION;

CREATE TEMPORARY TABLE ext_passenger_new AS
SELECT x.*
FROM ext_passenger_resolved x
WHERE @ext_ready=1
  AND NOT EXISTS (
   SELECT 1 FROM flight f
   WHERE f.airline_id=x.airline_id
     AND f.departure_airport_id=x.departure_airport_id
     AND f.arrival_airport_id=x.arrival_airport_id
     AND f.departure_at=x.departure_at
  );
SET @ext_to_insert = (SELECT COUNT(*) FROM ext_passenger_new);

INSERT INTO flight
(airline_id,departure_airport_id,arrival_airport_id,
 flight_status,departure_at,arrival_at,base_price,remaining_seats)
SELECT airline_id,departure_airport_id,arrival_airport_id,
       flight_status,departure_at,arrival_at,base_price,
       CASE WHEN cabin_mode='E' THEN 144 ELSE 176 END
FROM ext_passenger_new
ORDER BY departure_at,route_no;
SET @ext_added_flights=ROW_COUNT();

CREATE TEMPORARY TABLE ext_passenger_inserted AS
SELECT f.flight_id,x.cabin_mode,x.route_no
FROM ext_passenger_new x
JOIN flight f ON f.airline_id=x.airline_id
             AND f.departure_airport_id=x.departure_airport_id
             AND f.arrival_airport_id=x.arrival_airport_id
             AND f.departure_at=x.departure_at;

-- 이번에 새로 추가한 항공편의 좌석만 만듦.
INSERT INTO seat (flight_id,seat_no,seat_class,is_available)
SELECT x.flight_id,CONCAT(sr.row_no,letters.seat_letter),
       CASE WHEN sr.row_no BETWEEN 1 AND 2 THEN '퍼스트'
            WHEN sr.row_no BETWEEN 3 AND 8 THEN '비즈니스'
            ELSE '이코노미' END, TRUE
FROM ext_passenger_inserted x
CROSS JOIN (
 SELECT t.n*10+o.n AS row_no
 FROM (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) t
 CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2
             UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
             UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
             UNION ALL SELECT 9) o
) sr
CROSS JOIN (SELECT 'A' seat_letter UNION ALL SELECT 'B' UNION ALL SELECT 'C'
            UNION ALL SELECT 'D' UNION ALL SELECT 'E' UNION ALL SELECT 'F') letters
WHERE (sr.row_no BETWEEN 10 AND 33)
   OR (x.cabin_mode='M' AND sr.row_no BETWEEN 1 AND 8
       AND letters.seat_letter IN ('A','B','C','D'));
SET @ext_added_seats=ROW_COUNT();
SET @ext_expected_seats=(
 SELECT COALESCE(SUM(CASE WHEN cabin_mode='E' THEN 144 ELSE 176 END),0)
 FROM ext_passenger_inserted
);

COMMIT;

-- 실행 결과: 정상 완주 후에는 added_seats == expected_seats.
-- 중복 재실행 시 added_flights, added_seats 모두 0.
SELECT CASE WHEN @ext_lock IS NULL OR @ext_lock<>1 THEN '실패: 잠금 획득 실패'
            WHEN @ext_span NOT BETWEEN 0 AND 180 THEN '실패: 기간 범위 초과'
            WHEN @ext_planned<>@ext_unique THEN '실패: 내부 중복 키 확인'
            WHEN @ext_planned<>@ext_resolved THEN '실패: 공항/항공사 참조 누락'
            WHEN @ext_added_flights<>@ext_to_insert
              OR @ext_added_seats<>@ext_expected_seats
                THEN '경고: 삽입 건수 불일치'
            ELSE '완료' END AS result,
       @ext_start AS start_date, @ext_end AS end_date,
       @ext_planned AS planned_flights,
       @ext_resolved AS resolved_flights,
       @ext_added_flights AS added_flights,
       @ext_added_seats AS added_seats,
       @ext_expected_seats AS expected_seats;

-- 누락 공항/항공사 진단: 정상 시 0행.
SELECT r.route_no,r.airline_code,r.dep_code,r.arr_code
FROM ext_passenger_routes r
LEFT JOIN airline a ON a.iata_code=r.airline_code
LEFT JOIN airport dep ON dep.iata_code=r.dep_code
LEFT JOIN airport arr ON arr.iata_code=r.arr_code
WHERE a.airline_id IS NULL OR dep.airport_id IS NULL OR arr.airport_id IS NULL;

-- 이번 실행에서 추가된 편의 도착 국가/지역별 요약.
SELECT arr.country AS destination_country,
       COUNT(*) AS added_flights,
       MIN(f.base_price) AS min_price_krw,
       MAX(f.base_price) AS max_price_krw
FROM ext_passenger_inserted x
JOIN flight f ON f.flight_id=x.flight_id
JOIN airport arr ON arr.airport_id=f.arrival_airport_id
GROUP BY arr.country
ORDER BY added_flights DESC,destination_country;

DO RELEASE_LOCK('airline_reservation.extended_passenger_seed_v1');
DROP TEMPORARY TABLE ext_passenger_inserted;
DROP TEMPORARY TABLE ext_passenger_new;
DROP TEMPORARY TABLE ext_passenger_resolved;
DROP TEMPORARY TABLE ext_passenger_stage;
DROP TEMPORARY TABLE ext_passenger_dates;
DROP TEMPORARY TABLE ext_passenger_routes;
