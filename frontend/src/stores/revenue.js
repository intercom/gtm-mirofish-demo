import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { revenueApi } from '../api/revenue'

export const useRevenueStore = defineStore('revenue', () => {
  const metrics = ref([])
  const customers = ref([])
  const churnEvents = ref([])
  const expansionEvents = ref([])
  const summary = ref(null)
  const cohortData = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // --- Getters (derived from summary or latest metric) ---

  const latestMetric = computed(() => {
    if (!metrics.value.length) return null
    return metrics.value[metrics.value.length - 1]
  })

  const currentMrr = computed(() => summary.value?.current_mrr ?? latestMetric.value?.mrr ?? 0)
  const currentArr = computed(() => summary.value?.arr ?? currentMrr.value * 12)
  const growthRate = computed(() => summary.value?.growth_rate ?? 0)
  const netRetention = computed(() => summary.value?.net_retention ?? 0)
  const grossRetention = computed(() => summary.value?.gross_retention ?? 0)

  const avgMrr = computed(() => {
    if (!customers.value.length) return 0
    const total = customers.value.reduce((sum, c) => sum + (c.mrr || 0), 0)
    return total / customers.value.length
  })

  // --- Actions ---

  async function fetchMetrics(months = 12) {
    loading.value = true
    error.value = null
    try {
      const res = await revenueApi.getMetrics({ months })
      metrics.value = res.data.metrics || []
      return metrics.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchCustomers(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await revenueApi.getCustomers(filters)
      customers.value = res.data.customers || []
      return customers.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchChurn(dateRange = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await revenueApi.getChurnEvents(dateRange)
      churnEvents.value = res.data.events || []
      return churnEvents.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchExpansion(dateRange = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await revenueApi.getExpansionEvents(dateRange)
      expansionEvents.value = res.data.events || []
      return expansionEvents.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary() {
    loading.value = true
    error.value = null
    try {
      const res = await revenueApi.getSummary()
      summary.value = res.data
      return summary.value
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchCohort() {
    loading.value = true
    error.value = null
    try {
      const res = await revenueApi.getCohortData()
      cohortData.value = res.data
      return cohortData.value
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    metrics,
    customers,
    churnEvents,
    expansionEvents,
    summary,
    cohortData,
    loading,
    error,
    latestMetric,
    currentMrr,
    currentArr,
    growthRate,
    netRetention,
    grossRetention,
    avgMrr,
    fetchMetrics,
    fetchCustomers,
    fetchChurn,
    fetchExpansion,
    fetchSummary,
    fetchCohort,
  }
})
