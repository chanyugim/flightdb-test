import { useState } from "react";
import "../pwa.css";

export function PwaStatus({ pwa }) {
  return (
    <div className="pwa-status" aria-live="polite">
      {!pwa.online && (
        <p role="status">인터넷 연결이 끊겼어요. 항공편 조회와 예약은 연결 후 이용해 주세요.</p>
      )}
      {pwa.needRefresh && (
        <div className="pwa-update" role="status">
          <span>새 버전이 준비됐어요. 새로고침하면 입력 중인 내용이 초기화돼요.</span>
          <button type="button" onClick={pwa.update} disabled={!pwa.online}>
            새로고침
          </button>
          <button type="button" onClick={pwa.dismissUpdate}>
            나중에
          </button>
        </div>
      )}
      {pwa.error && (
        <div className="pwa-update" role="alert">
          <span>{pwa.error}</span>
          <button type="button" onClick={pwa.dismissError}>
            닫기
          </button>
        </div>
      )}
    </div>
  );
}

export function InstallApp({ pwa }) {
  const [showHelp, setShowHelp] = useState(false);
  if (pwa.installed) return null;
  const ios =
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  return (
    <div className="pwa-install">
      {pwa.canInstall ? (
        <button type="button" onClick={pwa.install} disabled={pwa.installing}>
          앱 설치
        </button>
      ) : (
        <button
          type="button"
          onClick={() => setShowHelp(!showHelp)}
          aria-expanded={showHelp}
          aria-controls="install-help"
        >
          앱 설치 안내
        </button>
      )}
      {showHelp && (
        <p id="install-help">
          {ios
            ? "Safari의 공유 메뉴에서 ‘홈 화면에 추가’를 선택해 주세요."
            : "Chrome 또는 Edge의 주소창 설치 아이콘이나 브라우저 메뉴의 앱 설치를 이용해 주세요. 설치 메뉴가 없으면 웹으로 계속 이용할 수 있어요."}
        </p>
      )}
    </div>
  );
}
