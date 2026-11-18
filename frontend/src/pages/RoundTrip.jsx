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

export default function RoundTrip() {
  const { outboundId, inboundId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [passengers, setPassengers] = useState([[null, null]]);
  const [person, setPerson] = useState(0);
  const [leg, setLeg] = useState(0);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    Promise.all([outboundId, inboundId].map((id) => getFlightWithSeats(id, controller.signal)))
      .then((rows) => {
        if (controller.signal.aborted) return;
        const available = rows.map((row) => availableSeatMap(row.seats));
        setData(rows);
        setPassengers((prev) => prev.map((pair) => pair.map((s, i) => available[i].get(s?.seat_id) ?? null)));
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [outboundId, inboundId, revision]);
  const choose = (seat) => {
    if (passengers.some((p, i) => i !== person && p[leg]?.seat_id === seat.seat_id)) {
      setError("다른 탑승객이 선택한 좌석이에요. 해당 탑승객을 선택해 좌석을 먼저 해제해 주세요.");
      return;
    }
    setError("");
    setPassengers((previous) =>
      previous.map((pair, index) => {
        if (index !== person) return pair;
        const updated = [...pair];
        updated[leg] = pair[leg]?.seat_id === seat.seat_id ? null : seat;
        return updated;
      }),
    );
  };
  const changePassengerCount = (event) => {
    const count = Number(event.target.value);
    if (count < passengers.length && !window.confirm("줄어드는 탑승객의 좌석 선택을 해제할까요?")) return;
    setPassengers((previous) => Array.from({ length: count }, (_, index) => previous[index] ?? [null, null]));
    setPerson((index) => Math.min(index, count - 1));
  };

  const continueBooking = () => {
    navigate("/booking", {
      state: {
        flight: data[0].flight,
        seats: passengers.map((pair) => pair[0]),
        inbound: data[1].flight,
        inboundSeats: passengers.map((pair) => pair[1]),
      },
    });
  };

  if (!data)
    return (
      <div className="container page">
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : (
          <LoadingFlight label="항공편과 좌석을 확인하고 있어요" />
        )}
      </div>
    );
  const bookable = data.every(
    ({ flight }) =>
      ["예정", "지연"].includes(flight.flight_status) && parseKstDate(flight.departure_at) > new Date(),
  );
  const missing = passengers.flatMap((p, i) =>
    p.flatMap((s, j) => (s ? [] : [`탑승객 ${i + 1} ${j ? "오는 편" : "가는 편"}`])),
  );
  const assigned = new Map(passengers.flatMap((p, i) => (p[leg] ? [[p[leg].seat_id, i]] : [])));
  const flight = data[leg].flight;
  const fare = data.reduce((sum, { flight: item }) => sum + Number(item.base_price), 0);
  return (
    <>
      <BookingHeader title="왕복 좌석 선택" step={0} />
      <div className="container booking-page seat-selection-page">
        <div className="booking-layout">
          <section className="booking-sheet" aria-label="항공편 및 좌석 선택">
            <div className="tabs" role="tablist" aria-label="여정">
              <button
                role="tab"
                aria-selected={leg === 0}
                className={leg === 0 ? "active" : ""}
                onClick={() => setLeg(0)}
              >
                가는 편
              </button>
              <button
                role="tab"
                aria-selected={leg === 1}
                className={leg === 1 ? "active" : ""}
                onClick={() => setLeg(1)}
              >
                오는 편
              </button>
            </div>
            <SeatFlightInfo flight={flight} />
            <div className="booking-section-heading">
              <div>
                <h2>
                  탑승객 {person + 1} · {leg ? "오는 편" : "가는 편"} 좌석 선택
                </h2>
                <p>탑승객마다 가는 편과 오는 편 좌석을 하나씩 선택해 주세요.</p>
              </div>
            </div>
            <SeatLegend roundTrip />
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            <SeatMap
              seats={data[leg].seats}
              selected={passengers[person][leg]}
              assigned={assigned}
              disabled={!bookable}
              onSelect={choose}
            />
          </section>
          <BookingPanel
            title="탑승객별 좌석"
            meta={`왕복 · ${passengers.length}명`}
            amount={fare * passengers.length}
            amountLabel="기본 운임 합계"
            actions={
              <div className="seat-selection-actions">
                <button
                  className="btn-primary btn-block"
                  disabled={!bookable || missing.length > 0}
                  onClick={continueBooking}
                >
                  예약 정보 입력
                </button>
              </div>
            }
          >
            <label className="seat-passenger-count">
              탑승 인원
              <select aria-label="탑승 인원" value={passengers.length} onChange={changePassengerCount}>
                {Array.from({ length: 9 }, (_, i) => (
                  <option key={i} value={i + 1}>
                    {i + 1}명
                  </option>
                ))}
              </select>
            </label>
            {passengers.map((p, i) => (
              <button
                className={`passenger-choice ${i === person ? "active" : ""}`}
                key={i}
                aria-pressed={i === person}
                onClick={() => setPerson(i)}
              >
                <strong>탑승객 {i + 1}</strong>
                <span>
                  가는 편 {p[0]?.seat_no || "미선택"} / 오는 편 {p[1]?.seat_no || "미선택"}
                </span>
              </button>
            ))}
            <div className="booking-price-breakdown">
              <div className="summary-line">
                <span>1인 왕복 운임</span>
                <span>{formatWon(fare)}</span>
              </div>
              <div className="summary-line summary-total booking-repeated-total">
                <span>기본 운임 합계</span>
                <strong>{formatWon(fare * passengers.length)}</strong>
              </div>
            </div>
            <p className="small muted">
              할인과 포인트는 다음 단계에서 적용해요. 좌석은 예약 완료 시 확보돼요.
            </p>
            <p role="status">
              {!bookable
                ? "예약할 수 없는 항공편이에요."
                : missing.length
                  ? `${missing[0]} 좌석을 선택해 주세요. (남은 선택 ${missing.length}개)`
                  : "모든 좌석을 선택했어요."}
            </p>
            <button className="btn-block" onClick={() => setRevision((r) => r + 1)}>
              좌석 새로고침
            </button>
          </BookingPanel>
        </div>
      </div>
    </>
  );
}
