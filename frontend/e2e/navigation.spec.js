import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test.describe('Navbar Structure', () => {
    test('displays main navigation links', async ({ page }) => {
      await page.goto('/')
      const nav = page.locator('nav')
      await expect(nav.locator('text=Home')).toBeVisible()
      await expect(nav.locator('text=Simulations')).toBeVisible()
      await expect(nav.locator('text=Settings')).toBeVisible()
    })

    test('displays app branding in navbar', async ({ page }) => {
      await page.goto('/')
      const nav = page.locator('nav')
      await expect(nav.locator('svg[aria-label="Intercom logo"]')).toBeVisible()
    })

    test('navbar is visible on non-login pages', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('nav')).toBeVisible()

      await page.goto('/settings')
      await expect(page.locator('nav')).toBeVisible()
    })
  })

  test.describe('Page Navigation', () => {
    test('navigates to Settings page', async ({ page }) => {
      await page.goto('/')
      await page.locator('nav').locator('text=Settings').click()
      await expect(page).toHaveURL('/settings')
    })

    test('navigates to Simulations page', async ({ page }) => {
      await page.goto('/')
      await page.locator('nav').locator('text=Simulations').click()
      await expect(page).toHaveURL('/simulations')
    })

    test('logo links back to home', async ({ page }) => {
      await page.goto('/settings')
      await page.locator('nav a[href="/"]').first().click()
      await expect(page).toHaveURL('/')
    })

    test('Home link navigates to landing page', async ({ page }) => {
      await page.goto('/settings')
      await page.locator('nav').locator('text=Home').click()
      await expect(page).toHaveURL('/')
    })
  })

  test.describe('Active Route State', () => {
    test('highlights current route in navbar', async ({ page }) => {
      await page.goto('/settings')
      const settingsLink = page.locator('nav .nav-link', { hasText: 'Settings' })
      await expect(settingsLink).toHaveClass(/router-link-active/)
    })

    test('Home link is active only on landing page', async ({ page }) => {
      await page.goto('/')
      const homeLink = page.locator('nav .nav-link--exact', { hasText: 'Home' })
      await expect(homeLink).toHaveClass(/router-link-exact-active/)

      await page.goto('/settings')
      const homeLinkOnSettings = page.locator('nav .nav-link--exact', { hasText: 'Home' })
      await expect(homeLinkOnSettings).not.toHaveClass(/router-link-exact-active/)
    })
  })

  test.describe('Mobile Menu', () => {
    test.use({ viewport: { width: 375, height: 812 } })

    test('toggle button opens and closes mobile menu', async ({ page }) => {
      await page.goto('/')
      const toggleBtn = page.getByLabel('Toggle navigation menu')
      await expect(toggleBtn).toBeVisible()

      await toggleBtn.click()
      await expect(page.locator('.md\\:hidden >> text=Home')).toBeVisible()
      await expect(page.locator('.md\\:hidden >> text=Simulations')).toBeVisible()
      await expect(page.locator('.md\\:hidden >> text=Settings')).toBeVisible()

      await toggleBtn.click()
      await expect(page.locator('.md\\:hidden >> text=Home')).toBeHidden()
    })

    test('mobile menu closes after navigation', async ({ page }) => {
      await page.goto('/')
      const toggleBtn = page.getByLabel('Toggle navigation menu')
      await toggleBtn.click()

      await page.locator('.md\\:hidden >> text=Settings').click()
      await expect(page).toHaveURL('/settings')

      // Menu should auto-close on route change
      const mobileDropdown = page.locator('.md\\:hidden.absolute')
      await expect(mobileDropdown).toBeHidden()
    })
  })

  test.describe('Help Menu', () => {
    test('opens and displays help options', async ({ page }) => {
      await page.goto('/')
      const helpBtn = page.getByLabel('Help menu')
      await helpBtn.click()

      await expect(page.locator('text=Welcome Tour')).toBeVisible()
      await expect(page.locator('text=Guided Walkthrough')).toBeVisible()
      await expect(page.locator('text=Keyboard Shortcuts')).toBeVisible()
    })

    test('closes when clicking outside', async ({ page }) => {
      await page.goto('/')
      const helpBtn = page.getByLabel('Help menu')
      await helpBtn.click()
      await expect(page.locator('text=Welcome Tour')).toBeVisible()

      // Click outside the help menu
      await page.locator('main').click()
      await expect(page.locator('text=Welcome Tour')).toBeHidden()
    })
  })

  test.describe('Accessibility', () => {
    test('skip-to-main-content link exists', async ({ page }) => {
      await page.goto('/')
      const skipLink = page.locator('a.skip-to-main')
      await expect(skipLink).toBeAttached()
      await expect(skipLink).toHaveAttribute('href', '#main-content')
    })

    test('main content landmark has correct id', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('main#main-content')).toBeAttached()
    })
  })

  test.describe('Redirects', () => {
    test('/login redirects to landing when auth is disabled', async ({ page }) => {
      await page.goto('/login')
      await expect(page).toHaveURL('/')
    })

    test('/network/:taskId redirects to workspace', async ({ page }) => {
      await page.goto('/network/test-123')
      await expect(page).toHaveURL(/\/workspace\/test-123\?tab=network/)
    })
  })
})
