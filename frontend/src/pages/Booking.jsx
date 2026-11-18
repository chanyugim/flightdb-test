import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { requestApi } from "../api/client";
import { createReservation } from "../api/reservations";
import { useAuth } from "../context/AuthContext";
import BookingSummary from "../components/BookingSummary";
import "../booking.css";
import BookingHeader from "../components/BookingHeader";

export default function Booking() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { token, member, isLoggedIn } = useAuth();

  // 상세 화면에서 선택한 항공편과 좌석을 라우터 state로 전달받음.
  const flight = state?.flight;
  const seats = state?.seats;
  const inbound = state?.inbound;
  const inboundSeats = state?.inboundSeats;
  const attempt = useRef(null);

  const [promotions, setPromotions] = useState([]);
  const [promotionId, setPromotionId] = useState("");
  const [usedPoints, setUsedPoints] = useState(0);
  const [booker, setBooker] = useState({
    booker_name: "",
    booker_phone: "",
    booker_email: "",
    booker_birth_date: "",
  });
  const [passengers, setPassengers] = useState(() =>
    (seats ?? []).map((s, i) => ({
      ...(inbound
        ? { outbound_seat_id: s.seat_id, inbound_seat_id: inboundSeats[i].seat_id }
        : { seat_id: s.seat_id }),
      passenger_name: "",
      passenger_birth_date: "",
    })),
  );
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [copyNotice, setCopyNotice] = useState("");

  useEffect(() => {
    setPromotionId("");
    setPromotions([]);
    if (!isLoggedIn) return;
    let active = true;
    requestApi("/promotions")
      .then((data) => {
        if (active) setPromotions(data);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [isLoggedIn]);

  useEffect(() => {
    if (member) {
      setBooker((b) => ({
        ...b,
        booker_name: b.booker_name || member.name,
        booker_phone: b.booker_phone || member.phone,
        booker_birth_date: b.booker_birth_date || member.birth_date,
      }));
    }
  }, [member]);

  if (!flight || !seats?.length) return <Navigate to="/" replace />;

  const setBookerField = (key) => (e) => setBooker((b) => ({ ...b, [key]: e.target.value }));
  const setPassengerField = (index, key) => (e) =>
    setPassengers((list) => list.map((p, i) => (i === index ? { ...p, [key]: e.target.value } : p)));

  const copyBookerToPassenger = (index) => {
    if (!booker.booker_name.trim() || !booker.booker_birth_date) return;
    setPassengers((list) =>
      list.map((passenger, i) =>
        i === index
          ? {
              ...passenger,
              passenger_name: booker.booker_name.trim(),
              passenger_birth_date: booker.booker_birth_date,
            }
          : passenger,
      ),
    );
    setCopyNotice(
      `탑승객 ${index + 1}에 예약자의 이름과 생년월일을 불러왔어요. 실제 탑승자 정보와 맞는지 확인해 주세요.`,
    );
  };

  const promo = isLoggedIn && promotions.find((p) => String(p.promotion_id) === promotionId);
  const base = (Number(flight.base_price) + Number(inbound?.base_price ?? 0)) * seats.length;
  const discount = promo ? Math.floor((base * Number(promo.discount_rate)) / 100) : 0;
  const points = isLoggedIn ? Number(usedPoints) || 0 : 0;
  const estimated = Math.max(base - discount - points, 0);
  const maxPoints = Math.min(member?.point_balance ?? 0, base - discount);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError("");
    try {
      // 최종 금액과 좌석 가능 여부는 서버가 다시 계산·확인함.
      const payload = {
        promotion_id: isLoggedIn && promotionId ? Number(promotionId) : null,
        ...booker,
        used_points: points,
        passengers,
      };
      const signature = JSON.stringify({ payload, token });
      if (attempt.current?.signature !== signature) attempt.current = { signature, key: crypto.randomUUID() };
      const created = await createReservation(payload, token, attempt.current.key, Boolean(inbound));
      if (isLoggedIn) {
        // 회원 예약은 인증된 상세 조회 화면으로 이동함.
        navigate(`/reservations/${created.reservation_no}`, { replace: true, state: { justBooked: true } });
      } else {
        // 비회원은 생성 직후 예약자 이메일·전화번호로 결과를 확인함.
        navigate(`/reservations/${created.reservation_no}`, {
          replace: true,
          state: { justBooked: true, guest: { email: booker.booker_email, phone: booker.booker_phone } },
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <BookingHeader title="예약 정보 입력" step={1} />
      <div className="container booking-page">
        <form onSubmit={onSubmit} className="booking-layout">
          <div className="booking-sheet">
            <section className="booking-section" aria-labelledby="booker-heading">
              <div className="booking-section-heading">
                <div>
                  <h2 id="booker-heading">예약자 정보</h2>
                  <p>
                    {isLoggedIn
                      ? "회원 정보를 불러왔어요. 연락처와 이메일을 확인해 주세요."
                      : "예약 조회에 사용할 연락처와 이메일을 입력해 주세요."}
                  </p>
                </div>
              </div>
              <div className="booking-fields">
                <label>
                  예약자 이름
                  <input
                    autoComplete="section-booker name"
                    value={booker.booker_name}
                    onChange={setBookerField("booker_name")}
                    required
                  />
                </label>
                <label>
                  예약자 전화번호
                  <input
                    type="tel"
                    autoComplete="section-booker tel"
                    value={booker.booker_phone}
                    onChange={setBookerField("booker_phone")}
                    placeholder="010-1234-5678"
                    required
                  />
                </label>
                <label>
                  예약자 이메일
                  <input
                    type="email"
                    autoComplete="section-booker email"
                    value={booker.booker_email}
                    onChange={setBookerField("booker_email")}
                    placeholder="example@email.com"
                    required
                  />
                </label>
                <label>
                  예약자 생년월일
                  <input
                    type="date"
                    autoComplete="section-booker bday"
                    value={booker.booker_birth_date}
                    onChange={setBookerField("booker_birth_date")}
                    required
                  />
                </label>
              </div>
            </section>

            <section className="booking-section" aria-labelledby="passenger-heading">
              <div className="booking-section-heading">
                <div>
                  <h2 id="passenger-heading">탑승객 정보</h2>
                  <p>
                    실제 탑승하는 분의 정보를 입력해 주세요. 예약자도 탑승한다면 아래 버튼으로 불러올 수
                    있어요.
                  </p>
                </div>
              </div>
              {passengers.map((passenger, index) => (
                <div className="booking-passenger" key={index}>
                  <div className="booking-passenger-head">
                    <div>
                      <h3>탑승객 {index + 1}</h3>
                      <span className="small muted">
                        {inbound
                          ? `가는 편 ${seats[index].seat_no} · 오는 편 ${inboundSeats[index].seat_no}`
                          : `좌석 ${seats[index].seat_no}`}{" "}
                        · {seats[index].seat_class}
                      </span>
                    </div>
                    <button
                      className="booking-copy"
                      type="button"
                      aria-label={`탑승객 ${index + 1}에 예약자 정보 불러오기`}
                      disabled={!booker.booker_name.trim() || !booker.booker_birth_date || submitting}
                      onClick={() => copyBookerToPassenger(index)}
                    >
                      예약자 정보 불러오기
                    </button>
                  </div>
                  <div className="booking-fields">
                    <label>
                      탑승객 {index + 1} 이름
                      <input
                        autoComplete="off"
                        value={passenger.passenger_name}
                        onChange={setPassengerField(index, "passenger_name")}
                        required
                      />
                    </label>
                    <label>
                      탑승객 {index + 1} 생년월일
                      <input
                        type="date"
                        autoComplete="off"
                        value={passenger.passenger_birth_date}
                        onChange={setPassengerField(index, "passenger_birth_date")}
                        required
                      />
                    </label>
                  </div>
                </div>
              ))}
              <p className="booking-copy-notice" role="status">
                {copyNotice}
              </p>
            </section>

            <section className="booking-section" aria-labelledby="discount-heading">
              <div className="booking-section-heading">
                <div>
                  <h2 id="discount-heading">할인 및 포인트</h2>
                  <p>적용할 혜택을 선택하고 예상 결제 금액을 확인해 주세요.</p>
                  <Link className="small" to="/benefits" target="_blank" rel="noopener noreferrer">등급·프로모션 혜택 보기 (새 창) ↗</Link>
                </div>
              </div>
              <div className="booking-fields">
                <label>
                  프로모션
                  <select
                    aria-label="프로모션"
                    disabled={!isLoggedIn}
                    aria-describedby={!isLoggedIn ? "promotion-member-notice" : undefined}
                    value={isLoggedIn ? promotionId : ""}
                    onChange={(event) => setPromotionId(event.target.value)}
                  >
                    <option value="">{isLoggedIn ? "선택 안 함" : "회원 전용 혜택"}</option>
                    {promotions.map((promotion) => (
                      <option key={promotion.promotion_id} value={promotion.promotion_id}>
                        {promotion.promotion_name} ({Number(promotion.discount_rate)}% 할인)
                      </option>
                    ))}
                  </select>
                </label>
                {isLoggedIn && (
                  <label>
                    사용 포인트 · 보유 {(member?.point_balance ?? 0).toLocaleString("ko-KR")}P
                    <div className="booking-points">
                      <input
                        aria-label="사용 포인트"
                        type="number"
                        min="0"
                        max={maxPoints}
                        step="1"
                        value={usedPoints}
                        onChange={(event) => setUsedPoints(event.target.value)}
                      />
                      <button type="button" onClick={() => setUsedPoints(maxPoints)}>
                        전액 사용
                      </button>
                    </div>
                  </label>
                )}
              </div>
              {!isLoggedIn && (
                <p id="promotion-member-notice" className="small muted">
                  프로모션 할인과 포인트 혜택은 로그인한 회원만 이용할 수 있어요.
                </p>
              )}
              <p className="small muted">프로모션은 한 개만 선택할 수 있어요. 할인 후 포인트를 사용하고, 최종 결제 금액에 등급별 적립률이 적용돼요.</p>
            </section>
          </div>
          <BookingSummary
            flight={flight}
            inbound={inbound}
            seats={seats}
            inboundSeats={inboundSeats}
            base={base}
            discount={discount}
            points={points}
            estimated={estimated}
            error={error}
            submitting={submitting}
          />
        </form>
      </div>
    </>
  );
}
