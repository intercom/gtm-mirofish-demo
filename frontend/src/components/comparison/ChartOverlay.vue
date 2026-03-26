<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  dataA: { type: Array, default: () => [] },
  dataB: { type: Array, default: () => [] },
  labelA: { type: String, default: 'Sim A' },
  labelB: { type: String, default: 'Sim B' },
  metric: { type: String, default: 'sentiment' },
  chartType: { type: String, default: 'line' },
})

const chartRef = ref(null)
const viewMode = ref('both') // 'both' | 'a' | 'b' | 'difference'
let resizeObserver = null
let resizeTimer = null

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function getValue(d) {
  return d[props.metric] ?? d.sentiment ?? d.actions ?? 0
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || (!props.dataA.length && !props.dataB.length)) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 20, bottom: 32, left: 44 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxRound = Math.max(
    props.dataA.length ? props.dataA[props.dataA.length - 1].round : 0,
    props.dataB.length ? props.dataB[props.dataB.length - 1].round : 0,
  )

  const allValues = [
    ...(viewMode.value !== 'b' ? props.dataA.map(getValue) : []),
    ...(viewMode.value !== 'a' ? props.dataB.map(getValue) : []),
  ]

  if (viewMode.value === 'difference') {
    const minLen = Math.min(props.dataA.length, props.dataB.length)
    allValues.length = 0
    for (let i = 0; i < minLen; i++) {
      allValues.push(getValue(props.dataA[i]) - getValue(props.dataB[i]))
    }
  }

  const yExtent = d3.extent(allValues)
  const yPad = (yExtent[1] - yExtent[0]) * 0.15 || 0.2

  const x = d3.scaleLinear().domain([1, maxRound]).range([0, width])
  const y = d3.scaleLinear()
    .domain([yExtent[0] - yPad, yExtent[1] + yPad])
    .range([height, 0])

  // Grid
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.08))')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8).attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => d.toFixed(1))

  // X-axis labels
  const step = Math.max(1, Math.floor(maxRound / 8))
  const xLabels = []
  for (let r = 1; r <= maxRound; r += step) xLabels.push(r)
  if (xLabels[xLabels.length - 1] !== maxRound) xLabels.push(maxRound)

  g.selectAll('.x-label')
    .data(xLabels)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d}`)

  const line = d3.line().curve(d3.curveMonotoneX)

  if (viewMode.value === 'difference') {
    const minLen = Math.min(props.dataA.length, props.dataB.length)
    const diffData = []
    for (let i = 0; i < minLen; i++) {
      diffData.push({ round: props.dataA[i].round, value: getValue(props.dataA[i]) - getValue(props.dataB[i]) })
    }

    // Zero line
    g.append('line')
      .attr('x1', 0).attr('x2', width)
      .attr('y1', y(0)).attr('y2', y(0))
      .attr('stroke', 'var(--color-text-muted, #888)')
      .attr('stroke-dasharray', '4,4')
      .attr('opacity', 0.5)

    const diffLine = line.x(d => x(d.round)).y(d => y(d.value))
    g.append('path')
      .datum(diffData)
      .attr('d', diffLine)
      .attr('fill', 'none')
      .attr('stroke', '#AA00FF')
      .attr('stroke-width', 2)
    return
  }

  // Sim A line
  if (viewMode.value !== 'b' && props.dataA.length) {
    const lineA = line.x(d => x(d.round)).y(d => y(getValue(d)))

    g.append('path')
      .datum(props.dataA)
      .attr('d', lineA)
      .attr('fill', 'none')
      .attr('stroke', '#2068FF')
      .attr('stroke-width', 2)
      .attr('opacity', viewMode.value === 'a' ? 1 : 0.9)
  }

  // Sim B line
  if (viewMode.value !== 'a' && props.dataB.length) {
    const lineB = line.x(d => x(d.round)).y(d => y(getValue(d)))

    g.append('path')
      .datum(props.dataB)
      .attr('d', lineB)
      .attr('fill', 'none')
      .attr('stroke', '#ff5600')
      .attr('stroke-width', 2)
      .attr('opacity', viewMode.value === 'b' ? 1 : 0.9)
  }

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

  const vertLine = g.append('line')
    .attr('y1', 0).attr('y2', height)
    .attr('stroke', 'var(--color-text-muted, #888)')
    .attr('stroke-dasharray', '3,3')
    .style('opacity', 0)

  // Invisible overlay for hover
  g.append('rect')
    .attr('width', width).attr('height', height)
    .attr('fill', 'transparent')
    .on('mousemove', (event) => {
      const [mx] = d3.pointer(event)
      const round = Math.round(x.invert(mx))
      const ptA = props.dataA.find(d => d.round === round)
      const ptB = props.dataB.find(d => d.round === round)
      if (!ptA && !ptB) return

      vertLine.attr('x1', x(round)).attr('x2', x(round)).style('opacity', 0.5)

      let html = `<div style="font-weight:600;color:var(--color-text);margin-bottom:4px">Round ${round}</div>`
      if (ptA && viewMode.value !== 'b') html += `<div style="color:#2068FF">${props.labelA}: ${getValue(ptA).toFixed(2)}</div>`
      if (ptB && viewMode.value !== 'a') html += `<div style="color:#ff5600">${props.labelB}: ${getValue(ptB).toFixed(2)}</div>`

      const rect = container.getBoundingClientRect()
      tooltip.html(html).style('opacity', 1)
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
      vertLine.style('opacity', 0)
    })
}

watch([() => props.dataA, () => props.dataB, () => props.metric, viewMode], () => {
  nextTick(renderChart)
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
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-[var(--color-text)] capitalize">{{ metric }} Over Time</h3>
      <div class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          v-for="mode in [
            { key: 'both', label: 'Both' },
            { key: 'a', label: 'A' },
            { key: 'b', label: 'B' },
            { key: 'difference', label: 'Diff' },
          ]"
          :key="mode.key"
          class="px-2 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === mode.key
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = mode.key"
        >
          {{ mode.label }}
        </button>
      </div>
    </div>

    <div v-if="dataA.length || dataB.length" ref="chartRef" class="relative" style="height: 248px" />
    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      No timeline data available
    </div>
  </div>
</template>
