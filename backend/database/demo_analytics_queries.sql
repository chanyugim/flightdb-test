-- 발표용 읽기 전용 조회 예시임. 챗봇에 자동 연결된 기능은 아님.
-- MySQL 8.0 이상에서 사용함. 모든 시각은 한국 표준시임.
-- seed_flights_202611_202701.sql 적용 후 실행함.
USE airline_reservation;
SET time_zone = '+09:00';
SET @query_start = TIMESTAMP('2026-11-12 00:00:00');
SET @query_end = TIMESTAMP('2027-02-01 00:00:00');
SET @as_of = TIMESTAMP('2026-11-11 12:00:00');

-- 질문 1: 비즈니스 좌석이 남은 인천 출발 항공편을 목적지별로 저렴한 3개씩 보여줘.
-- 좌석을 먼저 항공편별로 집계하여 JOIN으로 항공편 행이 중복되는 것을 방지함.
WITH seat_counts AS (
    SELECT flight_id,
           SUM(CASE WHEN seat_class = '비즈니스' AND is_available = TRUE
                    THEN 1 ELSE 0 END) AS business_available
    FROM seat
    GROUP BY flight_id
), ranked AS (
    SELECT f.flight_id, a.name_ko AS airline, dep.iata_code AS departure,
           arr.iata_code AS arrival, arr.name_ko AS arrival_name,
           f.departure_at, f.base_price, sc.business_available,
           ROW_NUMBER() OVER (
               PARTITION BY arr.airport_id ORDER BY f.base_price, f.flight_id
           ) AS price_rank
    FROM flight f
    JOIN airline a ON a.airline_id = f.airline_id
    JOIN airport dep ON dep.airport_id = f.departure_airport_id
    JOIN airport arr ON arr.airport_id = f.arrival_airport_id
    JOIN seat_counts sc ON sc.flight_id = f.flight_id
    WHERE dep.iata_code = 'ICN'
      AND f.departure_at >= @query_start AND f.departure_at < @query_end
      AND f.departure_at > @as_of
      AND f.flight_status IN ('예정', '지연')
      AND f.remaining_seats > 0 AND sc.business_available > 0
)
SELECT * FROM ranked WHERE price_rank <= 3
ORDER BY arrival, price_rank
LIMIT 50;

-- 질문 2: 항공편이 3개 이상인 항공사·노선별 편수와 평균·최저 기본 요금을 비교해줘.
SELECT a.name_ko AS airline, dep.iata_code AS departure, arr.iata_code AS arrival,
       COUNT(*) AS flight_count, MIN(f.base_price) AS min_price,
       ROUND(AVG(f.base_price), 0) AS average_price,
       MAX(f.base_price) AS max_price
FROM flight f
JOIN airline a ON a.airline_id = f.airline_id
JOIN airport dep ON dep.airport_id = f.departure_airport_id
JOIN airport arr ON arr.airport_id = f.arrival_airport_id
WHERE f.departure_at >= @query_start AND f.departure_at < @query_end
  AND f.departure_at > @as_of
  AND f.flight_status IN ('예정', '지연') AND f.remaining_seats > 0
GROUP BY a.airline_id, a.name_ko, dep.iata_code, arr.iata_code
HAVING COUNT(*) >= 3
ORDER BY average_price, airline, departure, arrival
LIMIT 50;

-- 질문 3: 기준 시점의 프로모션 중 할인율이 가장 높은 하나를 적용한 예상가를 비교해줘.
-- 포인트·인원수를 반영하지 않는 1인 예상가임. 실제 결제 금액은 예약 API에서 확정함.
-- 프로모션은 예약 시점 기준이며 출발일과 기간을 비교하지 않음. 할인은 중첩하지 않음.
WITH prices AS (
    SELECT f.flight_id, a.name_ko AS airline, dep.iata_code AS departure,
           arr.iata_code AS arrival, f.departure_at, f.base_price,
           p.promotion_id, p.promotion_name, COALESCE(p.discount_rate, 0) AS discount_rate,
           FLOOR(f.base_price * (100 - COALESCE(p.discount_rate, 0)) / 100) AS estimated_price,
           ROW_NUMBER() OVER (
               PARTITION BY f.flight_id
               ORDER BY COALESCE(p.discount_rate, 0) DESC, p.promotion_id
           ) AS promotion_rank
    FROM flight f
    JOIN airline a ON a.airline_id = f.airline_id
    JOIN airport dep ON dep.airport_id = f.departure_airport_id
    JOIN airport arr ON arr.airport_id = f.arrival_airport_id
    LEFT JOIN promotion p ON p.start_at <= @as_of AND p.end_at >= @as_of
    WHERE f.departure_at >= @query_start AND f.departure_at < @query_end
      AND f.departure_at > @as_of
      AND f.flight_status IN ('예정', '지연') AND f.remaining_seats > 0
)
SELECT * FROM prices WHERE promotion_rank = 1
ORDER BY estimated_price, flight_id
LIMIT 10;
