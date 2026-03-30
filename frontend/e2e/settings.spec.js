import { test, expect } from '@playwright/test'

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to start fresh
    await page.goto('/settings')
    await page.evaluate(() => localStorage.clear())
    await page.reload()
    await page.waitForLoadState('networkidle')
  })

  // ── Section visibility ──────────────────────────────

  test('displays all settings sections', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
    await expect(page.getByText('LLM Provider')).toBeVisible()
    await expect(page.getByText('Zep Cloud')).toBeVisible()
    await expect(page.getByText('Simulation Defaults')).toBeVisible()
    await expect(page.getByText('Demo Features')).toBeVisible()
  })

  test('displays all LLM provider options', async ({ page }) => {
    await expect(page.getByText('Claude (Anthropic)')).toBeVisible()
    await expect(page.getByText('OpenAI (GPT-4o)')).toBeVisible()
    await expect(page.getByText('Google Gemini')).toBeVisible()
  })

  test('displays all simulation duration options', async ({ page }) => {
    await expect(page.getByRole('button', { name: '24 hours' })).toBeVisible()
    await expect(page.getByRole('button', { name: '48 hours' })).toBeVisible()
    await expect(page.getByRole('button', { name: /72 hours/ })).toBeVisible()
  })

  test('displays platform mode options', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Twitter' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Reddit' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Both' })).toBeVisible()
  })

  // ── LLM provider switching ─────────────────────────

  test('switches LLM provider and shows correct model', async ({ page }) => {
    // Default is Anthropic
    const anthropicRadio = page.locator('input[type="radio"][value="anthropic"]')
    await expect(anthropicRadio).toBeChecked()

    // Switch to OpenAI
    const openaiLabel = page.getByText('OpenAI (GPT-4o)')
    await openaiLabel.click()
    await expect(page.locator('input[type="radio"][value="openai"]')).toBeChecked()
    await expect(page.getByText('gpt-4o')).toBeVisible()

    // Switch to Gemini
    const geminiLabel = page.getByText('Google Gemini')
    await geminiLabel.click()
    await expect(page.locator('input[type="radio"][value="gemini"]')).toBeChecked()
  })

  // ── Simulation defaults interaction ────────────────

  test('changes duration selection', async ({ page }) => {
    // Default is 72 hours
    const dur24 = page.getByRole('button', { name: '24 hours' })
    const dur48 = page.getByRole('button', { name: '48 hours' })

    await dur24.click()
    // Active button gets primary bg + white text
    await expect(dur24).toHaveCSS('color', 'rgb(255, 255, 255)')

    await dur48.click()
    await expect(dur48).toHaveCSS('color', 'rgb(255, 255, 255)')
  })

  test('changes platform mode selection', async ({ page }) => {
    const twitterBtn = page.getByRole('button', { name: 'Twitter' })
    const redditBtn = page.getByRole('button', { name: 'Reddit' })

    await twitterBtn.click()
    await expect(twitterBtn).toHaveCSS('color', 'rgb(255, 255, 255)')

    await redditBtn.click()
    await expect(redditBtn).toHaveCSS('color', 'rgb(255, 255, 255)')
  })

  test('adjusts agent count slider', async ({ page }) => {
    const slider = page.locator('input[type="range"]')
    await expect(slider).toBeVisible()

    // Default value is 200
    await expect(page.getByText('200')).toBeVisible()

    // Drag slider to change value
    await slider.fill('350')
    await expect(page.getByText('350')).toBeVisible()
  })

  // ── Settings persistence via localStorage ──────────

  test('persists settings to localStorage', async ({ page }) => {
    // Switch to OpenAI
    await page.getByText('OpenAI (GPT-4o)').click()

    // Change duration
    await page.getByRole('button', { name: '24 hours' }).click()

    // Change platform
    await page.getByRole('button', { name: 'Reddit' }).click()

    // Verify localStorage was updated
    const saved = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('mirofish-settings'))
    })
    expect(saved.provider).toBe('openai')
    expect(saved.duration).toBe(24)
    expect(saved.platformMode).toBe('reddit')
  })

  test('restores settings after navigation and return', async ({ page }) => {
    // Configure some non-default settings
    await page.getByText('Google Gemini').click()
    await page.getByRole('button', { name: '48 hours' }).click()
    await page.getByRole('button', { name: 'Twitter' }).click()
    await page.locator('input[type="range"]').fill('300')

    // Navigate away
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Navigate back
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')

    // Verify settings restored
    await expect(page.locator('input[type="radio"][value="gemini"]')).toBeChecked()
    await expect(page.getByText('300')).toBeVisible()
  })

  // ── Connection test buttons ────────────────────────

  test('test connection buttons are disabled without API keys', async ({ page }) => {
    const testButtons = page.getByRole('button', { name: 'Test Connection' })
    const count = await testButtons.count()

    // Both LLM and Zep test buttons should be disabled when keys are empty
    for (let i = 0; i < count; i++) {
      await expect(testButtons.nth(i)).toBeDisabled()
    }
  })

  test('LLM test connection button enables when key is entered', async ({ page }) => {
    const llmKeyInput = page.locator('input[type="password"]').first()
    await llmKeyInput.fill('sk-test-key-123')

    // First Test Connection button (LLM) should now be enabled
    const testButtons = page.getByRole('button', { name: 'Test Connection' })
    await expect(testButtons.first()).toBeEnabled()
  })

  test('Zep test connection button enables when key is entered', async ({ page }) => {
    const zepKeyInput = page.locator('input[type="password"]').nth(1)
    await zepKeyInput.fill('zep-test-key-456')

    // Second Test Connection button (Zep) should now be enabled
    const testButtons = page.getByRole('button', { name: 'Test Connection' })
    await expect(testButtons.last()).toBeEnabled()
  })

  // ── Collaboration presence toggle ──────────────────

  test('toggles collaboration presence setting', async ({ page }) => {
    const toggle = page.locator('input[type="checkbox"]')
    // Default is checked (showPresence: true)
    await expect(toggle).toBeChecked()

    // Click the toggle container to uncheck
    await toggle.click({ force: true })
    await expect(toggle).not.toBeChecked()

    // Verify persisted
    const saved = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('mirofish-settings'))
    })
    expect(saved.showPresence).toBe(false)
  })

  // ── Info section ───────────────────────────────────

  test('shows localStorage guidance text', async ({ page }) => {
    await expect(page.getByText('Settings are stored locally in your browser')).toBeVisible()
  })
})
