-- 최초 설치용 SQL임. 기존 테이블을 자동 삭제하지 않음.
CREATE DATABASE IF NOT EXISTS airline_reservation
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;
USE airline_reservation;
CREATE TABLE airline (
airline_id INTEGER NOT NULL AUTO_INCREMENT,
name_ko VARCHAR(50) NOT NULL,
name_en VARCHAR(100) NOT NULL,
iata_code CHAR(2),
icao_code CHAR(3),
country VARCHAR(50) NOT NULL,
CONSTRAINT pk_airline PRIMARY KEY (airline_id),
CONSTRAINT uq_airline_iata UNIQUE (iata_code),
CONSTRAINT uq_airline_icao UNIQUE (icao_code)
);
CREATE TABLE airport (
airport_id INTEGER NOT NULL AUTO_INCREMENT,
name_ko VARCHAR(50) NOT NULL,
name_en VARCHAR(100) NOT NULL,
iata_code CHAR(3),
icao_code CHAR(4),
country VARCHAR(50) NOT NULL,
city VARCHAR(50) NOT NULL,
CONSTRAINT pk_airport PRIMARY KEY (airport_id),
CONSTRAINT uq_airport_iata UNIQUE (iata_code),
CONSTRAINT uq_airport_icao UNIQUE (icao_code)
);
CREATE TABLE member_grade (
grade_code VARCHAR(10) NOT NULL,
grade_name VARCHAR(20) NOT NULL,
upgrade_requirement INTEGER NOT NULL,
point_rate DECIMAL(5,2) NOT NULL,
CONSTRAINT pk_member_grade PRIMARY KEY (grade_code),
CONSTRAINT ck_grade_requirement CHECK (upgrade_requirement >= 0),
CONSTRAINT ck_grade_point_rate CHECK (point_rate BETWEEN 0 AND 100)
);
CREATE TABLE promotion (
promotion_id INTEGER NOT NULL AUTO_INCREMENT,
promotion_name VARCHAR(50) NOT NULL,
discount_rate DECIMAL(5,2) NOT NULL,
start_at TIMESTAMP NOT NULL,
end_at TIMESTAMP NOT NULL,
CONSTRAINT pk_promotion PRIMARY KEY (promotion_id),
CONSTRAINT ck_promotion_rate CHECK (discount_rate BETWEEN 0 AND 100),
CONSTRAINT ck_promotion_period CHECK (start_at <= end_at)
);
CREATE TABLE flight (
flight_id INTEGER NOT NULL AUTO_INCREMENT,
airline_id INTEGER NOT NULL,
departure_airport_id INTEGER NOT NULL,
arrival_airport_id INTEGER NOT NULL,
flight_status VARCHAR(20) DEFAULT '예정' NOT NULL,
departure_at TIMESTAMP NOT NULL,
arrival_at TIMESTAMP NOT NULL,
base_price INTEGER NOT NULL,
remaining_seats INTEGER NOT NULL,
CONSTRAINT pk_flight PRIMARY KEY (flight_id),
CONSTRAINT fk_flight_airline
FOREIGN KEY (airline_id) REFERENCES airline (airline_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT fk_flight_departure
FOREIGN KEY (departure_airport_id) REFERENCES airport (airport_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT fk_flight_arrival
FOREIGN KEY (arrival_airport_id) REFERENCES airport (airport_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT ck_flight_airports CHECK (departure_airport_id <> arrival_airport_id),
CONSTRAINT ck_flight_time CHECK (departure_at < arrival_at),
CONSTRAINT ck_flight_price CHECK (base_price >= 0),
CONSTRAINT ck_flight_seats CHECK (remaining_seats >= 0),
CONSTRAINT ck_flight_status CHECK (flight_status IN ('예정', '지연', '결항', '완료'))
);
CREATE TABLE member_account (
member_id VARCHAR(20) NOT NULL,
grade_code VARCHAR(10) NOT NULL,
password_hash VARCHAR(255) NOT NULL,
name VARCHAR(30) NOT NULL,
birth_date DATE NOT NULL,
gender CHAR(1) NOT NULL,
phone VARCHAR(20) NOT NULL,
point_balance INTEGER DEFAULT 0 NOT NULL,
role_type VARCHAR(20) DEFAULT '일반' NOT NULL,
CONSTRAINT pk_member_account PRIMARY KEY (member_id),
CONSTRAINT fk_member_grade
FOREIGN KEY (grade_code) REFERENCES member_grade (grade_code)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT ck_member_points CHECK (point_balance >= 0),
CONSTRAINT ck_member_role CHECK (role_type IN ('일반', '관리자'))
);
CREATE TABLE seat (
seat_id INTEGER NOT NULL AUTO_INCREMENT,
flight_id INTEGER NOT NULL,
seat_no VARCHAR(5) NOT NULL,
seat_class VARCHAR(20) NOT NULL,
is_available BOOLEAN DEFAULT TRUE NOT NULL,
CONSTRAINT pk_seat PRIMARY KEY (seat_id),
CONSTRAINT fk_seat_flight
FOREIGN KEY (flight_id) REFERENCES flight (flight_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT uq_seat_no UNIQUE (flight_id, seat_no),
CONSTRAINT ck_seat_class CHECK (seat_class IN ('이코노미', '비즈니스', '퍼스트'))
);
CREATE TABLE reservation (
reservation_no VARCHAR(20) NOT NULL,
member_id VARCHAR(20),
promotion_id INTEGER,
booker_name VARCHAR(30) NOT NULL,
booker_phone VARCHAR(20) NOT NULL,
booker_email VARCHAR(100) NOT NULL,
booker_birth_date DATE NOT NULL,
used_points INTEGER DEFAULT 0 NOT NULL,
final_amount INTEGER NOT NULL,
reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
reservation_status VARCHAR(20) NOT NULL,
CONSTRAINT pk_reservation PRIMARY KEY (reservation_no),
CONSTRAINT fk_reservation_member
FOREIGN KEY (member_id) REFERENCES member_account (member_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT fk_reservation_promotion
FOREIGN KEY (promotion_id) REFERENCES promotion (promotion_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT ck_reservation_points CHECK (used_points >= 0),
CONSTRAINT ck_reservation_amount CHECK (final_amount >= 0),
CONSTRAINT ck_reservation_status CHECK (reservation_status IN ('확정', '취소'))
);
CREATE TABLE reservation_detail (
reservation_detail_id INTEGER NOT NULL AUTO_INCREMENT,
reservation_no VARCHAR(20) NOT NULL,
seat_id INTEGER NOT NULL,
passenger_name VARCHAR(30) NOT NULL,
passenger_birth_date DATE NOT NULL,
CONSTRAINT pk_reservation_detail PRIMARY KEY (reservation_detail_id),
CONSTRAINT fk_detail_reservation
FOREIGN KEY (reservation_no) REFERENCES reservation (reservation_no)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT fk_detail_seat
FOREIGN KEY (seat_id) REFERENCES seat (seat_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT uq_detail_reservation_seat UNIQUE (reservation_no, seat_id)
);
CREATE TABLE inquiry (
inquiry_id INTEGER NOT NULL AUTO_INCREMENT,
member_id VARCHAR(20),
reservation_no VARCHAR(20),
author_name VARCHAR(30) NOT NULL,
author_phone VARCHAR(20) NOT NULL,
inquiry_password VARCHAR(255),
subject VARCHAR(100) NOT NULL,
content TEXT NOT NULL,
admin_reply TEXT,
reply_status VARCHAR(20) DEFAULT '답변대기' NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
CONSTRAINT pk_inquiry PRIMARY KEY (inquiry_id),
CONSTRAINT fk_inquiry_member
FOREIGN KEY (member_id) REFERENCES member_account (member_id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT fk_inquiry_reservation
FOREIGN KEY (reservation_no) REFERENCES reservation (reservation_no)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT ck_inquiry_reply CHECK (reply_status IN ('답변대기', '답변완료'))
);
CREATE TABLE point_history (
point_history_id INTEGER NOT NULL AUTO_INCREMENT,
reservation_no VARCHAR(20) NOT NULL,
change_type VARCHAR(20) NOT NULL,
change_amount INTEGER NOT NULL,
balance_after INTEGER NOT NULL,
occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
CONSTRAINT pk_point_history PRIMARY KEY (point_history_id),
CONSTRAINT fk_point_reservation
FOREIGN KEY (reservation_no) REFERENCES reservation (reservation_no)
ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT ck_point_type CHECK (change_type IN ('적립', '사용', '회수', '반환')),
CONSTRAINT ck_point_amount CHECK (change_amount >= 0),
CONSTRAINT ck_point_balance CHECK (balance_after >= 0)
);
CREATE INDEX idx_flight_route_time
ON flight (departure_airport_id, arrival_airport_id, departure_at);
CREATE INDEX idx_reservation_member_date
ON reservation (member_id, reserved_at);
CREATE INDEX idx_inquiry_member_date
ON inquiry (member_id, created_at);
SELECT 'airline_reservation schema created successfully.' AS result;
SHOW TABLES;
