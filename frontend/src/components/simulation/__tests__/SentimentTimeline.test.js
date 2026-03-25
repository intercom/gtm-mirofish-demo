import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SentimentTimeline from '../SentimentTimeline.vue'

// D3 needs element dimensions for rendering; stub clientWidth via ResizeObserver
beforeEach(() => {
  vi.stubGlobal('ResizeObserver', class {
    observe() {}
    disconnect() {}
  })
})

const sampleActions = [
  { round_num: 1, agent_name: 'Agent A', agent_id: 1, action_type: 'REPLY', action_args: { content: 'This is impressive and great work' } },
  { round_num: 1, agent_name: 'Agent B', agent_id: 2, action_type: 'LIKE_POST', action_args: {} },
  { round_num: 2, agent_name: 'Agent A', agent_id: 1, action_type: 'REPLY', action_args: { content: 'I am skeptical and concerned about risk' } },
  { round_num: 2, agent_name: 'Agent C', agent_id: 3, action_type: 'CREATE_POST', action_args: { content: 'Neutral statement here' } },
  { round_num: 3, agent_name: 'Agent B', agent_id: 2, action_type: 'REPOST', action_args: {} },
]

function mountTimeline(props = {}) {
  return mount(SentimentTimeline, {
    props: {
      actions: [],
      timeline: [],
      ...props,
    },
  })
}

describe('SentimentTimeline', () => {
  it('renders empty state when no actions provided', () => {
    const wrapper = mountTimeline()
    expect(wrapper.text()).toContain('Sentiment data will appear as agents interact')
  })

  it('hides empty state when actions are provided', () => {
    const wrapper = mountTimeline({ actions: sampleActions })
    expect(wrapper.text()).not.toContain('Sentiment data will appear as agents interact')
  })

  it('renders the title', () => {
    const wrapper = mountTimeline()
    expect(wrapper.text()).toContain('Sentiment Timeline')
  })

  it('shows view mode toggle buttons when data exists', () => {
    const wrapper = mountTimeline({ actions: sampleActions })
    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(2)
    expect(buttons[0].text()).toBe('Trend')
    expect(buttons[1].text()).toBe('Distribution')
  })

  it('hides view mode toggle when no data', () => {
    const wrapper = mountTimeline()
    expect(wrapper.findAll('button')).toHaveLength(0)
  })

  it('defaults to trend view mode', () => {
    const wrapper = mountTimeline({ actions: sampleActions })
    const trendBtn = wrapper.findAll('button')[0]
    expect(trendBtn.classes()).toContain('shadow-sm')
  })

  it('switches to distribution view on click', async () => {
    const wrapper = mountTimeline({ actions: sampleActions })
    const distBtn = wrapper.findAll('button')[1]
    await distBtn.trigger('click')
    expect(distBtn.classes()).toContain('shadow-sm')
  })

  it('shows trend legend items by default', () => {
    const wrapper = mountTimeline({ actions: sampleActions })
    const text = wrapper.text()
    expect(text).toContain('Positive')
    expect(text).toContain('Neutral')
    expect(text).toContain('Negative')
  })

  it('shows distribution legend items after switching', async () => {
    const wrapper = mountTimeline({ actions: sampleActions })
    await wrapper.findAll('button')[1].trigger('click')
    const text = wrapper.text()
    expect(text).toContain('Positive')
    expect(text).toContain('Neutral')
    expect(text).toContain('Negative')
  })

  it('hides legend when no data', () => {
    const wrapper = mountTimeline()
    const legendDots = wrapper.findAll('.rounded-full')
    expect(legendDots).toHaveLength(0)
  })

  it('renders chart container ref div when actions exist', () => {
    const wrapper = mountTimeline({ actions: sampleActions })
    const chartDiv = wrapper.find('[style*="height: 220px"]')
    expect(chartDiv.exists()).toBe(true)
  })

  it('filters out actions with no round_num from sentiment computation', () => {
    const actionsWithMissing = [
      { round_num: 1, agent_name: 'A', agent_id: 1, action_type: 'REPLY', action_args: { content: 'great' } },
      { agent_name: 'B', agent_id: 2, action_type: 'LIKE', action_args: {} },
    ]
    const wrapper = mountTimeline({ actions: actionsWithMissing })
    expect(wrapper.text()).not.toContain('Sentiment data will appear as agents interact')
  })
})
