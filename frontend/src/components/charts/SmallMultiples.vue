<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, required: true },
  chartType: { type: String, default: 'line', validator: v => ['line', 'bar', 'area'].includes(v) },
  columns: { type: Number, default: 3 },
  sharedYAxis: { type: Boolean, default: true },
})

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
}

const PALETTE = [
  COLORS.primary,
  COLORS.orange,
  COLORS.green,
  COLORS.purple,
  '#0ea5e9',
  '#e11d48',
  '#8b5cf6',
  '#14b8a6',
  '#f59e0b',
  '#6366f1',
]

const containerRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const hoveredX = ref(null)

const gridCols = computed(() => {
  if (!props.data.length) return 1
  return Math.min(props.columns, props.data.length)
})

const globalYDomain = computed(() => {
  if (!props.sharedYAxis || !props.data.length) return null
  let min = Infinity
  let max = -Infinity
  for (const dataset of props.data) {
    for (const pt of dataset.values || []) {
      if (pt.y < min) min = pt.y
      if (pt.y > max) max = pt.y
    }
  }
  if (min === Infinity) return [0, 1]
  const padding = (max - min) * 0.1 || 1
  return [Math.min(0, min - padding), max + padding]
})

function clearAll() {
  if (!containerRef.value) return
  const panels = containerRef.value.querySelectorAll('.sm-panel')
  for (const panel of panels) {
    d3.select(panel).selectAll('*').remove()
  }
}

function renderAll() {
  clearAll()
  if (!containerRef.value || !props.data.length) return
  nextTick(() => {
    const panels = containerRef.value.querySelectorAll('.sm-panel')
    props.data.forEach((dataset, i) => {
      if (panels[i]) renderChart(panels[i], dataset, i)
    })
  })
}

function renderChart(el, dataset, index) {
  const values = dataset.values || []
  if (!values.length) return

  const containerWidth = el.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 28, right: 12, bottom: 24, left: 36 }
  const width = containerWidth - margin.left - margin.right
  const height = 120
  const totalHeight = height + margin.top + margin.bottom
  const color = PALETTE[index % PALETTE.length]

  const svg = d3.select(el)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  // Title
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 16)
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text(dataset.title || `Dataset ${index + 1}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const xDomain = d3.extent(values, d => d.x)
  const x = d3.scaleLinear().domain(xDomain).range([0, width])

  const yDomain = globalYDomain.value || (() => {
    const [yMin, yMax] = d3.extent(values, d => d.y)
    const pad = (yMax - yMin) * 0.1 || 1
    return [Math.min(0, yMin - pad), yMax + pad]
  })()
  const y = d3.scaleLinear().domain(yDomain).range([height, 0])

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
    .attr('x', -6)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', '#aaa')
    .text(d => formatTick(d))

  // X-axis labels
  const xTicks = x.ticks(Math.min(5, values.length))
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', '#aaa')
    .text(d => formatTick(d))

  // Render the chart type
  if (props.chartType === 'bar') {
    renderBars(g, values, x, y, width, height, color)
  } else if (props.chartType === 'area') {
    renderArea(g, values, x, y, height, color)
    renderLine(g, values, x, y, color)
  } else {
    renderLine(g, values, x, y, color)
    renderDots(g, values, x, y, color, index)
  }

  // Crosshair line (hidden by default, shown on hover)
  const crosshair = g.append('line')
    .attr('class', 'crosshair')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.2)')
    .attr('stroke-dasharray', '3,3')
    .attr('stroke-width', 1)
    .style('opacity', 0)
    .style('pointer-events', 'none')

  // Crosshair dot
  const crossDot = g.append('circle')
    .attr('class', 'cross-dot')
    .attr('r', 4)
    .attr('fill', color)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('opacity', 0)
    .style('pointer-events', 'none')

  // Tooltip
  const tooltip = d3.select(el)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '6px')
    .style('padding', '6px 10px')
    .style('font-size', '11px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('white-space', 'nowrap')

  // Hover overlay
  g.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'crosshair')
    .on('mousemove', (event) => {
      const [mx] = d3.pointer(event)
      const xVal = x.invert(mx)
      const closest = findClosest(values, xVal)
      if (!closest) return

      hoveredX.value = closest.x

      showCrosshair(crosshair, crossDot, x, y, closest, tooltip, el, margin)
    })
    .on('mouseleave', () => {
      hoveredX.value = null
      crosshair.style('opacity', 0)
      crossDot.style('opacity', 0)
      tooltip.style('opacity', 0)
    })

  // Store references for cross-chart sync
  el._smRefs = { x, y, values, crosshair, crossDot, tooltip, margin, color }
}

function showCrosshair(crosshair, crossDot, x, y, point, tooltip, el, margin) {
  crosshair
    .attr('x1', x(point.x))
    .attr('x2', x(point.x))
    .style('opacity', 1)

  crossDot
    .attr('cx', x(point.x))
    .attr('cy', y(point.y))
    .style('opacity', 1)

  const rect = el.getBoundingClientRect()
  tooltip
    .html(`<span style="font-weight:600;color:var(--color-text,#050505)">${formatValue(point.y)}</span> <span style="color:var(--color-text-muted,#888)">at ${formatTick(point.x)}</span>`)
    .style('opacity', 1)
    .style('left', `${x(point.x) + margin.left + 10}px`)
    .style('top', `${y(point.y) + margin.top - 12}px`)
}

function renderLine(g, values, x, y, color) {
  const line = d3.line()
    .x(d => x(d.x))
    .y(d => y(d.y))
    .curve(d3.curveMonotoneX)

  const path = g.append('path')
    .datum(values)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', color)
    .attr('stroke-width', 2)

  const totalLength = path.node().getTotalLength()
  path
    .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(600)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)
}

function renderDots(g, values, x, y, color, delayBase) {
  g.selectAll('.dot')
    .data(values)
    .join('circle')
    .attr('cx', d => x(d.x))
    .attr('cy', d => y(d.y))
    .attr('r', 0)
    .attr('fill', color)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('pointer-events', 'none')
    .transition()
    .duration(300)
    .delay((_, i) => 600 + i * 30)
    .attr('r', 3)
}

function renderArea(g, values, x, y, height, color) {
  const area = d3.area()
    .x(d => x(d.x))
    .y0(height)
    .y1(d => y(d.y))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(values)
    .attr('d', area)
    .attr('fill', color)
    .attr('fill-opacity', 0.12)
    .style('opacity', 0)
    .transition()
    .duration(600)
    .ease(d3.easeCubicOut)
    .style('opacity', 1)
}

function renderBars(g, values, x, y, width, height, color) {
  const barWidth = Math.max(2, (width / values.length) * 0.7)

  g.selectAll('.bar')
    .data(values)
    .join('rect')
    .attr('x', d => x(d.x) - barWidth / 2)
    .attr('y', height)
    .attr('width', barWidth)
    .attr('height', 0)
    .attr('rx', 2)
    .attr('fill', color)
    .attr('opacity', 0.8)
    .transition()
    .duration(600)
    .delay((_, i) => i * 30)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.y))
    .attr('height', d => height - y(d.y))
}

function findClosest(values, targetX) {
  if (!values.length) return null
  let closest = values[0]
  let minDist = Math.abs(values[0].x - targetX)
  for (let i = 1; i < values.length; i++) {
    const dist = Math.abs(values[i].x - targetX)
    if (dist < minDist) {
      minDist = dist
      closest = values[i]
    }
  }
  return closest
}

function formatTick(val) {
  if (Math.abs(val) >= 1000) return d3.format('.2s')(val)
  if (Number.isInteger(val)) return String(val)
  return d3.format('.1f')(val)
}

function formatValue(val) {
  if (Math.abs(val) >= 1000) return d3.format(',.0f')(val)
  if (Number.isInteger(val)) return String(val)
  return d3.format('.2f')(val)
}

// Cross-chart hover sync
watch(hoveredX, (xVal) => {
  if (!containerRef.value) return
  const panels = containerRef.value.querySelectorAll('.sm-panel')

  for (const panel of panels) {
    const refs = panel._smRefs
    if (!refs) continue

    if (xVal == null) {
      refs.crosshair.style('opacity', 0)
      refs.crossDot.style('opacity', 0)
      refs.tooltip.style('opacity', 0)
      continue
    }

    const closest = findClosest(refs.values, xVal)
    if (!closest) continue

    showCrosshair(
      refs.crosshair, refs.crossDot,
      refs.x, refs.y, closest,
      refs.tooltip, panel, refs.margin
    )
  }
})

watch([() => props.data, () => props.chartType, () => props.columns, () => props.sharedYAxis], () => {
  nextTick(() => renderAll())
}, { deep: true })

onMounted(() => {
  renderAll()
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderAll, 200)
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div
    ref="containerRef"
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4"
  >
    <div
      v-if="data.length"
      class="grid gap-4"
      :style="{ gridTemplateColumns: `repeat(${gridCols}, 1fr)` }"
    >
      <div
        v-for="(dataset, i) in data"
        :key="dataset.title || i"
        class="sm-panel relative border border-[var(--color-border)] rounded-md bg-[var(--color-bg)] overflow-hidden"
        style="min-height: 172px"
      />
    </div>

    <div
      v-else
      class="flex items-center justify-center h-[172px] text-[var(--color-text-muted)] text-sm"
    >
      No data available
    </div>
  </div>
</template>
