import { useEffect, useState } from "react";

export default function Typewriter({ text, animate, children }) {
  const [length, setLength] = useState(animate ? 0 : Array.from(text).length);
  const chars = Array.from(text);
  useEffect(() => {
    if (!animate || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setLength(Array.from(text).length);
      return;
    }
    const total = Array.from(text).length;
    let count = 0;
    setLength(0);
    const timer = setInterval(() => {
      count += 1;
      setLength(count);
      if (count >= total) clearInterval(timer);
    }, 12);
    return () => clearInterval(timer);
  }, [text, animate]);
  return (
    <>
      <p className="typed-message" role="status" aria-label={text} aria-atomic="true">
        <span aria-hidden="true">{chars.slice(0, length).join("")}</span>
        {length < chars.length && (
          <span className="typing-cursor" aria-hidden="true">
            ▍
          </span>
        )}
      </p>
      {length >= chars.length && children}
    </>
  );
}
