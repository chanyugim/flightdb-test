USE airline_reservation;
SET NAMES utf8mb4;
SET time_zone = '+09:00';
START TRANSACTION;
INSERT INTO promotion (promotion_name,discount_rate,start_at,end_at) VALUES
('가을 항공권 할인',10.00,'2026-10-01 00:00:00','2026-11-30 23:59:59'),
('연말 항공권 할인',15.00,'2026-11-01 00:00:00','2026-12-31 23:59:59'),
('연중 항공권 할인',5.00,'2026-01-01 00:00:00','2026-12-31 23:59:59'),
('여름 휴가 할인',20.00,'2026-07-01 00:00:00','2026-08-31 23:59:59');
INSERT INTO member_account (member_id,grade_code,password_hash,name,birth_date,gender,phone,point_balance,role_type) VALUES
('testuser','BASIC','$argon2id$v=19$m=65536,t=3,p=4$Z1oY/3LqOCeNpOyYqE3u4A$V+wDtLGFNhZm/7cuqraJEOSw6eJbMZrtPkK6X0i42u4','홍길동','2000-01-01','M','010-1234-5678',12000,'일반'),
('admin','BASIC','$argon2id$v=19$m=65536,t=3,p=4$mw8DTpe3pXYGmkwxPLto5Q$u56nTOUHV4n3kZxT0MTl/DgJvL18uSFOFkihZiQrm1g','관리자','1990-01-01','M','010-0000-0000',0,'관리자');
INSERT INTO flight (airline_id,departure_airport_id,arrival_airport_id,flight_status,departure_at,arrival_at,base_price,remaining_seats)
SELECT a.airline_id,dep.airport_id,arr.airport_id,x.flight_status,x.departure_at,x.arrival_at,x.base_price,0
FROM (
SELECT 'KE' airline_code,'ICN' dep_code,'NRT' arr_code,'예정' flight_status,'2026-11-10 09:00:00' departure_at,'2026-11-10 11:30:00' arrival_at,250000 base_price
UNION ALL SELECT 'OZ','ICN','NRT','예정','2026-11-10 10:30:00','2026-11-10 13:00:00',230000
UNION ALL SELECT '7C','ICN','NRT','예정','2026-11-10 13:20:00','2026-11-10 15:50:00',180000
UNION ALL SELECT 'LJ','ICN','NRT','지연','2026-11-10 17:00:00','2026-11-10 19:30:00',170000
UNION ALL SELECT 'KE','ICN','HND','예정','2026-11-10 08:00:00','2026-11-10 10:20:00',280000
UNION ALL SELECT 'OZ','ICN','HND','예정','2026-11-10 18:00:00','2026-11-10 20:20:00',260000
UNION ALL SELECT 'KE','ICN','KIX','예정','2026-11-11 09:30:00','2026-11-11 11:20:00',220000
UNION ALL SELECT '7C','ICN','KIX','예정','2026-11-11 14:00:00','2026-11-11 15:50:00',160000
UNION ALL SELECT 'KE','ICN','FUK','예정','2026-11-11 08:30:00','2026-11-11 10:00:00',180000
UNION ALL SELECT 'LJ','ICN','FUK','예정','2026-11-11 16:30:00','2026-11-11 18:00:00',140000
UNION ALL SELECT 'KE','GMP','CJU','예정','2026-11-12 08:00:00','2026-11-12 09:10:00',90000
UNION ALL SELECT 'OZ','GMP','CJU','예정','2026-11-12 10:00:00','2026-11-12 11:10:00',85000
UNION ALL SELECT '7C','GMP','CJU','예정','2026-11-12 13:00:00','2026-11-12 14:10:00',70000
UNION ALL SELECT 'BX','PUS','CJU','예정','2026-11-12 09:00:00','2026-11-12 10:00:00',65000
UNION ALL SELECT 'KE','ICN','BKK','예정','2026-11-13 09:00:00','2026-11-13 13:00:00',420000
UNION ALL SELECT 'KE','ICN','TPE','결항','2026-11-14 11:00:00','2026-11-14 13:00:00',210000
UNION ALL SELECT 'OZ','ICN','TPE','예정','2026-11-14 15:00:00','2026-11-14 17:00:00',195000
UNION ALL SELECT 'KE','ICN','SIN','예정','2026-11-15 08:00:00','2026-11-15 14:20:00',480000
) x
JOIN airline a ON a.iata_code=x.airline_code
JOIN airport dep ON dep.iata_code=x.dep_code
JOIN airport arr ON arr.iata_code=x.arr_code;
-- 프론트 배치도 테스트용 가상 좌석 구성임. 특정 기종을 재현하지 않음.
-- 퍼스트: 1~2열 A~D (8석), 비즈니스: 3~8열 A~D (24석)
-- 이코노미: 10~33열 A~F (144석), 항공편당 총 176석임.
-- 예매 예시의 10A, 10B, 10C 좌석번호를 유지함.
INSERT INTO seat (flight_id,seat_no,seat_class,is_available)
SELECT f.flight_id,CONCAT(r.row_no,c.seat_letter),
CASE WHEN r.row_no <= 2 THEN '퍼스트'
     WHEN r.row_no <= 8 THEN '비즈니스'
     ELSE '이코노미' END,TRUE
FROM flight f
CROSS JOIN (
SELECT 1 row_no
UNION ALL SELECT 2
UNION ALL SELECT 3
UNION ALL SELECT 4
UNION ALL SELECT 5
UNION ALL SELECT 6
UNION ALL SELECT 7
UNION ALL SELECT 8
UNION ALL SELECT 10
UNION ALL SELECT 11
UNION ALL SELECT 12
UNION ALL SELECT 13
UNION ALL SELECT 14
UNION ALL SELECT 15
UNION ALL SELECT 16
UNION ALL SELECT 17
UNION ALL SELECT 18
UNION ALL SELECT 19
UNION ALL SELECT 20
UNION ALL SELECT 21
UNION ALL SELECT 22
UNION ALL SELECT 23
UNION ALL SELECT 24
UNION ALL SELECT 25
UNION ALL SELECT 26
UNION ALL SELECT 27
UNION ALL SELECT 28
UNION ALL SELECT 29
UNION ALL SELECT 30
UNION ALL SELECT 31
UNION ALL SELECT 32
UNION ALL SELECT 33
) r
CROSS JOIN (
SELECT 'A' seat_letter
UNION ALL SELECT 'B'
UNION ALL SELECT 'C'
UNION ALL SELECT 'D'
UNION ALL SELECT 'E'
UNION ALL SELECT 'F'
) c
WHERE r.row_no >= 10 OR c.seat_letter IN ('A','B','C','D');
INSERT INTO reservation (reservation_no,member_id,promotion_id,booker_name,booker_phone,booker_email,booker_birth_date,used_points,final_amount,reserved_at,reservation_status) VALUES
('R202611010001','testuser',NULL,'홍길동','010-1234-5678','testuser@example.com','2000-01-01',0,250000,'2026-11-01 10:00:00','확정'),
('R202611010002',NULL,(SELECT promotion_id FROM promotion WHERE promotion_name='가을 항공권 할인' LIMIT 1),'김비회원','010-5555-1234','guest@example.com','1998-05-12',0,162000,'2026-11-01 11:00:00','확정'),
('R202610200001','testuser',NULL,'홍길동','010-1234-5678','testuser@example.com','2000-01-01',0,90000,'2026-10-20 09:00:00','취소');
INSERT INTO reservation_detail (reservation_no,seat_id,passenger_name,passenger_birth_date)
SELECT 'R202611010001',s.seat_id,'홍길동','2000-01-01'
FROM seat s
JOIN flight f ON f.flight_id=s.flight_id
JOIN airline a ON a.airline_id=f.airline_id
JOIN airport dep ON dep.airport_id=f.departure_airport_id
JOIN airport arr ON arr.airport_id=f.arrival_airport_id
WHERE a.iata_code='KE' AND dep.iata_code='ICN' AND arr.iata_code='NRT' AND f.departure_at='2026-11-10 09:00:00' AND s.seat_no='10A'
LIMIT 1;
INSERT INTO reservation_detail (reservation_no,seat_id,passenger_name,passenger_birth_date)
SELECT 'R202611010002',s.seat_id,'김비회원','1998-05-12'
FROM seat s
JOIN flight f ON f.flight_id=s.flight_id
JOIN airline a ON a.airline_id=f.airline_id
JOIN airport dep ON dep.airport_id=f.departure_airport_id
JOIN airport arr ON arr.airport_id=f.arrival_airport_id
WHERE a.iata_code='7C' AND dep.iata_code='ICN' AND arr.iata_code='NRT' AND f.departure_at='2026-11-10 13:20:00' AND s.seat_no='10B'
LIMIT 1;
INSERT INTO reservation_detail (reservation_no,seat_id,passenger_name,passenger_birth_date)
SELECT 'R202610200001',s.seat_id,'홍길동','2000-01-01'
FROM seat s
JOIN flight f ON f.flight_id=s.flight_id
JOIN airline a ON a.airline_id=f.airline_id
JOIN airport dep ON dep.airport_id=f.departure_airport_id
JOIN airport arr ON arr.airport_id=f.arrival_airport_id
WHERE a.iata_code='KE' AND dep.iata_code='GMP' AND arr.iata_code='CJU' AND f.departure_at='2026-11-12 08:00:00' AND s.seat_no='10C'
LIMIT 1;
UPDATE seat s
JOIN reservation_detail rd ON rd.seat_id=s.seat_id
JOIN reservation r ON r.reservation_no=rd.reservation_no
SET s.is_available=FALSE
WHERE r.reservation_status='확정';
UPDATE flight f
SET f.remaining_seats=(SELECT COUNT(*) FROM seat s WHERE s.flight_id=f.flight_id AND s.is_available=TRUE);
INSERT INTO point_history (reservation_no,change_type,change_amount,balance_after,occurred_at) VALUES
('R202610200001','적립',900,10400,'2026-10-20 09:05:00'),
('R202610200001','회수',900,9500,'2026-10-21 14:00:00'),
('R202611010001','적립',2500,12000,'2026-11-01 10:05:00');
INSERT INTO inquiry (member_id,reservation_no,author_name,author_phone,inquiry_password,subject,content,admin_reply,reply_status,created_at) VALUES
('testuser','R202611010001','홍길동','010-1234-5678',NULL,'좌석 변경 문의','예매한 좌석을 다른 좌석으로 변경할 수 있나요?','현재 프로젝트 구현 범위에서는 예매 취소 후 다시 예매해 주세요.','답변완료','2026-11-01 12:00:00'),
(NULL,'R202611010002','김비회원','010-5555-1234','$argon2id$v=19$m=65536,t=3,p=4$LJY+HuI2H6GBUbFebEV9uQ$DIjyCUkA7xS7o8rtv7V55YoMVDut+3EhyXY7qRQprQ4','비회원 예매 조회 문의','비회원 예매번호로 조회하는 방법을 알고 싶습니다.',NULL,'답변대기','2026-11-01 13:00:00');
COMMIT;
