import TabList from "./TabList";
import { useId, useMemo, useState } from "react";

const CLASS_ORDER = ["이코노미", "비즈니스", "퍼스트"];

export default function SeatMap({ seats, selected, assigned = new Map(), disabled, onSelect }) {
  const [activeClass, setActiveClass] = useState("이코노미");
  const id = useId();
  const selectedIds = new Set(
    (Array.isArray(selected) ? selected : [selected]).filter(Boolean).map((s) => s.seat_id),
  );
  const cabins = useMemo(() => {
    const groups = {};
    for (const seat of seats) {
      const [, row, letter] = /^(\d+)([A-Z]+)$/.exec(seat.seat_no) ?? [null, seat.seat_no, ""];
      const cabin = (groups[seat.seat_class] ??= { rows: {}, letters: new Set(), available: 0 });
      (cabin.rows[row] ??= {})[letter] = seat;
      cabin.letters.add(letter);
      if (seat.is_available) cabin.available += 1;
    }
    return Object.entries(groups)
      .sort(([a], [b]) => CLASS_ORDER.indexOf(a) - CLASS_ORDER.indexOf(b))
      .map(([name, group]) => ({
        name,
        available: group.available,
        letters: [...group.letters].sort(),
        rows: Object.entries(group.rows).sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true })),
      }));
  }, [seats]);
  const currentClass = cabins.some((cabin) => cabin.name === activeClass) ? activeClass : cabins[0]?.name;
  return (
    <div className="seat-map">
      <TabList
        id={id}
        label="좌석 등급"
        className="seat-class-tabs"
        value={currentClass}
        onChange={setActiveClass}
        items={cabins.map((cabin) => ({
          value: cabin.name,
          label: (
            <>
              <strong>{cabin.name}</strong>
              <span>{cabin.available ? `잔여 ${cabin.available}석` : "매진"}</span>
            </>
          ),
        }))}
      />
      <p className="small muted">좌석번호 기준 배치 · 실제 기내 배치와 다를 수 있어요.</p>
      {cabins.map((c) => (
        <section
          key={c.name}
          role="tabpanel"
          id={`${id}-panel-${c.name}`}
          aria-labelledby={`${id}-tab-${c.name}`}
          hidden={c.name !== currentClass}
        >
          <h3>{c.name}</h3>
          {c.rows.map(([row, columns]) => (
            <div className="seat-row" key={row}>
              <span className="row-no">{row}</span>
              {c.letters.map((letter, i) => {
                const s = columns[letter],
                  owner = s && assigned.get(s.seat_id),
                  isSelected = s && selectedIds.has(s.seat_id);
                return (
                  <span style={{ display: "contents" }} key={letter}>
                    {i === Math.ceil(c.letters.length / 2) && <span className="aisle" />}
                    {s ? (
                      <button
                        type="button"
                        className={`seat ${isSelected ? "selected" : owner !== undefined ? "assigned" : ""}`}
                        aria-pressed={!!isSelected}
                        aria-label={`${s.seat_no}${owner !== undefined ? ` · 탑승객 ${owner + 1}` : ""}`}
                        title={owner !== undefined ? `탑승객 ${owner + 1}` : s.seat_no}
                        disabled={disabled || !s.is_available}
                        onClick={() => onSelect(s)}
                      >
                        {s.seat_no}
                      </button>
                    ) : (
                      <span className="seat empty" />
                    )}
                  </span>
                );
              })}
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
