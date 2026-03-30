import { test, expect } from '@playwright/test'

test.describe('Agent Management', () => {
  test.beforeEach(async ({ page }) => {
    // Dismiss the tutorial overlay so it doesn't block clicks
    await page.addInitScript(() => {
      localStorage.setItem('mirofish-tutorial', JSON.stringify({
        hasSeenWelcome: true,
        completedTours: ['welcome'],
      }))
    })
    await page.goto('/agents')
  })

  test('displays page header and create button', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Agent Management')
    await expect(page.getByText('Create and customize AI simulation agents')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Create New Agent' })).toBeVisible()
  })

  test('displays summary stats', async ({ page }) => {
    // Use exact match to avoid ambiguity with the section filter <option>
    await expect(page.locator('div').filter({ hasText: /^My Agents$/ }).first()).toBeVisible()
    await expect(page.locator('div').filter({ hasText: /^Templates$/ }).first()).toBeVisible()
    await expect(page.locator('div').filter({ hasText: /^Departments$/ }).first()).toBeVisible()
  })

  test('displays template agent cards', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('Sarah Chen')).toBeVisible()
    await expect(page.getByText('Marcus Thompson')).toBeVisible()
    await expect(page.getByText('Priya Patel')).toBeVisible()
    await expect(page.getByText('Alex Kim')).toBeVisible()
    await expect(page.getByText('Diana Okafor')).toBeVisible()
  })

  test('shows template badges on template agents', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })
    const badges = page.locator('text=Template').all()
    expect((await badges).length).toBeGreaterThanOrEqual(6)
  })

  test('shows agent roles and departments', async ({ page }) => {
    await expect(page.getByText('VP of Customer Support')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('CX Director')).toBeVisible()
    await expect(page.getByText('Chief Marketing Officer')).toBeVisible()
  })

  test('search filters agents by name', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    const searchInput = page.getByPlaceholder('Search by name, role, department, or expertise...')
    await searchInput.fill('Diana')

    await expect(page.getByText('Diana Okafor')).toBeVisible()
    await expect(page.getByText('Jordan Rivera')).not.toBeVisible()
  })

  test('search filters agents by role', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    const searchInput = page.getByPlaceholder('Search by name, role, department, or expertise...')
    await searchInput.fill('CFO')

    await expect(page.getByText('Diana Okafor')).toBeVisible()
    await expect(page.getByText('Jordan Rivera')).not.toBeVisible()
  })

  test('shows no-results message when search has no matches', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    const searchInput = page.getByPlaceholder('Search by name, role, department, or expertise...')
    await searchInput.fill('zzz_nonexistent_agent_zzz')

    await expect(page.getByText('No agents match your filters.')).toBeVisible()
    await expect(page.getByText('Clear filters')).toBeVisible()
  })

  test('clear filters button resets search', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    const searchInput = page.getByPlaceholder('Search by name, role, department, or expertise...')
    await searchInput.fill('zzz_nonexistent_agent_zzz')

    await expect(page.getByText('No agents match your filters.')).toBeVisible()
    await page.getByText('Clear filters').click()

    await expect(page.getByText('Jordan Rivera')).toBeVisible()
  })

  test('section filter shows empty state for My Agents when none exist', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    // Select "My Agents" section filter
    const sectionSelect = page.locator('select').first()
    await sectionSelect.selectOption('custom')

    await expect(page.getByText('No custom agents yet')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Browse Templates' })).toBeVisible()
  })

  test('Browse Templates button switches to templates view', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    const sectionSelect = page.locator('select').first()
    await sectionSelect.selectOption('custom')

    await expect(page.getByText('No custom agents yet')).toBeVisible()
    await page.getByRole('button', { name: 'Browse Templates' }).click()

    await expect(page.getByText('Jordan Rivera')).toBeVisible()
  })

  test('cloning a template creates a custom agent', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    // Click the "Use template" link on the first template card
    const useTemplateLinks = page.getByText('Use template')
    await useTemplateLinks.first().click()

    // The cloned agent card heading should appear with "(Copy)" in the name
    await expect(page.getByRole('heading', { name: /\(Copy\)/ })).toBeVisible({ timeout: 5_000 })
  })

  test('Create New Agent button adds an agent', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    const createBtn = page.getByRole('button', { name: 'Create New Agent' })
    await createBtn.click()

    // The "Create New Agent" button clones the first template
    await expect(page.getByRole('heading', { name: /\(Copy\)/ })).toBeVisible({ timeout: 5_000 })
  })

  test('custom agent can be deleted via confirm dialog', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    // First create a custom agent by clicking "Use template"
    await page.getByText('Use template').first().click()
    await expect(page.getByRole('heading', { name: /\(Copy\)/ })).toBeVisible({ timeout: 5_000 })

    // Find and click the delete button (trash icon) on the custom agent card
    const deleteBtn = page.locator('button[title="Delete agent"]').first()
    await deleteBtn.click()

    // Confirm dialog should appear
    const dialog = page.locator('div[role="alertdialog"]')
    await expect(dialog).toBeVisible()
    await expect(dialog.locator('h3')).toContainText('Delete Agent')
    await expect(dialog.getByText('This cannot be undone.')).toBeVisible()

    // Click Delete to confirm
    await dialog.getByRole('button', { name: 'Delete' }).click()

    // Dialog should close
    await expect(dialog).not.toBeVisible()
  })

  test('delete dialog can be cancelled', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    // Create a custom agent
    await page.getByText('Use template').first().click()
    await expect(page.getByRole('heading', { name: /\(Copy\)/ })).toBeVisible({ timeout: 5_000 })

    // Open delete dialog
    await page.locator('button[title="Delete agent"]').first().click()
    const dialog = page.locator('div[role="alertdialog"]')
    await expect(dialog).toBeVisible()

    // Click Cancel
    await dialog.getByRole('button', { name: 'Cancel' }).click()

    // Dialog should close but the agent should still be visible
    await expect(dialog).not.toBeVisible()
    await expect(page.getByRole('heading', { name: /\(Copy\)/ })).toBeVisible()
  })

  test('personality summary displays on cards', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    // Jordan Rivera has assertive=80 and empathetic=70 (both >= 70)
    await expect(page.getByText('Assertive, Empathetic').first()).toBeVisible()
  })

  test('expertise tags display on cards', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    await expect(page.getByText('Customer Retention')).toBeVisible()
    await expect(page.getByText('Team Leadership')).toBeVisible()
  })

  test('communication style displays on cards', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    // Jordan Rivera has communication_style: 'formal'
    const formalLabels = page.getByText('Formal')
    expect((await formalLabels.all()).length).toBeGreaterThanOrEqual(1)
  })

  test('department filter narrows results', async ({ page }) => {
    await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 10_000 })

    // Filter by Finance department (only Diana Okafor is in Finance)
    const deptSelect = page.locator('select').last()
    await deptSelect.selectOption('Finance')

    await expect(page.getByText('Diana Okafor')).toBeVisible()
    await expect(page.getByText('Jordan Rivera')).not.toBeVisible()
    await expect(page.getByText('Sarah Chen')).not.toBeVisible()
  })
})
