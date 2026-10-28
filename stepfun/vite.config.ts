import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const seekdb = JSON.parse(
  readFileSync(new URL("./seekdb.config.json", import.meta.url), "utf8")
) as { host: string; port: number };

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ["@huggingface/transformers"],
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: `http://${seekdb.host}:${seekdb.port}`,
        changeOrigin: true,
      },
    },
  },
});
