import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSimulationStore } from '../simulation'

describe('useSimulationStore', () => {
  beforeEach(() => {
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
})
