import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSimulationStore } from '../simulation'

describe('simulation store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes as idle', () => {
    const store = useSimulationStore()
    expect(store.status).toBe('idle')
    expect(store.graphTaskId).toBeNull()
    expect(store.simulationTaskId).toBeNull()
    expect(store.reportTaskId).toBeNull()
    expect(store.progress).toBe(0)
    expect(store.isActive).toBe(false)
  })

  it('transitions to building state', () => {
    const store = useSimulationStore()
    store.startBuild('graph-123')
    expect(store.status).toBe('building')
    expect(store.graphTaskId).toBe('graph-123')
    expect(store.isActive).toBe(true)
  })

  it('transitions to graphReady', () => {
    const store = useSimulationStore()
    store.startBuild('graph-123')
    store.graphReady()
    expect(store.status).toBe('graphReady')
    expect(store.isActive).toBe(false)
  })

  it('starts simulation', () => {
    const store = useSimulationStore()
    store.startSimulation('sim-456')
    expect(store.status).toBe('running')
    expect(store.simulationTaskId).toBe('sim-456')
    expect(store.isActive).toBe(true)
    expect(store.metrics).toEqual({ actions: 0, replies: 0, likes: 0 })
  })

  it('updates progress incrementally', () => {
    const store = useSimulationStore()
    store.startSimulation('sim-456')
    store.updateProgress({ round: 5, totalRounds: 24, progress: 20 })
    expect(store.currentRound).toBe(5)
    expect(store.totalRounds).toBe(24)
    expect(store.progress).toBe(20)
    expect(store.roundLabel).toBe('5/24')
  })

  it('updates metrics and activities', () => {
    const store = useSimulationStore()
    store.startSimulation('sim-456')
    store.updateProgress({ metrics: { actions: 10, replies: 3 } })
    expect(store.metrics.actions).toBe(10)
    expect(store.metrics.replies).toBe(3)
    expect(store.metrics.likes).toBe(0)

    store.updateProgress({ activities: [{ id: 1, text: 'post' }] })
    expect(store.activities).toHaveLength(1)
    store.updateProgress({ activities: [{ id: 2, text: 'reply' }] })
    expect(store.activities).toHaveLength(2)
  })

  it('completes simulation', () => {
    const store = useSimulationStore()
    store.startSimulation('sim-456')
    store.complete('report-789')
    expect(store.status).toBe('complete')
    expect(store.reportTaskId).toBe('report-789')
    expect(store.progress).toBe(100)
    expect(store.isActive).toBe(false)
  })

  it('handles failure', () => {
    const store = useSimulationStore()
    store.startSimulation('sim-456')
    store.fail('LLM rate limit exceeded')
    expect(store.status).toBe('error')
    expect(store.error).toBe('LLM rate limit exceeded')
    expect(store.isActive).toBe(false)
  })

  it('resets all state', () => {
    const store = useSimulationStore()
    store.startSimulation('sim-456')
    store.updateProgress({ round: 10, totalRounds: 24, progress: 40 })
    store.reset()
    expect(store.status).toBe('idle')
    expect(store.simulationTaskId).toBeNull()
    expect(store.progress).toBe(0)
    expect(store.currentRound).toBe(0)
    expect(store.activities).toEqual([])
  })

  it('clears error on new build', () => {
    const store = useSimulationStore()
    store.fail('some error')
    store.startBuild('graph-new')
    expect(store.error).toBeNull()
    expect(store.status).toBe('building')
  })

  it('returns correct roundLabel with no rounds', () => {
    const store = useSimulationStore()
    expect(store.roundLabel).toBe('0/0')
  })
})
