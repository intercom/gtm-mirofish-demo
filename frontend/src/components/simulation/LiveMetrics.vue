<script setup>
import { ref, computed, watch, inject, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const polling = inject('polling')

const sentimentRef = ref(null)
const volumeRef = ref(null)
const gaugeRef = ref(null)
const spreadRef = ref(null)

let observers = []
let resizeTimer = null

// --- Sentiment scoring (consistent with SentimentTimeline) ---

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

function scoreSentiment(content) {
  if (!content) return 0
  const lower = content.toLowerCase()
  let pos = 0, neg = 0
  for (const w of POSITIVE_WORDS) { if (lower.includes(w)) pos++ }
  for (const w of NEGATIVE_WORDS) { if (lower.includes(w)) neg++ }
  if (pos + neg === 0) return 0
  return (pos - neg) / (pos + neg)
}

// --- Live status ---

const isLive = computed(() => {
  const rs = polling.runStatus.value?.runner_status
  return rs === 'running' || rs === 'starting'
})

// --- Derived data: Sentiment by agent per round ---

const AGENT_COLORS = ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#f59e0b']

const sentimentData = computed(() => {
  const actions = polling.recentActions.value
  if (!actions.length) return { agents: [], rounds: [] }

  const agentMap = new Map()
  for (const a of actions) {
    const name = a.agent_name?.split(',')[0]?.trim() || `Agent #${a.agent_id}`
    if (!agentMap.has(name)) agentMap.set(name, [])
    agentMap.get(name).push(a)
  }

  // Top 5 most active agents
  const topAgents = [...agentMap.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 5)
    .map(([name]) => name)

  // Group by round per agent
  const allRounds = new Set()
  const agentSeries = topAgents.map((name, i) => {
    const agentActions = agentMap.get(name)
    const byRound = new Map()
    for (const a of agentActions) {
      const r = a.round_num
      if (r == null) continue
      allRounds.add(r)
      if (!byRound.has(r)) byRound.set(r, [])
      byRound.get(r).push(scoreSentiment(a.action_args?.content))
    }
    const points = [...byRound.entries()]
      .sort(([a], [b]) => a - b)
      .map(([round, scores]) => ({
        round,
        score: scores.reduce((s, v) => s + v, 0) / scores.length,
      }))
    return { name, color: AGENT_COLORS[i], points }
  })

  const rounds = [...allRounds].sort((a, b) => a - b)
  return { agents: agentSeries, rounds }
})

// --- Derived data: Interaction volume per round ---

const volumeData = computed(() => {
  const tl = polling.timeline.value
  if (!tl.length) return []
  return tl.map(d => ({
    round: d.round_num,
    twitter: d.twitter_actions || 0,
    reddit: d.reddit_actions || 0,
  }))
})

// --- Derived data: Consensus gauge ---

const consensusScore = computed(() => {
  const actions = polling.recentActions.value
  if (actions.length < 2) return 0

  // Get scores per unique agent for the latest 3 rounds
  const currentRound = polling.runStatus.value?.current_round || 0
  const minRound = Math.max(1, currentRound - 2)
  const recent = actions.filter(a => a.round_num >= minRound)

  const agentScores = new Map()
  for (const a of recent) {
    const name = a.agent_name || a.agent_id
    const score = scoreSentiment(a.action_args?.content)
    if (!agentScores.has(name)) agentScores.set(name, [])
    agentScores.get(name).push(score)
  }

  const avgScores = [...agentScores.values()].map(
    scores => scores.reduce((s, v) => s + v, 0) / scores.length
  )

  if (avgScores.length < 2) return 0.5

  const mean = avgScores.reduce((s, v) => s + v, 0) / avgScores.length
  const variance = avgScores.reduce((s, v) => s + (v - mean) ** 2, 0) / avgScores.length
  const std = Math.sqrt(variance)

  // Map std to consensus: std=0 -> 100%, std>=1 -> 0%
  return Math.max(0, Math.min(1, 1 - std))
})

// --- Derived data: Information spread network ---

const spreadData = computed(() => {
  const actions = polling.recentActions.value
  if (!actions.length) return { nodes: [], links: [] }

  // Build agent nodes
  const agentCounts = new Map()
  for (const a of actions) {
    const name = a.agent_name?.split(',')[0]?.trim() || `Agent #${a.agent_id}`
    agentCounts.set(name, (agentCounts.get(name) || 0) + 1)
  }

  // Top 10 agents
  const topAgents = [...agentCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  const agentNames = new Set(topAgents.map(([n]) => n))
  const nodes = topAgents.map(([name, count]) => ({ id: name, count }))

  // Build links from co-occurrence in same round
  const roundAgents = new Map()
  for (const a of actions) {
    const name = a.agent_name?.split(',')[0]?.trim() || `Agent #${a.agent_id}`
    if (!agentNames.has(name)) continue
    const r = a.round_num
    if (r == null) continue
    if (!roundAgents.has(r)) roundAgents.set(r, new Set())
    roundAgents.get(r).add(name)
  }

  const linkMap = new Map()
  for (const agents of roundAgents.values()) {
    const arr = [...agents]
    for (let i = 0; i < arr.length; i++) {
      for (let j = i + 1; j < arr.length; j++) {
        const key = [arr[i], arr[j]].sort().join('|')
        linkMap.set(key, (linkMap.get(key) || 0) + 1)
      }
    }
  }

  const links = [...linkMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([key, weight]) => {
      const [source, target] = key.split('|')
      return { source, target, weight }
    })

  return { nodes, links }
})

// --- Chart rendering ---

function clearEl(el) {
  if (el) d3.select(el).selectAll('*').remove()
}

function renderSentiment() {
  const el = sentimentRef.value
  if (!el) return
  clearEl(el)

  const { agents, rounds } = sentimentData.value
  if (!agents.length || !rounds.length) return

  const w = el.clientWidth
  if (w === 0) return
  const margin = { top: 8, right: 12, bottom: 24, left: 32 }
  const width = w - margin.left - margin.right
  const height = 140

  const svg = d3.select(el).append('svg')
    .attr('width', w)
    .attr('height', height + margin.top + margin.bottom)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear()
    .domain(d3.extent(rounds))
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([-0.6, 0.6])
    .range([height, 0])
    .clamp(true)

  // Zero line
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', y(0)).attr('y2', y(0))
    .attr('stroke', 'rgba(0,0,0,0.12)')
    .attr('stroke-dasharray', '3,3')

  // Grid
  for (const v of [-0.3, 0.3]) {
    g.append('line')
      .attr('x1', 0).attr('x2', width)
      .attr('y1', y(v)).attr('y2', y(v))
      .attr('stroke', 'rgba(0,0,0,0.05)')
      .attr('stroke-dasharray', '2,4')
  }

  // Y labels
  g.selectAll('.y-label')
    .data([-0.3, 0, 0.3])
    .join('text')
    .attr('x', -4).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end').attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => d === 0 ? '0' : d > 0 ? `+${d.toFixed(1)}` : d.toFixed(1))

  // X labels
  const step = Math.max(1, Math.floor(rounds.length / 5))
  g.selectAll('.x-label')
    .data(rounds.filter((_, i) => i % step === 0))
    .join('text')
    .attr('x', d => x(d)).attr('y', height + 16)
    .attr('text-anchor', 'middle').attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d}`)

  // Lines per agent
  const line = d3.line()
    .x(d => x(d.round))
    .y(d => y(d.score))
    .curve(d3.curveMonotoneX)

  for (const agent of agents) {
    if (agent.points.length < 2) continue
    const path = g.append('path')
      .datum(agent.points)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', agent.color)
      .attr('stroke-width', 1.5)
      .attr('opacity', 0.8)

    // Animate
    const totalLen = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLen} ${totalLen}`)
      .attr('stroke-dashoffset', totalLen)
      .transition().duration(600).ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
  }
}

function renderVolume() {
  const el = volumeRef.value
  if (!el) return
  clearEl(el)

  const data = volumeData.value
  if (!data.length) return

  const w = el.clientWidth
  if (w === 0) return
  const margin = { top: 8, right: 12, bottom: 24, left: 32 }
  const width = w - margin.left - margin.right
  const height = 140

  const svg = d3.select(el).append('svg')
    .attr('width', w)
    .attr('height', height + margin.top + margin.bottom)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(data, d => d.twitter + d.reddit) || 1

  const x = d3.scaleBand()
    .domain(data.map(d => d.round))
    .range([0, width])
    .padding(0.3)

  const y = d3.scaleLinear()
    .domain([0, maxVal])
    .range([height, 0])
    .nice()

  // Grid
  const ticks = y.ticks(4)
  g.selectAll('.grid')
    .data(ticks)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')

  // Y labels
  g.selectAll('.y-label')
    .data(ticks)
    .join('text')
    .attr('x', -4).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end').attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => d)

  // X labels
  const xStep = Math.max(1, Math.floor(data.length / 6))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % xStep === 0))
    .join('text')
    .attr('x', d => x(d.round) + x.bandwidth() / 2)
    .attr('y', height + 16)
    .attr('text-anchor', 'middle').attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d.round}`)

  // Twitter bars (bottom)
  g.selectAll('.bar-twitter')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.round))
    .attr('width', x.bandwidth())
    .attr('y', height)
    .attr('height', 0)
    .attr('fill', '#2068FF')
    .attr('rx', 1)
    .transition().duration(500).delay((_, i) => i * 15)
    .attr('y', d => y(d.twitter + d.reddit))
    .attr('height', d => height - y(d.twitter))

  // Reddit bars (stacked on top)
  g.selectAll('.bar-reddit')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.round))
    .attr('width', x.bandwidth())
    .attr('y', height)
    .attr('height', 0)
    .attr('fill', '#ff5600')
    .attr('rx', 1)
    .transition().duration(500).delay((_, i) => i * 15)
    .attr('y', d => y(d.twitter + d.reddit))
    .attr('height', d => height - y(d.reddit))
}

function renderGauge() {
  const el = gaugeRef.value
  if (!el) return
  clearEl(el)

  const w = el.clientWidth
  if (w === 0) return
  const size = Math.min(w, 160)
  const cx = w / 2
  const cy = size / 2 + 10
  const radius = size / 2 - 16
  const thickness = 12

  const svg = d3.select(el).append('svg')
    .attr('width', w)
    .attr('height', size + 20)

  // Background arc (full semicircle)
  const bgArc = d3.arc()
    .innerRadius(radius - thickness)
    .outerRadius(radius)
    .startAngle(-Math.PI / 2)
    .endAngle(Math.PI / 2)
    .cornerRadius(thickness / 2)

  svg.append('path')
    .attr('transform', `translate(${cx},${cy})`)
    .attr('d', bgArc)
    .attr('fill', 'rgba(0,0,0,0.06)')

  // Value arc
  const score = consensusScore.value
  const endAngle = -Math.PI / 2 + Math.PI * score

  const valueArc = d3.arc()
    .innerRadius(radius - thickness)
    .outerRadius(radius)
    .startAngle(-Math.PI / 2)
    .cornerRadius(thickness / 2)

  const color = score > 0.7 ? '#009900' : score > 0.4 ? '#f59e0b' : '#ff5600'

  const valuePath = svg.append('path')
    .attr('transform', `translate(${cx},${cy})`)
    .attr('fill', color)

  // Animate the arc
  valuePath
    .transition().duration(800).ease(d3.easeCubicOut)
    .attrTween('d', () => {
      const interp = d3.interpolate(-Math.PI / 2, endAngle)
      return t => valueArc.endAngle(interp(t))()
    })

  // Percentage text
  svg.append('text')
    .attr('x', cx).attr('y', cy - 4)
    .attr('text-anchor', 'middle')
    .attr('font-size', '22px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text, #050505)')
    .text(`${Math.round(score * 100)}%`)

  // Label
  svg.append('text')
    .attr('x', cx).attr('y', cy + 14)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text('agreement')
}

let simulation = null

function renderSpread() {
  const el = spreadRef.value
  if (!el) return
  clearEl(el)

  const { nodes, links } = spreadData.value
  if (!nodes.length) return

  const w = el.clientWidth
  if (w === 0) return
  const height = 160

  const svg = d3.select(el).append('svg')
    .attr('width', w)
    .attr('height', height)

  const maxCount = d3.max(nodes, d => d.count) || 1
  const rScale = d3.scaleSqrt().domain([1, maxCount]).range([4, 12])

  // Build force simulation
  const simNodes = nodes.map(d => ({ ...d }))
  const simLinks = links.map(d => ({ ...d }))

  if (simulation) simulation.stop()

  simulation = d3.forceSimulation(simNodes)
    .force('link', d3.forceLink(simLinks).id(d => d.id).distance(40).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-60))
    .force('center', d3.forceCenter(w / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => rScale(d.count) + 2))

  const linkEls = svg.append('g')
    .selectAll('line')
    .data(simLinks)
    .join('line')
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
    .attr('stroke-width', d => Math.min(3, d.weight * 0.5))
    .attr('opacity', 0.5)

  const nodeEls = svg.append('g')
    .selectAll('circle')
    .data(simNodes)
    .join('circle')
    .attr('r', d => rScale(d.count))
    .attr('fill', (_, i) => AGENT_COLORS[i % AGENT_COLORS.length])
    .attr('stroke', 'var(--color-surface, #fff)')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.85)

  // Labels for top 3
  const labelEls = svg.append('g')
    .selectAll('text')
    .data(simNodes.slice(0, 3))
    .join('text')
    .attr('font-size', '8px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .attr('text-anchor', 'middle')
    .attr('dy', d => rScale(d.count) + 10)
    .text(d => d.id.split(' ')[0])

  simulation.on('tick', () => {
    linkEls
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeEls
      .attr('cx', d => Math.max(14, Math.min(w - 14, d.x)))
      .attr('cy', d => Math.max(14, Math.min(height - 14, d.y)))

    labelEls
      .attr('x', d => Math.max(14, Math.min(w - 14, d.x)))
      .attr('y', d => Math.max(14, Math.min(height - 14, d.y)))
  })

  // Cool down faster for mini chart
  simulation.alpha(0.8).alphaDecay(0.05)
}

function renderAll() {
  nextTick(() => {
    renderSentiment()
    renderVolume()
    renderGauge()
    renderSpread()
  })
}

function debouncedRender() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(renderAll, 200)
}

watch(
  [
    () => polling.recentActions.value.length,
    () => polling.timeline.value.length,
    () => polling.runStatus.value?.current_round,
  ],
  () => nextTick(renderAll),
)

onMounted(() => {
  renderAll()
  for (const el of [sentimentRef, volumeRef, gaugeRef, spreadRef]) {
    if (el.value) {
      const obs = new ResizeObserver(debouncedRender)
      obs.observe(el.value)
      observers.push(obs)
    }
  }
})

onUnmounted(() => {
  for (const obs of observers) obs.disconnect()
  observers = []
  clearTimeout(resizeTimer)
  if (simulation) { simulation.stop(); simulation = null }
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Live Metrics</h3>
      <span
        v-if="isLive"
        class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/10 text-red-500"
      >
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
        </span>
        LIVE
      </span>
    </div>

    <!-- Empty state -->
    <div
      v-if="!polling.recentActions.value.length && !polling.timeline.value.length"
      class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm"
    >
      Live metrics will appear as agents interact
    </div>

    <!-- 2x2 chart grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Sentiment Trend -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-medium text-[var(--color-text-secondary)]">Sentiment Trend</span>
          <div class="flex items-center gap-2">
            <span
              v-for="(agent, i) in sentimentData.agents.slice(0, 3)"
              :key="agent.name"
              class="flex items-center gap-1 text-[9px] text-[var(--color-text-muted)]"
            >
              <span class="inline-block w-2 h-0.5 rounded" :style="{ background: agent.color }" />
              {{ agent.name.split(' ')[0] }}
            </span>
          </div>
        </div>
        <div ref="sentimentRef" class="w-full" style="height: 172px" />
      </div>

      <!-- Interaction Volume -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-medium text-[var(--color-text-secondary)]">Interaction Volume</span>
          <div class="flex items-center gap-2 text-[9px] text-[var(--color-text-muted)]">
            <span class="flex items-center gap-1">
              <span class="inline-block w-2 h-2 rounded-sm bg-[#2068FF]" /> Twitter
            </span>
            <span class="flex items-center gap-1">
              <span class="inline-block w-2 h-2 rounded-sm bg-[#ff5600]" /> Reddit
            </span>
          </div>
        </div>
        <div ref="volumeRef" class="w-full" style="height: 172px" />
      </div>

      <!-- Consensus Gauge -->
      <div>
        <div class="mb-2">
          <span class="text-xs font-medium text-[var(--color-text-secondary)]">Consensus Level</span>
        </div>
        <div ref="gaugeRef" class="w-full flex items-center justify-center" style="height: 172px" />
      </div>

      <!-- Information Spread -->
      <div>
        <div class="mb-2">
          <span class="text-xs font-medium text-[var(--color-text-secondary)]">Information Spread</span>
        </div>
        <div ref="spreadRef" class="w-full" style="height: 172px" />
      </div>
    </div>
  </div>
</template>
