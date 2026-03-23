import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'
import LandingView from './LandingView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: LandingView },
      { path: '/scenarios/:id', component: { template: '<div />' } },
    ],
  })
}

describe('LandingView', () => {
  it('renders hero section with title', () => {
    const router = createTestRouter()
    const wrapper = mount(LandingView, {
      global: { plugins: [router] },
    })
    expect(wrapper.text()).toContain('MiroFish Swarm Intelligence')
  })

  it('renders scenario cards after mount via TransitionGroup', async () => {
    const router = createTestRouter()
    const wrapper = mount(LandingView, {
      global: { plugins: [router] },
    })

    // After mount, showCards becomes true
    await wrapper.vm.$nextTick()
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(4)
    expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
  })

  it('provides stagger hooks for card animation', async () => {
    const router = createTestRouter()
    const wrapper = mount(LandingView, {
      global: { plugins: [router] },
    })
    await wrapper.vm.$nextTick()

    // Cards should have data-index attributes for stagger timing
    const buttons = wrapper.findAll('button[data-index]')
    expect(buttons.length).toBe(4)
    expect(buttons[0].attributes('data-index')).toBe('0')
    expect(buttons[3].attributes('data-index')).toBe('3')
  })

  it('renders how-it-works steps with stagger', async () => {
    vi.useFakeTimers()
    const router = createTestRouter()
    const wrapper = mount(LandingView, {
      global: { plugins: [router] },
    })

    // showSteps is delayed by 200ms
    vi.advanceTimersByTime(300)
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Seed Your Scenario')
    expect(wrapper.text()).toContain('Simulate the Swarm')
    expect(wrapper.text()).toContain('Get Predictive Reports')
    vi.useRealTimers()
  })
})
