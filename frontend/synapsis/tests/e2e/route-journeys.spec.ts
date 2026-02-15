import { test, expect } from "@playwright/test";

test("first-run redirects to setup and setup route renders", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/setup$/);
  await expect(page.getByRole("heading", { name: "Welcome" })).toBeVisible();
});

test("all shell routes are reachable", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByRole("region", { name: "Chat" })).toBeVisible();

  await page.goto("/timeline");
  await expect(page.getByRole("heading", { name: "Timeline" })).toBeVisible();

  await page.goto("/graph");
  const graphHeading = page.getByRole("heading", { name: "Knowledge Graph" });
  const graphError = page.getByRole("alert").filter({ hasText: "Graph unavailable" });
  await expect(graphHeading.or(graphError)).toBeVisible();

  await page.goto("/search");
  await expect(page.getByRole("heading", { name: "Search" })).toBeVisible();
});
