import { getFlightWithSeats, availableSeatMap } from "../api/flights";
import LoadingFlight from "../components/LoadingFlight";
import BookingPanel from "../components/BookingPanel";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { parseKstDate, formatWon } from "../utils/format.js";
import BookingHeader from "../components/BookingHeader";
import SeatFlightInfo from "../components/SeatFlightInfo";
import SeatLegend from "../components/SeatLegend";
import SeatMap from "../components/SeatMap";
import "../booking.css";

const MAX_SEATS = 9;

export default function FlightDetail() {
  const { flightId } = useParams();
  const navigate = useNavigate();
  const [flight, setFlight] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selected, setSelected] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setFlight(null);
    setLoading(true);
    setError("");
    getFlightWithSeats(flightId, controller.signal)
      .then(({ flight: detail, seats: availableSeats }) => {
        if (controller.signal.aborted) return;
        setFlight(detail);
        setSeats(availableSeats);
        const available = availableSeatMap(availableSeats);
        setSelected((previous) =>
          previous.flatMap((seat) => (available.has(seat.seat_id) ? [available.get(seat.seat_id)] : [])),
        );
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [flightId, revision]);

  const toggle = (seat) => {
    const exists = selected.some((item) => item.seat_id === seat.seat_id);
    if (!exists && selected.length >= MAX_SEATS) {
      setError(`최대 ${MAX_SEATS}석까지 선택할 수 있어요.`);
      return;
    }
    setError("");
    setSelected(exists ? selected.filter((item) => item.seat_id !== seat.seat_id) : [...selected, seat]);
  };

  if (!flight)
    return (
      <div className="container page">
        {loading ? (
          <LoadingFlight label="항공편과 좌석을 확인하고 있어요" />
        ) : (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </div>
    );

  const total = Number(flight.base_price) * selected.length;
  const bookable =
    ["예정", "지연"].includes(flight.flight_status) && parseKstDate(flight.departure_at) > new Date();

  return (
    <>
      <BookingHeader title="좌석 선택" step={0} />
      <div className="container booking-page seat-selection-page">
        <div className="booking-layout">
          <section className="booking-sheet" aria-label="항공편 및 좌석 선택">
            <SeatFlightInfo flight={flight} />
            <div className="booking-section-heading">
              <div>
                <h2>탑승할 좌석을 선택해 주세요</h2>
                <p>
                  탑승하실 인원에 맞춰 좌석을 선택해 주세요. 한 번에 최대 {MAX_SEATS}석까지 선택할 수 있어요.
                </p>
              </div>
            </div>
            <SeatLegend />
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            <SeatMap seats={seats} selected={selected} disabled={!bookable} onSelect={toggle} />
          </section>
          <BookingPanel
            title="선택한 좌석"
            meta={`편도 · ${selected.length}명`}
            amount={total}
            amountLabel="기본 운임 합계"
            actions={
              <div className="seat-selection-actions">
                <button
                  className="btn-primary btn-block"
                  disabled={!selected.length || !bookable}
                  onClick={() => navigate("/booking", { state: { flight, seats: selected } })}
                >
                  예약 정보 입력
                </button>
              </div>
            }
          >
            <p className="seat-selection-status" role="status">
              {!bookable
                ? "예약할 수 없는 항공편이에요."
                : selected.length
                  ? `${selected.length}개 좌석을 선택했어요.`
                  : "좌석표에서 원하는 좌석을 선택해 주세요."}
            </p>
            <ul className="selected-seat-list">
              {selected.map((seat, index) => (
                <li key={seat.seat_id}>
                  <span>탑승객 {index + 1}</span>
                  <strong>{seat.seat_no}</strong>
                  <span>{seat.seat_class}</span>
                </li>
              ))}
            </ul>
            <div className="booking-price-breakdown">
              <div className="summary-line">
                <span>1인 운임</span>
                <span>{formatWon(flight.base_price)}</span>
              </div>
              <div className="summary-line summary-total booking-repeated-total">
                <span>기본 운임 합계</span>
                <strong>{formatWon(total)}</strong>
              </div>
            </div>
            <p className="small muted">
              할인과 포인트는 다음 단계에서 적용해요. 좌석은 예약 완료 시 확보돼요.
            </p>
            <button className="btn-block" onClick={() => setRevision((value) => value + 1)}>
              좌석 새로고침
            </button>
          </BookingPanel>
        </div>
      </div>
    </>
  );
}
