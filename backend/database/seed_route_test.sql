-- MySQL 8 이상용임. Workbench에서는 파일 전체를 실행함.
-- 현재 접속 DB가 프로젝트 DB인지 확인한 뒤 실행함. 다른 DB명을 사용하면 USE를 변경함.
USE airline_reservation;
SET NAMES utf8mb4;
SET time_zone = '+09:00';
-- 기존 공항(GMP/CJU/ICN/NRT/PUS), 항공사 KE, BASIC 등급이 필요함.
-- 전용 계정 비밀번호: UxDemo2026! / 비회원 문의 비밀번호: GuestDemo2026!
-- 중복 실행 시 기존 데이터를 덮어쓰지 않고 중단함. 정리 SQL 실행 후 재삽입함.
-- CREATE ROUTINE 권한이 있는 계정에서 실행함. 오류 발생 시 삽입 전체를 롤백함.
-- 명시적 숫자 ID 사용으로 AUTO_INCREMENT 다음 값이 증가할 수 있으며 되돌리지 않음.
DELIMITER $$
DROP PROCEDURE IF EXISTS ux26_insert_route_fixture$$
CREATE PROCEDURE ux26_insert_route_fixture()
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
  IF (SELECT COUNT(*) FROM airport WHERE iata_code IN ('GMP','CJU','ICN','NRT','PUS')) <> 5
     OR NOT EXISTS (SELECT 1 FROM airline WHERE iata_code='KE')
     OR NOT EXISTS (SELECT 1 FROM member_grade WHERE grade_code='BASIC') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='공항/항공사/등급 기본 시드를 먼저 적용해 주세요.';
  END IF;
  IF EXISTS (SELECT 1 FROM member_account WHERE member_id IN ('ux26_member_a','ux26_member_b','ux26_new','ux26_admin')) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='UX26 테스트 ID가 이미 존재함. 삭제 SQL 또는 ID 충돌을 확인해 주세요.';
  END IF;
  IF EXISTS (SELECT 1 FROM reservation WHERE reservation_no IN ('UX26R001','UX26R002','UX26R003','UX26R004','UX26R005','UX26R006','UX26R007','UX26R008','UX26R009','UX26R010','UX26R011','UX26R012','UX26R013','UX26R014','UX26R015','UX26R016')) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='UX26 테스트 ID가 이미 존재함. 삭제 SQL 또는 ID 충돌을 확인해 주세요.';
  END IF;
  IF EXISTS (SELECT 1 FROM flight WHERE flight_id IN (871001,871002,871003,871004,871005,871006,871007,871008,871009,871010,871011,871012,871013,871014,871015,871016,871017)) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='UX26 테스트 ID가 이미 존재함. 삭제 SQL 또는 ID 충돌을 확인해 주세요.';
  END IF;
  IF EXISTS (SELECT 1 FROM seat WHERE seat_id BETWEEN 881001 AND 881034) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='UX26 테스트 ID가 이미 존재함. 삭제 SQL 또는 ID 충돌을 확인해 주세요.';
  END IF;
  IF EXISTS (SELECT 1 FROM reservation_detail WHERE reservation_detail_id BETWEEN 891001 AND 891018) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='UX26 테스트 ID가 이미 존재함. 삭제 SQL 또는 ID 충돌을 확인해 주세요.';
  END IF;
  IF EXISTS (SELECT 1 FROM inquiry WHERE inquiry_id IN (901001,901002,901003,901004,901005,901006)) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='UX26 테스트 ID가 이미 존재함. 삭제 SQL 또는 ID 충돌을 확인해 주세요.';
  END IF;
  SET @ux26_now = NOW();
  SET @ux26_GMP = (SELECT airport_id FROM airport WHERE iata_code='GMP');
  SET @ux26_CJU = (SELECT airport_id FROM airport WHERE iata_code='CJU');
  SET @ux26_ICN = (SELECT airport_id FROM airport WHERE iata_code='ICN');
  SET @ux26_NRT = (SELECT airport_id FROM airport WHERE iata_code='NRT');
  SET @ux26_PUS = (SELECT airport_id FROM airport WHERE iata_code='PUS');
  SET @ux26_airline = (SELECT airline_id FROM airline WHERE iata_code='KE');
INSERT INTO member_account (member_id,grade_code,password_hash,name,birth_date,gender,phone,point_balance,role_type) VALUES
('ux26_member_a', 'BASIC', '$argon2id$v=19$m=65536,t=3,p=4$YTFnuVNk/5mqkeSIOnKa8Q$Yk6fYt/BKujZcRzCiZsbNLedPo5wCKhxL3g+uAdWm6Q', '[UX26] 여행회원A', '2000-01-01', 'F', '010-0000-2601', 0, '일반'),
('ux26_member_b', 'BASIC', '$argon2id$v=19$m=65536,t=3,p=4$YTFnuVNk/5mqkeSIOnKa8Q$Yk6fYt/BKujZcRzCiZsbNLedPo5wCKhxL3g+uAdWm6Q', '[UX26] 여행회원B', '2000-01-01', 'F', '010-0000-2602', 0, '일반'),
('ux26_new', 'BASIC', '$argon2id$v=19$m=65536,t=3,p=4$YTFnuVNk/5mqkeSIOnKa8Q$Yk6fYt/BKujZcRzCiZsbNLedPo5wCKhxL3g+uAdWm6Q', '[UX26] 신규회원', '2000-01-01', 'F', '010-0000-2603', 0, '일반'),
('ux26_admin', 'BASIC', '$argon2id$v=19$m=65536,t=3,p=4$YTFnuVNk/5mqkeSIOnKa8Q$Yk6fYt/BKujZcRzCiZsbNLedPo5wCKhxL3g+uAdWm6Q', '[UX26] 관리자', '2000-01-01', 'F', '010-0000-2604', 0, '관리자');
INSERT INTO flight (flight_id,airline_id,departure_airport_id,arrival_airport_id,flight_status,departure_at,arrival_at,base_price,remaining_seats) VALUES
(871001, @ux26_airline, @ux26_GMP, @ux26_CJU, '완료', DATE_ADD(@ux26_now, INTERVAL -15 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -15 DAY), INTERVAL 2 HOUR), 100000, 0),
(871002, @ux26_airline, @ux26_GMP, @ux26_CJU, '완료', DATE_ADD(@ux26_now, INTERVAL -14 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -14 DAY), INTERVAL 2 HOUR), 100000, 1),
(871003, @ux26_airline, @ux26_GMP, @ux26_CJU, '완료', DATE_ADD(@ux26_now, INTERVAL -13 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -13 DAY), INTERVAL 2 HOUR), 100000, 1),
(871004, @ux26_airline, @ux26_GMP, @ux26_CJU, '완료', DATE_ADD(@ux26_now, INTERVAL -12 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -12 DAY), INTERVAL 2 HOUR), 100000, 1),
(871005, @ux26_airline, @ux26_GMP, @ux26_CJU, '완료', DATE_ADD(@ux26_now, INTERVAL -11 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -11 DAY), INTERVAL 2 HOUR), 100000, 1),
(871006, @ux26_airline, @ux26_ICN, @ux26_NRT, '완료', DATE_ADD(@ux26_now, INTERVAL -10 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -10 DAY), INTERVAL 2 HOUR), 100000, 1),
(871007, @ux26_airline, @ux26_ICN, @ux26_NRT, '완료', DATE_ADD(@ux26_now, INTERVAL -13 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -13 DAY), INTERVAL 2 HOUR), 100000, 1),
(871008, @ux26_airline, @ux26_ICN, @ux26_NRT, '완료', DATE_ADD(@ux26_now, INTERVAL -12 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -12 DAY), INTERVAL 2 HOUR), 100000, 1),
(871009, @ux26_airline, @ux26_ICN, @ux26_NRT, '완료', DATE_ADD(@ux26_now, INTERVAL -11 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -11 DAY), INTERVAL 2 HOUR), 100000, 1),
(871010, @ux26_airline, @ux26_PUS, @ux26_CJU, '완료', DATE_ADD(@ux26_now, INTERVAL -8 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -8 DAY), INTERVAL 2 HOUR), 100000, 1),
(871011, @ux26_airline, @ux26_GMP, @ux26_CJU, '예정', DATE_ADD(@ux26_now, INTERVAL 7 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL 7 DAY), INTERVAL 2 HOUR), 100000, 1),
(871012, @ux26_airline, @ux26_GMP, @ux26_CJU, '예정', DATE_ADD(@ux26_now, INTERVAL 8 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL 8 DAY), INTERVAL 2 HOUR), 100000, 1),
(871013, @ux26_airline, @ux26_GMP, @ux26_CJU, '예정', DATE_ADD(@ux26_now, INTERVAL 9 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL 9 DAY), INTERVAL 2 HOUR), 100000, 2),
(871014, @ux26_airline, @ux26_PUS, @ux26_CJU, '결항', DATE_ADD(@ux26_now, INTERVAL 10 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL 10 DAY), INTERVAL 2 HOUR), 100000, 1),
(871015, @ux26_airline, @ux26_PUS, @ux26_CJU, '완료', DATE_ADD(@ux26_now, INTERVAL -45 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -45 DAY), INTERVAL 2 HOUR), 100000, 1),
(871016, @ux26_airline, @ux26_ICN, @ux26_NRT, '완료', DATE_ADD(@ux26_now, INTERVAL -4 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -4 DAY), INTERVAL 2 HOUR), 100000, 1),
(871017, @ux26_airline, @ux26_NRT, @ux26_ICN, '완료', DATE_ADD(@ux26_now, INTERVAL -2 DAY), DATE_ADD(DATE_ADD(@ux26_now, INTERVAL -2 DAY), INTERVAL 2 HOUR), 100000, 1);
INSERT INTO seat (seat_id,flight_id,seat_no,seat_class,is_available) VALUES
(881001, 871001, '1A', '이코노미', FALSE),
(881002, 871001, '1B', '이코노미', FALSE),
(881003, 871002, '1A', '이코노미', FALSE),
(881004, 871002, '1B', '이코노미', TRUE),
(881005, 871003, '1A', '이코노미', FALSE),
(881006, 871003, '1B', '이코노미', TRUE),
(881007, 871004, '1A', '이코노미', FALSE),
(881008, 871004, '1B', '이코노미', TRUE),
(881009, 871005, '1A', '이코노미', FALSE),
(881010, 871005, '1B', '이코노미', TRUE),
(881011, 871006, '1A', '이코노미', FALSE),
(881012, 871006, '1B', '이코노미', TRUE),
(881013, 871007, '1A', '이코노미', FALSE),
(881014, 871007, '1B', '이코노미', TRUE),
(881015, 871008, '1A', '이코노미', FALSE),
(881016, 871008, '1B', '이코노미', TRUE),
(881017, 871009, '1A', '이코노미', FALSE),
(881018, 871009, '1B', '이코노미', TRUE),
(881019, 871010, '1A', '이코노미', FALSE),
(881020, 871010, '1B', '이코노미', TRUE),
(881021, 871011, '1A', '이코노미', FALSE),
(881022, 871011, '1B', '이코노미', TRUE),
(881023, 871012, '1A', '이코노미', FALSE),
(881024, 871012, '1B', '이코노미', TRUE),
(881025, 871013, '1A', '이코노미', TRUE),
(881026, 871013, '1B', '이코노미', TRUE),
(881027, 871014, '1A', '이코노미', FALSE),
(881028, 871014, '1B', '이코노미', TRUE),
(881029, 871015, '1A', '이코노미', FALSE),
(881030, 871015, '1B', '이코노미', TRUE),
(881031, 871016, '1A', '이코노미', FALSE),
(881032, 871016, '1B', '이코노미', TRUE),
(881033, 871017, '1A', '이코노미', FALSE),
(881034, 871017, '1B', '이코노미', TRUE);
INSERT INTO reservation (reservation_no,member_id,promotion_id,booker_name,booker_phone,booker_email,booker_birth_date,used_points,final_amount,reserved_at,reservation_status) VALUES
('UX26R001', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 200000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R002', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R003', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R004', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R005', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R006', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R007', 'ux26_member_b', NULL, '[UX26] 예약자', '010-0000-2602', 'ux26_member_b@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R008', 'ux26_member_b', NULL, '[UX26] 예약자', '010-0000-2602', 'ux26_member_b@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R009', 'ux26_member_b', NULL, '[UX26] 예약자', '010-0000-2602', 'ux26_member_b@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R010', 'ux26_member_b', NULL, '[UX26] 예약자', '010-0000-2602', 'ux26_member_b@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정'),
('UX26R011', NULL, NULL, '[UX26] 비회원', '010-0000-2609', 'ux26_guest@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 1 DAY), '확정'),
('UX26R012', NULL, NULL, '[UX26] 비회원', '010-0000-2609', 'ux26_guest@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 1 DAY), '확정'),
('UX26R013', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 1 DAY), '취소'),
('UX26R014', 'ux26_member_b', NULL, '[UX26] 예약자', '010-0000-2602', 'ux26_member_b@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 1 DAY), '확정'),
('UX26R015', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 100000, DATE_SUB(@ux26_now, INTERVAL 50 DAY), '확정'),
('UX26R016', 'ux26_member_a', NULL, '[UX26] 예약자', '010-0000-2601', 'ux26_member_a@example.invalid', '2000-01-01', 0, 200000, DATE_SUB(@ux26_now, INTERVAL 20 DAY), '확정');
INSERT INTO reservation_detail (reservation_detail_id,reservation_no,seat_id,passenger_name,passenger_birth_date) VALUES
(891001, 'UX26R001', 881001, '[UX26] 탑승객', '2000-01-01'),
(891002, 'UX26R001', 881002, '[UX26] 동행인', '2000-01-02'),
(891003, 'UX26R002', 881003, '[UX26] 탑승객', '2000-01-01'),
(891004, 'UX26R003', 881005, '[UX26] 탑승객', '2000-01-01'),
(891005, 'UX26R004', 881007, '[UX26] 탑승객', '2000-01-01'),
(891006, 'UX26R005', 881009, '[UX26] 탑승객', '2000-01-01'),
(891007, 'UX26R006', 881011, '[UX26] 탑승객', '2000-01-01'),
(891008, 'UX26R007', 881013, '[UX26] 탑승객', '2000-01-01'),
(891009, 'UX26R008', 881015, '[UX26] 탑승객', '2000-01-01'),
(891010, 'UX26R009', 881017, '[UX26] 탑승객', '2000-01-01'),
(891011, 'UX26R010', 881019, '[UX26] 탑승객', '2000-01-01'),
(891012, 'UX26R011', 881021, '[UX26] 탑승객', '2000-01-01'),
(891013, 'UX26R012', 881023, '[UX26] 탑승객', '2000-01-01'),
(891014, 'UX26R013', 881025, '[UX26] 탑승객', '2000-01-01'),
(891015, 'UX26R014', 881027, '[UX26] 탑승객', '2000-01-01'),
(891016, 'UX26R015', 881029, '[UX26] 탑승객', '2000-01-01'),
(891017, 'UX26R016', 881031, '[UX26] 탑승객', '2000-01-01'),
(891018, 'UX26R016', 881033, '[UX26] 탑승객', '2000-01-01');
INSERT INTO inquiry (inquiry_id,member_id,reservation_no,author_name,author_phone,inquiry_password,subject,content,admin_reply,reply_status,created_at) VALUES
(901001, 'ux26_member_a', 'UX26R001', '[UX26] 문의작성자', '010-0000-2601', NULL, '[UX26] 테스트 문의 1', '테스트용 가상 문의 내용임. 예약 조회와 관리자 답변을 확인함.', '테스트 답변입니다. 요청하신 내용을 확인했습니다.', '답변완료', DATE_SUB(@ux26_now, INTERVAL 1 HOUR)),
(901002, 'ux26_member_a', 'UX26R006', '[UX26] 문의작성자', '010-0000-2601', NULL, '[UX26] 테스트 문의 2', '테스트용 가상 문의 내용임. 예약 조회와 관리자 답변을 확인함.', NULL, '답변대기', DATE_SUB(@ux26_now, INTERVAL 1 HOUR)),
(901003, 'ux26_member_b', 'UX26R010', '[UX26] 문의작성자', '010-0000-2602', NULL, '[UX26] 테스트 문의 3', '테스트용 가상 문의 내용임. 예약 조회와 관리자 답변을 확인함.', '테스트 답변입니다. 요청하신 내용을 확인했습니다.', '답변완료', DATE_SUB(@ux26_now, INTERVAL 1 HOUR)),
(901004, NULL, 'UX26R011', '[UX26] 문의작성자', '010-0000-2609', '$argon2id$v=19$m=65536,t=3,p=4$pK2LvJjYINgZHbtiiBHu5A$c4hJowAk9FMa/0QPIPNBssWzpYOK0QAmW0WHbb6IbbM', '[UX26] 테스트 문의 4', '테스트용 가상 문의 내용임. 예약 조회와 관리자 답변을 확인함.', '테스트 답변입니다. 요청하신 내용을 확인했습니다.', '답변완료', DATE_SUB(@ux26_now, INTERVAL 1 HOUR)),
(901005, NULL, 'UX26R012', '[UX26] 문의작성자', '010-0000-2609', '$argon2id$v=19$m=65536,t=3,p=4$pK2LvJjYINgZHbtiiBHu5A$c4hJowAk9FMa/0QPIPNBssWzpYOK0QAmW0WHbb6IbbM', '[UX26] 테스트 문의 5', '테스트용 가상 문의 내용임. 예약 조회와 관리자 답변을 확인함.', NULL, '답변대기', DATE_SUB(@ux26_now, INTERVAL 1 HOUR)),
(901006, NULL, NULL, '[UX26] 문의작성자', '010-0000-2609', '$argon2id$v=19$m=65536,t=3,p=4$pK2LvJjYINgZHbtiiBHu5A$c4hJowAk9FMa/0QPIPNBssWzpYOK0QAmW0WHbb6IbbM', '[UX26] 테스트 문의 6', '테스트용 가상 문의 내용임. 예약 조회와 관리자 답변을 확인함.', NULL, '답변대기', DATE_SUB(@ux26_now, INTERVAL 1 HOUR));
  COMMIT;
  SELECT 'UX26 테스트 데이터 삽입 완료' AS result;
END$$
CALL ux26_insert_route_fixture()$$
DROP PROCEDURE ux26_insert_route_fixture$$
DELIMITER ;
SELECT member_id, name, role_type FROM member_account WHERE member_id IN ('ux26_member_a','ux26_member_b','ux26_new','ux26_admin');
SELECT inquiry_id, member_id, subject, reply_status FROM inquiry WHERE inquiry_id IN (901001,901002,901003,901004,901005,901006);
