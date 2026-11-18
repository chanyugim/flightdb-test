import FormPage from "../components/FormPage";
import LoadingFlight from "../components/LoadingFlight";
import { useState } from "react";
import { cancelGuestReservation, lookupGuestReservation } from "../api/reservations";
import ReservationCard from "../components/ReservationCard";

export default function GuestLookup() {
  const [form, setForm] = useState({ reservation_no: "", booker_email: "", booker_phone: "" });
  const [reservation, setReservation] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const lookup = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError("");
    try {
      // 예약번호와 예약자 연락처가 모두 맞아야 비회원 예약을 조회할 수 있음.
      setReservation(await lookupGuestReservation(form));
    } catch (err) {
      setReservation(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const onCancel = async () => {
    if (!window.confirm("예약을 취소할까요?")) return;
    try {
      // 취소 후 같은 조회 조건으로 다시 조회해 변경된 예약 상태를 표시함.
      await cancelGuestReservation(form);
      await lookup();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <FormPage title="비회원 예약 조회">
      <section>
        <form onSubmit={lookup}>
          <div className="form-row">
            <label htmlFor="guest-reservation_no">예약번호</label>
            <input
              id="guest-reservation_no"
              value={form.reservation_no}
              onChange={set("reservation_no")}
              required
            />
          </div>
          <div className="form-row">
            <label htmlFor="guest-booker_email">예약자 이메일</label>
            <input
              type="email"
              id="guest-booker_email"
              value={form.booker_email}
              onChange={set("booker_email")}
              required
            />
          </div>
          <div className="form-row">
            <label htmlFor="guest-booker_phone">예약자 전화번호</label>
            <input
              id="guest-booker_phone"
              value={form.booker_phone}
              onChange={set("booker_phone")}
              required
            />
          </div>
          <button type="submit" className="btn-primary btn-block" disabled={loading}>
            조회하기
          </button>
        </form>
      </section>
      {error && <p className="error">{error}</p>}
      {loading && <LoadingFlight compact label="예약 내역을 확인하고 있어요" />}
      {reservation && !loading && (
        <div style={{ marginTop: 16 }}>
          <ReservationCard reservation={reservation} onCancel={onCancel} />
        </div>
      )}
    </FormPage>
  );
}
