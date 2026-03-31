<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: {
    type: Array,
    default: () => [
      { label: 'Starting MRR', value: 2450000, type: 'total' },
      { label: 'New', value: 320000, type: 'increase' },
      { label: 'Expansion', value: 185000, type: 'increase' },
      { label: 'Contraction', value: -95000, type: 'decrease' },
      { label: 'Churn', value: -142000, type: 'decrease' },
      { label: 'Ending MRR', value: 2718000, type: 'total' },
    ],
  },
  title: { type: String, default: 'MRR Bridge' },
  subtitle: { type: String, default: 'Monthly recurring revenue waterfall' },
  formatValue: { type: Function, default: null },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  increase: '#009900',
  decrease: '#ef4444',
  total: '#2068FF',
  connector: 'rgba(0,0,0,0.15)',
  text: '#050505',
  muted: '#888',
  grid: 'rgba(0,0,0,0.06)',
  barBg: 'rgba(0,0,0,0.03)',
}

// --- Value formatting ---

function fmt(value) {
  if (props.formatValue) return props.formatValue(value)
  const abs = Math.abs(value)
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value}`
}

// --- Compute waterfall positions ---

function computeWaterfallData(data) {
  const items = []
  let runningTotal = 0

  for (let i = 0; i < data.length; i++) {
    const d = data[i]
    if (d.type === 'total') {
      items.push({
        ...d,
        start: 0,
        end: d.value,
        y0: 0,
        y1: d.value,
      })
      runningTotal = d.value
    } else {
      const start = runningTotal
      runningTotal += d.value
      items.push({
        ...d,
        start,
        end: runningTotal,
        y0: Math.min(start, runningTotal),
        y1: Math.max(start, runningTotal),
      })
    }
  }

  return items
}

// --- Render ---

function render() {
  const container = chartRef.value
  if (!container) return

  d3.select(container).selectAll('*').remove()

  const items = computeWaterfallData(props.data)
  if (!items.length) return

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 56, left: 64 }
  const width = containerWidth - margin.left - margin.right
  const height = 320
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  // Title
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text(props.title)

  // Subtitle
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text(props.subtitle)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const allValues = items.flatMap(d => [d.y0, d.y1])
  const yMax = d3.max(allValues) * 1.1
  const yMin = Math.min(0, d3.min(allValues)) * 1.1

  const x = d3.scaleBand()
    .domain(items.map(d => d.label))
    .range([0, width])
    .paddingInner(0.3)
    .paddingOuter(0.15)

  const y = d3.scaleLinear()
    .domain([yMin, yMax])
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
    .text(d => fmt(d))

  // X-axis labels
  g.selectAll('.x-label')
    .data(items)
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text(d => d.label)

  // +/- prefix labels
  g.selectAll('.x-prefix')
    .data(items)
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 30)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', d => COLORS[d.type])
    .text(d => {
      if (d.type === 'total') return ''
      return d.value >= 0 ? `+${fmt(d.value)}` : fmt(d.value)
    })

  // Connector lines between bars
  for (let i = 0; i < items.length - 1; i++) {
    const curr = items[i]
    const next = items[i + 1]
    const connectorY = y(curr.end)

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
      .delay(400 + i * 120)
      .style('opacity', 1)
  }

  // Bars — animate from zero height
  g.selectAll('.bar')
    .data(items)
    .join('rect')
    .attr('x', d => x(d.label))
    .attr('width', x.bandwidth())
    .attr('rx', 4)
    .attr('fill', d => COLORS[d.type])
    .attr('opacity', 0.85)
    .attr('y', d => d.type === 'total' ? y(0) : y(d.start))
    .attr('height', 0)
    .transition()
    .duration(600)
    .delay((d, i) => i * 120)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.y1))
    .attr('height', d => Math.max(0, y(d.y0) - y(d.y1)))

  // Running total line
  const lineData = items.map(d => ({
    x: x(d.label) + x.bandwidth() / 2,
    y: y(d.end),
  }))

  const line = d3.line()
    .x(d => d.x)
    .y(d => d.y)
    .curve(d3.curveMonotoneX)

  const totalPath = g.append('path')
    .datum(lineData)
    .attr('fill', 'none')
    .attr('stroke', COLORS.text)
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '4,3')
    .attr('opacity', 0.3)
    .attr('d', line)

  // Animate the running total line using stroke-dashoffset
  const pathLength = totalPath.node().getTotalLength()
  totalPath
    .attr('stroke-dasharray', `${pathLength}`)
    .attr('stroke-dashoffset', pathLength)
    .transition()
    .duration(items.length * 120 + 600)
    .ease(d3.easeLinear)
    .attr('stroke-dashoffset', 0)

  // Running total dots
  g.selectAll('.total-dot')
    .data(lineData)
    .join('circle')
    .attr('cx', d => d.x)
    .attr('cy', d => d.y)
    .attr('r', 0)
    .attr('fill', COLORS.text)
    .attr('opacity', 0.4)
    .transition()
    .duration(300)
    .delay((d, i) => i * 120 + 400)
    .ease(d3.easeCubicOut)
    .attr('r', 3)

  // Value labels on bars — count up with easing
  g.selectAll('.bar-value')
    .data(items)
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', d => y(d.y1) - 8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('fill', d => COLORS[d.type])
    .style('opacity', 0)
    .each(function (d, i) {
      const el = d3.select(this)
      const targetValue = d.value

      el.transition()
        .duration(600)
        .delay(i * 120)
        .style('opacity', 1)
        .tween('text', function () {
          const interpolate = d3.interpolateNumber(0, targetValue)
          return function (t) {
            const val = Math.round(interpolate(t))
            el.text(d.type === 'total' ? fmt(val) : (val >= 0 ? `+${fmt(val)}` : fmt(val)))
          }
        })
    })

  // Legend
  const legendItems = [
    { label: 'Increase', color: COLORS.increase },
    { label: 'Decrease', color: COLORS.decrease },
    { label: 'Total', color: COLORS.total },
  ]

  const legend = svg.append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 240}, 14)`)

  legendItems.forEach((item, i) => {
    const offset = i * 80
    legend.append('rect')
      .attr('x', offset)
      .attr('y', 0)
      .attr('width', 10)
      .attr('height', 10)
      .attr('rx', 2)
      .attr('fill', item.color)
      .attr('opacity', 0.85)

    legend.append('text')
      .attr('x', offset + 16)
      .attr('y', 9)
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(item.label)
  })
}

// --- Lifecycle ---

watch(() => props.data, () => {
  nextTick(() => render())
}, { deep: true })

onMounted(() => {
  render()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => render(), 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
    <div ref="chartRef" class="w-full" />
  </div>
</template>
