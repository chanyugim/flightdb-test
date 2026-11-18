export default function AdminSummary({ data }) {
  return (
    <div className="stat-grid">
      <div className="card stat">
        <span className="muted small">회원 수</span>
        <strong>{data.members}</strong>
      </div>
      <div className="card stat">
        <span className="muted small">항공편 수</span>
        <strong>{data.flights}</strong>
      </div>
      <div className="card stat">
        <span className="muted small">확정 예약</span>
        <strong>{data.confirmed_reservations}</strong>
      </div>
      <div className="card stat">
        <span className="muted small">답변 대기 문의</span>
        <strong>{data.pending_inquiries}</strong>
      </div>
    </div>
  );
}
