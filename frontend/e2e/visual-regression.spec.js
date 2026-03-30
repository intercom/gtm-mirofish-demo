import { test, expect } from '@playwright/test'

// Pages that render fully without route params or active simulation data.
const staticPages = [
  ['/', 'landing'],
  ['/scenarios', 'scenarios'],
  ['/settings', 'settings'],
  ['/simulations', 'simulations'],
  ['/knowledge-graph', 'knowledge-graph'],
  ['/marketplace', 'marketplace'],
  ['/charts', 'charts-gallery'],
  ['/analytics', 'analytics'],
  ['/visualizations', 'visualizations'],
  ['/api-docs', 'api-docs'],
  ['/agents', 'agents'],
  ['/org-chart', 'org-chart'],
  ['/comparison', 'comparison'],
  ['/dashboard', 'gtm-dashboard'],
  ['/dashboard-builder', 'dashboard-builder'],
  ['/compare', 'compare'],
  ['/permission-denied', 'permission-denied'],
]

test.describe('Visual regression baselines', () => {
  for (const [route, name] of staticPages) {
    test(`${name} page matches baseline`, async ({ page }) => {
      await page.goto(route)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot(`${name}.png`)
    })
  }
})

test.describe('Visual regression — dark mode', () => {
  for (const [route, name] of staticPages) {
    test(`${name} dark mode matches baseline`, async ({ page }) => {
      await page.goto(route)
      await page.waitForLoadState('networkidle')
      await page.evaluate(() => document.documentElement.classList.add('dark'))
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot(`${name}-dark.png`)
    })
  }
})
