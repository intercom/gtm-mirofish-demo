import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ChordDiagram from '../ChordDiagram.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleMatrix = [
  [0, 5, 3],
  [5, 0, 8],
  [3, 8, 0],
]
const sampleLabels = ['Sales', 'Marketing', 'Engineering']

function mountChart(props = {}) {
  return mount(ChordDiagram, {
    props: { matrix: sampleMatrix, labels: sampleLabels, ...props },
    attachTo: document.body,
  })
}

describe('ChordDiagram', () => {
  it('shows empty state with no matrix data', () => {
    const wrapper = mount(ChordDiagram, {
      props: { matrix: [], labels: [] },
      attachTo: document.body,
    })
    expect(wrapper.text()).toContain('No flow data available')
    wrapper.unmount()
  })

  it('does not show empty state when data is provided', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).not.toContain('No flow data available')
    wrapper.unmount()
  })

  it('renders chart container when data is provided', () => {
    const wrapper = mountChart()
    expect(wrapper.find('.relative.w-full').exists()).toBe(true)
    wrapper.unmount()
  })

  it('renders default title via slot', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).toContain('Communication Flow')
    wrapper.unmount()
  })

  it('renders legend with all labels', () => {
    const wrapper = mountChart()
    expect(wrapper.text()).toContain('Sales')
    expect(wrapper.text()).toContain('Marketing')
    expect(wrapper.text()).toContain('Engineering')
    wrapper.unmount()
  })

  it('renders color swatches for each label', () => {
    const wrapper = mountChart()
    const legendSpans = wrapper.findAll('.flex.flex-wrap span')
    expect(legendSpans.length).toBeGreaterThanOrEqual(sampleLabels.length)
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
