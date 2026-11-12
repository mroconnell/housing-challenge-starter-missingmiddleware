import { defineConfig, devices } from "@playwright/test";

// Smoke tests run against the production build served by `vite preview` (run `npm run build` first,
// or use `bash scripts/test_ui.sh`, which does both). Chromium only; uses an existing Playwright
// browser install (PLAYWRIGHT_BROWSERS_PATH or the default cache).
export default defineConfig({
  testDir: "tests",
  timeout: 60_000,
  retries: 0,
  reporter: [["list"]],
  // The content tests open unfinished pages too: "mm-show-unfinished" shows every page as finished (ui/src/finished.ts).
  // tests/finished.spec.ts clears it to check the greyed tabs, the "coming soon" note and that nothing links to them.
  use: { baseURL: "http://127.0.0.1:4317/", trace: "off",
    storageState: { cookies: [], origins: [{ origin: "http://127.0.0.1:4317", localStorage: [{ name: "mm-show-unfinished", value: "1" }] }] } },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 } } },
    { name: "mobile", use: { ...devices["Pixel 7"], browserName: "chromium" } },
  ],
  webServer: { command: "npx vite preview --host 127.0.0.1 --port 4317 --strictPort", url: "http://127.0.0.1:4317/", reuseExistingServer: false, timeout: 60_000 },
});
