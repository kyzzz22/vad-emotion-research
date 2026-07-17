const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const baseUrl = process.env.A2_BASE_URL || "http://127.0.0.1:8765";
const outputDir = path.resolve(__dirname, "..", "results", "ui");
fs.mkdirSync(outputDir, { recursive: true });

async function chooseAll(page, value = "5") {
  const fields = page.locator(".scale-field");
  const count = await fields.count();
  for (let index = 0; index < count; index += 1) {
    const option = fields.nth(index).locator(".scale-option").nth(Number(value) - 1);
    await option.locator("span").click({ force: true });
    if (!(await option.locator("input").isChecked())) throw new Error(`Scale ${index} did not retain selection`);
  }
}

async function assertNoHorizontalOverflow(page) {
  const overflow = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth,
  }));
  if (overflow.content > overflow.viewport + 1) {
    throw new Error(`Horizontal overflow: ${JSON.stringify(overflow)}`);
  }
}

async function answerComprehension(page, value) {
  await page.locator(`input[name="comprehension"][value="${value}"]`).check();
  await page.getByRole("button", { name: "确认" }).click();
}

async function runSemantic(browser) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.goto(`${baseUrl}/?test=1`);
  await page.locator("#participantId").fill("P001");
  await page.locator("#sessionId").selectOption("S1");
  await page.getByRole("button", { name: "核对并开始" }).click();
  await page.getByRole("button", { name: "继续" }).click();
  await page.getByRole("button", { name: "开始区块" }).click();
  const firstCondition = await page.locator(".instruction").textContent();
  await answerComprehension(page, firstCondition.includes("词本身") ? "lexical" : "prototype");
  await page.screenshot({ path: path.join(outputDir, "semantic-desktop.png"), fullPage: true });

  for (let completed = 0; completed < 36; completed += 1) {
    await page.locator(".rating-form").waitFor();
    if (await page.locator(".scale-field").count() !== 3) throw new Error("Semantic VAD count is not 3");
    await chooseAll(page, "5");
    await page.getByRole("button", { name: "提交并继续" }).click();
    if (completed === 17) {
      await page.getByRole("button", { name: "开始区块" }).waitFor();
      await page.getByRole("button", { name: "开始区块" }).click();
      const secondCondition = await page.locator(".instruction").textContent();
      await answerComprehension(page, secondCondition.includes("词本身") ? "lexical" : "prototype");
    }
  }
  await page.locator("#attentionValue1").selectOption("3");
  await page.locator("#attentionValue2").selectOption("7");
  await page.getByRole("button", { name: "完成场次" }).click();
  await page.getByText("评分记录：36 条").waitFor();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "导出评分 CSV" }).click();
  const download = await downloadPromise;
  if (download.suggestedFilename() !== "ratings_P001_S1.csv") throw new Error("Unexpected ratings filename");
  await download.saveAs(path.join(outputDir, "ratings_P001_S1.csv"));
  const eventDownloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "导出事件 CSV" }).click();
  const eventDownload = await eventDownloadPromise;
  await eventDownload.saveAs(path.join(outputDir, "events_P001_S1.csv"));
  await page.screenshot({ path: path.join(outputDir, "semantic-complete-desktop.png"), fullPage: true });
  await assertNoHorizontalOverflow(page);
  if (errors.length) throw new Error(`Browser errors: ${errors.join(" | ")}`);
  await page.close();
}

async function runInducedMobile(browser) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true });
  const errors = [];
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.goto(`${baseUrl}/?test=1`);
  await page.locator("#participantId").fill("P002");
  await page.locator("#sessionId").selectOption("S1");
  await page.getByRole("button", { name: "核对并开始" }).click();
  await page.getByRole("button", { name: "继续" }).click();
  await answerComprehension(page, "induced");
  await page.getByRole("button", { name: "模拟视频结束" }).waitFor();
  await page.screenshot({ path: path.join(outputDir, "induced-video-mobile.png"), fullPage: true });
  await page.getByRole("button", { name: "模拟视频结束" }).click();
  await page.locator(".rating-form").waitFor();
  if (await page.locator(".scale-field").count() !== 3) throw new Error("Induced VAD count is not 3");
  await chooseAll(page, "6");
  await page.getByRole("button", { name: "提交并继续" }).click();
  await page.locator(".rating-form").waitFor();
  if (await page.locator(".scale-field").count() !== 10) throw new Error("Induced secondary count is not 10");
  await page.screenshot({ path: path.join(outputDir, "induced-ratings-mobile.png"), fullPage: true });
  await chooseAll(page, "5");
  await page.getByRole("button", { name: "提交并继续" }).click();
  await page.getByText("静息基线").waitFor();
  await assertNoHorizontalOverflow(page);
  if (errors.length) throw new Error(`Browser errors: ${errors.join(" | ")}`);
  await page.close();
}

async function runMissingMedia(browser) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto(`${baseUrl}/?test=1&media=real`);
  await page.locator("#participantId").fill("P002");
  await page.locator("#sessionId").selectOption("S1");
  await page.getByRole("button", { name: "核对并开始" }).click();
  await page.getByRole("button", { name: "继续" }).click();
  await page.locator('input[name="comprehension"][value="lexical"]').check();
  await page.getByRole("button", { name: "确认" }).click();
  await page.getByText("请注意本区块的评分对象").waitFor();
  await page.getByRole("button", { name: "我已理解，继续" }).click();
  await page.getByRole("button", { name: "记录技术失败并跳过" }).waitFor();
  await page.getByRole("button", { name: "记录技术失败并跳过" }).click();
  await page.getByRole("button", { name: "记录技术失败并跳过" }).waitFor();
  await page.close();
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.A2_BROWSER_PATH || undefined,
  });
  try {
    await runSemantic(browser);
    await runInducedMobile(browser);
    await runMissingMedia(browser);
    process.stdout.write("PASS semantic_complete=36 induced_first_trial=complete missing_media=handled desktop_mobile=ok\n");
  } finally {
    await browser.close();
  }
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exit(1);
});
