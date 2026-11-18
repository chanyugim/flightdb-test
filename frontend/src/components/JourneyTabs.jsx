const JOURNEYS = [
  { value: "one_way", label: "편도" },
  { value: "round_trip", label: "왕복" },
];

export default function JourneyTabs({ value, onChange }) {
  return (
    <div className="journey-tabs" data-journey={value} role="group" aria-label="여정 선택">
      <span className="journey-indicator" aria-hidden="true" />
      {JOURNEYS.map((journey) => (
        <button
          type="button"
          key={journey.value}
          aria-pressed={value === journey.value}
          onClick={() => onChange(journey.value)}
        >
          {journey.label}
        </button>
      ))}
    </div>
  );
}
