<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { trendsApi } from '../../api/trends'

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const runs = ref([])
const availableMetrics = ref([])
const metricLabels = ref({})
const selectedMetric = ref('engagement_rate')
const loading = ref(false)
const error = ref(null)

const CATEGORY_COLORS = {
  outbound: '#2068FF',
  personalization: '#ff5600',
  pricing: '#AA00FF',
  signals: '#009900',
}

const CATEGORY_FALLBACK = '#666666'

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await trendsApi.getScenarioTrends()
    const d = res.data?.data || res.data
    runs.value = d.runs || []
    availableMetrics.value = d.available_metrics || []
    metricLabels.value = d.metric_labels || {}
    if (availableMetrics.value.length && !availableMetrics.value.includes(selectedMetric.value)) {
      selectedMetric.value = availableMetrics.value[0]
    }
  } catch (e) {
    error.value = e.message || 'Failed to load trend data'
  } finally {
    loading.value = false
  }
}

const chartData = computed(() => {
  if (!runs.value.length) return []
  const metric = selectedMetric.value
  return runs.value
    .map(r => ({
      x: r.day_offset,
      y: r.metrics?.[metric] ?? 0,
      category: r.category,
      scenarioName: r.scenario_name,
      runIndex: r.run_index,
    }))
    .sort((a, b) => a.x - b.x)
})

const categories = computed(() => {
  const cats = new Set(runs.value.map(r => r.category))
  return Array.from(cats).sort()
})

// --- Linear regression with confidence band ---

function linearRegression(data) {
  const n = data.length
  if (n < 2) return null

  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0
  for (const d of data) {
    sumX += d.x
    sumY += d.y
    sumXY += d.x * d.y
    sumX2 += d.x * d.x
  }

  const denom = n * sumX2 - sumX * sumX
  if (Math.abs(denom) < 1e-10) return null

  const slope = (n * sumXY - sumX * sumY) / denom
  const intercept = (sumY - slope * sumX) / n

  // Standard error for confidence band
  const meanX = sumX / n
  let ssRes = 0
  for (const d of data) {
    const predicted = slope * d.x + intercept
    ssRes += (d.y - predicted) ** 2
  }
  const se = Math.sqrt(ssRes / (n - 2))
  const ssX = sumX2 - (sumX * sumX) / n

  return { slope, intercept, se, ssX, meanX, n }
}

function confidenceBand(reg, xVal, tValue = 1.96) {
  if (!reg) return 0
  const deviation = xVal - reg.meanX
  const margin = tValue * reg.se * Math.sqrt(1 / reg.n + (deviation * deviation) / reg.ssX)
  return margin
}

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  const data = chartData.value
  if (!container || !data.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 24, bottom: 40, left: 52 }
  const width = containerWidth - margin.left - margin.right
  const height = 260
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const xExtent = d3.extent(data, d => d.x)
  const yExtent = d3.extent(data, d => d.y)
  const yPad = (yExtent[1] - yExtent[0]) * 0.15 || 1

  const x = d3.scaleLinear()
    .domain([xExtent[0] - 0.5, xExtent[1] + 0.5])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([yExtent[0] - yPad, yExtent[1] + yPad])
    .range([height, 0])
    .nice()

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid-line')
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
    .attr('fill', '#888')
    .text(d => {
      if (Math.abs(d) >= 100) return d3.format('.0f')(d)
      if (Math.abs(d) >= 1) return d3.format('.1f')(d)
      return d3.format('.2f')(d)
    })

  // X-axis labels
  const xTicks = x.ticks(Math.min(10, xExtent[1] - xExtent[0] + 1))
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 24)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `Day ${d}`)

  // X-axis title
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height + 38)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#666')
    .text('Simulation Sequence')

  // Y-axis title
  const yLabel = metricLabels.value[selectedMetric.value] || selectedMetric.value
  g.append('text')
    .attr('transform', `rotate(-90)`)
    .attr('x', -height / 2)
    .attr('y', -40)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#666')
    .text(yLabel)

  // --- Confidence band + trend line ---
  const reg = linearRegression(data)

  if (reg) {
    const bandPoints = []
    const steps = 60
    const xMin = xExtent[0]
    const xMax = xExtent[1]

    for (let i = 0; i <= steps; i++) {
      const xVal = xMin + (xMax - xMin) * (i / steps)
      const yVal = reg.slope * xVal + reg.intercept
      const band = confidenceBand(reg, xVal)
      bandPoints.push({ x: xVal, yUpper: yVal + band, yLower: yVal - band })
    }

    // Confidence band area
    const area = d3.area()
      .x(d => x(d.x))
      .y0(d => y(d.yLower))
      .y1(d => y(d.yUpper))
      .curve(d3.curveLinear)

    g.append('path')
      .datum(bandPoints)
      .attr('d', area)
      .attr('fill', 'rgba(32, 104, 255, 0.08)')

    // Trend line
    g.append('line')
      .attr('x1', x(xMin))
      .attr('y1', y(reg.slope * xMin + reg.intercept))
      .attr('x2', x(xMax))
      .attr('y2', y(reg.slope * xMax + reg.intercept))
      .attr('stroke', '#2068FF')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,3')
      .attr('opacity', 0.7)
  }

  // --- Scatter dots ---
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('background', 'rgba(5,5,5,0.9)')
    .style('color', '#fff')
    .style('padding', '6px 10px')
    .style('border-radius', '6px')
    .style('font-size', '11px')
    .style('line-height', '1.4')
    .style('opacity', 0)
    .style('transition', 'opacity 0.15s')

  g.selectAll('.dot')
    .data(data)
    .join('circle')
    .attr('cx', d => x(d.x))
    .attr('cy', d => y(d.y))
    .attr('r', 0)
    .attr('fill', d => CATEGORY_COLORS[d.category] || CATEGORY_FALLBACK)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.85)
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      d3.select(event.target).attr('r', 7).attr('opacity', 1)
      const formatVal = Math.abs(d.y) >= 1 ? d3.format('.1f') : d3.format('.3f')
      tooltip
        .html(`<strong>${d.scenarioName}</strong><br/>${yLabel}: ${formatVal(d.y)}<br/>Day ${d.x}`)
        .style('opacity', 1)
        .style('left', `${x(d.x) + margin.left + 12}px`)
        .style('top', `${y(d.y) + margin.top - 10}px`)
    })
    .on('mouseleave', (event) => {
      d3.select(event.target).attr('r', 5).attr('opacity', 0.85)
      tooltip.style('opacity', 0)
    })
    .transition()
    .duration(600)
    .delay((_, i) => i * 15)
    .attr('r', 5)
}

// --- Lifecycle ---

watch([chartData, selectedMetric], () => {
  nextTick(() => renderChart())
})

onMounted(async () => {
  await fetchData()
  nextTick(() => renderChart())
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderChart, 200)
    })
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Cross-Scenario Trends</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Are simulation outcomes improving over time?
        </p>
      </div>
      <select
        v-if="availableMetrics.length"
        v-model="selectedMetric"
        class="text-xs border border-[var(--color-border)] rounded-md px-2 py-1.5 bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[#2068FF]"
      >
        <option v-for="m in availableMetrics" :key="m" :value="m">
          {{ metricLabels[m] || m }}
        </option>
      </select>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center h-[300px] text-[var(--color-text-muted)] text-sm">
      <span>Loading trend data...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="flex items-center justify-center h-[300px] text-[var(--color-error)] text-sm">
      <span>{{ error }}</span>
    </div>

    <!-- Chart -->
    <div v-else-if="chartData.length" class="relative" ref="chartRef" style="height: 300px" />

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[300px] text-[var(--color-text-muted)] text-sm">
      <span>No simulation runs to display</span>
    </div>

    <!-- Legend -->
    <div v-if="categories.length && !loading && !error" class="flex flex-wrap items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
      <span v-for="cat in categories" :key="cat" class="flex items-center gap-1.5">
        <span
          class="inline-block w-2.5 h-2.5 rounded-full"
          :style="{ backgroundColor: CATEGORY_COLORS[cat] || CATEGORY_FALLBACK }"
        />
        {{ cat.charAt(0).toUpperCase() + cat.slice(1) }}
      </span>
      <span class="flex items-center gap-1.5 ml-2">
        <span class="inline-block w-4 border-t-2 border-dashed border-[#2068FF]" />
        Trend
      </span>
    </div>
  </div>
</template>
