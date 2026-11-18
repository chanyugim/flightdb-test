import { useEffect, useRef, useState } from "react";
import { useRegisterSW } from "virtual:pwa-register/react";

export default function usePwa() {
  const [online, setOnline] = useState(navigator.onLine);
  const [installPrompt, setInstallPrompt] = useState(null);
  const [installed, setInstalled] = useState(
    () => window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true,
  );
  const [registration, setRegistration] = useState(null);
  const [installing, setInstalling] = useState(false);
  const [error, setError] = useState("");
  const lastUpdate = useRef(0);
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(_url, value) {
      setRegistration(value);
    },
    onRegisterError() {
      setError("앱 설치 준비를 완료하지 못했어요. 연결 상태를 확인하고 새로고침해 주세요.");
    },
  });
  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    const onInstallPrompt = (event) => {
      event.preventDefault();
      setInstallPrompt(event);
    };
    const onInstalled = () => {
      setInstalled(true);
      setInstallPrompt(null);
    };
    const media = window.matchMedia("(display-mode: standalone)");
    const onDisplayMode = () => setInstalled(media.matches || navigator.standalone === true);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    window.addEventListener("beforeinstallprompt", onInstallPrompt);
    window.addEventListener("appinstalled", onInstalled);
    media.addEventListener("change", onDisplayMode);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
      window.removeEventListener("beforeinstallprompt", onInstallPrompt);
      window.removeEventListener("appinstalled", onInstalled);
      media.removeEventListener("change", onDisplayMode);
    };
  }, []);
  useEffect(() => {
    if (!registration) return;
    const check = () => {
      if (
        !navigator.onLine ||
        document.visibilityState !== "visible" ||
        Date.now() - lastUpdate.current < 300000
      )
        return;
      lastUpdate.current = Date.now();
      registration.update().catch(() => {});
    };
    window.addEventListener("online", check);
    document.addEventListener("visibilitychange", check);
    return () => {
      window.removeEventListener("online", check);
      document.removeEventListener("visibilitychange", check);
    };
  }, [registration]);
  const install = async () => {
    if (!installPrompt || installing) return;
    setInstalling(true);
    try {
      await installPrompt.prompt();
      await installPrompt.userChoice;
      setInstallPrompt(null);
    } catch {
      setError("설치 창을 열지 못했어요. 브라우저 메뉴에서 앱 설치를 선택해 주세요.");
    } finally {
      setInstalling(false);
    }
  };
  const update = async () => {
    try {
      await updateServiceWorker(true);
    } catch {
      setError("새 버전을 불러오지 못했어요. 연결 후 다시 시도해 주세요.");
    }
  };
  return {
    online,
    installed,
    installing,
    canInstall: Boolean(installPrompt),
    install,
    needRefresh,
    dismissUpdate: () => setNeedRefresh(false),
    update,
    error,
    dismissError: () => setError(""),
  };
}
