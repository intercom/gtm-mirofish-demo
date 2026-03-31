<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useSimulationStore } from '../stores/simulation'
import { generateMockComparison, comparisonApi } from '../api/comparison'
import ComparisonLayout from '../components/comparison/ComparisonLayout.vue'
import ComparisonTable from '../components/comparison/ComparisonTable.vue'
import ComparisonRadar from '../components/comparison/ComparisonRadar.vue'
import ChartOverlay from '../components/comparison/ChartOverlay.vue'
import ComparisonTimeline from '../components/comparison/ComparisonTimeline.vue'
import AbScenarioBuilder from '../components/comparison/AbScenarioBuilder.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useSimulationStore()

const selectedIdA = ref(route.query.a || '')
const selectedIdB = ref(route.query.b || '')
const comparison = ref(null)
const loading = ref(false)
const selectedMetric = ref('sentiment')

const completedRuns = computed(() =>
  store.sessionRuns.filter(r => {
    const s = (r.status || '').toLowerCase()
    return s === 'completed' || s === 'complete'
  }),
)

const runA = computed(() => store.sessionRuns.find(r => r.id === selectedIdA.value))
const runB = computed(() => store.sessionRuns.find(r => r.id === selectedIdB.value))

const canCompare = computed(() =>
  selectedIdA.value && selectedIdB.value && selectedIdA.value !== selectedIdB.value,
)

async function runComparison() {
  if (!canCompare.value || !runA.value || !runB.value) return
  loading.value = true

  // Update URL query params
  router.replace({ query: { a: selectedIdA.value, b: selectedIdB.value } })

  try {
    const { data } = await comparisonApi.compare([selectedIdA.value, selectedIdB.value])
    comparison.value = data
  } catch {
    // Backend not available — use client-side mock
    comparison.value = generateMockComparison(runA.value, runB.value)
  } finally {
    loading.value = false
  }
}

function swapSimulations() {
  const tmpId = selectedIdA.value
  selectedIdA.value = selectedIdB.value
  selectedIdB.value = tmpId
  if (comparison.value) runComparison()
}

function handleDimensionSelect(dimension) {
  const metricMap = {
    'Overall Sentiment': 'sentiment',
    'Agent Engagement': 'actions',
    'Information Spread': 'agents',
  }
  selectedMetric.value = metricMap[dimension] || 'sentiment'
}

// Auto-run comparison if both IDs are set from query params
watch([selectedIdA, selectedIdB], () => {
  if (canCompare.value) runComparison()
}, { immediate: true })
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">{{ t('comparison.title') }}</h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1">{{ t('comparison.subtitle') }}</p>
      </div>
      <router-link
        to="/simulations"
        class="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[#2068FF] transition-colors no-underline"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
        </svg>
        {{ t('comparison.backToSimulations') }}
      </router-link>
    </div>

    <!-- Simulation selectors -->
    <div v-if="completedRuns.length >= 2" class="flex flex-col sm:flex-row items-start sm:items-end gap-3 mb-8">
      <div class="flex-1 min-w-0">
        <label class="flex items-center gap-1.5 text-xs font-medium mb-1.5">
          <span class="w-2 h-2 rounded-full bg-[#2068FF]" />
          <span class="text-[#2068FF]">{{ t('comparison.simulationA') }}</span>
        </label>
        <select
          v-model="selectedIdA"
          class="w-full text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        >
          <option value="" disabled>{{ t('comparison.selectSimulation') }}</option>
          <option
            v-for="run in completedRuns"
            :key="run.id"
            :value="run.id"
            :disabled="run.id === selectedIdB"
          >
            {{ run.scenarioName }} ({{ run.totalActions }} actions, {{ run.totalRounds }} rounds)
          </option>
        </select>
      </div>

      <button
        @click="swapSimulations"
        class="p-2 rounded-lg border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[#2068FF] hover:border-[#2068FF]/50 transition-colors shrink-0"
        :title="t('comparison.swapSimulations')"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
        </svg>
      </button>

      <div class="flex-1 min-w-0">
        <label class="flex items-center gap-1.5 text-xs font-medium mb-1.5">
          <span class="w-2 h-2 rounded-full bg-[#ff5600]" />
          <span class="text-[#ff5600]">{{ t('comparison.simulationB') }}</span>
        </label>
        <select
          v-model="selectedIdB"
          class="w-full text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        >
          <option value="" disabled>{{ t('comparison.selectSimulation') }}</option>
          <option
            v-for="run in completedRuns"
            :key="run.id"
            :value="run.id"
            :disabled="run.id === selectedIdA"
          >
            {{ run.scenarioName }} ({{ run.totalActions }} actions, {{ run.totalRounds }} rounds)
          </option>
        </select>
      </div>
    </div>

    <!-- Not enough simulations -->
    <div v-if="completedRuns.length < 2" class="text-center py-16 md:py-24">
      <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-5">
        <svg class="w-7 h-7 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
        </svg>
      </div>
      <h2 class="text-base font-semibold text-[var(--color-text)] mb-2">{{ t('comparison.needTwoSimulations') }}</h2>
      <p class="text-sm text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
        {{ t('comparison.needTwoSimulationsHint') }}
      </p>
      <router-link
        to="/"
        class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors no-underline"
      >
        {{ t('comparison.runSimulation') }}
      </router-link>
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="space-y-6">
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-8 flex items-center justify-center">
        <div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
          <svg class="w-5 h-5 animate-spin text-[#2068FF]" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ t('comparison.comparing') }}
        </div>
      </div>
    </div>

    <!-- Comparison results -->
    <ComparisonLayout
      v-else-if="comparison"
      :simAName="comparison.simA.name"
      :simBName="comparison.simB.name"
      @swap="swapSimulations"
    >
      <!-- Top: Metrics Table -->
      <ComparisonTable
        :dimensions="comparison.dimensions"
        :simAName="comparison.simA.name"
        :simBName="comparison.simB.name"
        :summary="comparison.summary"
      />

      <!-- Middle: Radar + Chart Overlay -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ComparisonRadar
          :data="comparison.radar"
          :simAName="comparison.simA.name"
          :simBName="comparison.simB.name"
          @selectDimension="handleDimensionSelect"
        />
        <div class="lg:col-span-2">
          <ChartOverlay
            :dataA="comparison.timelineA"
            :dataB="comparison.timelineB"
            :labelA="comparison.simA.name"
            :labelB="comparison.simB.name"
            :metric="selectedMetric"
          />
        </div>
      </div>

      <!-- Bottom: Timeline -->
      <ComparisonTimeline
        :timelineA="comparison.timelineA"
        :timelineB="comparison.timelineB"
        :labelA="comparison.simA.name"
        :labelB="comparison.simB.name"
      />

      <!-- Sidebar: A/B Scenario Builder -->
      <template #sidebar>
        <AbScenarioBuilder />
      </template>
    </ComparisonLayout>

    <!-- Prompt to select -->
    <div
      v-else-if="completedRuns.length >= 2 && !canCompare"
      class="text-center py-16 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg"
    >
      <div class="w-12 h-12 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 7.5 7.5 3m0 0L12 7.5M7.5 3v13.5m13.5-6L16.5 16.5m0 0L12 12m4.5 4.5V3" />
        </svg>
      </div>
      <p class="text-sm text-[var(--color-text-secondary)]">
        {{ t('comparison.selectTwoPrompt') }}
      </p>
    </div>
  </div>
</template>
