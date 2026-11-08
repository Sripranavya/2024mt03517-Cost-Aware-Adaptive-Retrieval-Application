import { expect, test, type Page } from "@playwright/test";

// Live end-to-end UI test: drives the real page against a backend running on live AWS.
// Run with: E2E_NO_SERVER=1 E2E_CHANNEL=msedge E2E_PASSWORD=<demo password> npx playwright test live
// Skipped unless E2E_PASSWORD is set. Costs a few cents of Bedrock per run.

const PASSWORD = process.env.E2E_PASSWORD;
// Live-AWS-only assertions; set E2E_EXPECT_CLOUD=0 to check the harness against a mock backend.
const CLOUD = process.env.E2E_EXPECT_CLOUD !== "0";
const IN_INDEX = 'Eddie Jemison had a role in the television series "IZombie", which premiered on what date?';
const OUT_OF_INDEX = "How does photosynthesis convert light into chemical energy?";
const STRATEGIES = ["POMDP", "Fixed RAG", "Self-RAG", "Adaptive-RAG"];
// When set, a PNG of each step is written here (evidence for the report).
const SHOTS = process.env.E2E_SHOTS_DIR;
const slug = (s: string): string => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
let shotNo = 1;

test.describe.configure({ mode: "serial" });
test.skip(!PASSWORD, "set E2E_PASSWORD to run the live UI test");

interface Answer {
  strategy: string;
  hops: number;
  belief: number;
  tokens: number;
  usd: number;
  text: string;
}

async function ask(page: Page, strategy: string, question: string): Promise<Answer> {
  await page.getByLabel("Retrieval strategy").selectOption({ label: strategy });
  const before = await page.getByText(/^\d+ hops$/).count();
  await page.getByPlaceholder(/Send a message/).fill(question);
  await page.getByRole("button", { name: /^Send/ }).click();
  await expect(page.getByText(/^\d+ hops$/)).toHaveCount(before + 1, { timeout: 150_000 });

  const card = page.locator("div.rounded-2xl", { hasText: /\d+ hops/ }).last();
  const chips = await card.innerText();
  const num = (re: RegExp): number => Number(re.exec(chips)?.[1] ?? Number.NaN);
  const text = (await card.locator("p.whitespace-pre-wrap").first().innerText()).trim();
  if (SHOTS) {
    await card.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${SHOTS}/${String(shotNo++).padStart(2, "0")}-${slug(strategy)}.png` });
  }
  return {
    strategy,
    hops: num(/(\d+) hops/),
    belief: num(/belief ([\d.]+)/),
    tokens: num(/(\d+) tok/),
    usd: num(/\$([\d.]+)/),
    text,
  };
}

test("signs in, runs every strategy on live AWS, and shows a real trace", async ({ page }) => {
  test.setTimeout(600_000);
  await page.goto("/login");
  await page.getByLabel("Username").fill("demo");
  await page.getByLabel("Password").fill(PASSWORD ?? "");
  await page.getByRole("button", { name: /Sign in/ }).click();
  await expect(page.getByLabel("Retrieval strategy")).toBeVisible({ timeout: 30_000 });
  if (CLOUD) await expect(page.getByText(/Cloud · \d+ docs/)).toBeVisible({ timeout: 30_000 });

  const results: Answer[] = [];
  for (const strategy of STRATEGIES) {
    const a = await ask(page, strategy, IN_INDEX);
    results.push(a);
    expect(a.text.length).toBeGreaterThan(0);
    expect(a.hops).toBeGreaterThanOrEqual(1);
    expect(a.tokens).toBeGreaterThan(0);
    expect(a.usd).toBeGreaterThan(0);
  }

  console.log("\nUI comparison (same question, live AWS)");
  console.log("strategy       hops  belief  tokens   usd        answer");
  for (const a of results) {
    console.log(
      `${a.strategy.padEnd(14)} ${String(a.hops).padEnd(5)} ${a.belief.toFixed(3).padEnd(7)} ` +
        `${String(a.tokens).padEnd(8)} ${a.usd.toFixed(5).padEnd(10)} ${a.text.slice(0, 40)}`,
    );
  }

  const pomdp = results[0];
  if (CLOUD) expect(pomdp.text.toLowerCase()).toContain("march 17, 2015");

  // The reasoning trace of the latest answer opens and lists real hops.
  await page.getByText(/Reasoning & trace/).last().click();
  const steps = page.getByTestId("hop-trace-step");
  await expect(steps.last()).toBeVisible();
  expect(await steps.count()).toBeGreaterThanOrEqual(1);
  if (SHOTS) {
    await steps.last().scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${SHOTS}/${String(shotNo++).padStart(2, "0")}-reasoning-trace.png` });
  }

  // An out-of-index question must not produce a confident invented answer.
  const unsupported = await ask(page, "POMDP", OUT_OF_INDEX);
  if (CLOUD) {
    expect(
      unsupported.text.toLowerCase().includes("insufficient") || unsupported.belief < 0.5,
    ).toBe(true);
  }

  // Dashboard page loads for the signed-in user.
  await page.getByRole("link", { name: /Comparison/ }).first().click();
  await expect(page).toHaveURL(/\/compare/);
  await expect(page.getByRole("heading", { name: "Comparison Dashboard" })).toBeVisible();
  if (SHOTS) {
    await page.screenshot({ path: `${SHOTS}/${String(shotNo++).padStart(2, "0")}-comparison-dashboard.png` });
  }
});
