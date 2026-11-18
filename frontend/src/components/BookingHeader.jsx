const STEPS = ["항공편·좌석 선택", "예약 정보 입력", "예약 확인"];

export default function BookingHeader({ title, step }) {
  return (
    <section className="booking-hero">
      <div className="container">
        <h1>{title}</h1>
        <ol className="booking-steps" aria-label="예약 진행 단계">
          {STEPS.map((label, index) => (
            <li key={label} aria-current={step === index ? "step" : undefined}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              {label}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
