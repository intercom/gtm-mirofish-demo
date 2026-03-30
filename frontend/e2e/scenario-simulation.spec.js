import { test, expect } from '@playwright/test'

const MOCK_SCENARIO = {
  id: 'outbound_campaign',
  name: 'Outbound Campaign Pre-Testing',
  description: 'Simulate how AI-generated outbound emails land with synthetic prospect populations.',
  category: 'outbound',
  icon: 'mail',
  seed_text: 'Intercom is launching an automated outbound campaign targeting mid-market companies.',
  agent_config: {
    count: 200,
    persona_types: ['VP of Support', 'CX Director', 'IT Leader', 'Head of Operations'],
    firmographic_mix: {
      industries: ['SaaS', 'Healthcare', 'Fintech', 'E-commerce'],
      company_sizes: ['200-500', '500-1000', '1000-2000'],
      regions: ['North America', 'EMEA', 'APAC'],
    },
  },
  simulation_config: {
    total_hours: 72,
    minutes_per_round: 30,
    platform_mode: 'parallel',
  },
  expected_outputs: ['Engagement prediction by persona type'],
}

const MOCK_SCENARIOS_LIST = {
  scenarios: [
    {
      id: 'outbound_campaign',
      name: 'Outbound Campaign Pre-Testing',
      description: 'Simulate outbound emails with synthetic prospects.',
      category: 'outbound',
      icon: 'mail',
    },
  ],
}

async function setupApiMocks(page) {
  // Catch-all FIRST — Playwright matches routes in LIFO order,
  // so registering this first means it's matched last (lowest priority).
  await page.route('**/api/v1/**', (route) => {
    route.fulfill({ json: { success: true, data: {} } })
  })

  await page.route('**/api/v1/gtm/scenarios', (route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({ json: MOCK_SCENARIOS_LIST })
    } else {
      route.continue()
    }
  })

  await page.route('**/api/v1/gtm/scenarios/outbound_campaign', (route) => {
    route.fulfill({ json: MOCK_SCENARIO })
  })

  await page.route('**/api/v1/gtm/simulate', (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        json: { task_id: 'test-task-123', project_id: 'test-project-456' },
      })
    } else {
      route.continue()
    }
  })

  await page.route('**/api/v1/graph/task/test-task-123', (route) => {
    route.fulfill({
      json: { success: true, data: { id: 'test-task-123', status: 'building', progress: 30 } },
    })
  })

  await page.route('**/api/v1/simulation/test-task-123/run-status', (route) => {
    route.fulfill({
      json: { success: true, data: { status: 'idle', progress: 0 } },
    })
  })

  await page.route('**/api/v1/batch', (route) => {
    route.fulfill({ json: { success: true, results: [] } })
  })
}

/** Navigate and suppress overlays that block interactions in dev mode */
async function gotoAndSuppress(page, url) {
  await page.goto(url)
  // Suppress Vite error overlays (from pre-existing build issues in other views)
  // and onboarding tutorial backdrops that intercept pointer events.
  await page.evaluate(() => {
    const style = document.createElement('style')
    style.textContent =
      'vite-error-overlay,.tutorial-overlay,.tutorial-backdrop{display:none!important;pointer-events:none!important}'
    document.head.appendChild(style)
  })
}

/** Wait for the scenario builder to finish loading */
async function waitForBuilder(page) {
  await expect(page.locator('h1')).toContainText('Outbound Campaign', { timeout: 10_000 })
}

test.describe('Scenario Creation & Simulation Launch', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await setupApiMocks(page)
  })

  test('loads scenario builder with pre-filled form', async ({ page }) => {
    await gotoAndSuppress(page, '/scenarios/outbound_campaign')
    await waitForBuilder(page)

    // Seed text populated
    await expect(page.locator('text=Intercom is launching an automated outbound')).toBeVisible()

    // Persona buttons rendered
    await expect(page.locator('button', { hasText: 'VP of Support' })).toBeVisible()
    await expect(page.locator('button', { hasText: 'CX Director' })).toBeVisible()
    await expect(page.locator('button', { hasText: 'IT Leader' })).toBeVisible()

    // Industry checkboxes rendered (use label selector to avoid seed text matches)
    await expect(page.locator('label', { hasText: 'SaaS' })).toBeVisible()
    await expect(page.locator('label', { hasText: 'Healthcare' })).toBeVisible()

    // Duration buttons present
    await expect(page.locator('button', { hasText: '24h' })).toBeVisible()
    await expect(page.locator('button', { hasText: '72h' })).toBeVisible()

    // Agent count slider is present
    await expect(page.locator('input[type="range"]').first()).toBeVisible()
  })

  test('allows toggling persona and industry selections', async ({ page }) => {
    await gotoAndSuppress(page, '/scenarios/outbound_campaign')
    await waitForBuilder(page)

    // Toggle persona off
    const vpButton = page.locator('button', { hasText: 'VP of Support' })
    await vpButton.click()

    // Toggle industry checkbox
    const saasCheckbox = page.locator('label', { hasText: 'SaaS' }).locator('input[type="checkbox"]')
    await saasCheckbox.click()
  })

  test('changes duration selection', async ({ page }) => {
    await gotoAndSuppress(page, '/scenarios/outbound_campaign')
    await waitForBuilder(page)

    const btn24 = page.locator('button', { hasText: '24h' })
    await btn24.click()

    // Active button gets primary background
    await expect(btn24).toHaveClass(/bg-\[var\(--color-primary\)\]/)
  })

  test('run button is disabled when no personas selected', async ({ page }) => {
    await gotoAndSuppress(page, '/scenarios/outbound_campaign')
    await waitForBuilder(page)

    // Deselect all personas
    for (const persona of MOCK_SCENARIO.agent_config.persona_types) {
      await page.locator('button', { hasText: persona }).click()
    }

    const runButton = page.locator('button', { hasText: 'Run Simulation' })
    await expect(runButton).toBeDisabled()
  })

  test('launches simulation and navigates to workspace', async ({ page }) => {
    let simulatePayload = null

    // Override simulate endpoint to capture payload
    await page.route('**/api/v1/gtm/simulate', (route) => {
      if (route.request().method() === 'POST') {
        simulatePayload = route.request().postDataJSON()
        route.fulfill({
          json: { task_id: 'test-task-123', project_id: 'test-project-456' },
        })
      } else {
        route.continue()
      }
    })

    await gotoAndSuppress(page, '/scenarios/outbound_campaign')
    await waitForBuilder(page)

    const runButton = page.locator('button', { hasText: 'Run Simulation' })
    await expect(runButton).toBeEnabled({ timeout: 5_000 })
    await runButton.click()

    // Should navigate to workspace
    await expect(page).toHaveURL(/\/workspace\/test-task-123/, { timeout: 10_000 })

    // Verify API payload
    expect(simulatePayload).toBeTruthy()
    expect(simulatePayload.seed_text).toContain('Intercom is launching')
    expect(simulatePayload.agent_count).toBe(200)
    expect(simulatePayload.persona_types).toEqual(
      expect.arrayContaining(['VP of Support', 'CX Director']),
    )
  })

  test('workspace loads after simulation launch', async ({ page }) => {
    await gotoAndSuppress(page, '/scenarios/outbound_campaign')
    await waitForBuilder(page)

    // Launch simulation
    const runButton = page.locator('button', { hasText: 'Run Simulation' })
    await expect(runButton).toBeEnabled({ timeout: 5_000 })
    await runButton.click()

    // Should navigate to workspace
    await expect(page).toHaveURL(/\/workspace\/test-task-123/, { timeout: 10_000 })

    // Workspace should render with the graph building phase
    await expect(page.locator('text=Building')).toBeVisible({ timeout: 10_000 })
  })

  test('shows error when simulation launch fails', async ({ page }) => {
    // Override simulate to return 500
    await page.route('**/api/v1/gtm/simulate', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 500,
          json: { success: false, error: 'LLM service unavailable' },
        })
      } else {
        route.continue()
      }
    })

    await gotoAndSuppress(page, '/scenarios/outbound_campaign')
    await waitForBuilder(page)

    const runButton = page.locator('button', { hasText: 'Run Simulation' })
    await expect(runButton).toBeEnabled({ timeout: 5_000 })
    await runButton.click()

    // Should stay on builder
    await expect(page).toHaveURL(/\/scenarios\/outbound_campaign/)

    // Error message visible (appears both inline and in toast — check either)
    await expect(
      page.locator('text=Failed to start simulation: LLM service unavailable'),
    ).toBeVisible({ timeout: 5_000 })
  })

  test('custom scenario starts empty and can be configured', async ({ page }) => {
    await gotoAndSuppress(page, '/scenarios/custom')

    await expect(page.locator('h1')).toContainText('Custom Simulation', { timeout: 10_000 })
  

    // Template selector visible for custom scenarios
    await expect(page.locator('text=Start from a template')).toBeVisible()

    // Run button disabled without seed text and personas
    const runButton = page.locator('button', { hasText: 'Run Simulation' })
    await expect(runButton).toBeDisabled()

    // Apply a template
    await page.locator('button', { hasText: 'Competitive Displacement Campaign' }).click()

    // Seed text populated from template
    await expect(page.locator('text=Why leading support teams are switching')).toBeVisible({
      timeout: 5_000,
    })
  })
})
