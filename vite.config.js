import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/Cursed-Doll/",
  plugins: [react()],
  server: {
    host: "127.0.0.1",
  },
});
