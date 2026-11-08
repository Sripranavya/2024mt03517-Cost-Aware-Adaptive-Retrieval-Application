import { expect, test } from "@playwright/test";

// End-to-end: log in, send a chat message, and assert the agent responds with a
// reasoning trace. Requires the backend running in local-mock mode on :8000.
test("login, send a message, and see the agent response", async ({ page }) => {
  await page.goto("/login");

  // Enter local credentials and submit the login form.
  await page.getByLabel(/username/i).fill("researcher");
  await page.getByLabel(/password/i).fill("local-demo");
  await page.getByRole("button", { name: /sign in/i }).click();

  // The chat composer should appear; send a question.
  const composer = page.getByPlaceholder(/send a message/i);
  await expect(composer).toBeVisible();
  await composer.fill("What is the capital of France?");
  await page.getByRole("button", { name: /^send/i }).click();

  // The agent response and its reasoning trace must render.
  await expect(page.getByText(/reasoning & trace/i)).toBeVisible({ timeout: 15_000 });
});
