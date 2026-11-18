import { airportLabel } from "../api/labels";
import { cancellationReason } from "../api/reservationStatus";
import { Link } from "react-router-dom";
import { formatDate, formatDuration, formatTime, formatWon } from "../utils/format.js";

export default function ReservationCard({ reservation: r, onCancel, linkToDetail = false }) {
  const f = r.flight;
  const cancelled = r.reservation_status === "취소";
  const cancelReason = cancellationReason(r);
  // 예약 카드 공통 UI이며, props에 따라 상세 링크와 취소 버튼을 표시함.
  return (
    <div className="res-card">
      <div className="res-head">
        <strong>
          {linkToDetail ? (
            <Link to={`/reservations/${r.reservation_no}`}>{r.reservation_no}</Link>
          ) : (
            r.reservation_no
          )}
        </strong>
        <span className={`badge ${cancelled ? "off" : ""}`}>{r.reservation_status}</span>
      </div>
      {r.trip_type === "round_trip"
        ? r.segments.map((segment) => (
            <div key={segment.flight.flight_id}>
              <strong>{segment.direction === "outbound" ? "가는 편" : "오는 편"}</strong>
              <p>
                {segment.flight.airline.name_ko} · {airportLabel(segment.flight.departure_airport)} →{" "}
                {airportLabel(segment.flight.arrival_airport)}
                <br />
                {formatDate(segment.flight.departure_at)} {formatTime(segment.flight.departure_at)} →{" "}
                {formatDate(segment.flight.arrival_at)} {formatTime(segment.flight.arrival_at)}
              </p>
              <ul>
                {segment.details.map((d) => (
                  <li key={d.reservation_detail_id}>
                    {d.passenger_name} · {d.seat_no} ({d.seat_class})
                  </li>
                ))}
              </ul>
            </div>
          ))
        : f && (
            <>
              <div className="fc-airline">
                {f.airline.name_ko} · {formatDate(f.departure_at)}
                <span className="badge">{f.flight_status}</span>
              </div>
              <div className="fc-times">
                <div className="time">
                  <strong>{formatTime(f.departure_at)}</strong>
                  <small>{airportLabel(f.departure_airport)}</small>
                </div>
                <div className="fc-duration">
                  {formatDuration(f.departure_at, f.arrival_at)}
                  <span className="line" />
                </div>
                <div className="time">
                  <strong>{formatTime(f.arrival_at)}</strong>
                  <small>{airportLabel(f.arrival_airport)}</small>
                </div>
              </div>
            </>
          )}
      <ul>
        {(r.trip_type === "round_trip" ? [] : r.details).map((d) => (
          <li key={d.reservation_detail_id}>
            {d.seat_no} ({d.seat_class}) · {d.passenger_name}
          </li>
        ))}
      </ul>
      <div className="res-head">
        <span className="small muted">
          예약자 {r.booker_name} · 사용 포인트 {r.used_points}P
        </span>
        <strong>{formatWon(r.final_amount)}</strong>
      </div>
      {onCancel &&
        !cancelled &&
        (cancelReason ? (
          <p className="small muted">{cancelReason}</p>
        ) : (
          <button className="btn-danger" onClick={() => onCancel(r)}>
            예약 취소
          </button>
        ))}
    </div>
  );
}
