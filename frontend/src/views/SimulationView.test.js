import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import SimulationView from './SimulationView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/simulation/:taskId', component: SimulationView, props: true },
      { path: '/report/:taskId', component: { template: '<div />' } },
    ],
  })
}

describe('SimulationView', () => {
  it('renders with running status', () => {
    const router = createTestRouter()
    const wrapper = mount(SimulationView, {
      props: { taskId: 'test-456' },
      global: { plugins: [router] },
    })
    expect(wrapper.text()).toContain('Live Simulation')
    expect(wrapper.text()).toContain('test-456')
    expect(wrapper.text()).toContain('Running')
  })

  it('renders metric cards with staggered entry after mount', async () => {
    const router = createTestRouter()
    const wrapper = mount(SimulationView, {
      props: { taskId: 'test-456' },
      global: { plugins: [router] },
    })

    await wrapper.vm.$nextTick()
    const cards = wrapper.findAll('[data-index]')
    expect(cards.length).toBe(4)
  })

  it('displays metric labels', async () => {
    const router = createTestRouter()
    const wrapper = mount(SimulationView, {
      props: { taskId: 'test-456' },
      global: { plugins: [router] },
    })

    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Total Actions')
    expect(wrapper.text()).toContain('Replies')
    expect(wrapper.text()).toContain('Likes')
    expect(wrapper.text()).toContain('Round')
  })

  it('renders activity feed placeholder', () => {
    const router = createTestRouter()
    const wrapper = mount(SimulationView, {
      props: { taskId: 'test-456' },
      global: { plugins: [router] },
    })
    expect(wrapper.text()).toContain('Agent Activity Feed')
  })
})
