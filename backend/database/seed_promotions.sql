-- 예약 한 건에 프로모션 하나만 적용함. 같은 이름이 있으면 추가하지 않음.
SET time_zone = '+09:00';
START TRANSACTION;

INSERT INTO promotion (promotion_name, discount_rate, start_at, end_at)
SELECT '가을 여행 할인', 10.00, '2026-11-01 00:00:00', '2026-11-30 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM promotion WHERE promotion_name = '가을 여행 할인');

INSERT INTO promotion (promotion_name, discount_rate, start_at, end_at)
SELECT '연말 여행 할인', 15.00, '2026-11-01 00:00:00', '2026-12-31 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM promotion WHERE promotion_name = '연말 여행 할인');

INSERT INTO promotion (promotion_name, discount_rate, start_at, end_at)
SELECT '겨울 여행 할인', 20.00, '2026-11-01 00:00:00', '2027-01-31 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM promotion WHERE promotion_name = '겨울 여행 할인');

COMMIT;
