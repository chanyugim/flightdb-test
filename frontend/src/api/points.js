export function formatPointChange({ change_type, change_amount }) {
  const amount = Number(change_amount);
  const sign =
    amount === 0
      ? ""
      : ["사용", "회수"].includes(change_type)
        ? "−"
        : ["적립", "반환"].includes(change_type)
          ? "+"
          : "";
  return `${sign}${amount.toLocaleString("ko-KR")}P`;
}
