import BookingPanel from "./BookingPanel";
import { airportLabel } from "../api/labels";
import { formatDate, formatTime, formatWon } from "../utils/format.js";

export default function BookingSummary({
  flight,
  inbound,
  seats,
  inboundSeats,
  base,
  discount,
  points,
  estimated,
  error,
  submitting,
}) {
  const legs = [{ flight, seats, label: inbound ? "가는 편" : "편도" }];
  if (inbound) legs.push({ flight: inbound, seats: inboundSeats, label: "오는 편" });
  return (
    <BookingPanel
      title="선택한 여정"
      meta={`${inbound ? "왕복" : "편도"} · ${seats.length}명`}
      amount={estimated}
      amountLabel="예상 결제 금액"
      notice={
        error && (
          <p className="error" role="alert">
            {error}
          </p>
        )
      }
      actions={
        <button type="submit" className="btn-primary btn-block" disabled={submitting}>
          {submitting ? "예약 중..." : "예약 확정하기"}
        </button>
      }
    >
      {legs.map(({ flight: leg, seats: selected, label }) => (
        <section className="booking-leg" key={label}>
          <h3>
            {label} <span>{leg.airline.name_ko}</span>
          </h3>
          <strong className="booking-route-codes">
            {leg.departure_airport.iata_code || leg.departure_airport.icao_code} <span>→</span>{" "}
            {leg.arrival_airport.iata_code || leg.arrival_airport.icao_code}
          </strong>
          <p>
            {airportLabel(leg.departure_airport)}
            <br />→ {airportLabel(leg.arrival_airport)}
          </p>
          <dl>
            <div>
              <dt>출발</dt>
              <dd>
                {formatDate(leg.departure_at)} {formatTime(leg.departure_at)}
              </dd>
            </div>
            <div>
              <dt>도착</dt>
              <dd>
                {formatDate(leg.arrival_at)} {formatTime(leg.arrival_at)}
              </dd>
            </div>
            <div>
              <dt>좌석</dt>
              <dd>{selected.map((seat) => `${seat.seat_no} (${seat.seat_class})`).join(", ")}</dd>
            </div>
          </dl>
        </section>
      ))}
      <span className="small muted">모든 일정은 한국 시간 기준이에요.</span>
      <div className="booking-price-breakdown">
        <div className="summary-line">
          <span>기본 운임 · {seats.length}명</span>
          <span>{formatWon(base)}</span>
        </div>
        <div className="summary-line">
          <span>프로모션 할인</span>
          <span>{discount ? `−${formatWon(discount)}` : "0원"}</span>
        </div>
        <div className="summary-line">
          <span>포인트 사용</span>
          <span>{points ? `−${formatWon(points)}` : "0원"}</span>
        </div>
        <div className="summary-line summary-total">
          <span>예상 결제 금액</span>
          <strong>{formatWon(estimated)}</strong>
        </div>
      </div>
      <p className="small muted">모의 결제로 예약 즉시 확정돼요. 최종 금액과 좌석은 예약 시 다시 확인해요.</p>
    </BookingPanel>
  );
}
