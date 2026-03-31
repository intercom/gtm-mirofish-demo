import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import StreamGraph from '../StreamGraph.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = [
  { time: 1, topicA: 10, topicB: 20, topicC: 15 },
  { time: 2, topicA: 15, topicB: 18, topicC: 20 },
  { time: 3, topicA: 20, topicB: 25, topicC: 10 },
]

function mountChart(props = {}) {
  return mount(StreamGraph, {
    props: { data: sampleData, ...props },
    attachTo: document.body,
  })
}

describe('StreamGraph', () => {
  it('shows empty state when data is empty', () => {
    const wrapper = mount(StreamGraph, { props: { data: [] }, attachTo: document.body })
    expect(wrapper.text()).toContain('No stream data available')
    wrapper.unmount()
  })

  it('renders chart container when data is provided', () => {
    const wrapper = mountChart()
    expect(wrapper.find('[style*="height: 280px"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('renders title slot with default text', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).toContain('Topic Evolution')
    wrapper.unmount()
  })

  it('renders legend buttons for each category', () => {
    const wrapper = mountChart()
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(3)
    expect(buttons[0].text()).toContain('topicA')
    expect(buttons[1].text()).toContain('topicB')
    expect(buttons[2].text()).toContain('topicC')
    wrapper.unmount()
  })

  it('toggles category on button click', async () => {
    const wrapper = mountChart()
    await wrapper.findAll('button')[0].trigger('click')
    await nextTick()
    expect(wrapper.findAll('button')[0].classes()).toContain('opacity-40')
    wrapper.unmount()
  })

  it('re-enables disabled category on second click', async () => {
    const wrapper = mountChart()
    const btn = wrapper.findAll('button')[0]
    await btn.trigger('click')
    await nextTick()
    expect(wrapper.findAll('button')[0].classes()).toContain('opacity-40')
    await wrapper.findAll('button')[0].trigger('click')
    await nextTick()
    expect(wrapper.findAll('button')[0].classes()).not.toContain('opacity-40')
    wrapper.unmount()
  })

  it('prevents disabling all categories', async () => {
    const wrapper = mountChart()
    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
    await nextTick()
    await wrapper.findAll('button')[1].trigger('click')
    await nextTick()
    // Third click should be prevented (can't disable all)
    await wrapper.findAll('button')[2].trigger('click')
    await nextTick()
    const active = wrapper.findAll('button').filter(b => !b.classes().includes('opacity-40'))
    expect(active.length).toBeGreaterThanOrEqual(1)
    wrapper.unmount()
  })

  it('observes ResizeObserver on mount', () => {
    const wrapper = mountChart()
    expect(mockObserve).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('disconnects ResizeObserver on unmount', () => {
    const wrapper = mountChart()
    wrapper.unmount()
    expect(mockDisconnect).toHaveBeenCalled()
  })
})
