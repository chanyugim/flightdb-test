import Icon from "./Icon";
import { useEffect, useId, useRef, useState } from "react";
import { formatWon } from "../utils/format.js";

export default function BookingPanel({ title, meta, amount, amountLabel, actions, notice, children }) {
  const [expanded, setExpanded] = useState(false);
  const id = useId();
  const toggle = useRef(null);
  useEffect(() => {
    if (!expanded) return;
    const close = (event) => {
      if (event.key === "Escape") {
        setExpanded(false);
        toggle.current?.focus();
      }
    };
    const showInvalidField = () => setExpanded(false);
    window.addEventListener("keydown", close);
    window.addEventListener("invalid", showInvalidField, true);
    return () => {
      window.removeEventListener("keydown", close);
      window.removeEventListener("invalid", showInvalidField, true);
    };
  }, [expanded]);

  return (
    <aside className={`booking-summary booking-dock${expanded ? " expanded" : ""}`} aria-label={title}>
      <div className="booking-summary-title">
        <span>{title}</span>
        <strong>{meta}</strong>
        <button
          type="button"
          ref={toggle}
          className="booking-expand"
          aria-expanded={expanded}
          aria-controls={id}
          aria-label={expanded ? "여정 상세 접기" : "여정 상세 펼치기"}
          onClick={() => setExpanded(!expanded)}
        >
          <Icon name={expanded ? "down" : "expand"} />
        </button>
      </div>
      <div id={id} className="booking-panel-details">
        <div className="booking-summary-body">{children}</div>
      </div>
      <div className="booking-panel-actions">
        <div className="booking-mobile-total">
          <span>{amountLabel}</span>
          <strong>{formatWon(amount)}</strong>
        </div>
        {notice}
        {actions}
      </div>
    </aside>
  );
}
