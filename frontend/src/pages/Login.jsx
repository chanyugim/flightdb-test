import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AuthLayout from "../components/AuthLayout";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [memberId, setMemberId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(memberId, password);
      // 보호 페이지에서 로그인으로 왔다면 원래 가려던 주소로 돌아감.
      navigate(location.state?.from || "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout title="로그인">
      <form onSubmit={onSubmit}>
        <div className="form-row">
          <label htmlFor="login-id">아이디</label>
          <input
            id="login-id"
            autoComplete="username"
            value={memberId}
            onChange={(e) => setMemberId(e.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="login-password">비밀번호</label>
          <div className="auth-password">
            <input
              id="login-password"
              autoComplete="current-password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
              aria-pressed={showPassword}
              onClick={() => setShowPassword((value) => !value)}
            >
              {showPassword ? "숨기기" : "보기"}
            </button>
          </div>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn-primary btn-block" disabled={submitting}>
          {submitting ? "로그인 중..." : "로그인"}
        </button>
      </form>
      <p className="small muted" style={{ textAlign: "center" }}>
        계정이 없으신가요? <Link to="/register">회원가입</Link>
      </p>
    </AuthLayout>
  );
}
