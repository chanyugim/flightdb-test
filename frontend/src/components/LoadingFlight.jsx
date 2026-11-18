import Icon from "./Icon";
import "../loading.css";

export default function LoadingFlight({ label = "잠시만 기다려 주세요", compact = false }) {
  return (
    <div className={`flight-loading${compact ? " compact" : ""}`} role="status" aria-live="polite">
      <div className="flight-loading-track" aria-hidden="true">
        <span className="flight-loading-path" />
        <Icon name="plane" />
      </div>
      <p>{label}</p>
    </div>
  );
}
