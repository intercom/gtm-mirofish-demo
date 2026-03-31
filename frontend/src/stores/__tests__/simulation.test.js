import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSimulationStore } from '../simulation'

describe('useSimulationStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('initialises in idle state', () => {
    const store = useSimulationStore()
    expect(store.status).toBe('idle')
    expect(store.simulationId).toBeNull()
    expect(store.isActive).toBe(false)
  })

  it('startGraphBuild sets state correctly', () => {
    const store = useSimulationStore()
    store.startGraphBuild('task-1', 'proj-1')
    expect(store.status).toBe('building_graph')
    expect(store.graphTaskId).toBe('task-1')
    expect(store.projectId).toBe('proj-1')
    expect(store.isActive).toBe(true)
    expect(store.error).toBeNull()
  })

  it('startPrepare transitions to preparing', () => {
    const store = useSimulationStore()
    store.startPrepare('sim-1', 'task-2')
    expect(store.status).toBe('preparing')
    expect(store.simulationId).toBe('sim-1')
    expect(store.prepareTaskId).toBe('task-2')
  })

  it('startRun transitions to running', () => {
    const store = useSimulationStore()
    store.startRun('sim-1')
    expect(store.status).toBe('running')
    expect(store.simulationId).toBe('sim-1')
    expect(store.isActive).toBe(true)
  })

  it('updateProgress merges new data', () => {
    const store = useSimulationStore()
    store.updateProgress({ percent: 50, message: 'Building...' })
    expect(store.progress.percent).toBe(50)
    expect(store.progress.message).toBe('Building...')
    expect(store.progress.currentRound).toBe(0)

    // Partial update preserves existing values
    store.updateProgress({ currentRound: 5, totalRounds: 24 })
    expect(store.progress.percent).toBe(50)
    expect(store.progress.currentRound).toBe(5)
  })

  it('updateProgress accepts snake_case backend keys', () => {
    const store = useSimulationStore()
    store.updateProgress({
      progress_percent: 75,
      current_round: 10,
      total_rounds: 24,
    })
    expect(store.progress.percent).toBe(75)
    expect(store.progress.currentRound).toBe(10)
    expect(store.progress.totalRounds).toBe(24)
  })

  it('updateMetrics populates run-time metrics', () => {
    const store = useSimulationStore()
    store.updateMetrics({
      total_actions_count: 350,
      twitter_actions_count: 150,
      reddit_actions_count: 200,
      simulated_hours: 12,
      total_simulation_hours: 72,
    })
    expect(store.metrics.totalActions).toBe(350)
    expect(store.metrics.twitterActions).toBe(150)
    expect(store.metrics.redditActions).toBe(200)
    expect(store.metrics.simulatedHours).toBe(12)
  })

  it('setError transitions to error state', () => {
    const store = useSimulationStore()
    store.startRun('sim-1')
    store.setError('Connection lost')
    expect(store.status).toBe('error')
    expect(store.error).toBe('Connection lost')
  })

  it('complete sets status and progress to 100%', () => {
    const store = useSimulationStore()
    store.startRun('sim-1')
    store.updateProgress({ percent: 95 })
    store.complete()
    expect(store.status).toBe('complete')
    expect(store.progress.percent).toBe(100)
    expect(store.isActive).toBe(false)
  })

  it('reset clears all state', () => {
    const store = useSimulationStore()
    store.startRun('sim-1')
    store.updateProgress({ percent: 50 })
    store.updateMetrics({ total_actions_count: 100 })
    store.reset()
    expect(store.status).toBe('idle')
    expect(store.simulationId).toBeNull()
    expect(store.progress.percent).toBe(0)
    expect(store.metrics.totalActions).toBe(0)
  })

  it('setStatus rejects invalid statuses', () => {
    const store = useSimulationStore()
    store.setStatus('invalid')
    expect(store.status).toBe('idle')
  })

  it('setStatus to idle resets progress and metrics', () => {
    const store = useSimulationStore()
    store.updateProgress({ percent: 50 })
    store.updateMetrics({ total_actions_count: 100 })
    store.setStatus('idle')
    expect(store.progress.percent).toBe(0)
    expect(store.metrics.totalActions).toBe(0)
  })

  // --- scenarioConfig ---

  it('setScenarioConfig stores config', () => {
    const store = useSimulationStore()
    const config = { scenarioId: 'outbound', scenarioName: 'Outbound Campaign', agentCount: 25 }
    store.setScenarioConfig(config)
    expect(store.scenarioConfig).toEqual(config)
  })

  it('reset clears scenarioConfig', () => {
    const store = useSimulationStore()
    store.setScenarioConfig({ scenarioId: 'test' })
    store.reset()
    expect(store.scenarioConfig).toBeNull()
  })

  // --- sessionRuns ---

  it('hasRuns is false when empty', () => {
    const store = useSimulationStore()
    expect(store.hasRuns).toBe(false)
  })

  it('addSessionRun adds a new entry and hasRuns becomes true', () => {
    const store = useSimulationStore()
    store.addSessionRun({ id: 'run-1', scenarioName: 'Test Run' })
    expect(store.sessionRuns).toHaveLength(1)
    expect(store.sessionRuns[0].id).toBe('run-1')
    expect(store.sessionRuns[0].scenarioName).toBe('Test Run')
    expect(store.hasRuns).toBe(true)
  })

  it('addSessionRun uses scenarioConfig as fallback', () => {
    const store = useSimulationStore()
    store.setScenarioConfig({
      scenarioId: 'outbound',
      scenarioName: 'Outbound Campaign',
      seedText: 'some seed',
      agentCount: 30,
    })
    store.addSessionRun({ id: 'run-2' })
    expect(store.sessionRuns[0].scenarioId).toBe('outbound')
    expect(store.sessionRuns[0].scenarioName).toBe('Outbound Campaign')
    expect(store.sessionRuns[0].agentCount).toBe(30)
  })

  it('addSessionRun updates existing entry with same id', () => {
    const store = useSimulationStore()
    store.addSessionRun({ id: 'run-1', totalActions: 50 })
    store.addSessionRun({ id: 'run-1', totalActions: 200, status: 'completed' })
    expect(store.sessionRuns).toHaveLength(1)
    expect(store.sessionRuns[0].totalActions).toBe(200)
    expect(store.sessionRuns[0].status).toBe('completed')
  })

  it('addSessionRun caps at 50 entries', () => {
    const store = useSimulationStore()
    for (let i = 0; i < 55; i++) {
      store.addSessionRun({ id: `run-${i}` })
    }
    expect(store.sessionRuns).toHaveLength(50)
    // Oldest entries were dropped
    expect(store.sessionRuns[0].id).toBe('run-5')
    expect(store.sessionRuns[49].id).toBe('run-54')
  })

  it('updateSessionRunStatus changes a run status', () => {
    const store = useSimulationStore()
    store.addSessionRun({ id: 'run-1' })
    store.updateSessionRunStatus('run-1', 'failed')
    expect(store.sessionRuns[0].status).toBe('failed')
  })

  it('updateSessionRunStatus is no-op for unknown id', () => {
    const store = useSimulationStore()
    store.addSessionRun({ id: 'run-1', status: 'completed' })
    store.updateSessionRunStatus('run-999', 'failed')
    expect(store.sessionRuns[0].status).toBe('completed')
  })

  it('removeSessionRun deletes by id', () => {
    const store = useSimulationStore()
    store.addSessionRun({ id: 'run-1' })
    store.addSessionRun({ id: 'run-2' })
    store.removeSessionRun('run-1')
    expect(store.sessionRuns).toHaveLength(1)
    expect(store.sessionRuns[0].id).toBe('run-2')
  })

  it('removeSessionRun is no-op for unknown id', () => {
    const store = useSimulationStore()
    store.addSessionRun({ id: 'run-1' })
    store.removeSessionRun('run-999')
    expect(store.sessionRuns).toHaveLength(1)
  })

  it('clearAllRuns empties sessionRuns', () => {
    const store = useSimulationStore()
    store.addSessionRun({ id: 'run-1' })
    store.addSessionRun({ id: 'run-2' })
    store.clearAllRuns()
    expect(store.sessionRuns).toEqual([])
    expect(store.hasRuns).toBe(false)
  })

  it('loads sessionRuns from localStorage on init', () => {
    localStorage.setItem('mirofish_simulation_runs', JSON.stringify([
      { id: 'stored-1', scenarioName: 'From Storage', status: 'completed' },
    ]))
    setActivePinia(createPinia())
    const store = useSimulationStore()
    expect(store.sessionRuns).toHaveLength(1)
    expect(store.sessionRuns[0].id).toBe('stored-1')
  })

  it('handles corrupted localStorage for sessionRuns', () => {
    localStorage.setItem('mirofish_simulation_runs', '{not-an-array')
    setActivePinia(createPinia())
    const store = useSimulationStore()
    expect(store.sessionRuns).toEqual([])
  })
})
