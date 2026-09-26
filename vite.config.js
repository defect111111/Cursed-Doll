import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiTarget = process.env.CURSED_DOLL_API_TARGET || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    proxy: {
      "/api": apiTarget,
    },
  },
});
