import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      includeAssets: ["icons/*.png", "icons/*.svg", "images/*.jpg"],
      manifest: {
        id: "/",
        name: "항공권 예매 서비스",
        short_name: "항공권 예매",
        description: "항공편 검색, 좌석 선택 및 예약 서비스",
        lang: "ko",
        start_url: "/",
        scope: "/",
        display: "standalone",
        theme_color: "#05203c",
        background_color: "#f1f2f8",
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
          { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,png,svg,webmanifest}"],
        cleanupOutdatedCaches: true,
        navigateFallback: "index.html",
        navigateFallbackDenylist: [/^\/api(?:\/|$)/, /^\/assets\//, /\.[^/]+$/],
        runtimeCaching: [],
      },
      devOptions: { enabled: false },
    }),
  ],
  // 프론트 개발 서버 주소와 포트를 지정함.
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
});
