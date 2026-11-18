import assert from "node:assert/strict";
import { test } from "node:test";
import { cancellationReason } from "../src/api/reservationStatus.js";
import { chatDisplayMessage } from "../src/api/chatPresentation.js";
import { formatPointChange } from "../src/api/points.js";

test("검색 결과와 부가 안내를 문단으로 나누되 금액·날짜·목록은 보존함", () => {
  const data = { message: "항공편 2건을 찾았어요. 표시된 금액은 1인 기본 요금이에요. 할인율은 1.5%예요.\n출발: 2026. 11. 25.\n도착: 파리" };
  assert.equal(chatDisplayMessage(data), "항공편 2건을 찾았어요.\n\n표시된 금액은 1인 기본 요금이에요. 할인율은 1.5%예요.\n출발: 2026. 11. 25.\n도착: 파리");
  assert.ok(!data.message.includes("\n\n"));
  const existing = "조건을 확인해 주세요.\n\n조회한 귀국편 출발 기간: 11월 26일~12월 25일";
  assert.equal(chatDisplayMessage({ message: existing }), existing);
  assert.equal(chatDisplayMessage({ message: "항공편을 찾지 못했어요. 다른 날짜나 목적지도 찾아볼까요?" }), "항공편을 찾지 못했어요.\n\n다른 날짜나 목적지도 찾아볼까요?");
});

test("포인트 절댓값은 사용·회수 시 차감, 적립·반환 시 증가로 표시함", () => {
  for (const change_type of ["사용", "회수"]) {
    assert.equal(formatPointChange({ change_type, change_amount: 1200 }), "−1,200P");
  }
  for (const change_type of ["적립", "반환"]) {
    assert.equal(formatPointChange({ change_type, change_amount: 1200 }), "+1,200P");
  }
  assert.equal(formatPointChange({ change_type: "회수", change_amount: 0 }), "0P");
});

test("취소 가능 여부는 KST 출발 시각과 결항 예외, 왕복의 두 구간을 반영함", () => {
  const now = Date.parse("2026-11-16T03:00:00Z");
  const flight = { flight_status: "예정", departure_at: "2026-11-16T12:00:00" };
  const reservation = { reservation_status: "확정", flight };
  assert.match(cancellationReason(reservation, now), /이미 출발/);
  assert.equal(cancellationReason(reservation, now - 1), "");
  assert.equal(cancellationReason({ ...reservation, flight: { ...flight, flight_status: "결항" } }, now), "");
  assert.match(
    cancellationReason({ ...reservation, flight: { ...flight, flight_status: "완료" } }, now - 1),
    /완료/,
  );
  assert.match(
    cancellationReason(
      {
        ...reservation,
        trip_type: "round_trip",
        segments: [{ flight }, { flight: { ...flight, departure_at: "2026-11-20T12:00:00" } }],
      },
      now,
    ),
    /구간/,
  );
  assert.match(cancellationReason({ ...reservation, reservation_status: "취소" }, now), /취소된/);
});

test("카드에 표시되는 목록만 생략하고 통계 기준·로그인 안내와 원문은 보존함", () => {
  const row = "김포 → 제주: 예약 7건";
  const data = {
    message: `최근 30일간 확정 예약 기준이에요.\n${row}\n실제 탑승 확인 기록은 아니에요.\n자주 이용한 노선은 로그인해 주세요.`,
    popular_routes: [
      { departure_airport: { name_ko: "김포" }, arrival_airport: { name_ko: "제주" }, reservation_count: 7 },
    ],
  };
  const visible = chatDisplayMessage(data);
  assert.ok(!visible.includes(row));
  assert.match(visible, /30일/);
  assert.match(visible, /실제 탑승/);
  assert.match(visible, /로그인/);
  assert.ok(data.message.includes(row));
  assert.equal(chatDisplayMessage({ message: data.message }), data.message);
});

test("프로모션 기간과 할인율이 카드 데이터와 일치할 때만 중복 행을 제거함", () => {
  const row = "겨울 할인 — 10.00% 할인, 2026-11-01 00:00 ~ 2027-01-31 23:59(한국 시각)";
  const data = {
    message: `프로모션을 안내해 드릴게요.\n${row}\n탑승일이 아니라 예약 시점의 적용 기간이에요.`,
    promotions: [
      {
        promotion_name: "겨울 할인",
        discount_rate: "10.00",
        start_at: "2026-11-01T00:00:00",
        end_at: "2027-01-31T23:59:59",
      },
    ],
  };
  assert.ok(!chatDisplayMessage(data).includes(row));
  assert.match(chatDisplayMessage(data), /예약 시점/);
  const different = { ...data, message: data.message.replace("10.00%", "15.00%") };
  assert.match(chatDisplayMessage(different), /15.00%/);
});
