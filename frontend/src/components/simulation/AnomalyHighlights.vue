<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  simulationId: { type: String, required: true },
  actions: { type: Array, default: () => [] },
})

const emit = defineEmits(['jump-to-round'])

const anomalies = ref([])
const loading = ref(false)
const expandedId = ref(null)
const explanationCache = ref({})
const loadingExplanation = ref(null)

async function fetchAnomalies() {
  if (!props.simulationId) return
  loading.value = true
  try {
    const res = await simulationApi.getAnomalies(props.simulationId)
    if (res.data?.success) {
      anomalies.value = res.data.data.anomalies || []
    }
  } catch {
    anomalies.value = []
  } finally {
    loading.value = false
  }
}

async function toggleExplanation(anomaly) {
  if (expandedId.value === anomaly.anomaly_id) {
    expandedId.value = null
    return
  }
  expandedId.value = anomaly.anomaly_id

  if (explanationCache.value[anomaly.anomaly_id]) return
  if (anomaly.explanation) {
    explanationCache.value[anomaly.anomaly_id] = anomaly.explanation
    return
  }

  loadingExplanation.value = anomaly.anomaly_id
  try {
    const res = await simulationApi.getAnomalyExplanation(props.simulationId, anomaly.anomaly_id)
    if (res.data?.success) {
      explanationCache.value[anomaly.anomaly_id] = res.data.data.explanation
    }
  } catch {
    explanationCache.value[anomaly.anomaly_id] = anomaly.description
  } finally {
    loadingExplanation.value = null
  }
}

const summary = computed(() => {
  const list = anomalies.value
  if (!list.length) return null

  const topAgent = list[0]
  const types = {}
  for (const a of list) {
    types[a.anomaly_type] = (types[a.anomaly_type] || 0) + 1
  }

  // Trend: compare first half vs second half anomaly counts
  const rounds = list.map(a => a.round_num).sort((a, b) => a - b)
  const midRound = rounds[Math.floor(rounds.length / 2)]
  const firstHalf = list.filter(a => a.round_num <= midRound).length
  const secondHalf = list.filter(a => a.round_num > midRound).length
  let trend = 'stable'
  if (secondHalf > firstHalf * 1.3) trend = 'increasing'
  else if (firstHalf > secondHalf * 1.3) trend = 'decreasing'

  return {
    total: list.length,
    mostSurprising: topAgent.agent_name,
    topScore: topAgent.surprise_score,
    trend,
    types,
  }
})

const typeLabels = {
  sentiment_reversal: 'Sentiment Reversal',
  unexpected_agreement: 'Unexpected Agreement',
  leadership_emergence: 'Leadership Emergence',
  topic_hijacking: 'Topic Hijacking',
}

const typeColors = {
  sentiment_reversal: '#ff5600',
  unexpected_agreement: '#2068FF',
  leadership_emergence: '#009900',
  topic_hijacking: '#9333ea',
}

function surpriseBarWidth(score) {
  return `${Math.round(score * 100)}%`
}

function surpriseBarColor(score) {
  if (score >= 0.8) return '#ef4444'
  if (score >= 0.5) return '#f59e0b'
  return '#2068FF'
}

function isHighSurprise(score) {
  return score >= 0.8
}

const trendIcon = computed(() => {
  if (!summary.value) return ''
  if (summary.value.trend === 'increasing') return '\u2191'
  if (summary.value.trend === 'decreasing') return '\u2193'
  return '\u2192'
})

const trendLabel = computed(() => {
  if (!summary.value) return ''
  if (summary.value.trend === 'increasing') return 'Increasing'
  if (summary.value.trend === 'decreasing') return 'Decreasing'
  return 'Stable'
})

onMounted(fetchAnomalies)

watch(() => props.actions.length, () => {
  fetchAnomalies()
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Behavior Anomalies</h3>
      <button
        v-if="anomalies.length"
        class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors"
        @click="fetchAnomalies"
      >
        Refresh
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading && !anomalies.length" class="flex items-center justify-center h-[120px] text-[var(--color-text-muted)] text-sm">
      <span class="animate-pulse">Analyzing agent behaviors...</span>
    </div>

    <!-- Empty state -->
    <div v-else-if="!anomalies.length" class="flex items-center justify-center h-[120px] text-[var(--color-text-muted)] text-sm">
      <span>Anomalies will appear as agents interact</span>
    </div>

    <template v-else>
      <!-- Summary -->
      <div v-if="summary" class="grid grid-cols-3 gap-3 mb-4">
        <div class="bg-[var(--color-tint)] rounded-lg px-3 py-2 text-center">
          <div class="text-lg font-semibold text-[var(--color-text)]">{{ summary.total }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Total Anomalies</div>
        </div>
        <div class="bg-[var(--color-tint)] rounded-lg px-3 py-2 text-center truncate">
          <div class="text-xs font-semibold text-[var(--color-text)] truncate" :title="summary.mostSurprising">
            {{ summary.mostSurprising.split(' ')[0] }}
          </div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Most Surprising</div>
        </div>
        <div class="bg-[var(--color-tint)] rounded-lg px-3 py-2 text-center">
          <div class="text-sm font-semibold text-[var(--color-text)]">
            {{ trendIcon }} {{ trendLabel }}
          </div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Trend</div>
        </div>
      </div>

      <!-- Anomaly list -->
      <div class="space-y-2 max-h-[400px] overflow-y-auto">
        <div
          v-for="anomaly in anomalies"
          :key="anomaly.anomaly_id"
          class="border rounded-lg p-3 transition-all cursor-pointer hover:shadow-sm"
          :class="isHighSurprise(anomaly.surprise_score)
            ? 'border-red-300 bg-red-50/50 shadow-[0_0_8px_rgba(239,68,68,0.15)]'
            : 'border-[var(--color-border)] bg-[var(--color-surface)]'"
          @click="toggleExplanation(anomaly)"
        >
          <!-- Header row -->
          <div class="flex items-start justify-between gap-2 mb-1.5">
            <div class="flex items-center gap-2 min-w-0">
              <span
                class="shrink-0 w-2 h-2 rounded-full"
                :style="{ backgroundColor: typeColors[anomaly.anomaly_type] || '#888' }"
              />
              <span
                class="text-xs font-semibold truncate"
                :class="isHighSurprise(anomaly.surprise_score) ? 'text-red-700' : 'text-[var(--color-text)]'"
              >
                {{ anomaly.agent_name }}
              </span>
            </div>
            <button
              class="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors"
              @click.stop="emit('jump-to-round', anomaly.round_num)"
            >
              R{{ anomaly.round_num }}
            </button>
          </div>

          <!-- Type badge + description -->
          <div class="mb-2">
            <span
              class="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded-full mb-1"
              :style="{
                color: typeColors[anomaly.anomaly_type] || '#888',
                backgroundColor: (typeColors[anomaly.anomaly_type] || '#888') + '15',
              }"
            >
              {{ typeLabels[anomaly.anomaly_type] || anomaly.anomaly_type }}
            </span>
            <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">
              {{ anomaly.description }}
            </p>
          </div>

          <!-- Surprise score bar -->
          <div class="flex items-center gap-2">
            <span class="text-[10px] text-[var(--color-text-muted)] w-14 shrink-0">Surprise</span>
            <div class="flex-1 h-1.5 bg-[var(--color-tint)] rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :style="{
                  width: surpriseBarWidth(anomaly.surprise_score),
                  backgroundColor: surpriseBarColor(anomaly.surprise_score),
                }"
              />
            </div>
            <span
              class="text-[10px] font-mono w-8 text-right shrink-0"
              :class="isHighSurprise(anomaly.surprise_score) ? 'text-red-600 font-bold' : 'text-[var(--color-text-muted)]'"
            >
              {{ (anomaly.surprise_score * 100).toFixed(0) }}%
            </span>
          </div>

          <!-- Expanded explanation -->
          <Transition name="expand">
            <div v-if="expandedId === anomaly.anomaly_id" class="mt-3 pt-3 border-t border-[var(--color-border)]">
              <div v-if="loadingExplanation === anomaly.anomaly_id" class="text-xs text-[var(--color-text-muted)] animate-pulse">
                Generating explanation...
              </div>
              <p v-else class="text-xs text-[var(--color-text-secondary)] leading-relaxed italic">
                {{ explanationCache[anomaly.anomaly_id] || anomaly.description }}
              </p>
            </div>
          </Transition>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex flex-wrap gap-3 mt-4 pt-3 border-t border-[var(--color-border)]">
        <span
          v-for="(label, type) in typeLabels"
          :key="type"
          class="flex items-center gap-1.5 text-[10px] text-[var(--color-text-muted)]"
        >
          <span
            class="inline-block w-2 h-2 rounded-full"
            :style="{ backgroundColor: typeColors[type] }"
          />
          {{ label }}
        </span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 200px;
}
</style>
