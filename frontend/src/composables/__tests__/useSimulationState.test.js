import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { useSimulationState, TRANSITIONS, PHASE_LABELS } from '../useSimulationState'
import { useSimulationStore } from '../../stores/simulation'

function mountComposable(setup) {
  const Comp = defineComponent({
    setup() {
      const result = setup()
      return { result }
    },
    render() {
      return h('div')
    },
  })
  return mount(Comp, {
    global: { plugins: [createPinia()] },
  })
}

describe('useSimulationState', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // --- Initialization ---

  it('starts in idle phase', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    expect(state.phase.value).toBe('idle')
    expect(state.isIdle.value).toBe(true)
    expect(state.isActive.value).toBe(false)
    expect(state.phaseLabel.value).toBe('Ready')
    expect(state.phaseHistory.value).toEqual([])
    wrapper.unmount()
  })

  // --- Valid transitions ---

  it('transitions idle → configuring', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    const result = state.configure({ scenarioId: 's1', scenarioName: 'Test' })
    expect(result).toBe(true)
    expect(state.phase.value).toBe('configuring')
    expect(state.isConfiguring.value).toBe(true)
    expect(state.phaseLabel.value).toBe('Configuring')
    wrapper.unmount()
  })

  it('transitions idle → building_graph (skip configuring)', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    const result = state.buildGraph('task-1', 'proj-1')
    expect(result).toBe(true)
    expect(state.phase.value).toBe('building_graph')
    expect(state.isBuildingGraph.value).toBe(true)
    expect(state.isActive.value).toBe(true)
    wrapper.unmount()
  })

  it('follows full lifecycle: idle → configuring → building_graph → preparing → running → complete', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    expect(state.configure({ scenarioId: 's1' })).toBe(true)
    expect(state.buildGraph('task-1', 'proj-1')).toBe(true)
    expect(state.prepare('sim-1', 'task-2')).toBe(true)
    expect(state.startRun('sim-1')).toBe(true)
    expect(state.isRunning.value).toBe(true)
    expect(state.complete()).toBe(true)
    expect(state.isComplete.value).toBe(true)
    expect(state.isActive.value).toBe(false)

    expect(state.phaseHistory.value).toHaveLength(5)
    wrapper.unmount()
  })

  it('supports pause and resume during running', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')

    expect(state.canPause.value).toBe(true)
    expect(state.pause()).toBe(true)
    expect(state.isPaused.value).toBe(true)
    expect(state.isActive.value).toBe(true)
    expect(state.canResume.value).toBe(true)

    expect(state.resume()).toBe(true)
    expect(state.isRunning.value).toBe(true)
    wrapper.unmount()
  })

  // --- Invalid transitions ---

  it('rejects invalid transitions', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    // idle → running (skipping required steps)
    expect(state.startRun('sim-1')).toBe(false)
    expect(state.phase.value).toBe('idle')

    // idle → complete
    expect(state.complete()).toBe(false)
    expect(state.phase.value).toBe('idle')

    // idle → paused
    expect(state.pause()).toBe(false)
    expect(state.phase.value).toBe('idle')
    wrapper.unmount()
  })

  it('rejects pause when not running', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    expect(state.pause()).toBe(false)
    expect(state.phase.value).toBe('building_graph')
    wrapper.unmount()
  })

  it('rejects resume when not paused', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    expect(state.resume()).toBe(false)
    expect(state.phase.value).toBe('running')
    wrapper.unmount()
  })

  // --- Error handling ---

  it('fail() transitions active phase to error', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    const result = state.fail('Build failed')
    expect(result).toBe(true)
    expect(state.phase.value).toBe('error')
    expect(state.hasError.value).toBe(true)
    expect(state.isActive.value).toBe(false)
    wrapper.unmount()
  })

  it('fail() works from running phase', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    expect(state.fail('Timeout')).toBe(true)
    expect(state.phase.value).toBe('error')
    wrapper.unmount()
  })

  it('fail() rejects from idle phase', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    expect(state.fail('Oops')).toBe(false)
    expect(state.phase.value).toBe('idle')
    wrapper.unmount()
  })

  it('fail() rejects from complete phase', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    state.complete()
    expect(state.fail('Late error')).toBe(false)
    expect(state.phase.value).toBe('complete')
    wrapper.unmount()
  })

  // --- Stop and reset ---

  it('stop() transitions active phase to idle', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    expect(state.canStop.value).toBe(true)
    expect(state.stop()).toBe(true)
    expect(state.phase.value).toBe('idle')
    wrapper.unmount()
  })

  it('reset() clears all state and syncs store', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    state.reset()

    expect(state.phase.value).toBe('idle')
    expect(state.phaseHistory.value).toEqual([])
    expect(state.phaseStartedAt.value).toBeNull()
    expect(state.elapsedMs.value).toBe(0)

    const store = useSimulationStore()
    expect(store.status).toBe('idle')
    expect(store.simulationId).toBeNull()
    wrapper.unmount()
  })

  it('retry() transitions from error to configuring', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.fail('Error')
    expect(state.retry()).toBe(true)
    expect(state.phase.value).toBe('configuring')
    wrapper.unmount()
  })

  it('retry() transitions from complete to configuring', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    state.complete()
    expect(state.retry()).toBe(true)
    expect(state.phase.value).toBe('configuring')
    wrapper.unmount()
  })

  // --- Store sync ---

  it('syncs phase changes to simulation store status', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    const store = useSimulationStore()

    state.buildGraph('t1', 'p1')
    expect(store.status).toBe('building_graph')

    state.prepare('s1', 't2')
    expect(store.status).toBe('preparing')

    state.startRun('s1')
    expect(store.status).toBe('running')

    state.complete()
    expect(store.status).toBe('complete')
    wrapper.unmount()
  })

  it('configuring maps to idle in store (no store equivalent)', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    const store = useSimulationStore()

    state.configure({ scenarioId: 's1' })
    expect(state.phase.value).toBe('configuring')
    expect(store.status).toBe('idle')
    wrapper.unmount()
  })

  it('paused maps to running in store', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    const store = useSimulationStore()

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    state.pause()
    expect(state.phase.value).toBe('paused')
    expect(store.status).toBe('running')
    wrapper.unmount()
  })

  it('buildGraph sets store graphTaskId and projectId', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    const store = useSimulationStore()

    state.buildGraph('task-42', 'proj-7')
    expect(store.graphTaskId).toBe('task-42')
    expect(store.projectId).toBe('proj-7')
    wrapper.unmount()
  })

  it('configure sets store scenarioConfig', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })
    const store = useSimulationStore()

    const config = { scenarioId: 's1', scenarioName: 'Launch Plan' }
    state.configure(config)
    expect(store.scenarioConfig).toEqual(config)
    wrapper.unmount()
  })

  // --- Phase history ---

  it('records phase transitions in history', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')

    expect(state.phaseHistory.value).toHaveLength(2)
    expect(state.phaseHistory.value[0].from).toBe('idle')
    expect(state.phaseHistory.value[0].to).toBe('building_graph')
    expect(state.phaseHistory.value[1].from).toBe('building_graph')
    expect(state.phaseHistory.value[1].to).toBe('preparing')
    expect(state.phaseHistory.value[0].at).toBeLessThanOrEqual(Date.now())
    wrapper.unmount()
  })

  // --- Elapsed timer ---

  it('tracks elapsed time during active phases', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    expect(state.elapsedMs.value).toBe(0)

    vi.advanceTimersByTime(3000)
    expect(state.elapsedMs.value).toBeGreaterThanOrEqual(3000)
    expect(state.elapsedFormatted.value).toMatch(/\ds/)
    wrapper.unmount()
  })

  it('stops elapsed timer when reaching complete', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    state.prepare('s1', 't2')
    state.startRun('s1')
    vi.advanceTimersByTime(5000)
    const elapsed = state.elapsedMs.value

    state.complete()
    vi.advanceTimersByTime(3000)
    expect(state.elapsedMs.value).toBe(elapsed)
    wrapper.unmount()
  })

  it('resets elapsed timer on new active phase', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')
    vi.advanceTimersByTime(5000)
    expect(state.elapsedMs.value).toBeGreaterThanOrEqual(5000)

    state.prepare('s1', 't2')
    expect(state.elapsedMs.value).toBe(0)
    wrapper.unmount()
  })

  it('formats elapsed time correctly', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    state.buildGraph('t1', 'p1')

    vi.advanceTimersByTime(45000)
    expect(state.elapsedFormatted.value).toBe('45s')

    vi.advanceTimersByTime(20000)
    expect(state.elapsedFormatted.value).toBe('1m 5s')
    wrapper.unmount()
  })

  // --- Computed helpers ---

  it('availableTransitions reflects current phase', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    expect(state.availableTransitions.value).toEqual(['configuring', 'building_graph'])

    state.buildGraph('t1', 'p1')
    expect(state.availableTransitions.value).toEqual(['preparing', 'error', 'idle'])

    state.prepare('s1', 't2')
    state.startRun('s1')
    expect(state.availableTransitions.value).toEqual(['complete', 'paused', 'error', 'idle'])
    wrapper.unmount()
  })

  it('canStop is true only when active and idle is reachable', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    expect(state.canStop.value).toBe(false)

    state.buildGraph('t1', 'p1')
    expect(state.canStop.value).toBe(true)

    state.prepare('s1', 't2')
    state.startRun('s1')
    expect(state.canStop.value).toBe(true)

    state.complete()
    expect(state.canStop.value).toBe(false)
    wrapper.unmount()
  })

  // --- canTransition ---

  it('canTransition returns correct boolean', () => {
    let state
    const wrapper = mountComposable(() => {
      state = useSimulationState()
      return state
    })

    expect(state.canTransition('configuring')).toBe(true)
    expect(state.canTransition('building_graph')).toBe(true)
    expect(state.canTransition('running')).toBe(false)
    expect(state.canTransition('complete')).toBe(false)
    expect(state.canTransition('nonexistent')).toBe(false)
    wrapper.unmount()
  })

  // --- Exported constants ---

  it('exports TRANSITIONS map', () => {
    expect(TRANSITIONS).toBeDefined()
    expect(TRANSITIONS.idle).toContain('configuring')
    expect(TRANSITIONS.running).toContain('complete')
  })

  it('exports PHASE_LABELS', () => {
    expect(PHASE_LABELS).toBeDefined()
    expect(PHASE_LABELS.idle).toBe('Ready')
    expect(PHASE_LABELS.running).toBe('Running Simulation')
  })
})
