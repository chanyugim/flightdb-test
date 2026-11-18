import { requestApi } from "./client.js";

const TIME_BANDS = {
  dawn: ["00:00:00", "05:59:59"],
  morning: ["06:00:00", "11:59:59"],
  afternoon: ["12:00:00", "17:59:59"],
  evening: ["18:00:00", "23:59:59"],
};

export async function resolveSearchAirports(conditions) {
  const resolved = { ...conditions };
  for (const field of ["departure", "arrival"]) {
    const value = (conditions[field] || "").trim();
    if (!value) {
      resolved[field] = "";
      continue;
    }

    const data = await requestApi("/airports", {
      query: { keyword: value, limit: 10, selectable_only: true },
    });
    const exact = data.airports.find((airport) =>
      [airport.iata_code, airport.icao_code].some((code) => code?.toUpperCase() === value.toUpperCase()),
    );
    const airport = exact || (data.airports.length === 1 ? data.airports[0] : null);
    if (!airport) throw new Error("도시·공항 검색 목록에서 이용할 공항을 선택해 주세요.");
    if (!airport.iata_code && !airport.icao_code)
      throw new Error("검색에 사용할 공항 코드가 없어요. 다른 공항을 선택해 주세요.");
    resolved[field] = airport.iata_code || airport.icao_code;
  }
  return resolved;
}

export function searchCriteriaKey(conditions) {
  // 항공사 선택과 정렬만 바뀐 경우에는 기존 항공사 선택을 유지함.
  const ignoredFields = new Set(["exclude_airlines", "airline", "sort_by", "sort_order"]);
  return JSON.stringify(Object.entries(conditions).filter(([key]) => !ignoredFields.has(key)));
}

function timeRange(prefix, date, band) {
  const range = TIME_BANDS[band];
  if (!date || !range) return {};
  return { [`${prefix}_from`]: `${date}T${range[0]}`, [`${prefix}_to`]: `${date}T${range[1]}` };
}

export function buildFlightSearch(conditions, offset, limit) {
  const {
    trip_type,
    return_date,
    arrival_date,
    departure_time_band,
    arrival_time_band,
    return_arrival_date,
    return_departure_time_band,
    return_arrival_time_band,
    exclude_airlines,
    ...rest
  } = conditions;
  const roundTrip = trip_type === "round_trip";
  return {
    path: roundTrip ? "/flights/round-trips" : "/flights",
    query: {
      ...rest,
      include_airline_options: true,
      ...(roundTrip ? {
        return_date,
        ...timeRange("return_departure", return_date, return_departure_time_band),
        ...timeRange("return_arrival", return_arrival_date || return_date, return_arrival_time_band),
      } : {}),
      exclude_airlines: exclude_airlines
        .split(",")
        .map((code) => code.trim())
        .filter(Boolean),
      ...timeRange("departure", conditions.date, departure_time_band),
      ...timeRange("arrival", arrival_date || conditions.date, arrival_time_band),
      limit,
      offset,
    },
  };
}
