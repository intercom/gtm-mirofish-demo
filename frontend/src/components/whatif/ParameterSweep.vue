<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  /** Array of sweep data points: [{ paramValue: number, metrics: { [key]: { mean: number, stddev: number } } }] */
  data: { type: Array, default: () => [] },
  /** Label for the x-axis parameter */
  parameterName: { type: String, default: 'Parameter' },
  /** Optional unit for the x-axis (e.g., 'agents', 'rounds') */
  parameterUnit: { type: String, default: '' },
  /** Metric definitions: [{ key: string, label: string, color?: string, higherIsBetter?: boolean }] */
  metrics: { type: Array, default: () => [] },
})

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
}

const METRIC_COLORS = [COLORS.primary, COLORS.orange, COLORS.purple, COLORS.green, '#E91E63', '#00BCD4']

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const enabledMetrics = ref(new Set())

const resolvedMetrics = computed(() =>
  props.metrics.map((m, i) => ({
    ...m,
    color: m.color || METRIC_COLORS[i % METRIC_COLORS.length],
    higherIsBetter: m.higherIsBetter !== false,
  })),
)

// Demo data for when no real data is provided
const DEMO_DATA = [
  { paramValue: 2, metrics: { consensus: { mean: 0.32, stddev: 0.08 }, sentiment: { mean: 0.15, stddev: 0.05 }, speed: { mean: 0.90, stddev: 0.04 } } },
  { paramValue: 3, metrics: { consensus: { mean: 0.48, stddev: 0.10 }, sentiment: { mean: 0.28, stddev: 0.07 }, speed: { mean: 0.82, stddev: 0.06 } } },
  { paramValue: 4, metrics: { consensus: { mean: 0.61, stddev: 0.09 }, sentiment: { mean: 0.38, stddev: 0.06 }, speed: { mean: 0.71, stddev: 0.05 } } },
  { paramValue: 5, metrics: { consensus: { mean: 0.72, stddev: 0.07 }, sentiment: { mean: 0.45, stddev: 0.08 }, speed: { mean: 0.58, stddev: 0.07 } } },
  { paramValue: 6, metrics: { consensus: { mean: 0.78, stddev: 0.06 }, sentiment: { mean: 0.49, stddev: 0.09 }, speed: { mean: 0.44, stddev: 0.06 } } },
  { paramValue: 7, metrics: { consensus: { mean: 0.81, stddev: 0.08 }, sentiment: { mean: 0.51, stddev: 0.10 }, speed: { mean: 0.31, stddev: 0.08 } } },
  { paramValue: 8, metrics: { consensus: { mean: 0.82, stddev: 0.09 }, sentiment: { mean: 0.50, stddev: 0.11 }, speed: { mean: 0.20, stddev: 0.07 } } },
]

const DEMO_METRICS = [
  { key: 'consensus', label: 'Consensus Score', higherIsBetter: true },
  { key: 'sentiment', label: 'Avg Sentiment', higherIsBetter: true },
  { key: 'speed', label: 'Resolution Speed', higherIsBetter: true },
]

const isDemo = computed(() => !props.data.length || !props.metrics.length)
const chartData = computed(() => isDemo.value ? DEMO_DATA : props.data)
const chartMetrics = computed(() => {
  const source = isDemo.value ? DEMO_METRICS : resolvedMetrics.value
  return source.map((m, i) => ({
    ...m,
    color: m.color || METRIC_COLORS[i % METRIC_COLORS.length],
    higherIsBetter: m.higherIsBetter !== false,
  }))
})

// Initialize enabled metrics when metrics change
watch(chartMetrics, (m) => {
  enabledMetrics.value = new Set(m.map(d => d.key))
}, { immediate: true })

function toggleMetric(key) {
  const next = new Set(enabledMetrics.value)
  if (next.has(key)) {
    if (next.size > 1) next.delete(key)
  } else {
    next.add(key)
  }
  enabledMetrics.value = next
}

function findOptimal(metricDef) {
  const data = chartData.value
  if (!data.length) return null
  let best = data[0]
  for (const point of data) {
    const val = point.metrics[metricDef.key]?.mean ?? 0
    const bestVal = best.metrics[metricDef.key]?.mean ?? 0
    if (metricDef.higherIsBetter ? val > bestVal : val < bestVal) {
      best = point
    }
  }
  return best
}

function findDiminishingReturnsStart(metricDef) {
  const data = chartData.value
  if (data.length < 3) return null

  const values = data.map(d => d.metrics[metricDef.key]?.mean ?? 0)

  // Compute slopes between consecutive points
  for (let i = 1; i < values.length - 1; i++) {
    const slopeBefore = values[i] - values[i - 1]
    const slopeAfter = values[i + 1] - values[i]
    const dir = metricDef.higherIsBetter ? 1 : -1

    // Diminishing returns: slope starts declining significantly
    if (dir * slopeBefore > 0.02 && dir * slopeAfter < dir * slopeBefore * 0.4) {
      return data[i].paramValue
    }
  }
  return null
}

// --- D3 Rendering ---

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
  const metrics = chartMetrics.value.filter(m => enabledMetrics.value.has(m.key))
  if (!data.length || !metrics.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 24, right: 24, bottom: 44, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = 280
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const xExtent = d3.extent(data, d => d.paramValue)
  const x = d3.scaleLinear()
    .domain(xExtent)
    .range([0, width])

  // Compute y-domain across all enabled metrics (including confidence bands)
  let yMin = Infinity
  let yMax = -Infinity
  for (const point of data) {
    for (const m of metrics) {
      const v = point.metrics[m.key]
      if (!v) continue
      const lo = v.mean - (v.stddev || 0)
      const hi = v.mean + (v.stddev || 0)
      if (lo < yMin) yMin = lo
      if (hi > yMax) yMax = hi
    }
  }
  const yPad = (yMax - yMin) * 0.1 || 0.1
  const y = d3.scaleLinear()
    .domain([yMin - yPad, yMax + yPad])
    .range([height, 0])
    .nice()

  // Grid lines
  const yTicks = y.ticks(6)
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
    .text(d => d.toFixed(2))

  // X-axis labels
  const xTicks = data.map(d => d.paramValue)
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => d)

  // X-axis title
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height + 38)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#666')
    .text(props.parameterName + (props.parameterUnit ? ` (${props.parameterUnit})` : ''))

  // Diminishing returns shading (for primary enabled metric)
  const primaryMetric = metrics[0]
  const drStart = findDiminishingReturnsStart(primaryMetric)
  if (drStart != null) {
    g.append('rect')
      .attr('x', x(drStart))
      .attr('y', 0)
      .attr('width', width - x(drStart))
      .attr('height', height)
      .attr('fill', 'rgba(255, 86, 0, 0.04)')
      .style('opacity', 0)
      .transition()
      .duration(800)
      .delay(600)
      .style('opacity', 1)

    g.append('text')
      .attr('x', x(drStart) + 6)
      .attr('y', 14)
      .attr('font-size', '9px')
      .attr('fill', COLORS.orange)
      .attr('opacity', 0.7)
      .text('Diminishing returns')
      .style('opacity', 0)
      .transition()
      .duration(400)
      .delay(1000)
      .style('opacity', 0.7)
  }

  // Draw each metric
  metrics.forEach((metricDef, mi) => {
    const metricData = data
      .filter(d => d.metrics[metricDef.key])
      .map(d => ({
        paramValue: d.paramValue,
        mean: d.metrics[metricDef.key].mean,
        stddev: d.metrics[metricDef.key].stddev || 0,
      }))

    if (!metricData.length) return

    // Confidence band
    const area = d3.area()
      .x(d => x(d.paramValue))
      .y0(d => y(d.mean - d.stddev))
      .y1(d => y(d.mean + d.stddev))
      .curve(d3.curveMonotoneX)

    g.append('path')
      .datum(metricData)
      .attr('d', area)
      .attr('fill', metricDef.color)
      .attr('opacity', 0)
      .transition()
      .duration(600)
      .delay(mi * 100)
      .attr('opacity', 0.1)

    // Line
    const line = d3.line()
      .x(d => x(d.paramValue))
      .y(d => y(d.mean))
      .curve(d3.curveMonotoneX)

    const path = g.append('path')
      .datum(metricData)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', metricDef.color)
      .attr('stroke-width', 2.5)

    // Animate line drawing
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .delay(mi * 100)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Scatter points
    g.selectAll(`.dot-${mi}`)
      .data(metricData)
      .join('circle')
      .attr('cx', d => x(d.paramValue))
      .attr('cy', d => y(d.mean))
      .attr('r', 0)
      .attr('fill', metricDef.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .transition()
      .duration(300)
      .delay((_, i) => 800 + mi * 100 + i * 50)
      .attr('r', 4.5)

    // Optimal annotation
    const optimal = findOptimal(metricDef)
    if (optimal && mi === 0) {
      const optVal = optimal.metrics[metricDef.key]
      const cx = x(optimal.paramValue)
      const cy = y(optVal.mean)

      // Pulsing ring
      const ring = g.append('circle')
        .attr('cx', cx)
        .attr('cy', cy)
        .attr('r', 0)
        .attr('fill', 'none')
        .attr('stroke', metricDef.color)
        .attr('stroke-width', 2)
        .attr('opacity', 0)

      ring.transition()
        .duration(400)
        .delay(1200)
        .attr('r', 10)
        .attr('opacity', 0.6)

      // Label
      const labelX = cx + (cx > width / 2 ? -14 : 14)
      const labelAnchor = cx > width / 2 ? 'end' : 'start'

      const labelGroup = g.append('g')
        .attr('opacity', 0)

      labelGroup.append('text')
        .attr('x', labelX)
        .attr('y', cy - 10)
        .attr('text-anchor', labelAnchor)
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', metricDef.color)
        .text('Optimal')

      labelGroup.append('text')
        .attr('x', labelX)
        .attr('y', cy + 2)
        .attr('text-anchor', labelAnchor)
        .attr('font-size', '9px')
        .attr('fill', '#888')
        .text(`${optimal.paramValue} = ${optVal.mean.toFixed(2)}`)

      labelGroup.transition()
        .duration(400)
        .delay(1200)
        .attr('opacity', 1)
    }
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

  // Vertical hover line + invisible rects for hit targets
  const hoverLine = g.append('line')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-dasharray', '3,3')
    .style('opacity', 0)

  // All dots for highlight
  const allDots = g.selectAll('circle')

  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].paramValue) : x(d.paramValue)
      return (prev + x(d.paramValue)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].paramValue) : x(d.paramValue)
      const next = i < data.length - 1 ? x(data[i + 1].paramValue) : x(d.paramValue)
      return Math.max(((x(d.paramValue) - prev) + (next - x(d.paramValue))) / 2, 20)
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      hoverLine
        .attr('x1', x(d.paramValue))
        .attr('x2', x(d.paramValue))
        .style('opacity', 1)

      allDots.filter(dd => dd && dd.paramValue === d.paramValue)
        .transition().duration(100).attr('r', 6.5)

      const lines = metrics.map(m => {
        const val = d.metrics[m.key]
        if (!val) return ''
        return `<div style="display:flex;align-items:center;gap:6px;margin-top:3px">
          <span style="width:8px;height:8px;border-radius:50%;background:${m.color};display:inline-block"></span>
          <span style="color:#666">${m.label}:</span>
          <span style="font-weight:600;color:${m.color}">${val.mean.toFixed(3)}</span>
          <span style="color:#aaa;font-size:11px">&plusmn;${val.stddev.toFixed(3)}</span>
        </div>`
      }).join('')

      tooltip.html(`
        <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">
          ${props.parameterName}: ${d.paramValue}${props.parameterUnit ? ' ' + props.parameterUnit : ''}
        </div>
        ${lines}
      `).style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 20}px`)
    })
    .on('mouseleave', (event, d) => {
      hoverLine.style('opacity', 0)
      tooltip.style('opacity', 0)
      allDots.filter(dd => dd && dd.paramValue === d.paramValue)
        .transition().duration(100).attr('r', 4.5)
    })
}

// --- Lifecycle ---

watch([chartData, enabledMetrics], () => {
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
  <div class="bg-[var(--color-surface,#fff)] border border-[var(--color-border,rgba(0,0,0,0.1))] rounded-lg p-5">
    <div class="flex items-center justify-between mb-1">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text,#050505)]">Parameter Sweep</h3>
        <p class="text-xs text-[var(--color-text-muted,#888)] mt-0.5">
          {{ isDemo ? 'Demo: ' : '' }}Outcome metrics vs {{ parameterName.toLowerCase() }} value
        </p>
      </div>
    </div>

    <!-- Metric toggle legend -->
    <div class="flex flex-wrap items-center gap-3 mt-3 mb-4">
      <button
        v-for="m in chartMetrics"
        :key="m.key"
        class="flex items-center gap-1.5 text-xs px-2 py-1 rounded-md border transition-all cursor-pointer"
        :class="enabledMetrics.has(m.key)
          ? 'border-transparent bg-black/5 text-[var(--color-text,#050505)] font-medium'
          : 'border-transparent bg-transparent text-[var(--color-text-muted,#aaa)]'"
        @click="toggleMetric(m.key)"
      >
        <span
          class="inline-block w-2.5 h-2.5 rounded-full transition-opacity"
          :style="{ background: m.color, opacity: enabledMetrics.has(m.key) ? 1 : 0.3 }"
        />
        {{ m.label }}
      </button>
    </div>

    <div ref="chartRef" class="relative w-full" style="min-height: 340px" />
  </div>
</template>
