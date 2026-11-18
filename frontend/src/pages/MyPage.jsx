import { airportLabel } from "../api/labels";
import { formatPointChange } from "../api/points";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { formatKst } from "../utils/format.js";
import { requestApi } from "../api/client";
import { cancelMemberReservation } from "../api/reservations";
import ReservationCard from "../components/ReservationCard";
import { useAuth } from "../context/AuthContext";

export default function MyPage() {
  const { token, member, refreshMember } = useAuth();
  const [reservations, setReservations] = useState([]);
  const [points, setPoints] = useState(null);
  const [inquiries, setInquiries] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      // 마이페이지의 네 종류 데이터를 병렬로 조회해 한 번에 화면을 갱신함.
      const [r, p, i, rt] = await Promise.all([
        requestApi("/me/reservations", { token }),
        requestApi("/me/points", { token }),
        requestApi("/me/inquiries", { token }),
        requestApi("/me/recommended-routes", { token }),
      ]);
      setReservations(r);
      setPoints(p);
      setInquiries(i);
      setRoutes(rt);
    } catch (e) {
      setError(e.message);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const onCancel = async (r) => {
    if (!window.confirm("예약을 취소할까요?")) return;
    try {
      // 취소 후 예약·포인트와 로그인 사용자 잔액을 다시 불러옴.
      await cancelMemberReservation(r.reservation_no, token);
      await Promise.all([load(), refreshMember()]);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="container page">
      <h1>마이페이지</h1>
      {error && <p className="error">{error}</p>}

      {member && (
        <div className="stat-grid">
          <div className="card stat">
            <span className="muted small">회원</span>
            <strong>{member.name}</strong>
            <span className="small muted">{member.member_id}</span>
          </div>
          <div className="card stat">
            <span className="muted small">등급</span>
            <strong>{member.grade_name}</strong>
            <Link className="small" to="/benefits#grades">전체 등급 혜택 보기 →</Link>
          </div>
          <div className="card stat">
            <span className="muted small">보유 포인트</span>
            <strong>{member.point_balance.toLocaleString("ko-KR")}P</strong>
          </div>
          <div className="card stat">
            <span className="muted small">연락처</span>
            <strong style={{ fontSize: 18 }}>{member.phone}</strong>
          </div>
        </div>
      )}

      <h2>자주 이용한 노선</h2>
      {routes.length === 0 ? (
        <p className="muted">아직 이용 내역이 없어요.</p>
      ) : (
        <div className="chips">
          {routes.map((r, i) => (
            <span className="badge" key={i}>
              {airportLabel(r.departure_airport)} → {airportLabel(r.arrival_airport)} ({r.reservation_count}
              회)
            </span>
          ))}
        </div>
      )}

      <h2>내 예약</h2>
      {reservations.length === 0 && <p className="muted">예약 내역이 없습니다.</p>}
      {reservations.map((r) => (
        <ReservationCard key={r.reservation_no} reservation={r} onCancel={onCancel} linkToDetail />
      ))}

      <h2>포인트 이력</h2>
      {!points ? null : points.history.length === 0 ? (
        <p className="muted">이력이 없습니다.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>일시</th>
              <th>구분</th>
              <th>변동</th>
              <th>잔액</th>
              <th>예약번호</th>
            </tr>
          </thead>
          <tbody>
            {points?.history.map((h) => (
              <tr key={h.point_history_id}>
                <td>{formatKst(h.occurred_at)}</td>
                <td>{h.change_type}</td>
                <td>{formatPointChange(h)}</td>
                <td>{h.balance_after}</td>
                <td>{h.reservation_no}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>내 문의</h2>
      <p>
        <Link to="/inquiry" className="btn">
          문의 작성
        </Link>
      </p>
      {inquiries.length === 0 && <p className="muted">문의 내역이 없습니다.</p>}
      {inquiries.map((q) => (
        <div className="res-card" key={q.inquiry_id}>
          <div className="res-head">
            <strong>{q.subject}</strong>
            <span className="badge">{q.reply_status}</span>
          </div>
          <p>{q.content}</p>
          {q.admin_reply && <p className="notice">답변: {q.admin_reply}</p>}
        </div>
      ))}
    </div>
  );
}
