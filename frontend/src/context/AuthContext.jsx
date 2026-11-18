import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { requestApi } from "../api/client";

const AuthContext = createContext(null);
const TOKEN_KEY = "access_token";

export function AuthProvider({ children }) {
  // 새로고침 후 로그인 복원을 위해 브라우저 저장소에서 토큰을 읽음.
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  });
  const [member, setMember] = useState(null);
  const currentToken = useRef(token);
  currentToken.current = token;
  const [loading, setLoading] = useState(Boolean(token));

  const logout = useCallback(() => {
    currentToken.current = null;
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {}
    setToken(null);
    setMember(null);
  }, []);

  const refreshMember = useCallback(async () => {
    if (!token) return;
    try {
      // 화면에 필요한 이름·등급·권한 정보는 /me에서 조회함.
      const data = await requestApi("/me", { token });
      if (currentToken.current === token) setMember(data);
    } catch (e) {
      if (e.status === 401 && currentToken.current === token) logout();
    }
  }, [token, logout]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    refreshMember().finally(() => setLoading(false));
  }, [token, refreshMember]);

  const login = async (member_id, password) => {
    const data = await requestApi("/auth/login", { method: "POST", body: { member_id, password } });
    try {
      // 이후 보호 API 요청에 사용할 인증 토큰을 저장함.
      localStorage.setItem(TOKEN_KEY, data.access_token);
    } catch {}
    setToken(data.access_token);
  };

  const value = {
    token,
    member,
    loading,
    isLoggedIn: Boolean(token),
    isAdmin: member?.role_type === "관리자",
    login,
    logout,
    refreshMember,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
