import { test, expect } from '@playwright/test'

/**
 * E2E test for the report generation flow.
 *
 * Uses Playwright route interception to mock backend API responses,
 * simulating the full lifecycle: check → generate → poll progress → sections.
 */

const TASK_ID = 'demo-sim-00001'
const REPORT_ID = 'demo-report-00001'

const DEMO_SECTIONS = [
  {
    section_index: 0,
    content: `## Executive Summary\n\nThis report presents findings from a 72-hour swarm intelligence simulation involving **200 AI agents**.`,
  },
  {
    section_index: 1,
    content: `## Engagement Analysis\n\n### Engagement by Persona Type\n\nThe simulation reveals dramatic differences.`,
  },
  {
    section_index: 2,
    content: `## Messaging Effectiveness\n\n### Subject Line Performance\n\nAll four subject line variants were tested.`,
  },
  {
    section_index: 3,
    content: `## Behavioral Patterns\n\n### Temporal Engagement Patterns\n\nThe 72-hour simulation revealed distinct behavioral waves.`,
  },
  {
    section_index: 4,
    content: `## Recommendations\n\nBased on the simulation findings, we recommend the following prioritized action items.`,
  },
]

const TEMPLATES = [
  { id: 'exec_summary', name: 'Executive Summary', category: 'leadership', icon: 'briefcase', description: 'High-level overview for leadership' },
  { id: 'full_analysis', name: 'Full GTM Analysis', category: 'comprehensive', icon: 'chart-bar', description: 'Comprehensive multi-chapter analysis' },
]

function ok(data) {
  return {
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data }),
  }
}

/** Dismiss onboarding/tutorial overlays that block pointer events. */
async function dismissTutorials(page) {
  await page.addInitScript(() => {
    localStorage.setItem('mirofish-onboarding-completed', 'true')
    localStorage.setItem('mirofish-tutorial', JSON.stringify({
      hasSeenWelcome: true,
      completedTours: ['welcome'],
    }))
  })
}

/** Mock shared endpoints that are needed regardless of report state. */
async function mockSharedRoutes(page) {
  await page.route('**/report/templates', (route) =>
    route.fulfill(ok(TEMPLATES))
  )
  await page.route('**/report/types', (route) =>
    route.fulfill(ok({
      types: [
        { id: 'executive_summary', description: 'Executive Summary' },
        { id: 'detailed_analysis', description: 'Detailed Analysis' },
      ],
      default: 'executive_summary',
    }))
  )
  await page.route('**/simulation/*/agent-stats', (route) =>
    route.fulfill(ok({
      stats: [
        { agent_id: 0, name: 'Agent Alpha', total_actions: 42, posts: 12, replies: 20, likes: 10 },
        { agent_id: 1, name: 'Agent Beta', total_actions: 38, posts: 10, replies: 18, likes: 10 },
      ],
    }))
  )
  await page.route('**/report/*/agent-log**', (route) =>
    route.fulfill(ok({ logs: [] }))
  )
  await page.route('**/report/*/console-log**', (route) =>
    route.fulfill(ok({ logs: [] }))
  )
  await page.route('**/report/*/tool-calls', (route) =>
    route.fulfill(ok({ tool_calls: [] }))
  )
}

/** Mock routes for a scenario where a completed report already exists. */
async function mockCompletedReport(page) {
  await dismissTutorials(page)
  await mockSharedRoutes(page)

  await page.route('**/report/check/**', (route) =>
    route.fulfill(ok({ has_report: true, report_id: REPORT_ID, report_status: 'completed' }))
  )
  await page.route('**/report/*/sections', (route) =>
    route.fulfill(ok({ sections: DEMO_SECTIONS, is_complete: true }))
  )
  await page.route('**/report/*/progress', (route) =>
    route.fulfill(ok({ progress: 100, total_sections: 5, completed_sections: 5, message: 'Report complete' }))
  )
}

/** Mock routes for the generation flow (no report exists → generate → poll → done). */
async function mockGenerationFlow(page) {
  await dismissTutorials(page)
  await mockSharedRoutes(page)

  let generated = false
  let pollCount = 0

  await page.route('**/report/check/**', (route) =>
    route.fulfill(ok(
      generated
        ? { has_report: true, report_id: REPORT_ID, report_status: 'completed' }
        : { has_report: false, report_id: null, report_status: null }
    ))
  )

  await page.route('**/report/generate', (route) => {
    if (route.request().method() !== 'POST') return route.fallback()
    generated = true
    pollCount = 0
    return route.fulfill(ok({
      simulation_id: TASK_ID,
      report_id: REPORT_ID,
      task_id: null,
      status: 'generating',
      already_generated: false,
    }))
  })

  await page.route('**/report/*/progress', (route) => {
    pollCount++
    const progress = Math.min(100, pollCount * 50)
    return route.fulfill(ok({
      progress,
      total_sections: 5,
      completed_sections: Math.min(5, Math.floor(progress / 20)),
      message: progress >= 100 ? 'Report complete' : 'Generating report...',
    }))
  })

  await page.route('**/report/*/sections', (route) => {
    const isComplete = pollCount >= 2
    const visible = isComplete ? DEMO_SECTIONS : DEMO_SECTIONS.slice(0, Math.min(3, pollCount + 1))
    return route.fulfill(ok({ sections: visible, is_complete: isComplete }))
  })
}

test.describe('Report Generation Flow', () => {
  test('shows template selector when no report exists', async ({ page }) => {
    await mockGenerationFlow(page)
    await page.goto(`/report/${TASK_ID}`)

    // Template selector should appear since no report exists
    await expect(page.locator('text=Report Template')).toBeVisible({ timeout: 10_000 })

    // Templates should be listed (auto-selected "comprehensive" enables the button)
    await expect(page.locator('text=Full GTM Analysis')).toBeVisible({ timeout: 5_000 })

    // Generate Report button should be visible and enabled
    await expect(page.getByRole('button', { name: /generate report/i })).toBeEnabled({ timeout: 5_000 })
  })

  test('generates a report and displays sections progressively', async ({ page }) => {
    await mockGenerationFlow(page)
    await page.goto(`/report/${TASK_ID}`)

    // Wait for template selector to load and auto-select comprehensive template
    await expect(page.locator('text=Full GTM Analysis')).toBeVisible({ timeout: 10_000 })

    // Wait for button to be enabled and click
    const generateBtn = page.getByRole('button', { name: /generate report/i })
    await expect(generateBtn).toBeEnabled({ timeout: 5_000 })
    await generateBtn.click()

    // Should show progress message during generation
    await expect(
      page.locator('text=/Generating|analysis/i').first()
    ).toBeVisible({ timeout: 5_000 })

    // Wait for report sections to appear (use heading to avoid strict mode issues)
    await expect(
      page.getByRole('heading', { name: 'Executive Summary' }).first()
    ).toBeVisible({ timeout: 15_000 })
  })

  test('displays all report sections after generation completes', async ({ page }) => {
    await mockCompletedReport(page)
    await page.goto(`/report/${TASK_ID}`)

    // Wait for sections to load (use heading to target the rendered markdown)
    await expect(
      page.getByRole('heading', { name: 'Executive Summary' }).first()
    ).toBeVisible({ timeout: 10_000 })

    // All chapter titles should appear somewhere on the page (sidebar nav, mobile tabs, or rendered content)
    const sectionTitles = [
      'Executive Summary',
      'Engagement Analysis',
      'Messaging Effectiveness',
      'Behavioral Patterns',
      'Recommendations',
    ]

    for (const title of sectionTitles) {
      await expect(
        page.getByText(title).first()
      ).toBeAttached({ timeout: 5_000 })
    }
  })

  test('navigates between report chapters', async ({ page }) => {
    await mockCompletedReport(page)
    await page.goto(`/report/${TASK_ID}`)

    await expect(
      page.getByRole('heading', { name: 'Executive Summary' }).first()
    ).toBeVisible({ timeout: 10_000 })

    // Click on Engagement Analysis in the chapter nav sidebar
    await page.locator('nav button', { hasText: 'Engagement Analysis' }).click()

    // Content area should now show engagement analysis content
    await expect(
      page.locator('text=/Engagement by Persona|dramatic differences/i').first()
    ).toBeVisible({ timeout: 5_000 })

    // Navigate to Recommendations
    await page.locator('nav button', { hasText: 'Recommendations' }).click()

    await expect(
      page.locator('text=/prioritized action items|Segment-Specific/i').first()
    ).toBeVisible({ timeout: 5_000 })
  })

  test('shows export options for completed report', async ({ page }) => {
    await mockCompletedReport(page)
    await page.goto(`/report/${TASK_ID}`)

    await expect(
      page.getByRole('heading', { name: 'Executive Summary' }).first()
    ).toBeVisible({ timeout: 10_000 })

    // Click the Export button (use first() — there may be a second export button in another component)
    const exportBtn = page.getByRole('button', { name: 'Export' }).first()
    await expect(exportBtn).toBeVisible()
    await exportBtn.click()

    // Export dropdown should show format options
    await expect(page.locator('text=Markdown')).toBeVisible({ timeout: 3_000 })
    await expect(page.locator('text=HTML')).toBeVisible()
    await expect(page.locator('text=PDF')).toBeVisible()
    await expect(page.locator('text=JSON')).toBeVisible()
  })
})
