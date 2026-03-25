import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
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
      { path: '/login', component: { template: '<div>Login</div>' } },
    ],
  })
}

function mountNav(options = {}) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createTestRouter()
  return { wrapper: mount(AppNav, { global: { plugins: [pinia, router] }, ...options }), router }
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

  it('renders navigation links for Home and Settings', () => {
    const { wrapper } = mountNav()
    const links = wrapper.findAll('a')
    const hrefs = links.map(l => l.attributes('href'))
    expect(hrefs).toContain('/')
    expect(hrefs).toContain('/settings')
  })

  it('shows "Local" connection status', () => {
    const { wrapper } = mountNav()
    expect(wrapper.text()).toContain('Local')
  })

  it('mobile menu is hidden by default', () => {
    const { wrapper } = mountNav()
    const mobileMenuLinks = wrapper.findAll('.border-t')
    expect(mobileMenuLinks.length).toBe(0)
  })

  it('toggles mobile menu on hamburger click', async () => {
    const { wrapper } = mountNav()
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    expect(hamburger.exists()).toBe(true)

    await hamburger.trigger('click')
    expect(hamburger.attributes('aria-expanded')).toBe('true')

    await hamburger.trigger('click')
    expect(hamburger.attributes('aria-expanded')).toBe('false')
  })

  it('closes mobile menu on route change', async () => {
    const { wrapper, router } = mountNav()
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    await hamburger.trigger('click')
    expect(hamburger.attributes('aria-expanded')).toBe('true')

    await router.push('/settings')
    await wrapper.vm.$nextTick()
    expect(hamburger.attributes('aria-expanded')).toBe('false')
  })

  it('renders Simulations nav link', () => {
    const { wrapper } = mountNav()
    const links = wrapper.findAll('a')
    const hrefs = links.map(l => l.attributes('href'))
    expect(hrefs).toContain('/simulations')
  })
})
