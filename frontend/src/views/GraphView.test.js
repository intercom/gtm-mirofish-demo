import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import GraphView from './GraphView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/graph/:taskId', component: GraphView, props: true },
      { path: '/simulation/:taskId', component: { template: '<div />' } },
    ],
  })
}

describe('GraphView', () => {
  it('renders with building status initially', () => {
    const router = createTestRouter()
    const wrapper = mount(GraphView, {
      props: { taskId: 'test-123' },
      global: { plugins: [router] },
    })
    expect(wrapper.text()).toContain('Building Graph...')
    expect(wrapper.text()).toContain('test-123')
  })

  it('displays animated nodes after mount', async () => {
    const router = createTestRouter()
    const wrapper = mount(GraphView, {
      props: { taskId: 'test-123' },
      global: { plugins: [router] },
    })

    await wrapper.vm.$nextTick()
    // Nodes should have data-index for stagger
    const nodes = wrapper.findAll('[data-index]')
    expect(nodes.length).toBe(7)
    expect(wrapper.text()).toContain('Campaign')
    expect(wrapper.text()).toContain('Audience')
    expect(wrapper.text()).toContain('Signal')
  })

  it('transitions to complete status and shows continue button', async () => {
    vi.useFakeTimers()
    const router = createTestRouter()
    const wrapper = mount(GraphView, {
      props: { taskId: 'test-123' },
      global: { plugins: [router] },
    })

    vi.advanceTimersByTime(2000)
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Complete')
    expect(wrapper.text()).toContain('Continue to Simulation')
    vi.useRealTimers()
  })

  it('shows node and edge counts', async () => {
    const router = createTestRouter()
    const wrapper = mount(GraphView, {
      props: { taskId: 'test-123' },
      global: { plugins: [router] },
    })

    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('7 nodes')
    expect(wrapper.text()).toContain('9 edges')
  })
})
