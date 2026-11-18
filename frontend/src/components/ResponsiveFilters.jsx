import { useEffect, useRef, useState } from "react";
import "../filters.css";

export default function ResponsiveFilters({ children, onApply, open, onOpenChange }) {
  const [mobile, setMobile] = useState(() => window.matchMedia("(max-width: 800px)").matches);
  const dialog = useRef(null);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 800px)");
    const update = () => {
      setMobile(media.matches);
      onOpenChange(false);
    };
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [onOpenChange]);

  useEffect(() => {
    if (!mobile || !open) {
      dialog.current?.close();
      return;
    }
    dialog.current?.showModal();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [mobile, open]);

  if (!mobile)
    return (
      <aside className="card filters">
        <h3>필터</h3>
        {children}
      </aside>
    );
  return (
    <dialog
      id="mobile-filter-dialog"
      ref={dialog}
      className="filter-dialog"
      aria-labelledby="filter-title"
      onCancel={() => onOpenChange(false)}
      onClose={() => onOpenChange(false)}
    >
      <div className="filter-dialog-header">
        <h2 id="filter-title">검색 필터</h2>
        <button autoFocus aria-label="검색 필터 닫기" onClick={() => onOpenChange(false)}>
          닫기
        </button>
      </div>
      <div className="filters filter-dialog-content">{children}</div>
      <div className="filter-dialog-footer">
        <span className="small muted">선택한 조건으로 항공편을 검색해요.</span>
        <button
          className="btn-primary"
          onClick={() => {
            onApply();
            onOpenChange(false);
          }}
        >
          필터 적용
        </button>
      </div>
    </dialog>
  );
}
