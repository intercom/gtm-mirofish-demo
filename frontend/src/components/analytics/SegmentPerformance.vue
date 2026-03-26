<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'
import { analyticsApi } from '../../api/analytics'

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const segmentType = ref('plan_tier')
const data = ref(null)
const loading = ref(false)
const error = ref(null)
const viewMode = ref('bar') // 'bar' | 'radar' | 'trend'
const selectedSegment = ref(null) // for drill-down
const drillDownAccounts = ref([])
const drillDownLoading = ref(false)

const SEGMENT_TYPES = [
  { value: 'plan_tier', label: 'Plan Tier' },
  { value: 'industry', label: 'Industry' },
  { value: 'company_size', label: 'Company Size' },
  { value: 'region', label: 'Region' },
]

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  navy: '#050505',
  gray: '#888',
}

const SEGMENT_COLORS = ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#6366f1']

// Active metric for bar chart
const activeMetric = ref('mrr')

const metricKeys = computed(() =>
  data.value ? Object.keys(data.value.metrics) : [],
)

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

async function fetchData() {
  loading.value = true
  error.value = null
  selectedSegment.value = null
  drillDownAccounts.value = []
  try {
    const res = await analyticsApi.getSegments(segmentType.value)
    data.value = res.data
  } catch (e) {
    error.value = e.message || 'Failed to load segment data'
  } finally {
    loading.value = false
  }
}

async function fetchAccounts(segName) {
  if (selectedSegment.value === segName) {
    selectedSegment.value = null
    drillDownAccounts.value = []
    return
  }
  selectedSegment.value = segName
  drillDownLoading.value = true
  try {
    const res = await analyticsApi.getSegmentAccounts(segmentType.value, segName)
    drillDownAccounts.value = res.data.accounts
  } catch {
    drillDownAccounts.value = []
  } finally {
    drillDownLoading.value = false
  }
}

// ---------------------------------------------------------------------------
// Chart refs & resize
// ---------------------------------------------------------------------------

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderActiveChart() {
  clearChart()
  if (!chartRef.value || !data.value) return
  nextTick(() => {
    if (viewMode.value === 'bar') renderBarChart()
    else if (viewMode.value === 'radar') renderRadarChart()
    else if (viewMode.value === 'trend') renderTrendChart()
  })
}

// ---------------------------------------------------------------------------
// Chart 1: Grouped Bar — Segments side-by-side for one metric
// ---------------------------------------------------------------------------

function renderBarChart() {
  const container = chartRef.value
  if (!container) return

  const segments = data.value.segments
  const metric = activeMetric.value
  const higherIsBetter = data.value.metric_direction[metric]

  const barData = segments.map((s, i) => ({
    name: s.name,
    value: s.metrics[metric],
    color: SEGMENT_COLORS[i % SEGMENT_COLORS.length],
    tag: s.tags?.[metric],
  }))

  const containerWidth = container.clientWidth
  const margin = { top: 20, right: 24, bottom: 48, left: 56 }
  const width = containerWidth - margin.left - margin.right
  const height = 240
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(barData, d => d.value) * 1.15

  const x = d3.scaleBand()
    .domain(barData.map(d => d.name))
    .range([0, width])
    .padding(0.3)

  const y = d3.scaleLinear()
    .domain([0, maxVal])
    .range([height, 0])

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8).attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => metric === 'mrr' ? `$${d.toLocaleString()}` : d)

  // Bars with animation
  g.selectAll('.bar')
    .data(barData)
    .join('rect')
    .attr('x', d => x(d.name))
    .attr('y', height)
    .attr('width', x.bandwidth())
    .attr('height', 0)
    .attr('rx', 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.85)
    .attr('cursor', 'pointer')
    .on('click', (_, d) => fetchAccounts(d.name))
    .transition()
    .duration(600)
    .delay((_, i) => i * 80)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.value))
    .attr('height', d => height - y(d.value))

  // Value labels
  g.selectAll('.val-label')
    .data(barData)
    .join('text')
    .attr('x', d => x(d.name) + x.bandwidth() / 2)
    .attr('y', d => y(d.value) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', d => d.color)
    .style('opacity', 0)
    .text(d => metric === 'mrr' ? `$${d.value.toLocaleString()}` : d.value)
    .transition()
    .duration(300)
    .delay((_, i) => 600 + i * 80)
    .style('opacity', 1)

  // Best/worst badges
  g.selectAll('.badge')
    .data(barData.filter(d => d.tag))
    .join('text')
    .attr('x', d => x(d.name) + x.bandwidth() / 2)
    .attr('y', d => y(d.value) - 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('font-weight', '700')
    .attr('fill', d => d.tag === 'best'
      ? (higherIsBetter ? COLORS.green : COLORS.orange)
      : (higherIsBetter ? COLORS.orange : COLORS.green))
    .style('opacity', 0)
    .text(d => d.tag === 'best' ? 'BEST' : 'WORST')
    .transition()
    .duration(300)
    .delay((_, i) => 700 + i * 80)
    .style('opacity', 1)

  // X-axis labels
  g.selectAll('.x-label')
    .data(barData)
    .join('text')
    .attr('x', d => x(d.name) + x.bandwidth() / 2)
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .attr('cursor', 'pointer')
    .text(d => d.name)
    .on('click', (_, d) => fetchAccounts(d.name))

  // Subtitle
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height + 40)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text('Click a segment bar to view individual accounts')
}

// ---------------------------------------------------------------------------
// Chart 2: Radar — Multi-metric comparison across segments
// ---------------------------------------------------------------------------

function renderRadarChart() {
  const container = chartRef.value
  if (!container) return

  const segments = data.value.segments
  const metrics = metricKeys.value
  const direction = data.value.metric_direction
  const labels = data.value.metrics

  const containerWidth = container.clientWidth
  const size = Math.min(containerWidth, 420)
  const cx = containerWidth / 2
  const cy = size / 2 + 10
  const radius = size / 2 - 60
  const angleSlice = (2 * Math.PI) / metrics.length
  const totalHeight = size + 40

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${cx},${cy})`)

  // Normalize metric values to 0-1 for radar
  const ranges = {}
  for (const m of metrics) {
    const vals = segments.map(s => s.metrics[m])
    const min = d3.min(vals) * 0.8
    const max = d3.max(vals) * 1.2
    ranges[m] = { min, max }
  }

  function normalize(metric, value) {
    const { min, max } = ranges[metric]
    let norm = (value - min) / (max - min || 1)
    // For churn_rate, invert so lower = better = farther from center
    if (!direction[metric]) norm = 1 - norm
    return Math.max(0, Math.min(1, norm))
  }

  // Grid rings
  const levels = 4
  for (let lev = 1; lev <= levels; lev++) {
    const r = (radius / levels) * lev
    g.append('circle')
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0,0,0,0.08)')
      .attr('stroke-dasharray', '2,3')
  }

  // Axis lines + labels
  for (let i = 0; i < metrics.length; i++) {
    const angle = angleSlice * i - Math.PI / 2
    const xEnd = Math.cos(angle) * radius
    const yEnd = Math.sin(angle) * radius

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', xEnd).attr('y2', yEnd)
      .attr('stroke', 'rgba(0,0,0,0.1)')

    const labelR = radius + 18
    const xLabel = Math.cos(angle) * labelR
    const yLabel = Math.sin(angle) * labelR

    // Shorten labels for display
    const shortLabel = labels[metrics[i]]
      .replace('Net Revenue Retention', 'NRR')
      .replace('Avg MRR ($)', 'Avg MRR')
      .replace('Expansion Rate (%)', 'Expansion')
      .replace('Churn Rate (%)', 'Churn')
      .replace('CSAT Score', 'CSAT')

    g.append('text')
      .attr('x', xLabel)
      .attr('y', yLabel)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('fill', '#555')
      .text(shortLabel)
  }

  // Radar polygons per segment
  const radarLine = d3.lineRadial()
    .radius(d => d.r)
    .angle(d => d.angle)
    .curve(d3.curveCardinalClosed.tension(0.2))

  segments.forEach((seg, idx) => {
    const color = SEGMENT_COLORS[idx % SEGMENT_COLORS.length]
    const points = metrics.map((m, i) => ({
      angle: angleSlice * i,
      r: normalize(m, seg.metrics[m]) * radius,
    }))

    // Area fill
    g.append('path')
      .datum(points)
      .attr('d', radarLine)
      .attr('fill', color)
      .attr('fill-opacity', 0.08)
      .attr('stroke', color)
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0)
      .transition()
      .duration(600)
      .delay(idx * 100)
      .attr('stroke-opacity', 0.7)

    // Data points
    g.selectAll(`.dot-${idx}`)
      .data(points)
      .join('circle')
      .attr('cx', d => Math.cos(d.angle - Math.PI / 2) * d.r)
      .attr('cy', d => Math.sin(d.angle - Math.PI / 2) * d.r)
      .attr('r', 0)
      .attr('fill', color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .transition()
      .duration(300)
      .delay(600 + idx * 100)
      .attr('r', 3.5)
  })

  // Legend at bottom
  const legendG = svg.append('g')
    .attr('transform', `translate(${cx - (segments.length * 70) / 2},${totalHeight - 18})`)

  segments.forEach((seg, i) => {
    const lx = i * 70
    legendG.append('rect')
      .attr('x', lx).attr('y', 0)
      .attr('width', 8).attr('height', 8)
      .attr('rx', 2)
      .attr('fill', SEGMENT_COLORS[i % SEGMENT_COLORS.length])

    legendG.append('text')
      .attr('x', lx + 12).attr('y', 8)
      .attr('font-size', '10px')
      .attr('fill', '#555')
      .text(seg.name.length > 8 ? seg.name.slice(0, 7) + '…' : seg.name)
  })
}

// ---------------------------------------------------------------------------
// Chart 3: Trend Lines — Performance over time per segment
// ---------------------------------------------------------------------------

function renderTrendChart() {
  const container = chartRef.value
  if (!container) return

  const trends = data.value.trends
  const metric = activeMetric.value
  const months = trends.months
  const segNames = Object.keys(trends.segments)

  const containerWidth = container.clientWidth
  const margin = { top: 20, right: 80, bottom: 32, left: 56 }
  const width = containerWidth - margin.left - margin.right
  const height = 240
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Collect all values for Y domain
  const allVals = segNames.flatMap(name =>
    trends.segments[name].map(p => p[metric]),
  )
  const yMin = d3.min(allVals) * 0.95
  const yMax = d3.max(allVals) * 1.05

  const x = d3.scalePoint()
    .domain(months)
    .range([0, width])
    .padding(0.1)

  const y = d3.scaleLinear()
    .domain([yMin, yMax])
    .range([height, 0])

  // Grid
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8).attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => metric === 'mrr' ? `$${d.toLocaleString()}` : d)

  // X-axis
  g.selectAll('.x-label')
    .data(months)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => d)

  // Lines per segment
  const line = d3.line()
    .x(d => x(d.month))
    .y(d => y(d[metric]))
    .curve(d3.curveMonotoneX)

  segNames.forEach((name, idx) => {
    const color = SEGMENT_COLORS[idx % SEGMENT_COLORS.length]
    const segData = trends.segments[name]

    const path = g.append('path')
      .datum(segData)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2)

    // Animate line drawing
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .delay(idx * 120)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Dots
    g.selectAll(`.dot-${idx}`)
      .data(segData)
      .join('circle')
      .attr('cx', d => x(d.month))
      .attr('cy', d => y(d[metric]))
      .attr('r', 0)
      .attr('fill', color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .transition()
      .duration(300)
      .delay(800 + idx * 120)
      .attr('r', 3.5)

    // Segment label at end
    const last = segData[segData.length - 1]
    g.append('text')
      .attr('x', width + 8)
      .attr('y', y(last[metric]))
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('fill', color)
      .attr('font-weight', '600')
      .style('opacity', 0)
      .text(name.length > 10 ? name.slice(0, 9) + '…' : name)
      .transition()
      .duration(300)
      .delay(800 + idx * 120)
      .style('opacity', 1)
  })
}

// ---------------------------------------------------------------------------
// Watchers & lifecycle
// ---------------------------------------------------------------------------

watch(segmentType, () => fetchData())
watch([viewMode, activeMetric], () => renderActiveChart())
watch(data, () => {
  nextTick(() => {
    renderActiveChart()
    // Re-attach resize observer when chart element re-enters DOM
    if (chartRef.value && resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver.observe(chartRef.value)
    }
  })
})

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(renderActiveChart, 200)
  })
  fetchData()
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Segment Performance</h3>

      <div class="flex items-center gap-2 flex-wrap">
        <!-- Segment type selector -->
        <select
          v-model="segmentType"
          class="text-xs border border-[var(--color-border)] rounded-md px-2 py-1.5 bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[#2068FF]"
        >
          <option v-for="t in SEGMENT_TYPES" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </select>

        <!-- View mode tabs -->
        <div class="flex gap-0.5 bg-[var(--color-tint)] rounded-md p-0.5">
          <button
            v-for="mode in [
              { key: 'bar', label: 'Bar' },
              { key: 'radar', label: 'Radar' },
              { key: 'trend', label: 'Trends' },
            ]"
            :key="mode.key"
            class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
            :class="viewMode === mode.key
              ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
            @click="viewMode = mode.key"
          >
            {{ mode.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Metric selector (bar + trend views) -->
    <div v-if="viewMode !== 'radar' && data" class="flex gap-1.5 mb-4 flex-wrap">
      <button
        v-for="m in metricKeys"
        :key="m"
        class="px-2.5 py-1 text-[11px] rounded-full font-medium transition-colors border"
        :class="activeMetric === m
          ? 'bg-[#2068FF] text-white border-[#2068FF]'
          : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[#2068FF] hover:text-[#2068FF]'"
        @click="activeMetric = m"
      >
        {{ data.metrics[m] }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[300px]">
      <div class="animate-spin rounded-full h-6 w-6 border-2 border-[#2068FF] border-t-transparent" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-[300px] text-sm text-[var(--color-text-muted)]">
      {{ error }}
    </div>

    <!-- Chart -->
    <div v-else ref="chartRef" class="w-full" style="min-height: 300px" />

    <!-- Drill-down panel -->
    <div
      v-if="selectedSegment"
      class="mt-4 border-t border-[var(--color-border)] pt-4"
    >
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-xs font-semibold text-[var(--color-text)]">
          {{ selectedSegment }} — Individual Accounts
        </h4>
        <button
          class="text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
          @click="selectedSegment = null; drillDownAccounts = []"
        >
          Close
        </button>
      </div>

      <div v-if="drillDownLoading" class="flex justify-center py-4">
        <div class="animate-spin rounded-full h-5 w-5 border-2 border-[#2068FF] border-t-transparent" />
      </div>

      <div v-else-if="drillDownAccounts.length" class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="text-left text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <th class="py-2 pr-4 font-medium">Account</th>
              <th class="py-2 pr-4 font-medium">MRR</th>
              <th class="py-2 pr-4 font-medium">NRR</th>
              <th class="py-2 pr-4 font-medium">Churn Risk</th>
              <th class="py-2 pr-4 font-medium">CSAT</th>
              <th class="py-2 font-medium">Last Active</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="acct in drillDownAccounts"
              :key="acct.name"
              class="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-tint)] transition-colors"
            >
              <td class="py-2 pr-4 font-medium text-[var(--color-text)]">{{ acct.name }}</td>
              <td class="py-2 pr-4 text-[var(--color-text-secondary)]">${{ acct.mrr.toLocaleString() }}</td>
              <td class="py-2 pr-4 text-[var(--color-text-secondary)]">{{ acct.nrr }}%</td>
              <td class="py-2 pr-4">
                <span
                  class="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium"
                  :class="acct.churn_risk > 60
                    ? 'bg-red-50 text-red-600'
                    : acct.churn_risk > 30
                      ? 'bg-amber-50 text-amber-600'
                      : 'bg-green-50 text-green-600'"
                >
                  {{ acct.churn_risk }}%
                </span>
              </td>
              <td class="py-2 pr-4 text-[var(--color-text-secondary)]">{{ acct.csat }}</td>
              <td class="py-2 text-[var(--color-text-muted)]">{{ acct.last_active }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
