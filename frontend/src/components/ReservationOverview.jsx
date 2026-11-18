import { Link } from "react-router-dom";
import { formatDate, formatTime, formatWon } from "../utils/format.js";
import { cancellationReason } from "../api/reservationStatus";
import SeatFlightInfo from "./SeatFlightInfo";

export default function ReservationOverview({ reservation: r, onCancel, cancelling }) {
  const segments =
    r.trip_type === "round_trip"
      ? r.segments
      : [{ direction: "outbound", flight: r.flight, details: r.details }];
  const reason = cancellationReason(r);
  return (
    <div className="booking-layout reservation-overview">
      <div className="booking-sheet">
        {segments.map((segment) => (
          <section className="booking-section" key={segment.flight.flight_id}>
            <div className="booking-section-heading">
              <h2>
                {r.trip_type === "round_trip"
                  ? segment.direction === "outbound"
                    ? "가는 편"
                    : "오는 편"
                  : "선택한 항공편"}
              </h2>
            </div>
            <SeatFlightInfo flight={segment.flight} />
            <p className="small muted">도착일 {formatDate(segment.flight.arrival_at)} · 한국 시간</p>
            <h3>탑승객 및 좌석</h3>
            <ul className="confirmed-passengers">
              {segment.details.map((passenger) => (
                <li key={passenger.reservation_detail_id}>
                  <div>
                    <strong>{passenger.passenger_name}</strong>
                    <span>{passenger.passenger_birth_date}</span>
                  </div>
                  <div>
                    <strong>{passenger.seat_no}</strong>
                    <span>{passenger.seat_class}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))}
        <section className="booking-section">
          <div className="booking-section-heading">
            <h2>예약자 정보</h2>
          </div>
          <dl className="reservation-contact">
            <div>
              <dt>이름</dt>
              <dd>{r.booker_name}</dd>
            </div>
            <div>
              <dt>생년월일</dt>
              <dd>{r.booker_birth_date}</dd>
            </div>
            <div>
              <dt>이메일</dt>
              <dd>{r.booker_email}</dd>
            </div>
            <div>
              <dt>전화번호</dt>
              <dd>{r.booker_phone}</dd>
            </div>
          </dl>
        </section>
      </div>
      <aside className="booking-summary" aria-label="예약 확인 요약">
        <div className="booking-summary-title">
          <span>예약 상태</span>
          <strong>{r.reservation_status}</strong>
        </div>
        <div className="booking-summary-body">
          <p className="small muted">예약번호</p>
          <strong className="reservation-number">{r.reservation_no}</strong>
          <p className="small muted">
            {r.trip_type === "round_trip" ? "왕복" : "편도"} · 탑승객 {segments[0]?.details.length ?? 0}명
          </p>
          <p className="small muted">
            예약일 {formatDate(r.reserved_at)} {formatTime(r.reserved_at)}
          </p>
          <div className="booking-price-breakdown">
            <div className="summary-line">
              <span>사용 포인트</span>
              <span>{r.used_points.toLocaleString()}P</span>
            </div>
            <div className="summary-line summary-total">
              <span>{r.reservation_status === "취소" ? "취소된 예약 금액" : "결제 금액"}</span>
              <strong>{formatWon(r.final_amount)}</strong>
            </div>
          </div>
          <div className="reservation-actions">
            <Link to="/" className="btn btn-primary btn-block">
              항공편 검색
            </Link>
            {onCancel &&
              r.reservation_status !== "취소" &&
              (reason ? (
                <p className="small muted">{reason}</p>
              ) : (
                <button className="btn-block btn-danger" disabled={cancelling} onClick={onCancel}>
                  {cancelling ? "취소 중..." : "예약 취소"}
                </button>
              ))}
          </div>
        </div>
      </aside>
    </div>
  );
}
