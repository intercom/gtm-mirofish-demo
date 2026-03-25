import { test, expect } from '@playwright/test'

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('displays LLM provider options', async ({ page }) => {
    await expect(page.locator('text=Claude (Anthropic)')).toBeVisible()
    await expect(page.locator('text=OpenAI')).toBeVisible()
    await expect(page.locator('text=Google Gemini')).toBeVisible()
  })

  test('displays theme options', async ({ page }) => {
    await expect(page.locator('text=Light')).toBeVisible()
    await expect(page.locator('text=Dark')).toBeVisible()
  })

  test('displays simulation duration options', async ({ page }) => {
    await expect(page.locator('text=72 hours')).toBeVisible()
  })
})
