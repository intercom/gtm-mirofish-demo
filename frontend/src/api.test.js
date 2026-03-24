import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  listScenarios,
  getScenario,
  buildGraph,
  getTask,
  generateOntology,
  createSimulation,
  prepareSimulation,
  getPrepareStatus,
  startSimulation,
  getRunStatus,
  getSimulationActions,
  generateReport,
  getReportGenerateStatus,
  getReport,
  getReportSections,
  chatWithReport,
  poll,
} from './api.js'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

function jsonResponse(body, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  })
}

beforeEach(() => {
  mockFetch.mockReset()
})

describe('API envelope handling', () => {
  it('unwraps successful {success: true, data: ...} responses', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { task_id: 'task_123', message: 'ok' },
    }))
    const result = await getTask('task_123')
    expect(result.data.task_id).toBe('task_123')
  })

  it('throws on {success: false} response', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: false,
      error: 'Project not found',
    }))
    await expect(buildGraph('bad_id')).rejects.toThrow('Project not found')
  })

  it('throws on non-OK HTTP status', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: false,
      error: 'Server error',
    }, 500))
    await expect(getTask('task_x')).rejects.toThrow('Server error')
  })
})

describe('GTM scenario endpoints', () => {
  it('listScenarios calls /api/gtm/scenarios', async () => {
    mockFetch.mockReturnValue(jsonResponse({ scenarios: [{ id: 'test' }] }))
    const result = await listScenarios()
    expect(mockFetch).toHaveBeenCalledWith('/api/gtm/scenarios')
    expect(result.scenarios).toHaveLength(1)
  })

  it('getScenario calls /api/gtm/scenarios/:id', async () => {
    mockFetch.mockReturnValue(jsonResponse({ id: 'outbound', name: 'Outbound' }))
    const result = await getScenario('outbound')
    expect(mockFetch).toHaveBeenCalledWith('/api/gtm/scenarios/outbound')
    expect(result.id).toBe('outbound')
  })
})

describe('Graph endpoints', () => {
  it('buildGraph POSTs to /api/graph/build with project_id', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { project_id: 'p1', task_id: 't1' },
    }))
    await buildGraph('p1')
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('/api/graph/build')
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ project_id: 'p1' })
  })

  it('getTask GETs /api/graph/task/:taskId', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { status: 'completed', progress: 100 },
    }))
    const result = await getTask('t1')
    expect(mockFetch).toHaveBeenCalledWith('/api/graph/task/t1', expect.any(Object))
    expect(result.data.status).toBe('completed')
  })
})

describe('Simulation endpoints', () => {
  it('createSimulation POSTs to /api/simulation/create', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { simulation_id: 'sim_1' },
    }))
    await createSimulation('p1', 'g1', { enable_twitter: true })
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('/api/simulation/create')
    expect(JSON.parse(opts.body)).toMatchObject({
      project_id: 'p1',
      graph_id: 'g1',
      enable_twitter: true,
    })
  })

  it('getPrepareStatus sends simulation_id when provided', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { status: 'ready', already_prepared: true },
    }))
    await getPrepareStatus(null, 'sim_1')
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body).toEqual({ simulation_id: 'sim_1' })
  })

  it('startSimulation POSTs with simulation_id and platform', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { runner_status: 'running' },
    }))
    await startSimulation('sim_1', 'parallel')
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body).toEqual({ simulation_id: 'sim_1', platform: 'parallel' })
  })

  it('getRunStatus GETs /api/simulation/:simId/run-status', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { runner_status: 'running', total_actions_count: 50 },
    }))
    await getRunStatus('sim_1')
    expect(mockFetch).toHaveBeenCalledWith('/api/simulation/sim_1/run-status', expect.any(Object))
  })
})

describe('Report endpoints', () => {
  it('generateReport POSTs with simulation_id', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { task_id: 't1', report_id: 'r1', status: 'generating' },
    }))
    await generateReport('sim_1')
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body).toEqual({ simulation_id: 'sim_1' })
  })

  it('chatWithReport sends message and history', async () => {
    mockFetch.mockReturnValue(jsonResponse({
      success: true,
      data: { response: 'The data shows...' },
    }))
    await chatWithReport('sim_1', 'Hello', [{ role: 'user', content: 'Hi' }])
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body.simulation_id).toBe('sim_1')
    expect(body.message).toBe('Hello')
    expect(body.chat_history).toHaveLength(1)
  })
})

describe('poll utility', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('calls fn and delivers results to onData', async () => {
    vi.useFakeTimers()
    const fn = vi.fn().mockResolvedValue({ status: 'ok' })
    const poller = poll(fn, 1000)
    const onData = vi.fn()

    poller.start(onData)
    await vi.advanceTimersByTimeAsync(0) // first tick

    expect(fn).toHaveBeenCalledTimes(1)
    expect(onData).toHaveBeenCalledWith({ status: 'ok' })

    poller.stop()
  })

  it('stops polling when stop() is called', async () => {
    vi.useFakeTimers()
    const fn = vi.fn().mockResolvedValue({ status: 'ok' })
    const poller = poll(fn, 100)
    const onData = vi.fn()

    poller.start(onData)
    await vi.advanceTimersByTimeAsync(0) // first tick
    poller.stop()
    await vi.advanceTimersByTimeAsync(500) // should not fire more

    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('passes errors to onData as second arg', async () => {
    vi.useFakeTimers()
    const fn = vi.fn().mockRejectedValue(new Error('Network fail'))
    const poller = poll(fn, 1000)
    const onData = vi.fn()

    poller.start(onData)
    await vi.advanceTimersByTimeAsync(0)

    expect(onData).toHaveBeenCalledWith(null, expect.any(Error))

    poller.stop()
  })
})
