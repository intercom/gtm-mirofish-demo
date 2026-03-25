import { ref, computed, onUnmounted, toValue } from 'vue'
import { metricsApi } from '../api/metrics'
import { useDemoMode } from './useDemoMode'

/**
 * Composable for polling OASIS simulation metrics.
 *
 * Fetches a unified metrics snapshot (summary, platform breakdown,
 * action distribution, agent leaderboard, round series) and keeps
 * it up-to-date via interval polling while the simulation is active.
 *
 * @param {Ref<string>|string} simulationIdSource - reactive or static simulation ID
 * @param {object} options
 * @param {number} options.interval - polling interval in ms (default 5000)
 */
export function useMetricsCollector(simulationIdSource, options = {}) {
  const { isDemoMode } = useDemoMode()
  const interval = options.interval ?? 5000

  const metrics = ref(null)
  const loading = ref(false)
  const error = ref(null)
  let timer = null

  const summary = computed(() => metrics.value?.summary ?? null)
  const platformBreakdown = computed(() => metrics.value?.platform_breakdown ?? null)
  const actionDistribution = computed(() => metrics.value?.action_distribution ?? [])
  const agentLeaderboard = computed(() => metrics.value?.agent_leaderboard ?? [])
  const roundSeries = computed(() => metrics.value?.round_series ?? [])
  const status = computed(() => metrics.value?.status ?? 'idle')
  const isComplete = computed(() => ['completed', 'stopped'].includes(status.value))

  async function fetch() {
    const simId = toValue(simulationIdSource)
    if (!simId && !isDemoMode) return

    loading.value = true
    error.value = null

    try {
      let res
      if (isDemoMode && !simId) {
        res = await metricsApi.getDemoMetrics()
      } else {
        const params = isDemoMode ? { demo: 'true' } : {}
        res = await metricsApi.getSimulationMetrics(simId, params)
      }

      if (res.data?.success) {
        metrics.value = res.data.data
      } else {
        error.value = res.data?.error || 'Failed to fetch metrics'
      }
    } catch (err) {
      error.value = err.message || 'Network error fetching metrics'
    } finally {
      loading.value = false
    }
  }

  function startPolling() {
    stopPolling()
    fetch()
    timer = setInterval(() => {
      if (!isComplete.value) fetch()
    }, interval)
  }

  function stopPolling() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onUnmounted(stopPolling)

  return {
    metrics,
    loading,
    error,
    summary,
    platformBreakdown,
    actionDistribution,
    agentLeaderboard,
    roundSeries,
    status,
    isComplete,
    fetch,
    startPolling,
    stopPolling,
  }
}
