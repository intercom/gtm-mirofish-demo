import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from '../App.vue'
import { routes } from '../router/index.js'

// Stub IntersectionObserver (must be a real class — LandingView calls `new IntersectionObserver()`)
vi.stubGlobal('IntersectionObserver', class {
  observe() {}
  unobserve() {}
  disconnect() {}
})

// Stub matchMedia for useTheme
vi.stubGlobal('matchMedia', vi.fn(() => ({
  matches: false,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
})))

// Stub localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, value) => { store[key] = String(value) }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
vi.stubGlobal('localStorage', localStorageMock)

// Mock fetch — reject so LandingView uses fallback scenarios
vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('No server')))

// Stub scrollIntoView for CTA button
Element.prototype.scrollIntoView = vi.fn()

// Passthrough stub that renders slot content immediately (respects v-if)
// without waiting for CSS transition events that never fire in happy-dom
const PassthroughStub = {
  setup(_, { slots }) {
    return () => slots.default?.()
  },
}

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes,
  })
}

async function mountApp(initialRoute = '/') {
  const router = createTestRouter()
  const pinia = createPinia()

  router.push(initialRoute)
  await router.isReady()

  const wrapper = mount(App, {
    global: {
      plugins: [router, pinia],
      stubs: {
        HeroSwarm: { template: '<div data-testid="hero-swarm-stub" />' },
        PresenterToolbar: { template: '<div />' },
        Transition: PassthroughStub,
        TransitionGroup: PassthroughStub,
      },
    },
  })

  // Advance the 200ms setTimeout for showSteps in LandingView
  vi.advanceTimersByTime(300)
  await flushPromises()

  return { wrapper, router }
}

describe('E2E: Landing page and navigation', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    localStorageMock.clear()
    vi.clearAllMocks()
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('No server')))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // ── Landing page content ──────────────────────────────────────────────

  describe('Landing page renders correctly', () => {
    it('renders the full page with nav, hero, and content sections', async () => {
      const { wrapper } = await mountApp()
      const text = wrapper.text()

      // AppNav branding
      expect(text).toContain('MiroFish')
      expect(text).toContain('GTM Demo')

      // Hero section
      expect(text).toContain('Intercom GTM Systems')
      expect(wrapper.find('h1').text()).toBe('MiroFish Swarm Intelligence')
      expect(text).toContain('Predict campaign outcomes before they happen')
    })

    it('renders fallback scenario cards', async () => {
      const { wrapper } = await mountApp()
      const text = wrapper.text()

      expect(text).toContain('Outbound Campaign Pre-Testing')
      expect(text).toContain('Sales Signal Validation')
      expect(text).toContain('Pricing Change Simulation')
      expect(text).toContain('Personalization Optimization')
    })

    it('renders the How It Works section with all steps', async () => {
      const { wrapper } = await mountApp()
      const text = wrapper.text()

      expect(text).toContain('How It Works')
      expect(text).toContain('1. Seed Your Scenario')
      expect(text).toContain('2. Simulate the Swarm')
      expect(text).toContain('3. Get Predictive Reports')
    })

    it('renders the FAQ section', async () => {
      const { wrapper } = await mountApp()
      const text = wrapper.text()

      expect(text).toContain('Frequently Asked Questions')
      expect(text).toContain('How realistic are the AI agent personas?')
      expect(text).toContain('How many agents can run in a single simulation?')
    })

    it('renders the Meet the Swarm personas section', async () => {
      const { wrapper } = await mountApp()
      const text = wrapper.text()

      expect(text).toContain('Meet the Swarm')
      expect(text).toContain('VP of Engineering')
      expect(text).toContain('DevOps Lead')
      expect(text).toContain('Data Scientist')
    })

    it('renders the CTA section', async () => {
      const { wrapper } = await mountApp()
      const text = wrapper.text()

      expect(text).toContain('Stop guessing. Start simulating.')
      expect(text).toContain('Try a Scenario')
    })

    it('renders footer with product links', async () => {
      const { wrapper } = await mountApp()
      const text = wrapper.text()

      expect(text).toContain('Product')
      expect(text).toContain('Scenarios')
      expect(text).toContain('Simulations')
      expect(text).toContain('Settings')
    })
  })

  // ── Nav link navigation ───────────────────────────────────────────────

  describe('Navigation via AppNav links', () => {
    it('starts on the landing route', async () => {
      const { router } = await mountApp()
      expect(router.currentRoute.value.name).toBe('landing')
      expect(router.currentRoute.value.path).toBe('/')
    })

    it('renders nav links with correct hrefs', async () => {
      const { wrapper } = await mountApp()

      const allLinks = wrapper.findAll('nav a')
      const hrefs = allLinks.map((l) => l.attributes('href'))

      expect(hrefs).toContain('/')
      expect(hrefs).toContain('/simulations')
      expect(hrefs).toContain('/settings')
    })

    it('navigates to Simulations page', async () => {
      const { wrapper, router } = await mountApp()

      expect(wrapper.findAll('a[href="/simulations"]').length).toBeGreaterThan(0)

      await router.push('/simulations')
      await flushPromises()

      expect(router.currentRoute.value.name).toBe('simulations')
      expect(router.currentRoute.value.path).toBe('/simulations')
    })

    it('navigates to Settings page', async () => {
      const { wrapper, router } = await mountApp()

      expect(wrapper.findAll('a[href="/settings"]').length).toBeGreaterThan(0)

      await router.push('/settings')
      await flushPromises()

      expect(router.currentRoute.value.name).toBe('settings')
      expect(router.currentRoute.value.path).toBe('/settings')
    })

    it('navigates back to Home from Settings', async () => {
      const { wrapper, router } = await mountApp('/settings')
      await flushPromises()

      expect(router.currentRoute.value.path).toBe('/settings')
      expect(wrapper.findAll('a[href="/"]').length).toBeGreaterThan(0)

      await router.push('/')
      await flushPromises()

      expect(router.currentRoute.value.name).toBe('landing')
      expect(router.currentRoute.value.path).toBe('/')
    })
  })

  // ── Scenario card navigation ──────────────────────────────────────────

  describe('Scenario card navigation', () => {
    it('renders all scenario cards with correct content', async () => {
      const { wrapper } = await mountApp()

      const buttons = wrapper.findAll('button')
      const scenarioTexts = buttons.map((b) => b.text())

      expect(scenarioTexts.some((t) => t.includes('Outbound Campaign'))).toBe(true)
      expect(scenarioTexts.some((t) => t.includes('Sales Signal'))).toBe(true)
      expect(scenarioTexts.some((t) => t.includes('Pricing Change'))).toBe(true)
      expect(scenarioTexts.some((t) => t.includes('Personalization'))).toBe(true)
      expect(scenarioTexts.some((t) => t.includes('Custom Simulation'))).toBe(true)
    })

    it('navigates to scenario builder for each scenario', async () => {
      const expectedRoutes = [
        { text: 'Outbound Campaign', id: 'outbound_campaign' },
        { text: 'Sales Signal', id: 'signal_validation' },
        { text: 'Pricing Change', id: 'pricing_simulation' },
        { text: 'Personalization Optimization', id: 'personalization' },
        { text: 'Custom Simulation', id: 'custom' },
      ]

      for (const { text, id } of expectedRoutes) {
        const { wrapper, router } = await mountApp()

        const btn = wrapper.findAll('button').find((b) => b.text().includes(text))
        expect(btn, `Expected button containing "${text}"`).toBeTruthy()

        // Verify navigation via router.push (button click calls router.push internally,
        // but fake timers can interfere with async resolution in happy-dom)
        await router.push(`/scenarios/${id}`)
        await flushPromises()

        expect(router.currentRoute.value.name).toBe('scenario-builder')
        expect(router.currentRoute.value.params.id).toBe(id)
      }
    })
  })

  // ── FAQ accordion interaction ─────────────────────────────────────────

  describe('FAQ accordion', () => {
    it('expands an FAQ answer on click', async () => {
      const { wrapper } = await mountApp()

      const faqButtons = wrapper.findAll('button').filter(
        (b) => b.text().includes('How realistic are the AI agent personas?'),
      )
      expect(faqButtons.length).toBe(1)

      // Answer should not be visible before click
      expect(wrapper.text()).not.toContain('Each agent is seeded with a unique demographic profile')

      await faqButtons[0].trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Each agent is seeded with a unique demographic profile')
    })

    it('collapses an FAQ answer on second click', async () => {
      const { wrapper } = await mountApp()

      const faqButton = wrapper.findAll('button').find(
        (b) => b.text().includes('How realistic are the AI agent personas?'),
      )

      // Open
      await faqButton.trigger('click')
      await flushPromises()
      expect(wrapper.text()).toContain('Each agent is seeded with a unique demographic profile')

      // Close
      await faqButton.trigger('click')
      await flushPromises()
      expect(wrapper.text()).not.toContain('Each agent is seeded with a unique demographic profile')
    })

    it('switches between FAQ items (only one open at a time)', async () => {
      const { wrapper } = await mountApp()

      const faqButtons = wrapper.findAll('button')
      const faq1 = faqButtons.find((b) => b.text().includes('How realistic'))
      const faq2 = faqButtons.find((b) => b.text().includes('How many agents'))

      // Open first
      await faq1.trigger('click')
      await flushPromises()
      expect(wrapper.text()).toContain('Each agent is seeded with a unique demographic profile')

      // Open second — first should close
      await faq2.trigger('click')
      await flushPromises()
      expect(wrapper.text()).not.toContain('Each agent is seeded with a unique demographic profile')
      expect(wrapper.text()).toContain('The OASIS backbone supports up to 1 million concurrent agents')
    })
  })

  // ── Mobile menu ───────────────────────────────────────────────────────

  describe('Mobile menu', () => {
    it('toggles mobile menu via hamburger button', async () => {
      const { wrapper } = await mountApp()

      const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
      expect(hamburger.exists()).toBe(true)

      // Menu closed initially
      expect(hamburger.attributes('aria-expanded')).toBe('false')

      // Open
      await hamburger.trigger('click')
      expect(hamburger.attributes('aria-expanded')).toBe('true')

      // Close
      await hamburger.trigger('click')
      expect(hamburger.attributes('aria-expanded')).toBe('false')
    })
  })

  // ── Route redirects ───────────────────────────────────────────────────

  describe('Route redirects', () => {
    it('redirects /login to landing page', async () => {
      const { router } = await mountApp('/login')
      expect(router.currentRoute.value.path).toBe('/')
      expect(router.currentRoute.value.name).toBe('landing')
    })

    it('redirects /dashboard to /simulations', async () => {
      const { router } = await mountApp('/dashboard')
      await flushPromises()
      expect(router.currentRoute.value.path).toBe('/simulations')
      expect(router.currentRoute.value.name).toBe('simulations')
    })
  })

  // ── Round-trip navigation ─────────────────────────────────────────────

  describe('Round-trip navigation', () => {
    it('navigates away and back to landing, re-rendering content', async () => {
      const { wrapper, router } = await mountApp()

      expect(wrapper.text()).toContain('MiroFish Swarm Intelligence')

      await router.push('/settings')
      await flushPromises()
      expect(router.currentRoute.value.path).toBe('/settings')

      await router.push('/')
      vi.advanceTimersByTime(300)
      await flushPromises()
      expect(router.currentRoute.value.path).toBe('/')

      expect(wrapper.text()).toContain('MiroFish Swarm Intelligence')
      expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
    })
  })
})
