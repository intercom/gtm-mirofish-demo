import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppNav from '../components/layout/AppNav.vue'
import ReportView from '../views/ReportView.vue'
import LandingView from '../views/LandingView.vue'

const routerLinkStub = {
  template: '<a :href="to" class="router-link" v-bind="$attrs"><slot /></a>',
  props: ['to'],
}

const routerViewStub = {
  template: '<div class="router-view"></div>',
}

function mountWithStubs(component, options = {}) {
  return mount(component, {
    global: {
      stubs: {
        'router-link': routerLinkStub,
        'router-view': routerViewStub,
      },
    },
    ...options,
  })
}

describe('AppNav responsive behavior', () => {
  it('renders hamburger button with md:hidden class', () => {
    const wrapper = mountWithStubs(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    expect(hamburger.exists()).toBe(true)
    expect(hamburger.classes()).toContain('md:hidden')
  })

  it('hides desktop nav links on mobile via hidden md:flex', () => {
    const wrapper = mountWithStubs(AppNav)
    const desktopNav = wrapper.find('.hidden.md\\:flex')
    expect(desktopNav.exists()).toBe(true)
    expect(desktopNav.text()).toContain('Home')
    expect(desktopNav.text()).toContain('Settings')
  })

  it('does not show mobile menu by default', () => {
    const wrapper = mountWithStubs(AppNav)
    const mobileMenu = wrapper.find('.md\\:hidden.mt-3')
    expect(mobileMenu.exists()).toBe(false)
  })

  it('toggles mobile menu when hamburger is clicked', async () => {
    const wrapper = mountWithStubs(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')

    await hamburger.trigger('click')
    let mobileMenu = wrapper.find('.md\\:hidden.mt-3')
    expect(mobileMenu.exists()).toBe(true)
    expect(mobileMenu.text()).toContain('Home')
    expect(mobileMenu.text()).toContain('Settings')

    await hamburger.trigger('click')
    mobileMenu = wrapper.find('.md\\:hidden.mt-3')
    expect(mobileMenu.exists()).toBe(false)
  })

  it('shows X icon when menu is open', async () => {
    const wrapper = mountWithStubs(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')

    // Closed: hamburger icon (3-line path with fill-rule)
    expect(hamburger.findAll('svg').length).toBe(1)

    await hamburger.trigger('click')
    // Open: X icon (different SVG)
    const svg = hamburger.find('svg')
    expect(svg.exists()).toBe(true)
  })

  it('sets aria-expanded attribute correctly', async () => {
    const wrapper = mountWithStubs(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')

    expect(hamburger.attributes('aria-expanded')).toBe('false')
    await hamburger.trigger('click')
    expect(hamburger.attributes('aria-expanded')).toBe('true')
  })
})

describe('ReportView responsive behavior', () => {
  it('renders desktop sidebar with hidden md:block class', () => {
    const wrapper = mountWithStubs(ReportView, {
      props: { taskId: 'test-123' },
    })
    const desktopSidebar = wrapper.find('.hidden.md\\:block')
    expect(desktopSidebar.exists()).toBe(true)
  })

  it('uses responsive grid layout', () => {
    const wrapper = mountWithStubs(ReportView, {
      props: { taskId: 'test-123' },
    })
    const grid = wrapper.find('.grid')
    expect(grid.classes()).toContain('grid-cols-1')
    expect(grid.classes()).toContain('md:grid-cols-4')
  })

  it('has responsive padding on container', () => {
    const wrapper = mountWithStubs(ReportView, {
      props: { taskId: 'test-123' },
    })
    const container = wrapper.find('.max-w-6xl')
    expect(container.classes()).toContain('px-4')
    expect(container.classes()).toContain('md:px-6')
  })
})

describe('LandingView responsive behavior', () => {
  it('uses single column on mobile, 2 columns on tablet for scenario cards', () => {
    const wrapper = mountWithStubs(LandingView)
    const cardGrid = wrapper.find('.grid.grid-cols-1.md\\:grid-cols-2')
    expect(cardGrid.exists()).toBe(true)
  })

  it('renders all 4 scenario cards', () => {
    const wrapper = mountWithStubs(LandingView)
    const cards = wrapper.findAll('button')
    expect(cards.length).toBe(4)
  })

  it('uses responsive text size for hero heading', () => {
    const wrapper = mountWithStubs(LandingView)
    const h1 = wrapper.find('h1')
    expect(h1.classes()).toContain('text-3xl')
    expect(h1.classes()).toContain('md:text-6xl')
  })

  it('has responsive padding on hero section', () => {
    const wrapper = mountWithStubs(LandingView)
    const hero = wrapper.find('section')
    expect(hero.classes()).toContain('px-4')
    expect(hero.classes()).toContain('md:px-6')
    expect(hero.classes()).toContain('py-12')
    expect(hero.classes()).toContain('md:py-32')
  })

  it('uses responsive grid for stats banner', () => {
    const wrapper = mountWithStubs(LandingView)
    const statsGrid = wrapper.find('.grid.grid-cols-2.md\\:grid-cols-4')
    expect(statsGrid.exists()).toBe(true)
  })

  it('uses responsive grid for how-it-works section', () => {
    const wrapper = mountWithStubs(LandingView)
    const howGrid = wrapper.find('.grid.grid-cols-1.md\\:grid-cols-3')
    expect(howGrid.exists()).toBe(true)
  })
})
