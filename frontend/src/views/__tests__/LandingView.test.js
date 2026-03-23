import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LandingView from '../LandingView.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const SCENARIOS = [
  {
    id: 'outbound_campaign',
    name: 'Outbound Campaign Pre-Testing',
    description: 'Simulate how AI-generated outbound emails land with synthetic prospect populations.',
    icon: '📧',
    hero: true,
  },
  {
    id: 'signal_validation',
    name: 'Sales Signal Validation',
    description: 'Test whether signals actually predict buying behavior.',
    icon: '📡',
  },
  {
    id: 'pricing_simulation',
    name: 'Pricing Change Simulation',
    description: 'Predict customer reactions to P5 pricing migration.',
    icon: '💰',
  },
  {
    id: 'personalization',
    name: 'Personalization Optimization',
    description: 'Rank email variants by simulated engagement.',
    icon: '✨',
  },
]

beforeEach(() => {
  mockPush.mockClear()
  vi.stubGlobal('fetch', vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(SCENARIOS) }),
  ))
})

async function mountLanding() {
  const wrapper = mount(LandingView)
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

  it('renders exactly 4 scenario cards', async () => {
    const wrapper = await mountLanding()
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(4)
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
    const heroButton = wrapper.findAll('button')[0]
    expect(heroButton.classes()).toContain('border-[rgba(32,104,255,0.3)]')
    expect(heroButton.classes()).toContain('bg-[rgba(32,104,255,0.15)]')
  })

  it('shows a Hero badge on the outbound campaign card', async () => {
    const wrapper = await mountLanding()
    const heroBadge = wrapper.findAll('span').find(s => s.text() === 'Hero')
    expect(heroBadge).toBeTruthy()
  })

  it('does not show Hero badge on non-hero cards', async () => {
    const wrapper = await mountLanding()
    const buttons = wrapper.findAll('button')
    const nonHeroButtons = buttons.slice(1)
    for (const btn of nonHeroButtons) {
      expect(btn.text()).not.toContain('Hero')
    }
  })

  it('uses a 2-column grid for cards on md+ screens', async () => {
    const wrapper = await mountLanding()
    const grid = wrapper.find('.grid.grid-cols-1.md\\:grid-cols-2')
    expect(grid.exists()).toBe(true)
  })

  it('navigates to scenario builder when a card is clicked', async () => {
    const wrapper = await mountLanding()
    const firstButton = wrapper.findAll('button')[0]
    await firstButton.trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/scenarios/outbound_campaign')
  })

  it('navigates to correct scenario for each card', async () => {
    const wrapper = await mountLanding()
    const buttons = wrapper.findAll('button')
    const expectedIds = [
      'outbound_campaign',
      'signal_validation',
      'pricing_simulation',
      'personalization',
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
    const wrapper = mount(LandingView)
    expect(wrapper.findAll('.animate-pulse').length).toBeGreaterThan(0)
    expect(wrapper.findAll('button').length).toBe(0)
  })

  it('falls back to hardcoded scenarios on fetch error', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('Network error'))))
    const wrapper = mount(LandingView)
    await flushPromises()
    expect(wrapper.findAll('button').length).toBe(4)
    expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
  })
})
