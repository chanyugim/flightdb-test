import { parseKstDate } from "../utils/format.js";

export function cancellationReason(reservation, now = Date.now()) {
  if (reservation.reservation_status === "취소") return "취소된 예약이에요.";
  const flights =
    reservation.trip_type === "round_trip"
      ? (reservation.segments ?? []).map((segment) => segment.flight)
      : [reservation.flight];
  if (!flights.length || flights.some((flight) => !flight)) return "항공편 정보를 확인할 수 없어요.";
  if (
    flights.some(
      (flight) =>
        flight.flight_status === "완료" ||
        (flight.flight_status !== "결항" && parseKstDate(flight.departure_at)?.getTime() <= now),
    )
  ) {
    return reservation.trip_type === "round_trip"
      ? "이미 출발하거나 운항이 완료된 구간이 있어 왕복 예약을 취소할 수 없어요."
      : "이미 출발했거나 운항이 완료되어 취소할 수 없어요.";
  }
  return "";
}
