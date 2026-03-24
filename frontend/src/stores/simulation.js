import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

/**
 * Simulation lifecycle phases (mirrors backend SimulationStatus / RunnerStatus):
 *   idle → building_graph → preparing → running → complete
 *   Any phase can transition to 'error'.
 */
const VALID_STATUSES = ['idle', 'building_graph', 'preparing', 'running', 'complete', 'error']

export const useSimulationStore = defineStore('simulation', () => {
  const status = ref('idle')
  const simulationId = ref(null)
  const graphTaskId = ref(null)
  const prepareTaskId = ref(null)
  const projectId = ref(null)
  const error = ref(null)

  // Progress tracking for the active phase
  const progress = ref({
    percent: 0,
    message: '',
    currentRound: 0,
    totalRounds: 0,
  })

  // Run-status metrics (populated during 'running' phase via polling)
  const metrics = ref({
    totalActions: 0,
    twitterActions: 0,
    redditActions: 0,
    simulatedHours: 0,
    totalSimulationHours: 0,
  })

  // Session-level history of completed simulation runs
  const sessionRuns = ref([])

  const isActive = computed(() =>
    ['building_graph', 'preparing', 'running'].includes(status.value),
  )

  const hasRuns = computed(() => sessionRuns.value.length > 0)

  function setStatus(newStatus) {
    if (!VALID_STATUSES.includes(newStatus)) return
    status.value = newStatus
    if (newStatus === 'error') return
    if (newStatus === 'idle') {
      progress.value = { percent: 0, message: '', currentRound: 0, totalRounds: 0 }
      metrics.value = { totalActions: 0, twitterActions: 0, redditActions: 0, simulatedHours: 0, totalSimulationHours: 0 }
    }
  }

  function startGraphBuild(taskId, projId) {
    graphTaskId.value = taskId
    projectId.value = projId
    error.value = null
    setStatus('building_graph')
  }

  function startPrepare(simId, taskId) {
    simulationId.value = simId
    prepareTaskId.value = taskId
    error.value = null
    setStatus('preparing')
  }

  function startRun(simId) {
    simulationId.value = simId
    error.value = null
    setStatus('running')
  }

  function updateProgress(data) {
    progress.value = {
      percent: data.percent ?? data.progress_percent ?? progress.value.percent,
      message: data.message ?? progress.value.message,
      currentRound: data.currentRound ?? data.current_round ?? progress.value.currentRound,
      totalRounds: data.totalRounds ?? data.total_rounds ?? progress.value.totalRounds,
    }
  }

  function updateMetrics(data) {
    metrics.value = {
      totalActions: data.total_actions_count ?? metrics.value.totalActions,
      twitterActions: data.twitter_actions_count ?? metrics.value.twitterActions,
      redditActions: data.reddit_actions_count ?? metrics.value.redditActions,
      simulatedHours: data.simulated_hours ?? metrics.value.simulatedHours,
      totalSimulationHours: data.total_simulation_hours ?? metrics.value.totalSimulationHours,
    }
  }

  function setError(msg) {
    error.value = msg
    setStatus('error')
  }

  function complete() {
    setStatus('complete')
    progress.value.percent = 100
  }

  function addSessionRun(run) {
    if (sessionRuns.value.some(r => r.id === run.id)) return
    sessionRuns.value.push({
      id: run.id,
      scenarioName: run.scenarioName || 'Untitled Scenario',
      totalRounds: run.totalRounds || 0,
      totalActions: run.totalActions || 0,
      twitterActions: run.twitterActions || 0,
      redditActions: run.redditActions || 0,
      timestamp: Date.now(),
    })
  }

  function reset() {
    status.value = 'idle'
    simulationId.value = null
    graphTaskId.value = null
    prepareTaskId.value = null
    projectId.value = null
    error.value = null
    progress.value = { percent: 0, message: '', currentRound: 0, totalRounds: 0 }
    metrics.value = { totalActions: 0, twitterActions: 0, redditActions: 0, simulatedHours: 0, totalSimulationHours: 0 }
  }

  return {
    status,
    simulationId,
    graphTaskId,
    prepareTaskId,
    projectId,
    error,
    progress,
    metrics,
    sessionRuns,
    isActive,
    hasRuns,
    setStatus,
    startGraphBuild,
    startPrepare,
    startRun,
    updateProgress,
    updateMetrics,
    setError,
    complete,
    addSessionRun,
    reset,
  }
})
