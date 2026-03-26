<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Demo data fallback ---

const DEMO_DATA = [
  { month: '2025-01', newBusiness: 80, expansion: 10, churn: 5 },
  { month: '2025-02', newBusiness: 95, expansion: 18, churn: 8 },
  { month: '2025-03', newBusiness: 120, expansion: 30, churn: 10 },
  { month: '2025-04', newBusiness: 150, expansion: 45, churn: 12 },
  { month: '2025-05', newBusiness: 185, expansion: 60, churn: 15 },
  { month: '2025-06', newBusiness: 220, expansion: 80, churn: 18 },
  { month: '2025-07', newBusiness: 260, expansion: 105, churn: 22 },
  { month: '2025-08', newBusiness: 310, expansion: 130, churn: 28 },
  { month: '2025-09', newBusiness: 365, expansion: 160, churn: 35 },
  { month: '2025-10', newBusiness: 420, expansion: 200, churn: 40 },
  { month: '2025-11', newBusiness: 490, expansion: 245, churn: 48 },
  { month: '2025-12', newBusiness: 560, expansion: 300, churn: 55 },
  { month: '2026-01', newBusiness: 640, expansion: 360, churn: 62 },
  { month: '2026-02', newBusiness: 730, expansion: 430, churn: 72 },
  { month: '2026-03', newBusiness: 830, expansion: 510, churn: 80 },
]

const chartData = computed(() => {
  const raw = props.data.length ? props.data : DEMO_DATA
  return raw.map((d, i) => {
    const totalArr = (d.newBusiness || 0) + (d.expansion || 0)
    const prevTotal = i > 0
      ? (raw[i - 1].newBusiness || 0) + (raw[i - 1].expansion || 0)
      : null
    const growthRate = prevTotal ? ((totalArr - prevTotal) / prevTotal) * 100 : 0
    return {
      month: d.month,
      monthLabel: formatMonth(d.month),
      newBusiness: (d.newBusiness || 0) / 1000,
      expansion: (d.expansion || 0) / 1000,
      churn: (d.churn || 0) / 1000,
      totalArr: totalArr / 1000,
      growthRate,
    }
  })
})

const milestones = computed(() => {
  const thresholds = [0.5, 1.0, 1.5, 2.0]
  const maxArr = d3.max(chartData.value, d => d.totalArr) || 0
  return thresholds.filter(t => t <= maxArr * 1.05)
})

function formatMonth(str) {
  const [year, month] = str.split('-')
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${names[parseInt(month, 10) - 1]} '${year.slice(2)}`
}

function formatDollar(val) {
  if (val >= 1) return `$${val.toFixed(1)}M`
  return `$${Math.round(val * 1000)}K`
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
  if (!container || !chartData.value.length) return

  const data = chartData.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 52, bottom: 32, left: 52 }
  const width = containerWidth - margin.left - margin.right
  const height = 260
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const defs = svg.append('defs')
  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // --- Scales ---
  const x = d3.scalePoint()
    .domain(data.map(d => d.month))
    .range([0, width])
    .padding(0.1)

  const maxArr = d3.max(data, d => d.totalArr) * 1.1
  const y = d3.scaleLinear()
    .domain([0, maxArr])
    .range([height, 0])
    .nice()

  const maxGrowth = d3.max(data, d => Math.abs(d.growthRate)) || 30
  const yGrowth = d3.scaleLinear()
    .domain([0, Math.ceil(maxGrowth / 10) * 10])
    .range([height, 0])
    .nice()

  // --- Grid lines ---
  const yTicks = y.ticks(5)
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.08))')
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,4')

  // --- Stacked area: New Business + Expansion ---
  const stackGen = d3.stack()
    .keys(['newBusiness', 'expansion'])
    .order(d3.stackOrderNone)
    .offset(d3.stackOffsetNone)

  const stacked = stackGen(data)

  const areaGen = d3.area()
    .x(d => x(d.data.month))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(d3.curveMonotoneX)

  const colors = {
    newBusiness: '#2068FF',
    expansion: 'rgba(32, 104, 255, 0.4)',
  }
  const fillIds = {}

  // Gradients for stacked areas
  stacked.forEach((series) => {
    const key = series.key
    const gradId = `arr-grad-${key}`
    fillIds[key] = gradId
    const baseColor = colors[key]

    const grad = defs.append('linearGradient')
      .attr('id', gradId)
      .attr('x1', '0').attr('y1', '0')
      .attr('x2', '0').attr('y2', '1')

    grad.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', baseColor)
      .attr('stop-opacity', key === 'newBusiness' ? 0.6 : 0.4)

    grad.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', baseColor)
      .attr('stop-opacity', 0.05)
  })

  // Render stacked areas with entrance animation
  g.selectAll('.stacked-area')
    .data(stacked)
    .join('path')
    .attr('d', areaGen)
    .attr('fill', d => `url(#${fillIds[d.key]})`)
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((_, i) => i * 100)
    .style('opacity', 1)

  // Total ARR line on top of stacked area
  const totalLine = d3.line()
    .x(d => x(d.month))
    .y(d => y(d.totalArr))
    .curve(d3.curveMonotoneX)

  const arrPath = g.append('path')
    .datum(data)
    .attr('d', totalLine)
    .attr('fill', 'none')
    .attr('stroke', '#2068FF')
    .attr('stroke-width', 2.5)

  // Animate line drawing
  const arrLen = arrPath.node().getTotalLength()
  arrPath
    .attr('stroke-dasharray', `${arrLen} ${arrLen}`)
    .attr('stroke-dashoffset', arrLen)
    .transition()
    .duration(800)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)

  // --- Churn line (red, below) ---
  const churnLine = d3.line()
    .x(d => x(d.month))
    .y(d => y(d.churn))
    .curve(d3.curveMonotoneX)

  const churnPath = g.append('path')
    .datum(data)
    .attr('d', churnLine)
    .attr('fill', 'none')
    .attr('stroke', '#ef4444')
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '6,3')

  const churnLen = churnPath.node().getTotalLength()
  churnPath
    .attr('stroke-dasharray', `${churnLen} ${churnLen}`)
    .attr('stroke-dashoffset', churnLen)
    .transition()
    .duration(800)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)
    .on('end', function () {
      d3.select(this).attr('stroke-dasharray', '6,3')
    })

  // Churn area fill
  const churnArea = d3.area()
    .x(d => x(d.month))
    .y0(y(0))
    .y1(d => y(d.churn))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', churnArea)
    .attr('fill', 'rgba(239, 68, 68, 0.06)')
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay(200)
    .style('opacity', 1)

  // --- Growth rate line (secondary Y-axis) ---
  const growthLine = d3.line()
    .x(d => x(d.month))
    .y(d => yGrowth(d.growthRate))
    .defined(d => d.growthRate != null)
    .curve(d3.curveMonotoneX)

  const growthGradId = 'arr-growth-grad'
  const growthGrad = defs.append('linearGradient')
    .attr('id', growthGradId)
    .attr('gradientUnits', 'userSpaceOnUse')
    .attr('x1', 0).attr('y1', yGrowth(maxGrowth))
    .attr('x2', 0).attr('y2', yGrowth(0))

  growthGrad.append('stop').attr('offset', '0%').attr('stop-color', '#009900')
  growthGrad.append('stop').attr('offset', '100%').attr('stop-color', '#f59e0b')

  const growthPath = g.append('path')
    .datum(data.slice(1))
    .attr('d', growthLine)
    .attr('fill', 'none')
    .attr('stroke', `url(#${growthGradId})`)
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '4,2')
    .style('opacity', 0.7)

  const growthLen = growthPath.node().getTotalLength()
  growthPath
    .attr('stroke-dasharray', `${growthLen} ${growthLen}`)
    .attr('stroke-dashoffset', growthLen)
    .transition()
    .duration(800)
    .delay(200)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)
    .on('end', function () {
      d3.select(this).attr('stroke-dasharray', '4,2')
    })

  // --- Milestone annotations ---
  milestones.value.forEach(threshold => {
    const yPos = y(threshold)

    g.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', yPos)
      .attr('y2', yPos)
      .attr('stroke', 'var(--color-primary, #2068FF)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,4')
      .style('opacity', 0.3)

    g.append('rect')
      .attr('x', width - 56)
      .attr('y', yPos - 10)
      .attr('width', 52)
      .attr('height', 16)
      .attr('rx', 3)
      .attr('fill', 'var(--color-primary-light, rgba(32,104,255,0.08))')

    g.append('text')
      .attr('x', width - 30)
      .attr('y', yPos)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('font-weight', '600')
      .attr('fill', 'var(--color-primary, #2068FF)')
      .text(formatDollar(threshold))
  })

  // --- Y-axis left (ARR) ---
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => formatDollar(d))

  // --- Y-axis right (Growth %) ---
  const growthTicks = yGrowth.ticks(4)
  g.selectAll('.y-growth-label')
    .data(growthTicks)
    .join('text')
    .attr('x', width + 8)
    .attr('y', d => yGrowth(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'start')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `${d}%`)

  // --- X-axis labels ---
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.month))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => d.monthLabel)

  // Axis titles
  g.append('text')
    .attr('x', -8)
    .attr('y', -6)
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text('ARR')

  g.append('text')
    .attr('x', width + 8)
    .attr('y', -6)
    .attr('text-anchor', 'start')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text('Growth %')

  // --- Data points for total ARR ---
  const dots = g.selectAll('.arr-dot')
    .data(data)
    .join('circle')
    .attr('cx', d => x(d.month))
    .attr('cy', d => y(d.totalArr))
    .attr('r', 0)
    .attr('fill', '#2068FF')
    .attr('stroke', 'var(--color-surface, #fff)')
    .attr('stroke-width', 1.5)

  dots.transition()
    .duration(300)
    .delay((_, i) => 800 + i * 30)
    .attr('r', 3.5)

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
    .style('min-width', '160px')

  // Vertical hover line
  const hoverLine = g.append('line')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'var(--color-border-strong, rgba(0,0,0,0.2))')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')
    .style('opacity', 0)

  // Invisible hover targets
  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].month) : x(d.month)
      return (prev + x(d.month)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].month) : x(d.month)
      const next = i < data.length - 1 ? x(data[i + 1].month) : x(d.month)
      return ((x(d.month) - prev) + (next - x(d.month))) / 2 || width / data.length
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const growthStr = d.growthRate > 0 ? `+${d.growthRate.toFixed(1)}%` : `${d.growthRate.toFixed(1)}%`
      const growthColor = d.growthRate >= 0 ? '#009900' : '#ef4444'

      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:6px">${d.monthLabel}</div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px">
            <span style="color:var(--color-text-muted,#888)">Total ARR</span>
            <span style="font-weight:600;color:var(--color-text,#050505)">${formatDollar(d.totalArr)}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px">
            <span style="color:#2068FF">New Business</span>
            <span style="font-weight:500">${formatDollar(d.newBusiness)}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px">
            <span style="color:rgba(32,104,255,0.7)">Expansion</span>
            <span style="font-weight:500">${formatDollar(d.expansion)}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px">
            <span style="color:#ef4444">Churn</span>
            <span style="font-weight:500">-${formatDollar(d.churn)}</span>
          </div>
          <div style="border-top:1px solid var(--color-border,rgba(0,0,0,0.1));margin-top:4px;padding-top:4px;display:flex;justify-content:space-between;gap:16px">
            <span style="color:var(--color-text-muted,#888)">Growth</span>
            <span style="font-weight:600;color:${growthColor}">${growthStr}</span>
          </div>
        `)
        .style('opacity', 1)

      hoverLine
        .attr('x1', x(d.month))
        .attr('x2', x(d.month))
        .style('opacity', 1)

      dots.filter(dd => dd.month === d.month)
        .transition().duration(100)
        .attr('r', 5.5)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      const tooltipX = event.clientX - rect.left + 14
      const tooltipRight = tooltipX + 180
      const flipX = tooltipRight > containerWidth ? event.clientX - rect.left - 194 : tooltipX

      tooltip
        .style('left', `${flipX}px`)
        .style('top', `${event.clientY - rect.top - 60}px`)
    })
    .on('mouseleave', (event, d) => {
      tooltip.style('opacity', 0)
      hoverLine.style('opacity', 0)
      dots.filter(dd => dd.month === d.month)
        .transition().duration(100)
        .attr('r', 3.5)
    })
}

// --- Lifecycle ---

watch(() => props.data, () => {
  nextTick(() => renderChart())
}, { deep: true })

onMounted(() => {
  renderChart()
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
        <h3 class="text-sm font-semibold text-[var(--color-text)]">ARR Trend</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">Annual recurring revenue over time</p>
      </div>
      <div v-if="chartData.length" class="text-right">
        <span class="text-lg font-bold text-[var(--color-text)]">
          {{ formatDollar(chartData[chartData.length - 1].totalArr) }}
        </span>
        <span
          v-if="chartData.length > 1"
          class="ml-1.5 text-xs font-medium"
          :class="chartData[chartData.length - 1].growthRate >= 0
            ? 'text-[var(--color-success)]'
            : 'text-[var(--color-error)]'"
        >
          {{ chartData[chartData.length - 1].growthRate >= 0 ? '+' : '' }}{{ chartData[chartData.length - 1].growthRate.toFixed(1) }}%
        </span>
      </div>
    </div>

    <div v-if="chartData.length" class="relative" ref="chartRef" style="height: 308px" />

    <div v-else class="flex items-center justify-center h-[260px] text-[var(--color-text-muted)] text-sm">
      <span>ARR data will appear once revenue metrics are available</span>
    </div>

    <!-- Legend -->
    <div v-if="chartData.length" class="flex items-center gap-5 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[#2068FF]" /> New Business
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[rgba(32,104,255,0.4)]" /> Expansion
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#ef4444]" style="border-top: 2px dashed #ef4444; height: 0;" /> Churn
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5" style="border-top: 2px dashed #009900; height: 0;" /> Growth Rate
      </span>
    </div>
  </div>
</template>
