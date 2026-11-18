import LoadingFlight from "./LoadingFlight";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { isLoggedIn, isAdmin, loading } = useAuth();
  const location = useLocation();

  // 인증 확인 중에는 로그인 화면으로 성급하게 이동하지 않도록 기다림.
  if (loading) return <LoadingFlight label="로그인 정보를 확인하고 있어요" />;
  if (!isLoggedIn) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (adminOnly && !isAdmin) return <p>접근 권한이 없습니다.</p>;
  return children;
}
