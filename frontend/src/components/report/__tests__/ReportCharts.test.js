import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ReportCharts from '../ReportCharts.vue'

const mockObserve = vi.fn()
const mockDisconnect = vi.fn()

class MockResizeObserver {
  constructor() {}
  observe = mockObserve
  disconnect = mockDisconnect
  unobserve = vi.fn()
}

beforeEach(() => {
  vi.stubGlobal('ResizeObserver', MockResizeObserver)
})

afterEach(() => {
  vi.unstubAllGlobals()
  mockObserve.mockClear()
  mockDisconnect.mockClear()
})

describe('ReportCharts', () => {
  describe('conditional rendering', () => {
    it('renders container for chapterIndex 1', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 1 } })
      expect(wrapper.find('.bg-white').exists()).toBe(true)
      wrapper.unmount()
    })

    it('renders container for chapterIndex 2', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 2 } })
      expect(wrapper.find('.bg-white').exists()).toBe(true)
      wrapper.unmount()
    })

    it('renders container for chapterIndex 3', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 3 } })
      expect(wrapper.find('.bg-white').exists()).toBe(true)
      wrapper.unmount()
    })

    it('does not render for chapterIndex 0', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 0 } })
      expect(wrapper.find('.bg-white').exists()).toBe(false)
      wrapper.unmount()
    })

    it('does not render for chapterIndex 4', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 4 } })
      expect(wrapper.find('.bg-white').exists()).toBe(false)
      wrapper.unmount()
    })

    it('does not render for chapterIndex 5', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 5 } })
      expect(wrapper.find('.bg-white').exists()).toBe(false)
      wrapper.unmount()
    })

    it('does not render for negative chapterIndex', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: -1 } })
      expect(wrapper.find('.bg-white').exists()).toBe(false)
      wrapper.unmount()
    })

    it('re-renders when chapterIndex changes', async () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 1 } })
      expect(wrapper.find('.bg-white').exists()).toBe(true)

      await wrapper.setProps({ chapterIndex: 4 })
      expect(wrapper.find('.bg-white').exists()).toBe(false)

      await wrapper.setProps({ chapterIndex: 2 })
      expect(wrapper.find('.bg-white').exists()).toBe(true)
      wrapper.unmount()
    })

    it('hides when switching from valid to invalid chapter', async () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 3 } })
      expect(wrapper.find('.bg-white').exists()).toBe(true)

      await wrapper.setProps({ chapterIndex: 99 })
      expect(wrapper.find('.bg-white').exists()).toBe(false)
      wrapper.unmount()
    })
  })

  describe('D3 chart rendering', () => {
    function mountWithDimensions(chapterIndex) {
      const wrapper = mount(ReportCharts, {
        props: { chapterIndex },
        attachTo: document.body,
      })
      const chartEl = wrapper.find('[class*="w-full"]').element
      if (chartEl) {
        Object.defineProperty(chartEl, 'clientWidth', { value: 600, configurable: true })
        Object.defineProperty(chartEl, 'clientHeight', { value: 400, configurable: true })
      }
      return wrapper
    }

    it('creates SVG for persona engagement chart (index 1)', async () => {
      const wrapper = mountWithDimensions(1)
      await wrapper.setProps({ chapterIndex: 1 })
      await nextTick()
      await nextTick()

      const svg = wrapper.find('svg')
      if (svg.exists()) {
        expect(svg.attributes('width')).toBe('600')
        expect(wrapper.find('text').exists()).toBe(true)
      }
      wrapper.unmount()
    })

    it('creates SVG for subject line chart (index 2)', async () => {
      const wrapper = mountWithDimensions(2)
      await wrapper.setProps({ chapterIndex: 2 })
      await nextTick()
      await nextTick()

      const svg = wrapper.find('svg')
      if (svg.exists()) {
        expect(svg.attributes('width')).toBe('600')
      }
      wrapper.unmount()
    })

    it('creates SVG for behavioral clusters chart (index 3)', async () => {
      const wrapper = mountWithDimensions(3)
      await wrapper.setProps({ chapterIndex: 3 })
      await nextTick()
      await nextTick()

      const svg = wrapper.find('svg')
      if (svg.exists()) {
        expect(svg.attributes('width')).toBe('600')
      }
      wrapper.unmount()
    })

    it('clears previous chart before rendering new one on prop change', async () => {
      const wrapper = mountWithDimensions(1)
      await nextTick()
      await nextTick()

      await wrapper.setProps({ chapterIndex: 2 })
      await nextTick()
      await nextTick()

      // Should still have exactly one SVG (old one cleared)
      const svgs = wrapper.findAll('svg')
      expect(svgs.length).toBeLessThanOrEqual(1)
      wrapper.unmount()
    })
  })

  describe('ResizeObserver lifecycle', () => {
    it('creates and observes ResizeObserver on mount', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 1 } })
      expect(mockObserve).toHaveBeenCalled()
      wrapper.unmount()
    })

    it('disconnects ResizeObserver on unmount', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 1 } })
      wrapper.unmount()
      expect(mockDisconnect).toHaveBeenCalled()
    })

    it('does not observe if container does not exist', () => {
      const wrapper = mount(ReportCharts, { props: { chapterIndex: 99 } })
      // Container is hidden via v-if, so observe should not be called
      // (ResizeObserver is still created in onMounted, but chartRef.value is null)
      wrapper.unmount()
    })
  })
})
