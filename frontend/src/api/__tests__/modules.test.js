import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockClient = {
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
}

vi.mock('../client', () => ({ default: mockClient }))

describe('graphApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('wraps all graph endpoints', async () => {
    const { graphApi } = await import('../graph')

    graphApi.getProject('p1')
    expect(mockClient.get).toHaveBeenCalledWith('/graph/project/p1')

    graphApi.listProjects({ limit: 10 })
    expect(mockClient.get).toHaveBeenCalledWith('/graph/project/list', { params: { limit: 10 } })

    graphApi.deleteProject('p1')
    expect(mockClient.delete).toHaveBeenCalledWith('/graph/project/p1')

    graphApi.resetProject('p1')
    expect(mockClient.post).toHaveBeenCalledWith('/graph/project/p1/reset')

    const fd = new FormData()
    graphApi.generateOntology(fd)
    expect(mockClient.post).toHaveBeenCalledWith('/graph/ontology/generate', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    graphApi.build({ project_id: 'p1' })
    expect(mockClient.post).toHaveBeenCalledWith('/gtm/simulate', { project_id: 'p1' })

    graphApi.getTask('t1')
    expect(mockClient.get).toHaveBeenCalledWith('/graph/task/t1')

    graphApi.listTasks()
    expect(mockClient.get).toHaveBeenCalledWith('/graph/tasks')

    graphApi.getData('g1')
    expect(mockClient.get).toHaveBeenCalledWith('/graph/data/g1')

    graphApi.deleteGraph('g1')
    expect(mockClient.delete).toHaveBeenCalledWith('/graph/delete/g1')
  })
})

describe('simulationApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('wraps entity endpoints', async () => {
    const { simulationApi } = await import('../simulation')

    simulationApi.getEntities('g1', { limit: 5 })
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/entities/g1', { params: { limit: 5 } })

    simulationApi.getEntity('g1', 'uuid1')
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/entities/g1/uuid1')

    simulationApi.getEntitiesByType('g1', 'person', { limit: 10 })
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/entities/g1/by-type/person', { params: { limit: 10 } })
  })

  it('wraps lifecycle endpoints', async () => {
    const { simulationApi } = await import('../simulation')

    simulationApi.create({ graph_id: 'g1' })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/create', { graph_id: 'g1' })

    simulationApi.prepare({ simulation_id: 's1' })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/prepare', { simulation_id: 's1' })

    simulationApi.start({ simulation_id: 's1' })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/start', { simulation_id: 's1' })

    simulationApi.stop({ simulation_id: 's1' })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/stop', { simulation_id: 's1' })
  })

  it('wraps config and download endpoints', async () => {
    const { simulationApi } = await import('../simulation')

    simulationApi.downloadConfig('s1')
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/s1/config/download', { responseType: 'blob' })

    simulationApi.downloadScript('run.py')
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/script/run.py/download', { responseType: 'blob' })
  })

  it('wraps status and results endpoints', async () => {
    const { simulationApi } = await import('../simulation')

    simulationApi.get('s1')
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/s1')

    simulationApi.getRunStatus('s1')
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/s1/run-status')

    simulationApi.getActions('s1', { page: 1 })
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/s1/actions', { params: { page: 1 } })

    simulationApi.getPosts('s1', { limit: 20 })
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/s1/posts', { params: { limit: 20 } })
  })

  it('wraps interview endpoints', async () => {
    const { simulationApi } = await import('../simulation')

    simulationApi.interview({ simulation_id: 's1', question: 'why?' })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/interview', { simulation_id: 's1', question: 'why?' })

    simulationApi.interviewBatch({ simulation_id: 's1' })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/interview/batch', { simulation_id: 's1' })
  })
})

describe('reportApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('wraps generation endpoints', async () => {
    const { reportApi } = await import('../report')

    reportApi.generate({ simulation_id: 's1' })
    expect(mockClient.post).toHaveBeenCalledWith('/report/generate', { simulation_id: 's1' })

    reportApi.generateStatus({ task_id: 't1' })
    expect(mockClient.post).toHaveBeenCalledWith('/report/generate/status', { task_id: 't1' })
  })

  it('wraps CRUD endpoints', async () => {
    const { reportApi } = await import('../report')

    reportApi.get('r1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/r1')

    reportApi.getBySimulation('s1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/by-simulation/s1')

    reportApi.list({ limit: 10 })
    expect(mockClient.get).toHaveBeenCalledWith('/report/list', { params: { limit: 10 } })

    reportApi.delete('r1')
    expect(mockClient.delete).toHaveBeenCalledWith('/report/r1')

    reportApi.download('r1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/r1/download', { responseType: 'blob' })
  })

  it('wraps progress and section endpoints', async () => {
    const { reportApi } = await import('../report')

    reportApi.getProgress('r1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/r1/progress')

    reportApi.getSections('r1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/r1/sections')

    reportApi.getSection('r1', 2)
    expect(mockClient.get).toHaveBeenCalledWith('/report/r1/section/2')

    reportApi.checkStatus('s1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/check/s1')
  })
})

describe('scenariosApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('wraps all scenario endpoints', async () => {
    const { scenariosApi } = await import('../scenarios')

    scenariosApi.list()
    expect(mockClient.get).toHaveBeenCalledWith('/gtm/scenarios')

    scenariosApi.get('enterprise-expansion')
    expect(mockClient.get).toHaveBeenCalledWith('/gtm/scenarios/enterprise-expansion')

    scenariosApi.getSeedData('account_profiles')
    expect(mockClient.get).toHaveBeenCalledWith('/gtm/seed-data/account_profiles')

    scenariosApi.getSeedText('enterprise-expansion')
    expect(mockClient.get).toHaveBeenCalledWith('/gtm/scenarios/enterprise-expansion/seed-text')
  })
})

describe('chatApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('sends chat messages via report/chat endpoint', async () => {
    const { chatApi } = await import('../chat')

    const data = { simulation_id: 's1', message: 'hello' }
    chatApi.send(data)
    expect(mockClient.post).toHaveBeenCalledWith('/report/chat', data)
  })
})

describe('cpqApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('wraps product endpoints', async () => {
    const { cpqApi } = await import('../cpq')

    cpqApi.getProducts({ family: 'Support' })
    expect(mockClient.get).toHaveBeenCalledWith('/cpq/products', { params: { family: 'Support' } })
  })

  it('wraps quote list and detail endpoints', async () => {
    const { cpqApi } = await import('../cpq')

    cpqApi.getQuotes({ status: 'Review', page: 1 })
    expect(mockClient.get).toHaveBeenCalledWith('/cpq/quotes', { params: { status: 'Review', page: 1 } })

    cpqApi.getQuote('q-100')
    expect(mockClient.get).toHaveBeenCalledWith('/cpq/quotes/q-100')

    cpqApi.getPdfPreview('q-100')
    expect(mockClient.get).toHaveBeenCalledWith('/cpq/quotes/q-100/pdf-preview')
  })

  it('wraps quote action endpoints', async () => {
    const { cpqApi } = await import('../cpq')

    cpqApi.approveQuote('q-100')
    expect(mockClient.post).toHaveBeenCalledWith('/cpq/quotes/q-100/approve')

    cpqApi.rejectQuote('q-100', 'Discount too high')
    expect(mockClient.post).toHaveBeenCalledWith('/cpq/quotes/q-100/reject', { reason: 'Discount too high' })
  })

  it('wraps stats endpoint', async () => {
    const { cpqApi } = await import('../cpq')

    cpqApi.getCpqStats()
    expect(mockClient.get).toHaveBeenCalledWith('/cpq/stats')
  })
})
