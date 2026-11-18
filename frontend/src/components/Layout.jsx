import Icon from "./Icon";
import usePwa from "../hooks/usePwa";
import { InstallApp, PwaStatus } from "./PwaControls";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import Chatbot from "./Chatbot";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const pwa = usePwa();
  const { isLoggedIn, isAdmin, member, logout } = useAuth();
  const navigate = useNavigate();
  const cls = ({ isActive }) => (isActive ? "active" : undefined);

  // 로그인 여부와 관리자 권한에 따라 메뉴를 다르게 표시함.
  return (
    <>
      <header className="header">
        <div className="container header-inner">
          <Link to="/" className="logo">
            <Icon name="plane" /> 항공권<span>예매</span>
          </Link>
          <nav className="nav">
            <NavLink to="/" end className={cls}>
              항공권
            </NavLink>
            <NavLink to="/guest/lookup" className={cls}>
              비회원 예약조회
            </NavLink>
            <NavLink to="/inquiry" className={cls}>
              문의
            </NavLink>
            <NavLink to="/benefits" className={cls}>혜택</NavLink>
            {isLoggedIn && (
              <NavLink to="/mypage" className={cls}>
                마이페이지
              </NavLink>
            )}
            {isAdmin && (
              <NavLink to="/admin" className={cls}>
                관리자
              </NavLink>
            )}
          </nav>
          <div className="header-user">
            {isLoggedIn ? (
              <>
                <span>{member?.name}님</span>
                <button
                  onClick={() => {
                    logout();
                    navigate("/");
                  }}
                >
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <Link to="/login">로그인</Link>
                <Link to="/register" className="btn btn-primary">
                  회원가입
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      <PwaStatus pwa={pwa} />
      <main>
        <Outlet />
      </main>
      <footer className="site-footer">
        항공권 예매 서비스 · Term Project 5팀
        <InstallApp pwa={pwa} />
      </footer>
      <Chatbot />
    </>
  );
}
