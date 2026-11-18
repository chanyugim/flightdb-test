import re
from datetime import date

REASONS = {
    "discount_calculation": "할인이나 포인트를 적용한 최종 금액으로 항공편을 비교하는 기능은 아직 없어요. 기본 요금 기준으로 찾아드릴까요?",
    "promotion_period": "프로모션 기간은 탑승일이 아니라 예약하는 시점에 적용되는 기간이에요. 이벤트 기간을 출발일에 자동 적용하거나 할인 후 최저가를 비교하는 기능은 아직 없어요. 말씀하신 여행 기간의 항공편을 기본 요금 기준으로 찾고, 현재 이용 가능한 프로모션을 함께 안내해 드릴까요?",
    "multiple_promotions": "프로모션은 예약 한 건에 하나만 적용할 수 있어요. 여러 프로모션을 합산한 할인 검색은 지원하지 않아요.",
    "airline_exclusion": "특정 항공사를 제외하는 검색은 아직 지원하지 않아요. 이용하실 항공사를 지정해 주시면 찾아드릴게요.",
    "duration": "비행시간이나 공항까지의 거리로 비교하는 기능은 아직 없어요. 출발 시각·도착 시각·기본 요금으로 찾아드릴 수 있어요.",
    "return_time": "가는 날은 하루를 정해 주세요. 돌아오는 날은 날짜 하나 또는 최대 30일의 기간으로 찾아드릴 수 있어요.",
    "local_time": "현재는 한국 시간 기준으로 검색하고 있어요. 원하시는 출발·도착 시간을 한국 시간으로 알려주시겠어요?",
    "connections": "현재는 직항 항공편만 검색할 수 있어요. 직항으로 찾아드릴까요?",
    "passengers": "챗봇은 1인 기준으로 조회해요. 여러 명의 좌석이나 어린이·유아 운임은 보장해 드릴 수 없어요.",
    "private_data": "개인 예약·포인트·회원 정보는 챗봇에서 조회할 수 없어요. 로그인 후 해당 메뉴에서 확인해 주세요.",
    "mutation": "예약·취소나 포인트 변경은 챗봇에서 처리할 수 없어요. 해당 메뉴를 이용해 주세요.",
    "external_data": "실시간 날씨·환율 정보는 연동되어 있지 않아요. 항공편의 기본 요금과 일정으로 찾아드릴까요?",
    "security": "권한이나 제한을 변경하려는 요청을 실행할 수는 없어요. 원하시는 항공편 조건을 말씀해 주세요.",
    "recurring_time": "여러 날짜에 반복되는 시간대 조건은 아직 지원하지 않아요. 특정 날짜나 연속된 시간 범위로 말씀해 주세요.",
    "out_of_scope": "편도·왕복 항공편, 프로모션·회원 등급, 최근 30일 인기 노선, 로그인한 회원님의 자주 이용한 노선과 문의 작성 방법을 안내해 드릴 수 있어요. 노선 통계의 기간·공항별 조건 지정은 아직 지원하지 않아요.",
    "invalid_date": "입력하신 날짜가 존재하지 않거나 날짜 조건이 맞지 않아요. 여행 날짜를 다시 확인해 주시겠어요?",
    "invalid_price": "최소 금액이 최대 금액보다 높아요. 원하시는 가격 범위를 다시 알려주시겠어요?",
    "missing_context": "이전 검색 조건을 확인할 수 없어요. 원하시는 항공편 조건을 다시 말씀해 주세요.",
    "ambiguous_time": "정확한 여행 날짜와 원하시는 시간대를 알려주시겠어요? 말씀하신 시간만으로 날짜나 퇴근·출근 시각을 정하기는 어려워요.",
}

CAPABILITIES = {
    "supported": [
        "편도·왕복 직항 1인 기본 요금 검색",
        "공항·도시·국가·등록 지역 검색",
        "특정 항공사 포함 및 여러 항공사 제외 (왕복은 양쪽 편에 적용)",
        "예약 가능한 도착 공항 목록",
        "현재 프로모션",
        "공개 회원 등급",
        "최근 30일간 확정 예약 건수 기준 전체 인기 노선",
        "로그인한 본인의 도착 시각이 지난 확정 예약 기준 자주 이용한 노선",
        "문의 작성·답변 조회 화면 이용 안내 (챗봇 내 등록·조회는 수행하지 않음)",
        "서로 다른 출발일·도착일 시간 범위",
        "왕복 가는 편·오는 편 각각의 출발·도착 시간 범위 (한국 시간)",
        "출국일 하나와 귀국 출발 날짜 기간으로 왕복 검색 (최대 30일, 종료일 생략 시 시작일부터 30일)",
        "제안 수락·거절과 감사·대화 마무리에 대한 조회 없는 응답",
    ],
    "optional": ["departure", "arrival", "편도의 date"],
    "round_trip_required": ["date", "return_date 또는 return_date_from (return_date_to 선택)"],
    "unsupported": {
        key: REASONS[key]
        for key in (
            "discount_calculation",
            "multiple_promotions",
            "duration",
            "return_time",
            "local_time",
            "connections",
            "passengers",
            "private_data",
            "mutation",
            "external_data",
            "recurring_time",
        )
    },
}


def explicit_dates(question):
    return list(
        re.finditer(
            r"(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월\s*(\d{1,2})\s*일|(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)",
            question,
        )
    )


def guard_question(question):
    lowered = question.casefold()
    if re.search(
        r"\b(select|union|drop|alter|delete|update|insert|create|information_schema|sqlite_master)\b|or\s+['\d].*=|%27|--|/\*",
        lowered,
    ):
        return "security"
    if re.search(
        r"(지침|규칙|권한|검증).{0,20}(무시|제거|해제|생략)|(?:보안|보호|조회)\s*(?:필터|제한).{0,15}(무시|제거|해제)|범용\s*sql|테스트\s*모드|\[system\]|allow_all_queries|비밀번호.*해시",
        lowered,
    ):
        return "security"
    for match in explicit_dates(question):
        y, m, d, iy, im, iday = match.groups()
        year = int(y or iy or 2000)
        try:
            date(year, int(m or im), int(d or iday))
        except ValueError:
            return "invalid_date"
    if re.search(
        r"비행\s*시간.{0,15}(이내|이하|짧|최단)|가장\s*가까운\s*공항", question
    ):
        return "duration"
    return None
