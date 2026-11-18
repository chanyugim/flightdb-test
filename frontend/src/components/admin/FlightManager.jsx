import { useEffect, useState } from "react";
import { formatKst, formatWon, toDateTimeInput } from "../../utils/format.js";
import { requestApi } from "../../api/client";
import { airportLabel } from "../../api/labels";

const STATUSES = ["예정", "지연", "결항", "완료"];

const emptyFlightForm = () => ({
  airline_id: "",
  departure_airport_id: "",
  arrival_airport_id: "",
  departure_at: "",
  arrival_at: "",
  base_price: "",
  flight_status: "예정",
});

// 관리자가 새 항공편에 함께 등록할 시연용 좌석 배치(총 176석).
function defaultSeatLayout() {
  const seats = [];
  const addRows = (start, end, letters, seatClass) => {
    for (let row = start; row <= end; row += 1) {
      for (const letter of letters) seats.push({ seat_no: `${row}${letter}`, seat_class: seatClass });
    }
  };
  addRows(1, 2, "ABCD", "퍼스트");
  addRows(3, 8, "ABCD", "비즈니스");
  addRows(10, 33, "ABCDEF", "이코노미");
  return seats;
}

export default function FlightManager({ data, token, load }) {
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [airlines, setAirlines] = useState([]);
  const [airports, setAirports] = useState([]);
  const [flightForm, setFlightForm] = useState(emptyFlightForm);
  const [editingFlightId, setEditingFlightId] = useState(null);
  const [savingFlight, setSavingFlight] = useState(false);
  const [seatActionId, setSeatActionId] = useState(null);

  useEffect(() => {
    // 항공편 등록 폼의 선택지를 불러오며, 탭을 벗어나면 늦게 온 응답을 무시함.
    let active = true;
    Promise.all([
      requestApi("/airlines", { query: { limit: 100 } }),
      requestApi("/airports", { query: { limit: 100 } }),
    ])
      .then(([airlineData, airportData]) => {
        if (!active) return;
        setAirlines(airlineData.airlines);
        setAirports(airportData.airports);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, []);

  const resetFlightForm = () => {
    setFlightForm(emptyFlightForm());
    setEditingFlightId(null);
  };

  const editFlight = (flight) => {
    // 목록의 항공편 데이터를 수정 폼이 쓰는 문자열 값으로 옮김.
    setEditingFlightId(flight.flight_id);
    setFlightForm({
      airline_id: String(flight.airline.airline_id),
      departure_airport_id: String(flight.departure_airport.airport_id),
      arrival_airport_id: String(flight.arrival_airport.airport_id),
      departure_at: toDateTimeInput(flight.departure_at),
      arrival_at: toDateTimeInput(flight.arrival_at),
      base_price: String(flight.base_price),
      flight_status: flight.flight_status,
    });
    setNotice("");
    setError("");
  };

  const saveFlight = async (e) => {
    e.preventDefault();
    setSavingFlight(true);
    setError("");
    setNotice("");
    try {
      // 수정은 PATCH, 신규 등록은 POST를 사용하고 생성된 항공편에 좌석을 추가함.
      const commonFields = {
        departure_at: flightForm.departure_at,
        arrival_at: flightForm.arrival_at,
        base_price: Number(flightForm.base_price),
        flight_status: flightForm.flight_status,
      };
      if (editingFlightId) {
        await requestApi(`/admin/flights/${editingFlightId}`, {
          method: "PATCH",
          token,
          body: commonFields,
        });
        setNotice(`항공편 #${editingFlightId} 정보를 수정했습니다.`);
        resetFlightForm();
      } else {
        const created = await requestApi("/admin/flights", {
          method: "POST",
          token,
          body: {
            ...commonFields,
            airline_id: Number(flightForm.airline_id),
            departure_airport_id: Number(flightForm.departure_airport_id),
            arrival_airport_id: Number(flightForm.arrival_airport_id),
          },
        });
        resetFlightForm();
        try {
          await addDefaultSeats(created.flight_id, false);
        } catch (seatError) {
          setNotice(
            `항공편 #${created.flight_id}은 등록됐지만 좌석 배치 등록에 실패했습니다. 아래에서 좌석 배치를 다시 등록할 수 있습니다. (${seatError.message})`,
          );
        }
      }
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setSavingFlight(false);
    }
  };

  const addDefaultSeats = async (flightId, refresh = true) => {
    setSeatActionId(flightId);
    try {
      // 이미 존재하는 좌석 번호는 제외하여 기본 배치를 중복 등록하지 않음.
      const current = await requestApi(`/admin/flights/${flightId}/seats`, { token });
      const existing = new Set(current.seats.map((seat) => seat.seat_no.toUpperCase()));
      const seats = defaultSeatLayout().filter((seat) => !existing.has(seat.seat_no));
      if (seats.length === 0) {
        setNotice(`항공편 #${flightId}에는 기본 좌석 배치가 이미 등록되어 있습니다.`);
        return;
      }
      await requestApi(`/admin/flights/${flightId}/seats`, {
        method: "POST",
        token,
        body: { seats },
      });
      setNotice(`항공편 #${flightId}에 기본 좌석 ${seats.length}석을 추가했습니다.`);
      if (refresh) await load();
    } finally {
      setSeatActionId(null);
    }
  };

  return (
    <section className="admin-flight-manager">
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="notice" role="status">
          {notice}
        </p>
      )}
      <>
        <form className="card" onSubmit={saveFlight} style={{ marginBottom: 16 }}>
          <h2 style={{ marginTop: 0 }}>
            {editingFlightId ? `항공편 #${editingFlightId} 수정` : "항공편 등록"}
          </h2>
          {editingFlightId ? (
            <p className="small muted">
              항공사와 노선은 등록 후 변경할 수 없습니다. 운항 상태, 출·도착 시각, 요금을 수정할 수 있습니다.
            </p>
          ) : (
            <div className="two-col">
              <div className="form-row">
                <label>항공사</label>
                <select
                  value={flightForm.airline_id}
                  onChange={(e) => setFlightForm((f) => ({ ...f, airline_id: e.target.value }))}
                  required
                >
                  <option value="">항공사 선택</option>
                  {airlines.map((airline) => (
                    <option key={airline.airline_id} value={airline.airline_id}>
                      {airline.name_ko} ({airline.iata_code ?? airline.icao_code})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <label>출발 공항</label>
                <select
                  value={flightForm.departure_airport_id}
                  onChange={(e) => setFlightForm((f) => ({ ...f, departure_airport_id: e.target.value }))}
                  required
                >
                  <option value="">출발 공항 선택</option>
                  {airports.map((airport) => (
                    <option key={airport.airport_id} value={airport.airport_id}>
                      {airport.name_ko} ({airport.iata_code ?? airport.icao_code})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <label>도착 공항</label>
                <select
                  value={flightForm.arrival_airport_id}
                  onChange={(e) => setFlightForm((f) => ({ ...f, arrival_airport_id: e.target.value }))}
                  required
                >
                  <option value="">도착 공항 선택</option>
                  {airports.map((airport) => (
                    <option key={airport.airport_id} value={airport.airport_id}>
                      {airport.name_ko} ({airport.iata_code ?? airport.icao_code})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
          <div className="two-col">
            <div className="form-row">
              <label>출발 시각</label>
              <input
                type="datetime-local"
                value={flightForm.departure_at}
                onChange={(e) => setFlightForm((f) => ({ ...f, departure_at: e.target.value }))}
                required
              />
            </div>
            <div className="form-row">
              <label>도착 시각</label>
              <input
                type="datetime-local"
                value={flightForm.arrival_at}
                onChange={(e) => setFlightForm((f) => ({ ...f, arrival_at: e.target.value }))}
                required
              />
            </div>
            <div className="form-row">
              <label>기본 운임 (원)</label>
              <input
                type="number"
                min="0"
                step="1"
                value={flightForm.base_price}
                onChange={(e) => setFlightForm((f) => ({ ...f, base_price: e.target.value }))}
                required
              />
            </div>
            <div className="form-row">
              <label>운항 상태</label>
              <select
                value={flightForm.flight_status}
                onChange={(e) => setFlightForm((f) => ({ ...f, flight_status: e.target.value }))}
              >
                {STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {!editingFlightId && (
            <p className="small muted">
              신규 항공편에는 시연용 기본 좌석 배치 176석(퍼스트·비즈니스·이코노미)을 함께 등록합니다.
            </p>
          )}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="submit" className="btn-primary" disabled={savingFlight}>
              {savingFlight ? "저장 중..." : editingFlightId ? "수정 저장" : "항공편 등록"}
            </button>
            {editingFlightId && (
              <button type="button" className="btn" onClick={resetFlightForm}>
                수정 취소
              </button>
            )}
          </div>
        </form>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>항공사</th>
              <th>노선</th>
              <th>출발</th>
              <th>요금</th>
              <th>상태</th>
              <th>잔여</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody>
            {data.map((f) => (
              <tr key={f.flight_id}>
                <td>{f.flight_id}</td>
                <td>{f.airline.name_ko}</td>
                <td>
                  {airportLabel(f.departure_airport)} → {airportLabel(f.arrival_airport)}
                </td>
                <td>{formatKst(f.departure_at)}</td>
                <td>{formatWon(f.base_price)}</td>
                <td>{f.flight_status}</td>
                <td>{f.remaining_seats}</td>
                <td>
                  <button type="button" className="btn" onClick={() => editFlight(f)}>
                    수정
                  </button>
                  <button
                    type="button"
                    className="btn"
                    style={{ marginLeft: 6 }}
                    disabled={seatActionId === f.flight_id}
                    onClick={() => addDefaultSeats(f.flight_id).catch((e) => setError(e.message))}
                  >
                    {seatActionId === f.flight_id ? "등록 중..." : "기본 좌석 배치"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </>
    </section>
  );
}
