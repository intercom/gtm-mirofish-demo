<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  simulationId: { type: String, default: '' },
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
const sentimentData = ref(null)
const loading = ref(false)
const error = ref('')
const smoothed = ref(true)
const hiddenAgents = ref(new Set())
const selectedRound = ref(null)

let resizeObserver = null
let resizeTimer = null

// Fetch sentiment data from backend
async function fetchSentiment() {
  if (!props.simulationId) return
  loading.value = true
  error.value = ''
  try {
    const res = await simulationApi.getSentiment(props.simulationId)
    if (res.data?.success && res.data?.data) {
      sentimentData.value = res.data.data
    }
  } catch {
    error.value = 'Failed to load sentiment data'
  } finally {
    loading.value = false
  }
}

const hasData = computed(() =>
  sentimentData.value && sentimentData.value.agents?.length > 0,
)

const visibleAgents = computed(() => {
  if (!sentimentData.value) return []
  return sentimentData.value.agents.filter(a => !hiddenAgents.value.has(a.id))
})

const roundDetails = computed(() => {
  if (!selectedRound.value || !sentimentData.value) return null
  const round = selectedRound.value
  const agents = sentimentData.value.agents.map(a => {
    const point = a.scores.find(s => s.round === round)
    return { name: a.name, color: a.color, score: point?.smoothed ?? point?.raw ?? 0 }
  })
  const groupPt = sentimentData.value.group_average.find(g => g.round === round)
  const events = sentimentData.value.events.filter(e => e.round === round)
  return { round, agents, groupAvg: groupPt?.smoothed ?? 0, events }
})

function toggleAgent(agentId) {
  const next = new Set(hiddenAgents.value)
  if (next.has(agentId)) next.delete(agentId)
  else next.add(agentId)
  hiddenAgents.value = next
}

// --- D3 Rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !hasData.value) return

  const data = sentimentData.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 20, bottom: 32, left: 40 }
  const width = containerWidth - margin.left - margin.right
  const height = 240
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const defs = svg.append('defs')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const rounds = data.rounds
  const x = d3.scaleLinear()
    .domain([rounds[0], rounds[rounds.length - 1]])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([-0.7, 0.7])
    .range([height, 0])
    .clamp(true)

  // Grid lines
  const gridValues = [-0.4, -0.2, 0, 0.2, 0.4]
  g.selectAll('.grid-line')
    .data(gridValues)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', d => d === 0 ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.05)')
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '3,4')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(gridValues)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', d => {
      if (d > 0) return '#009900'
      if (d < 0) return '#ff5600'
      return '#888'
    })
    .text(d => {
      if (d === 0) return '0'
      return d > 0 ? `+${d.toFixed(1)}` : d.toFixed(1)
    })

  // X-axis labels
  const step = Math.max(1, Math.floor(rounds.length / 10))
  g.selectAll('.x-label')
    .data(rounds.filter((_, i) => i % step === 0 || i === rounds.length - 1))
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 22)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d}`)

  // Story arc reference line (dashed)
  if (data.story_arc?.length > 1) {
    const arcLine = d3.line()
      .x(d => x(d.round))
      .y(d => y(d.value))
      .curve(d3.curveBasis)

    g.append('path')
      .datum(data.story_arc)
      .attr('d', arcLine)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0,0,0,0.08)')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '6,4')
  }

  // Event annotations
  const eventColors = { conflict: '#ff5600', consensus: '#009900', swing: '#AA00FF' }
  const events = data.events || []

  events.forEach(evt => {
    const ex = x(evt.round)
    g.append('line')
      .attr('x1', ex).attr('x2', ex)
      .attr('y1', 0).attr('y2', height)
      .attr('stroke', eventColors[evt.type] || '#888')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3')
      .attr('opacity', 0.4)

    g.append('text')
      .attr('x', ex)
      .attr('y', -4)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', eventColors[evt.type] || '#888')
      .attr('font-weight', '500')
      .text(evt.label)
  })

  // Per-agent areas + lines
  const scoreKey = smoothed.value ? 'smoothed' : 'raw'

  visibleAgents.value.forEach((agent, idx) => {
    const gradientId = `agent-gradient-${idx}`
    const grad = defs.append('linearGradient')
      .attr('id', gradientId)
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', 0).attr('y2', 1)
    grad.append('stop').attr('offset', '0%')
      .attr('stop-color', agent.color).attr('stop-opacity', 0.15)
    grad.append('stop').attr('offset', '100%')
      .attr('stop-color', agent.color).attr('stop-opacity', 0.02)

    const area = d3.area()
      .x(d => x(d.round))
      .y0(y(0))
      .y1(d => y(d[scoreKey]))
      .curve(d3.curveMonotoneX)

    g.append('path')
      .datum(agent.scores)
      .attr('d', area)
      .attr('fill', `url(#${gradientId})`)
      .style('opacity', 0)
      .transition()
      .duration(600)
      .delay(idx * 80)
      .style('opacity', 1)

    const line = d3.line()
      .x(d => x(d.round))
      .y(d => y(d[scoreKey]))
      .curve(d3.curveMonotoneX)

    const path = g.append('path')
      .datum(agent.scores)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', agent.color)
      .attr('stroke-width', 1.8)
      .attr('opacity', 0.85)

    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .delay(idx * 80)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
  })

  // Group average (thick line)
  if (data.group_average?.length > 1) {
    const groupLine = d3.line()
      .x(d => x(d.round))
      .y(d => y(d[scoreKey]))
      .curve(d3.curveMonotoneX)

    const groupPath = g.append('path')
      .datum(data.group_average)
      .attr('d', groupLine)
      .attr('fill', 'none')
      .attr('stroke', '#050505')
      .attr('stroke-width', 2.5)
      .attr('opacity', 0.7)

    const groupLen = groupPath.node().getTotalLength()
    groupPath
      .attr('stroke-dasharray', `${groupLen} ${groupLen}`)
      .attr('stroke-dashoffset', groupLen)
      .transition()
      .duration(900)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
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
    .style('padding', '10px 14px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('max-width', '220px')

  // Hover indicator line
  const hoverLine = g.append('line')
    .attr('y1', 0).attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-width', 1)
    .style('opacity', 0)

  // Invisible hover targets per round
  const roundWidth = width / Math.max(1, rounds.length - 1)
  g.selectAll('.hover-target')
    .data(rounds)
    .join('rect')
    .attr('x', (d, i) => x(d) - roundWidth / 2)
    .attr('y', 0)
    .attr('width', roundWidth)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, round) => {
      hoverLine
        .attr('x1', x(round)).attr('x2', x(round))
        .style('opacity', 1)

      const groupPt = data.group_average.find(g => g.round === round)
      const agentLines = visibleAgents.value.map(a => {
        const pt = a.scores.find(s => s.round === round)
        const val = pt ? pt[scoreKey] : 0
        return `<div style="display:flex;align-items:center;gap:6px">
          <span style="width:8px;height:8px;border-radius:50%;background:${a.color};display:inline-block"></span>
          <span style="flex:1">${a.name}</span>
          <span style="font-weight:600;color:${val > 0.1 ? '#009900' : val < -0.1 ? '#ff5600' : '#888'}">${val >= 0 ? '+' : ''}${val.toFixed(2)}</span>
        </div>`
      }).join('')

      const evts = (data.events || []).filter(e => e.round === round)
      const evtHtml = evts.length
        ? `<div style="margin-top:4px;padding-top:4px;border-top:1px solid rgba(0,0,0,0.06);font-size:11px;color:${eventColors[evts[0].type] || '#888'}">${evts.map(e => e.label).join(', ')}</div>`
        : ''

      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:6px">Round ${round}</div>
          ${agentLines}
          <div style="margin-top:6px;padding-top:6px;border-top:1px solid rgba(0,0,0,0.06);display:flex;align-items:center;gap:6px">
            <span style="width:8px;height:3px;background:#050505;display:inline-block;border-radius:1px"></span>
            <span style="flex:1;font-weight:500">Group avg</span>
            <span style="font-weight:600">${groupPt ? (groupPt[scoreKey] >= 0 ? '+' : '') + groupPt[scoreKey].toFixed(2) : '—'}</span>
          </div>
          ${evtHtml}
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      const tooltipNode = tooltip.node()
      const tw = tooltipNode.offsetWidth
      let left = event.clientX - rect.left + 14
      if (left + tw > containerWidth - 10) left = event.clientX - rect.left - tw - 14
      tooltip
        .style('left', `${left}px`)
        .style('top', `${event.clientY - rect.top - 20}px`)
    })
    .on('mouseleave', () => {
      hoverLine.style('opacity', 0)
      tooltip.style('opacity', 0)
    })
    .on('click', (event, round) => {
      selectedRound.value = selectedRound.value === round ? null : round
    })
}

// --- Lifecycle ---

watch([() => props.simulationId], () => {
  fetchSentiment()
})

watch([() => props.actions.length], () => {
  if (props.simulationId) fetchSentiment()
})

watch([hasData, smoothed, visibleAgents], () => {
  nextTick(() => renderChart())
})

onMounted(() => {
  fetchSentiment()
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
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Sentiment Arc</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">Per-agent sentiment narrative over simulation rounds</p>
      </div>
      <div v-if="hasData" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="smoothed
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="smoothed = true"
        >Smoothed</button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="!smoothed
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="smoothed = false"
        >Raw</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      <span>Loading sentiment data...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error && !hasData" class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      <span>{{ error }}</span>
    </div>

    <!-- Chart -->
    <div v-else-if="hasData" class="relative" ref="chartRef" style="height: 288px" />

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      <span>Sentiment arc will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="hasData" class="flex flex-wrap items-center gap-3 mt-3">
      <!-- Agent toggles -->
      <button
        v-for="agent in sentimentData.agents"
        :key="agent.id"
        class="flex items-center gap-1.5 text-xs transition-opacity"
        :class="hiddenAgents.has(agent.id) ? 'opacity-30' : 'opacity-100'"
        @click="toggleAgent(agent.id)"
      >
        <span
          class="inline-block w-2.5 h-2.5 rounded-full"
          :style="{ background: agent.color }"
        />
        <span class="text-[var(--color-text-muted)]">{{ agent.name }}</span>
      </button>
      <!-- Group avg indicator -->
      <span class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] ml-auto">
        <span class="inline-block w-4 h-0.5 rounded bg-[#050505]" />
        Group avg
      </span>
      <!-- Story arc indicator -->
      <span class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
        <span class="inline-block w-4 h-0 border-t border-dashed border-[rgba(0,0,0,0.2)]" />
        Story arc
      </span>
    </div>

    <!-- Round detail panel -->
    <div
      v-if="roundDetails"
      class="mt-3 p-3 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-md"
    >
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-semibold text-[var(--color-text)]">
          Round {{ roundDetails.round }} Details
        </span>
        <button
          class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
          @click="selectedRound = null"
        >&times; Close</button>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div
          v-for="a in roundDetails.agents"
          :key="a.name"
          class="flex items-center gap-2 text-xs"
        >
          <span
            class="w-2 h-2 rounded-full shrink-0"
            :style="{ background: a.color }"
          />
          <span class="text-[var(--color-text-secondary)] truncate">{{ a.name }}</span>
          <span
            class="ml-auto font-semibold"
            :style="{ color: a.score > 0.1 ? '#009900' : a.score < -0.1 ? '#ff5600' : '#888' }"
          >{{ a.score >= 0 ? '+' : '' }}{{ a.score.toFixed(2) }}</span>
        </div>
      </div>
      <div v-if="roundDetails.events.length" class="mt-2 pt-2 border-t border-[var(--color-border)]">
        <span
          v-for="evt in roundDetails.events"
          :key="evt.label"
          class="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded mr-1"
          :style="{
            background: evt.type === 'conflict' ? 'rgba(255,86,0,0.1)' : evt.type === 'consensus' ? 'rgba(0,153,0,0.1)' : 'rgba(170,0,255,0.1)',
            color: evt.type === 'conflict' ? '#ff5600' : evt.type === 'consensus' ? '#009900' : '#AA00FF',
          }"
        >{{ evt.label }}</span>
      </div>
    </div>
  </div>
</template>
