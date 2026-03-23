import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  listScenarios,
  getScenario,
  buildGraph,
  getGraphTask,
  getGraphData,
  createSimulation,
  prepareSimulation,
  getPrepareStatus,
  startSimulation,
  getRunStatus,
  generateReport,
  getReportGenerateStatus,
  getReportSections,
  chatWithReport,
  pollTask,
} from '../services/api.js'

function mockFetch(data, ok = true) {
  return vi.fn().mockResolvedValue({
    ok,
    status: ok ? 200 : 500,
    json: () => Promise.resolve(data),
  })
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('API service - GTM Scenarios', () => {
  it('listScenarios calls GET /api/gtm/scenarios', async () => {
    global.fetch = mockFetch({ scenarios: [{ id: 'test' }] })
    const res = await listScenarios()
    expect(fetch).toHaveBeenCalledWith('/api/gtm/scenarios', expect.objectContaining({ headers: expect.any(Object) }))
    expect(res.scenarios).toHaveLength(1)
  })

  it('getScenario calls GET /api/gtm/scenarios/:id', async () => {
    global.fetch = mockFetch({ id: 'outbound', name: 'Outbound' })
    const res = await getScenario('outbound')
    expect(fetch).toHaveBeenCalledWith('/api/gtm/scenarios/outbound', expect.any(Object))
    expect(res.id).toBe('outbound')
  })
})

describe('API service - Graph Building', () => {
  it('buildGraph sends POST with project_id', async () => {
    global.fetch = mockFetch({ success: true, data: { task_id: 'task_123', project_id: 'proj_1' } })
    const res = await buildGraph({ projectId: 'proj_1', graphName: 'Test' })
    expect(fetch).toHaveBeenCalledWith(
      '/api/graph/build',
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"project_id":"proj_1"'),
      }),
    )
    expect(res.data.task_id).toBe('task_123')
  })

  it('getGraphTask calls GET /api/graph/task/:id', async () => {
    global.fetch = mockFetch({ success: true, data: { status: 'processing', progress: 50 } })
    const res = await getGraphTask('task_1')
    expect(fetch).toHaveBeenCalledWith('/api/graph/task/task_1', expect.any(Object))
    expect(res.data.progress).toBe(50)
  })

  it('getGraphData calls GET /api/graph/data/:id', async () => {
    global.fetch = mockFetch({ success: true, data: { nodes: [{ name: 'A' }], edges: [] } })
    const res = await getGraphData('graph_1')
    expect(fetch).toHaveBeenCalledWith('/api/graph/data/graph_1', expect.any(Object))
    expect(res.data.nodes).toHaveLength(1)
  })
})

describe('API service - Simulation', () => {
  it('createSimulation sends POST with project_id and graph_id', async () => {
    global.fetch = mockFetch({ success: true, data: { simulation_id: 'sim_1' } })
    const res = await createSimulation({ projectId: 'proj_1', graphId: 'graph_1' })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.project_id).toBe('proj_1')
    expect(body.graph_id).toBe('graph_1')
    expect(res.data.simulation_id).toBe('sim_1')
  })

  it('prepareSimulation sends POST with simulation_id', async () => {
    global.fetch = mockFetch({ success: true, data: { task_id: 'task_2', status: 'preparing' } })
    await prepareSimulation({ simulationId: 'sim_1' })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.simulation_id).toBe('sim_1')
  })

  it('getPrepareStatus sends POST with task_id', async () => {
    global.fetch = mockFetch({ success: true, data: { status: 'processing', progress: 40 } })
    await getPrepareStatus({ taskId: 'task_2', simulationId: 'sim_1' })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.task_id).toBe('task_2')
  })

  it('startSimulation sends POST with simulation_id and platform', async () => {
    global.fetch = mockFetch({ success: true, data: { runner_status: 'running' } })
    await startSimulation({ simulationId: 'sim_1', platform: 'parallel' })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.simulation_id).toBe('sim_1')
    expect(body.platform).toBe('parallel')
  })

  it('getRunStatus calls GET /api/simulation/:id/run-status', async () => {
    global.fetch = mockFetch({
      success: true,
      data: { runner_status: 'running', current_round: 5, total_rounds: 100, total_actions_count: 42 },
    })
    const res = await getRunStatus('sim_1')
    expect(fetch).toHaveBeenCalledWith('/api/simulation/sim_1/run-status', expect.any(Object))
    expect(res.data.total_actions_count).toBe(42)
  })
})

describe('API service - Report', () => {
  it('generateReport sends POST with simulation_id', async () => {
    global.fetch = mockFetch({ success: true, data: { report_id: 'rpt_1', task_id: 'task_3' } })
    const res = await generateReport({ simulationId: 'sim_1' })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.simulation_id).toBe('sim_1')
    expect(res.data.report_id).toBe('rpt_1')
  })

  it('getReportSections calls GET /api/report/:id/sections', async () => {
    global.fetch = mockFetch({
      success: true,
      data: { sections: [{ content: '## Summary' }], is_complete: true },
    })
    const res = await getReportSections('rpt_1')
    expect(fetch).toHaveBeenCalledWith('/api/report/rpt_1/sections', expect.any(Object))
    expect(res.data.sections).toHaveLength(1)
  })
})

describe('API service - Chat', () => {
  it('chatWithReport sends POST with simulation_id and message', async () => {
    global.fetch = mockFetch({ success: true, data: { response: 'Hello from MiroFish' } })
    const res = await chatWithReport({ simulationId: 'sim_1', message: 'What happened?', chatHistory: [] })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.simulation_id).toBe('sim_1')
    expect(body.message).toBe('What happened?')
    expect(res.data.response).toBe('Hello from MiroFish')
  })
})

describe('API service - Error handling', () => {
  it('throws on non-ok response', async () => {
    global.fetch = mockFetch({ success: false, error: 'Not found' }, false)
    await expect(getGraphTask('bad_id')).rejects.toThrow('Not found')
  })

  it('throws on success: false', async () => {
    global.fetch = mockFetch({ success: false, error: 'Config error' })
    await expect(buildGraph({ projectId: 'p' })).rejects.toThrow('Config error')
  })
})

describe('pollTask', () => {
  it('resolves when task completes', async () => {
    let call = 0
    const pollFn = vi.fn(async () => {
      call++
      if (call < 3) return { data: { status: 'processing', progress: call * 30 } }
      return { data: { status: 'completed', progress: 100, result: { graph_id: 'g1' } } }
    })

    const progressUpdates = []
    const result = await pollTask(pollFn, {
      interval: 10,
      onProgress: (d) => progressUpdates.push(d.progress),
    })

    expect(result.data.status).toBe('completed')
    expect(progressUpdates).toContain(30)
    expect(pollFn).toHaveBeenCalledTimes(3)
  })

  it('throws on task failure', async () => {
    const pollFn = vi.fn(async () => ({ data: { status: 'failed', message: 'Out of memory' } }))
    await expect(pollTask(pollFn, { interval: 10 })).rejects.toThrow('Out of memory')
  })

  it('resolves on already_prepared', async () => {
    const pollFn = vi.fn(async () => ({
      data: { status: 'ready', already_prepared: true, progress: 100 },
    }))
    const result = await pollTask(pollFn, { interval: 10 })
    expect(result.data.already_prepared).toBe(true)
  })
})
