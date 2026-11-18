import { formatDate } from "../utils/format.js";
import FlightSchedule from "./FlightSchedule";

export default function SeatFlightInfo({ flight }) {
  return (
    <div className="seat-flight-info">
      <div className="fc-airline">
        {flight.airline.name_ko} · {formatDate(flight.departure_at)}
        <span className="badge">{flight.flight_status}</span>
      </div>
      <FlightSchedule flight={flight} />
      <p className="small muted">출발·도착 시간은 한국 시간 기준이에요.</p>
    </div>
  );
}
