import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ReportCharts from '../ReportCharts.vue'

class MockResizeObserver {
  constructor(cb) { this._cb = cb }
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = MockResizeObserver

function mountChart(chapterIndex) {
  return mount(ReportCharts, {
    props: { chapterIndex },
    attachTo: document.body,
  })
}

describe('ReportCharts', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  // --- Conditional rendering ---

  it('renders chart container for chapter 1', () => {
    const wrapper = mountChart(1)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)
  })

  it('renders chart container for chapter 2', () => {
    const wrapper = mountChart(2)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)
  })

  it('renders chart container for chapter 3', () => {
    const wrapper = mountChart(3)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)
  })

  it('does not render for chapter 0', () => {
    const wrapper = mountChart(0)
    expect(wrapper.find('.rounded-lg').exists()).toBe(false)
    expect(wrapper.html()).toBe('<!--v-if-->')
  })

  it('does not render for chapter 4', () => {
    const wrapper = mountChart(4)
    expect(wrapper.find('.rounded-lg').exists()).toBe(false)
  })

  it('does not render for chapter 5', () => {
    const wrapper = mountChart(5)
    expect(wrapper.find('.rounded-lg').exists()).toBe(false)
  })

  it('does not render for negative chapter index', () => {
    const wrapper = mountChart(-1)
    expect(wrapper.find('.rounded-lg').exists()).toBe(false)
  })

  // --- Chart container structure ---

  it('has a chartRef div inside the container', () => {
    const wrapper = mountChart(1)
    const chartDiv = wrapper.find('.w-full')
    expect(chartDiv.exists()).toBe(true)
  })

  it('applies white background and border styling', () => {
    const wrapper = mountChart(1)
    const container = wrapper.find('.bg-white')
    expect(container.exists()).toBe(true)
  })

  // --- Re-rendering on prop change ---

  it('re-renders when chapterIndex changes', async () => {
    const wrapper = mountChart(1)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)

    await wrapper.setProps({ chapterIndex: 4 })
    expect(wrapper.find('.rounded-lg').exists()).toBe(false)

    await wrapper.setProps({ chapterIndex: 2 })
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)
  })

  it('hides when switching from valid to invalid chapter', async () => {
    const wrapper = mountChart(3)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)

    await wrapper.setProps({ chapterIndex: 99 })
    expect(wrapper.find('.rounded-lg').exists()).toBe(false)
  })

  // --- D3 SVG generation (when clientWidth > 0) ---
  // Note: In happy-dom, clientWidth is typically 0 so D3 render functions
  // bail out early. These tests verify the component doesn't crash.

  it('does not crash when rendering chapter 1 with zero-width container', () => {
    const wrapper = mountChart(1)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)
  })

  it('does not crash when rendering chapter 2 with zero-width container', () => {
    const wrapper = mountChart(2)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)
  })

  it('does not crash when rendering chapter 3 with zero-width container', () => {
    const wrapper = mountChart(3)
    expect(wrapper.find('.rounded-lg').exists()).toBe(true)
  })
})
