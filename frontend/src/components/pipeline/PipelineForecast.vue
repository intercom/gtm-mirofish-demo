<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { pipelineApi } from '../../api/pipeline'

const COLORS = {
  primary: '#2068FF',
  text: '#1a1a1a',
  muted: '#6b7280',
}

const loading = ref(true)
const error = ref(null)
const forecastData = ref(null)

const barChartRef = ref(null)
const areaChartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

async function fetchForecast() {
  loading.value = true
  error.value = null
  try {
    const res = await pipelineApi.getForecast()
    forecastData.value = res.data?.data || res.data
  } catch (e) {
    error.value = e.message || 'Failed to load forecast data'
  } finally {
    loading.value = false
  }
}

const totalForecast = computed(() => forecastData.value?.total_weighted || 0)
const confidenceRange = computed(() => forecastData.value?.confidence_range || 0.15)
const totalLow = computed(() => Math.round(totalForecast.value * (1 - confidenceRange.value)))
const totalHigh = computed(() => Math.round(totalForecast.value * (1 + confidenceRange.value)))
const scenarios = computed(() => forecastData.value?.scenarios || {})

function formatCurrency(value) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value}`
}

// --- Bar Chart: Weighted vs Unweighted by Stage ---

function clearChart(ref) {
  if (ref.value) d3.select(ref.value).selectAll('*').remove()
}

function renderBarChart() {
  clearChart(barChartRef)
  const container = barChartRef.value
  if (!container || !forecastData.value) return

  const stages = forecastData.value.stages
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 12, right: 16, bottom: 40, left: 80 }
  const width = containerWidth - margin.left - margin.right
  const groupHeight = 32
  const groupGap = 14
  const height = stages.length * (groupHeight + groupGap) - groupGap
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(stages, d => d.unweighted_value)

  const x = d3.scaleLinear()
    .domain([0, maxVal * 1.15])
    .range([0, width])

  const y = d3.scaleBand()
    .domain(stages.map(d => d.stage))
    .range([0, height])
    .padding(groupGap / (groupHeight + groupGap))

  const barH = y.bandwidth() / 2 - 1

  // Grid lines
  const ticks = x.ticks(5)
  g.selectAll('.grid')
    .data(ticks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // X-axis labels
  g.selectAll('.x-label')
    .data(ticks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => formatCurrency(d))

  // Stage labels
  g.selectAll('.stage-label')
    .data(stages)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d.stage) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '12px')
    .attr('fill', COLORS.text)
    .text(d => d.stage)

  // Unweighted bars (light)
  g.selectAll('.bar-unweighted')
    .data(stages)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.stage))
    .attr('width', 0)
    .attr('height', barH)
    .attr('rx', 3)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.2)
    .transition()
    .duration(500)
    .delay((d, i) => i * 60)
    .ease(d3.easeCubicOut)
    .attr('width', d => x(d.unweighted_value))

  // Weighted bars (solid)
  g.selectAll('.bar-weighted')
    .data(stages)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.stage) + barH + 2)
    .attr('width', 0)
    .attr('height', barH)
    .attr('rx', 3)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.85)
    .transition()
    .duration(500)
    .delay((d, i) => i * 60)
    .ease(d3.easeCubicOut)
    .attr('width', d => x(d.weighted_value))

  // Value labels for weighted bars
  g.selectAll('.val-weighted')
    .data(stages)
    .join('text')
    .attr('x', d => x(d.weighted_value) + 6)
    .attr('y', d => y(d.stage) + barH + 2 + barH / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .style('opacity', 0)
    .text(d => formatCurrency(d.weighted_value))
    .transition()
    .duration(400)
    .delay((d, i) => i * 60 + 300)
    .style('opacity', 1)

  // Probability labels at bar end
  g.selectAll('.prob-label')
    .data(stages)
    .join('text')
    .attr('x', d => x(d.unweighted_value) + 6)
    .attr('y', d => y(d.stage) + barH / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .style('opacity', 0)
    .text(d => `${Math.round(d.probability * 100)}%`)
    .transition()
    .duration(400)
    .delay((d, i) => i * 60 + 300)
    .style('opacity', 1)
}

// --- Stacked Area Chart: Monthly Projection ---

function renderAreaChart() {
  clearChart(areaChartRef)
  const container = areaChartRef.value
  if (!container || !forecastData.value) return

  const { monthly_projection, stage_names } = forecastData.value
  if (!monthly_projection?.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 12, right: 16, bottom: 36, left: 56 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Stack the data
  const stack = d3.stack()
    .keys(stage_names)
    .order(d3.stackOrderNone)
    .offset(d3.stackOffsetNone)

  const series = stack(monthly_projection)

  const x = d3.scalePoint()
    .domain(monthly_projection.map(d => d.month))
    .range([0, width])
    .padding(0.1)

  const yMax = d3.max(series, layer => d3.max(layer, d => d[1]))

  const y = d3.scaleLinear()
    .domain([0, yMax * 1.1])
    .range([height, 0])

  const colorScale = d3.scaleOrdinal()
    .domain(stage_names)
    .range([
      'rgba(32,104,255,0.15)',
      'rgba(32,104,255,0.25)',
      'rgba(32,104,255,0.40)',
      'rgba(32,104,255,0.55)',
      'rgba(32,104,255,0.70)',
      'rgba(32,104,255,0.85)',
    ])

  const area = d3.area()
    .x(d => x(d.data.month))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(d3.curveMonotoneX)

  // Grid lines
  const yTicks = y.ticks(4)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => formatCurrency(d))

  // Stacked areas
  g.selectAll('.area-layer')
    .data(series)
    .join('path')
    .attr('d', area)
    .attr('fill', d => colorScale(d.key))
    .attr('stroke', COLORS.primary)
    .attr('stroke-width', 0.5)
    .attr('stroke-opacity', 0.3)
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((d, i) => i * 80)
    .style('opacity', 1)

  // X-axis labels
  g.selectAll('.x-label')
    .data(monthly_projection)
    .join('text')
    .attr('x', d => x(d.month))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => d.month)
}

function renderCharts() {
  renderBarChart()
  renderAreaChart()
}

watch(forecastData, () => nextTick(renderCharts))

onMounted(() => {
  fetchForecast()

  const observe = (ref) => {
    if (ref.value) {
      resizeObserver = new ResizeObserver(() => {
        clearTimeout(resizeTimer)
        resizeTimer = setTimeout(renderCharts, 200)
      })
      resizeObserver.observe(ref.value)
    }
  }
  nextTick(() => {
    observe(barChartRef)
  })
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="space-y-5">
    <!-- Loading State -->
    <div v-if="loading" class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-8 flex items-center justify-center">
      <div class="flex items-center gap-3 text-[var(--color-text-muted)] text-sm">
        <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25" />
          <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="3" stroke-linecap="round" class="opacity-75" />
        </svg>
        Loading forecast data...
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-[var(--color-surface)] border border-red-200 rounded-lg p-6 text-center">
      <p class="text-red-600 text-sm">{{ error }}</p>
      <button
        class="mt-3 px-3 py-1.5 text-xs font-medium text-[#2068FF] border border-[#2068FF] rounded hover:bg-[#2068FF]/5 transition-colors"
        @click="fetchForecast"
      >
        Retry
      </button>
    </div>

    <template v-else-if="forecastData">
      <!-- Total Forecast KPI -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <div class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">
          Weighted Pipeline Forecast
        </div>
        <div class="flex items-baseline gap-3">
          <span class="text-3xl font-bold text-[#2068FF]">
            {{ formatCurrency(totalForecast) }}
          </span>
          <span class="text-sm text-[var(--color-text-muted)]">
            &plusmn;{{ Math.round(confidenceRange * 100) }}%
            <span class="text-xs">({{ formatCurrency(totalLow) }} – {{ formatCurrency(totalHigh) }})</span>
          </span>
        </div>
        <div class="text-xs text-[var(--color-text-muted)] mt-1">
          Unweighted: {{ formatCurrency(forecastData.total_unweighted) }}
        </div>
      </div>

      <!-- Scenario Summary: Best / Expected / Worst -->
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
          <div class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">Best Case</div>
          <div class="text-lg font-bold text-[#009900]">{{ formatCurrency(scenarios.best_case) }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">90th percentile</div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[#2068FF]/30 rounded-lg p-4 text-center">
          <div class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">Expected</div>
          <div class="text-lg font-bold text-[#2068FF]">{{ formatCurrency(scenarios.expected) }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">50th percentile</div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
          <div class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">Worst Case</div>
          <div class="text-lg font-bold text-[#ff5600]">{{ formatCurrency(scenarios.worst_case) }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">10th percentile</div>
        </div>
      </div>

      <!-- Bar Chart: Weighted vs Unweighted -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Pipeline Value by Stage</h3>
        <p class="text-xs text-[var(--color-text-muted)] mb-3">Weighted (solid) vs unweighted (light) value per stage</p>
        <div ref="barChartRef" />
        <!-- Legend -->
        <div class="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-2 rounded-sm bg-[#2068FF]/20" /> Unweighted
          </span>
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-2 rounded-sm bg-[#2068FF]/85" /> Weighted
          </span>
        </div>
      </div>

      <!-- Stacked Area Chart: Monthly Projection -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Expected Close Timeline</h3>
        <p class="text-xs text-[var(--color-text-muted)] mb-3">Projected deal close values by month and stage</p>
        <div ref="areaChartRef" />
        <!-- Legend -->
        <div class="flex flex-wrap items-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
          <span v-for="(stage, i) in (forecastData.stage_names || [])" :key="stage" class="flex items-center gap-1.5">
            <span
              class="inline-block w-3 h-2 rounded-sm"
              :style="{ backgroundColor: `rgba(32,104,255,${0.15 + i * 0.14})` }"
            />
            {{ stage }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>
