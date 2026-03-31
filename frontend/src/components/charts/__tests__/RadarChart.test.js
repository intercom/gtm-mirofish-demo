import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import RadarChart from '../RadarChart.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests, setDimensions } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = [
  { label: 'Speed', values: { 'Team A': 80, 'Team B': 65 } },
  { label: 'Power', values: { 'Team A': 90, 'Team B': 70 } },
  { label: 'Accuracy', values: { 'Team A': 60, 'Team B': 85 } },
  { label: 'Stamina', values: { 'Team A': 75, 'Team B': 80 } },
]

function mountChart(props = {}) {
  return mount(RadarChart, {
    props: { data: sampleData, ...props },
    attachTo: document.body,
  })
}

describe('RadarChart', () => {
  it('shows empty state when data is empty', () => {
    const wrapper = mountChart({ data: [] })
    expect(wrapper.text()).toContain('No data available')
    wrapper.unmount()
  })

  it('does not show empty state when data is provided', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).not.toContain('No data available')
    wrapper.unmount()
  })

  it('creates SVG element', async () => {
    const wrapper = mountChart()
    const chartEl = wrapper.element.children[0]
    setDimensions(chartEl)
    // Trigger watcher via data change (maxValue default is 100, so changing it wouldn't help)
    await wrapper.setProps({ data: [...sampleData] })
    await nextTick()
    await nextTick()
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })

  it('renders grid circles based on levels prop', async () => {
    const wrapper = mountChart({ levels: 4 })
    const chartEl = wrapper.element.children[0]
    setDimensions(chartEl)
    await wrapper.setProps({ data: [...sampleData] })
    await nextTick()
    await nextTick()
    const circles = wrapper.findAll('circle')
    expect(circles.length).toBeGreaterThanOrEqual(4)
    wrapper.unmount()
  })

  it('renders legend buttons for multiple series', () => {
    const wrapper = mountChart()
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(2)
    expect(buttons[0].text()).toContain('Team A')
    expect(buttons[1].text()).toContain('Team B')
    wrapper.unmount()
  })

  it('hides legend when showLegend is false', () => {
    const wrapper = mountChart({ showLegend: false })
    expect(wrapper.findAll('button').length).toBe(0)
    wrapper.unmount()
  })

  it('does not show legend for single series', () => {
    const singleData = sampleData.map(d => ({
      label: d.label,
      values: { 'Team A': d.values['Team A'] },
    }))
    const wrapper = mountChart({ data: singleData })
    // showLegend && seriesNames.length > 1 → false
    expect(wrapper.findAll('button').length).toBe(0)
    wrapper.unmount()
  })

  it('toggles series visibility on legend click', async () => {
    const wrapper = mountChart()
    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
    await nextTick()
    expect(wrapper.findAll('button')[0].classes()).toContain('opacity-50')
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
