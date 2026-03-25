<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const gaugeRef = ref(null)
const sparklineRef = ref(null)
const showBreakdown = ref(false)
let resizeObserver = null
let resizeTimer = null

// --- Sentiment scoring (matches SentimentTimeline approach) ---

const POSITIVE_WORDS = [
  'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
  'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
  'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
]

const NEGATIVE_WORDS = [
  'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
  'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
  'problem', 'unclear', 'confusing', 'frustrated', 'poor', 'slow',
]

function scoreContent(content) {
  if (!content) return 0
  const lower = content.toLowerCase()
  let pos = 0
  let neg = 0
  for (const w of POSITIVE_WORDS) {
    if (lower.includes(w)) pos++
  }
  for (const w of NEGATIVE_WORDS) {
    if (lower.includes(w)) neg++
  }
  if (pos + neg === 0) return 0
  return (pos - neg) / (pos + neg)
}

function scoreAction(action) {
  const type = (action.action_type || '').toUpperCase()
  const contentScore = scoreContent(action.action_args?.content)
  if (type.includes('LIKE') || type.includes('UPVOTE')) return 0.3 + contentScore * 0.2
  if (type.includes('REPOST') || type.includes('SHARE')) return 0.2 + contentScore * 0.2
  if (type.includes('REPLY') || type.includes('COMMENT')) return contentScore * 0.8
  return contentScore * 0.6
}

// --- Polarization per round ---

const roundData = computed(() => {
  if (!props.actions.length) return []

  const roundMap = new Map()

  for (const action of props.actions) {
    const round = action.round_num
    if (round == null) continue
    if (!roundMap.has(round)) roundMap.set(round, [])
    roundMap.get(round).push({
      agent: action.agent_name || action.agent_id || 'unknown',
      score: scoreAction(action),
      content: action.action_args?.content || '',
      topic: action.action_args?.topic || action.action_args?.subject || '',
    })
  }

  const rounds = Array.from(roundMap.keys()).sort((a, b) => a - b)
  return rounds.map(round => {
    const entries = roundMap.get(round)
    const scores = entries.map(e => e.score)
    const mean = scores.reduce((s, v) => s + v, 0) / scores.length
    // Variance normalized to 0-1: std dev of scores in [-1,1] range, max possible ~1
    const variance = scores.reduce((s, v) => s + (v - mean) ** 2, 0) / scores.length
    const polarization = Math.min(1, Math.sqrt(variance) * 2)
    return { round, polarization, entries }
  })
})

const currentPolarization = computed(() => {
  if (!roundData.value.length) return 0
  return roundData.value[roundData.value.length - 1].polarization
})

const polarizationLabel = computed(() => {
  const p = currentPolarization.value
  if (p < 0.2) return 'Low polarization — group mostly agrees'
  if (p < 0.4) return 'Mild polarization — minor disagreements'
  if (p < 0.6) return 'Moderate polarization — noticeable division'
  if (p < 0.8) return 'High polarization — significant divide'
  return 'Extreme polarization — deeply divided'
})

// --- Breakdown: divisive topics + opposed agent pairs ---

const breakdown = computed(() => {
  if (!roundData.value.length) return { topics: [], pairs: [] }

  // Collect all entries from recent rounds (last 3)
  const recentRounds = roundData.value.slice(-3)
  const allEntries = recentRounds.flatMap(r => r.entries)

  // Divisive topics: topics with highest score variance
  const topicMap = new Map()
  for (const e of allEntries) {
    const topic = e.topic || 'General discussion'
    if (!topicMap.has(topic)) topicMap.set(topic, [])
    topicMap.get(topic).push(e.score)
  }

  const topics = Array.from(topicMap.entries())
    .filter(([, scores]) => scores.length >= 2)
    .map(([topic, scores]) => {
      const mean = scores.reduce((s, v) => s + v, 0) / scores.length
      const variance = scores.reduce((s, v) => s + (v - mean) ** 2, 0) / scores.length
      return { topic, divisiveness: Math.sqrt(variance), count: scores.length }
    })
    .sort((a, b) => b.divisiveness - a.divisiveness)
    .slice(0, 4)

  // Most opposed agent pairs
  const agentScores = new Map()
  for (const e of allEntries) {
    if (!agentScores.has(e.agent)) agentScores.set(e.agent, [])
    agentScores.get(e.agent).push(e.score)
  }

  const agents = Array.from(agentScores.entries()).map(([agent, scores]) => ({
    agent,
    avgScore: scores.reduce((s, v) => s + v, 0) / scores.length,
  }))

  const pairs = []
  for (let i = 0; i < agents.length; i++) {
    for (let j = i + 1; j < agents.length; j++) {
      pairs.push({
        agent1: agents[i].agent,
        agent2: agents[j].agent,
        opposition: Math.abs(agents[i].avgScore - agents[j].avgScore),
      })
    }
  }
  pairs.sort((a, b) => b.opposition - a.opposition)

  return { topics, pairs: pairs.slice(0, 4) }
})

// --- D3 gauge rendering ---

const GAUGE_COLORS = {
  consensus: '#009900',
  moderate: '#f59e0b',
  polarized: '#ff5600',
}

function clearGauge() {
  if (gaugeRef.value) d3.select(gaugeRef.value).selectAll('*').remove()
}

function clearSparkline() {
  if (sparklineRef.value) d3.select(sparklineRef.value).selectAll('*').remove()
}

function renderGauge() {
  clearGauge()
  const container = gaugeRef.value
  if (!container) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 260)
  const radius = size / 2
  const innerRadius = radius * 0.62
  const needleLength = radius * 0.78

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', radius + 24)
    .attr('viewBox', `0 0 ${containerWidth} ${radius + 24}`)

  const g = svg.append('g')
    .attr('transform', `translate(${containerWidth / 2},${radius + 4})`)

  // Background arc segments: green → yellow → red
  const arcGen = d3.arc().innerRadius(innerRadius).outerRadius(radius)

  const segments = [
    { start: -Math.PI / 2, end: -Math.PI / 6, color: GAUGE_COLORS.consensus },
    { start: -Math.PI / 6, end: Math.PI / 6, color: GAUGE_COLORS.moderate },
    { start: Math.PI / 6, end: Math.PI / 2, color: GAUGE_COLORS.polarized },
  ]

  // Gradient transitions between segments
  const gradientSteps = 60
  const totalAngle = Math.PI
  for (let i = 0; i < gradientSteps; i++) {
    const t = i / gradientSteps
    const startAngle = -Math.PI / 2 + t * totalAngle
    const endAngle = startAngle + totalAngle / gradientSteps + 0.005

    let color
    if (t < 0.33) {
      const localT = t / 0.33
      color = d3.interpolateRgb(GAUGE_COLORS.consensus, GAUGE_COLORS.moderate)(localT)
    } else if (t < 0.67) {
      const localT = (t - 0.33) / 0.34
      color = d3.interpolateRgb(GAUGE_COLORS.moderate, GAUGE_COLORS.polarized)(localT)
    } else {
      color = GAUGE_COLORS.polarized
    }

    g.append('path')
      .attr('d', arcGen({ startAngle, endAngle }))
      .attr('fill', color)
      .attr('opacity', 0.85)
  }

  // Inner arc background (subtle)
  const innerArc = d3.arc()
    .innerRadius(innerRadius - 2)
    .outerRadius(innerRadius)
  g.append('path')
    .attr('d', innerArc({ startAngle: -Math.PI / 2, endAngle: Math.PI / 2 }))
    .attr('fill', 'rgba(0,0,0,0.08)')

  // Tick marks
  const tickCount = 11
  for (let i = 0; i <= tickCount - 1; i++) {
    const t = i / (tickCount - 1)
    const angle = -Math.PI / 2 + t * Math.PI
    const isMajor = i % 5 === 0
    const tickInner = radius - (isMajor ? 12 : 6)
    const tickOuter = radius + 1

    g.append('line')
      .attr('x1', tickInner * Math.cos(angle))
      .attr('y1', tickInner * Math.sin(angle))
      .attr('x2', tickOuter * Math.cos(angle))
      .attr('y2', tickOuter * Math.sin(angle))
      .attr('stroke', isMajor ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.15)')
      .attr('stroke-width', isMajor ? 1.5 : 1)
  }

  // Scale labels
  const labels = [
    { value: '0', angle: -Math.PI / 2 },
    { value: '0.5', angle: 0 },
    { value: '1', angle: Math.PI / 2 },
  ]
  for (const label of labels) {
    const labelRadius = radius + 14
    g.append('text')
      .attr('x', labelRadius * Math.cos(label.angle))
      .attr('y', labelRadius * Math.sin(label.angle))
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#888')
      .text(label.value)
  }

  // Needle
  const needleAngle = -Math.PI / 2 + currentPolarization.value * Math.PI
  const needleGroup = g.append('g')

  // Needle shadow
  needleGroup.append('line')
    .attr('x1', 0).attr('y1', 0)
    .attr('x2', needleLength * Math.cos(needleAngle) + 1)
    .attr('y2', needleLength * Math.sin(needleAngle) + 1)
    .attr('stroke', 'rgba(0,0,0,0.1)')
    .attr('stroke-width', 3)
    .attr('stroke-linecap', 'round')

  // Needle line
  needleGroup.append('line')
    .attr('x1', 0).attr('y1', 0)
    .attr('x2', needleLength * Math.cos(needleAngle))
    .attr('y2', needleLength * Math.sin(needleAngle))
    .attr('stroke', '#050505')
    .attr('stroke-width', 2)
    .attr('stroke-linecap', 'round')
    .style('opacity', 0)
    .transition()
    .duration(800)
    .ease(d3.easeCubicOut)
    .style('opacity', 1)

  // Center pivot
  g.append('circle')
    .attr('cx', 0).attr('cy', 0)
    .attr('r', 5)
    .attr('fill', '#050505')

  g.append('circle')
    .attr('cx', 0).attr('cy', 0)
    .attr('r', 2.5)
    .attr('fill', '#fff')

  // Current value label inside gauge
  g.append('text')
    .attr('x', 0)
    .attr('y', -16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '22px')
    .attr('font-weight', '700')
    .attr('fill', currentPolarization.value < 0.4
      ? GAUGE_COLORS.consensus
      : currentPolarization.value < 0.7
        ? GAUGE_COLORS.moderate
        : GAUGE_COLORS.polarized)
    .text(currentPolarization.value.toFixed(2))
}

function renderSparkline() {
  clearSparkline()
  const container = sparklineRef.value
  if (!container || roundData.value.length < 2) return

  const data = roundData.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 4, right: 8, bottom: 18, left: 28 }
  const width = containerWidth - margin.left - margin.right
  const height = 48
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear()
    .domain([data[0].round, data[data.length - 1].round])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([0, 1])
    .range([height, 0])

  // Subtle grid
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', y(0.5)).attr('y2', y(0.5))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Area fill
  const area = d3.area()
    .x(d => x(d.round))
    .y0(height)
    .y1(d => y(d.polarization))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', area)
    .attr('fill', 'rgba(255, 86, 0, 0.08)')

  // Line
  const line = d3.line()
    .x(d => x(d.round))
    .y(d => y(d.polarization))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', '#ff5600')
    .attr('stroke-width', 1.5)
    .attr('stroke-linecap', 'round')

  // End dot
  const last = data[data.length - 1]
  g.append('circle')
    .attr('cx', x(last.round))
    .attr('cy', y(last.polarization))
    .attr('r', 3)
    .attr('fill', '#ff5600')

  // X-axis labels
  const labelData = data.length <= 6 ? data : [data[0], data[data.length - 1]]
  g.selectAll('.x-label')
    .data(labelData)
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', height + 14)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text(d => `R${d.round}`)

  // Y-axis labels
  g.selectAll('.y-label')
    .data([0, 0.5, 1])
    .join('text')
    .attr('x', -4)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text(d => d.toFixed(1))
}

function renderAll() {
  nextTick(() => {
    renderGauge()
    renderSparkline()
  })
}

// --- Lifecycle ---

watch(() => props.actions.length, renderAll)

onMounted(() => {
  renderAll()
  const el = gaugeRef.value?.parentElement
  if (el) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderAll, 200)
    })
    resizeObserver.observe(el)
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
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Polarization Index</h3>
      <button
        v-if="roundData.length"
        class="text-[11px] px-2 py-0.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
        @click="showBreakdown = !showBreakdown"
      >
        {{ showBreakdown ? 'Hide details' : 'View breakdown' }}
      </button>
    </div>

    <template v-if="roundData.length">
      <!-- Gauge -->
      <div ref="gaugeRef" class="flex justify-center" />

      <!-- Description -->
      <p class="text-xs text-center mt-2 text-[var(--color-text-muted)]">
        {{ polarizationLabel }}
      </p>

      <!-- Sparkline -->
      <div v-if="roundData.length >= 2" class="mt-4">
        <div class="text-[10px] text-[var(--color-text-muted)] mb-1">Trend over rounds</div>
        <div ref="sparklineRef" />
      </div>

      <!-- Breakdown panel -->
      <div
        v-if="showBreakdown"
        class="mt-4 pt-4 border-t border-[var(--color-border)] space-y-4"
      >
        <!-- Divisive topics -->
        <div v-if="breakdown.topics.length">
          <div class="text-[11px] font-medium text-[var(--color-text-secondary)] mb-2">
            Most Divisive Topics
          </div>
          <div class="space-y-1.5">
            <div
              v-for="topic in breakdown.topics"
              :key="topic.topic"
              class="flex items-center gap-2"
            >
              <div class="flex-1 min-w-0">
                <div class="text-xs text-[var(--color-text)] truncate">{{ topic.topic }}</div>
              </div>
              <div
                class="h-1.5 rounded-full"
                :style="{
                  width: `${Math.max(20, topic.divisiveness * 80)}px`,
                  backgroundColor: topic.divisiveness > 0.5 ? '#ff5600' : topic.divisiveness > 0.3 ? '#f59e0b' : '#009900',
                }"
              />
              <span class="text-[10px] text-[var(--color-text-muted)] w-8 text-right">
                {{ topic.divisiveness.toFixed(2) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Opposed agent pairs -->
        <div v-if="breakdown.pairs.length">
          <div class="text-[11px] font-medium text-[var(--color-text-secondary)] mb-2">
            Most Opposed Agent Pairs
          </div>
          <div class="space-y-1.5">
            <div
              v-for="pair in breakdown.pairs"
              :key="`${pair.agent1}-${pair.agent2}`"
              class="flex items-center gap-2 text-xs"
            >
              <span class="text-[var(--color-text)] truncate max-w-[80px]">{{ pair.agent1 }}</span>
              <span class="text-[var(--color-text-muted)]">vs</span>
              <span class="text-[var(--color-text)] truncate max-w-[80px]">{{ pair.agent2 }}</span>
              <span class="ml-auto text-[10px] text-[var(--color-fin-orange)]">
                {{ pair.opposition.toFixed(2) }}
              </span>
            </div>
          </div>
        </div>

        <div
          v-if="!breakdown.topics.length && !breakdown.pairs.length"
          class="text-xs text-[var(--color-text-muted)] text-center py-2"
        >
          Not enough data for breakdown analysis yet
        </div>
      </div>
    </template>

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[160px] text-[var(--color-text-muted)] text-sm">
      <span>Polarization data will appear as agents interact</span>
    </div>
  </div>
</template>
