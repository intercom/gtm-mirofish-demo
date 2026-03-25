<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useComparisonData } from '../../composables/useComparisonData'

const {
  availableRuns,
  selectedRunIds,
  comparisonData,
  loading,
  error,
  hasSelection,
  fetchRuns,
  fetchComparison,
  toggleRun,
} = useComparisonData()

const chartRef = ref(null)
const activeMetric = ref('actions')
let resizeObserver = null
let resizeTimer = null

const METRIC_LABELS = {
  actions: 'Actions per Round',
  sentiment: 'Avg Sentiment',
  engagement: 'Engagement Rate (%)',
}

const RUN_COLORS = ['#2068FF', '#ff5600', '#009900', '#AA00FF', '#888']
const RUN_DASHES = ['', '6,3', '2,3', '8,4,2,4', '4,4']

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function getTimelineKey(metric) {
  return `${metric}_timeline`
}

function getValueKey(metric) {
  if (metric === 'actions') return 'actions'
  if (metric === 'sentiment') return 'sentiment'
  return 'engagement_rate'
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !comparisonData.value) return

  const runs = comparisonData.value.runs
  if (!runs || runs.length === 0) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const metric = activeMetric.value
  const timelineKey = getTimelineKey(metric)
  const valueKey = getValueKey(metric)

  const margin = { top: 20, right: 20, bottom: 36, left: 48 }
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

  // Compute domains across all runs
  let allValues = []
  let maxRound = 0
  for (const run of runs) {
    const timeline = run[timelineKey]
    if (!timeline) continue
    for (const pt of timeline) {
      allValues.push(pt[valueKey])
      if (pt.round > maxRound) maxRound = pt.round
    }
  }

  if (allValues.length === 0) return

  const yMin = metric === 'sentiment' ? Math.min(-0.3, d3.min(allValues) - 0.05) : 0
  const yMax = d3.max(allValues) * 1.15

  const x = d3.scaleLinear().domain([1, maxRound]).range([0, width])
  const y = d3.scaleLinear().domain([yMin, yMax]).range([height, 0]).nice()

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', d => (metric === 'sentiment' && d === 0) ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', d => (metric === 'sentiment' && d === 0) ? 'none' : '2,3')

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
      if (metric === 'sentiment') return d >= 0 ? `+${d.toFixed(1)}` : d.toFixed(1)
      if (metric === 'engagement') return `${d.toFixed(0)}%`
      return d.toFixed(0)
    })

  // X-axis labels
  const step = Math.max(1, Math.floor(maxRound / 8))
  const xLabels = d3.range(1, maxRound + 1).filter((_, i) => i % step === 0 || i === maxRound - 1)
  g.selectAll('.x-label')
    .data(xLabels)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 22)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d}`)

  // Draw lines for each run
  runs.forEach((run, i) => {
    const timeline = run[timelineKey]
    if (!timeline) return

    const color = RUN_COLORS[i % RUN_COLORS.length]
    const dash = RUN_DASHES[i % RUN_DASHES.length]

    const line = d3.line()
      .x(d => x(d.round))
      .y(d => y(d[valueKey]))
      .curve(d3.curveMonotoneX)

    const path = g.append('path')
      .datum(timeline)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2.5)
      .attr('stroke-dasharray', dash || 'none')
      .attr('opacity', 0.85)

    // Animate line drawing
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', dash ? `${dash}` : `${totalLength} ${totalLength}`)

    if (!dash) {
      path
        .attr('stroke-dashoffset', totalLength)
        .transition()
        .duration(800)
        .delay(i * 150)
        .ease(d3.easeCubicOut)
        .attr('stroke-dashoffset', 0)
    } else {
      path
        .style('opacity', 0)
        .transition()
        .duration(600)
        .delay(i * 150)
        .style('opacity', 0.85)
    }

    // Data points
    g.selectAll(`.dot-${i}`)
      .data(timeline.filter((_, j) => j % Math.max(1, Math.floor(timeline.length / 10)) === 0 || j === timeline.length - 1))
      .join('circle')
      .attr('cx', d => x(d.round))
      .attr('cy', d => y(d[valueKey]))
      .attr('r', 0)
      .attr('fill', color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .transition()
      .duration(300)
      .delay((_, j) => 800 + i * 150 + j * 30)
      .attr('r', 3.5)
  })

  // Tooltip
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('max-width', '200px')

  // Vertical hover line + tooltip
  const hoverLine = g.append('line')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-dasharray', '3,3')
    .style('opacity', 0)

  g.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'crosshair')
    .on('mousemove', (event) => {
      const [mx] = d3.pointer(event)
      const roundNum = Math.round(x.invert(mx))
      const clampedRound = Math.max(1, Math.min(maxRound, roundNum))

      hoverLine
        .attr('x1', x(clampedRound))
        .attr('x2', x(clampedRound))
        .style('opacity', 1)

      let html = `<div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${clampedRound}</div>`
      runs.forEach((run, i) => {
        const timeline = run[timelineKey]
        if (!timeline) return
        const pt = timeline.find(p => p.round === clampedRound)
        if (!pt) return
        const color = RUN_COLORS[i % RUN_COLORS.length]
        let val = pt[valueKey]
        if (metric === 'sentiment') val = (val >= 0 ? '+' : '') + val.toFixed(2)
        else if (metric === 'engagement') val = val.toFixed(1) + '%'
        else val = val.toString()
        html += `<div style="display:flex;align-items:center;gap:6px;margin-top:2px">
          <span style="width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0"></span>
          <span style="color:var(--color-text-secondary,#555)">${run.name}:</span>
          <span style="font-weight:600;color:${color}">${val}</span>
        </div>`
      })

      tooltip.html(html).style('opacity', 1)

      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 16}px`)
        .style('top', `${event.clientY - rect.top - 20}px`)
    })
    .on('mouseleave', () => {
      hoverLine.style('opacity', 0)
      tooltip.style('opacity', 0)
    })
}

async function loadAndRender() {
  await fetchComparison()
  nextTick(renderChart)
}

watch(activeMetric, loadAndRender)
watch(selectedRunIds, loadAndRender, { deep: true })

onMounted(async () => {
  await fetchRuns()
  await loadAndRender()

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
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Scenario Comparison</h3>

      <!-- Metric toggle -->
      <div class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          v-for="key in ['actions', 'sentiment', 'engagement']"
          :key="key"
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors capitalize"
          :class="activeMetric === key
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="activeMetric = key"
        >
          {{ key }}
        </button>
      </div>
    </div>

    <!-- Run selector pills -->
    <div v-if="availableRuns.length" class="flex flex-wrap gap-2 mb-4">
      <button
        v-for="(run, i) in availableRuns"
        :key="run.id"
        @click="toggleRun(run.id)"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors border"
        :class="selectedRunIds.includes(run.id)
          ? 'border-transparent text-white'
          : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-text-muted)]'"
        :style="selectedRunIds.includes(run.id) ? { background: RUN_COLORS[i % RUN_COLORS.length] } : {}"
      >
        <span
          v-if="!selectedRunIds.includes(run.id)"
          class="w-2 h-2 rounded-full"
          :style="{ background: RUN_COLORS[i % RUN_COLORS.length] }"
        />
        {{ run.name }}
      </button>
    </div>

    <!-- Subtitle -->
    <p class="text-xs text-[var(--color-text-muted)] mb-3">
      {{ METRIC_LABELS[activeMetric] }} — overlay across {{ selectedRunIds.length }} runs
    </p>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[260px] text-[var(--color-text-muted)] text-sm">
      <svg class="w-4 h-4 animate-spin mr-2 text-[#2068FF]" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading comparison data...
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-[260px] text-red-500 text-sm">
      {{ error }}
    </div>

    <!-- Not enough selected -->
    <div v-else-if="!hasSelection" class="flex items-center justify-center h-[260px] text-[var(--color-text-muted)] text-sm">
      Select at least 2 runs to compare
    </div>

    <!-- Chart container -->
    <div v-else ref="chartRef" class="relative w-full" style="height: 296px" />

    <!-- Legend -->
    <div v-if="comparisonData?.runs?.length && !loading" class="flex flex-wrap items-center gap-4 mt-3 pt-3 border-t border-[var(--color-border)]">
      <div
        v-for="(run, i) in comparisonData.runs"
        :key="run.run_id"
        class="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]"
      >
        <svg width="24" height="10">
          <line
            x1="0" y1="5" x2="24" y2="5"
            :stroke="RUN_COLORS[i % RUN_COLORS.length]"
            stroke-width="2.5"
            :stroke-dasharray="RUN_DASHES[i % RUN_DASHES.length] || 'none'"
          />
          <circle
            cx="12" cy="5" r="3"
            :fill="RUN_COLORS[i % RUN_COLORS.length]"
            stroke="#fff"
            stroke-width="1"
          />
        </svg>
        <span>{{ run.name }}</span>
        <span class="text-[var(--color-text-muted)]">
          ({{ run.summary.total_actions }} actions, avg {{ run.summary.avg_engagement }}% eng.)
        </span>
      </div>
    </div>
  </div>
</template>
