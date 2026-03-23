import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LandingView from '../LandingView.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

beforeEach(() => {
  vi.clearAllMocks()
  // Mock fetch to reject so the fallback scenario data is used
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('No server')))
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
    const buttons = wrapper.findAll('button')
    const heroButton = buttons[0]
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

  it('unwraps {scenarios:[...]} response from backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        scenarios: [
          { id: 'test_scenario', name: 'Test', description: 'A test', icon: 'mail' },
        ],
      }),
    }))
    const wrapper = mount(LandingView)
    await flushPromises()
    expect(wrapper.text()).toContain('Test')
  })
})
