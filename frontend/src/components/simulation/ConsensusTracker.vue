<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  simulationId: { type: String, default: '' },
  consensusData: { type: Object, default: null },
})

const chartRef = ref(null)
const barRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  navy: '#050505',
  lines: ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#e63946'],
}

const CONSENSUS_THRESHOLD = 75

const topics = computed(() => {
  if (!props.consensusData?.topics) return []
  return Object.values(props.consensusData.topics)
})

const summary = computed(() => props.consensusData?.summary || { resolved_count: 0, open_count: 0, total_topics: 0 })

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function clearBar() {
  if (barRef.value) d3.select(barRef.value).selectAll('*').remove()
}

function renderAll() {
  clearChart()
  clearBar()
  if (!topics.value.length) return
  nextTick(() => {
    renderLineChart()
    renderStatusBar()
  })
}

function renderLineChart() {
  const container = chartRef.value
  if (!container) return

  const data = topics.value
  if (!data.length || !data[0].rounds?.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 12, right: 120, bottom: 28, left: 40 }
  const width = containerWidth - margin.left - margin.right
  const height = 220
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Gather all rounds across topics
  const allRounds = data.flatMap(t => t.rounds.map(r => r.round))
  const roundExtent = d3.extent(allRounds)

  const x = d3.scaleLinear()
    .domain(roundExtent)
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([30, 100])
    .range([height, 0])
    .clamp(true)

  // Grid lines
  const gridValues = [40, 50, 60, 75, 80, 100]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', d => d === CONSENSUS_THRESHOLD ? 'rgba(0,153,0,0.25)' : 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', d => d === CONSENSUS_THRESHOLD ? '6,3' : '2,3')

  // Threshold label
  g.append('text')
    .attr('x', width + 4)
    .attr('y', y(CONSENSUS_THRESHOLD))
    .attr('dy', '0.35em')
    .attr('font-size', '9px')
    .attr('fill', '#009900')
    .text(`${CONSENSUS_THRESHOLD}% threshold`)

  // Y-axis labels
  g.selectAll('.y-label')
    .data([40, 60, 80, 100])
    .join('text')
    .attr('x', -6)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `${d}%`)

  // X-axis labels
  const xTicks = data[0].rounds.filter((_, i, arr) => {
    const step = Math.max(1, Math.floor(arr.length / 8))
    return i % step === 0 || i === arr.length - 1
  })
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round}`)

  // Draw lines per topic
  const line = d3.line()
    .x(d => x(d.round))
    .y(d => y(d.consensus))
    .curve(d3.curveMonotoneX)

  data.forEach((topic, i) => {
    const color = COLORS.lines[i % COLORS.lines.length]

    // Line path
    const path = g.append('path')
      .datum(topic.rounds)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2)
      .attr('opacity', 0.85)

    // Animate
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .delay(i * 120)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Consensus moment marker (where line first crosses threshold)
    if (topic.resolved && topic.resolved_at != null) {
      const resolvedRound = topic.rounds.find(r => r.round >= topic.resolved_at && r.consensus >= CONSENSUS_THRESHOLD)
      if (resolvedRound) {
        // Pulsing circle at consensus moment
        const cx = x(resolvedRound.round)
        const cy = y(resolvedRound.consensus)

        g.append('circle')
          .attr('cx', cx)
          .attr('cy', cy)
          .attr('r', 0)
          .attr('fill', color)
          .attr('opacity', 0.2)
          .transition()
          .delay(800 + i * 120)
          .duration(400)
          .attr('r', 10)
          .transition()
          .duration(600)
          .attr('r', 6)
          .attr('opacity', 0.15)

        g.append('circle')
          .attr('cx', cx)
          .attr('cy', cy)
          .attr('r', 0)
          .attr('fill', color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 2)
          .transition()
          .delay(800 + i * 120)
          .duration(300)
          .attr('r', 5)
      }
    }

    // End-of-line label
    const lastPoint = topic.rounds[topic.rounds.length - 1]
    if (lastPoint) {
      g.append('text')
        .attr('x', x(lastPoint.round) + 8)
        .attr('y', y(lastPoint.consensus))
        .attr('dy', '0.35em')
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .attr('fill', color)
        .style('opacity', 0)
        .text(topic.topic)
        .transition()
        .delay(800 + i * 120)
        .duration(300)
        .style('opacity', 1)
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
    .style('max-width', '220px')

  // Hover columns
  const allRoundsUnique = [...new Set(data[0].rounds.map(r => r.round))].sort((a, b) => a - b)

  g.selectAll('.hover-col')
    .data(allRoundsUnique)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(allRoundsUnique[i - 1]) : x(d)
      return (prev + x(d)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(allRoundsUnique[i - 1]) : x(d)
      const next = i < allRoundsUnique.length - 1 ? x(allRoundsUnique[i + 1]) : x(d)
      return ((x(d) - prev) + (next - x(d))) / 2
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, roundNum) => {
      let html = `<div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${roundNum}</div>`
      data.forEach((topic, i) => {
        const point = topic.rounds.find(r => r.round === roundNum)
        if (point) {
          const color = COLORS.lines[i % COLORS.lines.length]
          const icon = point.consensus >= CONSENSUS_THRESHOLD ? '●' : '○'
          html += `<div style="display:flex;justify-content:space-between;gap:12px;margin-top:2px">
            <span style="color:${color}">${icon} ${topic.topic}</span>
            <span style="font-weight:600;color:${color}">${point.consensus}%</span>
          </div>`
        }
      })
      tooltip.html(html).style('opacity', 1)
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

function renderStatusBar() {
  const container = barRef.value
  if (!container) return

  const resolved = summary.value.resolved_count
  const open = summary.value.open_count
  const total = resolved + open
  if (total === 0) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 4, right: 8, bottom: 4, left: 8 }
  const width = containerWidth - margin.left - margin.right
  const height = 28
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear().domain([0, total]).range([0, width])

  // Resolved portion
  g.append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', 0)
    .attr('height', height)
    .attr('rx', 4)
    .attr('fill', COLORS.green)
    .attr('opacity', 0.75)
    .transition()
    .duration(600)
    .ease(d3.easeCubicOut)
    .attr('width', x(resolved))

  // Open portion
  g.append('rect')
    .attr('x', x(resolved))
    .attr('y', 0)
    .attr('width', 0)
    .attr('height', height)
    .attr('rx', 4)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0.5)
    .transition()
    .duration(600)
    .delay(100)
    .ease(d3.easeCubicOut)
    .attr('width', x(open))

  // Labels inside bars
  if (resolved > 0) {
    g.append('text')
      .attr('x', x(resolved) / 2)
      .attr('y', height / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .style('opacity', 0)
      .text(`${resolved} resolved`)
      .transition()
      .delay(600)
      .duration(200)
      .style('opacity', 1)
  }

  if (open > 0) {
    g.append('text')
      .attr('x', x(resolved) + x(open) / 2)
      .attr('y', height / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .style('opacity', 0)
      .text(`${open} open`)
      .transition()
      .delay(700)
      .duration(200)
      .style('opacity', 1)
  }
}

// --- Lifecycle ---

watch(() => props.consensusData, () => {
  nextTick(() => renderAll())
}, { deep: true })

onMounted(() => {
  renderAll()
  const observe = (el) => {
    if (!el) return
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderAll, 200)
    })
    resizeObserver.observe(el)
  }
  observe(chartRef.value)
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
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Consensus Tracker</h3>
        <p class="text-[11px] text-[var(--color-text-muted)] mt-0.5">
          Group agreement per topic over simulation rounds
        </p>
      </div>
      <div v-if="summary.total_topics" class="flex items-center gap-3 text-xs">
        <span class="flex items-center gap-1.5 text-[#009900]">
          <span class="inline-block w-2 h-2 rounded-full bg-[#009900]" />
          {{ summary.resolved_count }} resolved
        </span>
        <span class="flex items-center gap-1.5 text-[#ff5600]">
          <span class="inline-block w-2 h-2 rounded-full bg-[#ff5600] opacity-60" />
          {{ summary.open_count }} open
        </span>
      </div>
    </div>

    <!-- Line chart -->
    <div v-if="topics.length" ref="chartRef" class="relative" style="height: 260px" />

    <div v-else class="flex items-center justify-center h-[220px] text-[var(--color-text-muted)] text-sm">
      <span>Consensus data will appear as agents interact</span>
    </div>

    <!-- Resolved / Open stacked bar -->
    <div v-if="summary.total_topics" class="mt-3">
      <div ref="barRef" class="w-full" style="height: 36px" />
    </div>

    <!-- Legend -->
    <div v-if="topics.length" class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs text-[var(--color-text-muted)]">
      <span
        v-for="(topic, i) in topics"
        :key="topic.topic"
        class="flex items-center gap-1.5"
      >
        <span
          class="inline-block w-3 h-0.5 rounded"
          :style="{ backgroundColor: COLORS.lines[i % COLORS.lines.length] }"
        />
        {{ topic.topic }}
        <span v-if="topic.resolved" class="text-[#009900]">●</span>
      </span>
    </div>
  </div>
</template>
