import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LandingView from '../LandingView.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

vi.mock('../../components/landing/HeroSwarm.vue', () => ({
  default: { template: '<div class="hero-swarm-stub" />' },
}))

vi.mock('../../composables/useDemoMode', () => ({
  useDemoMode: () => ({ isDemoMode: false }),
}))

beforeEach(() => {
  vi.clearAllMocks()
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('No server')))
  vi.stubGlobal('IntersectionObserver', class {
    observe() {}
    disconnect() {}
    unobserve() {}
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

async function mountLanding() {
  const wrapper = mount(LandingView, {
    global: {
      stubs: { 'router-link': { template: '<a><slot /></a>' } },
    },
  })
  await flushPromises()
  return wrapper
}

describe('LandingView', () => {
  it('renders the Intercom GTM Systems branding', async () => {
    const wrapper = await mountLanding()
    expect(wrapper.text()).toContain('Intercom GTM Systems')
  })

  it('renders the MiroFish Swarm Intelligence headline', async () => {
    const wrapper = await mountLanding()
    const h1 = wrapper.find('h1')
    expect(h1.text()).toBe('MiroFish Swarm Intelligence')
  })

  it('renders a subtitle describing the tool', async () => {
    const wrapper = await mountLanding()
    expect(wrapper.text()).toContain('Predict campaign outcomes before they happen')
  })

  it('renders scenario cards plus the custom simulation card', async () => {
    const wrapper = await mountLanding()
    const scenarioButtons = wrapper.findAll('button[data-index]')
    expect(scenarioButtons.length).toBe(5)
  })

  it('renders all 4 scenario names', async () => {
    const wrapper = await mountLanding()
    const text = wrapper.text()
    expect(text).toContain('Outbound Campaign Pre-Testing')
    expect(text).toContain('Sales Signal Validation')
    expect(text).toContain('Pricing Change Simulation')
    expect(text).toContain('Personalization Optimization')
  })

  it('highlights the outbound campaign card as hero with blue accent', async () => {
    const wrapper = await mountLanding()
    const buttons = wrapper.findAll('button[data-index]')
    const heroButton = buttons[0]
    expect(heroButton.classes()).toContain('bg-[rgba(32,104,255,0.15)]')
    expect(heroButton.classes()).toContain('border-[rgba(32,104,255,0.3)]')
  })

  it('hero card spans two columns on md+', async () => {
    const wrapper = await mountLanding()
    const buttons = wrapper.findAll('button[data-index]')
    const heroButton = buttons[0]
    expect(heroButton.classes()).toContain('md:col-span-2')
  })

  it('non-hero cards use default subtle styling', async () => {
    const wrapper = await mountLanding()
    const buttons = wrapper.findAll('button[data-index]')
    const nonHeroCard = buttons.find((b) => b.text().includes('Sales Signal'))
    expect(nonHeroCard.classes()).toContain('bg-white/5')
    expect(nonHeroCard.classes()).toContain('border-white/10')
  })

  it('renders the custom simulation card', async () => {
    const wrapper = await mountLanding()
    expect(wrapper.text()).toContain('Custom Simulation')
  })

  it('uses a 2-column grid for scenario cards', async () => {
    const wrapper = await mountLanding()
    const grid = wrapper.find('.grid.grid-cols-1.md\\:grid-cols-2')
    expect(grid.exists()).toBe(true)
  })

  it('navigates to scenario builder when a card is clicked', async () => {
    const wrapper = await mountLanding()
    const firstButton = wrapper.findAll('button[data-index]')[0]
    await firstButton.trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/scenarios/outbound_campaign')
  })

  it('navigates to correct scenario for each card', async () => {
    const wrapper = await mountLanding()
    const buttons = wrapper.findAll('button[data-index]')
    const expectedIds = [
      'outbound_campaign',
      'signal_validation',
      'pricing_simulation',
      'personalization',
      'custom',
    ]
    for (let i = 0; i < buttons.length; i++) {
      mockPush.mockClear()
      await buttons[i].trigger('click')
      expect(mockPush).toHaveBeenCalledWith(`/scenarios/${expectedIds[i]}`)
    }
  })

  it('has a dark gradient hero section', async () => {
    const wrapper = await mountLanding()
    const hero = wrapper.find('section')
    expect(hero.classes()).toContain('bg-gradient-to-b')
    expect(hero.classes()).toContain('from-[#050505]')
    expect(hero.classes()).toContain('to-[#1a1a3e]')
  })

  it('shows loading skeleton while fetching scenarios', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    const wrapper = mount(LandingView, {
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>' } },
      },
    })
    expect(wrapper.findAll('.animate-pulse').length).toBeGreaterThan(0)
    expect(wrapper.findAll('button[data-index]').length).toBe(0)
  })

  it('falls back to hardcoded scenarios on fetch error', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('Network error'))))
    const wrapper = mount(LandingView, {
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>' } },
      },
    })
    await flushPromises()
    const scenarioButtons = wrapper.findAll('button[data-index]')
    expect(scenarioButtons.length).toBe(5)
    expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
  })

  it('unwraps {scenarios:[...]} response from backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        scenarios: [
          { id: 'test_scenario', name: 'Test', description: 'A test', icon: 'mail' },
        ],
      }),
    }))
    const wrapper = mount(LandingView, {
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>' } },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Test')
  })
})
