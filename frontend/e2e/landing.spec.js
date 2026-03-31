import { test, expect } from '@playwright/test'
import { suppressViteOverlay, dismissTour } from './helpers.js'

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await suppressViteOverlay(page)
    await page.goto('/')
    await dismissTour(page)
  })

  test.describe('Hero Section', () => {
    test('displays hero heading and tagline', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('MiroFish Swarm Intelligence')
      await expect(page.getByText('Intercom GTM Systems', { exact: true })).toBeVisible()
    })

    test('renders HeroSwarm canvas animation', async ({ page }) => {
      const canvas = page.locator('section').first().locator('canvas')
      await expect(canvas).toBeAttached()
    })
  })

  test.describe('Scenario Gallery', () => {
    test('displays scenario cards', async ({ page }) => {
      await expect(page.locator('text=Outbound Campaign')).toBeVisible({ timeout: 10_000 })
    })

    test('navigates to scenario builder on card click', async ({ page }) => {
      await expect(page.locator('text=Outbound Campaign')).toBeVisible({ timeout: 10_000 })
      await page.locator('text=Outbound Campaign').first().click()
      await expect(page).toHaveURL(/\/scenarios\//)
    })

    test('shows multiple scenario options', async ({ page }) => {
      await expect(page.locator('text=Outbound Campaign')).toBeVisible({ timeout: 10_000 })
      await expect(page.locator('text=Sales Signal Validation')).toBeVisible()
      await expect(page.locator('text=Pricing Change Simulation')).toBeVisible()
    })
  })

  test.describe('Social Proof Bar', () => {
    test('displays audience role badges', async ({ page }) => {
      const proofBar = page.locator('text=Sales Development').first()
      await proofBar.scrollIntoViewIfNeeded()
      await expect(proofBar).toBeVisible()
      await expect(page.locator('text=Product Marketing').first()).toBeVisible()
      await expect(page.locator('text=Revenue Operations').first()).toBeVisible()
      await expect(page.locator('text=Growth & Demand Gen').first()).toBeVisible()
      await expect(page.locator('text=Pricing & Packaging')).toBeVisible()
    })
  })

  test.describe('How It Works', () => {
    test('displays three-step process', async ({ page }) => {
      await expect(page.locator('text=Seed Your Scenario')).toBeVisible()
      await expect(page.locator('text=Simulate the Swarm')).toBeVisible()
      await expect(page.locator('text=Get Predictive Reports')).toBeVisible()
    })
  })

  test.describe('Stats Banner', () => {
    test('displays stat labels', async ({ page }) => {
      const statsBanner = page.locator('[data-tour="stats"]')
      await statsBanner.scrollIntoViewIfNeeded()
      await expect(statsBanner).toBeVisible()
      await expect(statsBanner.locator('text=Max Agents')).toBeVisible()
      await expect(statsBanner.locator('text=Action Types')).toBeVisible()
      await expect(statsBanner.locator('text=Analysis Tools')).toBeVisible()
      await expect(statsBanner.locator('text=Platforms')).toBeVisible()
    })
  })

  test.describe('Agent Personas', () => {
    test('displays persona cards with roles', async ({ page }) => {
      const personaSection = page.locator('text=VP of Engineering').first()
      await personaSection.scrollIntoViewIfNeeded()
      await expect(personaSection).toBeVisible()
      await expect(page.locator('text=DevOps Lead')).toBeVisible()
      await expect(page.locator('text=Data Scientist')).toBeVisible()
      await expect(page.locator('text=Head of CS')).toBeVisible()
      await expect(page.locator('text=CTO')).toBeVisible()
      await expect(page.locator('text=Product Manager')).toBeVisible()
    })

    test('shows company context for personas', async ({ page }) => {
      const persona = page.locator('text=Series B SaaS')
      await persona.scrollIntoViewIfNeeded()
      await expect(persona).toBeVisible()
      await expect(page.locator('text=Enterprise Fintech')).toBeVisible()
    })
  })

  test.describe('Before/After Comparison', () => {
    test('displays both comparison panels', async ({ page }) => {
      const traditional = page.locator('text=Traditional A/B Testing')
      await traditional.scrollIntoViewIfNeeded()
      await expect(traditional).toBeVisible()
      await expect(page.locator('text=MiroFish Swarm Simulation')).toBeVisible()
    })

    test('lists drawbacks and benefits', async ({ page }) => {
      const drawback = page.locator('text=Weeks to reach statistical significance')
      await drawback.scrollIntoViewIfNeeded()
      await expect(drawback).toBeVisible()
      await expect(page.locator('text=Results in minutes, not weeks')).toBeVisible()
    })
  })

  test.describe('Simulation Pipeline', () => {
    test('displays pipeline stages', async ({ page }) => {
      const pipeline = page.locator('text=The Simulation Pipeline')
      await pipeline.scrollIntoViewIfNeeded()
      await expect(pipeline).toBeVisible()
      await expect(page.locator('text=Seed Document')).toBeVisible()
      await expect(page.locator('text=Persona Generation')).toBeVisible()
      await expect(page.locator('text=Swarm Simulation').first()).toBeVisible()
      await expect(page.locator('text=Graph Analysis')).toBeVisible()
      await expect(page.locator('text=Predictive Report')).toBeVisible()
    })
  })

  test.describe('FAQ Accordion', () => {
    test('expands FAQ answer on click', async ({ page }) => {
      const question = page.locator('text=How realistic are the AI agent personas?')
      await question.scrollIntoViewIfNeeded()
      await question.click()
      await expect(page.locator('text=Each agent is seeded with a unique demographic')).toBeVisible()
    })

    test('collapses open FAQ when clicking it again', async ({ page }) => {
      const question = page.locator('text=How realistic are the AI agent personas?')
      await question.scrollIntoViewIfNeeded()

      await question.click()
      await expect(page.locator('text=Each agent is seeded with a unique demographic')).toBeVisible()

      await question.click()
      await expect(page.locator('text=Each agent is seeded with a unique demographic')).toBeHidden()
    })

    test('only one FAQ is open at a time', async ({ page }) => {
      const firstQ = page.locator('text=How realistic are the AI agent personas?')
      const secondQ = page.locator('text=How many agents can run in a single simulation?')
      await firstQ.scrollIntoViewIfNeeded()

      await firstQ.click()
      await expect(page.locator('text=Each agent is seeded with a unique demographic')).toBeVisible()

      await secondQ.click()
      await expect(page.locator('text=The OASIS backbone supports up to 1 million')).toBeVisible()
      await expect(page.locator('text=Each agent is seeded with a unique demographic')).toBeHidden()
    })
  })
})
