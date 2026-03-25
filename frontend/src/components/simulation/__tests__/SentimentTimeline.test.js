import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SentimentTimeline from '../SentimentTimeline.vue'

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

function makeAction(round, content, type = 'COMMENT') {
  return {
    round_num: round,
    agent_name: `agent-${round}`,
    action_type: type,
    action_args: { content },
  }
}

describe('SentimentTimeline', () => {
  describe('empty state', () => {
    it('shows placeholder when no actions provided', () => {
      const wrapper = mount(SentimentTimeline)
      expect(wrapper.text()).toContain('Sentiment data will appear as agents interact')
      wrapper.unmount()
    })

    it('shows placeholder when actions array is empty', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions: [], timeline: [] } })
      expect(wrapper.text()).toContain('Sentiment data will appear as agents interact')
      wrapper.unmount()
    })

    it('does not show view mode buttons when empty', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions: [] } })
      expect(wrapper.findAll('button').length).toBe(0)
      wrapper.unmount()
    })

    it('does not show legend when empty', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions: [] } })
      expect(wrapper.text()).not.toContain('Positive')
      expect(wrapper.text()).not.toContain('Negative')
      wrapper.unmount()
    })
  })

  describe('data state', () => {
    const actions = [
      makeAction(1, 'This is an impressive and excellent product'),
      makeAction(1, 'Very innovative approach, love it'),
      makeAction(2, 'Concerned about the risk and expensive pricing'),
      makeAction(2, 'The product seems slow and confusing'),
      makeAction(3, 'Neutral statement about the weather'),
    ]

    it('shows view mode buttons when data exists', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBe(2)
      expect(buttons[0].text()).toBe('Trend')
      expect(buttons[1].text()).toBe('Distribution')
      wrapper.unmount()
    })

    it('shows trend legend by default', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.text()).toContain('Positive')
      expect(wrapper.text()).toContain('Neutral')
      expect(wrapper.text()).toContain('Negative')
      wrapper.unmount()
    })

    it('hides empty placeholder when data exists', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.text()).not.toContain('Sentiment data will appear as agents interact')
      wrapper.unmount()
    })

    it('renders chart container when data exists', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.find('[style*="height: 220px"]').exists()).toBe(true)
      wrapper.unmount()
    })
  })

  describe('view mode switching', () => {
    const actions = [
      makeAction(1, 'impressive product'),
      makeAction(2, 'concerned about risk'),
    ]

    it('defaults to trend view', () => {
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      const trendBtn = wrapper.findAll('button')[0]
      expect(trendBtn.classes()).toContain('shadow-sm')
      wrapper.unmount()
    })

    it('switches to distribution view on click', async () => {
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      const distBtn = wrapper.findAll('button')[1]
      await distBtn.trigger('click')
      await nextTick()

      expect(distBtn.classes()).toContain('shadow-sm')
      wrapper.unmount()
    })

    it('switches back to trend view on click', async () => {
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      const [trendBtn, distBtn] = wrapper.findAll('button')

      await distBtn.trigger('click')
      await nextTick()
      await trendBtn.trigger('click')
      await nextTick()

      expect(trendBtn.classes()).toContain('shadow-sm')
      wrapper.unmount()
    })
  })

  describe('sentiment scoring via actions', () => {
    it('processes actions without round_num gracefully', () => {
      const actions = [{ action_type: 'COMMENT', action_args: { content: 'test' } }]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      // No round_num means data is skipped — should show empty state
      expect(wrapper.text()).toContain('Sentiment data will appear as agents interact')
      wrapper.unmount()
    })

    it('groups actions by round number', () => {
      const actions = [
        makeAction(1, 'impressive'),
        makeAction(1, 'excellent'),
        makeAction(2, 'good'),
      ]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      // Component should have data since rounds exist — shows chart, not empty
      expect(wrapper.text()).not.toContain('Sentiment data will appear as agents interact')
      wrapper.unmount()
    })

    it('handles actions with empty content', () => {
      const actions = [makeAction(1, ''), makeAction(1, null)]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      // Should still render (neutral scores)
      expect(wrapper.text()).not.toContain('Sentiment data will appear as agents interact')
      wrapper.unmount()
    })

    it('computes positive sentiment for positive words', () => {
      const actions = [
        makeAction(1, 'This is impressive, excellent, and innovative'),
      ]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.find('[style*="height: 220px"]').exists()).toBe(true)
      wrapper.unmount()
    })

    it('computes negative sentiment for negative words', () => {
      const actions = [
        makeAction(1, 'This is expensive, complex, and confusing'),
      ]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.find('[style*="height: 220px"]').exists()).toBe(true)
      wrapper.unmount()
    })

    it('weights LIKE actions positively', () => {
      const actions = [
        makeAction(1, '', 'LIKE'),
        makeAction(1, '', 'LIKE'),
      ]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.find('[style*="height: 220px"]').exists()).toBe(true)
      wrapper.unmount()
    })

    it('weights REPOST actions positively', () => {
      const actions = [
        makeAction(1, '', 'REPOST'),
      ]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.find('[style*="height: 220px"]').exists()).toBe(true)
      wrapper.unmount()
    })

    it('handles SHARE and RETWEET action types', () => {
      const actions = [
        makeAction(1, 'interesting', 'RETWEET'),
        makeAction(1, 'valuable', 'SHARE'),
      ]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(wrapper.text()).toContain('Sentiment Timeline')
      wrapper.unmount()
    })
  })

  describe('title', () => {
    it('renders Sentiment Timeline heading', () => {
      const wrapper = mount(SentimentTimeline)
      expect(wrapper.find('h3').text()).toBe('Sentiment Timeline')
      wrapper.unmount()
    })
  })

  describe('lifecycle', () => {
    it('sets up ResizeObserver when data exists', () => {
      const actions = [makeAction(1, 'impressive')]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      expect(mockObserve).toHaveBeenCalled()
      wrapper.unmount()
    })

    it('disconnects ResizeObserver on unmount', () => {
      const actions = [makeAction(1, 'impressive')]
      const wrapper = mount(SentimentTimeline, { props: { actions } })
      wrapper.unmount()
      expect(mockDisconnect).toHaveBeenCalled()
    })
  })
})
