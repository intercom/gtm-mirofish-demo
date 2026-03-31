<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSimulationStore } from '../../stores/simulation'
import client from '../../api/client'

const store = useSimulationStore()
const insights = ref([])
const loading = ref(false)
const error = ref(null)

const runs = computed(() => store.sessionRuns)
const hasEnoughData = computed(() => runs.value.length >= 2)

const CATEGORY_META = {
  configuration: { label: 'Configuration', icon: '⚙️', variant: 'primary' },
  template: { label: 'Template', icon: '📋', variant: 'orange' },
  channels: { label: 'Channels', icon: '📡', variant: 'info' },
  trend: { label: 'Trend', icon: '📈', variant: 'success' },
  strategic: { label: 'Strategic', icon: '🎯', variant: 'warning' },
}

const CONFIDENCE_COLORS = {
  high: 'bg-[var(--badge-success-bg-soft)] text-[var(--badge-success-text-soft)]',
  medium: 'bg-[var(--badge-warning-bg-soft)] text-[var(--badge-warning-text-soft)]',
  low: 'bg-[var(--badge-error-bg-soft)] text-[var(--badge-error-text-soft)]',
}

function categoryMeta(category) {
  return CATEGORY_META[category] || CATEGORY_META.strategic
}

function confidenceClass(level) {
  return CONFIDENCE_COLORS[level] || CONFIDENCE_COLORS.medium
}

function generateClientInsights(runData) {
  const results = []
  const completed = runData.filter((r) => r.status === 'completed')
  const source = completed.length >= 2 ? completed : runData

  if (source.length < 2) return results

  // Agent count correlation
  const highAgent = source.filter((r) => (r.agentCount || 0) >= 6)
  const lowAgent = source.filter((r) => (r.agentCount || 0) < 6 && (r.agentCount || 0) > 0)
  if (highAgent.length && lowAgent.length) {
    const avgHigh = highAgent.reduce((s, r) => s + (r.totalActions || 0), 0) / highAgent.length
    const avgLow = lowAgent.reduce((s, r) => s + (r.totalActions || 0), 0) / lowAgent.length
    if (avgLow > 0) {
      const pct = Math.round(((avgHigh - avgLow) / avgLow) * 100)
      if (pct > 0) {
        results.push({
          id: 'agent-count-actions',
          text: `Simulations with 6+ agents produce ${pct}% more actions than those with 5 or fewer.`,
          confidence: highAgent.length >= 3 && lowAgent.length >= 3 ? 'high' : 'medium',
          category: 'configuration',
          supporting_data: { avg_6plus: Math.round(avgHigh), avg_5_or_less: Math.round(avgLow) },
        })
      }
    }
  }

  // Best template
  const byScenario = {}
  for (const r of source) {
    const name = r.scenarioName || 'Unknown'
    if (!byScenario[name]) byScenario[name] = []
    byScenario[name].push(r.totalActions || 0)
  }
  const scenarioNames = Object.keys(byScenario)
  if (scenarioNames.length >= 2) {
    const ranked = scenarioNames
      .map((n) => ({ name: n, avg: byScenario[n].reduce((a, b) => a + b, 0) / byScenario[n].length }))
      .sort((a, b) => b.avg - a.avg)
    results.push({
      id: 'best-template',
      text: `The "${ranked[0].name}" template produces the most engagement with an average of ${Math.round(ranked[0].avg)} actions per run.`,
      confidence: byScenario[ranked[0].name].length >= 3 ? 'high' : 'medium',
      category: 'template',
      supporting_data: { best: ranked[0].name, best_avg: Math.round(ranked[0].avg) },
    })
  }

  // Channel distribution
  const totalTw = source.reduce((s, r) => s + (r.twitterActions || 0), 0)
  const totalRd = source.reduce((s, r) => s + (r.redditActions || 0), 0)
  const totalSocial = totalTw + totalRd
  if (totalSocial > 0) {
    const twPct = Math.round((totalTw / totalSocial) * 100)
    results.push({
      id: 'channel-distribution',
      text: `Twitter/X drives ${twPct}% of all social actions across simulations, with Reddit accounting for ${100 - twPct}%.`,
      confidence: 'high',
      category: 'channels',
      supporting_data: { twitter_pct: twPct, reddit_pct: 100 - twPct },
    })
  }

  // Trend over time
  if (source.length >= 3) {
    const sorted = [...source].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
    const half = Math.floor(sorted.length / 2)
    const first = sorted.slice(0, half)
    const second = sorted.slice(half)
    const avgFirst = first.reduce((s, r) => s + (r.totalActions || 0), 0) / first.length
    const avgSecond = second.reduce((s, r) => s + (r.totalActions || 0), 0) / second.length
    if (avgFirst > 0) {
      const trendPct = Math.round(((avgSecond - avgFirst) / avgFirst) * 100)
      if (Math.abs(trendPct) >= 5) {
        const direction = trendPct > 0 ? 'improving' : 'declining'
        results.push({
          id: 'trend-over-time',
          text: `Simulation engagement is ${direction} — recent runs average ${Math.abs(trendPct)}% ${trendPct > 0 ? 'more' : 'fewer'} actions than earlier ones.`,
          confidence: source.length >= 5 ? 'medium' : 'low',
          category: 'trend',
          supporting_data: { earlier_avg: Math.round(avgFirst), recent_avg: Math.round(avgSecond) },
        })
      }
    }
  }

  return results
}

async function fetchInsights() {
  if (!hasEnoughData.value) return
  loading.value = true
  error.value = null

  // Always compute client-side insights first as a baseline
  const clientInsights = generateClientInsights(runs.value)

  try {
    const { data } = await client.post('/insights/generate', { runs: runs.value })
    if (data?.success && data.data?.insights?.length) {
      insights.value = data.data.insights
    } else {
      insights.value = clientInsights
    }
  } catch {
    insights.value = clientInsights
  } finally {
    loading.value = false
  }
}

const expandedCards = ref(new Set())

function toggleCard(id) {
  if (expandedCards.value.has(id)) {
    expandedCards.value.delete(id)
  } else {
    expandedCards.value.add(id)
  }
}

function formatKey(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

onMounted(fetchInsights)
</script>

<template>
  <div class="insights-summary">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-base font-semibold text-[var(--color-text)]">Cross-Run Insights</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Patterns detected across {{ runs.length }} simulation{{ runs.length !== 1 ? 's' : '' }}
        </p>
      </div>
      <button
        v-if="hasEnoughData && !loading"
        class="text-xs text-[#2068FF] hover:text-[#1a5ae0] font-medium transition-colors"
        @click="fetchInsights"
      >
        Refresh
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="!hasEnoughData"
      class="flex flex-col items-center justify-center py-10 text-center"
    >
      <div class="w-12 h-12 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mb-3">
        <span class="text-2xl">💡</span>
      </div>
      <p class="text-sm font-medium text-[var(--color-text)] mb-1">Not enough data yet</p>
      <p class="text-xs text-[var(--color-text-muted)] max-w-[240px]">
        Run at least 2 simulations to see cross-run pattern insights.
      </p>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="space-y-3">
      <div
        v-for="i in 3"
        :key="i"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 overflow-hidden"
      >
        <div class="shimmer-line rounded w-1/4 mb-3" />
        <div class="shimmer-line rounded w-full mb-2" />
        <div class="shimmer-line rounded w-3/4" />
      </div>
    </div>

    <!-- Error fallback -->
    <div v-else-if="error && !insights.length" class="text-sm text-[var(--color-text-muted)] py-4">
      {{ error }}
    </div>

    <!-- Insight cards -->
    <div v-else class="space-y-3">
      <div
        v-for="insight in insights"
        :key="insight.id"
        class="insight-card bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-4 transition-shadow hover:shadow-md cursor-pointer"
        @click="toggleCard(insight.id)"
      >
        <div class="flex items-start gap-3">
          <span class="text-lg mt-0.5 shrink-0">{{ categoryMeta(insight.category).icon }}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1.5 flex-wrap">
              <span
                class="inline-flex items-center rounded-full text-[10px] font-medium px-2 py-0.5"
                :class="{
                  'bg-[var(--badge-primary-bg)] text-[var(--badge-primary-text)]': categoryMeta(insight.category).variant === 'primary',
                  'bg-[var(--badge-orange-bg-soft)] text-[var(--badge-orange-text-soft)]': categoryMeta(insight.category).variant === 'orange',
                  'bg-[var(--badge-secondary-bg)] text-[var(--badge-secondary-text)]': categoryMeta(insight.category).variant === 'info',
                  'bg-[var(--badge-success-bg-soft)] text-[var(--badge-success-text-soft)]': categoryMeta(insight.category).variant === 'success',
                  'bg-[var(--badge-warning-bg-soft)] text-[var(--badge-warning-text-soft)]': categoryMeta(insight.category).variant === 'warning',
                }"
              >
                {{ categoryMeta(insight.category).label }}
              </span>
              <span
                class="inline-flex items-center rounded-full text-[10px] font-medium px-2 py-0.5"
                :class="confidenceClass(insight.confidence)"
              >
                {{ insight.confidence }} confidence
              </span>
              <span
                v-if="insight.source === 'llm'"
                class="inline-flex items-center rounded-full text-[10px] font-medium px-2 py-0.5 bg-[rgba(170,0,255,0.1)] text-[#AA00FF]"
              >
                AI-generated
              </span>
            </div>
            <p class="text-sm text-[var(--color-text)] leading-relaxed">{{ insight.text }}</p>

            <!-- Expandable supporting data -->
            <transition name="expand">
              <div
                v-if="expandedCards.has(insight.id) && insight.supporting_data"
                class="mt-3 pt-3 border-t border-[var(--color-border)]"
              >
                <p class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold mb-2">
                  Supporting Data
                </p>
                <div class="grid grid-cols-2 gap-2">
                  <div
                    v-for="(value, key) in insight.supporting_data"
                    :key="key"
                    class="text-xs"
                  >
                    <span class="text-[var(--color-text-muted)]">{{ formatKey(key) }}:</span>
                    <span class="text-[var(--color-text)] font-medium ml-1">
                      {{ typeof value === 'object' ? JSON.stringify(value) : value }}
                    </span>
                  </div>
                </div>
              </div>
            </transition>
          </div>
          <svg
            class="w-4 h-4 text-[var(--color-text-muted)] shrink-0 mt-1 transition-transform"
            :class="{ 'rotate-180': expandedCards.has(insight.id) }"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shimmer-line {
  height: 12px;
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.04) 25%,
    rgba(0, 0, 0, 0.08) 50%,
    rgba(0, 0, 0, 0.04) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

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
