import LoadingFlight from "../components/LoadingFlight";
import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  cancelGuestReservation,
  cancelMemberReservation,
  getMemberReservation,
  lookupGuestReservation,
} from "../api/reservations";
import ReservationOverview from "../components/ReservationOverview";
import BookingHeader from "../components/BookingHeader";
import "../booking.css";
import { useAuth } from "../context/AuthContext";

export default function ReservationDetail() {
  const { reservationNo } = useParams();
  const { state } = useLocation();
  const { token, isLoggedIn, loading: authLoading, refreshMember } = useAuth();
  const [reservation, setReservation] = useState(state?.reservation ?? null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    // 화면 이동 시 예약 데이터가 전달되지 않은 회원 직접 접속은 예약번호로 조회함.
    if (authLoading || reservation || (!isLoggedIn && !state?.guest)) return;
    setLoading(true);
    (state?.guest
      ? lookupGuestReservation({
          reservation_no: reservationNo,
          booker_email: state.guest.email,
          booker_phone: state.guest.phone,
        })
      : getMemberReservation(reservationNo, token)
    )
      .then(setReservation)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [authLoading, reservation, isLoggedIn, token, reservationNo]);

  const onCancel = async () => {
    if (cancelling) return;
    if (!window.confirm("예약을 취소할까요?")) return;
    setCancelling(true);
    setError("");
    try {
      if (!state?.guest && isLoggedIn) {
        // 회원은 토큰으로 취소하고, 취소된 상세 정보를 다시 가져옴.
        await cancelMemberReservation(reservationNo, token);
        setReservation(await getMemberReservation(reservationNo, token));
        refreshMember();
      } else {
        // 비회원 취소에는 최초 조회 때 사용한 이메일과 전화번호가 필요함.
        const body = {
          reservation_no: reservationNo,
          booker_email: state.guest.email,
          booker_phone: state.guest.phone,
        };
        await cancelGuestReservation(body);
        setReservation(await lookupGuestReservation(body));
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setCancelling(false);
    }
  };

  if (authLoading || loading) return <LoadingFlight label="예약 내역을 확인하고 있어요" />;

  return (
    <>
      <BookingHeader title="예약 확인" step={2} />
      <div className="container booking-page">
        {reservation && state?.justBooked && reservation.reservation_status === "확정" && (
          <p className="notice">
            예약이 완료되었습니다. 예약번호 <strong>{reservation.reservation_no}</strong>
            {!isLoggedIn && " 를 꼭 기록해 두세요. 비회원 예약 조회에 필요합니다."}
          </p>
        )}
        {state?.justBooked && !reservation && (
          <p className="notice">
            예약이 접수되었어요. 예약번호: <strong>{reservationNo}</strong>. 조회가 실패해도 예약을 다시
            생성하지 말고 예약 조회에서 확인해 주세요.
          </p>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {reservation ? (
          <ReservationOverview
            reservation={reservation}
            cancelling={cancelling}
            onCancel={isLoggedIn || state?.guest ? onCancel : undefined}
          />
        ) : (
          !error && (
            <p className="empty">
              예약 정보를 불러올 수 없습니다. 비회원은 <Link to="/guest/lookup">비회원 예약조회</Link>에서
              확인해 주세요.
            </p>
          )
        )}
      </div>
    </>
  );
}
