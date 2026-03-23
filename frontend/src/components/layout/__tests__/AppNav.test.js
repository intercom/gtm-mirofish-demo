import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
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
      { path: '/settings', component: { template: '<div>Settings</div>' } },
      { path: '/login', component: { template: '<div>Login</div>' } },
    ],
  })
}

function mountNav(options = {}) {
  const router = createTestRouter()
  return { wrapper: mount(AppNav, { global: { plugins: [router] }, ...options }), router }
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

  it('shows "Connected" status when no auth user', () => {
    const { wrapper } = mountNav()
    expect(wrapper.text()).toContain('Connected')
  })

  it('shows user initial and email when auth_user is in localStorage', () => {
    localStorageMock.setItem('auth_user', JSON.stringify({ email: 'alice@intercom.io' }))
    const { wrapper } = mountNav()
    expect(wrapper.text()).toContain('A')
    expect(wrapper.text()).toContain('alice@intercom.io')
    expect(wrapper.text()).toContain('Sign out')
  })

  it('does not show "Connected" when auth user is present', () => {
    localStorageMock.setItem('auth_user', JSON.stringify({ email: 'bob@intercom.io' }))
    const { wrapper } = mountNav()
    expect(wrapper.text()).not.toContain('Connected')
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
    expect(wrapper.findAll('.nav-link').length).toBeGreaterThan(2)

    await hamburger.trigger('click')
    expect(wrapper.findAll('.nav-link').length).toBe(2)
  })

  it('closes mobile menu when a nav link is clicked', async () => {
    const { wrapper } = mountNav()
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    await hamburger.trigger('click')

    const allLinks = wrapper.findAll('.nav-link')
    const mobileLink = allLinks[allLinks.length - 1]
    await mobileLink.trigger('click')

    expect(wrapper.findAll('.nav-link').length).toBe(2)
  })

  it('handles malformed JSON in localStorage gracefully', () => {
    localStorageMock.setItem('auth_user', 'not-json')
    const { wrapper } = mountNav()
    expect(wrapper.text()).toContain('Connected')
  })
})
