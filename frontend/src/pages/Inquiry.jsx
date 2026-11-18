import TabList from "../components/TabList";
import FormPage from "../components/FormPage";
import LoadingFlight from "../components/LoadingFlight";
import { useState } from "react";
import { requestApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Inquiry() {
  const { token, member, isLoggedIn } = useAuth();
  const [tab, setTab] = useState("write");
  const activeTab = isLoggedIn ? "write" : tab;
  const [form, setForm] = useState({
    reservation_no: "",
    author_name: "",
    author_phone: "",
    inquiry_password: "",
    subject: "",
    content: "",
  });
  const [created, setCreated] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [lookup, setLookup] = useState({ inquiry_id: "", password: "" });
  const [found, setFound] = useState(null);
  const [lookupError, setLookupError] = useState("");
  const [lookingUp, setLookingUp] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setCreated(null);
    try {
      // 회원은 계정 정보를 기본값으로 쓰고, 비회원은 조회 비밀번호를 함께 전송함.
      const body = {
        reservation_no: form.reservation_no || null,
        author_name: form.author_name || member?.name || "",
        author_phone: form.author_phone || member?.phone || "",
        inquiry_password: isLoggedIn ? null : form.inquiry_password,
        subject: form.subject,
        content: form.content,
      };
      setCreated(await requestApi("/inquiries", { method: "POST", token, body }));
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const onLookup = async (e) => {
    e.preventDefault();
    if (lookingUp) return;
    setLookingUp(true);
    setLookupError("");
    setFound(null);
    try {
      // 비회원 문의 조회 API는 문의번호와 password 필드를 받음.
      setFound(
        await requestApi("/inquiries/guest/lookup", {
          method: "POST",
          body: { inquiry_id: Number(lookup.inquiry_id), password: lookup.password },
        }),
      );
    } catch (err) {
      setLookupError(err.message);
    } finally {
      setLookingUp(false);
    }
  };

  return (
    <FormPage
      title={activeTab === "write" ? "문의하기" : "비회원 문의 조회"}
      wide
      navigation={
        !isLoggedIn && (
          <TabList
            id="inquiry"
            label="문의 메뉴"
            className="auth-nav inquiry-tabs"
            value={activeTab}
            onChange={setTab}
            items={[
              { value: "write", label: "문의 작성" },
              { value: "lookup", label: "비회원 문의 조회" },
            ]}
          />
        )
      }
    >
      <section
        className="inquiry-panel"
        id="inquiry-panel-write"
        role={!isLoggedIn ? "tabpanel" : undefined}
        aria-labelledby={!isLoggedIn ? "inquiry-tab-write" : undefined}
        hidden={activeTab !== "write"}
      >
        <form onSubmit={onSubmit}>
          <div className="form-row">
            <label htmlFor="inquiry-reservation_no">예약번호 (선택)</label>
            <input id="inquiry-reservation_no" value={form.reservation_no} onChange={set("reservation_no")} />
          </div>
          <div className="form-row">
            <label htmlFor="inquiry-author_name">이름</label>
            <input
              id="inquiry-author_name"
              value={form.author_name || (member?.name ?? "")}
              onChange={set("author_name")}
              required
            />
          </div>
          <div className="form-row">
            <label htmlFor="inquiry-author_phone">전화번호</label>
            <input
              id="inquiry-author_phone"
              value={form.author_phone || (member?.phone ?? "")}
              onChange={set("author_phone")}
              required
            />
          </div>
          {!isLoggedIn && (
            <div className="form-row">
              <label htmlFor="inquiry-inquiry_password">조회용 비밀번호</label>
              <input
                type="password"
                id="inquiry-inquiry_password"
                value={form.inquiry_password}
                onChange={set("inquiry_password")}
                required
              />
            </div>
          )}
          <div className="form-row">
            <label htmlFor="inquiry-subject">제목</label>
            <input id="inquiry-subject" value={form.subject} onChange={set("subject")} required />
          </div>
          <div className="form-row">
            <label htmlFor="inquiry-content">내용</label>
            <textarea id="inquiry-content" value={form.content} onChange={set("content")} required />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn-primary btn-block" disabled={submitting}>
            문의 등록
          </button>
        </form>
        {created && (
          <>
            <p className="notice">
              등록되었습니다. 문의번호 <strong>{created.inquiry_id}</strong>
              {!isLoggedIn && " — 비회원 조회에 필요하니 꼭 기억해 주세요."}
            </p>
            {!isLoggedIn && (
              <button
                type="button"
                className="btn-block"
                onClick={() => {
                  setLookup({ inquiry_id: String(created.inquiry_id), password: form.inquiry_password });
                  setFound(null);
                  setLookupError("");
                  setTab("lookup");
                  document.getElementById("inquiry-tab-lookup")?.focus();
                }}
              >
                등록한 문의 조회
              </button>
            )}
          </>
        )}
      </section>

      {!isLoggedIn && (
        <section
          className="inquiry-panel"
          id="inquiry-panel-lookup"
          role="tabpanel"
          aria-labelledby="inquiry-tab-lookup"
          hidden={activeTab !== "lookup"}
        >
          <form onSubmit={onLookup}>
            <div className="form-row">
              <label htmlFor="lookup-inquiry_id">문의번호</label>
              <input
                id="lookup-inquiry_id"
                value={lookup.inquiry_id}
                onChange={(e) => setLookup((l) => ({ ...l, inquiry_id: e.target.value }))}
                required
              />
            </div>
            <div className="form-row">
              <label htmlFor="lookup-password">비밀번호</label>
              <input
                type="password"
                id="lookup-password"
                value={lookup.password}
                onChange={(e) => setLookup((l) => ({ ...l, password: e.target.value }))}
                required
              />
            </div>
            <button type="submit" className="btn-primary btn-block" disabled={lookingUp}>
              조회하기
            </button>
          </form>
          {lookingUp && <LoadingFlight compact label="문의 내역을 확인하고 있어요" />}
          {lookupError && <p className="error">{lookupError}</p>}
          {found && (
            <div className="res-card" style={{ marginTop: 12 }}>
              <div className="res-head">
                <strong>{found.subject}</strong>
                <span className="badge">{found.reply_status}</span>
              </div>
              <p>{found.content}</p>
              {found.admin_reply && <p className="notice">답변: {found.admin_reply}</p>}
            </div>
          )}
        </section>
      )}
    </FormPage>
  );
}
