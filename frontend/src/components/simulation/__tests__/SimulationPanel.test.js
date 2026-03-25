import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import SimulationPanel from '../SimulationPanel.vue'

// --- Canvas & ResizeObserver stubs ---

const canvasCtx = {
  clearRect: vi.fn(), beginPath: vi.fn(), moveTo: vi.fn(), lineTo: vi.fn(),
  stroke: vi.fn(), fill: vi.fn(), closePath: vi.fn(), fillText: vi.fn(),
  scale: vi.fn(), strokeStyle: '', fillStyle: '', lineWidth: 1, font: '',
  textAlign: '', arc: vi.fn(),
}

beforeEach(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => canvasCtx)
  HTMLCanvasElement.prototype.getBoundingClientRect = vi.fn(() => ({
    width: 400, height: 200, top: 0, left: 0, right: 400, bottom: 200,
  }))
  vi.stubGlobal('ResizeObserver', class {
    observe() {}
    disconnect() {}
  })
  vi.stubGlobal('requestAnimationFrame', vi.fn((cb) => 1))
  vi.stubGlobal('cancelAnimationFrame', vi.fn())
})

afterEach(() => {
  vi.restoreAllMocks()
})

// --- Mock polling factory ---

function makePolling(overrides = {}) {
  return {
    graphStatus: ref(overrides.graphStatus ?? 'complete'),
    graphProgress: ref(overrides.graphProgress ?? 100),
    graphData: ref(overrides.graphData ?? { nodes: [], edges: [] }),
    graphId: ref(overrides.graphId ?? 'g-1'),
    graphTask: ref(overrides.graphTask ?? null),
    isDemoFallback: ref(overrides.isDemoFallback ?? false),
    runStatus: ref(overrides.runStatus ?? null),
    simStatus: ref(overrides.simStatus ?? 'idle'),
    recentActions: ref(overrides.recentActions ?? []),
    timeline: ref(overrides.timeline ?? []),
  }
}

function mountPanel(props = {}, pollingOverrides = {}) {
  const polling = makePolling(pollingOverrides)
  return mount(SimulationPanel, {
    props: { taskId: 'task-abc', ...props },
    global: {
      provide: { polling },
      stubs: {
        RouterLink: { template: '<a :to="to"><slot /></a>', props: ['to'] },
        SentimentTimeline: { template: '<div data-testid="sentiment-stub" />' },
        ShimmerCard: { template: '<div data-testid="shimmer" />' },
      },
    },
  })
}

// --- Sample data ---

const runningStatus = {
  runner_status: 'running',
  current_round: 5,
  total_rounds: 24,
  progress_percent: 21,
  total_actions_count: 150,
  twitter_actions_count: 80,
  reddit_actions_count: 70,
}

const completedStatus = {
  ...runningStatus,
  runner_status: 'completed',
  progress_percent: 100,
  current_round: 24,
}

const sampleActions = [
  { round_num: 5, platform: 'twitter', agent_id: 1, agent_name: 'VP Sales', action_type: 'CREATE_POST', action_args: { content: 'New strategy' } },
  { round_num: 5, platform: 'reddit', agent_id: 2, agent_name: 'CX Lead', action_type: 'REPLY_POST', action_args: { content: 'Great insight' } },
  { round_num: 4, platform: 'twitter', agent_id: 3, agent_name: 'IT Manager', action_type: 'LIKE_POST', action_args: {} },
  { round_num: 4, platform: 'twitter', agent_id: 1, agent_name: 'VP Sales', action_type: 'REPOST', action_args: {} },
  { round_num: 3, platform: 'reddit', agent_id: 4, agent_name: 'Product Lead', action_type: 'UPVOTE', action_args: {} },
]

// ======================================
// Tests
// ======================================

describe('SimulationPanel', () => {
  // --- Building / empty state ---

  describe('building state', () => {
    it('shows preparing message when graph is building', () => {
      const wrapper = mountPanel({}, { graphStatus: 'building', runStatus: null })
      expect(wrapper.text()).toContain('Preparing Simulation')
      expect(wrapper.text()).toContain('knowledge graph is ready')
    })

    it('renders heartbeat canvas during build', () => {
      const wrapper = mountPanel({}, { graphStatus: 'building' })
      const canvases = wrapper.findAll('canvas')
      expect(canvases.length).toBeGreaterThanOrEqual(1)
    })
  })

  // --- Status badge computation ---

  describe('status badges', () => {
    it('shows Building for idle runner_status', () => {
      const wrapper = mountPanel({}, { runStatus: { runner_status: 'idle' } })
      expect(wrapper.text()).toContain('Building')
    })

    it('shows Building for starting runner_status', () => {
      const wrapper = mountPanel({}, { runStatus: { runner_status: 'starting' } })
      expect(wrapper.text()).toContain('Building')
    })

    it('shows Running for running runner_status', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      expect(wrapper.text()).toContain('Running')
    })

    it('shows Completed for completed runner_status', () => {
      const wrapper = mountPanel({}, { runStatus: completedStatus })
      expect(wrapper.text()).toContain('Completed')
    })

    it('shows Failed for failed runner_status', () => {
      const wrapper = mountPanel({}, { runStatus: { runner_status: 'failed' } })
      expect(wrapper.text()).toContain('Failed')
    })
  })

  // --- Header ---

  describe('header', () => {
    it('displays task ID', () => {
      const wrapper = mountPanel({ taskId: 'sim-xyz' }, { runStatus: runningStatus })
      expect(wrapper.text()).toContain('sim-xyz')
    })

    it('displays Live Simulation title', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      expect(wrapper.text()).toContain('Live Simulation')
    })
  })

  // --- Progress bar ---

  describe('progress bar', () => {
    it('shows round and percentage info', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      expect(wrapper.text()).toContain('Round 5 / 24')
      expect(wrapper.text()).toContain('21%')
    })

    it('renders progress bar with correct width', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      const progressBar = wrapper.find('.rounded-full.transition-all')
      expect(progressBar.attributes('style')).toContain('width: 21%')
    })

    it('uses success color when completed', () => {
      const wrapper = mountPanel({}, { runStatus: completedStatus })
      const bars = wrapper.findAll('.rounded-full.transition-all')
      const completedBar = bars.find(b => b.classes().includes('bg-[var(--color-success)]'))
      expect(completedBar).toBeTruthy()
    })
  })

  // --- Metrics cards ---

  describe('metrics', () => {
    it('displays total actions from runStatus', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      expect(wrapper.text()).toContain('150')
      expect(wrapper.text()).toContain('Total Actions')
    })

    it('shows shimmer cards when no runStatus in building state', () => {
      const wrapper = mountPanel({}, { runStatus: null })
      const shimmers = wrapper.findAll('[data-testid="shimmer"]')
      expect(shimmers).toHaveLength(5)
    })

    it('computes reply count from actions', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('Replies')
    })

    it('computes like count from actions', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('Likes')
    })

    it('computes repost count from actions', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('Reposts')
    })

    it('shows current round in metrics', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      expect(wrapper.text()).toContain('Current Round')
    })
  })

  // --- Platform tabs ---

  describe('platform filtering', () => {
    it('renders all three platform tabs', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      expect(wrapper.text()).toContain('Both Platforms')
      expect(wrapper.text()).toContain('Twitter')
      expect(wrapper.text()).toContain('Reddit')
    })

    it('defaults to Both Platforms', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      const bothBtn = wrapper.findAll('button').find(b => b.text() === 'Both Platforms')
      expect(bothBtn.classes()).toContain('shadow-sm')
    })

    it('filters actions when Twitter tab is clicked', async () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      const twitterBtn = wrapper.findAll('button').find(b => b.text() === 'Twitter')
      await twitterBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('VP Sales')
      expect(wrapper.text()).not.toContain('CX Lead')
    })

    it('filters actions when Reddit tab is clicked', async () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      const redditBtn = wrapper.findAll('button').find(b => b.text() === 'Reddit')
      await redditBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('CX Lead')
      expect(wrapper.text()).not.toContain('IT Manager')
    })
  })

  // --- Activity feed ---

  describe('activity feed', () => {
    it('shows empty state when no actions', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus, recentActions: [] })
      expect(wrapper.text()).toContain('Real-time agent actions will appear here')
    })

    it('renders agent names in feed', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('VP Sales')
      expect(wrapper.text()).toContain('CX Lead')
      expect(wrapper.text()).toContain('IT Manager')
    })

    it('renders action content in feed', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('New strategy')
      expect(wrapper.text()).toContain('Great insight')
    })

    it('shows action count in feed header', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('5 actions')
    })

    it('renders round number badge', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('R5')
    })

    it('shows platform badges on activity items', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      expect(wrapper.text()).toContain('Twitter')
      expect(wrapper.text()).toContain('Reddit')
    })
  })

  // --- Chart ---

  describe('engagement timeline chart', () => {
    it('shows waiting message when no timeline data in building state', () => {
      const wrapper = mountPanel({}, { runStatus: { runner_status: 'starting' }, timeline: [] })
      expect(wrapper.text()).toContain('Waiting for simulation to start')
    })

    it('shows "No timeline data yet" when running with empty timeline', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus, timeline: [] })
      expect(wrapper.text()).toContain('No timeline data yet')
    })

    it('renders canvas when timeline has data', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        timeline: [
          { round_num: 1, twitter_actions: 5, reddit_actions: 3 },
          { round_num: 2, twitter_actions: 8, reddit_actions: 6 },
        ],
      })
      const canvas = wrapper.find('canvas')
      expect(canvas.exists()).toBe(true)
    })

    it('shows chart legend when timeline has data', () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        timeline: [{ round_num: 1, twitter_actions: 5, reddit_actions: 3 }],
      })
      expect(wrapper.text()).toContain('Twitter')
      expect(wrapper.text()).toContain('Reddit')
    })
  })

  // --- Platform breakdown cards ---

  describe('platform breakdown', () => {
    it('shows Twitter and Reddit breakdown cards', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      const text = wrapper.text()
      expect(text).toContain('80')
      expect(text).toContain('70')
    })
  })

  // --- Report button ---

  describe('report link', () => {
    it('shows Generate Report link when completed', () => {
      const wrapper = mountPanel({ taskId: 'task-99' }, { runStatus: completedStatus })
      expect(wrapper.text()).toContain('Generate Report')
      const link = wrapper.findAll('a').find(a => a.text().includes('Generate Report'))
      expect(link.attributes('to')).toBe('/report/task-99')
    })

    it('hides Generate Report when not completed', () => {
      const wrapper = mountPanel({}, { runStatus: runningStatus })
      expect(wrapper.text()).not.toContain('Generate Report')
    })
  })

  // --- Agent detail panel ---

  describe('agent detail panel', () => {
    it('opens agent panel when agent name is clicked', async () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      const agentButton = wrapper.findAll('button').find(b => b.text().includes('VP Sales'))
      await agentButton.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('VP Sales')
      expect(wrapper.text()).toContain('Recent Activity')
    })

    it('shows agent action stats in detail panel', async () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      const agentButton = wrapper.findAll('button').find(b => b.text().includes('VP Sales'))
      await agentButton.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Actions')
      expect(wrapper.text()).toContain('Twitter')
      expect(wrapper.text()).toContain('Reddit')
    })

    it('closes agent panel when close button is clicked', async () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      const agentButton = wrapper.findAll('button').find(b => b.text().includes('VP Sales'))
      await agentButton.trigger('click')
      await flushPromises()
      expect(wrapper.text()).toContain('Recent Activity')

      const closeBtn = wrapper.findAll('button').find(b => b.text() === '\u00D7')
      await closeBtn.trigger('click')
      await flushPromises()
      expect(wrapper.text()).not.toContain('Recent Activity')
    })

    it('closes agent panel when overlay is clicked', async () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      const agentButton = wrapper.findAll('button').find(b => b.text().includes('VP Sales'))
      await agentButton.trigger('click')
      await flushPromises()

      const overlay = wrapper.find('.fixed.inset-0')
      await overlay.trigger('click')
      await flushPromises()
      expect(wrapper.text()).not.toContain('Recent Activity')
    })

    it('shows engagement badge in agent panel', async () => {
      const wrapper = mountPanel({}, {
        runStatus: runningStatus,
        recentActions: sampleActions,
      })
      const agentButton = wrapper.findAll('button').find(b => b.text().includes('VP Sales'))
      await agentButton.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Moderate')
    })
  })
})
