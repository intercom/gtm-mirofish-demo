import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

/**
 * Pinia store for OASIS metrics state.
 *
 * Holds the latest metrics snapshot from the MetricsCollector API
 * and exposes computed helpers for common dashboard needs.
 */
export const useMetricsStore = defineStore('metrics', () => {
  const snapshot = ref(null)
  const lastFetchedAt = ref(null)

  const summary = computed(() => snapshot.value?.summary ?? null)
  const platformBreakdown = computed(() => snapshot.value?.platform_breakdown ?? null)
  const actionDistribution = computed(() => snapshot.value?.action_distribution ?? [])
  const agentLeaderboard = computed(() => snapshot.value?.agent_leaderboard ?? [])
  const roundSeries = computed(() => snapshot.value?.round_series ?? [])
  const simulationStatus = computed(() => snapshot.value?.status ?? 'idle')

  const totalActions = computed(() => summary.value?.total_actions ?? 0)
  const uniqueAgents = computed(() => summary.value?.unique_agents ?? 0)
  const actionsPerRound = computed(() => summary.value?.actions_per_round ?? 0)
  const contentRatio = computed(() => {
    const s = summary.value
    if (!s || !s.total_actions) return 0
    return Math.round((s.content_actions / s.total_actions) * 100)
  })

  function setSnapshot(data) {
    snapshot.value = data
    lastFetchedAt.value = Date.now()
  }

  function reset() {
    snapshot.value = null
    lastFetchedAt.value = null
  }

  return {
    snapshot,
    lastFetchedAt,
    summary,
    platformBreakdown,
    actionDistribution,
    agentLeaderboard,
    roundSeries,
    simulationStatus,
    totalActions,
    uniqueAgents,
    actionsPerRound,
    contentRatio,
    setSnapshot,
    reset,
  }
})
