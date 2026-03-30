import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import BulletChart from '../BulletChart.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests, setDimensions } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleMetrics = [
  { label: 'Revenue', actual: 75, target: 100, ranges: [50, 80, 100] },
  { label: 'Profit', actual: 45, target: 60, ranges: [30, 50, 70] },
]

function mountChart(props = {}) {
  return mount(BulletChart, {
    props: { metrics: sampleMetrics, ...props },
    attachTo: document.body,
  })
}

async function mountAndRender(props = {}) {
  const wrapper = mountChart(props)
  setDimensions(wrapper.find('.w-full').element)
  await wrapper.setProps({ metrics: [...(props.metrics || sampleMetrics)] })
  await nextTick()
  await nextTick()
  return wrapper
}

describe('BulletChart', () => {
  it('creates SVG element', async () => {
    const wrapper = await mountAndRender()
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })

  it('does not render SVG with empty metrics', async () => {
    const wrapper = mountChart({ metrics: [] })
    setDimensions(wrapper.find('.w-full').element)
    await nextTick()
    expect(wrapper.find('svg').exists()).toBe(false)
    wrapper.unmount()
  })

  it('renders rect elements for range bands and bars', async () => {
    const wrapper = await mountAndRender()
    const rects = wrapper.findAll('rect')
    // Each metric: 3 range bands + 1 actual bar + 1 target marker = 5 rects
    expect(rects.length).toBeGreaterThanOrEqual(sampleMetrics.length * 5)
    wrapper.unmount()
  })

  it('renders title and subtitle', async () => {
    const wrapper = await mountAndRender({ title: 'KPIs', subtitle: 'Q1 Progress' })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('KPIs')
    expect(texts).toContain('Q1 Progress')
    wrapper.unmount()
  })

  it('renders percentage value labels', async () => {
    const metrics = [{ label: 'Test', actual: 50, target: 100, ranges: [25, 75, 100] }]
    const wrapper = await mountAndRender({ metrics })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('50%')
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
