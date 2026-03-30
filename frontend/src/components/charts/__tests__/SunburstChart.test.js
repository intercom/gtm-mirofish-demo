import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SunburstChart from '../SunburstChart.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests, setDimensions } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = {
  name: 'Root',
  children: [
    { name: 'A', children: [
      { name: 'A1', value: 10 },
      { name: 'A2', value: 20 },
    ]},
    { name: 'B', value: 30 },
    { name: 'C', value: 15 },
  ],
}

function mountChart(props = {}) {
  return mount(SunburstChart, {
    props: { data: sampleData, ...props },
    attachTo: document.body,
  })
}

async function mountAndRender(props = {}) {
  const wrapper = mountChart(props)
  const chartEl = wrapper.find('.relative.w-full').element
  if (chartEl) setDimensions(chartEl)
  await wrapper.setProps({ data: { ...sampleData } })
  await nextTick()
  await nextTick()
  return wrapper
}

describe('SunburstChart', () => {
  it('renders hint text', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).toContain('Click a segment to zoom in')
    expect(wrapper.text()).toContain('Click center to zoom out')
    wrapper.unmount()
  })

  it('does not show breadcrumbs initially', () => {
    const wrapper = mountChart()
    // Only root breadcrumb = showBreadcrumbs is false
    expect(wrapper.findAll('button').length).toBe(0)
    wrapper.unmount()
  })

  it('creates SVG element', async () => {
    const wrapper = await mountAndRender()
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })

  it('renders center circle for navigation', async () => {
    const wrapper = await mountAndRender()
    const circles = wrapper.findAll('circle')
    expect(circles.length).toBeGreaterThanOrEqual(1)
    wrapper.unmount()
  })

  it('renders arc paths for hierarchy', async () => {
    const wrapper = await mountAndRender()
    const paths = wrapper.findAll('path')
    // At least one path per non-root node (A, A1, A2, B, C = 5)
    expect(paths.length).toBeGreaterThanOrEqual(4)
    wrapper.unmount()
  })

  it('renders arc labels', async () => {
    const wrapper = await mountAndRender()
    const texts = wrapper.findAll('text')
    expect(texts.length).toBeGreaterThan(0)
    wrapper.unmount()
  })

  it('uses custom centerLabel', async () => {
    const wrapper = await mountAndRender({ centerLabel: 'Revenue' })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('Revenue')
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
