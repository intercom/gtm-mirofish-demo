import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppNav from '../components/layout/AppNav.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import LandingView from '../views/LandingView.vue'
import ReportView from '../views/ReportView.vue'
import ScenarioBuilderView from '../views/ScenarioBuilderView.vue'
import ChatView from '../views/ChatView.vue'
import SettingsView from '../views/SettingsView.vue'
import SimulationView from '../views/SimulationView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/settings', component: { template: '<div />' } },
      { path: '/scenarios/:id', component: { template: '<div />' } },
      { path: '/chat/:taskId', component: { template: '<div />' } },
      { path: '/report/:taskId', component: { template: '<div />' } },
      { path: '/simulation/:taskId', component: { template: '<div />' } },
    ],
  })
}

async function mountWithRouter(component, options = {}) {
  const router = createTestRouter()
  router.push('/')
  await router.isReady()
  return mount(component, {
    global: { plugins: [router] },
    ...options,
  })
}

describe('AppNav — hamburger menu', () => {
  it('renders hamburger button with md:hidden class', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle menu"]')
    expect(hamburger.exists()).toBe(true)
    expect(hamburger.classes()).toContain('md:hidden')
  })

  it('hides desktop nav links on mobile via hidden md:flex', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const desktopNav = wrapper.find('.hidden.md\\:flex')
    expect(desktopNav.exists()).toBe(true)
  })

  it('mobile menu is hidden by default', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const mobileMenu = wrapper.find('.md\\:hidden.absolute')
    expect(mobileMenu.exists()).toBe(false)
  })

  it('toggles mobile menu on hamburger click', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle menu"]')

    await hamburger.trigger('click')
    let mobileMenu = wrapper.find('.md\\:hidden.absolute')
    expect(mobileMenu.exists()).toBe(true)

    const links = mobileMenu.findAll('a')
    expect(links.length).toBeGreaterThanOrEqual(2)

    await hamburger.trigger('click')
    mobileMenu = wrapper.find('.md\\:hidden.absolute')
    expect(mobileMenu.exists()).toBe(false)
  })

  it('hamburger animates to X when open', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle menu"]')
    await hamburger.trigger('click')

    const bars = hamburger.findAll('span')
    expect(bars[0].classes()).toContain('rotate-45')
    expect(bars[1].classes()).toContain('opacity-0')
    expect(bars[2].classes()).toContain('-rotate-45')
  })
})

describe('LandingView — mobile card stacking', () => {
  it('scenario card grid uses grid-cols-1 for mobile', async () => {
    const wrapper = await mountWithRouter(LandingView)
    const cardGrid = wrapper.find('.grid.grid-cols-1')
    expect(cardGrid.exists()).toBe(true)
  })

  it('hero section has responsive padding', async () => {
    const wrapper = await mountWithRouter(LandingView)
    const hero = wrapper.find('section')
    expect(hero.classes()).toContain('px-4')
    expect(hero.classes()).toContain('md:px-6')
  })

  it('hero heading has responsive text size', async () => {
    const wrapper = await mountWithRouter(LandingView)
    const h1 = wrapper.find('h1')
    expect(h1.classes()).toContain('text-3xl')
    expect(h1.classes()).toContain('md:text-6xl')
  })

  it('renders all 4 scenario cards', async () => {
    const wrapper = await mountWithRouter(LandingView)
    const cards = wrapper.findAll('button')
    expect(cards.length).toBe(4)
  })
})

describe('ReportView — sidebar to tabs on mobile', () => {
  it('renders mobile horizontal tab bar with md:hidden', async () => {
    const wrapper = await mountWithRouter(ReportView, {
      props: { taskId: 'test-123' },
    })
    // Set chapters to trigger tab bar rendering
    wrapper.vm.chapters = [
      { title: 'Chapter 1', html: '<p>Content 1</p>' },
      { title: 'Chapter 2', html: '<p>Content 2</p>' },
    ]
    wrapper.vm.generating = false
    await wrapper.vm.$nextTick()

    const tabBar = wrapper.find('.md\\:hidden.overflow-x-auto')
    expect(tabBar.exists()).toBe(true)
  })

  it('hides desktop sidebar on mobile via hidden md:block', async () => {
    const wrapper = await mountWithRouter(ReportView, {
      props: { taskId: 'test-123' },
    })
    wrapper.vm.chapters = [
      { title: 'Chapter 1', html: '<p>Content 1</p>' },
    ]
    wrapper.vm.generating = false
    await wrapper.vm.$nextTick()

    const sidebar = wrapper.find('.hidden.md\\:block.space-y-2')
    expect(sidebar.exists()).toBe(true)
  })

  it('mobile tabs switch active chapter', async () => {
    const wrapper = await mountWithRouter(ReportView, {
      props: { taskId: 'test-123' },
    })
    wrapper.vm.chapters = [
      { title: 'Chapter 1', html: '<p>Content 1</p>' },
      { title: 'Chapter 2', html: '<p>Content 2</p>' },
    ]
    wrapper.vm.generating = false
    await wrapper.vm.$nextTick()

    const tabButtons = wrapper.find('.md\\:hidden.overflow-x-auto').findAll('button')
    expect(tabButtons.length).toBe(2)

    await tabButtons[1].trigger('click')
    expect(wrapper.vm.activeChapter).toBe(1)
  })
})

describe('ScenarioBuilderView — sidebar to tabs on mobile', () => {
  it('renders mobile tab switcher with md:hidden', async () => {
    const wrapper = await mountWithRouter(ScenarioBuilderView, {
      props: { id: 'test' },
    })
    wrapper.vm.scenario = {
      name: 'Test Scenario',
      description: 'Test desc',
      seed_text: 'Test seed',
    }
    wrapper.vm.loading = false
    await wrapper.vm.$nextTick()

    const tabSwitcher = wrapper.find('.md\\:hidden.flex.gap-2')
    expect(tabSwitcher.exists()).toBe(true)

    const tabs = tabSwitcher.findAll('button')
    expect(tabs.length).toBe(2)
    expect(tabs[0].text()).toContain('Seed Document')
    expect(tabs[1].text()).toContain('Configuration')
  })

  it('tab switching toggles seed/config visibility', async () => {
    const wrapper = await mountWithRouter(ScenarioBuilderView, {
      props: { id: 'test' },
    })
    wrapper.vm.scenario = {
      name: 'Test Scenario',
      description: 'Test desc',
      seed_text: 'Test seed',
    }
    wrapper.vm.loading = false
    await wrapper.vm.$nextTick()

    // Default: seed tab active
    expect(wrapper.vm.activeTab).toBe('seed')
    const seedPanel = wrapper.find('.md\\:col-span-2')
    expect(seedPanel.classes()).not.toContain('hidden')

    // Switch to config
    const tabs = wrapper.find('.md\\:hidden.flex.gap-2').findAll('button')
    await tabs[1].trigger('click')
    expect(wrapper.vm.activeTab).toBe('config')
  })
})

describe('ChatView — mobile layout adjustments', () => {
  it('uses responsive message margins', async () => {
    const wrapper = await mountWithRouter(ChatView, {
      props: { taskId: 'test-123' },
    })
    // Add a user message
    wrapper.vm.messages = [{ role: 'user', content: 'Hello' }]
    await wrapper.vm.$nextTick()

    const msg = wrapper.find('.rounded-lg.px-3')
    expect(msg.exists()).toBe(true)
    expect(msg.classes()).toContain('ml-6')
    expect(msg.classes()).toContain('md:ml-12')
  })

  it('has responsive input padding', async () => {
    const wrapper = await mountWithRouter(ChatView, {
      props: { taskId: 'test-123' },
    })
    const inputArea = wrapper.find('.border-t')
    expect(inputArea.classes()).toContain('px-4')
    expect(inputArea.classes()).toContain('md:px-6')
  })
})

describe('SimulationView — mobile layout', () => {
  it('header wraps on mobile with flex-col sm:flex-row', async () => {
    const wrapper = await mountWithRouter(SimulationView, {
      props: { taskId: 'test-123' },
    })
    const header = wrapper.find('.flex.flex-col.sm\\:flex-row')
    expect(header.exists()).toBe(true)
  })

  it('metric cards have responsive padding', async () => {
    const wrapper = await mountWithRouter(SimulationView, {
      props: { taskId: 'test-123' },
    })
    const metricCard = wrapper.find('.bg-\\[var\\(--color-surface\\)\\].border.border-\\[var\\(--color-border\\)\\].rounded-lg.p-3')
    expect(metricCard.exists()).toBe(true)
    expect(metricCard.classes()).toContain('md:p-4')
  })
})

describe('SettingsView — mobile layout', () => {
  it('API key inputs stack on mobile with flex-col sm:flex-row', async () => {
    const wrapper = await mountWithRouter(SettingsView)
    const inputGroups = wrapper.findAll('.flex.flex-col.sm\\:flex-row')
    expect(inputGroups.length).toBeGreaterThanOrEqual(2)
  })

  it('has responsive page padding', async () => {
    const wrapper = await mountWithRouter(SettingsView)
    const container = wrapper.find('.max-w-2xl')
    expect(container.classes()).toContain('px-4')
    expect(container.classes()).toContain('md:px-6')
  })
})

describe('AppFooter — mobile layout', () => {
  it('breaks footer text on mobile with sm:hidden br', async () => {
    const router = createTestRouter()
    router.push('/')
    await router.isReady()
    const wrapper = mount(AppFooter, { global: { plugins: [router] } })

    const br = wrapper.find('br')
    expect(br.exists()).toBe(true)
    expect(br.classes()).toContain('sm:hidden')
  })
})
