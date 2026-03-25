import { ref, computed, onUnmounted } from 'vue'
import { useSimulationStore } from '../stores/simulation'

/**
 * Simulation lifecycle phases and their allowed transitions.
 *
 * Lifecycle:
 *   idle → configuring → building_graph → preparing → running → complete
 *                                                   ↘ paused ↗
 *   Any active phase can transition to 'error'.
 *   'error' and 'complete' can return to 'idle' or 'configuring'.
 */
const TRANSITIONS = {
  idle:           ['configuring', 'building_graph'],
  configuring:    ['building_graph', 'idle'],
  building_graph: ['preparing', 'error', 'idle'],
  preparing:      ['running', 'error', 'idle'],
  running:        ['complete', 'paused', 'error', 'idle'],
  paused:         ['running', 'idle', 'error'],
  complete:       ['idle', 'configuring'],
  error:          ['idle', 'configuring'],
}

const PHASE_LABELS = {
  idle: 'Ready',
  configuring: 'Configuring',
  building_graph: 'Building Graph',
  preparing: 'Preparing Simulation',
  running: 'Running Simulation',
  paused: 'Paused',
  complete: 'Complete',
  error: 'Error',
}

const STORE_STATUS_MAP = {
  idle: 'idle',
  configuring: 'idle',
  building_graph: 'building_graph',
  preparing: 'preparing',
  running: 'running',
  paused: 'running',
  complete: 'complete',
  error: 'error',
}

export function useSimulationState() {
  const simStore = useSimulationStore()

  const phase = ref('idle')
  const phaseHistory = ref([])
  const phaseStartedAt = ref(null)
  const elapsedMs = ref(0)
  let elapsedTimer = null

  // --- Transition logic ---

  function canTransition(target) {
    return TRANSITIONS[phase.value]?.includes(target) ?? false
  }

  function transition(target) {
    if (!canTransition(target)) return false

    phaseHistory.value.push({
      from: phase.value,
      to: target,
      at: Date.now(),
    })

    phase.value = target
    phaseStartedAt.value = Date.now()

    const storeStatus = STORE_STATUS_MAP[target]
    if (storeStatus) simStore.setStatus(storeStatus)

    if (['building_graph', 'preparing', 'running'].includes(target)) {
      startElapsedTimer()
    } else {
      stopElapsedTimer()
    }

    return true
  }

  // --- Lifecycle actions ---

  function configure(config) {
    if (!transition('configuring')) return false
    simStore.setScenarioConfig(config)
    return true
  }

  function buildGraph(taskId, projectId) {
    if (!transition('building_graph')) return false
    simStore.startGraphBuild(taskId, projectId)
    return true
  }

  function prepare(simulationId, taskId) {
    if (!transition('preparing')) return false
    simStore.startPrepare(simulationId, taskId)
    return true
  }

  function startRun(simulationId) {
    if (!transition('running')) return false
    simStore.startRun(simulationId)
    return true
  }

  function pause() {
    return transition('paused')
  }

  function resume() {
    return transition('running')
  }

  function complete() {
    if (!transition('complete')) return false
    simStore.complete()
    return true
  }

  function fail(errorMsg) {
    const active = ['building_graph', 'preparing', 'running', 'paused']
    if (!active.includes(phase.value)) return false

    phaseHistory.value.push({
      from: phase.value,
      to: 'error',
      at: Date.now(),
    })
    phase.value = 'error'
    phaseStartedAt.value = Date.now()
    stopElapsedTimer()
    simStore.setError(errorMsg)
    return true
  }

  function stop() {
    if (!canTransition('idle')) return false
    return transition('idle')
  }

  function reset() {
    stopElapsedTimer()
    phase.value = 'idle'
    phaseHistory.value = []
    phaseStartedAt.value = null
    elapsedMs.value = 0
    simStore.reset()
  }

  function retry() {
    return transition('configuring')
  }

  // --- Elapsed time tracking ---

  function startElapsedTimer() {
    stopElapsedTimer()
    elapsedMs.value = 0
    const start = Date.now()
    elapsedTimer = setInterval(() => {
      elapsedMs.value = Date.now() - start
    }, 1000)
  }

  function stopElapsedTimer() {
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }
  }

  // --- Computed properties ---

  const isIdle = computed(() => phase.value === 'idle')
  const isConfiguring = computed(() => phase.value === 'configuring')
  const isBuildingGraph = computed(() => phase.value === 'building_graph')
  const isPreparing = computed(() => phase.value === 'preparing')
  const isRunning = computed(() => phase.value === 'running')
  const isPaused = computed(() => phase.value === 'paused')
  const isComplete = computed(() => phase.value === 'complete')
  const hasError = computed(() => phase.value === 'error')

  const isActive = computed(() =>
    ['building_graph', 'preparing', 'running', 'paused'].includes(phase.value),
  )

  const canPause = computed(() => phase.value === 'running')
  const canResume = computed(() => phase.value === 'paused')
  const canStop = computed(() => canTransition('idle') && isActive.value)

  const phaseLabel = computed(() => PHASE_LABELS[phase.value] || 'Unknown')

  const availableTransitions = computed(() => TRANSITIONS[phase.value] || [])

  const elapsedFormatted = computed(() => {
    const totalSec = Math.floor(elapsedMs.value / 1000)
    const min = Math.floor(totalSec / 60)
    const sec = totalSec % 60
    if (min === 0) return `${sec}s`
    return `${min}m ${sec}s`
  })

  onUnmounted(() => {
    stopElapsedTimer()
  })

  return {
    phase,
    phaseHistory,
    phaseStartedAt,
    elapsedMs,

    canTransition,
    transition,

    configure,
    buildGraph,
    prepare,
    startRun,
    pause,
    resume,
    complete,
    fail,
    stop,
    reset,
    retry,

    isIdle,
    isConfiguring,
    isBuildingGraph,
    isPreparing,
    isRunning,
    isPaused,
    isComplete,
    hasError,
    isActive,
    canPause,
    canResume,
    canStop,
    phaseLabel,
    availableTransitions,
    elapsedFormatted,
  }
}

export { TRANSITIONS, PHASE_LABELS, STORE_STATUS_MAP }
