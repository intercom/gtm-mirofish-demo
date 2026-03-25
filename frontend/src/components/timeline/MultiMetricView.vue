<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
  timeline: { type: Array, default: () => [] },
})

const ROWS = [
  { key: 'sentiment', label: 'Sentiment', color: '#2068FF' },
  { key: 'volume', label: 'Volume', color: '#ff5600' },
  { key: 'consensus', label: 'Consensus', color: '#AA00FF' },
]

const VOLUME_CATS = [
  { key: 'posts', color: '#2068FF', label: 'Posts' },
  { key: 'replies', color: '#ff5600', label: 'Replies' },
  { key: 'likes', color: '#AA00FF', label: 'Likes' },
  { key: 'reposts', color: '#009900', label: 'Reposts' },
]

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

// --- State ---
const viewMode = ref('expanded')
const visibleRows = ref(new Set(['sentiment', 'volume', 'consensus']))
const crosshairX = ref(null)
const activeRound = ref(null)

const containerRef = ref(null)
const sentimentRef = ref(null)
const volumeRef = ref(null)
const consensusRef = ref(null)

let resizeObserver = null
let resizeTimer = null
let xScale = null

const MARGIN = { top: 8, right: 16, bottom: 24, left: 44 }
const MARGIN_COMPACT = { top: 4, right: 16, bottom: 4, left: 44 }
const EXPANDED_H = 140
const COMPACT_H = 40

// --- Sentiment scoring (matches SentimentTimeline.vue) ---
function scoreContent(content) {
  if (!content) return 0
  const lower = content.toLowerCase()
  let pos = 0, neg = 0
  for (const w of POSITIVE_WORDS) if (lower.includes(w)) pos++
  for (const w of NEGATIVE_WORDS) if (lower.includes(w)) neg++
  return pos + neg === 0 ? 0 : (pos - neg) / (pos + neg)
}

function scoreAction(action) {
  const type = (action.action_type || '').toUpperCase()
  const cs = scoreContent(action.action_args?.content)
  if (type.includes('LIKE') || type.includes('UPVOTE')) return 0.3 + cs * 0.2
  if (type.includes('REPOST') || type.includes('RETWEET') || type.includes('SHARE')) return 0.2 + cs * 0.2
  if (type.includes('REPLY') || type.includes('COMMENT')) return cs * 0.8
  return cs * 0.6
}

// --- Computed data ---
const roundData = computed(() => {
  if (!props.actions.length) return []
  const map = new Map()

  for (const action of props.actions) {
    const round = action.round_num
    if (round == null) continue
    if (!map.has(round)) map.set(round, { scores: [], agents: new Map(), posts: 0, replies: 0, likes: 0, reposts: 0 })
    const entry = map.get(round)
    const score = scoreAction(action)
    entry.scores.push(score)

    const agentKey = action.agent_name || action.agent_id
    if (!entry.agents.has(agentKey)) entry.agents.set(agentKey, [])
    entry.agents.get(agentKey).push(score)

    const t = (action.action_type || '').toUpperCase()
    if (t.includes('POST') || t.includes('CREATE') || t.includes('THREAD')) entry.posts++
    else if (t.includes('REPLY') || t.includes('COMMENT')) entry.replies++
    else if (t.includes('LIKE') || t.includes('UPVOTE')) entry.likes++
    else entry.reposts++
  }

  return Array.from(map.keys()).sort((a, b) => a - b).map(round => {
    const e = map.get(round)
    const avg = e.scores.reduce((s, v) => s + v, 0) / e.scores.length

    // Consensus = 1 - stddev of per-agent sentiment averages
    const agentAvgs = Array.from(e.agents.values()).map(s => s.reduce((a, v) => a + v, 0) / s.length)
    const mean = agentAvgs.reduce((s, v) => s + v, 0) / (agentAvgs.length || 1)
    const variance = agentAvgs.reduce((s, v) => s + (v - mean) ** 2, 0) / (agentAvgs.length || 1)

    return {
      round,
      sentiment: Math.max(-1, Math.min(1, avg)),
      volume: e.scores.length,
      posts: e.posts,
      replies: e.replies,
      likes: e.likes,
      reposts: e.reposts,
      consensus: Math.max(0, Math.min(1, 1 - Math.sqrt(variance))),
      agentCount: e.agents.size,
    }
  })
})

const hasData = computed(() => roundData.value.length > 0)

const lastVisibleRow = computed(() => {
  for (const key of ['consensus', 'volume', 'sentiment']) {
    if (visibleRows.value.has(key)) return key
  }
  return null
})

// --- Row toggle ---
function toggleRow(key) {
  const s = new Set(visibleRows.value)
  if (s.has(key)) { if (s.size > 1) s.delete(key) }
  else s.add(key)
  visibleRows.value = s
}

// --- Crosshair ---
function onMouseMove(event) {
  if (!xScale || !containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const chartX = event.clientX - rect.left - MARGIN.left
  const data = roundData.value
  if (!data.length || chartX < 0 || chartX > xScale.range()[1]) {
    crosshairX.value = null
    activeRound.value = null
    return
  }
  const xVal = xScale.invert(chartX)
  let closest = data[0], minDist = Infinity
  for (const d of data) {
    const dist = Math.abs(d.round - xVal)
    if (dist < minDist) { minDist = dist; closest = d }
  }
  crosshairX.value = xScale(closest.round) + MARGIN.left
  activeRound.value = closest
}

function onMouseLeave() {
  crosshairX.value = null
  activeRound.value = null
}

const tooltipSide = computed(() => {
  if (!containerRef.value || crosshairX.value === null) return 'right'
  return crosshairX.value > containerRef.value.clientWidth / 2 ? 'left' : 'right'
})

// --- D3 rendering ---
function clearAll() {
  for (const r of [sentimentRef, volumeRef, consensusRef]) {
    if (r.value) d3.select(r.value).selectAll('*').remove()
  }
}

function renderAll() {
  clearAll()
  const data = roundData.value
  if (!data.length || !containerRef.value) return
  const cw = containerRef.value.clientWidth
  if (cw === 0) return

  const w = cw - MARGIN.left - MARGIN.right
  xScale = d3.scaleLinear()
    .domain([data[0].round, data[data.length - 1].round])
    .range([0, w])

  const compact = viewMode.value === 'compact'
  const h = compact ? COMPACT_H : EXPANDED_H

  if (visibleRows.value.has('sentiment')) renderSentiment(data, cw, w, h, compact)
  if (visibleRows.value.has('volume')) renderVolume(data, cw, w, h, compact)
  if (visibleRows.value.has('consensus')) renderConsensus(data, cw, w, h, compact)
}

function makeSvg(container, cw, h, showXAxis) {
  const m = showXAxis ? MARGIN : MARGIN_COMPACT
  const total = h + m.top + m.bottom
  const svg = d3.select(container)
    .append('svg')
    .attr('width', cw)
    .attr('height', total)
    .attr('viewBox', `0 0 ${cw} ${total}`)
  const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${m.top})`)
  return { svg, g }
}

function addXLabels(g, data, h) {
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => xScale(d.round))
    .attr('y', h + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d.round}`)
}

// --- Row 1: Sentiment line chart ---
function renderSentiment(data, cw, w, h, compact) {
  if (!sentimentRef.value) return
  const showX = !compact && lastVisibleRow.value === 'sentiment'
  const { g } = makeSvg(sentimentRef.value, cw, h, showX)
  const y = d3.scaleLinear().domain([-0.5, 0.5]).range([h, 0]).clamp(true)

  if (!compact) {
    const gridVals = [-0.4, -0.2, 0, 0.2, 0.4]
    g.selectAll('.grid').data(gridVals).join('line')
      .attr('x1', 0).attr('x2', w)
      .attr('y1', d => y(d)).attr('y2', d => y(d))
      .attr('stroke', d => d === 0 ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.05)')
      .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,3')

    g.selectAll('.y-label').data([-0.4, 0, 0.4]).join('text')
      .attr('x', -6).attr('y', d => y(d)).attr('dy', '0.35em')
      .attr('text-anchor', 'end').attr('font-size', '10px')
      .attr('fill', d => d > 0 ? '#009900' : d < 0 ? '#ff5600' : '#888')
      .text(d => d === 0 ? '0' : d > 0 ? `+${d}` : `${d}`)

    if (showX) addXLabels(g, data, h)
  }

  // Positive area
  g.append('path').datum(data)
    .attr('d', d3.area()
      .x(d => xScale(d.round)).y0(y(0))
      .y1(d => d.sentiment > 0 ? y(d.sentiment) : y(0))
      .curve(d3.curveMonotoneX))
    .attr('fill', 'rgba(0,153,0,0.06)')

  // Negative area
  g.append('path').datum(data)
    .attr('d', d3.area()
      .x(d => xScale(d.round)).y0(y(0))
      .y1(d => d.sentiment < 0 ? y(d.sentiment) : y(0))
      .curve(d3.curveMonotoneX))
    .attr('fill', 'rgba(255,86,0,0.06)')

  // Sentiment line
  const path = g.append('path').datum(data)
    .attr('d', d3.line().x(d => xScale(d.round)).y(d => y(d.sentiment)).curve(d3.curveMonotoneX))
    .attr('fill', 'none').attr('stroke', '#2068FF').attr('stroke-width', compact ? 1.5 : 2)

  const len = path.node().getTotalLength()
  path.attr('stroke-dasharray', `${len} ${len}`).attr('stroke-dashoffset', len)
    .transition().duration(600).ease(d3.easeCubicOut).attr('stroke-dashoffset', 0)

  if (!compact) {
    g.selectAll('.dot').data(data).join('circle')
      .attr('cx', d => xScale(d.round)).attr('cy', d => y(d.sentiment))
      .attr('r', 0)
      .attr('fill', d => d.sentiment > 0.1 ? '#009900' : d.sentiment < -0.1 ? '#ff5600' : '#2068FF')
      .attr('stroke', '#fff').attr('stroke-width', 1.5)
      .transition().duration(200).delay((_, i) => 600 + i * 30).attr('r', 3)
  }
}

// --- Row 2: Interaction volume bars ---
function computeStack(d) {
  let cum = 0
  return VOLUME_CATS.map(cat => {
    const start = cum
    cum += d[cat.key]
    return { start, end: cum }
  })
}

function renderVolume(data, cw, w, h, compact) {
  if (!volumeRef.value) return
  const showX = !compact && lastVisibleRow.value === 'volume'
  const { g } = makeSvg(volumeRef.value, cw, h, showX)

  const maxVol = Math.max(...data.map(d => d.volume), 1)
  const y = d3.scaleLinear().domain([0, maxVol]).range([h, 0])

  if (compact) {
    // Sparkline area
    g.append('path').datum(data)
      .attr('d', d3.area().x(d => xScale(d.round)).y0(h).y1(d => y(d.volume)).curve(d3.curveMonotoneX))
      .attr('fill', 'rgba(255,86,0,0.1)')
    g.append('path').datum(data)
      .attr('d', d3.line().x(d => xScale(d.round)).y(d => y(d.volume)).curve(d3.curveMonotoneX))
      .attr('fill', 'none').attr('stroke', '#ff5600').attr('stroke-width', 1.5)
    return
  }

  // Grid
  const ticks = y.ticks(4)
  g.selectAll('.grid').data(ticks).join('line')
    .attr('x1', 0).attr('x2', w)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.05)').attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label').data(ticks).join('text')
    .attr('x', -6).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end').attr('font-size', '10px').attr('fill', '#888')
    .text(d => d)

  if (showX) addXLabels(g, data, h)

  // Stacked bars
  const barW = Math.max(2, w / data.length - 2)
  for (const [ci, cat] of VOLUME_CATS.entries()) {
    g.selectAll(`.bar-${cat.key}`).data(data).join('rect')
      .attr('x', d => xScale(d.round) - barW / 2)
      .attr('y', h).attr('width', barW).attr('height', 0)
      .attr('rx', 2).attr('fill', cat.color).attr('opacity', 0.75)
      .transition().duration(400).delay((_, i) => i * 15 + ci * 40).ease(d3.easeCubicOut)
      .attr('y', d => y(computeStack(d)[ci].end))
      .attr('height', d => {
        const s = computeStack(d)[ci]
        return Math.max(0, y(s.start) - y(s.end))
      })
  }
}

// --- Row 3: Consensus area chart ---
function renderConsensus(data, cw, w, h, compact) {
  if (!consensusRef.value) return
  const showX = !compact && lastVisibleRow.value === 'consensus'
  const { g } = makeSvg(consensusRef.value, cw, h, showX)
  const y = d3.scaleLinear().domain([0, 1]).range([h, 0])

  if (!compact) {
    g.selectAll('.grid').data([0, 0.25, 0.5, 0.75, 1]).join('line')
      .attr('x1', 0).attr('x2', w)
      .attr('y1', d => y(d)).attr('y2', d => y(d))
      .attr('stroke', 'rgba(0,0,0,0.05)').attr('stroke-dasharray', '2,3')

    g.selectAll('.y-label').data([0, 0.5, 1]).join('text')
      .attr('x', -6).attr('y', d => y(d)).attr('dy', '0.35em')
      .attr('text-anchor', 'end').attr('font-size', '10px').attr('fill', '#888')
      .text(d => `${Math.round(d * 100)}%`)

    if (showX) addXLabels(g, data, h)
  }

  // Area fill
  g.append('path').datum(data)
    .attr('d', d3.area().x(d => xScale(d.round)).y0(h).y1(d => y(d.consensus)).curve(d3.curveMonotoneX))
    .attr('fill', 'rgba(170,0,255,0.08)')
    .style('opacity', 0).transition().duration(600).style('opacity', 1)

  // Consensus line
  const path = g.append('path').datum(data)
    .attr('d', d3.line().x(d => xScale(d.round)).y(d => y(d.consensus)).curve(d3.curveMonotoneX))
    .attr('fill', 'none').attr('stroke', '#AA00FF').attr('stroke-width', compact ? 1.5 : 2)

  const len = path.node().getTotalLength()
  path.attr('stroke-dasharray', `${len} ${len}`).attr('stroke-dashoffset', len)
    .transition().duration(600).ease(d3.easeCubicOut).attr('stroke-dashoffset', 0)

  if (!compact) {
    g.selectAll('.dot').data(data).join('circle')
      .attr('cx', d => xScale(d.round)).attr('cy', d => y(d.consensus))
      .attr('r', 0).attr('fill', '#AA00FF').attr('stroke', '#fff').attr('stroke-width', 1.5)
      .transition().duration(200).delay((_, i) => 600 + i * 30).attr('r', 3)
  }
}

// --- Lifecycle ---
watch([() => props.actions.length, () => props.timeline.length, viewMode, visibleRows], () => {
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
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 px-5 py-3 border-b border-[var(--color-border)]">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Multi-Metric View</h3>

      <div class="flex items-center gap-3">
        <!-- Row toggles -->
        <div class="flex gap-1">
          <button
            v-for="row in ROWS"
            :key="row.key"
            class="px-2 py-0.5 text-[11px] rounded font-medium transition-colors border"
            :class="visibleRows.has(row.key)
              ? 'border-current opacity-100'
              : 'border-transparent opacity-40 hover:opacity-60'"
            :style="{ color: row.color }"
            @click="toggleRow(row.key)"
          >
            {{ row.label }}
          </button>
        </div>

        <!-- Compact / Expanded toggle -->
        <div class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
          <button
            class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
            :class="viewMode === 'expanded'
              ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
            @click="viewMode = 'expanded'"
          >
            Expanded
          </button>
          <button
            class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
            :class="viewMode === 'compact'
              ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
            @click="viewMode = 'compact'"
          >
            Compact
          </button>
        </div>
      </div>
    </div>

    <!-- Charts container (no padding so crosshair aligns with SVGs) -->
    <div class="px-5 py-3">
      <div
        v-if="hasData"
        ref="containerRef"
        class="relative"
        @mousemove="onMouseMove"
        @mouseleave="onMouseLeave"
      >
        <!-- Crosshair line -->
        <div
          v-if="crosshairX !== null"
          class="absolute top-0 bottom-0 w-px pointer-events-none z-10"
          style="background: var(--color-text); opacity: 0.15"
          :style="{ left: `${crosshairX}px` }"
        />

        <!-- Crosshair tooltip -->
        <div
          v-if="activeRound"
          class="absolute top-1 z-20 pointer-events-none bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 shadow-lg text-xs"
          :style="tooltipSide === 'right'
            ? { left: `${crosshairX + 12}px` }
            : { right: `${(containerRef?.clientWidth || 0) - crosshairX + 12}px` }"
        >
          <div class="font-semibold text-[var(--color-text)] mb-1">Round {{ activeRound.round }}</div>
          <div v-if="visibleRows.has('sentiment')" class="flex items-center gap-1.5 mb-0.5">
            <span class="w-1.5 h-1.5 rounded-full bg-[#2068FF]" />
            <span class="text-[var(--color-text-secondary)]">Sentiment:</span>
            <span
              class="font-medium"
              :style="{ color: activeRound.sentiment > 0.1 ? '#009900' : activeRound.sentiment < -0.1 ? '#ff5600' : '#2068FF' }"
            >
              {{ activeRound.sentiment >= 0 ? '+' : '' }}{{ activeRound.sentiment.toFixed(2) }}
            </span>
          </div>
          <div v-if="visibleRows.has('volume')" class="flex items-center gap-1.5 mb-0.5">
            <span class="w-1.5 h-1.5 rounded-full bg-[#ff5600]" />
            <span class="text-[var(--color-text-secondary)]">Volume:</span>
            <span class="font-medium text-[var(--color-text)]">{{ activeRound.volume }} actions</span>
          </div>
          <div v-if="visibleRows.has('consensus')" class="flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-[#AA00FF]" />
            <span class="text-[var(--color-text-secondary)]">Consensus:</span>
            <span class="font-medium text-[#AA00FF]">{{ Math.round(activeRound.consensus * 100) }}%</span>
          </div>
        </div>

        <!-- Sentiment row -->
        <div v-if="visibleRows.has('sentiment')" class="mb-1">
          <div class="flex items-center gap-1.5 mb-0.5">
            <span class="w-2 h-0.5 rounded bg-[#2068FF]" />
            <span class="text-[11px] font-medium text-[var(--color-text-secondary)]">Agent Sentiment</span>
          </div>
          <div ref="sentimentRef" />
        </div>

        <!-- Volume row -->
        <div v-if="visibleRows.has('volume')" class="mb-1">
          <div class="flex items-center gap-1.5 mb-0.5">
            <span class="w-2 h-0.5 rounded bg-[#ff5600]" />
            <span class="text-[11px] font-medium text-[var(--color-text-secondary)]">Interaction Volume</span>
          </div>
          <div ref="volumeRef" />
        </div>

        <!-- Consensus row -->
        <div v-if="visibleRows.has('consensus')">
          <div class="flex items-center gap-1.5 mb-0.5">
            <span class="w-2 h-0.5 rounded bg-[#AA00FF]" />
            <span class="text-[11px] font-medium text-[var(--color-text-secondary)]">Consensus</span>
          </div>
          <div ref="consensusRef" />
        </div>

        <!-- Volume legend (expanded only) -->
        <div
          v-if="visibleRows.has('volume') && viewMode === 'expanded'"
          class="flex items-center gap-3 mt-2 pt-2 border-t border-[var(--color-border)] text-[11px] text-[var(--color-text-muted)]"
        >
          <span v-for="cat in VOLUME_CATS" :key="cat.key" class="flex items-center gap-1">
            <span class="inline-block w-2 h-2 rounded-sm" :style="{ backgroundColor: cat.color, opacity: 0.75 }" />
            {{ cat.label }}
          </span>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm">
        <span>Multi-metric data will appear as agents interact</span>
      </div>
    </div>
  </div>
</template>
