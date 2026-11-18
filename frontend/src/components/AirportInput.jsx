import { useEffect, useId, useState } from "react";
import { requestApi } from "../api/client";
import { airportLabel } from "../api/labels";

export default function AirportInput({ label, value, onChange }) {
  const id = useId();
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const code = (a) => a.iata_code || a.icao_code;
  useEffect(() => {
    const keyword = value.trim();
    setOptions([]);
    setActive(0);
    setError("");
    if (!keyword) {
      setSelected(null);
      setOptions([]);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const timer = setTimeout(
      () =>
        requestApi("/airports", {
          query: { keyword, limit: 20, selectable_only: true },
          signal: controller.signal,
        })
          .then((data) => {
            if (controller.signal.aborted) return;
            setOptions(data.airports);
            setActive(0);
            setSelected(
              data.airports.find((a) => [a.iata_code, a.icao_code].includes(keyword.toUpperCase())) ?? null,
            );
          })
          .catch((e) => {
            if (e.name !== "AbortError") setError(e.message);
          })
          .finally(() => {
            if (!controller.signal.aborted) setLoading(false);
          }),
      250,
    );
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value]);
  const choose = (a) => {
    setSelected(a);
    onChange(code(a));
    setOpen(false);
  };
  return (
    <div
      className="field airport-field"
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
      }}
    >
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        role="combobox"
        aria-expanded={open}
        aria-controls={`${id}-list`}
        aria-autocomplete="list"
        aria-activedescendant={open && options[active] ? `${id}-${active}` : undefined}
        value={
          selected && [selected.iata_code, selected.icao_code].includes(value.trim().toUpperCase())
            ? airportLabel(selected)
            : value
        }
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          setSelected(null);
          setOptions([]);
          onChange(e.target.value);
          setOpen(true);
        }}
        onKeyDown={(e) => {
          if (e.nativeEvent.isComposing || e.keyCode === 229) return;
          if (e.key === "Escape") setOpen(false);
          if (e.key === "ArrowDown" || e.key === "ArrowUp") {
            e.preventDefault();
            setOpen(true);
            setActive((i) => Math.max(0, Math.min(options.length - 1, i + (e.key === "ArrowDown" ? 1 : -1))));
          }
          if (e.key === "Enter" && open && options[active] && !loading) {
            e.preventDefault();
            choose(options[active]);
          }
        }}
        placeholder="도시·국가·공항·코드"
        maxLength={100}
        autoComplete="off"
      />
      {open && value.trim() && (
        <div className="airport-options" id={`${id}-list`} role="listbox">
          {loading ? (
            <p>검색 중…</p>
          ) : error ? (
            <p>{error}</p>
          ) : options.length ? (
            <>
              {options.map((a, i) => (
                <button
                  id={`${id}-${i}`}
                  role="option"
                  aria-selected={i === active}
                  type="button"
                  key={a.airport_id}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => choose(a)}
                >
                  {airportLabel(a)}
                  <small className="airport-country">{a.country}</small>
                </button>
              ))}
              {options.length === 20 && (
                <p className="small muted">
                  최대 20개를 표시해요. 도시·공항명이나 코드로 검색 범위를 좁혀 주세요.
                </p>
              )}
            </>
          ) : (
            <p>일치하는 공항이 없어요.</p>
          )}
        </div>
      )}
    </div>
  );
}
