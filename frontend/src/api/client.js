const API_BASE = (import.meta.env?.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

function userErrorMessage(status, detail) {
  const safeKoreanDetail =
    typeof detail === "string" && /[가-힣]/.test(detail) &&
    !/\b(sql|http|api|database|token|schema|query|traceback|exception|internal server error)\b/i.test(detail) &&
    !/\b[a-z]+(?:_[a-z]+)+\b/i.test(detail);

  if (safeKoreanDetail) return detail;
  if (status === 0) return "서버에 연결할 수 없어요. 잠시 후 다시 시도해 주세요.";
  if (status === 401) return "로그인이 필요하거나 로그인 정보가 만료됐어요. 다시 로그인해 주세요.";
  if (status === 403) return "이 요청을 처리할 권한이 없어요.";
  if (status === 404) return "요청한 정보를 찾을 수 없어요. 입력한 내용을 확인해 주세요.";
  if (status === 409) return "현재 상태에서는 요청을 완료할 수 없어요. 최신 정보를 확인한 뒤 다시 시도해 주세요.";
  if (status === 422) return "입력한 내용을 확인해 주세요.";
  if (status === 429) return "요청이 많아요. 잠시 후 다시 시도해 주세요.";
  if (status >= 500) return "서비스에 일시적인 문제가 있어요. 잠시 후 다시 시도해 주세요.";
  if (status >= 400) return "요청 내용을 확인한 뒤 다시 시도해 주세요.";
  return "요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.";
}

// API_BASE 뒤에 경로와 값이 있는 검색 조건을 붙여 최종 요청 주소를 만듦.
function buildApiUrl(path, query) {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  // 값이 비어 있는 검색 조건은 쿼리에서 제외함.
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      for (const item of Array.isArray(value) ? value : [value]) url.searchParams.append(key, String(item));
    }
  }
  return url;
}

// 화면 컴포넌트가 공통으로 사용하는 API 요청 함수.
export async function requestApi(path, { method = "GET", token, body, query, signal, headers = {} } = {}) {
  const url = buildApiUrl(path, query);
  let response;
  try {
    response = await fetch(url, {
      method,
      signal,
      cache: "no-store",
      headers: {
        ...(url.hostname.endsWith("ngrok-free.app") || url.hostname.endsWith("ngrok-free.dev")
          ? { "ngrok-skip-browser-warning": "true" }
          : {}),
        ...headers,
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
  } catch (e) {
    // 사용자가 취소한 요청은 서버 연결 실패와 구분해 그대로 전달함.
    if (e.name === "AbortError") throw e;
    const error = new Error(
      globalThis.navigator?.onLine === false
        ? "인터넷 연결이 끊겼어요. 연결 후 다시 시도해 주세요."
        : "서버에 연결할 수 없습니다.",
    );
    error.status = 0;
    throw error;
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const error = new Error(userErrorMessage(response.status, detail));
    error.status = response.status;
    error.retryAfter = Number(response.headers.get("Retry-After")) || 60;
    throw error;
  }
  if (data === null && response.status !== 204)
    throw new Error("API 응답을 읽을 수 없어요. 서버 주소를 확인해 주세요.");
  return data;
}
