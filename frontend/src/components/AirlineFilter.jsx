import { useState } from "react";

export default function AirlineFilter({ items = [], excluded, onChange, loading }) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(false);
  const codes = excluded.split(",").filter(Boolean);
  const matches = items.filter((a) =>
    `${a.name_ko} ${a.name_en} ${a.iata_code} ${a.icao_code}`
      .toLowerCase()
      .includes(query.trim().toLowerCase()),
  );
  const visible = expanded || query ? matches : matches.slice(0, 6);
  const allSelected = items.every((a) => !codes.includes(a.iata_code || a.icao_code));
  const change = (code) =>
    onChange(codes.includes(code) ? codes.filter((c) => c !== code).join(",") : [...codes, code].join(","));
  return (
    <fieldset className="airline-filter" disabled={loading}>
      <legend>항공사</legend>
      <p className="small muted">현재 검색 조건에서 이용 가능한 항공사예요. 체크를 해제하면 제외돼요.</p>
      {!items.length ? (
        <p className="small muted">
          {loading ? "항공사를 확인하고 있어요…" : "현재 조건에 맞는 항공사가 없어요."}
        </p>
      ) : (
        <>
          <label className="check">
            <input
              type="checkbox"
              checked={allSelected}
              ref={(el) => {
                if (el)
                  el.indeterminate =
                    !allSelected && items.some((a) => !codes.includes(a.iata_code || a.icao_code));
              }}
              onChange={(e) =>
                onChange(
                  e.target.checked
                    ? ""
                    : items
                        .map((a) => a.iata_code || a.icao_code)
                        .filter(Boolean)
                        .join(","),
                )
              }
            />
            전체 선택
          </label>
          {items.length > 6 && (
            <input
              aria-label="항공사 이름 또는 코드 검색"
              placeholder="결과 내 항공사 검색"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          )}
          {visible.map((a) => {
            const code = a.iata_code || a.icao_code;
            return (
              code && (
                <label className="check" key={a.airline_id}>
                  <input type="checkbox" checked={!codes.includes(code)} onChange={() => change(code)} />
                  {a.name_ko || a.name_en} ({code})
                </label>
              )
            );
          })}
          {!matches.length && <p className="small muted">일치하는 항공사가 없어요.</p>}
          {!query && items.length > 6 && (
            <button type="button" className="filter-more" onClick={() => setExpanded((v) => !v)}>
              {expanded ? "접기" : `항공사 ${items.length - 6}개 더 보기`}
            </button>
          )}
        </>
      )}
    </fieldset>
  );
}
