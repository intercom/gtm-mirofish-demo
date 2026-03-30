import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import DonutChart from '../DonutChart.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests, setDimensions } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = [
  { label: 'Segment A', value: 40 },
  { label: 'Segment B', value: 35 },
  { label: 'Segment C', value: 25 },
]

async function mountAndRender(props = {}) {
  const wrapper = mount(DonutChart, {
    props: { data: sampleData, ...props },
    attachTo: document.body,
  })
  setDimensions(wrapper.find('.w-full').element)
  const data = props.data || sampleData
  await wrapper.setProps({ data: [...data] })
  await nextTick()
  await nextTick()
  return wrapper
}

describe('DonutChart', () => {
  it('creates SVG element', async () => {
    const wrapper = await mountAndRender()
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })

  it('does not render SVG with empty data', async () => {
    const wrapper = mount(DonutChart, { props: { data: [] }, attachTo: document.body })
    await nextTick()
    expect(wrapper.find('svg').exists()).toBe(false)
    wrapper.unmount()
  })

  it('creates arc paths for each segment', async () => {
    const wrapper = await mountAndRender()
    const paths = wrapper.findAll('path')
    expect(paths.length).toBeGreaterThanOrEqual(sampleData.length)
    wrapper.unmount()
  })

  it('renders center text when provided', async () => {
    const wrapper = await mountAndRender({ centerText: '100%' })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('100%')
    wrapper.unmount()
  })

  it('renders center subtext when provided', async () => {
    const wrapper = await mountAndRender({ centerText: '100%', centerSubtext: 'Complete' })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('Complete')
    wrapper.unmount()
  })

  it('renders title and subtitle', async () => {
    const wrapper = await mountAndRender({ title: 'Distribution', subtitle: 'By segment' })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('Distribution')
    expect(texts).toContain('By segment')
    wrapper.unmount()
  })

  it('renders label connector lines when showLabels is true', async () => {
    const wrapper = await mountAndRender({ showLabels: true })
    const lines = wrapper.findAll('line')
    expect(lines.length).toBeGreaterThanOrEqual(sampleData.length)
    wrapper.unmount()
  })

  it('observes ResizeObserver on mount', () => {
    const wrapper = mount(DonutChart, { props: { data: sampleData }, attachTo: document.body })
    expect(mockObserve).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('disconnects ResizeObserver on unmount', () => {
    const wrapper = mount(DonutChart, { props: { data: sampleData }, attachTo: document.body })
    wrapper.unmount()
    expect(mockDisconnect).toHaveBeenCalled()
  })
})
