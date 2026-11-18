import { useEffect, useRef, useState } from "react";
import "../announcements.css";

export default function AnnouncementStrip({
  title,
  items,
  onSelect,
  tone = "routes",
  emptyText,
  animate = true,
}) {
  const viewport = useRef(null);
  const cycle = useRef(null);
  const [sizes, setSizes] = useState({ viewport: 0, cycle: 0 });
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (!animate) return;
    const measure = () =>
      setSizes({
        viewport: viewport.current?.clientWidth ?? 0,
        cycle: cycle.current?.getBoundingClientRect().width ?? 0,
      });
    const observer = new ResizeObserver(measure);
    observer.observe(viewport.current);
    if (cycle.current) observer.observe(cycle.current);
    return () => observer.disconnect();
  }, [items, animate]);

  const copies = sizes.cycle ? Math.max(1, Math.ceil(sizes.viewport / sizes.cycle)) : 1;
  return (
    <section className={`announcement-strip ${tone}${animate ? "" : " is-static"}`} aria-label={title}>
      <h2>{title}</h2>
      <div className="announcement-viewport" ref={viewport}>
        {items.length && !animate ? (
          <div className="announcement-static-list">
            {items.map((item) => (
              onSelect ? <button key={item.id} className="announcement-item" title={item.description} onClick={() => onSelect(item.data)}>
                <strong>{item.label}</strong><span>{item.detail}</span><span aria-hidden="true">↗</span>
              </button> : <span key={item.id} className="announcement-item" title={item.description}>
                <strong>{item.label}</strong><span>{item.detail}</span>
              </span>
            ))}
          </div>
        ) : items.length ? (
          <div
            className="announcement-track"
            data-paused={paused}
            style={{ "--scroll-duration": `${Math.max(20, (copies * sizes.cycle) / 40)}s` }}
          >
            {[0, 1].map((group) => (
              <div className="announcement-group" key={group}>
                {Array.from({ length: copies }, (_, copy) => {
                  const duplicate = group > 0 || copy > 0;
                  return (
                    <div
                      key={copy}
                      ref={duplicate ? undefined : cycle}
                      className={`announcement-cycle${duplicate ? " announcement-duplicate" : ""}`}
                      aria-hidden={duplicate ? true : undefined}
                    >
                      {items.map((item) =>
                        onSelect ? (
                          <button
                            key={item.id}
                            className="announcement-item"
                            tabIndex={duplicate ? -1 : 0}
                            onClick={() => onSelect(item.data)}
                            title={item.description}
                          >
                            <strong>{item.label}</strong>
                            {item.detail && <span>{item.detail}</span>}
                            <span aria-hidden="true">↗</span>
                          </button>
                        ) : (
                          <span key={item.id} className="announcement-item" title={item.description}>
                            <strong>{item.label}</strong>
                            <span>{item.detail}</span>
                          </span>
                        ),
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        ) : (
          <p className="announcement-empty">{emptyText}</p>
        )}
      </div>
      {animate && items.length > 0 && (
        <button
          className="announcement-pause"
          type="button"
          aria-pressed={paused}
          aria-label={`${title} 자동 이동 ${paused ? "재생" : "일시정지"}`}
          onClick={() => setPaused((value) => !value)}
        >
          <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor" aria-hidden="true">
            {paused ? <path d="M6 3l11 7-11 7z" /> : <path d="M5 3h3v14H5zM12 3h3v14h-3z" />}
          </svg>
        </button>
      )}
    </section>
  );
}
