import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SmallMultiples from '../SmallMultiples.vue'
import { mockObserve, mockDisconnect, setupChartTests, cleanupChartTests } from './chart-test-helpers'

beforeEach(() => setupChartTests())
afterEach(() => cleanupChartTests())

const sampleData = [
  { title: 'Dataset 1', values: [{ x: 1, y: 10 }, { x: 2, y: 20 }, { x: 3, y: 15 }] },
  { title: 'Dataset 2', values: [{ x: 1, y: 30 }, { x: 2, y: 25 }, { x: 3, y: 35 }] },
  { title: 'Dataset 3', values: [{ x: 1, y: 5 }, { x: 2, y: 15 }, { x: 3, y: 10 }] },
]

function mountChart(props = {}) {
  return mount(SmallMultiples, {
    props: { data: sampleData, ...props },
    attachTo: document.body,
  })
}

describe('SmallMultiples', () => {
  it('shows empty state when data is empty', () => {
    const wrapper = mount(SmallMultiples, { props: { data: [] }, attachTo: document.body })
    expect(wrapper.text()).toContain('No data available')
    wrapper.unmount()
  })

  it('renders panels for each dataset', async () => {
    const wrapper = mountChart()
    const panels = wrapper.findAll('.sm-panel')
    expect(panels.length).toBe(sampleData.length)
    await nextTick()
    wrapper.unmount()
  })

  it('uses correct grid columns', async () => {
    const wrapper = mountChart({ columns: 2 })
    const grid = wrapper.find('.grid')
    expect(grid.attributes('style')).toContain('grid-template-columns: repeat(2, 1fr)')
    await nextTick()
    wrapper.unmount()
  })

  it('limits grid columns to data length', async () => {
    const wrapper = mountChart({ columns: 5 })
    const grid = wrapper.find('.grid')
    // min(5, 3) = 3
    expect(grid.attributes('style')).toContain('grid-template-columns: repeat(3, 1fr)')
    await nextTick()
    wrapper.unmount()
  })

  it('defaults to 3 columns', async () => {
    const wrapper = mountChart()
    const grid = wrapper.find('.grid')
    expect(grid.attributes('style')).toContain('grid-template-columns: repeat(3, 1fr)')
    await nextTick()
    wrapper.unmount()
  })

  it('renders with bar chart type', async () => {
    const wrapper = mountChart({ chartType: 'bar' })
    expect(wrapper.findAll('.sm-panel').length).toBe(sampleData.length)
    await nextTick()
    wrapper.unmount()
  })

  it('renders with area chart type', async () => {
    const wrapper = mountChart({ chartType: 'area' })
    expect(wrapper.findAll('.sm-panel').length).toBe(sampleData.length)
    await nextTick()
    wrapper.unmount()
  })

  it('observes ResizeObserver on mount', async () => {
    const wrapper = mountChart()
    expect(mockObserve).toHaveBeenCalled()
    await nextTick()
    wrapper.unmount()
  })

  it('disconnects ResizeObserver on unmount', async () => {
    const wrapper = mountChart()
    await nextTick()
    wrapper.unmount()
    expect(mockDisconnect).toHaveBeenCalled()
  })
})
