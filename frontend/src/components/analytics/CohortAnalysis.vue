<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { analyticsApi } from '../../api/analytics'

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
}

const DIMENSIONS = [
  { value: 'signup_date', label: 'Signup Date' },
  { value: 'plan_tier', label: 'Plan Tier' },
  { value: 'source_channel', label: 'Source Channel' },
  { value: 'region', label: 'Region' },
]

const METRICS = [
  { value: 'retention_rate', label: 'Retention Rate', unit: '%' },
  { value: 'expansion_rate', label: 'Expansion Rate', unit: '%' },
  { value: 'churn_rate', label: 'Churn Rate', unit: '%' },
  { value: 'lifetime_value', label: 'Lifetime Value', unit: '$' },
]

const dimension = ref('signup_date')
const metric = ref('retention_rate')
const viewMode = ref('heatmap')
const compareMode = ref(false)
const selectedCohortA = ref(0)
const selectedCohortB = ref(1)

const loading = ref(false)
const error = ref(null)
const cohortData = ref(null)
const comparisonData = ref(null)

const heatmapRef = ref(null)
const lineChartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const currentMetric = computed(() => METRICS.find(m => m.value === metric.value))

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await analyticsApi.getCohorts({
      dimension: dimension.value,
      metric: metric.value,
    })
    cohortData.value = res.data.data

    if (compareMode.value) {
      await fetchComparison()
    }
  } catch (e) {
    error.value = e.message || 'Failed to load cohort data'
  } finally {
    loading.value = false
  }
}

async function fetchComparison() {
  try {
    const res = await analyticsApi.compareCohorts({
      dimension: dimension.value,
      metric: metric.value,
      cohort_a: selectedCohortA.value,
      cohort_b: selectedCohortB.value,
    })
    comparisonData.value = res.data.data
  } catch (e) {
    comparisonData.value = null
  }
}

function formatValue(val) {
  const m = currentMetric.value
  if (!m) return val
  if (m.unit === '$') return `$${Math.round(val).toLocaleString()}`
  return `${val}%`
}

// --- Heatmap ---

function renderHeatmap() {
  const container = heatmapRef.value
  if (!container || !cohortData.value) return

  d3.select(container).selectAll('*').remove()

  const data = cohortData.value
  const rows = data.cohorts
  const cols = data.periods
  const values = data.heatmap
  const scale = data.color_scale

  const containerWidth = container.clientWidth
  const labelWidth = 110
  const cellSize = Math.max(28, Math.min(48, (containerWidth - labelWidth - 60) / cols.length))
  const cellGap = 2
  const rowHeight = cellSize + cellGap
  const margin = { top: 60, right: 20, bottom: 40, left: labelWidth }
  const width = cols.length * (cellSize + cellGap)
  const height = rows.length * rowHeight
  const totalWidth = width + margin.left + margin.right
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', Math.max(containerWidth, totalWidth))
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${Math.max(containerWidth, totalWidth)} ${totalHeight}`)
    .style('overflow', 'visible')

  // Title
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text(`Cohort ${currentMetric.value?.label || 'Retention'} Heatmap`)

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(`By ${DIMENSIONS.find(d => d.value === data.dimension)?.label || data.dimension}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const colorScale = d3.scaleSequential()
    .domain([scale.min, scale.max])
    .interpolator(d3.interpolateRgb(scale.low_color, scale.high_color))

  // Column headers
  g.selectAll('.col-label')
    .data(cols)
    .join('text')
    .attr('x', (d, i) => i * (cellSize + cellGap) + cellSize / 2)
    .attr('y', -8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text(d => d.replace('Month ', 'M'))

  // Row labels
  g.selectAll('.row-label')
    .data(rows)
    .join('text')
    .attr('x', -8)
    .attr('y', (d, i) => i * rowHeight + cellSize / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text(d => d.length > 14 ? d.slice(0, 13) + '…' : d)

  // Cells
  rows.forEach((row, ri) => {
    const rowGroup = g.append('g')
      .attr('transform', `translate(0,${ri * rowHeight})`)

    rowGroup.selectAll('.cell')
      .data(values[ri])
      .join('rect')
      .attr('x', (d, ci) => ci * (cellSize + cellGap))
      .attr('y', 0)
      .attr('width', cellSize)
      .attr('height', cellSize)
      .attr('rx', 3)
      .attr('fill', d => colorScale(d))
      .attr('opacity', 0)
      .transition()
      .duration(400)
      .delay((d, ci) => ri * 30 + ci * 15)
      .ease(d3.easeCubicOut)
      .attr('opacity', 1)

    // Cell text
    rowGroup.selectAll('.cell-text')
      .data(values[ri])
      .join('text')
      .attr('x', (d, ci) => ci * (cellSize + cellGap) + cellSize / 2)
      .attr('y', cellSize / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('font-size', cellSize < 36 ? '8px' : '9px')
      .attr('font-weight', '500')
      .attr('fill', d => {
        const luminance = d3.rgb(colorScale(d)).r * 0.299 +
          d3.rgb(colorScale(d)).g * 0.587 + d3.rgb(colorScale(d)).b * 0.114
        return luminance > 150 ? '#333' : '#fff'
      })
      .style('opacity', 0)
      .text(d => currentMetric.value?.unit === '$' ? Math.round(d) : d.toFixed(0))
      .transition()
      .duration(300)
      .delay((d, ci) => 200 + ri * 30 + ci * 15)
      .style('opacity', 1)
  })

  // Color legend
  const legendWidth = 160
  const legendHeight = 10
  const legendX = width - legendWidth
  const legendY = height + 20

  const legendScale = d3.scaleLinear()
    .domain([0, legendWidth])
    .range([scale.min, scale.max])

  const legendG = g.append('g')
    .attr('transform', `translate(${legendX},${legendY})`)

  for (let px = 0; px < legendWidth; px++) {
    legendG.append('rect')
      .attr('x', px)
      .attr('y', 0)
      .attr('width', 1)
      .attr('height', legendHeight)
      .attr('fill', colorScale(legendScale(px)))
  }

  legendG.append('text')
    .attr('x', 0)
    .attr('y', legendHeight + 12)
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text(formatValue(scale.min))

  legendG.append('text')
    .attr('x', legendWidth)
    .attr('y', legendHeight + 12)
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text(formatValue(scale.max))
}

// --- Line Chart ---

function renderLineChart() {
  const container = lineChartRef.value
  if (!container || !cohortData.value) return

  d3.select(container).selectAll('*').remove()

  const data = cohortData.value
  const curves = compareMode.value && comparisonData.value
    ? [comparisonData.value.cohort_a, comparisonData.value.cohort_b]
    : data.curves

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 40, left: 52 }
  const width = containerWidth - margin.left - margin.right
  const height = 280
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  // Title
  const title = compareMode.value && comparisonData.value
    ? `${comparisonData.value.cohort_a.cohort} vs ${comparisonData.value.cohort_b.cohort}`
    : `Cohort ${currentMetric.value?.label || 'Retention'} Curves`

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text(title)

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(compareMode.value ? 'Head-to-head comparison' : 'All cohorts overlaid')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const allValues = curves.flatMap(c => c.points.map(p => p.value))
  const yMin = Math.floor(Math.min(...allValues) / 10) * 10
  const yMax = Math.ceil(Math.max(...allValues) / 10) * 10

  const x = d3.scaleLinear()
    .domain([0, curves[0].points.length - 1])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([yMin, yMax])
    .range([height, 0])

  // Grid
  const yTicks = d3.range(yMin, yMax + 1, Math.max(1, Math.round((yMax - yMin) / 5)))
  g.selectAll('.grid-line')
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
    .text(d => formatValue(d))

  // X-axis labels
  const xTicks = curves[0].points.filter((_, i) => i % 2 === 0 || i === curves[0].points.length - 1)
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d.period))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => d.label.replace('Month ', 'M'))

  const line = d3.line()
    .x(d => x(d.period))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX)

  // Generate colors for curves
  const lineColors = compareMode.value
    ? [COLORS.primary, COLORS.orange]
    : d3.scaleOrdinal()
        .domain(curves.map(c => c.cohort))
        .range([
          COLORS.primary, COLORS.orange, COLORS.purple, COLORS.green,
          '#888', '#2196F3', '#E91E63', '#009688', '#795548', '#607D8B',
          '#FF9800', '#3F51B5',
        ])

  curves.forEach((curve, idx) => {
    const color = compareMode.value ? lineColors[idx] : lineColors(curve.cohort)
    const opacity = compareMode.value ? 1 : 0.6

    const path = g.append('path')
      .datum(curve.points)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', compareMode.value ? 2.5 : 1.5)
      .attr('stroke-opacity', opacity)
      .attr('d', line)

    // Animate path drawing
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .delay(idx * 100)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Endpoint dot
    const last = curve.points[curve.points.length - 1]
    g.append('circle')
      .attr('cx', x(last.period))
      .attr('cy', y(last.value))
      .attr('r', 3)
      .attr('fill', color)
      .attr('opacity', 0)
      .transition()
      .duration(300)
      .delay(800 + idx * 100)
      .attr('opacity', 1)

    // Endpoint label (only in compare mode or few cohorts)
    if (compareMode.value || curves.length <= 6) {
      g.append('text')
        .attr('x', x(last.period) + 6)
        .attr('y', y(last.value))
        .attr('dy', '0.35em')
        .attr('font-size', '10px')
        .attr('fill', color)
        .attr('font-weight', '500')
        .style('opacity', 0)
        .text(curve.cohort.length > 12 ? curve.cohort.slice(0, 11) + '…' : curve.cohort)
        .transition()
        .duration(300)
        .delay(800 + idx * 100)
        .style('opacity', 1)
    }
  })

  // Legend (for compare mode)
  if (compareMode.value && comparisonData.value) {
    const legend = svg.append('g')
      .attr('transform', `translate(${containerWidth - margin.right - 200}, 14)`)

    ;[comparisonData.value.cohort_a, comparisonData.value.cohort_b].forEach((c, i) => {
      const lx = i * 100
      legend.append('rect')
        .attr('x', lx).attr('y', 0)
        .attr('width', 10).attr('height', 10)
        .attr('rx', 2)
        .attr('fill', lineColors[i])

      legend.append('text')
        .attr('x', lx + 14).attr('y', 9)
        .attr('font-size', '11px')
        .attr('fill', '#555')
        .text(c.cohort.length > 10 ? c.cohort.slice(0, 9) + '…' : c.cohort)
    })
  }
}

function renderCharts() {
  nextTick(() => {
    if (viewMode.value === 'heatmap' || viewMode.value === 'both') renderHeatmap()
    if (viewMode.value === 'lines' || viewMode.value === 'both') renderLineChart()
  })
}

// --- Watchers ---

watch([dimension, metric], () => {
  selectedCohortA.value = 0
  selectedCohortB.value = 1
  fetchData()
})

watch([viewMode, compareMode], () => renderCharts())

watch([selectedCohortA, selectedCohortB], async () => {
  if (compareMode.value) {
    await fetchComparison()
    renderCharts()
  }
})

watch(cohortData, () => renderCharts())

// --- Lifecycle ---

onMounted(() => {
  fetchData()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderCharts(), 200)
  })
  if (heatmapRef.value) resizeObserver.observe(heatmapRef.value)
  if (lineChartRef.value) resizeObserver.observe(lineChartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="space-y-4">
    <!-- Controls -->
    <div class="bg-white border border-black/10 rounded-lg p-4">
      <div class="flex flex-wrap items-center gap-4">
        <!-- Dimension -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Cohort By</label>
          <select
            v-model="dimension"
            class="text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white text-[#1a1a1a] focus:outline-none focus:ring-2 focus:ring-[#2068FF]/20 focus:border-[#2068FF]"
          >
            <option v-for="d in DIMENSIONS" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </div>

        <!-- Metric -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Metric</label>
          <select
            v-model="metric"
            class="text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white text-[#1a1a1a] focus:outline-none focus:ring-2 focus:ring-[#2068FF]/20 focus:border-[#2068FF]"
          >
            <option v-for="m in METRICS" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>

        <!-- View Mode -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">View</label>
          <div class="flex border border-gray-200 rounded-md overflow-hidden">
            <button
              v-for="v in [{ value: 'heatmap', label: 'Heatmap' }, { value: 'lines', label: 'Curves' }, { value: 'both', label: 'Both' }]"
              :key="v.value"
              @click="viewMode = v.value"
              class="text-sm px-3 py-1.5 transition-colors"
              :class="viewMode === v.value
                ? 'bg-[#2068FF] text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'"
            >{{ v.label }}</button>
          </div>
        </div>

        <!-- Compare Toggle -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Compare</label>
          <button
            @click="compareMode = !compareMode"
            class="text-sm px-3 py-1.5 border rounded-md transition-colors"
            :class="compareMode
              ? 'bg-[#2068FF] text-white border-[#2068FF]'
              : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
          >{{ compareMode ? 'On' : 'Off' }}</button>
        </div>

        <!-- Cohort selectors (compare mode) -->
        <template v-if="compareMode && cohortData">
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-[#2068FF] uppercase tracking-wide">Cohort A</label>
            <select
              v-model.number="selectedCohortA"
              class="text-sm border border-[#2068FF]/30 rounded-md px-3 py-1.5 bg-white text-[#1a1a1a] focus:outline-none focus:ring-2 focus:ring-[#2068FF]/20"
            >
              <option v-for="(c, i) in cohortData.cohorts" :key="i" :value="i">{{ c }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-[#ff5600] uppercase tracking-wide">Cohort B</label>
            <select
              v-model.number="selectedCohortB"
              class="text-sm border border-[#ff5600]/30 rounded-md px-3 py-1.5 bg-white text-[#1a1a1a] focus:outline-none focus:ring-2 focus:ring-[#ff5600]/20"
            >
              <option v-for="(c, i) in cohortData.cohorts" :key="i" :value="i">{{ c }}</option>
            </select>
          </div>
        </template>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bg-white border border-black/10 rounded-lg p-8 flex items-center justify-center">
      <div class="flex items-center gap-3 text-gray-400">
        <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span class="text-sm">Loading cohort data…</span>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
      {{ error }}
    </div>

    <template v-else-if="cohortData">
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="bg-white border border-black/10 rounded-lg p-3">
          <div class="text-xs text-gray-500 mb-1">Best Cohort</div>
          <div class="text-sm font-semibold text-[#009900]">{{ cohortData.summary.best_cohort.label }}</div>
          <div class="text-xs text-gray-400 mt-0.5">avg {{ formatValue(cohortData.summary.best_cohort.average) }}</div>
        </div>
        <div class="bg-white border border-black/10 rounded-lg p-3">
          <div class="text-xs text-gray-500 mb-1">Worst Cohort</div>
          <div class="text-sm font-semibold text-[#ef4444]">{{ cohortData.summary.worst_cohort.label }}</div>
          <div class="text-xs text-gray-400 mt-0.5">avg {{ formatValue(cohortData.summary.worst_cohort.average) }}</div>
        </div>
        <div class="bg-white border border-black/10 rounded-lg p-3">
          <div class="text-xs text-gray-500 mb-1">Spread</div>
          <div class="text-sm font-semibold text-[#1a1a1a]">{{ formatValue(cohortData.summary.difference) }}</div>
          <div class="text-xs mt-0.5" :class="cohortData.summary.statistically_significant ? 'text-[#2068FF]' : 'text-gray-400'">
            {{ cohortData.summary.statistically_significant ? 'Significant' : 'Not significant' }}
          </div>
        </div>
        <div class="bg-white border border-black/10 rounded-lg p-3">
          <div class="text-xs text-gray-500 mb-1">Overall Avg</div>
          <div class="text-sm font-semibold text-[#1a1a1a]">{{ formatValue(cohortData.summary.overall_average) }}</div>
          <div class="text-xs text-gray-400 mt-0.5">across all cohorts</div>
        </div>
      </div>

      <!-- Heatmap -->
      <div
        v-if="viewMode === 'heatmap' || viewMode === 'both'"
        class="bg-white border border-black/10 rounded-lg p-4 md:p-6 overflow-x-auto"
      >
        <div ref="heatmapRef" class="w-full min-w-[600px]" />
      </div>

      <!-- Line Chart -->
      <div
        v-if="viewMode === 'lines' || viewMode === 'both'"
        class="bg-white border border-black/10 rounded-lg p-4 md:p-6"
      >
        <div ref="lineChartRef" class="w-full" />
      </div>

      <!-- Comparison Delta Table -->
      <div
        v-if="compareMode && comparisonData"
        class="bg-white border border-black/10 rounded-lg p-4"
      >
        <h3 class="text-sm font-semibold text-[#050505] mb-3">
          Period-by-Period Comparison
          <span class="ml-2 text-xs font-normal text-gray-400">
            Winner: <span class="font-medium text-[#2068FF]">{{ comparisonData.winner }}</span>
          </span>
        </h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left py-2 pr-4 text-xs text-gray-500 font-medium">Period</th>
                <th class="text-right py-2 px-3 text-xs font-medium text-[#2068FF]">{{ comparisonData.cohort_a.cohort }}</th>
                <th class="text-right py-2 px-3 text-xs font-medium text-[#ff5600]">{{ comparisonData.cohort_b.cohort }}</th>
                <th class="text-right py-2 pl-3 text-xs text-gray-500 font-medium">Delta</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in comparisonData.deltas" :key="d.period" class="border-b border-gray-50">
                <td class="py-1.5 pr-4 text-gray-500">{{ d.label }}</td>
                <td class="py-1.5 px-3 text-right font-medium">{{ formatValue(d.value_a) }}</td>
                <td class="py-1.5 px-3 text-right font-medium">{{ formatValue(d.value_b) }}</td>
                <td
                  class="py-1.5 pl-3 text-right font-medium"
                  :class="d.delta > 0 ? 'text-[#009900]' : d.delta < 0 ? 'text-[#ef4444]' : 'text-gray-400'"
                >
                  {{ d.delta > 0 ? '+' : '' }}{{ formatValue(d.delta) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
