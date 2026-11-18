import { requestApi } from "./client.js";

// 예약 관련 API 경로를 한곳에 모아 화면 코드와 요청 방식을 일치시킴.
export function createReservation(body, token, key, roundTrip = false) {
  return requestApi(roundTrip ? "/reservations/round-trip" : "/reservations", {
    method: "POST",
    token,
    body,
    headers: key ? { "Idempotency-Key": key } : {},
  });
}

export function getMemberReservation(reservationNo, token) {
  return requestApi(`/reservations/${reservationNo}`, { token });
}

export function cancelMemberReservation(reservationNo, token) {
  return requestApi(`/reservations/${reservationNo}/cancel`, { method: "POST", token });
}

export function lookupGuestReservation(body) {
  return requestApi("/reservations/guest/lookup", { method: "POST", body });
}

export function cancelGuestReservation(body) {
  return requestApi("/reservations/guest/cancel", { method: "POST", body });
}
