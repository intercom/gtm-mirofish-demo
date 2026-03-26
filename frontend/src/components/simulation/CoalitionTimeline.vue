<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  evolution: { type: Array, default: () => [] },
  polarization: { type: Array, default: () => [] },
})

const chartRef = ref(null)
const viewMode = ref('alluvial') // 'alluvial' | 'polarization'
let resizeObserver = null
let resizeTimer = null

const COALITION_COLORS = [
  '#2068FF', '#ff5600', '#009900', '#9333ea', '#ea580c',
  '#0891b2', '#be185d', '#4f46e5', '#059669', '#d97706',
]

function getColor(coalitionId) {
  return COALITION_COLORS[coalitionId % COALITION_COLORS.length]
}

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  if (viewMode.value === 'polarization') {
    renderPolarization()
  } else {
    renderAlluvial()
  }
}

function renderAlluvial() {
  const container = chartRef.value
  if (!container || !props.evolution.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 20, bottom: 32, left: 40 }
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

  const data = props.evolution

  // Collect all coalition IDs across all rounds
  const allCoalitionIds = new Set()
  for (const evo of data) {
    for (const c of evo.coalitions) {
      allCoalitionIds.add(c.coalition_id)
    }
  }
  const coalitionIds = Array.from(allCoalitionIds).sort()

  // X scale: rounds
  const x = d3.scaleLinear()
    .domain([data[0].round_num, data[data.length - 1].round_num])
    .range([0, width])

  // For each round, compute stacked data (coalition sizes as fractions)
  const maxAgents = d3.max(data, d => d.coalitions.reduce((s, c) => s + c.size, 0)) || 1

  const y = d3.scaleLinear()
    .domain([0, maxAgents])
    .range([height, 0])

  // Build stack-like data
  const stackData = data.map(evo => {
    const entry = { round_num: evo.round_num }
    let cumulative = 0
    for (const cid of coalitionIds) {
      const coalition = evo.coalitions.find(c => c.coalition_id === cid)
      const size = coalition ? coalition.size : 0
      entry[`c${cid}`] = size
      entry[`c${cid}_label`] = coalition?.label || ''
      cumulative += size
    }
    return entry
  })

  // D3 stack
  const keys = coalitionIds.map(id => `c${id}`)
  const stack = d3.stack()
    .keys(keys)
    .order(d3.stackOrderNone)
    .offset(d3.stackOffsetWiggle)

  const series = stack(stackData)

  // Adjust y domain for wiggle offset
  const yMin = d3.min(series, s => d3.min(s, d => d[0]))
  const yMax = d3.max(series, s => d3.max(s, d => d[1]))
  y.domain([yMin, yMax])

  const area = d3.area()
    .x(d => x(d.data.round_num))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(d3.curveBasis)

  // Render streams
  g.selectAll('.stream')
    .data(series)
    .join('path')
    .attr('d', area)
    .attr('fill', (d, i) => getColor(coalitionIds[i]))
    .attr('fill-opacity', 0.6)
    .attr('stroke', (d, i) => getColor(coalitionIds[i]))
    .attr('stroke-width', 0.5)
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((_, i) => i * 80)
    .style('opacity', 1)

  // X-axis labels
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round_num))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round_num}`)

  // Y-axis label
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -height / 2)
    .attr('y', -30)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text('Coalition Size')

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

  // Overlay for tooltip interaction
  g.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .on('mousemove', (event) => {
      const [mx] = d3.pointer(event)
      const roundNum = Math.round(x.invert(mx))
      const evo = data.find(d => d.round_num === roundNum)
      if (!evo) return

      const lines = evo.coalitions.map(c =>
        `<div style="display:flex;align-items:center;gap:6px;margin-top:2px">
          <span style="width:8px;height:8px;border-radius:50%;background:${getColor(c.coalition_id)}"></span>
          <span style="color:var(--color-text-secondary,#666)">${c.label || 'Coalition ' + c.coalition_id}: ${c.size} agents</span>
        </div>`
      ).join('')

      tooltip.html(`
        <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${roundNum}</div>
        ${lines}
        <div style="color:var(--color-text-muted,#888);margin-top:4px;font-size:11px">
          Polarization: ${(evo.polarization_index * 100).toFixed(0)}%
        </div>
      `).style('opacity', 1)

      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => tooltip.style('opacity', 0))
}

function renderPolarization() {
  const container = chartRef.value
  if (!container || !props.polarization.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 20, bottom: 32, left: 40 }
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

  const data = props.polarization

  const x = d3.scaleLinear()
    .domain([data[0].round_num, data[data.length - 1].round_num])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([0, 1])
    .range([height, 0])

  // Grid lines
  const gridValues = [0, 0.25, 0.5, 0.75, 1.0]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data([0, 0.5, 1.0])
    .join('text')
    .attr('x', -6).attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `${(d * 100).toFixed(0)}%`)

  // X-axis labels
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round_num))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round_num}`)

  // Danger zone
  g.append('rect')
    .attr('x', 0).attr('y', y(1))
    .attr('width', width).attr('height', y(0.7) - y(1))
    .attr('fill', 'rgba(255, 86, 0, 0.05)')

  g.append('text')
    .attr('x', width - 4).attr('y', y(0.85))
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', '#ff5600')
    .attr('opacity', 0.6)
    .text('High polarization')

  // Area under curve
  const area = d3.area()
    .x(d => x(d.round_num))
    .y0(y(0))
    .y1(d => y(d.polarization_index))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', area)
    .attr('fill', 'rgba(32, 104, 255, 0.08)')

  // Line
  const line = d3.line()
    .x(d => x(d.round_num))
    .y(d => y(d.polarization_index))
    .curve(d3.curveMonotoneX)

  const path = g.append('path')
    .datum(data)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', '#2068FF')
    .attr('stroke-width', 2.5)

  const totalLength = path.node().getTotalLength()
  path
    .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
    .attr('stroke-dashoffset', totalLength)
    .transition().duration(800).ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)

  // Dots
  g.selectAll('.dot')
    .data(data)
    .join('circle')
    .attr('cx', d => x(d.round_num))
    .attr('cy', d => y(d.polarization_index))
    .attr('r', 0)
    .attr('fill', d => d.polarization_index > 0.7 ? '#ff5600' : '#2068FF')
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .transition().duration(300).delay((_, i) => 800 + i * 40)
    .attr('r', 4)
}

const hasData = computed(() => {
  if (viewMode.value === 'polarization') return props.polarization.length > 0
  return props.evolution.length > 0
})

watch([() => props.evolution, () => props.polarization, viewMode], () => {
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
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Coalition Evolution</h3>
      <div class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'alluvial'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'alluvial'"
        >
          Stream
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'polarization'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'polarization'"
        >
          Polarization
        </button>
      </div>
    </div>

    <div v-if="hasData" ref="chartRef" class="relative" style="height: 248px" />

    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Evolution data will appear as the simulation progresses</span>
    </div>
  </div>
</template>
