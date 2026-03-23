import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppLayout from '../AppLayout.vue'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false })))
})

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
    ],
  })
}

describe('AppLayout', () => {
  it('renders AppNav and AppFooter', async () => {
    const router = createTestRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
    })

    expect(wrapper.find('nav').exists()).toBe(true)
    expect(wrapper.find('footer').exists()).toBe(true)
  })

  it('renders slot content in main area', async () => {
    const router = createTestRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
      slots: {
        default: '<div class="test-content">Hello World</div>',
      },
    })

    const main = wrapper.find('main')
    expect(main.exists()).toBe(true)
    expect(main.find('.test-content').exists()).toBe(true)
    expect(main.text()).toContain('Hello World')
  })

  it('has flex column layout for sticky footer', async () => {
    const router = createTestRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
    })

    const container = wrapper.find('.min-h-screen')
    expect(container.exists()).toBe(true)
    expect(container.classes()).toContain('flex')
    expect(container.classes()).toContain('flex-col')
  })

  it('makes main content area fill available space', async () => {
    const router = createTestRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
    })

    const main = wrapper.find('main')
    expect(main.classes()).toContain('flex-1')
  })
})
