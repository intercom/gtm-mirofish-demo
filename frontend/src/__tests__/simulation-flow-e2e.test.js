import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useSimulationPolling } from '../composables/useSimulationPolling'
import { useSimulationStore } from '../stores/simulation'

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  API_BASE: '/api',
}))

vi.mock('../api/graph', () => ({
  graphApi: {
    build: vi.fn(),
    getTask: vi.fn(),
    getData: vi.fn(),
  },
}))

import client from '../api/client'
import { graphApi } from '../api/graph'

const GRAPH_NODES = [
  { id: '1', label: 'VP Support', type: 'Person' },
  { id: '2', label: 'CX Director', type: 'Person' },
  { id: '3', label: 'Intercom', type: 'Product' },
]
const GRAPH_EDGES = [
  { source: '1', target: '3', type: 'EVALUATES' },
  { source: '2', target: '3', type: 'USES' },
]

const SAMPLE_ACTIONS = [
  { round_num: 3, platform: 'twitter', agent_id: 1, agent_name: 'VP Support', action_type: 'CREATE_POST', action_args: { content: 'Exploring Intercom' } },
  { round_num: 3, platform: 'reddit', agent_id: 2, agent_name: 'CX Director', action_type: 'REPLY', action_args: { content: 'Good thread' } },
]

const SAMPLE_TIMELINE = [
  { round_num: 1, twitter_actions: 5, reddit_actions: 3 },
  { round_num: 2, twitter_actions: 8, reddit_actions: 6 },
]

function setupPhasedMocks() {
  let graphPollCount = 0
  let runStatusPollCount = 0

  graphApi.getTask.mockImplementation(() => {
    graphPollCount++
    if (graphPollCount < 3) {
      return Promise.resolve({
        data: {
          success: true,
          data: { status: 'building', progress: graphPollCount * 30, message: 'Building ontology...' },
        },
      })
    }
    return Promise.resolve({
      data: {
        success: true,
        data: { status: 'completed', progress: 100, result: { graph_id: 'graph-abc' } },
      },
    })
  })

  graphApi.getData.mockResolvedValue({
    data: {
      success: true,
      data: { nodes: GRAPH_NODES, edges: GRAPH_EDGES },
    },
  })

  client.get.mockImplementation((url) => {
    if (url.includes('/run-status/detail')) {
      return Promise.resolve({
        data: { success: true, data: { recent_actions: SAMPLE_ACTIONS } },
      })
    }
    if (url.includes('/run-status')) {
      runStatusPollCount++
      if (runStatusPollCount < 2) {
        return Promise.resolve({
          data: { success: true, data: { runner_status: 'idle', current_round: 0, total_rounds: 10, progress_percent: 0, total_actions_count: 0, twitter_actions_count: 0, reddit_actions_count: 0 } },
        })
      }
      if (runStatusPollCount < 5) {
        const round = (runStatusPollCount - 1) * 3
        return Promise.resolve({
          data: {
            success: true,
            data: {
              runner_status: 'running',
              current_round: round,
              total_rounds: 10,
              progress_percent: round * 10,
              total_actions_count: round * 8,
              twitter_actions_count: round * 4,
              reddit_actions_count: round * 4,
            },
          },
        })
      }
      return Promise.resolve({
        data: {
          success: true,
          data: {
            runner_status: 'completed',
            current_round: 10,
            total_rounds: 10,
            progress_percent: 100,
            total_actions_count: 80,
            twitter_actions_count: 42,
            reddit_actions_count: 38,
          },
        },
      })
    }
    if (url.includes('/timeline')) {
      return Promise.resolve({
        data: { success: true, data: { timeline: SAMPLE_TIMELINE } },
      })
    }
    return Promise.reject({ status: 404, message: 'Not found' })
  })
}

function mountPollingWrapper(taskId, pinia) {
  return mount(
    defineComponent({
      setup() {
        const polling = useSimulationPolling(() => taskId)
        return { polling }
      },
      template: '<div></div>',
    }),
    { global: { plugins: [pinia] } },
  )
}

describe('Full Simulation Flow E2E', () => {
  let pinia
  let store

  beforeEach(() => {
    vi.useFakeTimers()
    pinia = createPinia()
    setActivePinia(pinia)
    store = useSimulationStore()
    vi.mocked(graphApi.getTask).mockReset()
    vi.mocked(graphApi.getData).mockReset()
    vi.mocked(client.get).mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('progresses through complete lifecycle: graph build → simulation run → completion', async () => {
    const taskId = 'e2e-flow-task-1'
    setupPhasedMocks()

    store.setScenarioConfig({
      scenarioId: 'competitive_displacement',
      scenarioName: 'Competitive Displacement',
      seedText: 'Test seed...',
      agentCount: 200,
      personas: ['VP of Support', 'CX Director'],
      industries: ['SaaS'],
      duration: 72,
      platformMode: 'parallel',
    })
    store.startGraphBuild(taskId, 'proj-1')
    expect(store.status).toBe('building_graph')

    const wrapper = mountPollingWrapper(taskId, pinia)
    const p = wrapper.vm.polling

    p.start()
    await flushPromises()

    // --- Phase 1: Graph building (first poll) ---
    expect(p.graphStatus.value).toBe('building')
    expect(p.graphProgress.value).toBe(30)

    // Second graph poll at t=2s
    vi.advanceTimersByTime(2000)
    await flushPromises()
    expect(p.graphStatus.value).toBe('building')
    expect(p.graphProgress.value).toBe(60)

    // Third graph poll at t=4s → completes
    vi.advanceTimersByTime(2000)
    await flushPromises()
    expect(p.graphStatus.value).toBe('complete')
    expect(p.graphId.value).toBe('graph-abc')
    expect(p.graphData.value.nodes).toHaveLength(3)
    expect(p.graphData.value.edges).toHaveLength(2)
    expect(graphApi.getData).toHaveBeenCalledWith('graph-abc')

    // --- Phase 2: Simulation running ---
    // Run-status has been polled in parallel; advance to get running state
    vi.advanceTimersByTime(3000)
    await flushPromises()

    expect(p.simStatus.value).toBe('running')
    expect(store.metrics.totalActions).toBeGreaterThan(0)

    // Detail and timeline polling should have started
    expect(p.recentActions.value.length).toBeGreaterThan(0)
    expect(p.timeline.value.length).toBeGreaterThan(0)

    // Advance more — simulation still running, metrics update
    vi.advanceTimersByTime(3000)
    await flushPromises()
    const midMetrics = store.metrics.totalActions
    expect(midMetrics).toBeGreaterThan(0)

    // --- Phase 3: Completion ---
    // Advance enough for run-status to return completed (5th call)
    vi.advanceTimersByTime(6000)
    await flushPromises()

    expect(p.simStatus.value).toBe('completed')
    expect(p.overallPhase.value).toBe('complete')
    expect(store.status).toBe('complete')
    expect(store.progress.percent).toBe(100)
    expect(store.metrics.totalActions).toBe(80)
    expect(store.metrics.twitterActions).toBe(42)
    expect(store.metrics.redditActions).toBe(38)

    // Session run recorded
    expect(store.sessionRuns.length).toBeGreaterThanOrEqual(1)
    const completedRun = store.sessionRuns.find(r => r.id === taskId && r.status === 'completed')
    expect(completedRun).toBeTruthy()
    expect(completedRun.totalActions).toBe(80)

    // Polling should stop — no more API calls after completion
    const callsAfterComplete = client.get.mock.calls.length
    vi.advanceTimersByTime(10000)
    await flushPromises()
    expect(client.get.mock.calls.length).toBe(callsAfterComplete)

    wrapper.unmount()
  })

  it('records scenario metadata in session run on completion', async () => {
    const taskId = 'e2e-metadata-task'
    setupPhasedMocks()

    store.setScenarioConfig({
      scenarioId: 'product_launch',
      scenarioName: 'Product Launch',
      seedText: 'Launch email...',
      agentCount: 300,
      personas: ['VP of Support'],
      industries: ['SaaS', 'Healthcare'],
      duration: 48,
      platformMode: 'twitter',
    })
    store.startGraphBuild(taskId, 'proj-2')

    const wrapper = mountPollingWrapper(taskId, pinia)
    wrapper.vm.polling.start()

    // Fast-forward through entire lifecycle
    for (let i = 0; i < 8; i++) {
      vi.advanceTimersByTime(3000)
      await flushPromises()
    }

    const run = store.sessionRuns.find(r => r.id === taskId)
    expect(run).toBeTruthy()
    expect(run.scenarioId).toBe('product_launch')
    expect(run.scenarioName).toBe('Product Launch')

    wrapper.unmount()
  })

  it('handles graph build failure and stops graph polling', async () => {
    const taskId = 'e2e-fail-graph'
    let callCount = 0

    graphApi.getTask.mockImplementation(() => {
      callCount++
      if (callCount < 2) {
        return Promise.resolve({
          data: { success: true, data: { status: 'building', progress: 20 } },
        })
      }
      return Promise.resolve({
        data: { success: true, data: { status: 'failed', message: 'LLM quota exceeded' } },
      })
    })

    client.get.mockResolvedValue({
      data: { success: true, data: { runner_status: 'idle' } },
    })

    store.startGraphBuild(taskId, 'proj-3')
    const wrapper = mountPollingWrapper(taskId, pinia)
    const p = wrapper.vm.polling

    p.start()
    await flushPromises()
    expect(p.graphStatus.value).toBe('building')

    vi.advanceTimersByTime(2000)
    await flushPromises()

    expect(p.graphStatus.value).toBe('failed')
    expect(p.errorMsg.value).toBe('LLM quota exceeded')

    // Graph polling should stop
    const graphCalls = graphApi.getTask.mock.calls.length
    vi.advanceTimersByTime(10000)
    await flushPromises()
    expect(graphApi.getTask.mock.calls.length).toBe(graphCalls)

    wrapper.unmount()
  })

  it('handles simulation failure and records failed status', async () => {
    const taskId = 'e2e-fail-sim'

    graphApi.getTask.mockResolvedValue({
      data: { success: true, data: { status: 'completed', progress: 100, result: { graph_id: 'g-1' } } },
    })
    graphApi.getData.mockResolvedValue({
      data: { success: true, data: { nodes: [], edges: [] } },
    })

    let runCount = 0
    client.get.mockImplementation((url) => {
      if (url.includes('/run-status/detail')) {
        return Promise.resolve({ data: { success: true, data: { recent_actions: [] } } })
      }
      if (url.includes('/run-status')) {
        runCount++
        if (runCount < 3) {
          return Promise.resolve({
            data: { success: true, data: { runner_status: 'running', current_round: 2, total_rounds: 10, progress_percent: 20, total_actions_count: 10, twitter_actions_count: 5, reddit_actions_count: 5 } },
          })
        }
        return Promise.resolve({
          data: { success: true, data: { runner_status: 'failed', error: 'Agent crash', current_round: 3, total_rounds: 10 } },
        })
      }
      if (url.includes('/timeline')) {
        return Promise.resolve({ data: { success: true, data: { timeline: [] } } })
      }
      return Promise.reject({ status: 404 })
    })

    store.startGraphBuild(taskId, 'proj-4')
    const wrapper = mountPollingWrapper(taskId, pinia)
    const p = wrapper.vm.polling

    p.start()
    await flushPromises()

    // Advance until failure
    for (let i = 0; i < 5; i++) {
      vi.advanceTimersByTime(3000)
      await flushPromises()
    }

    expect(p.simStatus.value).toBe('failed')
    expect(p.errorMsg.value).toBe('Agent crash')

    const failedRun = store.sessionRuns.find(r => r.id === taskId && r.status === 'failed')
    expect(failedRun).toBeTruthy()

    // All sim polling should stop
    const totalCalls = client.get.mock.calls.length
    vi.advanceTimersByTime(10000)
    await flushPromises()
    expect(client.get.mock.calls.length).toBe(totalCalls)

    wrapper.unmount()
  })

  it('falls back to demo mode when backend is unreachable', async () => {
    const taskId = 'e2e-demo-fallback'

    graphApi.getTask.mockRejectedValue({ status: 0, message: 'Network error' })
    client.get.mockRejectedValue({ status: 0, message: 'Network error' })

    store.startGraphBuild(taskId, 'proj-5')
    const wrapper = mountPollingWrapper(taskId, pinia)
    const p = wrapper.vm.polling

    p.start()
    await flushPromises()

    expect(p.isDemoFallback.value).toBe(true)

    // Graph polling should stop after network error
    const graphCalls = graphApi.getTask.mock.calls.length
    vi.advanceTimersByTime(10000)
    await flushPromises()
    expect(graphApi.getTask.mock.calls.length).toBe(graphCalls)

    wrapper.unmount()
  })

  it('starts detail and timeline polling only when simulation is running', async () => {
    const taskId = 'e2e-detail-timing'

    graphApi.getTask.mockResolvedValue({
      data: { success: true, data: { status: 'building', progress: 50 } },
    })

    let runCount = 0
    client.get.mockImplementation((url) => {
      if (url.includes('/run-status/detail')) {
        return Promise.resolve({ data: { success: true, data: { recent_actions: SAMPLE_ACTIONS } } })
      }
      if (url.includes('/run-status')) {
        runCount++
        if (runCount < 3) {
          return Promise.resolve({
            data: { success: true, data: { runner_status: 'idle', current_round: 0, total_rounds: 10, progress_percent: 0, total_actions_count: 0, twitter_actions_count: 0, reddit_actions_count: 0 } },
          })
        }
        return Promise.resolve({
          data: { success: true, data: { runner_status: 'running', current_round: 2, total_rounds: 10, progress_percent: 20, total_actions_count: 15, twitter_actions_count: 8, reddit_actions_count: 7 } },
        })
      }
      if (url.includes('/timeline')) {
        return Promise.resolve({ data: { success: true, data: { timeline: SAMPLE_TIMELINE } } })
      }
      return Promise.reject({ status: 404 })
    })

    const wrapper = mountPollingWrapper(taskId, pinia)
    const p = wrapper.vm.polling

    p.start()
    await flushPromises()

    // Initially, no detail/timeline calls (sim is idle)
    const detailCalls = client.get.mock.calls.filter(c => c[0].includes('/detail')).length
    expect(detailCalls).toBe(0)

    // Advance until run-status returns running (3rd call at ~6s)
    vi.advanceTimersByTime(6000)
    await flushPromises()

    // Now detail polling should have started
    const detailCallsAfter = client.get.mock.calls.filter(c => c[0].includes('/detail')).length
    expect(detailCallsAfter).toBeGreaterThan(0)

    const timelineCalls = client.get.mock.calls.filter(c => c[0].includes('/timeline')).length
    expect(timelineCalls).toBeGreaterThan(0)

    wrapper.unmount()
  })

  it('graph and simulation statuses progress independently through full flow', async () => {
    const taskId = 'e2e-status-sequence'
    setupPhasedMocks()

    store.setScenarioConfig({ scenarioId: 'test', scenarioName: 'Test' })
    store.startGraphBuild(taskId, 'proj-6')

    const wrapper = mountPollingWrapper(taskId, pinia)
    const p = wrapper.vm.polling
    const graphHistory = []
    const simHistory = []

    function recordStatuses() {
      const gs = p.graphStatus.value
      const ss = p.simStatus.value
      if (graphHistory[graphHistory.length - 1] !== gs) graphHistory.push(gs)
      if (simHistory[simHistory.length - 1] !== ss) simHistory.push(ss)
    }

    p.start()
    await flushPromises()
    recordStatuses()

    for (let i = 0; i < 10; i++) {
      vi.advanceTimersByTime(3000)
      await flushPromises()
      recordStatuses()
    }

    // Graph: building → complete
    expect(graphHistory).toContain('building')
    expect(graphHistory).toContain('complete')
    expect(graphHistory.indexOf('building')).toBeLessThan(graphHistory.indexOf('complete'))

    // Simulation: building (idle) → running → completed
    expect(simHistory).toContain('building')
    expect(simHistory).toContain('running')
    expect(simHistory).toContain('completed')
    expect(simHistory.indexOf('running')).toBeLessThan(simHistory.indexOf('completed'))

    // Store reflects final state
    expect(store.status).toBe('complete')
    expect(p.overallPhase.value).toBe('complete')

    wrapper.unmount()
  })
})
