import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'

/**
 * Simulation lifecycle phases (mirrors backend SimulationStatus / RunnerStatus):
 *   idle → building_graph → preparing → running → complete
 *   Any phase can transition to 'error'.
 */
const VALID_STATUSES = ['idle', 'building_graph', 'preparing', 'running', 'complete', 'error']

const STORAGE_KEY = 'mirofish_simulation_runs'
const MAX_STORED_RUNS = 50

function loadStoredRuns() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

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

  // Branch points for the active simulation
  const branchPoints = ref([])
  const totalBranches = ref(0)

  // Current scenario config (set before navigating to workspace)
  const scenarioConfig = ref(null)

  // Session-level history of completed simulation runs — hydrated from localStorage
  const sessionRuns = ref(loadStoredRuns())

  // Persist sessionRuns to localStorage on every mutation
  watch(sessionRuns, (runs) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(runs))
    } catch {
      // Storage full or unavailable — silently ignore
    }
  }, { deep: true })

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

  function setBranchPoints(data) {
    branchPoints.value = data.branch_points || []
    totalBranches.value = data.total_branches || 0
  }

  function setScenarioConfig(config) {
    scenarioConfig.value = config
  }

  function addSessionRun(run) {
    const existing = sessionRuns.value.find(r => r.id === run.id)
    if (existing) {
      if (run.totalRounds) existing.totalRounds = run.totalRounds
      if (run.totalActions) existing.totalActions = run.totalActions
      if (run.twitterActions) existing.twitterActions = run.twitterActions
      if (run.redditActions) existing.redditActions = run.redditActions
      if (run.branchCount != null) existing.branchCount = run.branchCount
      if (run.status) existing.status = run.status
      return
    }
    const entry = {
      id: run.id,
      scenarioId: run.scenarioId || scenarioConfig.value?.scenarioId || null,
      scenarioName: run.scenarioName || scenarioConfig.value?.scenarioName || 'Untitled Scenario',
      seedText: run.seedText || scenarioConfig.value?.seedText || '',
      agentCount: run.agentCount || scenarioConfig.value?.agentCount || 0,
      personas: run.personas || scenarioConfig.value?.personas || [],
      industries: run.industries || scenarioConfig.value?.industries || [],
      duration: run.duration || scenarioConfig.value?.duration || 0,
      platformMode: run.platformMode || scenarioConfig.value?.platformMode || 'parallel',
      totalRounds: run.totalRounds || 0,
      totalActions: run.totalActions || 0,
      twitterActions: run.twitterActions || 0,
      redditActions: run.redditActions || 0,
      branchCount: run.branchCount || 0,
      status: run.status || 'completed',
      timestamp: Date.now(),
    }
    sessionRuns.value.push(entry)

    // Cap at MAX_STORED_RUNS — drop oldest
    while (sessionRuns.value.length > MAX_STORED_RUNS) {
      sessionRuns.value.shift()
    }
  }

  function updateSessionRunStatus(id, newStatus) {
    const run = sessionRuns.value.find(r => r.id === id)
    if (run) run.status = newStatus
  }

  function removeSessionRun(id) {
    const idx = sessionRuns.value.findIndex(r => r.id === id)
    if (idx !== -1) sessionRuns.value.splice(idx, 1)
  }

  function clearAllRuns() {
    sessionRuns.value = []
  }

  function reset() {
    status.value = 'idle'
    simulationId.value = null
    graphTaskId.value = null
    prepareTaskId.value = null
    projectId.value = null
    error.value = null
    scenarioConfig.value = null
    branchPoints.value = []
    totalBranches.value = 0
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
    branchPoints,
    totalBranches,
    scenarioConfig,
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
    setBranchPoints,
    setScenarioConfig,
    addSessionRun,
    updateSessionRunStatus,
    removeSessionRun,
    clearAllRuns,
    reset,
  }
})
