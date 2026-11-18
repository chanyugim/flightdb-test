import { parseKstDate } from "../utils/format.js";

function promotionDate(value) {
  const date = parseKstDate(value);
  if (!date || !Number.isFinite(date.getTime())) return "";
  return new Date(date.getTime() + 9 * 60 * 60 * 1000).toISOString().slice(0, 16).replace("T", " ");
}

export function chatDisplayMessage(data) {
  // 카드에 모두 표시하는 항목만 제거함. 원문은 대화 기록과 후속 요청에 그대로 보관함.
  const rows = new Set();
  for (const route of [...(data.popular_routes ?? []), ...(data.frequent_routes ?? [])]) {
    rows.add(
      `${route.departure_airport.name_ko} → ${route.arrival_airport.name_ko}: 예약 ${route.reservation_count}건`,
    );
  }
  for (const promotion of data.promotions ?? []) {
    rows.add(
      `${promotion.promotion_name} — ${Number(promotion.discount_rate)}% 할인, ${promotionDate(promotion.start_at)} ~ ${promotionDate(promotion.end_at)}(한국 시각)`,
    );
  }
  const message = (data.message ?? "")
    .split("\n")
    .filter((line) => {
      const normalized = line.replace(
        /(— )(\d+(?:\.\d+)?)(% 할인,)/,
        (_, prefix, rate, suffix) => `${prefix}${Number(rate)}${suffix}`,
      );
      return !rows.has(normalized);
    })
    .join("\n");
  return separateChatParagraphs(message);
}

function separateChatParagraphs(message) {
  // 결과 안내와 요금·예약 유의사항, 다음 행동 안내 사이에서만 문단을 나눔.
  return message
    .replace(/([.!?]) +(?=표시된? (?:금액|시각)|표시 시각|여행 날짜나 공항 조건|다른 날짜나 목적지|다른 목적지도|가격 범위를 바꿔|새로 찾을 항공편|원하시는 조건이면)/g, "$1\n\n")
    .replace(/([^\n])\n(?=조회한 귀국편 출발 기간:|적용한 시간 조건)/g, "$1\n\n");
}
