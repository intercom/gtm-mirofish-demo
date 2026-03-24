import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import SimulationView from '../views/SimulationView.vue'

// Mock fetch globally
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// Mock canvas context (jsdom doesn't support canvas)
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
  fill: vi.fn(),
  closePath: vi.fn(),
  fillText: vi.fn(),
  scale: vi.fn(),
  set strokeStyle(_) {},
  set fillStyle(_) {},
  set lineWidth(_) {},
  set font(_) {},
  set textAlign(_) {},
}))

function makeRunStatusResponse(overrides = {}) {
  return {
    success: true,
    data: {
      simulation_id: 'sim_abc123',
      runner_status: 'running',
      current_round: 5,
      total_rounds: 24,
      progress_percent: 20.8,
      simulated_hours: 10,
      total_simulation_hours: 48,
      twitter_current_round: 5,
      reddit_current_round: 4,
      twitter_simulated_hours: 10,
      reddit_simulated_hours: 8,
      twitter_running: true,
      reddit_running: true,
      twitter_completed: false,
      reddit_completed: false,
      twitter_actions_count: 42,
      reddit_actions_count: 38,
      total_actions_count: 80,
      started_at: '2025-12-01T10:00:00',
      updated_at: '2025-12-01T10:30:00',
      ...overrides,
    },
  }
}

function makeDetailResponse(actions = []) {
  return {
    success: true,
    data: {
      recent_actions: actions,
      all_actions: actions,
    },
  }
}

function makeTimelineResponse(rounds = []) {
  return {
    success: true,
    data: {
      rounds_count: rounds.length,
      timeline: rounds,
    },
  }
}

const sampleActions = [
  { round_num: 5, platform: 'twitter', agent_id: 1, agent_name: 'Alice', action_type: 'CREATE_POST', action_args: { content: 'Hello world!' }, success: true },
  { round_num: 5, platform: 'reddit', agent_id: 2, agent_name: 'Bob', action_type: 'LIKE_POST', action_args: {}, success: true },
  { round_num: 4, platform: 'twitter', agent_id: 3, agent_name: 'Charlie', action_type: 'REPLY', action_args: { content: 'Great point!' }, success: true },
  { round_num: 4, platform: 'reddit', agent_id: 4, agent_name: 'Diana', action_type: 'REPOST', action_args: {}, success: true },
]

const sampleTimeline = [
  { round_num: 1, twitter_actions: 5, reddit_actions: 3 },
  { round_num: 2, twitter_actions: 8, reddit_actions: 6 },
  { round_num: 3, twitter_actions: 12, reddit_actions: 9 },
]

function setupFetchMock(runStatus = {}, actions = sampleActions, timeline = sampleTimeline) {
  mockFetch.mockImplementation((url) => {
    if (url.includes('/run-status/detail')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(makeDetailResponse(actions)) })
    }
    if (url.includes('/run-status')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(makeRunStatusResponse(runStatus)) })
    }
    if (url.includes('/timeline')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(makeTimelineResponse(timeline)) })
    }
    return Promise.resolve({ ok: false })
  })
}

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/simulation/:taskId', name: 'simulation', component: SimulationView, props: true },
      { path: '/report/:taskId', name: 'report', component: { template: '<div>Report</div>' } },
    ],
  })
}

async function mountComponent(taskId = 'sim_abc123', runStatus = {}) {
  setupFetchMock(runStatus)

  const router = createTestRouter()
  await router.push(`/simulation/${taskId}`)
  await router.isReady()

  const wrapper = mount(SimulationView, {
    props: { taskId },
    global: { plugins: [router] },
  })

  await flushPromises()
  return wrapper
}

describe('SimulationView', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the page title and task ID', async () => {
    const wrapper = await mountComponent('sim_test123')
    expect(wrapper.text()).toContain('Live Simulation')
    expect(wrapper.text()).toContain('sim_test123')
  })

  it('displays status badge for running simulation', async () => {
    const wrapper = await mountComponent()
    expect(wrapper.text()).toContain('Running')
  })

  it('shows completed status when simulation finishes', async () => {
    const wrapper = await mountComponent('sim_abc123', { runner_status: 'completed' })
    expect(wrapper.text()).toContain('Completed')
  })

  it('shows building status for starting/idle simulations', async () => {
    const wrapper = await mountComponent('sim_abc123', { runner_status: 'starting' })
    expect(wrapper.text()).toContain('Building')
  })

  it('displays metrics cards with correct values', async () => {
    const wrapper = await mountComponent()
    // Total actions from run-status endpoint
    expect(wrapper.text()).toContain('80')
    expect(wrapper.text()).toContain('Total Actions')
    expect(wrapper.text()).toContain('Replies')
    expect(wrapper.text()).toContain('Likes')
    expect(wrapper.text()).toContain('Reposts')
    expect(wrapper.text()).toContain('Current Round')
  })

  it('shows progress bar with percentage', async () => {
    const wrapper = await mountComponent()
    expect(wrapper.text()).toContain('Round 5 / 24')
    expect(wrapper.text()).toContain('20.8%')
    const bar = wrapper.find('[style*="width"]')
    expect(bar.exists()).toBe(true)
  })

  it('renders platform tabs', async () => {
    const wrapper = await mountComponent()
    expect(wrapper.text()).toContain('Both Platforms')
    expect(wrapper.text()).toContain('Twitter')
    expect(wrapper.text()).toContain('Reddit')
  })

  it('filters activity feed by platform when tab clicked', async () => {
    const wrapper = await mountComponent()
    // Find the Twitter tab button (second tab)
    const tabs = wrapper.findAll('button')
    const twitterTab = tabs.find(t => t.text() === 'Twitter')
    expect(twitterTab).toBeDefined()

    await twitterTab.trigger('click')
    await flushPromises()

    // Activity feed should only show twitter actions
    const feedItems = wrapper.findAll('.flex.items-start.gap-2\\.5')
    for (const item of feedItems) {
      expect(item.text()).not.toContain('Reddit')
    }
  })

  it('displays agent activity feed with action details', async () => {
    const wrapper = await mountComponent()
    expect(wrapper.text()).toContain('Agent Activity Feed')
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('Bob')
    expect(wrapper.text()).toContain('Hello world!')
  })

  it('shows placeholder when no actions exist', async () => {
    setupFetchMock({}, [])
    const router = createTestRouter()
    await router.push('/simulation/sim_empty')
    await router.isReady()

    const wrapper = mount(SimulationView, {
      props: { taskId: 'sim_empty' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Real-time agent actions will appear here')
  })

  it('shows Generate Report button when completed', async () => {
    const wrapper = await mountComponent('sim_abc123', { runner_status: 'completed' })
    expect(wrapper.text()).toContain('Generate Report')
    const link = wrapper.find('a[href="/report/sim_abc123"]')
    expect(link.exists()).toBe(true)
  })

  it('hides Generate Report button when running', async () => {
    const wrapper = await mountComponent()
    const link = wrapper.find('a[href*="/report/"]')
    expect(link.exists()).toBe(false)
  })

  it('displays platform breakdown cards', async () => {
    const wrapper = await mountComponent()
    expect(wrapper.text()).toContain('42') // twitter actions
    expect(wrapper.text()).toContain('38') // reddit actions
  })

  it('polls run-status at 3-second intervals', async () => {
    await mountComponent()
    const initialCalls = mockFetch.mock.calls.filter(c => c[0].includes('/run-status') && !c[0].includes('/detail')).length

    vi.advanceTimersByTime(3000)
    await flushPromises()

    const afterCalls = mockFetch.mock.calls.filter(c => c[0].includes('/run-status') && !c[0].includes('/detail')).length
    expect(afterCalls).toBeGreaterThan(initialCalls)
  })

  it('polls detail at 5-second intervals', async () => {
    await mountComponent()
    const initialCalls = mockFetch.mock.calls.filter(c => c[0].includes('/detail')).length

    vi.advanceTimersByTime(5000)
    await flushPromises()

    const afterCalls = mockFetch.mock.calls.filter(c => c[0].includes('/detail')).length
    expect(afterCalls).toBeGreaterThan(initialCalls)
  })

  it('handles API errors gracefully', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))
    const router = createTestRouter()
    await router.push('/simulation/sim_err')
    await router.isReady()

    const wrapper = mount(SimulationView, {
      props: { taskId: 'sim_err' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Network error')
  })

  it('categorizes actions correctly into metrics', async () => {
    const actions = [
      { round_num: 1, platform: 'twitter', agent_id: 1, agent_name: 'A', action_type: 'REPLY', action_args: {}, success: true },
      { round_num: 1, platform: 'twitter', agent_id: 2, agent_name: 'B', action_type: 'LIKE_POST', action_args: {}, success: true },
      { round_num: 1, platform: 'twitter', agent_id: 3, agent_name: 'C', action_type: 'LIKE_POST', action_args: {}, success: true },
      { round_num: 1, platform: 'twitter', agent_id: 4, agent_name: 'D', action_type: 'REPOST', action_args: {}, success: true },
    ]
    setupFetchMock({}, actions)
    const router = createTestRouter()
    await router.push('/simulation/sim_metrics')
    await router.isReady()

    const wrapper = mount(SimulationView, {
      props: { taskId: 'sim_metrics' },
      global: { plugins: [router] },
    })
    await flushPromises()

    // Replies card should show 1, Likes should show 2, Reposts should show 1
    const cards = wrapper.findAll('.grid.grid-cols-2 > div')
    // Card order: Total Actions, Replies, Likes, Reposts, Current Round
    const repliesCard = cards[1]
    const likesCard = cards[2]
    const repostsCard = cards[3]

    expect(repliesCard.text()).toContain('1')
    expect(likesCard.text()).toContain('2')
    expect(repostsCard.text()).toContain('1')
  })
})
