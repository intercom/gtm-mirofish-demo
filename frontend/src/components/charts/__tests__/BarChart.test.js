import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import BarChart from '../BarChart.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests, setDimensions } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = [
  { label: 'A', value: 10 },
  { label: 'B', value: 20 },
  { label: 'C', value: 30 },
]

const groupedData = [
  { label: 'Q1', values: { open: 34, spam: 8 } },
  { label: 'Q2', values: { open: 45, spam: 12 } },
]

async function mountAndRender(props = {}) {
  const wrapper = mount(BarChart, {
    props: { data: sampleData, ...props },
    attachTo: document.body,
  })
  setDimensions(wrapper.find('.w-full').element)
  await wrapper.setProps({ data: props.data ? [...props.data] : [...sampleData] })
  await nextTick()
  await nextTick()
  return wrapper
}

describe('BarChart', () => {
  it('creates SVG element', async () => {
    const wrapper = await mountAndRender()
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })

  it('does not render SVG with empty data', async () => {
    const wrapper = mount(BarChart, { props: { data: [] }, attachTo: document.body })
    await nextTick()
    expect(wrapper.find('svg').exists()).toBe(false)
    wrapper.unmount()
  })

  it('renders title and subtitle text', async () => {
    const wrapper = await mountAndRender({ title: 'Sales', subtitle: 'Q1 2026' })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('Sales')
    expect(texts).toContain('Q1 2026')
    wrapper.unmount()
  })

  it('creates rect elements for each bar', async () => {
    const wrapper = await mountAndRender()
    const rects = wrapper.findAll('rect')
    expect(rects.length).toBeGreaterThanOrEqual(sampleData.length)
    wrapper.unmount()
  })

  it('renders horizontal bars with background rects', async () => {
    const wrapper = await mountAndRender({ horizontal: true })
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.findAll('rect').length).toBeGreaterThanOrEqual(sampleData.length * 2)
    wrapper.unmount()
  })

  it('renders grouped bars', async () => {
    const wrapper = await mountAndRender({ data: groupedData })
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })

  it('applies custom yFormat to labels', async () => {
    const wrapper = await mountAndRender({ yFormat: (v) => `$${v}` })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts.some(t => t.startsWith('$'))).toBe(true)
    wrapper.unmount()
  })

  it('observes ResizeObserver on mount', () => {
    const wrapper = mount(BarChart, { props: { data: sampleData }, attachTo: document.body })
    expect(mockObserve).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('disconnects ResizeObserver on unmount', () => {
    const wrapper = mount(BarChart, { props: { data: sampleData }, attachTo: document.body })
    wrapper.unmount()
    expect(mockDisconnect).toHaveBeenCalled()
  })

  it('clears previous SVG on re-render', async () => {
    const wrapper = await mountAndRender()
    await wrapper.setProps({ data: [{ label: 'New', value: 5 }] })
    await nextTick()
    await nextTick()
    expect(wrapper.findAll('svg').length).toBeLessThanOrEqual(1)
    wrapper.unmount()
  })
})
