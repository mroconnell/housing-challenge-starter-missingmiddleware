import { defineConfig } from "vite";

// Static build: the JSON bundle in public/runs/ is copied as is; relative base so dist/ works from any path.
// The Introduction bundles three small reference CSVs at build time (src/screens/intro.ts), so the dev server may
// read the repository root (one level up).
export default defineConfig({
  base: "./",
  build: { outDir: "dist", sourcemap: false, chunkSizeWarningLimit: 1200 },
  server: { host: "127.0.0.1", fs: { allow: [".."] } },
});
