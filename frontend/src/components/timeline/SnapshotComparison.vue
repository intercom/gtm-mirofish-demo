<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '@/api/simulation'

const props = defineProps({
  simulationId: { type: String, required: true },
  totalRounds: { type: Number, default: 144 },
})

const emit = defineEmits(['compare'])

// --- State ---
const roundA = ref(1)
const roundB = ref(props.totalRounds)
const loading = ref(false)
const error = ref(null)
const comparisonData = ref(null)

// --- Preset comparisons ---
const presets = computed(() => [
  { label: 'First vs Last', a: 1, b: props.totalRounds },
  { label: 'Early vs Mid', a: 1, b: Math.floor(props.totalRounds / 2) },
  { label: 'Mid vs Late', a: Math.floor(props.totalRounds / 2), b: props.totalRounds },
  { label: 'Q1 vs Q2', a: 1, b: Math.floor(props.totalRounds / 4) },
  { label: 'Before vs After Decision', a: Math.floor(props.totalRounds * 0.3), b: Math.floor(props.totalRounds * 0.7) },
])

function applyPreset(preset) {
  roundA.value = preset.a
  roundB.value = preset.b
  fetchComparison()
}

// --- API ---
async function fetchComparison() {
  if (!props.simulationId) return
  loading.value = true
  error.value = null
  try {
    const res = await simulationApi.snapshotCompare(props.simulationId, roundA.value, roundB.value)
    comparisonData.value = res.data?.data || res.data
    emit('compare', comparisonData.value)
    await nextTick()
    renderCharts()
  } catch (e) {
    error.value = e.message || 'Failed to fetch comparison'
  } finally {
    loading.value = false
  }
}

// --- Computed helpers ---
const pointA = computed(() => comparisonData.value?.point_a)
const pointB = computed(() => comparisonData.value?.point_b)
const diff = computed(() => comparisonData.value?.diff)

const metricKeys = [
  { key: 'totalActions', label: 'Total Actions', icon: '⚡' },
  { key: 'twitterActions', label: 'Twitter', icon: '🐦' },
  { key: 'redditActions', label: 'Reddit', icon: '💬' },
  { key: 'activeAgents', label: 'Active Agents', icon: '👥' },
]

function formatDelta(val) {
  if (val > 0) return `+${val}`
  return String(val)
}

function formatPct(val) {
  if (val > 0) return `+${val}%`
  if (val < 0) return `${val}%`
  return '0%'
}

function deltaClass(delta) {
  if (delta > 0) return 'text-[#009900]'
  if (delta < 0) return 'text-[#ff5600]'
  return 'text-[var(--color-text-muted)]'
}

function sentimentLabel(val) {
  if (val > 0.1) return 'Positive'
  if (val < -0.1) return 'Negative'
  return 'Neutral'
}

function sentimentColor(val) {
  if (val > 0.1) return '#009900'
  if (val < -0.1) return '#ff5600'
  return '#2068FF'
}

// --- D3 Charts ---
const agentChartRef = ref(null)
const sentimentChartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clearCharts() {
  if (agentChartRef.value) d3.select(agentChartRef.value).selectAll('*').remove()
  if (sentimentChartRef.value) d3.select(sentimentChartRef.value).selectAll('*').remove()
}

function renderCharts() {
  clearCharts()
  if (!comparisonData.value) return
  renderAgentChart()
  renderSentimentChart()
}

function renderAgentChart() {
  const container = agentChartRef.value
  if (!container || !pointA.value || !pointB.value) return

  const agentsA = new Map(pointA.value.agents.map(a => [a.name, a]))
  const agentsB = new Map(pointB.value.agents.map(a => [a.name, a]))
  const allNames = [...new Set([...agentsA.keys(), ...agentsB.keys()])]
  if (!allNames.length) return

  const data = allNames.map(name => ({
    name: name.split(' (')[0],
    fullName: name,
    a: agentsA.get(name)?.actionCount || 0,
    b: agentsB.get(name)?.actionCount || 0,
    status: !agentsA.has(name) ? 'new' : !agentsB.has(name) ? 'removed' : 'changed',
  })).sort((x, y) => (y.b - y.a) - (x.b - x.a))

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 20, right: 16, bottom: 4, left: 120 }
  const barHeight = 22
  const gap = 6
  const width = containerWidth - margin.left - margin.right
  const height = data.length * (barHeight + gap)
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(data, d => Math.max(d.a, d.b)) || 1

  const x = d3.scaleLinear().domain([0, maxVal]).range([0, width])

  // Agent labels
  g.selectAll('.agent-label')
    .data(data)
    .join('text')
    .attr('x', -8)
    .attr('y', (_, i) => i * (barHeight + gap) + barHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('fill', d => {
      if (d.status === 'new') return '#009900'
      if (d.status === 'removed') return '#ff5600'
      return 'var(--color-text-secondary, #555)'
    })
    .text(d => d.name)

  // Point A bars (lighter)
  g.selectAll('.bar-a')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', (_, i) => i * (barHeight + gap))
    .attr('height', barHeight / 2 - 1)
    .attr('rx', 2)
    .attr('fill', 'rgba(32, 104, 255, 0.3)')
    .attr('width', 0)
    .transition()
    .duration(500)
    .delay((_, i) => i * 30)
    .attr('width', d => x(d.a))

  // Point B bars (solid)
  g.selectAll('.bar-b')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', (_, i) => i * (barHeight + gap) + barHeight / 2)
    .attr('height', barHeight / 2 - 1)
    .attr('rx', 2)
    .attr('fill', d => {
      if (d.status === 'new') return '#009900'
      if (d.status === 'removed') return 'rgba(255, 86, 0, 0.4)'
      return '#2068FF'
    })
    .attr('width', 0)
    .transition()
    .duration(500)
    .delay((_, i) => i * 30)
    .attr('width', d => x(d.b))

  // Delta labels
  g.selectAll('.delta-label')
    .data(data)
    .join('text')
    .attr('x', d => x(Math.max(d.a, d.b)) + 6)
    .attr('y', (_, i) => i * (barHeight + gap) + barHeight / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', d => {
      const delta = d.b - d.a
      if (delta > 0) return '#009900'
      if (delta < 0) return '#ff5600'
      return '#888'
    })
    .style('opacity', 0)
    .text(d => {
      const delta = d.b - d.a
      if (d.status === 'new') return 'NEW'
      if (d.status === 'removed') return 'GONE'
      if (delta === 0) return '—'
      return delta > 0 ? `+${delta}` : String(delta)
    })
    .transition()
    .duration(300)
    .delay((_, i) => 500 + i * 30)
    .style('opacity', 1)

  // Legend
  const legend = svg.append('g')
    .attr('transform', `translate(${margin.left}, 4)`)

  const legendItems = [
    { label: `Round ${pointA.value.round}`, color: 'rgba(32, 104, 255, 0.3)' },
    { label: `Round ${pointB.value.round}`, color: '#2068FF' },
  ]
  legendItems.forEach((item, i) => {
    legend.append('rect')
      .attr('x', i * 100)
      .attr('y', 0)
      .attr('width', 12)
      .attr('height', 8)
      .attr('rx', 2)
      .attr('fill', item.color)
    legend.append('text')
      .attr('x', i * 100 + 16)
      .attr('y', 4)
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('fill', 'var(--color-text-muted, #888)')
      .text(item.label)
  })
}

function renderSentimentChart() {
  const container = sentimentChartRef.value
  if (!container || !pointA.value || !pointB.value) return

  const agentsA = new Map(pointA.value.agents.map(a => [a.name, a]))
  const agentsB = new Map(pointB.value.agents.map(a => [a.name, a]))
  const allNames = [...new Set([...agentsA.keys(), ...agentsB.keys()])]
  if (!allNames.length) return

  const data = allNames.map(name => ({
    name: name.split(' (')[0],
    a: agentsA.get(name)?.sentiment || 0,
    b: agentsB.get(name)?.sentiment || 0,
  })).sort((x, y) => (y.b - y.a) - (x.b - x.a))

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 12, right: 40, bottom: 12, left: 12 }
  const dotSize = 28
  const width = containerWidth - margin.left - margin.right
  const height = data.length * dotSize
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear().domain([-1, 1]).range([0, width])

  // Zero line
  g.append('line')
    .attr('x1', x(0)).attr('x2', x(0))
    .attr('y1', 0).attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.1)')
    .attr('stroke-dasharray', '3,3')

  // Region labels
  g.append('text').attr('x', x(-0.5)).attr('y', -2)
    .attr('text-anchor', 'middle').attr('font-size', '9px')
    .attr('fill', '#ff5600').text('Negative')
  g.append('text').attr('x', x(0.5)).attr('y', -2)
    .attr('text-anchor', 'middle').attr('font-size', '9px')
    .attr('fill', '#009900').text('Positive')

  // Arrows from A to B
  data.forEach((d, i) => {
    const y = i * dotSize + dotSize / 2

    // Arrow line
    g.append('line')
      .attr('x1', x(d.a)).attr('x2', x(d.a))
      .attr('y1', y).attr('y2', y)
      .attr('stroke', d.b > d.a ? '#009900' : d.b < d.a ? '#ff5600' : '#888')
      .attr('stroke-width', 1.5)
      .attr('opacity', 0.6)
      .transition()
      .duration(500)
      .delay(i * 30)
      .attr('x2', x(d.b))

    // Point A (hollow circle)
    g.append('circle')
      .attr('cx', x(d.a)).attr('cy', y)
      .attr('r', 4)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(32, 104, 255, 0.5)')
      .attr('stroke-width', 1.5)

    // Point B (filled circle)
    g.append('circle')
      .attr('cx', x(d.a)).attr('cy', y)
      .attr('r', 0)
      .attr('fill', sentimentColor(d.b))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .transition()
      .duration(500)
      .delay(i * 30)
      .attr('cx', x(d.b))
      .attr('r', 5)

    // Agent name
    g.append('text')
      .attr('x', width + 6).attr('y', y)
      .attr('dy', '0.35em')
      .attr('font-size', '9px')
      .attr('fill', 'var(--color-text-muted, #888)')
      .text(d.name)
  })
}

// --- Lifecycle ---
onMounted(() => {
  fetchComparison()

  if (agentChartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderCharts, 200)
    })
    resizeObserver.observe(agentChartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})

watch(() => props.totalRounds, (val) => {
  roundB.value = val
})
</script>

<template>
  <div class="space-y-5">
    <!-- Header + Controls -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Snapshot Comparison</h3>

      <!-- Preset buttons -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button
          v-for="preset in presets"
          :key="preset.label"
          class="px-3 py-1.5 text-xs font-medium rounded-md border transition-colors"
          :class="roundA === preset.a && roundB === preset.b
            ? 'bg-[#2068FF] text-white border-[#2068FF]'
            : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[#2068FF] hover:text-[#2068FF]'"
          @click="applyPreset(preset)"
        >
          {{ preset.label }}
        </button>
      </div>

      <!-- Round pickers -->
      <div class="flex items-center gap-4">
        <div class="flex-1">
          <label class="block text-xs text-[var(--color-text-muted)] mb-1">Point A — Round</label>
          <div class="flex items-center gap-2">
            <input
              v-model.number="roundA"
              type="range"
              :min="1"
              :max="totalRounds"
              class="flex-1 accent-[#2068FF]"
            />
            <span class="text-sm font-mono font-semibold text-[var(--color-text)] w-10 text-right">{{ roundA }}</span>
          </div>
        </div>
        <div class="flex items-center pt-4 text-[var(--color-text-muted)]">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 10h12m-4-4 4 4-4 4" />
          </svg>
        </div>
        <div class="flex-1">
          <label class="block text-xs text-[var(--color-text-muted)] mb-1">Point B — Round</label>
          <div class="flex items-center gap-2">
            <input
              v-model.number="roundB"
              type="range"
              :min="1"
              :max="totalRounds"
              class="flex-1 accent-[#2068FF]"
            />
            <span class="text-sm font-mono font-semibold text-[var(--color-text)] w-10 text-right">{{ roundB }}</span>
          </div>
        </div>
        <button
          class="mt-4 px-4 py-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
          :disabled="loading"
          @click="fetchComparison"
        >
          {{ loading ? 'Loading...' : 'Compare' }}
        </button>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="w-6 h-6 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Results -->
    <template v-if="comparisonData && !loading">
      <!-- Summary stats bar -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 flex items-center gap-6">
        <div class="flex items-center gap-2">
          <span class="text-xs text-[var(--color-text-muted)]">Total Changes</span>
          <span class="text-lg font-bold text-[var(--color-text)]">{{ diff.totalChanges }}</span>
        </div>
        <div class="w-px h-8 bg-[var(--color-border)]" />
        <div class="flex items-center gap-2">
          <span class="text-xs text-[var(--color-text-muted)]">Biggest Change</span>
          <span class="text-sm font-semibold text-[var(--color-text)]">{{ diff.biggestChange.description }}</span>
        </div>
        <div class="w-px h-8 bg-[var(--color-border)]" />
        <div class="flex items-center gap-2">
          <span class="text-xs text-[var(--color-text-muted)]">Most Affected</span>
          <span class="text-sm font-semibold text-[var(--color-text)]">{{ diff.mostAffectedAgent.name.split(' (')[0] }}</span>
        </div>
        <div class="w-px h-8 bg-[var(--color-border)]" />
        <div class="flex items-center gap-2">
          <span class="text-xs text-[var(--color-text-muted)]">Sentiment Shift</span>
          <span class="text-sm font-semibold" :class="deltaClass(diff.sentimentDelta)">
            {{ diff.sentimentDelta >= 0 ? '+' : '' }}{{ diff.sentimentDelta.toFixed(3) }}
          </span>
        </div>
      </div>

      <!-- Metrics side-by-side -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div
          v-for="m in metricKeys"
          :key="m.key"
          class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4"
        >
          <div class="flex items-center gap-1.5 mb-3">
            <span class="text-base">{{ m.icon }}</span>
            <span class="text-xs font-medium text-[var(--color-text-muted)]">{{ m.label }}</span>
          </div>
          <div class="flex items-end justify-between">
            <div>
              <div class="text-xs text-[var(--color-text-muted)]">R{{ pointA.round }}</div>
              <div class="text-lg font-bold text-[var(--color-text)]">{{ diff.metrics[m.key]?.a?.toLocaleString() }}</div>
            </div>
            <div class="text-center px-2">
              <div class="text-xs font-semibold" :class="deltaClass(diff.metrics[m.key]?.delta)">
                {{ formatDelta(diff.metrics[m.key]?.delta) }}
              </div>
              <div class="text-[10px]" :class="deltaClass(diff.metrics[m.key]?.pctChange)">
                {{ formatPct(diff.metrics[m.key]?.pctChange) }}
              </div>
            </div>
            <div class="text-right">
              <div class="text-xs text-[var(--color-text-muted)]">R{{ pointB.round }}</div>
              <div class="text-lg font-bold text-[var(--color-text)]">{{ diff.metrics[m.key]?.b?.toLocaleString() }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Overall sentiment comparison -->
      <div class="grid grid-cols-2 gap-3">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
          <div class="text-xs text-[var(--color-text-muted)] mb-1">Sentiment at Round {{ pointA.round }}</div>
          <div class="text-2xl font-bold" :style="{ color: sentimentColor(pointA.sentimentAvg) }">
            {{ pointA.sentimentAvg >= 0 ? '+' : '' }}{{ pointA.sentimentAvg.toFixed(3) }}
          </div>
          <div class="text-xs mt-1" :style="{ color: sentimentColor(pointA.sentimentAvg) }">
            {{ sentimentLabel(pointA.sentimentAvg) }}
          </div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
          <div class="text-xs text-[var(--color-text-muted)] mb-1">Sentiment at Round {{ pointB.round }}</div>
          <div class="text-2xl font-bold" :style="{ color: sentimentColor(pointB.sentimentAvg) }">
            {{ pointB.sentimentAvg >= 0 ? '+' : '' }}{{ pointB.sentimentAvg.toFixed(3) }}
          </div>
          <div class="text-xs mt-1" :style="{ color: sentimentColor(pointB.sentimentAvg) }">
            {{ sentimentLabel(pointB.sentimentAvg) }}
          </div>
        </div>
      </div>

      <!-- Agent activity comparison (D3 chart) -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Agent Activity Comparison</h3>
        <div ref="agentChartRef" class="w-full" />
      </div>

      <!-- Agent sentiment shift (D3 chart) -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Sentiment Shift by Agent</h3>
        <div ref="sentimentChartRef" class="w-full" />
      </div>

      <!-- Agent changes table -->
      <div
        v-if="diff.agentChanges.length || diff.newAgents.length || diff.removedAgents.length"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5"
      >
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Change Details</h3>

        <!-- New agents -->
        <div v-if="diff.newAgents.length" class="mb-3">
          <div class="text-xs font-medium text-[#009900] mb-1">New Agents ({{ diff.newAgents.length }})</div>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="agent in diff.newAgents"
              :key="agent.name"
              class="px-2 py-0.5 text-xs rounded-full bg-[rgba(0,153,0,0.08)] text-[#009900] border border-[rgba(0,153,0,0.2)]"
            >
              {{ agent.name.split(' (')[0] }}
            </span>
          </div>
        </div>

        <!-- Removed agents -->
        <div v-if="diff.removedAgents.length" class="mb-3">
          <div class="text-xs font-medium text-[#ff5600] mb-1">Removed Agents ({{ diff.removedAgents.length }})</div>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="agent in diff.removedAgents"
              :key="agent.name"
              class="px-2 py-0.5 text-xs rounded-full bg-[rgba(255,86,0,0.08)] text-[#ff5600] border border-[rgba(255,86,0,0.2)]"
            >
              {{ agent.name.split(' (')[0] }}
            </span>
          </div>
        </div>

        <!-- Changed metrics table -->
        <div v-if="diff.agentChanges.length" class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-[var(--color-border)]">
                <th class="text-left py-2 font-medium text-[var(--color-text-muted)]">Agent</th>
                <th class="text-left py-2 font-medium text-[var(--color-text-muted)]">Metric</th>
                <th class="text-right py-2 font-medium text-[var(--color-text-muted)]">R{{ pointA.round }}</th>
                <th class="text-right py-2 font-medium text-[var(--color-text-muted)]">R{{ pointB.round }}</th>
                <th class="text-right py-2 font-medium text-[var(--color-text-muted)]">Change</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(change, i) in diff.agentChanges.slice(0, 20)"
                :key="i"
                class="border-b border-[var(--color-border)] last:border-0"
              >
                <td class="py-1.5 text-[var(--color-text)]">{{ change.agent.split(' (')[0] }}</td>
                <td class="py-1.5 text-[var(--color-text-secondary)]">
                  <span
                    class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                    :class="change.metric === 'sentiment'
                      ? 'bg-[rgba(32,104,255,0.08)] text-[#2068FF]'
                      : 'bg-[rgba(0,0,0,0.04)] text-[var(--color-text-secondary)]'"
                  >
                    {{ change.metric }}
                  </span>
                </td>
                <td class="py-1.5 text-right font-mono text-[var(--color-text)]">
                  {{ typeof change.oldValue === 'number' && change.metric === 'sentiment' ? change.oldValue.toFixed(3) : change.oldValue }}
                </td>
                <td class="py-1.5 text-right font-mono text-[var(--color-text)]">
                  {{ typeof change.newValue === 'number' && change.metric === 'sentiment' ? change.newValue.toFixed(3) : change.newValue }}
                </td>
                <td class="py-1.5 text-right font-mono font-semibold" :class="deltaClass(change.change)">
                  {{ typeof change.change === 'number' && change.metric === 'sentiment'
                    ? (change.change >= 0 ? '+' : '') + change.change.toFixed(3)
                    : formatDelta(change.change) }}
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="diff.agentChanges.length > 20" class="text-xs text-[var(--color-text-muted)] mt-2 text-center">
            Showing 20 of {{ diff.agentChanges.length }} changes
          </div>
        </div>
      </div>
    </template>

    <!-- Empty state -->
    <div
      v-if="!comparisonData && !loading && !error"
      class="flex flex-col items-center justify-center py-16 text-center"
    >
      <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mb-4">
        <span class="text-3xl">📊</span>
      </div>
      <h3 class="text-base font-semibold text-[var(--color-text)] mb-1">No comparison data</h3>
      <p class="text-sm text-[var(--color-text-muted)] max-w-sm">
        Select two timeline points and click Compare to see how the simulation evolved.
      </p>
    </div>
  </div>
</template>
