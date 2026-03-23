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
  describe('hero section', () => {
    it('renders gradient hero with navy-to-dark-blue background', () => {
      const wrapper = mountLanding()
      const hero = wrapper.find('section')
      expect(hero.classes()).toContain('bg-gradient-to-b')
      expect(hero.classes()).toContain('from-[#050505]')
      expect(hero.classes()).toContain('to-[#1a1a3e]')
    })

    it('displays Intercom GTM Systems branding', () => {
      const wrapper = mountLanding()
      expect(wrapper.text()).toContain('Intercom GTM Systems')
    })

    it('displays the MiroFish Swarm Intelligence headline', () => {
      const wrapper = mountLanding()
      const h1 = wrapper.find('h1')
      expect(h1.text()).toBe('MiroFish Swarm Intelligence')
    })

    it('displays a subtitle explaining the tool', () => {
      const wrapper = mountLanding()
      expect(wrapper.text()).toContain('Predict campaign outcomes before they happen')
    })
  })

  describe('scenario cards', () => {
    it('renders exactly 4 scenario cards', () => {
      const wrapper = mountLanding()
      const cards = wrapper.findAll('button')
      expect(cards).toHaveLength(4)
    })

    it('renders cards in a 2x2 responsive grid', () => {
      const wrapper = mountLanding()
      const grid = wrapper.find('.grid.grid-cols-1.md\\:grid-cols-2')
      expect(grid.exists()).toBe(true)
    })

    it('renders all four scenario names', () => {
      const wrapper = mountLanding()
      const text = wrapper.text()
      expect(text).toContain('Outbound Campaign Pre-Testing')
      expect(text).toContain('Sales Signal Validation')
      expect(text).toContain('Pricing Change Simulation')
      expect(text).toContain('Personalization Optimization')
    })

    it('highlights the outbound campaign card with blue accent styling', () => {
      const wrapper = mountLanding()
      const buttons = wrapper.findAll('button')
      const heroCard = buttons.find((b) => b.text().includes('Outbound Campaign'))
      expect(heroCard.classes()).toContain('bg-[rgba(32,104,255,0.15)]')
      expect(heroCard.classes()).toContain('border-[rgba(32,104,255,0.3)]')
    })

    it('shows a Hero badge on the outbound campaign card', () => {
      const wrapper = mountLanding()
      const badge = wrapper.findAll('span').find((s) => s.text() === 'Hero')
      expect(badge.exists()).toBe(true)
      expect(badge.classes()).toContain('bg-[#2068FF]')
    })

    it('non-hero cards use default subtle styling', () => {
      const wrapper = mountLanding()
      const buttons = wrapper.findAll('button')
      const nonHeroCard = buttons.find((b) => b.text().includes('Sales Signal'))
      expect(nonHeroCard.classes()).toContain('bg-white/5')
      expect(nonHeroCard.classes()).toContain('border-white/10')
    })

    it('navigates to scenario route when a card is clicked', async () => {
      const wrapper = mountLanding()
      const buttons = wrapper.findAll('button')
      const outboundCard = buttons.find((b) => b.text().includes('Outbound Campaign'))
      await outboundCard.trigger('click')
      expect(mockPush).toHaveBeenCalledWith('/scenarios/outbound_campaign')
    })
  })
})
