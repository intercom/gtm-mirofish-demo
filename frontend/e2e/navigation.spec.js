import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('navbar contains main links', async ({ page }) => {
    await page.goto('/')

    const nav = page.locator('nav')
    await expect(nav.locator('text=Home')).toBeVisible()
    await expect(nav.locator('text=Simulations')).toBeVisible()
    await expect(nav.locator('text=Settings')).toBeVisible()
  })

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

  test('/login redirects to landing', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveURL('/')
  })

  test('/dashboard redirects to /simulations', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/simulations')
  })
})
