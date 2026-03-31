import { ref, onUnmounted } from 'vue'
import { simulationApi } from '../api/simulation'
import { useSimulationStore } from '../stores/simulation'

/**
 * Composable for real-time simulation progress via Server-Sent Events.
 *
 * Connects to the backend SSE endpoint and pushes progress/status/actions
 * updates into reactive refs and the Pinia simulation store.
 *
 * Falls back gracefully — callers should check `connected` and use polling
 * when SSE is unavailable.
 */
export function useSimulationSSE() {
  const simStore = useSimulationStore()

  const connected = ref(false)
  const runStatus = ref(null)
  const recentActions = ref([])
  const sseError = ref(null)

  let eventSource = null
  let simulationId = null
  const MAX_RECENT_ACTIONS = 100

  function connect(simId, { interval = 2 } = {}) {
    disconnect()
    simulationId = simId
    sseError.value = null

    const url = simulationApi.getProgressStreamUrl(simId, interval)

    try {
      eventSource = new EventSource(url)
    } catch (e) {
      sseError.value = e.message
      return
    }

    eventSource.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data)
        runStatus.value = data

        simStore.updateProgress({
          progress_percent: data.progress_percent,
          current_round: data.current_round,
          total_rounds: data.total_rounds,
        })
        simStore.updateMetrics({
          total_actions_count: data.total_actions_count,
          twitter_actions_count: data.twitter_actions_count,
          reddit_actions_count: data.reddit_actions_count,
          simulated_hours: data.simulated_hours,
          total_simulation_hours: data.total_simulation_hours,
        })
      } catch { /* malformed event */ }
    })

    eventSource.addEventListener('status', (e) => {
      try {
        const data = JSON.parse(e.data)
        const rs = data.runner_status
        if (rs === 'completed' || rs === 'stopped') {
          simStore.complete()
        } else if (rs === 'failed') {
          simStore.setError(data.error || 'Simulation failed')
        }
      } catch { /* malformed event */ }
    })

    eventSource.addEventListener('actions', (e) => {
      try {
        const newActions = JSON.parse(e.data)
        if (Array.isArray(newActions) && newActions.length > 0) {
          recentActions.value = [...newActions, ...recentActions.value].slice(0, MAX_RECENT_ACTIONS)
        }
      } catch { /* malformed event */ }
    })

    eventSource.addEventListener('complete', (e) => {
      try {
        const data = JSON.parse(e.data)
        runStatus.value = data
        simStore.complete()
        simStore.addSessionRun({
          id: simId,
          totalRounds: data.total_rounds ?? 0,
          totalActions: data.total_actions_count ?? 0,
          twitterActions: data.twitter_actions_count ?? 0,
          redditActions: data.reddit_actions_count ?? 0,
          status: 'completed',
        })
      } catch { /* malformed event */ }
      disconnect()
    })

    eventSource.addEventListener('error', (e) => {
      try {
        const data = JSON.parse(e.data)
        sseError.value = data.error
      } catch { /* not a JSON error event — connection-level error */ }
    })

    eventSource.onopen = () => {
      connected.value = true
      sseError.value = null
    }

    eventSource.onerror = () => {
      connected.value = false
      sseError.value = 'SSE connection lost'
    }
  }

  function disconnect() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    connected.value = false
    simulationId = null
  }

  onUnmounted(disconnect)

  return {
    connected,
    runStatus,
    recentActions,
    sseError,
    connect,
    disconnect,
  }
}
