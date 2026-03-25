<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Sentiment scoring (matches SentimentTimeline) ---

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

// --- Agent pair extraction ---

const TARGET_FIELDS = {
  LIKE_POST: 'post_author_name',
  DISLIKE_POST: 'post_author_name',
  REPOST: 'original_author_name',
  QUOTE_POST: 'original_author_name',
  CREATE_COMMENT: 'post_author_name',
  LIKE_COMMENT: 'comment_author_name',
  DISLIKE_COMMENT: 'comment_author_name',
  FOLLOW: 'target_user_name',
  MUTE: 'target_user_name',
}

const INTERACTIVE_TYPES = new Set([
  'LIKE_POST', 'DISLIKE_POST', 'REPOST', 'QUOTE_POST',
  'CREATE_COMMENT', 'LIKE_COMMENT', 'DISLIKE_COMMENT',
  'FOLLOW', 'REPLY', 'LIKE',
])

function simpleHash(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

function shortName(name) {
  if (!name) return '?'
  const cleaned = name.replace(/\s*\(.*\)\s*$/, '')
  const parts = cleaned.trim().split(/\s+/)
  if (parts.length >= 2) return `${parts[0]} ${parts[1][0]}.`
  return parts[0]
}

function getTargetAgent(action) {
  const args = action.action_args || {}
  const type = (action.action_type || '').toUpperCase()
  return args[TARGET_FIELDS[type]] || null
}

// --- Main computed ---

const MAX_PAIRS = 12

const commData = computed(() => {
  if (!props.actions.length) return null

  const agents = []
  const agentSet = new Set()
  for (const action of props.actions) {
    const name = action.agent_name || `Agent ${action.agent_id}`
    if (!agentSet.has(name)) {
      agentSet.add(name)
      agents.push(name)
    }
  }

  const pairMap = new Map()

  for (const action of props.actions) {
    const round = action.round_num
    if (round == null) continue

    const source = action.agent_name || `Agent ${action.agent_id}`
    const type = (action.action_type || '').toUpperCase()
    let target = getTargetAgent(action)

    if (!target && INTERACTIVE_TYPES.has(type)) {
      const others = agents.filter(a => a !== source)
      if (others.length) {
        target = others[(simpleHash(source) + round) % others.length]
      }
    }

    if (!target || target === source) continue

    const pairKey = `${shortName(source)} → ${shortName(target)}`

    if (!pairMap.has(pairKey)) {
      pairMap.set(pairKey, { source, target, pairKey, rounds: new Map(), totalCount: 0 })
    }
    const pair = pairMap.get(pairKey)

    if (!pair.rounds.has(round)) {
      pair.rounds.set(round, { count: 0, sentiments: [] })
    }
    const rd = pair.rounds.get(round)
    rd.count++
    pair.totalCount++

    const content = action.action_args?.content || action.action_args?.quote_content || ''
    if (content) rd.sentiments.push(scoreSentiment(content))
  }

  if (!pairMap.size) return null

  const sortedPairs = Array.from(pairMap.values())
    .sort((a, b) => b.totalCount - a.totalCount)
    .slice(0, MAX_PAIRS)

  const pairLabels = sortedPairs.map(p => p.pairKey)

  const allRoundsSet = new Set()
  for (const action of props.actions) {
    if (action.round_num != null) allRoundsSet.add(action.round_num)
  }
  const allRounds = Array.from(allRoundsSet).sort((a, b) => a - b)

  const points = []
  for (let pi = 0; pi < sortedPairs.length; pi++) {
    const pair = sortedPairs[pi]
    for (const [round, data] of pair.rounds) {
      const avgSentiment = data.sentiments.length
        ? data.sentiments.reduce((a, b) => a + b, 0) / data.sentiments.length
        : 0
      points.push({
        round,
        pairIndex: pi,
        pairKey: pair.pairKey,
        count: data.count,
        sentiment: Math.max(-1, Math.min(1, avgSentiment)),
        source: shortName(pair.source),
        target: shortName(pair.target),
      })
    }
  }

  // Pattern detection
  const patterns = {}
  for (const pair of sortedPairs) {
    const roundKeys = Array.from(pair.rounds.keys()).sort((a, b) => a - b)
    const roundCount = roundKeys.length

    if (roundCount === 1) {
      patterns[pair.pairKey] = 'one-time'
    } else if (roundCount >= allRounds.length * 0.4) {
      patterns[pair.pairKey] = 'regular'
    } else {
      let hasBurst = false
      for (let i = 0; i < roundKeys.length && !hasBurst; i++) {
        let windowCount = 0
        for (let j = i; j < roundKeys.length && roundKeys[j] - roundKeys[i] <= 5; j++) {
          windowCount++
        }
        if (windowCount >= 3) hasBurst = true
      }
      patterns[pair.pairKey] = hasBurst ? 'burst' : 'intermittent'
    }
  }

  // Summary
  const roundCounts = new Map()
  const agentInteractionCounts = new Map()

  for (const pair of pairMap.values()) {
    for (const [round, data] of pair.rounds) {
      roundCounts.set(round, (roundCounts.get(round) || 0) + data.count)
    }
    agentInteractionCounts.set(pair.source,
      (agentInteractionCounts.get(pair.source) || 0) + pair.totalCount)
    agentInteractionCounts.set(pair.target,
      (agentInteractionCounts.get(pair.target) || 0) + pair.totalCount)
  }

  let busiestRound = null, maxRoundCount = 0
  for (const [r, c] of roundCounts) {
    if (c > maxRoundCount) { maxRoundCount = c; busiestRound = r }
  }

  let mostTalkative = null, maxAgentCount = 0
  for (const [a, c] of agentInteractionCounts) {
    if (c > maxAgentCount) { maxAgentCount = c; mostTalkative = shortName(a) }
  }

  return {
    pairLabels,
    points,
    patterns,
    allRounds,
    maxCount: Math.max(...points.map(p => p.count), 1),
    summary: {
      busiestRound,
      busiestRoundCount: maxRoundCount,
      mostTalkative,
      mostTalkativeCount: maxAgentCount,
      mostCommonPair: sortedPairs[0]?.pairKey,
      mostCommonPairCount: sortedPairs[0]?.totalCount || 0,
    },
  }
})

const chartHeight = computed(() => {
  if (!commData.value) return 0
  return commData.value.pairLabels.length * 28 + 44
})

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !commData.value) return

  const data = commData.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const { pairLabels, points, patterns, allRounds, maxCount } = data

  const margin = { top: 12, right: 20, bottom: 32, left: 120 }
  const rowHeight = 28
  const width = containerWidth - margin.left - margin.right
  const height = pairLabels.length * rowHeight
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const roundExtent = d3.extent(allRounds)
  const x = d3.scaleLinear()
    .domain(roundExtent[0] === roundExtent[1]
      ? [roundExtent[0] - 1, roundExtent[0] + 1]
      : roundExtent)
    .range([0, width])

  const y = d3.scaleBand()
    .domain(pairLabels)
    .range([0, height])
    .padding(0.3)

  const rScale = d3.scaleSqrt()
    .domain([1, Math.max(maxCount, 2)])
    .range([3, 10])

  // Horizontal grid
  g.selectAll('.h-grid')
    .data(pairLabels)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d) + y.bandwidth() / 2)
    .attr('y2', d => y(d) + y.bandwidth() / 2)
    .attr('stroke', 'rgba(0,0,0,0.05)')

  // Vertical grid
  const roundStep = Math.max(1, Math.floor(allRounds.length / 10))
  g.selectAll('.v-grid')
    .data(allRounds.filter((_, i) => i % roundStep === 0))
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.04)')
    .attr('stroke-dasharray', '2,3')

  // Pattern indicators
  g.selectAll('.pattern-icon')
    .data(pairLabels)
    .join('text')
    .attr('x', -margin.left + 8)
    .attr('y', d => y(d) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '9px')
    .attr('fill', d => {
      const p = patterns[d]
      if (p === 'regular') return '#2068FF'
      if (p === 'burst') return '#ff5600'
      return '#999'
    })
    .text(d => {
      const p = patterns[d]
      if (p === 'regular') return '●'
      if (p === 'burst') return '◆'
      if (p === 'one-time') return '○'
      return '·'
    })

  // Y-axis labels
  g.selectAll('.y-label')
    .data(pairLabels)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', d => {
      const p = patterns[d]
      if (p === 'regular') return '#2068FF'
      if (p === 'burst') return '#ff5600'
      return 'var(--color-text-muted, #888)'
    })
    .text(d => d)

  // X-axis labels
  const xStep = Math.max(1, Math.floor(allRounds.length / 8))
  g.selectAll('.x-label')
    .data(allRounds.filter((_, i) => i % xStep === 0 || i === allRounds.length - 1))
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d}`)

  // Connect regular communicators with lines
  for (const pairKey of pairLabels) {
    if (patterns[pairKey] !== 'regular') continue
    const pairPoints = points
      .filter(p => p.pairKey === pairKey)
      .sort((a, b) => a.round - b.round)

    if (pairPoints.length < 2) continue

    const line = d3.line()
      .x(d => x(d.round))
      .y(() => y(pairKey) + y.bandwidth() / 2)
      .curve(d3.curveMonotoneX)

    g.append('path')
      .datum(pairPoints)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(32, 104, 255, 0.15)')
      .attr('stroke-width', 1.5)
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
    .style('max-width', '220px')

  // Scatter points
  const dots = g.selectAll('.dot')
    .data(points)
    .join('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', d => y(d.pairKey) + y.bandwidth() / 2)
    .attr('r', 0)
    .attr('fill', d => {
      if (d.sentiment > 0.1) return '#009900'
      if (d.sentiment < -0.1) return '#ff5600'
      return '#2068FF'
    })
    .attr('fill-opacity', 0.7)
    .attr('stroke', d => {
      if (patterns[d.pairKey] === 'one-time') return 'var(--color-text-muted, #888)'
      return '#fff'
    })
    .attr('stroke-width', d => patterns[d.pairKey] === 'one-time' ? 1.5 : 1)
    .attr('stroke-dasharray', d => patterns[d.pairKey] === 'one-time' ? '2,1' : 'none')
    .style('cursor', 'pointer')

  dots.transition()
    .duration(400)
    .delay((_, i) => i * 15)
    .attr('r', d => rScale(d.count))

  dots
    .on('mouseenter', (event, d) => {
      const patternLabel = {
        regular: 'Regular communicators',
        burst: 'Burst pattern',
        'one-time': 'One-time interaction',
        intermittent: 'Intermittent',
      }[patterns[d.pairKey]] || ''

      const sentimentLabel = d.sentiment > 0.1 ? 'Positive' : d.sentiment < -0.1 ? 'Negative' : 'Neutral'
      const sentimentColor = d.sentiment > 0.1 ? '#009900' : d.sentiment < -0.1 ? '#ff5600' : '#2068FF'

      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">${d.source} → ${d.target}</div>
          <div style="color:var(--color-text-secondary,#666)">Round ${d.round} · ${d.count} interaction${d.count > 1 ? 's' : ''}</div>
          <div style="color:${sentimentColor};margin-top:2px;font-weight:500">${sentimentLabel}</div>
          ${patternLabel ? `<div style="color:var(--color-text-muted,#888);margin-top:2px;font-size:11px">${patternLabel}</div>` : ''}
        `)
        .style('opacity', 1)

      d3.select(event.target)
        .transition().duration(100)
        .attr('r', rScale(d.count) + 2)
        .attr('fill-opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', (event, d) => {
      tooltip.style('opacity', 0)
      d3.select(event.target)
        .transition().duration(100)
        .attr('r', rScale(d.count))
        .attr('fill-opacity', 0.7)
    })
}

// --- Lifecycle ---

watch(() => props.actions.length, () => {
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
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Communication Patterns</h3>
      <span v-if="commData" class="text-[11px] text-[var(--color-text-muted)]">
        {{ commData.pairLabels.length }} pairs · {{ commData.allRounds.length }} rounds
      </span>
    </div>

    <div
      v-if="commData"
      class="relative"
      ref="chartRef"
      :style="{ height: `${chartHeight}px` }"
    />

    <div v-else class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm">
      <span>Communication patterns will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="commData" class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="font-medium text-[var(--color-text-secondary)]">Sentiment:</span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#009900]" /> Positive
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#2068FF]" /> Neutral
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#ff5600]" /> Negative
      </span>
      <span class="mx-1 text-[var(--color-border)]">|</span>
      <span class="font-medium text-[var(--color-text-secondary)]">Pattern:</span>
      <span class="flex items-center gap-1.5">
        <span class="text-[#2068FF]">●</span> Regular
      </span>
      <span class="flex items-center gap-1.5">
        <span class="text-[#ff5600]">◆</span> Burst
      </span>
      <span class="flex items-center gap-1.5">
        <span class="text-[#999]">○</span> One-time
      </span>
    </div>

    <!-- Summary -->
    <div v-if="commData" class="grid grid-cols-3 gap-3 mt-4 pt-3 border-t border-[var(--color-border)]">
      <div class="text-center">
        <div class="text-lg font-bold text-[var(--color-primary,#2068FF)]">
          R{{ commData.summary.busiestRound }}
        </div>
        <div class="text-[11px] text-[var(--color-text-muted)]">
          Busiest round ({{ commData.summary.busiestRoundCount }})
        </div>
      </div>
      <div class="text-center">
        <div class="text-sm font-bold text-[var(--color-text)] truncate" :title="commData.summary.mostTalkative">
          {{ commData.summary.mostTalkative }}
        </div>
        <div class="text-[11px] text-[var(--color-text-muted)]">
          Most active ({{ commData.summary.mostTalkativeCount }})
        </div>
      </div>
      <div class="text-center">
        <div class="text-sm font-bold text-[var(--color-text)] truncate" :title="commData.summary.mostCommonPair">
          {{ commData.summary.mostCommonPair }}
        </div>
        <div class="text-[11px] text-[var(--color-text-muted)]">
          Top pair ({{ commData.summary.mostCommonPairCount }})
        </div>
      </div>
    </div>
  </div>
</template>
