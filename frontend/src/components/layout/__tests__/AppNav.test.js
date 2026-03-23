import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppNav from '../AppNav.vue'

function createTestRouter(initialRoute = '/') {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/settings', component: { template: '<div>Settings</div>' } },
    ],
  })
}

async function mountNav(initialRoute = '/') {
  const router = createTestRouter()
  router.push(initialRoute)
  await router.isReady()

  return mount(AppNav, {
    global: {
      plugins: [router],
    },
  })
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false })))
})

describe('AppNav', () => {
  it('renders the Intercom logo SVG', async () => {
    const wrapper = await mountNav()
    const svg = wrapper.find('svg[aria-label="Intercom logo"]')
    expect(svg.exists()).toBe(true)
  })

  it('renders MiroFish brand text', async () => {
    const wrapper = await mountNav()
    expect(wrapper.text()).toContain('MiroFish')
    expect(wrapper.text()).toContain('GTM Demo')
  })

  it('renders navigation links', async () => {
    const wrapper = await mountNav()
    const links = wrapper.findAll('.nav-link')
    expect(links.length).toBeGreaterThanOrEqual(2)

    const labels = links.map((l) => l.text())
    expect(labels).toContain('Home')
    expect(labels).toContain('Settings')
  })

  it('applies active class to current route link', async () => {
    const wrapper = await mountNav('/')
    const homeLinks = wrapper.findAll('.nav-link').filter((l) => l.text() === 'Home')
    expect(homeLinks[0].classes()).toContain('nav-link--active')
  })

  it('shows auth status indicator', async () => {
    const wrapper = await mountNav()
    expect(wrapper.text()).toContain('Not signed in')
  })

  it('shows authenticated state when auth succeeds', async () => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ authenticated: true, email: 'user@intercom.io' }),
      }),
    ))

    const wrapper = await mountNav()
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('user@intercom.io')
    })
  })

  it('has a mobile menu toggle button', async () => {
    const wrapper = await mountNav()
    const toggleBtn = wrapper.find('button[aria-label="Toggle navigation menu"]')
    expect(toggleBtn.exists()).toBe(true)
  })

  it('toggles mobile menu on click', async () => {
    const wrapper = await mountNav()
    const toggleBtn = wrapper.find('button[aria-label="Toggle navigation menu"]')

    expect(wrapper.find('.md\\:hidden.mt-3').exists()).toBe(false)

    await toggleBtn.trigger('click')
    expect(wrapper.find('.md\\:hidden.mt-3').exists()).toBe(true)

    await toggleBtn.trigger('click')
    expect(wrapper.find('.md\\:hidden.mt-3').exists()).toBe(false)
  })
})
