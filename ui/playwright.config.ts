import { defineConfig, devices } from "@playwright/test";

// Smoke tests run against the production build served by `vite preview` (run `npm run build` first,
// or use `bash scripts/test_ui.sh`, which does both). Chromium only; uses an existing Playwright
// browser install (PLAYWRIGHT_BROWSERS_PATH or the default cache).
export default defineConfig({
  testDir: "tests",
  timeout: 60_000,
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: "http://127.0.0.1:4317/", trace: "off" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 } } },
    { name: "mobile", use: { ...devices["Pixel 7"], browserName: "chromium" } },
  ],
  webServer: { command: "npx vite preview --host 127.0.0.1 --port 4317 --strictPort", url: "http://127.0.0.1:4317/", reuseExistingServer: false, timeout: 60_000 },
});
