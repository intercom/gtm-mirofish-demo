import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { API_BASE } from '../api/client'

export const useReconciliationStore = defineStore('reconciliation', () => {
  const runs = ref([])
  const currentRun = ref(null)
  const discrepancies = ref([])
  const accountHistory = ref({})
  const rules = ref([])
  const stats = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const matchRate = computed(() => {
    if (!stats.value) return 0
    const { matched_count, total_count } = stats.value
    if (!total_count) return 0
    return (matched_count / total_count) * 100
  })

  const totalDiscrepancyValue = computed(() => {
    if (!stats.value) return 0
    return stats.value.total_discrepancy_value || 0
  })

  const criticalDiscrepancies = computed(() =>
    discrepancies.value.filter((d) => d.amount_diff > 1000),
  )

  const unresolvedCount = computed(() =>
    discrepancies.value.filter((d) => d.status === 'unresolved').length,
  )

  async function fetchRuns(force = false) {
    if (runs.value.length > 0 && !force) return runs.value

    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/reconciliation/runs`)
      if (!res.ok) throw new Error(`Failed to fetch runs: ${res.status}`)
      const data = await res.json()
      runs.value = data.runs || []
      return runs.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentRun() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/reconciliation/current`)
      if (!res.ok) throw new Error(`Failed to fetch current run: ${res.status}`)
      const data = await res.json()
      currentRun.value = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchDiscrepancies(params = {}) {
    loading.value = true
    error.value = null
    try {
      const qs = new URLSearchParams(params).toString()
      const url = `${API_BASE}/reconciliation/discrepancies${qs ? `?${qs}` : ''}`
      const res = await fetch(url)
      if (!res.ok)
        throw new Error(`Failed to fetch discrepancies: ${res.status}`)
      const data = await res.json()
      discrepancies.value = data.discrepancies || []
      return discrepancies.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchAccountRecon(accountId, force = false) {
    if (accountHistory.value[accountId] && !force)
      return accountHistory.value[accountId]

    loading.value = true
    error.value = null
    try {
      const res = await fetch(
        `${API_BASE}/reconciliation/account/${accountId}`,
      )
      if (!res.ok) throw new Error(`Account not found: ${accountId}`)
      const data = await res.json()
      accountHistory.value[accountId] = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function resolveDiscrepancy(recordId, resolution) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(
        `${API_BASE}/reconciliation/resolve/${recordId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(resolution),
        },
      )
      if (!res.ok) throw new Error(`Failed to resolve: ${res.status}`)
      const data = await res.json()
      const idx = discrepancies.value.findIndex((d) => d.id === recordId)
      if (idx !== -1) discrepancies.value[idx] = { ...discrepancies.value[idx], ...data }
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchRules() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/reconciliation/rules`)
      if (!res.ok) throw new Error(`Failed to fetch rules: ${res.status}`)
      const data = await res.json()
      rules.value = data.rules || []
      return rules.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchStats(force = false) {
    if (stats.value && !force) return stats.value

    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/reconciliation/stats`)
      if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`)
      const data = await res.json()
      stats.value = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  function clearCache() {
    runs.value = []
    currentRun.value = null
    discrepancies.value = []
    accountHistory.value = {}
    rules.value = []
    stats.value = null
    error.value = null
  }

  return {
    runs,
    currentRun,
    discrepancies,
    accountHistory,
    rules,
    stats,
    loading,
    error,
    matchRate,
    totalDiscrepancyValue,
    criticalDiscrepancies,
    unresolvedCount,
    fetchRuns,
    fetchCurrentRun,
    fetchDiscrepancies,
    fetchAccountRecon,
    resolveDiscrepancy,
    fetchRules,
    fetchStats,
    clearCache,
  }
})
