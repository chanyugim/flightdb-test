import LoadingFlight from "../components/LoadingFlight";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { formatDate, formatWon } from "../utils/format.js";
import { requestApi } from "../api/client";
import { buildFlightSearch, resolveSearchAirports, searchCriteriaKey } from "../api/flightSearch";
import { airportLabel } from "../api/labels";
import AirlineFilter from "../components/AirlineFilter";
import AirportInput from "../components/AirportInput";
import FlightSchedule from "../components/FlightSchedule";
import JourneyTabs from "../components/JourneyTabs";
import ResponsiveFilters from "../components/ResponsiveFilters";
import FlightTimeFilters from "../components/FlightTimeFilters";
import PromotionStrip from "../components/PromotionStrip";
import TripCard from "../components/TripCard";
import { useAuth } from "../context/AuthContext";

const LIMIT = 10;

const SORTS = [
  { label: "가격 낮은순", sort_by: "price", sort_order: "asc" },
  { label: "가격 높은순", sort_by: "price", sort_order: "desc" },
  { label: "빠른 출발순", sort_by: "departure_at", sort_order: "asc" },
  { label: "빠른 도착순", sort_by: "arrival_at", sort_order: "asc" },
];

const STATUS_BADGE = { 예정: "", 지연: "warn", 결항: "off", 완료: "off" };

const INITIAL_SEARCH = {
  departure: "",
  arrival: "",
  date: "",
  trip_type: "one_way",
  return_date: "",
  arrival_date: "",
  exclude_airlines: "",
  seat_class: "",
  airline: "",
  min_price: "",
  max_price: "",
  departure_time_band: "",
  arrival_time_band: "",
  return_arrival_date: "",
  return_departure_time_band: "",
  return_arrival_time_band: "",
  sort_by: "departure_at",
  sort_order: "asc",
  bookable_only: true,
};

export default function Home() {
  const { token, isLoggedIn } = useAuth();
  const [form, setForm] = useState(INITIAL_SEARCH);
  const [resetVersion, setResetVersion] = useState(0);
  const [result, setResult] = useState(null);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [routes, setRoutes] = useState([]);
  const sequence = useRef(0);
  const submitted = useRef(null);
  const criteria = useRef(null);
  const [promotions, setPromotions] = useState([]);
  const [filtersOpen, setFiltersOpen] = useState(false);
  useEffect(() => {
    requestApi("/promotions")
      .then(setPromotions)
      .catch(() => {});
  }, []);

  const set = (key) => (value) => setForm((f) => ({
    ...f,
    [key]: value,
    ...(key === "date" ? { arrival_date: "" } : {}),
    ...(key === "return_date" ? { return_arrival_date: "" } : {}),
  }));

  const search = async (nextOffset = 0, current = form) => {
    const seq = ++sequence.current;
    if (
      current.trip_type === "round_trip" &&
      (!current.date || !current.return_date || current.return_date < current.date)
    ) {
      setError("왕복 검색은 가는 날과 그 이후의 오는 날을 선택해 주세요.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      current = await resolveSearchAirports(current);
      if (seq !== sequence.current) return;

      const key = searchCriteriaKey(current);
      if (criteria.current !== key) {
        current = { ...current, airline: "", exclude_airlines: "" };
        setForm((previous) => ({ ...previous, airline: "", exclude_airlines: "" }));
        criteria.current = key;
      }

      submitted.current = current;
      const { path, query } = buildFlightSearch(current, nextOffset, LIMIT);
      const data = await requestApi(path, { query });
      if (seq !== sequence.current) return;
      setResult(data);
      setOffset(nextOffset);
    } catch (e) {
      if (seq === sequence.current) setError(e.message);
    } finally {
      if (seq === sequence.current) setLoading(false);
    }
  };

  useEffect(() => {
    // 시간대는 필터 적용 시 조회하고, 정렬·등급 변경은 바로 반영함.
    search(0);
  }, [
    form.sort_by,
    form.sort_order,
    form.seat_class,
    form.bookable_only,
    resetVersion,
  ]);

  useEffect(() => {
    if (!token) {
      setRoutes([]);
      return;
    }
    let active = true;
    // 로그인 회원에게 자주 이용한 노선을 검색 바로가기로 표시함.
    requestApi("/me/recommended-routes", { token, query: { limit: 5 } })
      .then((data) => {
        if (active) setRoutes(data);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [token]);

  const onSubmit = (e) => {
    e.preventDefault();
    search(0);
  };

  const swap = () => setForm((f) => ({ ...f, departure: f.arrival, arrival: f.departure }));

  const resetSearch = () => {
    sequence.current += 1;
    submitted.current = null;
    criteria.current = null;
    setForm({ ...INITIAL_SEARCH });
    setResult(null);
    setOffset(0);
    setError("");
    setResetVersion((version) => version + 1);
  };

  const applyRoute = (r) => {
    const next = {
      ...form,
      departure: r.departure_airport.iata_code ?? "",
      arrival: r.arrival_airport.iata_code ?? "",
    };
    setForm(next);
    search(0, next);
  };

  return (
    <>
      <section className="hero">
        <div className="container">
          <form onSubmit={onSubmit}>
            <div className="search-toolbar">
              <JourneyTabs value={form.trip_type} onChange={set("trip_type")} />
              <button type="button" className="search-reset" onClick={resetSearch}>
                <span aria-hidden="true">↺</span> 검색 초기화
              </button>
            </div>
            <div className={`search-bar ${form.trip_type === "round_trip" ? "round-search" : ""}`}>
              <AirportInput label="출발지" value={form.departure} onChange={set("departure")} />
              <AirportInput label="도착지" value={form.arrival} onChange={set("arrival")} />
              <button type="button" className="swap" onClick={swap} aria-label="출발·도착 바꾸기">
                ⇄
              </button>
              <div className="field">
                <span className="field-label">가는 날</span>
                <input type="date" value={form.date} onChange={(e) => set("date")(e.target.value)} />
              </div>
              {form.trip_type === "round_trip" && (
                <div className="field">
                  <label className="field-label" htmlFor="return-date">
                    오는 날
                  </label>
                  <input
                    id="return-date"
                    type="date"
                    min={form.date}
                    required
                    value={form.return_date}
                    onChange={(e) => set("return_date")(e.target.value)}
                  />
                </div>
              )}
              <div className="field seat-class-field">
                <span className="field-label">좌석 등급</span>
                <select value={form.seat_class} onChange={(e) => set("seat_class")(e.target.value)}>
                  <option value="">전체</option>
                  <option value="이코노미">이코노미</option>
                  <option value="비즈니스">비즈니스</option>
                  <option value="퍼스트">퍼스트</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                검색하기
              </button>
            </div>
          </form>
          {isLoggedIn && routes.length > 0 && (
            <div className="chips">
              <span>자주 가는 노선</span>
              {routes.map((r, i) => (
                <button key={i} type="button" className="chip" onClick={() => applyRoute(r)}>
                  {airportLabel(r.departure_airport)} → {airportLabel(r.arrival_airport)} (
                  {r.reservation_count}회)
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      <div className="container page">
        <div className="home-announcements">
          <PromotionStrip promotions={promotions} />
        </div>
        <div className="results-layout">
          <ResponsiveFilters onApply={() => search(0)} open={filtersOpen} onOpenChange={setFiltersOpen}>
            <p className="small muted">모든 시간 조건은 한국 시간 기준이에요.</p>
            <FlightTimeFilters form={form} onChange={(field, value) => set(field)(value)} />
            {form.trip_type === "round_trip" && (
              <FlightTimeFilters form={form} inbound onChange={(field, value) => set(field)(value)} />
            )}
            <div className="form-row">
              <label>가격 범위 (1인, 왕복은 두 편 합계)</label>
              <div className="price-range">
                <input
                  type="number"
                  min="0"
                  placeholder="최소"
                  value={form.min_price}
                  onChange={(e) => set("min_price")(e.target.value)}
                />
                ~
                <input
                  type="number"
                  min="0"
                  placeholder="최대"
                  value={form.max_price}
                  onChange={(e) => set("max_price")(e.target.value)}
                />
              </div>
            </div>
            <AirlineFilter
              items={result?.available_airlines ?? []}
              excluded={form.exclude_airlines}
              loading={loading}
              onChange={(exclude_airlines) => {
                const next = { ...(submitted.current || form), airline: "", exclude_airlines };
                setForm((f) => ({ ...f, airline: "", exclude_airlines }));
                search(0, next);
              }}
            />
            <button type="button" className="btn-block filter-apply" onClick={() => search(0)}>
              필터 적용
            </button>
            <div className="form-row" style={{ marginTop: 16 }}>
              <label className="check">
                <input
                  type="checkbox"
                  checked={form.bookable_only}
                  onChange={(e) => set("bookable_only")(e.target.checked)}
                />
                예약 가능한 항공편만
              </label>
            </div>
          </ResponsiveFilters>

          <div>
            <div className="sort-tabs">
              {SORTS.map((s) => (
                <button
                  key={s.label}
                  className={
                    form.sort_by === s.sort_by && form.sort_order === s.sort_order ? "active" : undefined
                  }
                  onClick={() => setForm((f) => ({ ...f, sort_by: s.sort_by, sort_order: s.sort_order }))}
                >
                  {form.trip_type === "round_trip" && s.sort_by !== "price"
                    ? `${s.sort_by === "departure_at" ? "가는 편" : "오는 편"} ${s.label}`
                    : s.label}
                </button>
              ))}
              <button
                className="mobile-filter-trigger"
                type="button"
                aria-label="검색 필터 열기"
                title="검색 필터"
                aria-haspopup="dialog"
                aria-controls="mobile-filter-dialog"
                aria-expanded={filtersOpen}
                onClick={() => setFiltersOpen(true)}
              >
                <svg
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  aria-hidden="true"
                >
                  <path d="M4 7h16M4 17h16" />
                  <circle cx="9" cy="7" r="3" fill="currentColor" />
                  <circle cx="15" cy="17" r="3" fill="currentColor" />
                </svg>
              </button>
            </div>

            {error && <p className="error">{error}</p>}
            {loading && <LoadingFlight label="조건에 맞는 항공편을 찾고 있어요" />}

            {result && !loading && (
              <>
                <p className="muted small">총 {result.total}건 · 한국 시간 기준</p>
                {result.total === 0 && (
                  <p className="empty">
                    검색 결과가 없습니다.
                    <br />
                    조건을 바꾸거나 &quot;예약 가능한 항공편만&quot;을 해제해 보세요.
                  </p>
                )}
                {result.round_trips?.map((trip) => (
                  <TripCard key={`${trip.outbound.flight_id}-${trip.inbound.flight_id}`} trip={trip} />
                ))}
                {(result.flights ?? []).map((f) => (
                  <div className="flight-card" key={f.flight_id}>
                    <div className="fc-main">
                      <div className="fc-airline">
                        {f.airline.name_ko}
                        <span className={`badge ${STATUS_BADGE[f.flight_status] ?? ""}`}>
                          {f.flight_status}
                        </span>
                        <span>{formatDate(f.departure_at)}</span>
                      </div>
                      <FlightSchedule flight={f} />
                    </div>
                    <div className="fc-price">
                      <strong>{formatWon(f.base_price)}</strong>
                      <small className="muted">1인 · 잔여 {f.remaining_seats}석</small>
                      <Link to={`/flights/${f.flight_id}`} className="btn btn-primary">
                        예매하기
                      </Link>
                    </div>
                  </div>
                ))}
                <div className="pager">
                  <button
                    disabled={offset === 0}
                    onClick={() => search(Math.max(0, offset - LIMIT), submitted.current)}
                  >
                    이전
                  </button>
                  <button
                    disabled={offset + LIMIT >= result.total}
                    onClick={() => search(offset + LIMIT, submitted.current)}
                  >
                    다음
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
