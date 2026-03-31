import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/whatif', () => ({
  whatifApi: {
    run: vi.fn(),
  },
}))

import { useWhatifStore } from '../whatif'
import { whatifApi } from '../../api/whatif'

describe('useWhatifStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initialises in idle state with no modifications', () => {
    const store = useWhatifStore()
    expect(store.baseSimulationId).toBeNull()
    expect(store.modifications).toEqual([])
    expect(store.status).toBe('idle')
    expect(store.progress).toBe(0)
    expect(store.progressMessage).toBe('')
    expect(store.error).toBeNull()
    expect(store.resultVariantId).toBeNull()
    expect(store.variants).toEqual([])
  })

  // --- isRunning computed ---

  it('isRunning is true only when status is running', () => {
    const store = useWhatifStore()
    expect(store.isRunning).toBe(false)
    store.status = 'running'
    expect(store.isRunning).toBe(true)
    store.status = 'complete'
    expect(store.isRunning).toBe(false)
  })

  // --- isComplete computed ---

  it('isComplete is true only when status is complete', () => {
    const store = useWhatifStore()
    expect(store.isComplete).toBe(false)
    store.status = 'complete'
    expect(store.isComplete).toBe(true)
  })

  // --- hasModifications computed ---

  it('hasModifications reflects whether modifications exist', () => {
    const store = useWhatifStore()
    expect(store.hasModifications).toBe(false)
    store.addModification('agent_count', 300)
    expect(store.hasModifications).toBe(true)
  })

  // --- canRun computed ---

  it('canRun requires baseSimulationId AND modifications AND not running', () => {
    const store = useWhatifStore()
    expect(store.canRun).toBeFalsy()

    store.setBaseSimulation('sim-1')
    expect(store.canRun).toBeFalsy()

    store.addModification('agent_count', 300)
    expect(store.canRun).toBe(true)

    store.status = 'running'
    expect(store.canRun).toBeFalsy()
  })

  // --- setBaseSimulation ---

  it('setBaseSimulation sets id and keeps idle status', () => {
    const store = useWhatifStore()
    store.setBaseSimulation('sim-1')
    expect(store.baseSimulationId).toBe('sim-1')
    expect(store.status).toBe('idle')
  })

  it('setBaseSimulation resets status if complete', () => {
    const store = useWhatifStore()
    store.status = 'complete'
    store.resultVariantId = 'variant-1'
    store.setBaseSimulation('sim-2')
    expect(store.status).toBe('idle')
    expect(store.resultVariantId).toBeNull()
  })

  it('setBaseSimulation resets status if error', () => {
    const store = useWhatifStore()
    store.status = 'error'
    store.setBaseSimulation('sim-3')
    expect(store.status).toBe('idle')
    expect(store.resultVariantId).toBeNull()
  })

  it('setBaseSimulation does not reset running status', () => {
    const store = useWhatifStore()
    store.status = 'running'
    store.setBaseSimulation('sim-4')
    expect(store.status).toBe('running')
  })

  // --- addModification ---

  it('addModification adds a new parameter modification', () => {
    const store = useWhatifStore()
    store.addModification('agent_count', 250)
    expect(store.modifications).toHaveLength(1)
    expect(store.modifications[0]).toEqual({ parameter: 'agent_count', value: 250 })
  })

  it('addModification updates existing parameter instead of duplicating', () => {
    const store = useWhatifStore()
    store.addModification('agent_count', 250)
    store.addModification('agent_count', 400)
    expect(store.modifications).toHaveLength(1)
    expect(store.modifications[0].value).toBe(400)
  })

  // --- removeModification ---

  it('removeModification removes by parameter key', () => {
    const store = useWhatifStore()
    store.addModification('agent_count', 250)
    store.addModification('rounds', 30)
    store.removeModification('agent_count')
    expect(store.modifications).toHaveLength(1)
    expect(store.modifications[0].parameter).toBe('rounds')
  })

  it('removeModification is no-op for unknown parameter', () => {
    const store = useWhatifStore()
    store.addModification('agent_count', 250)
    store.removeModification('nonexistent')
    expect(store.modifications).toHaveLength(1)
  })

  // --- clearModifications ---

  it('clearModifications empties the list', () => {
    const store = useWhatifStore()
    store.addModification('agent_count', 250)
    store.addModification('rounds', 30)
    store.clearModifications()
    expect(store.modifications).toEqual([])
  })

  // --- applyPreset ---

  it('applyPreset applies known preset modifications', () => {
    const store = useWhatifStore()
    store.applyPreset('more_agents')
    expect(store.modifications).toHaveLength(1)
    expect(store.modifications[0]).toEqual({ parameter: 'agent_count', value: 350 })
  })

  it('applyPreset updates existing modification if parameter overlaps', () => {
    const store = useWhatifStore()
    store.addModification('agent_count', 100)
    store.applyPreset('more_agents')
    expect(store.modifications).toHaveLength(1)
    expect(store.modifications[0].value).toBe(350)
  })

  it('applyPreset ignores unknown preset id', () => {
    const store = useWhatifStore()
    store.applyPreset('nonexistent_preset')
    expect(store.modifications).toEqual([])
  })

  // --- parameterDefs and presets ---

  it('parameterDefs is exposed and non-empty', () => {
    const store = useWhatifStore()
    expect(store.parameterDefs.length).toBeGreaterThan(0)
    expect(store.parameterDefs.some((p) => p.key === 'agent_count')).toBe(true)
  })

  it('presets is exposed and non-empty', () => {
    const store = useWhatifStore()
    expect(store.presets.length).toBeGreaterThan(0)
    expect(store.presets.some((p) => p.id === 'more_agents')).toBe(true)
  })

  // --- reset ---

  it('reset clears all state back to initial', () => {
    const store = useWhatifStore()
    store.setBaseSimulation('sim-1')
    store.addModification('agent_count', 300)
    store.status = 'complete'
    store.progress = 100
    store.progressMessage = 'Done'
    store.error = 'some error'
    store.resultVariantId = 'variant-1'

    store.reset()

    expect(store.baseSimulationId).toBeNull()
    expect(store.modifications).toEqual([])
    expect(store.status).toBe('idle')
    expect(store.progress).toBe(0)
    expect(store.progressMessage).toBe('')
    expect(store.error).toBeNull()
    expect(store.resultVariantId).toBeNull()
  })

  // --- runWhatIf (API success) ---

  it('runWhatIf calls API and sets complete on success', async () => {
    whatifApi.run.mockResolvedValue({
      data: { variant_id: 'variant-abc' },
    })
    const store = useWhatifStore()
    store.setBaseSimulation('sim-1')
    store.addModification('agent_count', 300)

    await store.runWhatIf()

    expect(whatifApi.run).toHaveBeenCalledWith({
      base_simulation_id: 'sim-1',
      modifications: [{ parameter: 'agent_count', value: 300 }],
    })
    expect(store.status).toBe('complete')
    expect(store.resultVariantId).toBe('variant-abc')
    expect(store.progress).toBe(100)
  })

  // --- runWhatIf does nothing when canRun is false ---

  it('runWhatIf does nothing when canRun is false (no base sim)', async () => {
    const store = useWhatifStore()
    store.addModification('agent_count', 300)
    await store.runWhatIf()
    expect(whatifApi.run).not.toHaveBeenCalled()
    expect(store.status).toBe('idle')
  })

  it('runWhatIf does nothing when canRun is false (no modifications)', async () => {
    const store = useWhatifStore()
    store.setBaseSimulation('sim-1')
    await store.runWhatIf()
    expect(whatifApi.run).not.toHaveBeenCalled()
    expect(store.status).toBe('idle')
  })

  // --- runWhatIf (API error with non-demo status) ---

  it('runWhatIf sets error state on API failure with status other than 0/404', async () => {
    const err = new Error('Server error')
    err.status = 500
    whatifApi.run.mockRejectedValue(err)

    const store = useWhatifStore()
    store.setBaseSimulation('sim-1')
    store.addModification('agent_count', 300)
    await store.runWhatIf()

    expect(store.status).toBe('error')
    expect(store.error).toBe('Server error')
  })

  // --- runWhatIf (demo mode fallback on 404) ---

  it('runWhatIf falls back to demo mode on 404', async () => {
    vi.useFakeTimers()
    const err = new Error('Not found')
    err.status = 404
    whatifApi.run.mockRejectedValue(err)

    const store = useWhatifStore()
    store.setBaseSimulation('sim-1')
    store.addModification('rounds', 20)

    const runPromise = store.runWhatIf()

    // Advance through all demo steps (6 steps, each ~600-1000ms)
    for (let i = 0; i < 6; i++) {
      await vi.advanceTimersByTimeAsync(1100)
    }

    await runPromise

    expect(store.status).toBe('complete')
    expect(store.resultVariantId).toMatch(/^demo-variant-/)
    expect(store.variants.length).toBeGreaterThan(0)

    vi.useRealTimers()
  })

  // --- runWhatIf (demo mode fallback on status 0) ---

  it('runWhatIf falls back to demo mode on status 0', async () => {
    vi.useFakeTimers()
    const err = new Error('Network error')
    err.status = 0
    whatifApi.run.mockRejectedValue(err)

    const store = useWhatifStore()
    store.setBaseSimulation('sim-1')
    store.addModification('temperature', 1.5)

    const runPromise = store.runWhatIf()

    for (let i = 0; i < 6; i++) {
      await vi.advanceTimersByTimeAsync(1100)
    }

    await runPromise

    expect(store.status).toBe('complete')
    expect(store.resultVariantId).toMatch(/^demo-variant-/)

    vi.useRealTimers()
  })
})
