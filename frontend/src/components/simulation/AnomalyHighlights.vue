<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  simulationId: { type: String, default: '' },
})

const emit = defineEmits(['jump-to-round'])

const anomalies = ref([])
const summary = ref({ total: 0, most_surprising_agent: null, highest_surprise_score: 0, trend: 'stable', total_rounds: 0 })
const loading = ref(false)
const error = ref('')
const expandedId = ref(null)
const chartRef = ref(null)
let resizeObserver = null

const typeLabels = {
  sentiment_reversal: 'Sentiment Reversal',
  unexpected_agreement: 'Unexpected Agreement',
  leadership_emergence: 'Leadership Emergence',
  topic_hijack: 'Topic Hijack',
}

const typeColors = {
  sentiment_reversal: 'var(--color-primary)',
  unexpected_agreement: '#009900',
  leadership_emergence: 'var(--color-accent)',
  topic_hijack: 'var(--color-orange)',
}

const trendIcon = computed(() => {
  if (summary.value.trend === 'increasing') return '\u2197'
  if (summary.value.trend === 'decreasing') return '\u2198'
  return '\u2192'
})

const trendLabel = computed(() => {
  if (summary.value.trend === 'increasing') return 'Increasing'
  if (summary.value.trend === 'decreasing') return 'Decreasing'
  return 'Stable'
})

const trendClass = computed(() => {
  if (summary.value.trend === 'increasing') return 'text-[var(--color-orange)]'
  if (summary.value.trend === 'decreasing') return 'text-[#009900]'
  return 'text-[var(--color-text-muted)]'
})

function isHighSurprise(score) {
  return score >= 0.75
}

async function fetchAnomalies() {
  if (!props.simulationId) return
  loading.value = true
  error.value = ''
  try {
    const res = await simulationApi.getAnomalies(props.simulationId)
    const json = res.data
    if (json.success) {
      anomalies.value = json.data.anomalies
      summary.value = json.data.summary
    } else {
      error.value = json.error || 'Failed to load anomalies'
    }
  } catch (e) {
    error.value = e.message || 'Network error'
  } finally {
    loading.value = false
  }
}

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

function jumpToRound(roundNum) {
  emit('jump-to-round', roundNum)
}

// --- D3 mini bar chart for surprise-score distribution by round ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !anomalies.value.length) return
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const roundMap = new Map()
  for (const a of anomalies.value) {
    if (!roundMap.has(a.round_num)) roundMap.set(a.round_num, [])
    roundMap.get(a.round_num).push(a)
  }
  const data = Array.from(roundMap.entries())
    .map(([round, items]) => ({
      round,
      count: items.length,
      maxSurprise: Math.max(...items.map(i => i.surprise_score)),
    }))
    .sort((a, b) => a.round - b.round)

  const margin = { top: 8, right: 12, bottom: 24, left: 28 }
  const width = containerWidth - margin.left - margin.right
  const height = 80
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const totalRounds = summary.value.total_rounds || Math.max(...data.map(d => d.round))
  const allRounds = Array.from({ length: totalRounds }, (_, i) => i + 1)

  const x = d3.scaleBand()
    .domain(allRounds)
    .range([0, width])
    .padding(0.3)

  const y = d3.scaleLinear()
    .domain([0, Math.max(3, d3.max(data, d => d.count))])
    .range([height, 0])

  const colorScale = d3.scaleLinear()
    .domain([0.3, 0.75, 1])
    .range(['var(--color-primary)', 'var(--color-orange)', '#ef4444'])
    .clamp(true)

  // Grid
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', height).attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.08)')

  // Bars
  const dataMap = new Map(data.map(d => [d.round, d]))
  g.selectAll('.bar')
    .data(allRounds)
    .join('rect')
    .attr('class', 'bar')
    .attr('x', d => x(d))
    .attr('width', x.bandwidth())
    .attr('y', d => {
      const item = dataMap.get(d)
      return item ? y(item.count) : height
    })
    .attr('height', d => {
      const item = dataMap.get(d)
      return item ? height - y(item.count) : 0
    })
    .attr('rx', 2)
    .attr('fill', d => {
      const item = dataMap.get(d)
      if (!item) return 'transparent'
      return colorScale(item.maxSurprise)
    })
    .attr('opacity', d => dataMap.has(d) ? 0.85 : 0)
    .style('cursor', d => dataMap.has(d) ? 'pointer' : 'default')
    .on('click', (event, d) => {
      if (dataMap.has(d)) jumpToRound(d)
    })

  // X labels (sparse)
  const step = Math.max(1, Math.floor(allRounds.length / 8))
  g.selectAll('.x-label')
    .data(allRounds.filter((_, i) => i % step === 0 || i === allRounds.length - 1))
    .join('text')
    .attr('x', d => x(d) + x.bandwidth() / 2)
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted)')
    .text(d => `R${d}`)

  // Y label
  g.append('text')
    .attr('x', -6)
    .attr('y', height / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted)')
    .text('#')
}

watch(() => anomalies.value, () => {
  nextTick(renderChart)
}, { deep: true })

watch(() => props.simulationId, () => {
  fetchAnomalies()
}, { immediate: true })

onMounted(() => {
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => renderChart())
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Anomaly Highlights</h3>
      <button
        v-if="!loading && anomalies.length"
        class="text-[11px] text-[var(--color-primary)] hover:underline"
        @click="fetchAnomalies"
      >
        Refresh
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[120px]">
      <div class="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-sm text-[var(--color-error)] p-3 bg-[var(--color-error-light)] rounded-md">
      {{ error }}
    </div>

    <!-- Empty -->
    <div v-else-if="!anomalies.length" class="flex items-center justify-center h-[120px] text-[var(--color-text-muted)] text-sm">
      <span>No anomalies detected yet</span>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Summary cards -->
      <div class="grid grid-cols-3 gap-3 mb-4">
        <div class="bg-[var(--color-tint)] rounded-md p-3 text-center">
          <div class="text-lg font-bold text-[var(--color-text)]">{{ summary.total }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mt-0.5">Anomalies</div>
        </div>
        <div class="bg-[var(--color-tint)] rounded-md p-3 text-center">
          <div class="text-xs font-semibold text-[var(--color-text)] truncate" :title="summary.most_surprising_agent">
            {{ summary.most_surprising_agent || '—' }}
          </div>
          <div class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mt-0.5">Most Surprising</div>
        </div>
        <div class="bg-[var(--color-tint)] rounded-md p-3 text-center">
          <div class="text-xs font-semibold" :class="trendClass">
            {{ trendIcon }} {{ trendLabel }}
          </div>
          <div class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mt-0.5">Trend</div>
        </div>
      </div>

      <!-- Mini chart: anomalies by round -->
      <div ref="chartRef" class="mb-4" style="height: 112px" />

      <!-- Anomaly list -->
      <div class="space-y-2 max-h-[380px] overflow-y-auto">
        <div
          v-for="anomaly in anomalies"
          :key="anomaly.id"
          class="border rounded-lg p-3 transition-all duration-200 cursor-pointer"
          :class="isHighSurprise(anomaly.surprise_score)
            ? 'border-[var(--color-orange)] bg-[rgba(255,86,0,0.04)] shadow-[0_0_8px_rgba(255,86,0,0.15)]'
            : 'border-[var(--color-border)] hover:border-[var(--color-border-hover)]'"
          @click="toggleExpand(anomaly.id)"
        >
          <!-- Row: agent + score + round -->
          <div class="flex items-center gap-3">
            <!-- Agent info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span
                  class="text-xs font-semibold"
                  :class="isHighSurprise(anomaly.surprise_score) ? 'text-[var(--color-orange)]' : 'text-[var(--color-text)]'"
                >
                  {{ anomaly.agent_name }}
                </span>
                <span
                  class="inline-block px-1.5 py-0.5 text-[10px] rounded-full font-medium"
                  :style="{ background: typeColors[anomaly.type] + '18', color: typeColors[anomaly.type] }"
                >
                  {{ typeLabels[anomaly.type] || anomaly.type }}
                </span>
              </div>
              <p class="text-xs text-[var(--color-text-secondary)] mt-1 leading-relaxed">{{ anomaly.description }}</p>
            </div>

            <!-- Surprise score bar -->
            <div class="flex items-center gap-2 shrink-0 w-[120px]">
              <div class="flex-1 h-2 bg-[var(--color-tint)] rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="{
                    width: (anomaly.surprise_score * 100) + '%',
                    background: isHighSurprise(anomaly.surprise_score)
                      ? 'linear-gradient(90deg, var(--color-orange), #ef4444)'
                      : 'linear-gradient(90deg, var(--color-primary), var(--color-primary-hover))',
                  }"
                />
              </div>
              <span
                class="text-[11px] font-mono font-semibold tabular-nums w-[32px] text-right"
                :class="isHighSurprise(anomaly.surprise_score) ? 'text-[var(--color-orange)]' : 'text-[var(--color-text-muted)]'"
              >
                {{ (anomaly.surprise_score * 100).toFixed(0) }}%
              </span>
            </div>

            <!-- Round badge -->
            <button
              class="shrink-0 px-2 py-1 text-[10px] font-semibold rounded bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-primary)] hover:text-white transition-colors"
              :title="`Jump to round ${anomaly.round_num}`"
              @click.stop="jumpToRound(anomaly.round_num)"
            >
              R{{ anomaly.round_num }}
            </button>
          </div>

          <!-- Expanded explanation -->
          <div
            v-if="expandedId === anomaly.id"
            class="mt-3 pt-3 border-t border-[var(--color-border)] text-xs text-[var(--color-text-secondary)] leading-relaxed"
          >
            <span class="font-medium text-[var(--color-text)]">Why this is unusual:</span>
            {{ anomaly.explanation }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
