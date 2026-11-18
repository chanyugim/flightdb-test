import { formatTime, formatDuration } from "../utils/format.js";
import { airportLabel } from "../api/labels";

function Stop({ airport, time }) {
  return (
    <div className="time schedule-stop">
      <strong>{formatTime(time)}</strong>
      <small>{airportLabel(airport)}</small>
    </div>
  );
}
export default function FlightSchedule({ flight }) {
  return (
    <div className="fc-times flight-schedule">
      <Stop airport={flight.departure_airport} time={flight.departure_at} />
      <div className="fc-duration schedule-duration">
        {formatDuration(flight.departure_at, flight.arrival_at)}
        <span className="line" aria-hidden="true" />
      </div>
      <Stop airport={flight.arrival_airport} time={flight.arrival_at} />
    </div>
  );
}
