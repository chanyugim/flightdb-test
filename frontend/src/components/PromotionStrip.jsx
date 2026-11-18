import { useEffect, useState } from "react";
import { formatKst } from "../utils/format.js";
import AnnouncementStrip from "./AnnouncementStrip";
import { useNavigate } from "react-router-dom";

export default function PromotionStrip({ promotions }) {
  const navigate = useNavigate();
  const [mobile, setMobile] = useState(() => window.matchMedia("(max-width: 800px)").matches);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 800px)");
    const update = () => setMobile(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  const items = promotions.map((promotion) => ({
    id: promotion.promotion_id,
    data: promotion.promotion_id,
    label: `${promotion.promotion_name} · ${Number(promotion.discount_rate)}% 할인`,
    detail: `예약 적용 기간 ${formatKst(promotion.start_at)} ~ ${formatKst(promotion.end_at)} (한국 시각)`,
    description: "탑승일이 아닌 예약 시점 기준이며, 예약 화면에서 프로모션을 선택해 주세요.",
  }));
  return (
    <AnnouncementStrip
      title="진행 중인 프로모션"
      tone="promotions"
      items={items}
      onSelect={(id) => navigate(`/benefits#promotion-${id}`)}
      animate={promotions.length > (mobile ? 1 : 2)}
      emptyText="현재 진행 중인 프로모션이 없어요."
    />
  );
}
