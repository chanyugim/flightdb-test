import { useCallback, useEffect, useRef, useState } from "react";
import { requestApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import LoadingFlight from "../components/LoadingFlight";
import PromotionManager from "../components/PromotionManager";
import FlightManager from "../components/admin/FlightManager";
import InquiryManager from "../components/admin/InquiryManager";
import ReservationList from "../components/admin/ReservationList";
import AdminSummary from "../components/admin/AdminSummary";

const TABS = {
  요약: { path: "/admin/summary", Component: AdminSummary },
  항공편: { path: "/admin/flights", query: { limit: 100 }, field: "flights", Component: FlightManager },
  예약: {
    path: "/admin/reservations",
    query: { limit: 50 },
    field: "reservations",
    Component: ReservationList,
  },
  문의: { path: "/admin/inquiries", Component: InquiryManager },
  프로모션: { path: "/admin/promotions" },
};

export default function Admin() {
  const { token } = useAuth();
  const [tab, setTab] = useState("요약");
  const [loaded, setLoaded] = useState(null);
  const [error, setError] = useState("");
  const sequence = useRef(0);
  const data = loaded?.tab === tab ? loaded.data : null;
  const { Component } = TABS[tab];
  const load = useCallback(
    async (signal) => {
      const version = ++sequence.current;
      setError("");
      try {
        const { path, query, field } = TABS[tab];
        const result = await requestApi(path, { query, token, signal });
        if (version === sequence.current && !signal?.aborted)
          setLoaded({ tab, data: field ? result[field] : result });
      } catch (e) {
        if (e.name !== "AbortError" && version === sequence.current) setError(e.message);
      }
    },
    [tab, token],
  );
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);
  return (
    <div className="container page">
      <h1>관리자</h1>
      <div className="tabs">
        {Object.keys(TABS).map((name) => (
          <button key={name} className={name === tab ? "active" : undefined} onClick={() => setTab(name)}>
            {name}
          </button>
        ))}
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!data && !error && <LoadingFlight label="관리 정보를 불러오고 있어요" />}
      {data &&
        (Component ? (
          <Component key={tab} data={data} token={token} load={load} />
        ) : (
          <PromotionManager promotions={data} token={token} reload={load} />
        ))}
    </div>
  );
}
