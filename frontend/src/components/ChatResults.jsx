import { Link } from "react-router-dom";
import { useState } from "react";
import { airportLabel } from "../api/labels";
import { formatDate, formatKst, formatTime, formatWon } from "../utils/format.js";

function FlightSummary({ flight, direction }) {
  return (
    <div className="chat-flight-summary">
      <strong>
        {direction && `${direction} · `}
        {flight.airline.name_ko}
      </strong>
      <div className="chat-flight-stops">
        <div>
          <span className="small muted">출발</span>
          <span>{airportLabel(flight.departure_airport)}</span>
        </div>
        <span aria-hidden="true">→</span>
        <div>
          <span className="small muted">도착</span>
          <span>{airportLabel(flight.arrival_airport)}</span>
        </div>
      </div>
      <small>
        {formatDate(flight.departure_at)} {formatTime(flight.departure_at)} → {formatDate(flight.arrival_at)}{" "}
        {formatTime(flight.arrival_at)} · 한국 시각
      </small>
    </div>
  );
}

function RouteResults({ routes, title, send, busy }) {
  if (!routes?.length) return null;
  return (
    <section className="chat-route-list" aria-label={title}>
      <h3>{title}</h3>
      {routes.map((route, index) => (
        <div
          className="chat-result chat-route"
          key={`${route.departure_airport.airport_id}-${route.arrival_airport.airport_id}`}
        >
          <span className="chat-route-rank">{index + 1}</span>
          <div>
            <strong>
              {airportLabel(route.departure_airport)} → {airportLabel(route.arrival_airport)}
            </strong>
            <small className="muted">예약 {route.reservation_count}건</small>
          </div>
          <button
            className="chat-action"
            disabled={busy}
            onClick={() =>
              send(
                `${route.departure_airport.iata_code || route.departure_airport.icao_code}에서 ${route.arrival_airport.iata_code || route.arrival_airport.icao_code} 항공편을 보여줘`,
              )
            }
          >
            이 노선 검색
          </button>
        </div>
      ))}
    </section>
  );
}

export default function ChatResults({ data, close, send, busy }) {
  const [visible, setVisible] = useState(3);
  const flights = data.flights ?? [];
  const trips = data.round_trips ?? [];
  const total = flights.length + trips.length;
  const remaining = Math.max(0, total - visible);
  return (
    <>
      {data.clarification?.options?.map((option) => (
        <button className="chat-action" key={option.value} disabled={busy} onClick={() => send(option.value)}>
          {option.label}
        </button>
      ))}
      {flights.slice(0, visible).map((flight) => (
        <div className="chat-result chat-flight" key={flight.flight_id}>
          <FlightSummary flight={flight} />
          <div className="chat-result-footer">
            <div>
              <strong>{formatWon(flight.base_price)}</strong>
              <small className="muted">1인 기본 요금</small>
            </div>
            <Link className="btn btn-primary" to={`/flights/${flight.flight_id}`} onClick={close}>
              좌석 선택
            </Link>
          </div>
        </div>
      ))}
      {trips.slice(0, Math.max(0, visible - flights.length)).map((trip) => (
        <div className="chat-result chat-flight" key={`${trip.outbound.flight_id}-${trip.inbound.flight_id}`}>
          <FlightSummary flight={trip.outbound} direction="가는 편" />
          <FlightSummary flight={trip.inbound} direction="오는 편" />
          <div className="chat-result-footer">
            <div>
              <strong>{formatWon(trip.total_base_price)}</strong>
              <small className="muted">1인 왕복 기본 요금</small>
            </div>
            <Link
              className="btn btn-primary"
              to={`/round-trip/${trip.outbound.flight_id}/${trip.inbound.flight_id}`}
              onClick={close}
            >
              왕복 좌석 선택
            </Link>
          </div>
        </div>
      ))}
      {remaining > 0 && (
        <button className="chat-more" onClick={() => setVisible((count) => count + 3)}>
          항공편 {Math.min(3, remaining)}개 더 보기
        </button>
      )}
      {data.promotions?.map((promotion) => (
        <div className="chat-result" key={promotion.promotion_id}>
          <strong>{promotion.promotion_name}</strong> · {Number(promotion.discount_rate)}% 할인
          <p>
            예약 적용 기간 (한국 시각): {formatKst(promotion.start_at)} ~ {formatKst(promotion.end_at)}
          </p>
        </div>
      ))}
      {data.grades?.map((grade) => (
        <div className="chat-result" key={grade.grade_code}>
          {grade.grade_name} · 적립률 {Number(grade.point_rate)}% · 승급 기준 {grade.upgrade_requirement}
        </div>
      ))}
      {data.destinations?.map((airport) => (
        <button
          className="chat-action"
          key={airport.airport_id}
          disabled={busy}
          onClick={() => send(`${airport.iata_code || airport.icao_code} 도착 항공편을 보여줘`)}
        >
          {airport.name_ko} ({airport.iata_code || airport.icao_code})
        </button>
      ))}
      <RouteResults routes={data.popular_routes} title="많이 예약한 노선" send={send} busy={busy} />
      <RouteResults routes={data.frequent_routes} title="나의 자주 이용한 노선" send={send} busy={busy} />
      {data.navigation?.map((navigation) => (
        <Link
          key={navigation}
          className="btn chat-action"
          to={navigation === "login" ? "/login" : "/inquiry"}
          onClick={close}
        >
          {navigation === "login" ? "로그인" : "문의 작성"}
        </Link>
      ))}
      {data.has_more && (
        <p className="small muted">일부 결과를 표시했어요. 날짜나 가격 조건을 좁혀 주세요.</p>
      )}
    </>
  );
}
