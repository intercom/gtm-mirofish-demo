<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
const highlightedAgent = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Sentiment scoring (mirrors backend / SentimentTimeline) ---

const POSITIVE_WORDS = [
  'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
  'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
  'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
  'exciting', 'confident', 'strong', 'pleased', 'significant', 'positive',
]

const NEGATIVE_WORDS = [
  'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
  'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
  'problem', 'unclear', 'confusing', 'frustrated', 'poor', 'slow',
  'lacks', 'overpriced', 'clunky', 'limited', 'negative', 'afraid',
]

function scoreContent(content) {
  if (!content) return 0
  const lower = content.toLowerCase()
  let pos = 0, neg = 0
  for (const w of POSITIVE_WORDS) { if (lower.includes(w)) pos++ }
  for (const w of NEGATIVE_WORDS) { if (lower.includes(w)) neg++ }
  if (pos + neg === 0) return 0
  return (pos - neg) / (pos + neg)
}

function scoreAction(action) {
  const type = (action.action_type || '').toUpperCase()
  const cs = scoreContent(action.action_args?.content)
  if (type.includes('LIKE') || type.includes('UPVOTE')) return 0.3 + cs * 0.2
  if (type.includes('REPOST') || type.includes('RETWEET') || type.includes('SHARE')) return 0.2 + cs * 0.2
  if (type.includes('REPLY') || type.includes('COMMENT')) return cs * 0.8
  return cs * 0.6
}

// --- Agent color palette ---
const AGENT_COLORS = [
  '#2068FF', '#ff5600', '#009900', '#9333ea', '#0891b2',
  '#d946ef', '#ca8a04', '#dc2626', '#059669', '#6366f1',
  '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4',
]

// --- Compute per-agent sentiment data ---
const agentData = computed(() => {
  if (!props.actions.length) return { agents: [], rounds: [], series: {} }

  const agentMap = new Map()  // agentKey -> { id, name, rounds: Map<round, scores[]> }

  for (const action of props.actions) {
    const round = action.round_num
    if (round == null) continue
    const key = action.agent_name || `Agent #${action.agent_id}`
    if (!agentMap.has(key)) {
      agentMap.set(key, { id: action.agent_id, name: key, rounds: new Map() })
    }
    const agent = agentMap.get(key)
    if (!agent.rounds.has(round)) agent.rounds.set(round, [])
    agent.rounds.get(round).push(scoreAction(action))
  }

  const allRounds = [...new Set(props.actions.map(a => a.round_num).filter(r => r != null))].sort((a, b) => a - b)

  const agents = [...agentMap.entries()].map(([key, data], i) => ({
    key,
    id: data.id,
    name: key.split(',')[0]?.trim() || key,
    fullName: key,
    color: AGENT_COLORS[i % AGENT_COLORS.length],
  }))

  const series = {}
  for (const [key, data] of agentMap) {
    series[key] = allRounds
      .filter(r => data.rounds.has(r))
      .map(r => {
        const scores = data.rounds.get(r)
        const avg = scores.reduce((s, v) => s + v, 0) / scores.length
        return { round: r, sentiment: Math.max(-1, Math.min(1, avg)), actions: scores.length }
      })
  }

  return { agents, rounds: allRounds, series }
})

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return
  const { agents, rounds, series } = agentData.value
  if (!agents.length || !rounds.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 12, right: 16, bottom: 28, left: 36 }
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

  // Scales
  const x = d3.scaleLinear()
    .domain([rounds[0], rounds[rounds.length - 1]])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([-0.6, 0.6])
    .range([height, 0])
    .clamp(true)

  // Grid lines
  const gridValues = [-0.4, -0.2, 0, 0.2, 0.4]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', d => d === 0 ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(gridValues)
    .join('text')
    .attr('x', -6).attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', d => d > 0 ? '#009900' : d < 0 ? '#ff5600' : '#888')
    .text(d => d === 0 ? '0' : d > 0 ? `+${d.toFixed(1)}` : d.toFixed(1))

  // X-axis labels
  const step = Math.max(1, Math.floor(rounds.length / 8))
  g.selectAll('.x-label')
    .data(rounds.filter((_, i) => i % step === 0 || i === rounds.length - 1))
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d}`)

  // Zero line shading
  const zeroArea = d3.area()
    .x(d => x(d))
    .y0(y(0))
    .y1(y(0))
  g.append('path').datum(rounds).attr('d', zeroArea).attr('fill', 'none')

  // Line generator
  const line = d3.line()
    .x(d => x(d.round))
    .y(d => y(d.sentiment))
    .curve(d3.curveMonotoneX)

  // Draw one line per agent
  const highlighted = highlightedAgent.value
  const agentLines = g.selectAll('.agent-line')
    .data(agents)
    .join('path')
    .attr('class', 'agent-line')
    .attr('d', a => {
      const points = series[a.key]
      return points && points.length >= 2 ? line(points) : null
    })
    .attr('fill', 'none')
    .attr('stroke', a => a.color)
    .attr('stroke-width', a => highlighted === a.key ? 3 : 1.5)
    .attr('opacity', a => {
      if (!highlighted) return 0.7
      return highlighted === a.key ? 1 : 0.15
    })
    .style('cursor', 'pointer')
    .on('click', (event, a) => {
      highlightedAgent.value = highlightedAgent.value === a.key ? null : a.key
    })

  // Animate line drawing
  agentLines.each(function () {
    const path = d3.select(this)
    const len = this.getTotalLength()
    if (len > 0) {
      path
        .attr('stroke-dasharray', `${len} ${len}`)
        .attr('stroke-dashoffset', len)
        .transition().duration(800).ease(d3.easeCubicOut)
        .attr('stroke-dashoffset', 0)
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

  // Invisible hover columns per round
  const roundWidth = rounds.length > 1 ? width / (rounds.length - 1) : width
  g.selectAll('.hover-col')
    .data(rounds)
    .join('rect')
    .attr('x', d => x(d) - roundWidth / 2)
    .attr('y', 0)
    .attr('width', roundWidth)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'crosshair')
    .on('mouseenter', (event, roundNum) => {
      const agentEntries = agents
        .map(a => {
          const pt = series[a.key]?.find(p => p.round === roundNum)
          return pt ? { ...a, ...pt } : null
        })
        .filter(Boolean)
        .sort((a, b) => b.sentiment - a.sentiment)
        .slice(0, 5)

      if (!agentEntries.length) return

      const rows = agentEntries.map(e => {
        const sign = e.sentiment >= 0 ? '+' : ''
        return `<div style="display:flex;align-items:center;gap:6px;margin-top:3px">
          <span style="width:8px;height:8px;border-radius:50%;background:${e.color};flex-shrink:0"></span>
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${e.name}</span>
          <span style="font-weight:600;color:${e.sentiment > 0.1 ? '#009900' : e.sentiment < -0.1 ? '#ff5600' : '#888'}">${sign}${e.sentiment.toFixed(2)}</span>
        </div>`
      }).join('')

      tooltip.html(`
        <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${roundNum}</div>
        ${rows}
        ${agentEntries.length < agents.length ? `<div style="color:var(--color-text-muted,#888);font-size:11px;margin-top:4px">+ ${agents.length - agentEntries.length} more agents</div>` : ''}
      `).style('opacity', 1)

      // Vertical guide line
      g.selectAll('.guide-line').remove()
      g.append('line')
        .attr('class', 'guide-line')
        .attr('x1', x(roundNum)).attr('x2', x(roundNum))
        .attr('y1', 0).attr('y2', height)
        .attr('stroke', 'rgba(0,0,0,0.15)')
        .attr('stroke-dasharray', '3,3')
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
      g.selectAll('.guide-line').remove()
    })
}

// --- Lifecycle ---

watch([() => props.actions.length, highlightedAgent], () => {
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
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Agent Sentiment Timeline</h3>
      <button
        v-if="highlightedAgent"
        class="text-xs text-[var(--color-primary)] hover:underline"
        @click="highlightedAgent = null"
      >
        Show all
      </button>
    </div>

    <div v-if="agentData.agents.length" class="relative" ref="chartRef" style="height: 240px" />

    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Per-agent sentiment will appear as agents interact</span>
    </div>

    <!-- Agent legend (clickable) -->
    <div v-if="agentData.agents.length" class="flex flex-wrap gap-x-4 gap-y-1.5 mt-3">
      <button
        v-for="agent in agentData.agents.slice(0, 8)"
        :key="agent.key"
        class="flex items-center gap-1.5 text-xs transition-opacity"
        :class="highlightedAgent && highlightedAgent !== agent.key ? 'opacity-30' : 'opacity-100'"
        @click="highlightedAgent = highlightedAgent === agent.key ? null : agent.key"
      >
        <span
          class="inline-block w-2 h-2 rounded-full flex-shrink-0"
          :style="{ background: agent.color }"
        />
        <span class="text-[var(--color-text-muted)] truncate max-w-[120px]">{{ agent.name }}</span>
      </button>
      <span
        v-if="agentData.agents.length > 8"
        class="text-xs text-[var(--color-text-muted)]"
      >
        +{{ agentData.agents.length - 8 }} more
      </span>
    </div>
  </div>
</template>
