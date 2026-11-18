import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { requestApi } from "../api/client";
import AuthLayout from "../components/AuthLayout";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    member_id: "",
    password: "",
    name: "",
    birth_date: "",
    gender: "M",
    phone: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // 입력 필드 이름을 받아 해당 항목만 폼 상태에서 갱신함.
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await requestApi("/auth/register", { method: "POST", body: form });
      alert("가입되었습니다. 로그인해 주세요.");
      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout title="회원가입">
      <form onSubmit={onSubmit}>
        <div className="form-row">
          <label htmlFor="register-id">아이디</label>
          <input
            id="register-id"
            autoComplete="username"
            value={form.member_id}
            onChange={set("member_id")}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="register-password">비밀번호</label>
          <input
            id="register-password"
            autoComplete="new-password"
            type="password"
            value={form.password}
            onChange={set("password")}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="register-name">이름</label>
          <input id="register-name" autoComplete="name" value={form.name} onChange={set("name")} required />
        </div>
        <div className="form-row">
          <label htmlFor="register-birth">생년월일</label>
          <input
            id="register-birth"
            autoComplete="bday"
            type="date"
            value={form.birth_date}
            onChange={set("birth_date")}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="register-gender">성별</label>
          <select id="register-gender" value={form.gender} onChange={set("gender")}>
            <option value="M">남</option>
            <option value="F">여</option>
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="register-phone">전화번호</label>
          <input
            id="register-phone"
            type="tel"
            autoComplete="tel"
            value={form.phone}
            onChange={set("phone")}
            placeholder="010-1234-5678"
            required
          />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="btn-primary btn-block" disabled={submitting}>
          가입하기
        </button>
      </form>
      <p className="small muted" style={{ textAlign: "center" }}>
        이미 계정이 있으신가요? <Link to="/login">로그인</Link>
      </p>
    </AuthLayout>
  );
}
