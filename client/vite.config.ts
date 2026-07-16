import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    // Dev: vite serves the frontend, uvicorn (port 8000) handles WebSockets.
    proxy: {
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
