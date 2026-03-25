<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const granularity = ref('monthly')
const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  addition: '#009900',
  subtraction: '#ef4444',
  total: '#2068FF',
  connector: 'rgba(0,0,0,0.15)',
  grid: 'rgba(0,0,0,0.06)',
  text: '#050505',
  muted: '#888',
  labelLight: '#fff',
  labelDark: '#050505',
}

const DEMO_DATA = {
  monthly: [
    { period: 'Jan', start: 2400000, additions: 860000, subtractions: 320000 },
    { period: 'Feb', start: 2940000, additions: 720000, subtractions: 410000 },
    { period: 'Mar', start: 3250000, additions: 1100000, subtractions: 280000 },
    { period: 'Apr', start: 4070000, additions: 640000, subtractions: 510000 },
    { period: 'May', start: 4200000, additions: 930000, subtractions: 370000 },
    { period: 'Jun', start: 4760000, additions: 780000, subtractions: 440000 },
  ],
  weekly: [
    { period: 'W1', start: 2400000, additions: 210000, subtractions: 80000 },
    { period: 'W2', start: 2530000, additions: 180000, subtractions: 95000 },
    { period: 'W3', start: 2615000, additions: 260000, subtractions: 60000 },
    { period: 'W4', start: 2815000, additions: 190000, subtractions: 120000 },
    { period: 'W5', start: 2885000, additions: 150000, subtractions: 70000 },
    { period: 'W6', start: 2965000, additions: 240000, subtractions: 110000 },
    { period: 'W7', start: 3095000, additions: 280000, subtractions: 90000 },
    { period: 'W8', start: 3285000, additions: 170000, subtractions: 140000 },
    { period: 'W9', start: 3315000, additions: 320000, subtractions: 75000 },
    { period: 'W10', start: 3560000, additions: 200000, subtractions: 110000 },
    { period: 'W11', start: 3650000, additions: 260000, subtractions: 130000 },
    { period: 'W12', start: 3780000, additions: 310000, subtractions: 90000 },
  ],
}

const chartData = computed(() => {
  const source = props.data.length ? props.data : DEMO_DATA[granularity.value]
  return buildWaterfallBars(source)
})

function buildWaterfallBars(raw) {
  const bars = []
  let runningTotal = raw[0].start

  bars.push({ label: 'Start', value: runningTotal, type: 'total', bottom: 0, top: runningTotal })

  for (const d of raw) {
    bars.push({
      label: `+${d.period}`,
      displayLabel: d.period,
      value: d.additions,
      type: 'addition',
      bottom: runningTotal,
      top: runningTotal + d.additions,
    })

    runningTotal += d.additions

    bars.push({
      label: `-${d.period}`,
      displayLabel: d.period,
      value: d.subtractions,
      type: 'subtraction',
      bottom: runningTotal - d.subtractions,
      top: runningTotal,
    })

    runningTotal -= d.subtractions
  }

  bars.push({ label: 'Current', value: runningTotal, type: 'total', bottom: 0, top: runningTotal })

  return bars
}

function formatValue(v) {
  if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`
  if (v >= 1000) return `$${(v / 1000).toFixed(0)}K`
  return `$${v}`
}

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const data = chartData.value
  if (!data.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 24, right: 20, bottom: 44, left: 60 }
  const width = containerWidth - margin.left - margin.right
  const height = 320
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(data, d => d.top) * 1.1

  const x = d3.scaleBand()
    .domain(data.map(d => d.label))
    .range([0, width])
    .padding(0.25)

  const y = d3.scaleLinear()
    .domain([0, maxVal])
    .range([height, 0])

  // Grid lines
  const yTicks = y.ticks(6)
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', COLORS.grid)
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
    .text(d => formatValue(d))

  // Connector lines between bars
  for (let i = 0; i < data.length - 1; i++) {
    const curr = data[i]
    const next = data[i + 1]
    const connectorY = curr.type === 'subtraction' ? y(curr.bottom) : y(curr.top)

    g.append('line')
      .attr('x1', x(curr.label) + x.bandwidth())
      .attr('x2', x(next.label))
      .attr('y1', connectorY)
      .attr('y2', connectorY)
      .attr('stroke', COLORS.connector)
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3')
      .style('opacity', 0)
      .transition()
      .duration(300)
      .delay(i * 60 + 400)
      .style('opacity', 1)
  }

  // Bars with animation
  g.selectAll('.bar')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.label))
    .attr('y', height)
    .attr('width', x.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', d => {
      if (d.type === 'addition') return COLORS.addition
      if (d.type === 'subtraction') return COLORS.subtraction
      return COLORS.total
    })
    .attr('opacity', 0.88)
    .transition()
    .duration(600)
    .delay((d, i) => i * 60)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.top))
    .attr('height', d => y(d.bottom) - y(d.top))

  // Value labels on bars
  g.selectAll('.bar-value')
    .data(data)
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', d => {
      const barHeight = y(d.bottom) - y(d.top)
      if (barHeight > 28) return y(d.top) + barHeight / 2
      return y(d.top) - 8
    })
    .attr('dy', d => {
      const barHeight = y(d.bottom) - y(d.top)
      return barHeight > 28 ? '0.35em' : '0'
    })
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', d => {
      const barHeight = y(d.bottom) - y(d.top)
      if (barHeight > 28) return COLORS.labelLight
      if (d.type === 'addition') return COLORS.addition
      if (d.type === 'subtraction') return COLORS.subtraction
      return COLORS.total
    })
    .style('opacity', 0)
    .text(d => formatValue(d.value))
    .transition()
    .duration(300)
    .delay((d, i) => 500 + i * 60)
    .style('opacity', 1)

  // X-axis labels — show period under each addition/subtraction pair, label totals directly
  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', d => d.type === 'total' ? COLORS.text : COLORS.muted)
    .attr('font-weight', d => d.type === 'total' ? '600' : '400')
    .text(d => {
      if (d.type === 'total') return d.label
      return ''
    })

  // Period labels centered between each addition/subtraction pair
  const source = props.data.length ? props.data : DEMO_DATA[granularity.value]
  source.forEach((d, i) => {
    const addLabel = `+${d.period}`
    const subLabel = `-${d.period}`
    const addX = x(addLabel)
    const subX = x(subLabel)
    if (addX == null || subX == null) return
    const cx = (addX + subX + x.bandwidth()) / 2

    g.append('text')
      .attr('x', cx)
      .attr('y', height + 16)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', COLORS.muted)
      .text(d.period)
  })

  // +/- indicators below period labels
  g.selectAll('.x-indicator')
    .data(data.filter(d => d.type !== 'total'))
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 30)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', d => d.type === 'addition' ? COLORS.addition : COLORS.subtraction)
    .text(d => d.type === 'addition' ? '+' : '\u2212')

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

  // Hover targets
  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.label))
    .attr('y', 0)
    .attr('width', x.bandwidth())
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const typeLabel = d.type === 'addition' ? 'New Opportunities' : d.type === 'subtraction' ? 'Lost / Disqualified' : 'Pipeline Total'
      const color = d.type === 'addition' ? COLORS.addition : d.type === 'subtraction' ? COLORS.subtraction : COLORS.total
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,${COLORS.text});margin-bottom:2px">${typeLabel}</div>
          <div style="color:${color};font-weight:700;font-size:14px">${formatValue(d.value)}</div>
          ${d.type !== 'total' ? `<div style="color:var(--color-text-muted,${COLORS.muted});margin-top:2px;font-size:11px">Running total: ${formatValue(d.type === 'addition' ? d.top : d.bottom)}</div>` : ''}
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
    })
}

watch([chartData, granularity], () => {
  nextTick(() => renderChart())
})

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
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Pipeline Waterfall</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">How pipeline value changes over time</p>
      </div>
      <div class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="granularity === 'monthly'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="granularity = 'monthly'"
        >
          Monthly
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="granularity === 'weekly'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="granularity = 'weekly'"
        >
          Weekly
        </button>
      </div>
    </div>

    <div ref="chartRef" class="relative w-full" style="min-height: 400px" />

    <div class="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #2068FF" /> Pipeline Total
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #009900" /> New Opportunities
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #ef4444" /> Lost / Disqualified
      </span>
    </div>
  </div>
</template>
