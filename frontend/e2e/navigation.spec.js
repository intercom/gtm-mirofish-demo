import { test, expect } from '@playwright/test'
import { setupPage } from './helpers.js'

test.describe('Navigation', () => {
  test('navbar contains main links', async ({ page }) => {
    await setupPage(page, '/')

    const nav = page.getByRole('navigation')
    await expect(nav.getByRole('link', { name: 'Home' })).toBeVisible()
    await expect(nav.getByRole('link', { name: 'Simulations' })).toBeVisible()
    await expect(nav.getByRole('link', { name: 'Settings' })).toBeVisible()
  })

  test('navigates to Settings page', async ({ page }) => {
    await setupPage(page, '/')
    await page.getByRole('navigation').getByRole('link', { name: 'Settings' }).click()
    await expect(page).toHaveURL('/settings')
  })

  test('logo links back to home', async ({ page }) => {
    await setupPage(page, '/settings')
    await page.getByRole('navigation').getByRole('link').first().click()
    await expect(page).toHaveURL('/')
  })
})
