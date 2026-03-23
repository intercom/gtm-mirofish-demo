import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LandingView from '../LandingView.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

function mountLanding() {
  return mount(LandingView)
}

describe('LandingView', () => {
  it('renders the Intercom GTM Systems branding', () => {
    const wrapper = mountLanding()
    expect(wrapper.text()).toContain('Intercom GTM Systems')
  })

  it('renders the MiroFish Swarm Intelligence headline', () => {
    const wrapper = mountLanding()
    const h1 = wrapper.find('h1')
    expect(h1.text()).toBe('MiroFish Swarm Intelligence')
  })

  it('renders a subtitle describing the tool', () => {
    const wrapper = mountLanding()
    expect(wrapper.text()).toContain('Predict campaign outcomes before they happen')
  })

  it('renders exactly 4 scenario cards', () => {
    const wrapper = mountLanding()
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(4)
  })

  it('renders all 4 scenario names', () => {
    const wrapper = mountLanding()
    const text = wrapper.text()
    expect(text).toContain('Outbound Campaign Pre-Testing')
    expect(text).toContain('Sales Signal Validation')
    expect(text).toContain('Pricing Change Simulation')
    expect(text).toContain('Personalization Optimization')
  })

  it('highlights the outbound campaign card as hero with blue accent', () => {
    const wrapper = mountLanding()
    const buttons = wrapper.findAll('button')
    const heroButton = buttons[0]
    expect(heroButton.classes()).toContain('border-[rgba(32,104,255,0.3)]')
    expect(heroButton.classes()).toContain('bg-[rgba(32,104,255,0.15)]')
  })

  it('shows a Hero badge on the outbound campaign card', () => {
    const wrapper = mountLanding()
    const heroBadge = wrapper.findAll('span').find(s => s.text() === 'Hero')
    expect(heroBadge).toBeTruthy()
  })

  it('does not show Hero badge on non-hero cards', () => {
    const wrapper = mountLanding()
    const buttons = wrapper.findAll('button')
    const nonHeroButtons = buttons.slice(1)
    for (const btn of nonHeroButtons) {
      expect(btn.text()).not.toContain('Hero')
    }
  })

  it('uses a 2-column grid for cards on md+ screens', () => {
    const wrapper = mountLanding()
    const grid = wrapper.find('.grid.grid-cols-1.md\\:grid-cols-2')
    expect(grid.exists()).toBe(true)
  })

  it('navigates to scenario builder when a card is clicked', async () => {
    mockPush.mockClear()
    const wrapper = mountLanding()
    const firstButton = wrapper.findAll('button')[0]
    await firstButton.trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/scenarios/outbound_campaign')
  })

  it('navigates to correct scenario for each card', async () => {
    mockPush.mockClear()
    const wrapper = mountLanding()
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

  it('has a dark gradient hero section', () => {
    const wrapper = mountLanding()
    const hero = wrapper.find('section')
    expect(hero.classes()).toContain('bg-gradient-to-b')
    expect(hero.classes()).toContain('from-[#050505]')
    expect(hero.classes()).toContain('to-[#1a1a3e]')
  })
})
