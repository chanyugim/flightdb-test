import { NavLink, Link } from "react-router-dom";
import "../auth.css";

export default function AuthLayout({ title, children }) {
  return (
    <div className="container auth-page">
      <div className="auth-layout">
        <section className="auth-content">
          <nav className="auth-nav" aria-label="회원 메뉴">
            <NavLink to="/login">로그인</NavLink>
            <NavLink to="/register">회원가입</NavLink>
          </nav>
          <h1>{title}</h1>
          {children}
          <div className="auth-guest-link">
            <span>비회원으로 예약하셨나요?</span>
            <Link to="/guest/lookup">예약 조회 →</Link>
          </div>
        </section>
      </div>
    </div>
  );
}
