import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ParallelCoordinates from '../ParallelCoordinates.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = [
  { speed: 80, power: 70, accuracy: 90, group: 'A' },
  { speed: 60, power: 85, accuracy: 75, group: 'B' },
  { speed: 70, power: 60, accuracy: 80, group: 'A' },
]

const sampleDimensions = [
  { key: 'speed', label: 'Speed' },
  { key: 'power', label: 'Power' },
  { key: 'accuracy', label: 'Accuracy' },
]

function mountChart(props = {}) {
  return mount(ParallelCoordinates, {
    props: { data: sampleData, dimensions: sampleDimensions, ...props },
    attachTo: document.body,
  })
}

describe('ParallelCoordinates', () => {
  it('shows empty state with no data', () => {
    const wrapper = mount(ParallelCoordinates, {
      props: { data: [], dimensions: sampleDimensions },
      attachTo: document.body,
    })
    expect(wrapper.text()).toContain('No data available')
    wrapper.unmount()
  })

  it('shows empty state with no dimensions', () => {
    const wrapper = mount(ParallelCoordinates, {
      props: { data: sampleData, dimensions: [] },
      attachTo: document.body,
    })
    expect(wrapper.text()).toContain('No data available')
    wrapper.unmount()
  })

  it('renders chart container when data is provided', () => {
    const wrapper = mountChart()
    expect(wrapper.find('.relative.w-full').exists()).toBe(true)
    wrapper.unmount()
  })

  it('renders default header text', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).toContain('Parallel Coordinates')
    wrapper.unmount()
  })

  it('renders color legend when colorBy is set', () => {
    const wrapper = mountChart({ colorBy: 'group' })
    // Should display category values in the legend
    const legendItems = wrapper.findAll('.flex.flex-wrap span')
    expect(legendItems.length).toBeGreaterThanOrEqual(2) // A and B
    wrapper.unmount()
  })

  it('does not render legend without colorBy', () => {
    const wrapper = mountChart()
    // Legend div uses v-if="colorBy && colorCategories.length"
    // Without colorBy, it should not be rendered
    const legendContainer = wrapper.findAll('.flex.flex-wrap.items-center.gap-3.mt-3')
    expect(legendContainer.length).toBe(0)
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
