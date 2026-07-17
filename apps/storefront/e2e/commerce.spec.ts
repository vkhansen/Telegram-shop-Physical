/**
 * Browser e2e — web storefront commerce parity with Telegram flows:
 *   C-06 browse → C-08 cart → C-12 delivery → C-13 cash → C-17 orders
 *
 * Uses real public API when available (snus-demo seed).
 * Skips gracefully if API/storefront are not reachable.
 */
import { test, expect, type Page, type APIRequestContext } from "@playwright/test";

const API = (process.env.PUBLIC_API_BASE || "http://127.0.0.1:9090").replace(/\/$/, "");
const BRAND = process.env.E2E_BRAND || "snus-demo";

async function apiUp(request: APIRequestContext): Promise<boolean> {
  try {
    const res = await request.get(`${API}/api/public/brands/${BRAND}?channel=web`, {
      timeout: 5000,
    });
    return res.ok();
  } catch {
    return false;
  }
}

async function resolveStoreItem(request: APIRequestContext): Promise<{
  store: string;
  item: string;
  name: string;
} | null> {
  const brand = await request.get(`${API}/api/public/brands/${BRAND}?channel=web`);
  if (!brand.ok()) return null;
  const b = await brand.json();
  const store = b.stores?.[0]?.slug;
  if (!store) return null;
  const menu = await request.get(`${API}/api/public/brands/${BRAND}/stores/${store}`);
  if (!menu.ok()) return null;
  const m = await menu.json();
  for (const cat of m.categories || []) {
    for (const it of cat.items || []) {
      if (it.available && it.cta === "order") {
        return { store, item: it.slug, name: it.name };
      }
    }
  }
  // any order CTA (may still show add when stock edge)
  for (const cat of m.categories || []) {
    for (const it of cat.items || []) {
      if (it.cta === "order") {
        return { store, item: it.slug, name: it.name };
      }
    }
  }
  return null;
}

async function safeGoto(page: Page, path: string) {
  try {
    await page.goto(path, { waitUntil: "domcontentloaded", timeout: 30_000 });
  } catch (e) {
    const msg = String(e);
    // Mid-navigation race after login redirect is common; page often still loads.
    if (!msg.includes("ERR_ABORTED") && !msg.includes("interrupted")) throw e;
  }
}

/** Age gate uses cookie age_ok_{slug} (SSR) + localStorage backup. */
async function passAgeGate(page: Page) {
  const base = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:4321";
  await page.context().addCookies([
    {
      name: `age_ok_${BRAND}`,
      value: "1",
      url: base.endsWith("/") ? base : `${base}/`,
    },
  ]);
  await page.addInitScript((slug) => {
    try {
      localStorage.setItem(`age_ok_${slug}`, "1");
      sessionStorage.setItem(`age_ok_${slug}`, "1");
    } catch {
      /* ignore */
    }
  }, BRAND);
  // If gate still rendered, click through
  const confirm = page.locator("#age-confirm");
  if (await confirm.count()) {
    try {
      if (await confirm.isVisible({ timeout: 500 })) {
        await confirm.click();
      }
    } catch {
      /* already dismissed */
    }
  }
}

async function devLogin(page: Page, email: string) {
  await passAgeGate(page);
  await safeGoto(page, `/${BRAND}/login?next=/${BRAND}/cart`);
  await passAgeGate(page);
  // Dev login box appears when OAUTH_DEV_LOGIN is on
  const devBox = page.locator("#dev-box");
  await expect(devBox).toBeVisible({ timeout: 15_000 });
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="name"]', "E2E Shopper");
  await Promise.all([
    page.waitForURL((u) => u.pathname.includes(`/${BRAND}/`) && !u.pathname.includes("/login"), {
      timeout: 15_000,
    }),
    page.locator("#dev-submit").click(),
  ]);
  // Settle after redirect
  await page.waitForLoadState("domcontentloaded");
}

test.describe("storefront commerce spine (TG parity)", () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await apiUp(request))) {
      testInfo.skip(true, `API not reachable at ${API} — start: python scripts/run_public_api.py`);
    }
  });

  test("catalog brand page loads", async ({ page }) => {
    await passAgeGate(page);
    const res = await page.goto(`/${BRAND}`);
    expect(res?.ok() || res?.status() === 304).toBeTruthy();
    await passAgeGate(page);
    await expect(page.locator("body")).toBeVisible();
  });

  test("item → add to cart → checkout cash → order detail", async ({ page, request }) => {
    const pick = await resolveStoreItem(request);
    test.skip(!pick, "No orderable item in demo catalog");

    const email = `e2e-shop-${Date.now()}@example.com`;

    // Sign in first (cart requires session — same as TG identity edge)
    await devLogin(page, email);

    // C-06 item detail
    await safeGoto(page, `/${BRAND}/${pick!.store}/i/${pick!.item}`);
    await passAgeGate(page);
    await expect(page.getByTestId("item-name")).toBeVisible({ timeout: 15_000 });

    const addBtn = page.getByTestId("add-to-cart");
    // Portfolio brands may only show inquire
    if (!(await addBtn.count())) {
      test.skip(true, "Add to cart not shown (commerce_mode / cta may be inquire-only or sold out)");
    }

    // C-08 add
    await addBtn.click();
    await expect(page.getByTestId("add-cart-msg")).toBeVisible({ timeout: 10_000 });

    // Cart
    await safeGoto(page, `/${BRAND}/cart`);
    await passAgeGate(page);
    await expect(page.getByTestId("cart-list")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("cart-footer")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("cart-checkout")).toBeVisible();

    // C-11/C-12/C-13 checkout
    await page.getByTestId("cart-checkout").click();
    await expect(page.getByTestId("checkout-form")).toBeVisible({ timeout: 10_000 });
    await page.getByTestId("checkout-phone").fill("+66819998877");
    await page.getByTestId("checkout-address").fill("99 E2E Test Soi, Bangkok 10110");
    await page.getByTestId("checkout-note").fill("Playwright order");
    await page.getByTestId("delivery-door").check();
    const cash = page.getByTestId("pay-cash");
    if (await cash.count()) await cash.check();
    await page.getByTestId("checkout-submit").click();

    await expect(page.getByTestId("checkout-success")).toBeVisible({ timeout: 20_000 });
    const codeEl = page.getByTestId("order-code");
    await expect(codeEl).toBeVisible();
    const code = (await codeEl.textContent())?.trim();
    expect(code && code.length >= 4).toBeTruthy();

    // C-17 detail
    await page.getByTestId("view-order").click();
    await expect(page.getByTestId("order-detail")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("detail-code")).toContainText(code!);

    // Orders list includes code
    await safeGoto(page, `/${BRAND}/orders`);
    await passAgeGate(page);
    await expect(page.getByTestId("order-list")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator(`[data-testid=order-row]:has-text("${code}")`)).toBeVisible();
  });

  test("unauthenticated cart redirects to login", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto(`/${BRAND}/cart`);
    // Either login redirect or "sign in" empty state
    await page.waitForTimeout(1500);
    const url = page.url();
    const body = await page.locator("body").innerText();
    const ok =
      url.includes("/login") ||
      body.toLowerCase().includes("sign in") ||
      body.toLowerCase().includes("not signed");
    expect(ok).toBeTruthy();
  });
});
