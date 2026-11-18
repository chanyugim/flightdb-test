import { requestApi } from "./client.js";

export async function getFlightWithSeats(id, signal) {
  const [flight, data] = await Promise.all([
    requestApi(`/flights/${id}`, { signal }),
    requestApi(`/flights/${id}/seats`, { signal }),
  ]);
  return { flight, seats: data.seats };
}

export function availableSeatMap(seats) {
  return new Map(seats.filter((seat) => seat.is_available).map((seat) => [seat.seat_id, seat]));
}
