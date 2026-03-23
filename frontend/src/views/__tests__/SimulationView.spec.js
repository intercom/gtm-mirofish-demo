import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SimulationView from '../SimulationView.vue'

const mockRunStatus = {
  success: true,
  data: {
    runner_status: 'running',
    current_round: 5,
    total_rounds: 144,
    progress_percent: 3.5,
    total_actions_count: 150,
    twitter_actions_count: 80,
    reddit_actions_count: 70,
  },
}

const mockActions = {
  success: true,
  data: [
    { round_num: 5, platform: 'twitter', agent_id: 1, agent_name: 'VP of Support', action_type: 'CREATE_POST', action_args: { content: 'Exploring new support tools' }, success: true },
    { round_num: 5, platform: 'reddit', agent_id: 2, agent_name: 'CX Director', action_type: 'REPLY_POST', action_args: { content: 'Great insight on that thread' }, success: true },
    { round_num: 4, platform: 'twitter', agent_id: 3, agent_name: 'IT Manager', action_type: 'LIKE_POST', action_args: {}, success: true },
    { round_num: 4, platform: 'twitter', agent_id: 1, agent_name: 'VP of Support', action_type: 'REPOST', action_args: {}, success: true },
    { round_num: 3, platform: 'reddit', agent_id: 4, agent_name: 'Product Lead', action_type: 'LIKE_POST', action_args: {}, success: true },
    { round_num: 3, platform: 'twitter', agent_id: 5, agent_name: 'Sales Rep', action_type: 'CREATE_POST', action_args: { content: 'New quarter strategy thoughts' }, success: true },
  ],
}

function createFetchMock(statusOverride = {}, actionsOverride = null) {
  return vi.fn((url) => {
    if (url.includes('/run-status')) {
      const data = { ...mockRunStatus.data, ...statusOverride }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, data }),
      })
    }
    if (url.includes('/actions')) {
      const response = actionsOverride ?? mockActions
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(response),
      })
    }
    return Promise.resolve({ ok: false })
  })
}

function mountView(props = {}) {
  return mount(SimulationView, {
    props: { taskId: 'test-sim-123', ...props },
    global: {
      stubs: { RouterLink: { template: '<a><slot /></a>' } },
    },
  })
}

async function mountAndFlush(props = {}) {
  const wrapper = mountView(props)
  await flushPromises()
  return wrapper
}

describe('SimulationView', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    global.fetch = createFetchMock()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('renders header with task ID', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('Live Simulation')
    expect(wrapper.text()).toContain('test-sim-123')
  })

  it('shows Running status badge when simulation is running', async () => {
    const wrapper = await mountAndFlush()
    const badge = wrapper.find('.rounded-full.text-xs')
    expect(badge.text()).toContain('Running')
    expect(badge.classes()).toContain('bg-green-100')
  })

  it('shows Building status badge for idle/starting states', async () => {
    global.fetch = createFetchMock({ runner_status: 'starting' })
    const wrapper = await mountAndFlush()
    const badge = wrapper.find('.rounded-full.text-xs')
    expect(badge.text()).toContain('Building')
    expect(badge.classes()).toContain('bg-yellow-100')
  })

  it('shows Completed status badge and report link', async () => {
    global.fetch = createFetchMock({ runner_status: 'completed' })
    const wrapper = await mountAndFlush()
    const badge = wrapper.find('.rounded-full.text-xs')
    expect(badge.text()).toContain('Completed')
    const reportLink = wrapper.find('a')
    expect(reportLink.text()).toContain('Generate Report')
  })

  it('displays progress bar with correct percentage', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('Round 5 of 144')
    expect(wrapper.text()).toContain('4%')
    const progressBar = wrapper.find('.bg-\\[\\#2068FF\\].rounded-full.transition-all')
    expect(progressBar.attributes('style')).toContain('width: 3.5%')
  })

  it('displays total actions from run-status', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('150')
    expect(wrapper.text()).toContain('Total Actions')
  })

  it('computes type counts from actions data', async () => {
    const wrapper = await mountAndFlush()
    const text = wrapper.text()
    expect(text).toContain('Replies')
    expect(text).toContain('Likes')
    expect(text).toContain('Reposts')
  })

  it('renders activity feed with agent actions', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('VP of Support')
    expect(wrapper.text()).toContain('posted')
    expect(wrapper.text()).toContain('Exploring new support tools')
    expect(wrapper.text()).toContain('CX Director')
    expect(wrapper.text()).toContain('replied')
  })

  it('filters activities by platform tab', async () => {
    const wrapper = await mountAndFlush()
    const twitterTab = wrapper.findAll('button').find(b => b.text() === 'Twitter')
    await twitterTab.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('VP of Support')
    expect(wrapper.text()).not.toContain('CX Director')
    expect(wrapper.text()).not.toContain('Product Lead')
  })

  it('shows Both Platforms tab as default active', async () => {
    const wrapper = await mountAndFlush()
    const bothTab = wrapper.findAll('button').find(b => b.text() === 'Both Platforms')
    expect(bothTab.classes()).toContain('bg-[#2068FF]')
  })

  it('shows chart placeholder when less than 2 rounds', async () => {
    global.fetch = createFetchMock({}, {
      success: true,
      data: [
        { round_num: 1, platform: 'twitter', agent_id: 1, agent_name: 'A', action_type: 'CREATE_POST', action_args: {}, success: true },
      ],
    })
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('Chart appears after 2+ rounds')
  })

  it('renders SVG chart when timeline has 2+ rounds', async () => {
    const wrapper = await mountAndFlush()
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
    const paths = svg.findAll('path')
    expect(paths.length).toBe(2)
  })

  it('polls run-status and actions APIs on mount', async () => {
    await mountAndFlush()
    const statusCalls = global.fetch.mock.calls.filter(c => c[0].includes('/run-status'))
    const actionCalls = global.fetch.mock.calls.filter(c => c[0].includes('/actions'))
    expect(statusCalls.length).toBeGreaterThanOrEqual(1)
    expect(actionCalls.length).toBeGreaterThanOrEqual(1)
  })

  it('stops polling when simulation completes', async () => {
    global.fetch = createFetchMock({ runner_status: 'completed' })
    await mountAndFlush()
    const callCountAfterStop = global.fetch.mock.calls.length

    vi.advanceTimersByTime(6000)
    await flushPromises()
    expect(global.fetch.mock.calls.length).toBe(callCountAfterStop)
  })

  it('shows waiting message when no activities', async () => {
    global.fetch = createFetchMock({}, { success: true, data: [] })
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('Waiting for agent actions...')
  })

  it('displays platform indicator on activity items', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('R5')
  })

  it('shows pulsing indicator when running', async () => {
    const wrapper = await mountAndFlush()
    const pulse = wrapper.find('.animate-pulse')
    expect(pulse.exists()).toBe(true)
  })

  it('hides report link when not completed', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).not.toContain('Generate Report')
  })

  it('continues polling while simulation is running', async () => {
    await mountAndFlush()
    const initialCalls = global.fetch.mock.calls.length

    vi.advanceTimersByTime(3000)
    await flushPromises()

    expect(global.fetch.mock.calls.length).toBeGreaterThan(initialCalls)
  })
})
