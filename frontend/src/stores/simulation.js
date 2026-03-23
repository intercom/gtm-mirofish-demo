import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSimulationStore = defineStore('simulation', () => {
  const status = ref('idle') // idle | building | graphReady | running | complete | error
  const graphTaskId = ref(null)
  const simulationTaskId = ref(null)
  const reportTaskId = ref(null)
  const progress = ref(0) // 0–100
  const currentRound = ref(0)
  const totalRounds = ref(0)
  const error = ref(null)
  const metrics = ref({ actions: 0, replies: 0, likes: 0 })
  const activities = ref([])

  const isActive = computed(() =>
    ['building', 'running'].includes(status.value),
  )

  const roundLabel = computed(() =>
    totalRounds.value ? `${currentRound.value}/${totalRounds.value}` : '0/0',
  )

  function startBuild(taskId) {
    status.value = 'building'
    graphTaskId.value = taskId
    error.value = null
    progress.value = 0
  }

  function graphReady() {
    status.value = 'graphReady'
  }

  function startSimulation(taskId) {
    status.value = 'running'
    simulationTaskId.value = taskId
    progress.value = 0
    metrics.value = { actions: 0, replies: 0, likes: 0 }
    activities.value = []
  }

  function updateProgress({ round, totalRounds: total, progress: pct, metrics: m, activities: acts }) {
    if (round !== undefined) currentRound.value = round
    if (total !== undefined) totalRounds.value = total
    if (pct !== undefined) progress.value = pct
    if (m) metrics.value = { ...metrics.value, ...m }
    if (acts) activities.value = [...activities.value, ...acts]
  }

  function complete(taskId) {
    status.value = 'complete'
    if (taskId) reportTaskId.value = taskId
    progress.value = 100
  }

  function fail(message) {
    status.value = 'error'
    error.value = message
  }

  function reset() {
    status.value = 'idle'
    graphTaskId.value = null
    simulationTaskId.value = null
    reportTaskId.value = null
    progress.value = 0
    currentRound.value = 0
    totalRounds.value = 0
    error.value = null
    metrics.value = { actions: 0, replies: 0, likes: 0 }
    activities.value = []
  }

  return {
    status,
    graphTaskId,
    simulationTaskId,
    reportTaskId,
    progress,
    currentRound,
    totalRounds,
    error,
    metrics,
    activities,
    isActive,
    roundLabel,
    startBuild,
    graphReady,
    startSimulation,
    updateProgress,
    complete,
    fail,
    reset,
  }
})
