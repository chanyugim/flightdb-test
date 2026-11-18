import { useState } from "react";
import { requestApi } from "../../api/client";

export default function InquiryManager({ data, token, load }) {
  const [replyText, setReplyText] = useState({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(null);
  const reply = async (id) => {
    if (saving !== null) return;
    setSaving(id);
    setError("");
    try {
      const current = data.find((item) => item.inquiry_id === id);
      await requestApi(`/admin/inquiries/${id}/reply`, {
        method: "PATCH",
        token,
        body: { admin_reply: replyText[id] ?? current?.admin_reply ?? "" },
      });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(null);
    }
  };
  return (
    <section>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {data.map((q) => (
        <div className="res-card" key={q.inquiry_id}>
          <div className="res-head">
            <strong>
              #{q.inquiry_id} {q.subject}
            </strong>
            <span className="badge">{q.reply_status}</span>
          </div>
          <p>{q.content}</p>
          <textarea
            placeholder="답변 내용"
            value={replyText[q.inquiry_id] ?? q.admin_reply ?? ""}
            onChange={(e) => setReplyText((r) => ({ ...r, [q.inquiry_id]: e.target.value }))}
          />
          <button
            className="btn-primary"
            disabled={saving !== null}
            style={{ marginTop: 8 }}
            onClick={() => reply(q.inquiry_id)}
          >
            답변 저장
          </button>
        </div>
      ))}
    </section>
  );
}
