import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import AppNav from '../AppNav.vue'

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

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/simulations', component: { template: '<div>Simulations</div>' } },
      { path: '/settings', component: { template: '<div>Settings</div>' } },
    ],
  })
}

function mountNav(options = {}) {
  const router = createTestRouter()
  return { wrapper: mount(AppNav, { global: { plugins: [createPinia(), router] }, ...options }), router }
}

describe('AppNav', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  it('renders the Intercom logo SVG', () => {
    const { wrapper } = mountNav()
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('rect[fill="var(--color-primary)"]').exists()).toBe(true)
  })

  it('renders MiroFish brand text', () => {
    const { wrapper } = mountNav()
    expect(wrapper.text()).toContain('MiroFish')
    expect(wrapper.text()).toContain('GTM Demo')
  })

  it('renders navigation links for Home, Simulations, and Settings', () => {
    const { wrapper } = mountNav()
    const links = wrapper.findAll('a')
    const hrefs = links.map(l => l.attributes('href'))
    expect(hrefs).toContain('/')
    expect(hrefs).toContain('/simulations')
    expect(hrefs).toContain('/settings')
  })

  it('shows "Local" connection status', () => {
    const { wrapper } = mountNav()
    expect(wrapper.text()).toContain('Local')
  })

  it('has three desktop nav links', () => {
    const { wrapper } = mountNav()
    expect(wrapper.findAll('.nav-link').length).toBe(3)
  })

  it('mobile menu is hidden by default', () => {
    const { wrapper } = mountNav()
    const mobileDropdown = wrapper.find('.md\\:hidden.absolute')
    expect(mobileDropdown.exists()).toBe(false)
  })

  it('toggles mobile menu on hamburger click', async () => {
    const { wrapper } = mountNav()
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    expect(hamburger.exists()).toBe(true)

    await hamburger.trigger('click')
    expect(wrapper.find('.md\\:hidden.absolute').exists()).toBe(true)

    await hamburger.trigger('click')
    expect(wrapper.find('.md\\:hidden.absolute').exists()).toBe(false)
  })

  it('mobile menu shows Connected text', async () => {
    const { wrapper } = mountNav()
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    await hamburger.trigger('click')
    expect(wrapper.text()).toContain('Connected')
  })

  it('closes mobile menu on route change', async () => {
    const { wrapper, router } = mountNav()
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    await hamburger.trigger('click')
    expect(wrapper.find('.md\\:hidden.absolute').exists()).toBe(true)

    await router.push('/settings')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.md\\:hidden.absolute').exists()).toBe(false)
  })
})
