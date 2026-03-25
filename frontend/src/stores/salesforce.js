import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { salesforceApi } from '../api/salesforce'

export const useSalesforceStore = defineStore('salesforce', () => {
  const stats = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const totalAccounts = computed(() => stats.value?.total_accounts ?? 0)
  const totalArr = computed(() => stats.value?.total_arr ?? 0)
  const avgHealthScore = computed(() => stats.value?.avg_health_score ?? 0)
  const pipelineValue = computed(() => stats.value?.pipeline_value ?? 0)
  const industryBreakdown = computed(() => stats.value?.industry_breakdown ?? [])
  const stageDistribution = computed(() => stats.value?.stage_distribution ?? [])

  async function fetchStats() {
    loading.value = true
    error.value = null
    try {
      const { data } = await salesforceApi.getStats()
      stats.value = data.data
    } catch (e) {
      error.value = e.message || 'Failed to load Salesforce stats'
    } finally {
      loading.value = false
    }
  }

  return {
    stats,
    loading,
    error,
    totalAccounts,
    totalArr,
    avgHealthScore,
    pipelineValue,
    industryBreakdown,
    stageDistribution,
    fetchStats,
  }
})
