<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { reconciliationApi } from '@/api/reconciliation'

const props = defineProps({
  runs: { type: Array, default: null },
  target: { type: Object, default: () => ({ matchRate: 95.0 }) },
})

const chartRef = ref(null)
const loading = ref(false)
const error = ref(null)
const chartData = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  matchRate: '#2068FF',
  discrepancyValue: '#ff5600',
  discrepancyCount: '#888888',
  target: '#009900',
  targetFill: 'rgba(0, 153, 0, 0.08)',
  annotation: '#AA00FF',
  grid: 'rgba(0, 0, 0, 0.06)',
  gridZero: 'rgba(0, 0, 0, 0.15)',
  text: '#050505',
  muted: '#888',
  axisLabel: '#aaa',
}

async function fetchData() {
  if (props.runs) {
    chartData.value = props.runs
    return
  }
  loading.value = true
  error.value = null
  try {
    const res = await reconciliationApi.getTrend()
    chartData.value = res.data.runs
  } catch (e) {
    error.value = e.message || 'Failed to load trend data'
  } finally {
    loading.value = false
  }
}

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  const data = chartData.value
  if (!container || !data?.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 64, bottom: 44, left: 52 }
  const width = containerWidth - margin.left - margin.right
  const height = 240
  const totalHeight = height + margin.top + margin.bottom

  const parseDate = d3.timeParse('%Y-%m-%d')
  const parsed = data.map(d => ({ ...d, _date: parseDate(d.date) }))

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // --- Scales ---
  const x = d3.scaleTime()
    .domain(d3.extent(parsed, d => d._date))
    .range([0, width])

  const yLeft = d3.scaleLinear()
    .domain([
      Math.max(80, d3.min(parsed, d => d.matchRate) - 3),
      100,
    ])
    .range([height, 0])
    .nice()

  const yRight = d3.scaleLinear()
    .domain([0, d3.max(parsed, d => d.discrepancyValue) * 1.1])
    .range([height, 0])
    .nice()

  const yCount = d3.scaleLinear()
    .domain([0, d3.max(parsed, d => d.discrepancyCount) * 1.2])
    .range([height, 0])

  // --- Grid lines ---
  const yLeftTicks = yLeft.ticks(5)
  g.selectAll('.grid-line')
    .data(yLeftTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => yLeft(d))
    .attr('y2', d => yLeft(d))
    .attr('stroke', COLORS.grid)
    .attr('stroke-dasharray', '2,3')

  // --- 95% target line ---
  const targetY = yLeft(props.target.matchRate)
  g.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', targetY)
    .attr('y2', targetY)
    .attr('stroke', COLORS.target)
    .attr('stroke-dasharray', '6,4')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.7)

  g.append('text')
    .attr('x', width + 4)
    .attr('y', targetY)
    .attr('dy', '0.35em')
    .attr('font-size', '9px')
    .attr('fill', COLORS.target)
    .text(`${props.target.matchRate}%`)

  // --- Green fill above target ---
  const aboveTargetArea = d3.area()
    .x(d => x(d._date))
    .y0(targetY)
    .y1(d => d.matchRate >= props.target.matchRate ? yLeft(d.matchRate) : targetY)
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(parsed)
    .attr('d', aboveTargetArea)
    .attr('fill', COLORS.targetFill)

  // --- Discrepancy count bars (background) ---
  const barWidth = Math.max(4, Math.min(16, width / parsed.length * 0.5))
  g.selectAll('.count-bar')
    .data(parsed)
    .join('rect')
    .attr('x', d => x(d._date) - barWidth / 2)
    .attr('y', height)
    .attr('width', barWidth)
    .attr('height', 0)
    .attr('rx', 2)
    .attr('fill', COLORS.discrepancyCount)
    .attr('opacity', 0.12)
    .transition()
    .duration(600)
    .delay((_, i) => i * 25)
    .ease(d3.easeCubicOut)
    .attr('y', d => yCount(d.discrepancyCount))
    .attr('height', d => height - yCount(d.discrepancyCount))

  // --- Discrepancy value line (right axis) ---
  const valueLine = d3.line()
    .x(d => x(d._date))
    .y(d => yRight(d.discrepancyValue))
    .curve(d3.curveMonotoneX)

  const valueLinePath = g.append('path')
    .datum(parsed)
    .attr('d', valueLine)
    .attr('fill', 'none')
    .attr('stroke', COLORS.discrepancyValue)
    .attr('stroke-width', 2)
    .attr('opacity', 0.8)

  animateLine(valueLinePath, 700)

  // --- Match rate line (left axis) ---
  const matchLine = d3.line()
    .x(d => x(d._date))
    .y(d => yLeft(d.matchRate))
    .curve(d3.curveMonotoneX)

  const matchLinePath = g.append('path')
    .datum(parsed)
    .attr('d', matchLine)
    .attr('fill', 'none')
    .attr('stroke', COLORS.matchRate)
    .attr('stroke-width', 2.5)

  animateLine(matchLinePath, 800)

  // --- Match rate dots ---
  const dots = g.selectAll('.match-dot')
    .data(parsed)
    .join('circle')
    .attr('cx', d => x(d._date))
    .attr('cy', d => yLeft(d.matchRate))
    .attr('r', 0)
    .attr('fill', d => d.matchRate >= props.target.matchRate ? COLORS.target : COLORS.matchRate)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)

  dots.transition()
    .duration(300)
    .delay((_, i) => 800 + i * 25)
    .attr('r', 3.5)

  // --- Annotation markers ---
  const annotations = parsed.filter(d => d.annotation)
  annotations.forEach(d => {
    const ax = x(d._date)

    g.append('line')
      .attr('x1', ax)
      .attr('x2', ax)
      .attr('y1', 0)
      .attr('y2', height)
      .attr('stroke', COLORS.annotation)
      .attr('stroke-dasharray', '3,3')
      .attr('opacity', 0.4)

    g.append('circle')
      .attr('cx', ax)
      .attr('cy', -6)
      .attr('r', 4)
      .attr('fill', COLORS.annotation)
      .attr('opacity', 0.7)

    g.append('text')
      .attr('x', ax)
      .attr('y', -14)
      .attr('text-anchor', 'middle')
      .attr('font-size', '8px')
      .attr('fill', COLORS.annotation)
      .attr('opacity', 0.8)
      .text(d.annotation)
  })

  // --- Left Y-axis labels (%) ---
  g.selectAll('.y-left-label')
    .data(yLeftTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => yLeft(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', COLORS.axisLabel)
    .text(d => `${d}%`)

  // --- Right Y-axis labels ($) ---
  const yRightTicks = yRight.ticks(5)
  g.selectAll('.y-right-label')
    .data(yRightTicks)
    .join('text')
    .attr('x', width + 8)
    .attr('y', d => yRight(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'start')
    .attr('font-size', '10px')
    .attr('fill', COLORS.axisLabel)
    .text(d => `$${d >= 1000 ? `${Math.round(d / 1000)}K` : d}`)

  // --- X-axis labels ---
  const formatDate = d3.timeFormat('%b %y')
  const xTicks = x.ticks(Math.min(parsed.length, 8))
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.axisLabel)
    .text(d => formatDate(d))

  // --- Axis titles ---
  g.append('text')
    .attr('x', -8)
    .attr('y', -8)
    .attr('font-size', '9px')
    .attr('fill', COLORS.matchRate)
    .attr('font-weight', '600')
    .text('Match %')

  g.append('text')
    .attr('x', width + 8)
    .attr('y', -8)
    .attr('font-size', '9px')
    .attr('fill', COLORS.discrepancyValue)
    .attr('font-weight', '600')
    .text('Discrepancy $')

  // --- Tooltip ---
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '10px 14px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('max-width', '220px')

  const formatTooltipDate = d3.timeFormat('%b %d, %Y')
  const hoverLine = g.append('line')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-dasharray', '2,2')
    .style('opacity', 0)

  // Invisible hover targets
  g.selectAll('.hover-target')
    .data(parsed)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(parsed[i - 1]._date) : x(d._date)
      return (prev + x(d._date)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(parsed[i - 1]._date) : x(d._date)
      const next = i < parsed.length - 1 ? x(parsed[i + 1]._date) : x(d._date)
      return ((x(d._date) - prev) + (next - x(d._date))) / 2 || barWidth
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const matchColor = d.matchRate >= props.target.matchRate ? COLORS.target : COLORS.matchRate
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:6px">
            ${formatTooltipDate(d._date)}
          </div>
          <div style="display:flex;justify-content:space-between;gap:12px;margin-bottom:3px">
            <span style="color:${COLORS.muted}">Match Rate</span>
            <span style="font-weight:600;color:${matchColor}">${d.matchRate}%</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:12px;margin-bottom:3px">
            <span style="color:${COLORS.muted}">Discrepancy</span>
            <span style="font-weight:600;color:${COLORS.discrepancyValue}">$${d.discrepancyValue.toLocaleString()}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:12px">
            <span style="color:${COLORS.muted}">Accounts</span>
            <span style="font-weight:600;color:${COLORS.discrepancyCount}">${d.discrepancyCount} issues</span>
          </div>
          ${d.annotation ? `<div style="margin-top:6px;padding-top:6px;border-top:1px solid rgba(0,0,0,0.08);color:${COLORS.annotation};font-size:11px">${d.annotation}</div>` : ''}
        `)
        .style('opacity', 1)

      hoverLine
        .attr('x1', x(d._date))
        .attr('x2', x(d._date))
        .style('opacity', 1)

      dots.filter(dd => dd._date === d._date)
        .transition().duration(100)
        .attr('r', 5.5)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 50}px`)
    })
    .on('mouseleave', (event, d) => {
      tooltip.style('opacity', 0)
      hoverLine.style('opacity', 0)
      dots.filter(dd => dd._date === d._date)
        .transition().duration(100)
        .attr('r', 3.5)
    })
}

function animateLine(path, duration) {
  const totalLength = path.node().getTotalLength()
  path
    .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(duration)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)
}

// --- Lifecycle ---

watch(() => props.runs, () => {
  if (props.runs) {
    chartData.value = props.runs
  }
}, { deep: true })

watch(chartData, () => {
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
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Reconciliation Trend</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">MRR match health over time</p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      <span>Loading trend data...</span>
    </div>

    <div v-else-if="error" class="flex items-center justify-center h-[280px] text-[var(--color-error)] text-sm">
      <span>{{ error }}</span>
    </div>

    <div v-else-if="chartData?.length" class="relative" ref="chartRef" style="height: 300px" />

    <div v-else class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      <span>No reconciliation data available</span>
    </div>

    <!-- Legend -->
    <div v-if="chartData?.length && !loading" class="flex flex-wrap items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 rounded" style="background: #2068FF" /> Match Rate
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 rounded" style="background: #ff5600" /> Discrepancy Value
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-sm" style="background: rgba(136,136,136,0.12)" /> Discrepancy Count
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0 border-t border-dashed" style="border-color: #009900" /> 95% Target
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full" style="background: #AA00FF; opacity: 0.7" /> Process Change
      </span>
    </div>
  </div>
</template>
