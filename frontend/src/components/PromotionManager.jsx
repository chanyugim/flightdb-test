import { useState } from "react";
import { formatKst, toDateTimeInput } from "../utils/format.js";
import { requestApi } from "../api/client";

export default function PromotionManager({ promotions, token, reload }) {
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const create = () => {
    setError("");
    setNotice("");
    setEditing({ promotion_name: "", discount_rate: "10", start_at: "", end_at: "" });
  };
  const edit = (p) => {
    setError("");
    setNotice("");
    setEditing({ ...p, start_at: toDateTimeInput(p.start_at), end_at: toDateTimeInput(p.end_at) });
  };
  const save = async (e) => {
    e.preventDefault();
    setError("");
    setNotice("");
    if (editing.start_at > editing.end_at) {
      setError("종료 시각은 시작 시각 이후로 지정해 주세요.");
      return;
    }
    setBusy(true);
    try {
      const isNew = !editing.promotion_id;
      await requestApi(isNew ? "/admin/promotions" : `/admin/promotions/${editing.promotion_id}`, {
        method: isNew ? "POST" : "PATCH",
        token,
        body: {
          promotion_name: editing.promotion_name.trim(),
          discount_rate: Number(editing.discount_rate),
          start_at: editing.start_at,
          end_at: editing.end_at,
        },
      });
      setEditing(null);
      setNotice(isNew ? "프로모션을 등록했어요." : "프로모션을 수정했어요.");
      await reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const remove = async (p) => {
    if (!window.confirm(`‘${p.promotion_name}’ 프로모션을 삭제할까요? 삭제하면 복구할 수 없어요.`)) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await requestApi(`/admin/promotions/${p.promotion_id}`, { method: "DELETE", token });
      if (editing?.promotion_id === p.promotion_id) setEditing(null);
      setNotice("프로모션을 삭제했어요.");
      await reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section>
      <button type="button" className="btn-primary" disabled={busy} onClick={create}>
        새 프로모션 등록
      </button>
      <p className="small muted">
        예약에 사용된 프로모션은 삭제할 수 없어요. 새 예약에 적용하지 않으려면 종료 시각을 수정해 주세요. 모든
        시각은 한국 시간 기준이에요.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="notice" role="status">
          {notice}
        </p>
      )}
      {editing && (
        <form className="card promotion-editor" onSubmit={save}>
          <h2>{editing.promotion_id ? "프로모션 수정" : "프로모션 등록"}</h2>
          <fieldset disabled={busy}>
            <label>
              프로모션 이름
              <input
                required
                maxLength={50}
                value={editing.promotion_name}
                onChange={(e) => setEditing((p) => ({ ...p, promotion_name: e.target.value }))}
              />
            </label>
            <label>
              할인율 (%)
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                required
                value={editing.discount_rate}
                onChange={(e) => setEditing((p) => ({ ...p, discount_rate: e.target.value }))}
              />
            </label>
            <label>
              시작 시각
              <input
                type="datetime-local"
                step="1"
                required
                value={editing.start_at}
                onChange={(e) => setEditing((p) => ({ ...p, start_at: e.target.value }))}
              />
            </label>
            <label>
              종료 시각
              <input
                type="datetime-local"
                step="1"
                required
                value={editing.end_at}
                onChange={(e) => setEditing((p) => ({ ...p, end_at: e.target.value }))}
              />
            </label>
            <button className="btn-primary" type="submit">
              {busy ? "저장 중…" : editing.promotion_id ? "수정 저장" : "등록하기"}
            </button>{" "}
            <button type="button" onClick={() => setEditing(null)}>
              취소
            </button>
          </fieldset>
        </form>
      )}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>이름</th>
              <th>할인율</th>
              <th>기간</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody>
            {promotions.map((p) => (
              <tr key={p.promotion_id}>
                <td>{p.promotion_name}</td>
                <td>{Number(p.discount_rate)}%</td>
                <td>
                  {formatKst(p.start_at)} ~ {formatKst(p.end_at)}
                </td>
                <td>
                  <button disabled={busy} onClick={() => edit(p)}>
                    수정
                  </button>{" "}
                  <button className="btn-danger" disabled={busy} onClick={() => remove(p)}>
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!promotions.length && <p>등록된 프로모션이 없어요.</p>}
    </section>
  );
}
