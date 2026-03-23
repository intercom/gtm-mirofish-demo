import { describe, it, expect, vi, beforeEach } from 'vitest'

// vi.hoisted runs during the hoisted phase, so mockClient is available to vi.mock
const mockClient = vi.hoisted(() => ({
  get: vi.fn().mockResolvedValue({ data: { success: true } }),
  post: vi.fn().mockResolvedValue({ data: { success: true } }),
  delete: vi.fn().mockResolvedValue({ data: { success: true } }),
}))

vi.mock('../client', () => ({ default: mockClient }))

import * as graph from '../graph'
import * as simulation from '../simulation'
import * as report from '../report'
import * as scenarios from '../scenarios'
import * as chat from '../chat'

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Graph API ───────────────────────────────────

describe('graph', () => {
  it('getProject calls GET /graph/project/:id', async () => {
    await graph.getProject('proj_123')
    expect(mockClient.get).toHaveBeenCalledWith('/graph/project/proj_123')
  })

  it('listProjects passes limit as query param', async () => {
    await graph.listProjects(10)
    expect(mockClient.get).toHaveBeenCalledWith('/graph/project/list', {
      params: { limit: 10 },
    })
  })

  it('deleteProject calls DELETE', async () => {
    await graph.deleteProject('proj_123')
    expect(mockClient.delete).toHaveBeenCalledWith('/graph/project/proj_123')
  })

  it('resetProject calls POST', async () => {
    await graph.resetProject('proj_123')
    expect(mockClient.post).toHaveBeenCalledWith(
      '/graph/project/proj_123/reset',
    )
  })

  it('generateOntology sends multipart/form-data', async () => {
    const formData = new FormData()
    await graph.generateOntology(formData)
    expect(mockClient.post).toHaveBeenCalledWith(
      '/graph/ontology/generate',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  })

  it('buildGraph posts data', async () => {
    const data = { project_id: 'proj_123' }
    await graph.buildGraph(data)
    expect(mockClient.post).toHaveBeenCalledWith('/graph/build', data)
  })

  it('getTask calls correct path', async () => {
    await graph.getTask('task_abc')
    expect(mockClient.get).toHaveBeenCalledWith('/graph/task/task_abc')
  })

  it('getGraphData calls correct path', async () => {
    await graph.getGraphData('g_xyz')
    expect(mockClient.get).toHaveBeenCalledWith('/graph/data/g_xyz')
  })

  it('deleteGraph calls DELETE on correct path', async () => {
    await graph.deleteGraph('g_xyz')
    expect(mockClient.delete).toHaveBeenCalledWith('/graph/delete/g_xyz')
  })
})

// ── Simulation API ──────────────────────────────

describe('simulation', () => {
  it('getEntities passes graphId and params', async () => {
    await simulation.getEntities('g_1', { entity_types: 'Person' })
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/entities/g_1', {
      params: { entity_types: 'Person' },
    })
  })

  it('createSimulation posts data', async () => {
    const data = { project_id: 'p1', graph_id: 'g1' }
    await simulation.createSimulation(data)
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/create', data)
  })

  it('startSimulation posts data', async () => {
    const data = { simulation_id: 'sim_1' }
    await simulation.startSimulation(data)
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/start', data)
  })

  it('stopSimulation posts data', async () => {
    const data = { simulation_id: 'sim_1' }
    await simulation.stopSimulation(data)
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/stop', data)
  })

  it('getSimulation fetches by id', async () => {
    await simulation.getSimulation('sim_1')
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/sim_1')
  })

  it('getRunStatus fetches status', async () => {
    await simulation.getRunStatus('sim_1')
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/sim_1/run-status')
  })

  it('getRunStatusDetail fetches detailed status', async () => {
    await simulation.getRunStatusDetail('sim_1')
    expect(mockClient.get).toHaveBeenCalledWith(
      '/simulation/sim_1/run-status/detail',
    )
  })

  it('downloadConfig uses blob responseType', async () => {
    await simulation.downloadConfig('sim_1')
    expect(mockClient.get).toHaveBeenCalledWith(
      '/simulation/sim_1/config/download',
      { responseType: 'blob' },
    )
  })

  it('getActions passes params', async () => {
    await simulation.getActions('sim_1', { page: 1 })
    expect(mockClient.get).toHaveBeenCalledWith('/simulation/sim_1/actions', {
      params: { page: 1 },
    })
  })
})

// ── Report API ──────────────────────────────────

describe('report', () => {
  it('generateReport posts data', async () => {
    const data = { simulation_id: 'sim_1' }
    await report.generateReport(data)
    expect(mockClient.post).toHaveBeenCalledWith('/report/generate', data)
  })

  it('getReport fetches by id', async () => {
    await report.getReport('rpt_1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/rpt_1')
  })

  it('getReportBySimulation fetches by simulation id', async () => {
    await report.getReportBySimulation('sim_1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/by-simulation/sim_1')
  })

  it('checkReportStatus fetches status', async () => {
    await report.checkReportStatus('sim_1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/check/sim_1')
  })

  it('getReportSections fetches sections', async () => {
    await report.getReportSections('rpt_1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/rpt_1/sections')
  })

  it('getSection fetches a single section', async () => {
    await report.getSection('rpt_1', 2)
    expect(mockClient.get).toHaveBeenCalledWith('/report/rpt_1/section/2')
  })

  it('downloadReport uses blob responseType', async () => {
    await report.downloadReport('rpt_1')
    expect(mockClient.get).toHaveBeenCalledWith('/report/rpt_1/download', {
      responseType: 'blob',
    })
  })

  it('deleteReport calls DELETE', async () => {
    await report.deleteReport('rpt_1')
    expect(mockClient.delete).toHaveBeenCalledWith('/report/rpt_1')
  })

  it('getAgentLog passes from_line param', async () => {
    await report.getAgentLog('rpt_1', 10)
    expect(mockClient.get).toHaveBeenCalledWith('/report/rpt_1/agent-log', {
      params: { from_line: 10 },
    })
  })
})

// ── Scenarios API ───────────────────────────────

describe('scenarios', () => {
  it('listScenarios calls GET /gtm/scenarios', async () => {
    await scenarios.listScenarios()
    expect(mockClient.get).toHaveBeenCalledWith('/gtm/scenarios')
  })

  it('getScenario fetches by id', async () => {
    await scenarios.getScenario('enterprise-churn')
    expect(mockClient.get).toHaveBeenCalledWith(
      '/gtm/scenarios/enterprise-churn',
    )
  })

  it('getSeedData fetches by type', async () => {
    await scenarios.getSeedData('account_profiles')
    expect(mockClient.get).toHaveBeenCalledWith(
      '/gtm/seed-data/account_profiles',
    )
  })

  it('getScenarioSeedText fetches seed text', async () => {
    await scenarios.getScenarioSeedText('plg-conversion')
    expect(mockClient.get).toHaveBeenCalledWith(
      '/gtm/scenarios/plg-conversion/seed-text',
    )
  })
})

// ── Chat API ────────────────────────────────────

describe('chat', () => {
  it('chatWithReport posts correct payload', async () => {
    await chat.chatWithReport({
      simulationId: 'sim_1',
      message: 'What happened?',
      chatHistory: [],
    })
    expect(mockClient.post).toHaveBeenCalledWith('/report/chat', {
      simulation_id: 'sim_1',
      message: 'What happened?',
      chat_history: [],
    })
  })

  it('interview posts correct payload', async () => {
    await chat.interview({
      simulationId: 'sim_1',
      agentName: 'agent_001',
      prompt: 'Tell me about yourself',
    })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/interview', {
      simulation_id: 'sim_1',
      agent_name: 'agent_001',
      prompt: 'Tell me about yourself',
    })
  })

  it('interviewBatch posts array of agents', async () => {
    await chat.interviewBatch({
      simulationId: 'sim_1',
      agentNames: ['a1', 'a2'],
      prompt: 'Hello',
    })
    expect(mockClient.post).toHaveBeenCalledWith(
      '/simulation/interview/batch',
      {
        simulation_id: 'sim_1',
        agent_names: ['a1', 'a2'],
        prompt: 'Hello',
      },
    )
  })

  it('interviewAll posts simulation-wide interview', async () => {
    await chat.interviewAll({ simulationId: 'sim_1', prompt: 'Reflect' })
    expect(mockClient.post).toHaveBeenCalledWith('/simulation/interview/all', {
      simulation_id: 'sim_1',
      prompt: 'Reflect',
    })
  })

  it('getInterviewHistory posts correct payload', async () => {
    await chat.getInterviewHistory({
      simulationId: 'sim_1',
      agentName: 'a1',
    })
    expect(mockClient.post).toHaveBeenCalledWith(
      '/simulation/interview/history',
      { simulation_id: 'sim_1', agent_name: 'a1' },
    )
  })
})
