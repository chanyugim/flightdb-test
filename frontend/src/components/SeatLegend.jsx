export default function SeatLegend({ roundTrip = false }) {
  return (
    <div className="legend seat-legend" aria-label="좌석 상태 안내">
      <span>
        <i className="available" />
        선택 가능
      </span>
      <span>
        <i className="selected" />
        선택함
      </span>
      {roundTrip && (
        <span>
          <i className="assigned" />
          다른 탑승객
        </span>
      )}
      <span>
        <i className="unavailable" />
        예약됨
      </span>
    </div>
  );
}
