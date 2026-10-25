import { defineConfig } from "vite";

// Static build: the JSON bundle in public/runs/ is copied as is; relative base so dist/ works from any path.
export default defineConfig({
  base: "./",
  build: { outDir: "dist", sourcemap: false, chunkSizeWarningLimit: 1200 },
  server: { host: "127.0.0.1" },
});
