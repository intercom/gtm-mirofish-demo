import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import LineChart from '../LineChart.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests, setDimensions } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const singleSeries = [
  { name: 'Revenue', points: [{ x: 'Jan', y: 100 }, { x: 'Feb', y: 200 }, { x: 'Mar', y: 150 }] },
]

const multiSeries = [
  { name: 'Revenue', points: [{ x: 'Jan', y: 100 }, { x: 'Feb', y: 200 }] },
  { name: 'Costs', points: [{ x: 'Jan', y: 80 }, { x: 'Feb', y: 90 }] },
]

async function mountAndRender(props = {}) {
  const wrapper = mount(LineChart, {
    props: { series: singleSeries, ...props },
    attachTo: document.body,
  })
  setDimensions(wrapper.find('.w-full').element)
  const series = props.series || singleSeries
  await wrapper.setProps({ series: series.map(s => ({ ...s })) })
  await nextTick()
  await nextTick()
  return wrapper
}

describe('LineChart', () => {
  it('creates SVG element', async () => {
    const wrapper = await mountAndRender()
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })

  it('does not render SVG with empty series', async () => {
    const wrapper = mount(LineChart, { props: { series: [] }, attachTo: document.body })
    await nextTick()
    expect(wrapper.find('svg').exists()).toBe(false)
    wrapper.unmount()
  })

  it('renders path elements for each series', async () => {
    const wrapper = await mountAndRender({ series: multiSeries })
    const paths = wrapper.findAll('path')
    expect(paths.length).toBeGreaterThanOrEqual(multiSeries.length)
    wrapper.unmount()
  })

  it('renders title and subtitle', async () => {
    const wrapper = await mountAndRender({ title: 'Trends', subtitle: 'Monthly' })
    const texts = wrapper.findAll('text').map(t => t.text())
    expect(texts).toContain('Trends')
    expect(texts).toContain('Monthly')
    wrapper.unmount()
  })

  it('renders dots when showDots is true', async () => {
    const wrapper = await mountAndRender({ showDots: true })
    const circles = wrapper.findAll('circle')
    expect(circles.length).toBeGreaterThanOrEqual(singleSeries[0].points.length)
    wrapper.unmount()
  })

  it('does not render dots when showDots is false', async () => {
    const wrapper = await mountAndRender({ showDots: false })
    expect(wrapper.findAll('circle').length).toBe(0)
    wrapper.unmount()
  })

  it('renders area fill when showArea is true', async () => {
    const wrapper = await mountAndRender({ showArea: true })
    const paths = wrapper.findAll('path')
    const areaPath = paths.filter(p => p.attributes('fill') && p.attributes('fill') !== 'none')
    expect(areaPath.length).toBeGreaterThanOrEqual(1)
    wrapper.unmount()
  })

  it('observes ResizeObserver on mount', () => {
    const wrapper = mount(LineChart, { props: { series: singleSeries }, attachTo: document.body })
    expect(mockObserve).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('disconnects ResizeObserver on unmount', () => {
    const wrapper = mount(LineChart, { props: { series: singleSeries }, attachTo: document.body })
    wrapper.unmount()
    expect(mockDisconnect).toHaveBeenCalled()
  })
})
