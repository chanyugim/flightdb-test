from app.schemas.member import RouteRecommendation
from app.services.members import get_recommended_routes
from app.services.route_stats import list_route_statistics


def answer_routes(db, response, current_member):
    messages = []
    if "popular_routes" in response.topics:
        rows = list_route_statistics(db, days=30, limit=min(response.limit, 20))
        response.popular_routes = [
            RouteRecommendation.model_validate(row) for row in rows
        ]
        messages.append(
            _describe(
                response.popular_routes,
                "최근 30일간 등록된 확정 예약이 많은 노선이에요. 취소된 예약과 결항편은 제외했어요.",
                "최근 30일간 집계할 확정 예약이 없어 아직 인기 노선을 안내해 드리기 어려워요.",
            )
        )
    if "frequent_routes" in response.topics:
        if current_member is None:
            response.navigation.append("login")
            messages.append(
                "자주 이용하신 노선은 로그인 후 확인할 수 있어요. 회원 메뉴에서 로그인해 주세요."
            )
        else:
            rows = get_recommended_routes(db, min(response.limit, 20), current_member)
            response.frequent_routes = [
                RouteRecommendation.model_validate(row) for row in rows
            ]
            messages.append(
                _describe(
                    response.frequent_routes,
                    "회원님의 도착 시각이 지난 확정 예약을 기준으로 자주 예약하신 노선이에요. 실제 탑승 확인 기록은 아니에요.",
                    "아직 도착 시각이 지난 확정 예약이 없어 자주 이용하신 노선을 안내해 드리기 어려워요.",
                )
            )
    return messages


def _describe(routes, introduction, empty):
    if not routes:
        return empty
    return (
        introduction
        + "\n"
        + "\n".join(
            f"{route.departure_airport.name_ko} → {route.arrival_airport.name_ko}: 예약 {route.reservation_count}건"
            for route in routes
        )
        + "\n동행자 수와 관계없이 같은 예약의 같은 방향 노선은 한 건으로 계산했어요."
    )


INQUIRY_GUIDE = (
    "문의는 문의 작성 화면에서 남겨 주세요. 제목과 문의 내용, 작성자 이름·연락처를 입력하시면 돼요. "
    "비회원은 나중에 답변을 확인할 수 있도록 조회 비밀번호도 설정하고, 등록 후 문의 번호를 보관해 주세요. "
    "회원은 로그인 후 내 문의에서, 비회원은 문의 번호와 비밀번호로 답변을 확인할 수 있어요. "
    "이 대화에서는 문의를 등록하거나 답변을 조회하지 않아요. 개인정보와 비밀번호는 문의 화면에서 입력해 주세요."
)
