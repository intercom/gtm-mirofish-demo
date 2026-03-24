import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppLayout from '../AppLayout.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
    ],
  })
}

describe('AppLayout', () => {
  it('renders AppNav, slot content, and AppFooter', () => {
    const router = createTestRouter()
    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
      slots: { default: '<div class="test-content">Page Content</div>' },
    })

    expect(wrapper.find('nav').exists()).toBe(true)
    expect(wrapper.find('main').exists()).toBe(true)
    expect(wrapper.find('footer').exists()).toBe(true)
    expect(wrapper.text()).toContain('Page Content')
  })

  it('renders slot content inside <main>', () => {
    const router = createTestRouter()
    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
      slots: { default: '<p>Hello World</p>' },
    })

    const main = wrapper.find('main')
    expect(main.text()).toContain('Hello World')
  })

  it('has a min-h-screen flex column layout', () => {
    const router = createTestRouter()
    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
    })

    const root = wrapper.find('div')
    expect(root.classes()).toContain('min-h-screen')
    expect(root.classes()).toContain('flex')
    expect(root.classes()).toContain('flex-col')
  })

  it('main area has flex-1 to fill remaining space', () => {
    const router = createTestRouter()
    const wrapper = mount(AppLayout, {
      global: { plugins: [router] },
    })

    const main = wrapper.find('main')
    expect(main.classes()).toContain('flex-1')
  })
})
