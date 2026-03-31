import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import PolarizationGauge from '../PolarizationGauge.vue'

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

function makeAction(round, agentName, content, topic = 'Product') {
  return {
    round_num: round,
    agent_name: agentName,
    agent_id: agentName,
    action_type: 'CREATE_POST',
    action_args: { content, topic },
    platform: 'twitter',
  }
}

describe('PolarizationGauge', () => {
  describe('heading', () => {
    it('shows "Polarization Index" heading', () => {
      const wrapper = mount(PolarizationGauge)
      expect(wrapper.find('h3').text()).toBe('Polarization Index')
      wrapper.unmount()
    })
  })

  describe('empty state', () => {
    it('shows empty state when no actions', () => {
      const wrapper = mount(PolarizationGauge)
      expect(wrapper.text()).toContain('Polarization data will appear as agents interact')
      wrapper.unmount()
    })
  })

  describe('data state', () => {
    const mixedActions = [
      makeAction(1, 'Alice', 'impressive innovative excellent'),
      makeAction(1, 'Bob', 'concerned skeptical expensive'),
    ]

    it('shows gauge area when actions provided', () => {
      const wrapper = mount(PolarizationGauge, { props: { actions: mixedActions } })
      expect(wrapper.text()).not.toContain('Polarization data will appear as agents interact')
      wrapper.unmount()
    })

    it('shows polarization description label', () => {
      const wrapper = mount(PolarizationGauge, { props: { actions: mixedActions } })
      expect(wrapper.text()).toMatch(/polarization/)
      wrapper.unmount()
    })

    it('shows "View breakdown" button when data exists', () => {
      const wrapper = mount(PolarizationGauge, { props: { actions: mixedActions } })
      const btn = wrapper.findAll('button').find(b => b.text().includes('View breakdown'))
      expect(btn).toBeTruthy()
      wrapper.unmount()
    })

    it('hides breakdown by default', () => {
      const wrapper = mount(PolarizationGauge, { props: { actions: mixedActions } })
      expect(wrapper.text()).not.toContain('Most Divisive Topics')
      wrapper.unmount()
    })

    it('toggles breakdown on button click', async () => {
      const wrapper = mount(PolarizationGauge, { props: { actions: mixedActions } })
      const btn = wrapper.findAll('button').find(b => b.text().includes('View breakdown'))
      await btn.trigger('click')
      await nextTick()
      expect(wrapper.text()).toContain('Hide details')
      wrapper.unmount()
    })

    it('shows "Hide details" text after toggling', async () => {
      const wrapper = mount(PolarizationGauge, { props: { actions: mixedActions } })
      const btn = wrapper.findAll('button').find(b => b.text().includes('View breakdown'))
      await btn.trigger('click')
      await nextTick()
      expect(wrapper.findAll('button').find(b => b.text().includes('Hide details'))).toBeTruthy()
      wrapper.unmount()
    })
  })

  describe('sparkline', () => {
    it('shows trend sparkline when 2+ rounds exist', () => {
      const actions = [
        makeAction(1, 'Alice', 'impressive innovative'),
        makeAction(1, 'Bob', 'concerned skeptical'),
        makeAction(2, 'Alice', 'great excellent'),
        makeAction(2, 'Bob', 'expensive complex'),
      ]
      const wrapper = mount(PolarizationGauge, { props: { actions } })
      expect(wrapper.text()).toContain('Trend over rounds')
      wrapper.unmount()
    })
  })

  describe('polarization computation', () => {
    it('computes zero polarization when all agents agree', () => {
      const actions = [
        makeAction(1, 'Alice', 'impressive innovative excellent'),
        makeAction(1, 'Bob', 'impressive innovative excellent'),
        makeAction(1, 'Carol', 'impressive innovative excellent'),
      ]
      const wrapper = mount(PolarizationGauge, { props: { actions } })
      expect(wrapper.text()).toContain('Low polarization')
      wrapper.unmount()
    })

    it('computes high polarization when agents disagree', () => {
      const actions = [
        makeAction(1, 'Alice', 'impressive innovative excellent amazing love great'),
        makeAction(1, 'Bob', 'concerned skeptical expensive complex difficult worried'),
      ]
      const wrapper = mount(PolarizationGauge, { props: { actions } })
      expect(wrapper.text()).toMatch(/Moderate|High|Extreme/)
      wrapper.unmount()
    })
  })

  describe('lifecycle', () => {
    it('sets up ResizeObserver on mount', () => {
      const actions = [makeAction(1, 'Alice', 'impressive')]
      const wrapper = mount(PolarizationGauge, { props: { actions } })
      expect(mockObserve).toHaveBeenCalled()
      wrapper.unmount()
    })
  })
})
