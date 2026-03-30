import { test, expect } from '@playwright/test'

test.describe('Data Views Load Correctly', () => {
  test('Scenarios view displays heading and category filters', async ({ page }) => {
    await page.goto('/scenarios')

    await expect(page.locator('h1')).toContainText('GTM Scenarios')
    await expect(page.locator('text=Pre-built simulation templates')).toBeVisible()
    await expect(page.locator('text=Custom Simulation')).toBeVisible()
  })

  test('Scenario Marketplace loads with search and categories', async ({ page }) => {
    await page.goto('/marketplace')

    await expect(page.locator('h1')).toContainText('Scenario Marketplace')
    // Category filters should render
    await expect(page.locator('text=All Scenarios')).toBeVisible({ timeout: 10_000 })
  })

  test('Analytics view displays section headers', async ({ page }) => {
    await page.goto('/analytics')

    await expect(page.locator('h1')).toContainText('Analytics')
    await expect(page.locator('text=Cohort trends, attribution, and segment insights')).toBeVisible()
  })

  test('GTM Dashboard displays KPI cards', async ({ page }) => {
    await page.goto('/dashboard')

    await expect(page.locator('h1')).toContainText('GTM Dashboard')
    // Verify KPI cards render with their values
    await expect(page.locator('text=Total ARR')).toBeVisible()
    await expect(page.locator('text=Pipeline')).toBeVisible()
    await expect(page.locator('text=Win Rate')).toBeVisible()
    await expect(page.locator('text=Net Retention')).toBeVisible()
  })

  test('Charts Gallery renders chart sections', async ({ page }) => {
    await page.goto('/charts')

    // Chart section headings from chartSections array
    await expect(page.locator('text=Radar Chart')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('text=Chord Diagram')).toBeVisible()
    await expect(page.locator('text=Sunburst Chart')).toBeVisible()
  })

  test('Agent Management view loads with filters', async ({ page }) => {
    await page.goto('/agents')

    await expect(page.locator('h1')).toContainText('Agent Management')
    // Section filter options
    await expect(page.locator('text=All Agents')).toBeVisible()
  })

  test('Comparison view loads with heading', async ({ page }) => {
    await page.goto('/comparison')

    await expect(page.locator('h1')).toContainText('Comparison')
  })

  test('Scenario Comparison matrix loads', async ({ page }) => {
    await page.goto('/compare')

    await expect(page.locator('h2')).toContainText('Scenario Comparison')
  })

  test('Visualizations view renders cards', async ({ page }) => {
    await page.goto('/visualizations')

    await expect(page.locator('h1')).toContainText('Animated Visualizations')
    await expect(page.locator('text=Agent Network')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('text=Engagement Waves')).toBeVisible()
    await expect(page.locator('text=Conversion Funnel')).toBeVisible()
  })

  test('API Docs view renders endpoint sidebar', async ({ page }) => {
    await page.goto('/api-docs')

    // Sidebar categories
    await expect(page.locator('text=Search endpoints')).toBeVisible()
    await expect(page.locator('text=Health')).toBeVisible()
    await expect(page.locator('text=Scenarios')).toBeVisible()
    await expect(page.locator('text=Simulation')).toBeVisible()
  })

  test('Simulations dashboard loads', async ({ page }) => {
    await page.goto('/simulations')

    await expect(page.locator('h1')).toContainText('Dashboard')
  })

  test('Org Chart view loads', async ({ page }) => {
    await page.goto('/org-chart')

    // The OrgInfoFlow component renders an SVG-based D3 visualization
    await expect(page.locator('.org-chart-view')).toBeVisible()
  })
})
