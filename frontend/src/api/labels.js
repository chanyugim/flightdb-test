export function airportLabel(airport) {
  if (!airport) return "";
  const name = [airport.city, airport.name_ko || airport.name_en].filter(Boolean);
  return `${[...new Set(name)].join(" · ")} (${airport.iata_code || airport.icao_code || ""})`;
}
