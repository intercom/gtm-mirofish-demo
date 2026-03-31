import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CalendarHeatmap from '../CalendarHeatmap.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = [
  { date: '2026-03-01', value: 5 },
  { date: '2026-03-02', value: 10 },
  { date: '2026-03-15', value: 3 },
]

function mountChart(props = {}) {
  return mount(CalendarHeatmap, {
    props: { data: sampleData, ...props },
    attachTo: document.body,
  })
}

describe('CalendarHeatmap', () => {
  it('shows empty state when data is empty', () => {
    const wrapper = mount(CalendarHeatmap, { props: { data: [] }, attachTo: document.body })
    expect(wrapper.text()).toContain('No activity data available')
    wrapper.unmount()
  })

  it('does not show empty state when data is provided', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).not.toContain('No activity data available')
    wrapper.unmount()
  })

  it('renders chart container when data is provided', () => {
    const wrapper = mountChart()
    expect(wrapper.find('.relative.overflow-x-auto').exists()).toBe(true)
    wrapper.unmount()
  })

  it('renders legend with Less/More labels', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).toContain('Less')
    expect(wrapper.text()).toContain('More')
    wrapper.unmount()
  })

  it('renders default title via slot', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).toContain('Activity')
    wrapper.unmount()
  })

  it('supports blue color scheme', () => {
    const wrapper = mountChart({ colorScheme: 'blue' })
    expect(wrapper.find('.relative.overflow-x-auto').exists()).toBe(true)
    wrapper.unmount()
  })

  it('supports green color scheme', () => {
    const wrapper = mountChart({ colorScheme: 'green' })
    expect(wrapper.find('.relative.overflow-x-auto').exists()).toBe(true)
    wrapper.unmount()
  })

  it('supports orange color scheme', () => {
    const wrapper = mountChart({ colorScheme: 'orange' })
    expect(wrapper.find('.relative.overflow-x-auto').exists()).toBe(true)
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
