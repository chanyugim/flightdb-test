const BANDS = [
  ["", "전체"],
  ["dawn", "새벽 (00~06시)"],
  ["morning", "오전 (06~12시)"],
  ["afternoon", "오후 (12~18시)"],
  ["evening", "저녁 (18~24시)"],
];

export default function FlightTimeFilters({ form, inbound = false, onChange }) {
  const prefix = inbound ? "return_" : "";
  const departureDate = inbound ? form.return_date : form.date;
  const arrivalDate = form[`${prefix}arrival_date`] || departureDate;
  const title = inbound ? "오는 편" : "가는 편";
  const bandSelect = (field, disabled) => (
    <select value={form[field]} disabled={disabled} onChange={(e) => onChange(field, e.target.value)}>
      {BANDS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
    </select>
  );

  return (
    <fieldset className="flight-time-filters">
      <legend>{title} 시간</legend>
      <div className="form-row">
        <label>
          출발 시간대
          {bandSelect(`${prefix}departure_time_band`, !departureDate)}
        </label>
        {!departureDate && <span className="small muted">{inbound ? "오는" : "가는"} 날을 먼저 선택해 주세요.</span>}
      </div>
      <div className="form-row">
        <label>
          도착 시간대
          {bandSelect(`${prefix}arrival_time_band`, !arrivalDate)}
        </label>
        {arrivalDate && <span className="small muted">도착 기준일: {arrivalDate} (한국 시간)</span>}
      </div>
      {departureDate && <details>
        <summary>도착일이 출발일과 다른 경우</summary>
        <div className="form-row">
          <label>
            도착 날짜
            <input type="date" min={departureDate} value={arrivalDate}
              onChange={(e) => onChange(`${prefix}arrival_date`, e.target.value)} />
          </label>
          <span className="small muted">기본값은 상단에서 선택한 출발 날짜예요. 다음 날 도착하는 항공편은 날짜를 변경해 주세요.</span>
        </div>
      </details>}
    </fieldset>
  );
}
