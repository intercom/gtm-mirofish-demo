import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ConsensusTracker from '../ConsensusTracker.vue'

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

const consensusData = {
  topics: {
    'Product Value': {
      topic: 'Product Value',
      rounds: [{ round: 1, consensus: 45 }, { round: 2, consensus: 55 }],
      resolved: true,
      resolved_at: 2,
    },
    'Migration Risk': {
      topic: 'Migration Risk',
      rounds: [{ round: 1, consensus: 30 }, { round: 2, consensus: 40 }],
      resolved: false,
    },
  },
  summary: { resolved_count: 1, open_count: 1, total_topics: 2 },
}

describe('ConsensusTracker', () => {
  describe('heading and subtitle', () => {
    it('shows "Consensus Tracker" heading', () => {
      const wrapper = mount(ConsensusTracker)
      expect(wrapper.find('h3').text()).toBe('Consensus Tracker')
      wrapper.unmount()
    })

    it('shows subtitle text', () => {
      const wrapper = mount(ConsensusTracker)
      expect(wrapper.text()).toContain('Group agreement per topic over simulation rounds')
      wrapper.unmount()
    })
  })

  describe('empty state', () => {
    it('shows empty state when no consensusData', () => {
      const wrapper = mount(ConsensusTracker)
      expect(wrapper.text()).toContain('Consensus data will appear as agents interact')
      wrapper.unmount()
    })

    it('shows empty state when consensusData is null', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData: null } })
      expect(wrapper.text()).toContain('Consensus data will appear as agents interact')
      wrapper.unmount()
    })
  })

  describe('data state', () => {
    it('shows chart container when topics exist', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData } })
      expect(wrapper.find('[style*="height: 260px"]').exists()).toBe(true)
      wrapper.unmount()
    })

    it('shows resolved count', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData } })
      expect(wrapper.text()).toContain('1 resolved')
      wrapper.unmount()
    })

    it('shows open count', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData } })
      expect(wrapper.text()).toContain('1 open')
      wrapper.unmount()
    })

    it('shows topic names in legend', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData } })
      expect(wrapper.text()).toContain('Product Value')
      expect(wrapper.text()).toContain('Migration Risk')
      wrapper.unmount()
    })

    it('shows green resolved indicator for resolved topics', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData } })
      const legendItems = wrapper.findAll('.flex.items-center.gap-1\\.5')
      const productValueItem = legendItems.find(el => el.text().includes('Product Value'))
      expect(productValueItem.text()).toContain('\u25CF')
      wrapper.unmount()
    })

    it('hides summary stats when total_topics is 0', () => {
      const emptyData = {
        topics: {},
        summary: { resolved_count: 0, open_count: 0, total_topics: 0 },
      }
      const wrapper = mount(ConsensusTracker, { props: { consensusData: emptyData } })
      expect(wrapper.text()).not.toContain('resolved')
      expect(wrapper.text()).not.toContain('open')
      wrapper.unmount()
    })
  })

  describe('lifecycle', () => {
    it('sets up ResizeObserver on mount', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData } })
      expect(mockObserve).toHaveBeenCalled()
      wrapper.unmount()
    })

    it('disconnects ResizeObserver on unmount', () => {
      const wrapper = mount(ConsensusTracker, { props: { consensusData } })
      wrapper.unmount()
      expect(mockDisconnect).toHaveBeenCalled()
    })
  })
})
