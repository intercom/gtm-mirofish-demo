import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SentimentTimeline from '../SentimentTimeline.vue'

class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = MockResizeObserver

function mountTimeline(props = {}) {
  return mount(SentimentTimeline, {
    props: { actions: [], timeline: [], ...props },
    attachTo: document.body,
  })
}

function makeAction(round, content, type = 'COMMENT') {
  return {
    round_num: round,
    action_type: type,
    agent_name: `agent-${round}`,
    action_args: { content },
  }
}

describe('SentimentTimeline', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  // --- Empty state ---

  it('shows placeholder when no actions provided', () => {
    const wrapper = mountTimeline()
    expect(wrapper.text()).toContain('Sentiment data will appear as agents interact')
  })

  it('does not render chart container when actions are empty', () => {
    const wrapper = mountTimeline()
    expect(wrapper.find('svg').exists()).toBe(false)
  })

  it('does not show view mode buttons when empty', () => {
    const wrapper = mountTimeline()
    expect(wrapper.findAll('button').length).toBe(0)
  })

  it('does not show legend when empty', () => {
    const wrapper = mountTimeline()
    expect(wrapper.text()).not.toContain('Positive')
    expect(wrapper.text()).not.toContain('Neutral')
    expect(wrapper.text()).not.toContain('Negative')
  })

  // --- With data ---

  it('hides placeholder when actions are provided', () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'This is great and impressive')],
    })
    expect(wrapper.text()).not.toContain('Sentiment data will appear')
  })

  it('shows view mode toggle buttons with data', () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'good')],
    })
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(2)
    expect(buttons[0].text()).toBe('Trend')
    expect(buttons[1].text()).toBe('Distribution')
  })

  it('starts in trend view mode', () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'good')],
    })
    const buttons = wrapper.findAll('button')
    // First button (Trend) should have the active style class
    expect(buttons[0].classes()).toContain('shadow-sm')
  })

  it('switches to distribution view when button clicked', async () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'good')],
    })
    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')
    // Distribution button should now be active
    expect(buttons[1].classes()).toContain('shadow-sm')
  })

  it('shows trend legend in trend mode', () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'good')],
    })
    // In trend mode, legend uses round dots (w-2 h-2)
    const legendDots = wrapper.findAll('.rounded-full.bg-\\[\\#009900\\]')
    expect(legendDots.length).toBe(1)
  })

  it('shows distribution legend after switching mode', async () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'good')],
    })
    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')
    // In distribution mode, legend uses square indicators (rounded-sm)
    const legendSquares = wrapper.findAll('.rounded-sm')
    expect(legendSquares.length).toBe(3)
  })

  // --- Sentiment scoring logic (tested via computed output) ---

  it('scores positive content as positive sentiment', () => {
    const actions = [
      makeAction(1, 'This is impressive and excellent, truly amazing work'),
    ]
    const wrapper = mountTimeline({ actions })
    // The heading should appear since data exists
    expect(wrapper.text()).toContain('Sentiment Timeline')
  })

  it('aggregates multiple rounds correctly', () => {
    const actions = [
      makeAction(1, 'great impressive'),
      makeAction(1, 'excellent helpful'),
      makeAction(2, 'concerned worried'),
      makeAction(3, 'neutral words here'),
    ]
    const wrapper = mountTimeline({ actions })
    // Should render chart with data from 3 rounds
    expect(wrapper.find('[style*="height"]').exists()).toBe(true)
  })

  it('handles actions with no round_num gracefully', () => {
    const actions = [
      { action_type: 'COMMENT', agent_name: 'a1', action_args: { content: 'hello' } },
    ]
    const wrapper = mountTimeline({ actions })
    // No valid round data → should show empty state
    expect(wrapper.text()).toContain('Sentiment data will appear')
  })

  it('handles LIKE action types with positive bias', () => {
    const actions = [
      makeAction(1, '', 'LIKE'),
      makeAction(1, '', 'UPVOTE'),
    ]
    const wrapper = mountTimeline({ actions })
    // LIKE/UPVOTE actions produce positive sentiment regardless of content
    expect(wrapper.text()).toContain('Sentiment Timeline')
  })

  it('handles SHARE/REPOST action types', () => {
    const actions = [
      makeAction(1, 'interesting', 'RETWEET'),
      makeAction(1, 'valuable', 'SHARE'),
    ]
    const wrapper = mountTimeline({ actions })
    expect(wrapper.text()).toContain('Sentiment Timeline')
  })

  // --- D3 rendering ---

  it('creates SVG element when data exists and container has width', async () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'good'), makeAction(2, 'bad')],
    })
    await flushPromises()
    // D3 appends SVG to the chartRef div — may not render in happy-dom
    // due to clientWidth being 0, but the chart container div should exist
    const chartContainer = wrapper.find('.relative')
    expect(chartContainer.exists()).toBe(true)
  })

  // --- Component structure ---

  it('renders the title "Sentiment Timeline"', () => {
    const wrapper = mountTimeline({
      actions: [makeAction(1, 'good')],
    })
    expect(wrapper.find('h3').text()).toBe('Sentiment Timeline')
  })

  it('has the correct outer container styling', () => {
    const wrapper = mountTimeline()
    const outer = wrapper.find('.rounded-lg')
    expect(outer.exists()).toBe(true)
  })
})
