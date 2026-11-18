import re
import unicodedata


CITY_ALIASES = {
    "서울": "seoul",
    "부산": "busan",
    "제주": "jeju",
    "제주도": "jeju",
    "대구": "daegu",
    "청주": "cheongju",
    "광주": "gwangju",
    "울산": "ulsan",
    "양양": "yangyang",
    "도쿄": "tokyo",
    "동경": "tokyo",
    "오사카": "osaka",
    "후쿠오카": "fukuoka",
    "삿포로": "sapporo",
    "나고야": "nagoya",
    "오키나와": "okinawa",
    "런던": "london",
    "파리": "paris",
    "방콕": "bangkok",
    "싱가포르": "singapore",
    "타이베이": "taipei",
    "타이페이": "taipei",
    "홍콩": "hong kong",
    "베이징": "beijing",
    "북경": "beijing",
    "상하이": "shanghai",
    "상해": "shanghai",
    "호놀룰루": "honolulu",
    "뉴욕": "new york",
    "nyc": "new york",
    "로스앤젤레스": "los angeles",
    "로스엔젤레스": "los angeles",
    "la": "los angeles",
    "샌프란시스코": "san francisco",
    "시드니": "sydney",
    "멜버른": "melbourne",
    "토론토": "toronto",
    "밴쿠버": "vancouver",
    "다낭": "da nang",
    "나트랑": "nha trang",
    "하노이": "hanoi",
    "호찌민": "ho chi minh",
    "호치민": "ho chi minh",
    "마닐라": "manila",
    "세부": "cebu",
    "푸켓": "phuket",
    "쿠알라룸푸르": "kuala lumpur",
    "울란바토르": "ulaanbaatar",
    "두바이": "dubai",
    "이스탄불": "istanbul",
    "마드리드": "madrid",
    "로마": "rome",
}
COUNTRY_ALIASES = {
    "일본": "japan",
    "영국": "united kingdom",
    "미국": "united states of america",
    "한국": "republic of korea",
    "대한민국": "republic of korea",
    "프랑스": "france",
    "태국": "thailand",
    "중국": "china",
    "대만": "taiwan",
    "베트남": "vietnam",
    "독일": "germany",
    "호주": "australia",
    "캐나다": "canada",
    "필리핀": "philippines",
    "말레이시아": "malaysia",
    "인도네시아": "indonesia",
    "몽골": "mongolia",
    "이탈리아": "italia",
    "스페인": "spain",
    "아랍에미리트": "united arab emirates",
    "튀르키예": "republic of turkiye",
    "터키": "republic of turkiye",
    "uk": "united kingdom",
    "gb": "united kingdom",
    "us": "united states of america",
    "usa": "united states of america",
    "unitedstates": "united states of america",
    "southkorea": "republic of korea",
    "kr": "republic of korea",
    "jp": "japan",
}
COUNTRY_VARIANTS = {
    "united states of america": (
        "united states of america",
        "united states",
        "us",
        "usa",
    ),
    "republic of korea": ("republic of korea", "south korea", "kr"),
    "united kingdom": ("united kingdom", "uk", "gb"),
    "vietnam": ("vietnam", "viet nam"),
    "italia": ("italia", "italy"),
    "republic of turkiye": ("republic of turkiye", "turkey", "turkiye", "türkiye"),
}
REGIONS = {
    "하와이": ("HNL", "OGG", "KOA", "LIH", "ITO", "MKK", "LNY"),
    "hawaii": ("HNL", "OGG", "KOA", "LIH", "ITO", "MKK", "LNY"),
}


def compact_location(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", value).casefold())


def country_names(value):
    key = compact_location(value)
    country = COUNTRY_ALIASES.get(key)
    if country:
        return COUNTRY_VARIANTS.get(country, (country,))
    for variants in COUNTRY_VARIANTS.values():
        if key in {compact_location(name) for name in variants}:
            return variants
    return None
