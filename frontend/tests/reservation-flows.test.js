import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

globalThis.window = { location: { origin: "http://frontend.test" } };

const {
  cancelGuestReservation,
  cancelMemberReservation,
  createReservation,
  getMemberReservation,
  lookupGuestReservation,
} = await import("../src/api/reservations.js");

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

function mockApi(responses) {
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: new URL(url), options });
    const body = responses.shift() ?? {};
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  return calls;
}

function bodyOf(call) {
  return JSON.parse(call.options.body);
}

test("회원 예약 생성·조회·취소에 인증 토큰을 전달함", async () => {
  const calls = mockApi([
    { reservation_no: "R-MEMBER-TEST" },
    { reservation_no: "R-MEMBER-TEST", reservation_status: "확정" },
    { message: "취소 완료" },
    { reservation_no: "R-MEMBER-TEST", reservation_status: "취소" },
  ]);
  const payload = {
    booker_name: "테스트 회원",
    booker_email: "member@example.test",
    booker_phone: "010-0000-0001",
    booker_birth_date: "2000-01-01",
    used_points: 0,
    passengers: [{ seat_id: 101, passenger_name: "테스트 회원", passenger_birth_date: "2000-01-01" }],
  };

  const created = await createReservation(payload, "member-token");
  const found = await getMemberReservation(created.reservation_no, "member-token");
  await cancelMemberReservation(created.reservation_no, "member-token");
  const cancelled = await getMemberReservation(created.reservation_no, "member-token");

  assert.equal(found.reservation_status, "확정");
  assert.equal(cancelled.reservation_status, "취소");
  assert.equal(calls[0].url.pathname, "/api/reservations");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.headers.Authorization, "Bearer member-token");
  assert.deepEqual(bodyOf(calls[0]), payload);
  assert.equal(calls[1].url.pathname, "/api/reservations/R-MEMBER-TEST");
  assert.equal(calls[1].options.headers.Authorization, "Bearer member-token");
  assert.equal(calls[2].url.pathname, "/api/reservations/R-MEMBER-TEST/cancel");
  assert.equal(calls[2].options.method, "POST");
  assert.equal(calls[2].options.headers.Authorization, "Bearer member-token");
});

test("비회원 예약 생성·조회·취소 요청에 예약자 정보를 전달하고 인증 토큰은 생략함", async () => {
  const calls = mockApi([
    { reservation_no: "R-GUEST-TEST" },
    { reservation_no: "R-GUEST-TEST", reservation_status: "확정" },
    { message: "취소 완료" },
    { reservation_no: "R-GUEST-TEST", reservation_status: "취소" },
  ]);
  const guest = {
    reservation_no: "R-GUEST-TEST",
    booker_email: "guest@example.test",
    booker_phone: "010-0000-0002",
  };
  const payload = {
    booker_name: "테스트 비회원",
    booker_email: guest.booker_email,
    booker_phone: guest.booker_phone,
    booker_birth_date: "2000-01-01",
    used_points: 0,
    passengers: [{ seat_id: 102, passenger_name: "테스트 비회원", passenger_birth_date: "2000-01-01" }],
  };

  await createReservation(payload);
  const found = await lookupGuestReservation(guest);
  await cancelGuestReservation(guest);
  const cancelled = await lookupGuestReservation(guest);

  assert.equal(found.reservation_status, "확정");
  assert.equal(cancelled.reservation_status, "취소");
  assert.equal(calls[0].url.pathname, "/api/reservations");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.headers.Authorization, undefined);
  assert.deepEqual(bodyOf(calls[0]), payload);
  assert.equal(calls[1].url.pathname, "/api/reservations/guest/lookup");
  assert.deepEqual(bodyOf(calls[1]), guest);
  assert.equal(calls[2].url.pathname, "/api/reservations/guest/cancel");
  assert.deepEqual(bodyOf(calls[2]), guest);
  assert.equal(calls[3].url.pathname, "/api/reservations/guest/lookup");
  for (const call of calls.slice(1)) {
    assert.equal(call.options.headers.Authorization, undefined);
  }
});
