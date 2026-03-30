import { test, expect } from '@playwright/test'
import { suppressViteOverlay, dismissTour } from './helpers.js'

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await suppressViteOverlay(page)
    await page.goto('/')
    await dismissTour(page)
  })

  test('displays hero section with branding', async ({ page }) => {
    await expect(page.getByRole('heading', { level: 1 })).toContainText('MiroFish Swarm Intelligence')
    await expect(page.getByText('Intercom GTM Systems', { exact: true })).toBeVisible()
  })

  test('displays how-it-works steps', async ({ page }) => {
    await expect(page.getByText('Seed Your Scenario')).toBeVisible()
    await expect(page.getByText('Simulate the Swarm')).toBeVisible()
    await expect(page.getByText('Get Predictive Reports')).toBeVisible()
  })

  test('displays FAQ section with accordion @smoke', async ({ page }) => {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    const faqQuestion = page.getByText('How realistic are the AI agent personas?')
    await expect(faqQuestion).toBeVisible({ timeout: 10_000 })

    await faqQuestion.click()
    await expect(page.getByText('Each agent is seeded with a unique demographic')).toBeVisible()
  })
})
