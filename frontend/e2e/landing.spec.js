import { test, expect } from '@playwright/test'

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('displays hero section with branding', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('MiroFish Swarm Intelligence')
    await expect(page.getByText('Intercom GTM Systems', { exact: true })).toBeVisible()
  })

  test('displays scenario cards', async ({ page }) => {
    // Wait for scenarios to load (API or fallback)
    await expect(page.locator('text=Outbound Campaign')).toBeVisible({ timeout: 10_000 })
  })

  test('navigates to scenario builder on card click', async ({ page }) => {
    await expect(page.locator('text=Outbound Campaign')).toBeVisible({ timeout: 10_000 })
    await page.locator('text=Outbound Campaign').first().click()
    await expect(page).toHaveURL(/\/scenarios\//)
  })

  test('displays how-it-works steps', async ({ page }) => {
    await expect(page.locator('text=Seed Your Scenario')).toBeVisible()
    await expect(page.locator('text=Simulate the Swarm')).toBeVisible()
    await expect(page.locator('text=Get Predictive Reports')).toBeVisible()
  })

  test('displays FAQ section with accordion', async ({ page }) => {
    const faqQuestion = page.locator('text=How realistic are the AI agent personas?')
    await expect(faqQuestion).toBeVisible()

    await faqQuestion.click()
    await expect(page.locator('text=Each agent is seeded with a unique demographic')).toBeVisible()
  })
})
