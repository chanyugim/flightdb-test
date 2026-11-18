const PATHS = {
  plane:
    "M22 12c0 .8-.8 1.4-1.7 1.4H15l-5 7.1H7.7l2.4-7.1H5.3L3.5 16H2l1-4-1-4h1.5l1.8 2.6h4.8L7.7 3.5H10l5 7.1h5.3c.9 0 1.7.6 1.7 1.4Z",
  expand: "m5 15 7-7 7 7",
  down: "m5 9 7 7 7-7",
};

export default function Icon({ name, className = "" }) {
  return (
    <svg className={`icon ${className}`} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d={PATHS[name]}
        fill={name === "plane" ? "currentColor" : "none"}
        stroke={name === "plane" ? "none" : "currentColor"}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
