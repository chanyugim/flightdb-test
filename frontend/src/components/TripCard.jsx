import FlightSchedule from "./FlightSchedule";
import { Link } from "react-router-dom";
import { formatDate, formatWon } from "../utils/format.js";

export default function TripCard({ trip, onChoose }) {
  return (
    <div className="flight-card">
      <div className="fc-main">
        {[trip.outbound, trip.inbound].map((f, i) => (
          <div className="trip-segment" key={f.flight_id}>
            <strong>
              {i ? "오는 편" : "가는 편"} · {f.airline.name_ko} · {formatDate(f.departure_at)}
            </strong>
            <FlightSchedule flight={f} />
          </div>
        ))}
      </div>
      <div className="fc-price">
        <strong>{formatWon(trip.total_base_price)}</strong>
        <small>1인 왕복 합계</small>
        <Link
          className="btn btn-primary"
          onClick={onChoose}
          to={`/round-trip/${trip.outbound.flight_id}/${trip.inbound.flight_id}`}
        >
          예매하기
        </Link>
      </div>
    </div>
  );
}
