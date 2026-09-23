import { defineConfig } from "@playwright/test";

// E2E config. Assumes the backend (8000) and frontend dev server (5173) are up,
// e.g. via `docker-compose up`. CI starts the frontend via the webServer hook.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    headless: true,
  },
  webServer: process.env.E2E_NO_SERVER
    ? undefined
    : {
        command: "npm run dev",
        url: "http://localhost:5173",
        reuseExistingServer: true,
        timeout: 60_000,
      },
});
