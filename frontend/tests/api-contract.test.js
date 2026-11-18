import assert from "node:assert/strict";
import { test, afterEach } from "node:test";
import { requestApi } from "../src/api/client.js";
import { createReservation } from "../src/api/reservations.js";
import { chatSuggestions } from "../src/api/chatSuggestions.js";
import { airportLabel } from "../src/api/labels.js";
import { buildFlightSearch, resolveSearchAirports, searchCriteriaKey } from "../src/api/flightSearch.js";
globalThis.window = { location: { origin: "http://frontend.test" } };
const original = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = original;
});
test("공백만 있는 출발지는 제외하고 ICAO를 정확히 찾아 검색 코드로 변환함", async () => {
  let calls = 0;
  globalThis.fetch = async (url) => {
    calls++;
    assert.equal(new URL(url).searchParams.get("keyword"), "rjtt");
    assert.equal(new URL(url).searchParams.get("selectable_only"), "true");
    return Response.json({
      airports: [
        { iata_code: "XXX", icao_code: "ZZZZ" },
        { iata_code: "HND", icao_code: "RJTT" },
      ],
    });
  };
  const result = await resolveSearchAirports({ departure: "  ", arrival: "  rjtt " });
  assert.equal(result.departure, "");
  assert.equal(result.arrival, "HND");
  assert.equal(calls, 1);
});
test("도시 검색의 복수 공항을 임의로 확정하지 않음", async () => {
  globalThis.fetch = async () => Response.json({ airports: [{ iata_code: "HND" }, { iata_code: "NRT" }] });
  await assert.rejects(resolveSearchAirports({ arrival: "도쿄" }), /공항을 선택/);
});
test("검색 조건 변환은 왕복 날짜·별도 도착 날짜·제외 항공사를 보존함", () => {
  const conditions = {
    trip_type: "round_trip",
    date: "2027-12-13",
    return_date: "2027-12-17",
    arrival_date: "2027-12-14",
    departure_time_band: "evening",
    arrival_time_band: "morning",
    return_arrival_date: "2027-12-18",
    return_departure_time_band: "evening",
    return_arrival_time_band: "dawn",
    exclude_airlines: "KE, OZ",
    airline: "",
    sort_by: "price",
    sort_order: "asc",
  };
  const request = buildFlightSearch(conditions, 20, 20);
  assert.equal(request.path, "/flights/round-trips");
  assert.equal(request.query.arrival_from, "2027-12-14T06:00:00");
  assert.equal(request.query.departure_to, "2027-12-13T23:59:59");
  assert.equal(request.query.return_date, "2027-12-17");
  assert.equal(request.query.return_departure_from, "2027-12-17T18:00:00");
  assert.equal(request.query.return_arrival_to, "2027-12-18T05:59:59");
  const oneWay = buildFlightSearch({ ...conditions, trip_type: "one_way" }, 0, 10);
  assert.equal(oneWay.query.return_departure_from, undefined);
  assert.equal(oneWay.query.return_arrival_date, undefined);
  assert.deepEqual(request.query.exclude_airlines, ["KE", "OZ"]);
  assert.equal(
    searchCriteriaKey(conditions),
    searchCriteriaKey({ ...conditions, exclude_airlines: "", sort_order: "desc" }),
  );
  assert.notEqual(searchCriteriaKey(conditions), searchCriteriaKey({ ...conditions, date: "2027-12-12" }));
});
test("도착 날짜를 따로 선택하지 않으면 상단의 각 출발 날짜를 사용함", () => {
  const conditions = {
    trip_type: "round_trip", date: "2027-12-13", return_date: "2027-12-17",
    arrival_date: "", return_arrival_date: "", exclude_airlines: "",
    arrival_time_band: "afternoon", return_arrival_time_band: "evening",
  };
  const { query } = buildFlightSearch(conditions, 0, 10);
  assert.equal(query.arrival_from, "2027-12-13T12:00:00");
  assert.equal(query.return_arrival_to, "2027-12-17T23:59:59");
  const changed = buildFlightSearch({ ...conditions, return_date: "2027-12-20" }, 0, 10);
  assert.equal(changed.query.return_arrival_from, "2027-12-20T18:00:00");
});

test("후속 질문은 응답 주제를 따르고 추가 확인 선택지와 중복하지 않음", () => {
  assert.deepEqual(chatSuggestions({ clarification: { options: [{ value: "ICN" }] } }), []);
  assert.ok(chatSuggestions({ flights: [{}] }).includes("가격이 저렴한 순으로 보여줘"));
  assert.ok(chatSuggestions({ promotions: [{}] }).includes("회원 등급별 혜택을 알려줘"));
});
test("공항 표시에 도시·이름과 IATA 또는 ICAO를 사용함", () => {
  assert.equal(
    airportLabel({ city: "서울", name_ko: "인천국제공항", iata_code: "ICN" }),
    "서울 · 인천국제공항 (ICN)",
  );
  assert.equal(airportLabel({ name_ko: "공항", icao_code: "RKSI" }), "공항 (RKSI)");
});
test("제외 항공사를 반복 쿼리로 전달함", async () => {
  globalThis.fetch = async (url) => {
    assert.deepEqual(new URL(url).searchParams.getAll("exclude_airlines"), ["KE", "OZ"]);
    return Response.json({});
  };
  await requestApi("/flights", { query: { exclude_airlines: ["KE", "OZ"] } });
});
test("왕복 재시도에 같은 멱등 키와 두 좌석을 전달함", async () => {
  const body = { passengers: [{ outbound_seat_id: 1, inbound_seat_id: 2 }] };
  globalThis.fetch = async (url, options) => {
    assert.equal(new URL(url).pathname, "/api/reservations/round-trip");
    assert.equal(options.headers["Idempotency-Key"], "same-key");
    assert.deepEqual(JSON.parse(options.body), body);
    return Response.json({});
  };
  await createReservation(body, null, "same-key", true);
  await createReservation(body, null, "same-key", true);
});
test("HTML 응답을 정상 API 데이터로 처리하지 않음", async () => {
  globalThis.fetch = async () => new Response("<html>warning</html>");
  await assert.rejects(requestApi("/flights"), /서버 주소/);
});
test("호출 제한의 재시도 시간을 보존함", async () => {
  globalThis.fetch = async () =>
    Response.json(
      { detail: "잠시 후 요청해 주세요", request_id: "test-id" },
      { status: 429, headers: { "Retry-After": "25" } },
    );
  await assert.rejects(
    requestApi("/chatbot/messages"),
    (e) => e.retryAfter === 25 && !e.message.includes("test-id"),
  );
});
