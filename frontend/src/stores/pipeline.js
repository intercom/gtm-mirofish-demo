import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { pipelineApi } from '../api/pipeline'

const DEMO_FUNNEL = {
  stages: [
    { name: 'Leads', count: 2450, value: 12250000 },
    { name: 'MQL', count: 980, value: 7840000 },
    { name: 'SQL', count: 490, value: 5880000 },
    { name: 'Opportunity', count: 196, value: 4704000 },
    { name: 'Proposal', count: 98, value: 2940000 },
    { name: 'Closed Won', count: 39, value: 1560000 },
  ],
}

const DEMO_FUNNEL_HISTORY = [
  { month: '2025-10', stages: [2200, 880, 440, 176, 88, 32] },
  { month: '2025-11', stages: [2300, 920, 460, 184, 92, 35] },
  { month: '2025-12', stages: [2350, 940, 470, 188, 94, 37] },
  { month: '2026-01', stages: [2400, 960, 480, 192, 96, 38] },
  { month: '2026-02', stages: [2420, 968, 484, 194, 97, 38] },
  { month: '2026-03', stages: [2450, 980, 490, 196, 98, 39] },
]

const DEMO_CONVERSIONS = {
  overall: 0.0159,
  byStage: [
    { from: 'Leads', to: 'MQL', rate: 0.40 },
    { from: 'MQL', to: 'SQL', rate: 0.50 },
    { from: 'SQL', to: 'Opportunity', rate: 0.40 },
    { from: 'Opportunity', to: 'Proposal', rate: 0.50 },
    { from: 'Proposal', to: 'Closed Won', rate: 0.398 },
  ],
  trend: [
    { month: '2025-10', rate: 0.0145 },
    { month: '2025-11', rate: 0.0152 },
    { month: '2025-12', rate: 0.0157 },
    { month: '2026-01', rate: 0.0158 },
    { month: '2026-02', rate: 0.0157 },
    { month: '2026-03', rate: 0.0159 },
  ],
}

const DEMO_VELOCITY = {
  avgCycleDays: 34,
  byStage: [
    { stage: 'Leads → MQL', days: 8 },
    { stage: 'MQL → SQL', days: 6 },
    { stage: 'SQL → Opportunity', days: 7 },
    { stage: 'Opportunity → Proposal', days: 8 },
    { stage: 'Proposal → Closed Won', days: 5 },
  ],
  trend: [
    { month: '2025-10', days: 38 },
    { month: '2025-11', days: 36 },
    { month: '2025-12', days: 35 },
    { month: '2026-01', days: 35 },
    { month: '2026-02', days: 34 },
    { month: '2026-03', days: 34 },
  ],
}

const DEMO_FORECAST = {
  current: 5880000,
  projected: 7200000,
  quarters: [
    { quarter: 'Q1 2026', projected: 4680000, confidence: 0.85 },
    { quarter: 'Q2 2026', projected: 7200000, confidence: 0.70 },
    { quarter: 'Q3 2026', projected: 8100000, confidence: 0.55 },
  ],
}

export const usePipelineStore = defineStore('pipeline', () => {
  const funnelData = ref(null)
  const funnelHistory = ref([])
  const conversions = ref(null)
  const velocity = ref(null)
  const forecast = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const overallConversionRate = computed(() =>
    conversions.value?.overall ?? 0,
  )

  const avgCycleTime = computed(() =>
    velocity.value?.avgCycleDays ?? 0,
  )

  const totalPipelineValue = computed(() => {
    if (!funnelData.value?.stages) return 0
    const open = funnelData.value.stages.filter(s => s.name !== 'Closed Won')
    return open.reduce((sum, s) => sum + (s.value || 0), 0)
  })

  const forecastedRevenue = computed(() =>
    forecast.value?.projected ?? 0,
  )

  async function fetchFunnel(force = false) {
    if (funnelData.value && !force) return funnelData.value
    loading.value = true
    error.value = null
    try {
      const { data } = await pipelineApi.getFunnel()
      funnelData.value = data
    } catch {
      funnelData.value = DEMO_FUNNEL
    } finally {
      loading.value = false
    }
    return funnelData.value
  }

  async function fetchFunnelHistory(months = 6) {
    loading.value = true
    error.value = null
    try {
      const { data } = await pipelineApi.getFunnelHistory(months)
      funnelHistory.value = data.history ?? data
    } catch {
      funnelHistory.value = DEMO_FUNNEL_HISTORY.slice(-months)
    } finally {
      loading.value = false
    }
    return funnelHistory.value
  }

  async function fetchConversions(dateRange) {
    loading.value = true
    error.value = null
    try {
      const { data } = await pipelineApi.getConversions(dateRange)
      conversions.value = data
    } catch {
      conversions.value = DEMO_CONVERSIONS
    } finally {
      loading.value = false
    }
    return conversions.value
  }

  async function fetchVelocity() {
    loading.value = true
    error.value = null
    try {
      const { data } = await pipelineApi.getVelocity()
      velocity.value = data
    } catch {
      velocity.value = DEMO_VELOCITY
    } finally {
      loading.value = false
    }
    return velocity.value
  }

  async function fetchForecast() {
    loading.value = true
    error.value = null
    try {
      const { data } = await pipelineApi.getForecast()
      forecast.value = data
    } catch {
      forecast.value = DEMO_FORECAST
    } finally {
      loading.value = false
    }
    return forecast.value
  }

  function reset() {
    funnelData.value = null
    funnelHistory.value = []
    conversions.value = null
    velocity.value = null
    forecast.value = null
    loading.value = false
    error.value = null
  }

  return {
    funnelData,
    funnelHistory,
    conversions,
    velocity,
    forecast,
    loading,
    error,
    overallConversionRate,
    avgCycleTime,
    totalPipelineValue,
    forecastedRevenue,
    fetchFunnel,
    fetchFunnelHistory,
    fetchConversions,
    fetchVelocity,
    fetchForecast,
    reset,
  }
})
