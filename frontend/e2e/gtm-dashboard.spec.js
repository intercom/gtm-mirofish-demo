import { test, expect } from '@playwright/test'

test.describe('GTM Dashboard Data Display', () => {
  test.beforeEach(async ({ page }) => {
    // Dismiss the tutorial overlay so it doesn't block interactions
    await page.addInitScript(() => {
      localStorage.setItem('mirofish-tutorial', JSON.stringify({
        hasSeenWelcome: true,
        completedTours: ['welcome'],
      }))
    })
    await page.goto('/dashboard')
  })

  test('displays dashboard title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('GTM Dashboard')
  })

  test('displays all 8 KPI cards with correct data', async ({ page }) => {
    const kpis = [
      { label: 'Total ARR', value: '$2.2M' },
      { label: 'MRR Growth', value: '+4.2%' },
      { label: 'Pipeline', value: '$3.1M' },
      { label: 'Win Rate', value: '35%' },
      { label: 'Net Retention', value: '112%' },
      { label: 'Avg Deal Size', value: '$48K' },
      { label: 'Sales Cycle', value: '45d' },
      { label: 'Customers', value: '500' },
    ]

    for (const kpi of kpis) {
      const label = page.getByText(kpi.label, { exact: true })
      await expect(label).toBeVisible()
      // Value is a sibling in the same card container
      const card = label.locator('..')
      await expect(card.getByText(kpi.value, { exact: true })).toBeVisible()
    }
  })

  test('displays date range selector with default "Last 30 days"', async ({ page }) => {
    const select = page.locator('select')
    await expect(select).toBeVisible()
    await expect(select).toHaveValue('last-30d')
  })

  test('date range selector contains all options', async ({ page }) => {
    const options = page.locator('select option')
    await expect(options).toHaveCount(5)
    await expect(options.nth(0)).toHaveText('Last 7 days')
    await expect(options.nth(1)).toHaveText('Last 30 days')
    await expect(options.nth(2)).toHaveText('Last 90 days')
    await expect(options.nth(3)).toHaveText('Last 12 months')
    await expect(options.nth(4)).toHaveText('Year to date')
  })

  test('displays Refresh button', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Refresh', exact: true })).toBeVisible()
  })

  test('displays chart and widget placeholder sections', async ({ page }) => {
    await expect(page.getByText('Revenue & Pipeline Chart')).toBeVisible()
    await expect(page.getByText('Health Scorecard')).toBeVisible()
    await expect(page.getByText('Activity Feed')).toBeVisible()
    await expect(page.getByText('Deal Velocity & Funnel')).toBeVisible()
    await expect(page.getByText('Top Accounts Table')).toBeVisible()
  })

  test('refresh button triggers loading state', async ({ page }) => {
    const header = page.locator('.dashboard-header')
    await header.getByRole('button', { name: 'Refresh', exact: true }).click()
    // The dashboard header shows a blue pulse dot while loading
    const pulse = header.locator('.animate-pulse')
    await expect(pulse).toBeVisible()
    await expect(pulse).toBeHidden({ timeout: 3000 })
  })

  test('changing date range triggers refresh', async ({ page }) => {
    const header = page.locator('.dashboard-header')
    const select = header.locator('select')
    await select.selectOption('last-7d')
    await expect(select).toHaveValue('last-7d')
    // The dashboard header shows a blue pulse dot while loading
    const pulse = header.locator('.animate-pulse')
    await expect(pulse).toBeVisible()
    await expect(pulse).toBeHidden({ timeout: 3000 })
  })
})
