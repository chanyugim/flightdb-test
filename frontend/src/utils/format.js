const kstFormat = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  dateStyle: "medium",
  timeStyle: "short",
});
const timeFormat = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});
const dateFormat = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  month: "long",
  day: "numeric",
  weekday: "short",
});
const wonFormat = new Intl.NumberFormat("ko-KR");

export function parseKstDate(value) {
  if (!value) return null;
  // 시간대 정보가 없는 시각은 KST로 해석하고, 정보가 있으면 입력값을 존중함.
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
  return new Date(hasTimezone ? value : `${value}+09:00`);
}

export function formatKst(value) {
  if (!value) return "";
  return kstFormat.format(parseKstDate(value));
}

export function formatTime(value) {
  if (!value) return "";
  return timeFormat.format(parseKstDate(value));
}

export function formatDate(value) {
  if (!value) return "";
  return dateFormat.format(parseKstDate(value));
}

export function formatDuration(from, to) {
  // 출발과 도착 사이 시간을 계산해 시간·분 단위로 표시함.
  const minutes = Math.round((parseKstDate(to) - parseKstDate(from)) / 60000);
  if (!Number.isFinite(minutes) || minutes <= 0) return "";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}시간 ${m ? `${m}분` : ""}`.trim() : `${m}분`;
}

export function formatWon(value) {
  return `${wonFormat.format(Number(value))}원`;
}

export function toDateTimeInput(value) {
  if (!value) return "";
  return new Date(parseKstDate(value).getTime() + 9 * 3600000).toISOString().slice(0, 19);
}
