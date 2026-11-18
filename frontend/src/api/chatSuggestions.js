export function chatSuggestions(data) {
  if (!data) return ["다음 주 가장 저렴한 항공편을 보여줘", "현재 프로모션을 알려줘", "인기 노선을 알려줘"];
  if (data.clarification?.options?.length) return [];
  if (data.status === "needs_clarification") {
    const field = data.clarification?.field;
    if (field === "departure") return ["인천에서 출발할게요", "김포에서 출발할게요"];
    if (field === "arrival") return ["제주로 가고 싶어요", "도쿄 나리타로 가고 싶어요"];
    if (field === "date") return ["다음 주 월요일에 출발할게요", "이번 주말에 출발할게요"];
    return ["새로운 항공편을 검색할게요", "문의 작성 방법을 알려줘"];
  }
  if (data.flights?.length || data.round_trips?.length)
    return [
      "가격이 저렴한 순으로 보여줘",
      "오전에 출발하는 항공편만 보여줘",
      "현재 진행 중인 프로모션도 알려줘",
    ];
  if (data.promotions?.length) return ["회원 등급별 혜택을 알려줘", "다음 주 가장 저렴한 항공편을 보여줘"];
  if (data.popular_routes?.length || data.frequent_routes?.length || data.destinations?.length)
    return ["다음 주 가장 저렴한 항공편을 보여줘", "현재 프로모션을 알려줘"];
  if (data.topics?.includes("flights")) return ["가격 제한 없이 다시 찾아줘", "새로운 항공편을 검색할게요"];
  return ["인기 노선을 알려줘", "현재 프로모션을 알려줘", "다음 주 가장 저렴한 항공편을 보여줘"];
}
