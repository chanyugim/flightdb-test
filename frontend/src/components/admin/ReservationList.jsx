import { formatWon } from "../../utils/format";

export default function ReservationList({ data }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>예약번호</th>
            <th>예약자</th>
            <th>금액</th>
            <th>상태</th>
            <th>회원</th>
          </tr>
        </thead>
        <tbody>
          {data.map((r) => (
            <tr key={r.reservation_no}>
              <td>{r.reservation_no}</td>
              <td>{r.booker_name}</td>
              <td>{formatWon(r.final_amount)}</td>
              <td>{r.reservation_status}</td>
              <td>{r.member_id ?? "비회원"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
