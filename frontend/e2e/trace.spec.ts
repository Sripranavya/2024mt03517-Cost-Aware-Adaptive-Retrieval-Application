import { expect, test } from "@playwright/test";

// End-to-end: log in, submit a query, and assert the trace viewer renders at
// least one hop. Requires the backend running in local-mock mode on :8000.
test("login, run a query, and see the hop trace", async ({ page }) => {
  await page.goto("/login");

  // Local demo credentials are prefilled; submit the login form.
  await page.getByRole("button", { name: /sign in/i }).click();

  // Land on the query page and run the default query.
  await expect(page.getByRole("button", { name: /run query/i })).toBeVisible();
  await page.getByRole("button", { name: /run query/i }).click();

  // The answer and at least one hop-trace step must render.
  await expect(page.getByText(/Answer/i)).toBeVisible();
  const steps = page.getByTestId("hop-trace-step");
  await expect(steps.first()).toBeVisible({ timeout: 15_000 });
  expect(await steps.count()).toBeGreaterThanOrEqual(1);
});
