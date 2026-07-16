import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

// Mirror the server's extension-less /host alias (server/main.py) in dev.
function hostAlias(): Plugin {
  return {
    name: "host-alias",
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        if (req.url?.split("?")[0] === "/host") {
          req.url = req.url.replace("/host", "/host.html");
        }
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), hostAlias()],
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
