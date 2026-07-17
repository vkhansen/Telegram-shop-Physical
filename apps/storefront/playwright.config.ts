import { defineConfig, devices } from "@playwright/test";

/**
 * Storefront browser e2e — commerce spine (C-08 → checkout → C-17).
 *
 * Expects:
 * - Public API on PUBLIC_API_BASE (default http://127.0.0.1:9090)
 * - Storefront dev server on http://127.0.0.1:4321
 *
 * Start API from repo root:  python scripts/run_public_api.py
 * Start storefront:          npm run dev
 *
 * Or set E2E_START_SERVERS=1 to let Playwright boot the storefront only
 * (API must already be up; reuseExistingServer preferred).
 */
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:4321";
const startServers = process.env.E2E_START_SERVERS === "1";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"]],
  timeout: 60_000,
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: startServers
    ? {
        command: "npm run dev -- --host 127.0.0.1 --port 4321",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      }
    : undefined,
});
