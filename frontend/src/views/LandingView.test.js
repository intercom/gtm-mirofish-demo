import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import LandingView from './LandingView.vue'

vi.mock('../components/landing/HeroSwarm.vue', () => ({
  default: { template: '<div class="hero-swarm-stub" />' },
}))

vi.mock('../composables/useDemoMode', () => ({
  useDemoMode: () => ({ isDemoMode: false }),
}))

const SCENARIOS = [
  { id: 'outbound_campaign', name: 'Outbound Campaign Pre-Testing', description: 'Test outbound emails.', icon: '📧', hero: true },
  { id: 'signal_validation', name: 'Sales Signal Validation', description: 'Validate signals.', icon: '📡' },
  { id: 'pricing_simulation', name: 'Pricing Change Simulation', description: 'Predict pricing reactions.', icon: '💰' },
  { id: 'personalization', name: 'Personalization Optimization', description: 'Rank email variants.', icon: '✨' },
]

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: LandingView },
      { path: '/scenarios/:id', component: { template: '<div />' } },
      { path: '/simulations', component: { template: '<div />' } },
      { path: '/settings', component: { template: '<div />' } },
    ],
  })
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(SCENARIOS) }),
  ))
  vi.stubGlobal('IntersectionObserver', class {
    observe() {}
    disconnect() {}
    unobserve() {}
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('LandingView', () => {
  it('renders hero section with title', async () => {
    const router = createTestRouter()
    const wrapper = mount(LandingView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.text()).toContain('MiroFish Swarm Intelligence')
  })

  it('renders scenario cards after fetch', async () => {
    const router = createTestRouter()
    const wrapper = mount(LandingView, { global: { plugins: [router] } })
    await flushPromises()
    const scenarioButtons = wrapper.findAll('button[data-index]')
    expect(scenarioButtons.length).toBe(5)
    expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
  })

  it('provides stagger hooks for card animation', async () => {
    const router = createTestRouter()
    const wrapper = mount(LandingView, { global: { plugins: [router] } })
    await flushPromises()
    const buttons = wrapper.findAll('button[data-index]')
    expect(buttons.length).toBe(5)
    expect(buttons[0].attributes('data-index')).toBe('0')
    expect(buttons[3].attributes('data-index')).toBe('3')
  })

  it('renders how-it-works steps', async () => {
    vi.useFakeTimers()
    const router = createTestRouter()
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(SCENARIOS) }),
    ))
    const wrapper = mount(LandingView, { global: { plugins: [router] } })
    await flushPromises()

    vi.advanceTimersByTime(300)
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Seed Your Scenario')
    expect(wrapper.text()).toContain('Simulate the Swarm')
    expect(wrapper.text()).toContain('Get Predictive Reports')
    vi.useRealTimers()
  })
})
