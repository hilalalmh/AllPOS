import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Pisahkan vendor besar (recharts + react) jadi chunk terpisah agar
        // index.js tidak melampaui 500 kB. Behavior runtime tidak berubah.
        manualChunks: {
          "vendor-chart": ["recharts"],
          "vendor-react": ["react", "react-dom", "react-router-dom", "zustand"],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      // Gambar produk disajikan backend dari /uploads (Statics), bukan dari
      // origin web dev. Tanpa proxy ini <img src="/uploads/..."> di browser
      // akan gagal dimuat dan melanggar CSP img-src 'self'.
      "/uploads": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});