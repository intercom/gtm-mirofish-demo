<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useMobileChart } from '../../composables/useMobileChart'

const { isMobile } = useMobileChart()

const props = defineProps({
  actions: { type: Array, default: () => [] },
  timeline: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Sentiment scoring ---

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

  // Weight by action type
  if (type.includes('LIKE') || type.includes('UPVOTE')) return 0.3 + contentScore * 0.2
  if (type.includes('REPOST') || type.includes('RETWEET') || type.includes('SHARE')) return 0.2 + contentScore * 0.2
  if (type.includes('REPLY') || type.includes('COMMENT')) return contentScore * 0.8
  return contentScore * 0.6
}

const sentimentData = computed(() => {
  if (!props.actions.length) return []

  const roundMap = new Map()

  for (const action of props.actions) {
    const round = action.round_num
    if (round == null) continue
    if (!roundMap.has(round)) {
      roundMap.set(round, { scores: [], agents: new Set() })
    }
    const entry = roundMap.get(round)
    entry.scores.push(scoreAction(action))
    entry.agents.add(action.agent_name || action.agent_id)
  }

  const rounds = Array.from(roundMap.keys()).sort((a, b) => a - b)
  return rounds.map(round => {
    const { scores, agents } = roundMap.get(round)
    const avg = scores.reduce((s, v) => s + v, 0) / scores.length
    const positive = scores.filter(s => s > 0.1).length
    const negative = scores.filter(s => s < -0.1).length
    const neutral = scores.length - positive - negative
    return {
      round,
      avgSentiment: Math.max(-1, Math.min(1, avg)),
      positive,
      negative,
      neutral,
      total: scores.length,
      agentCount: agents.size,
    }
  })
})

// --- View mode ---
const viewMode = ref('trend') // 'trend' | 'distribution'

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !sentimentData.value.length) return

  const data = sentimentData.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  if (viewMode.value === 'distribution') {
    renderDistribution(container, data, containerWidth)
  } else {
    renderTrend(container, data, containerWidth)
  }
}

function renderTrend(container, data, containerWidth) {
  const mobile = isMobile.value
  const margin = mobile
    ? { top: 8, right: 12, bottom: 24, left: 30 }
    : { top: 12, right: 16, bottom: 28, left: 36 }
  const width = containerWidth - margin.left - margin.right
  const height = mobile ? 140 : 180
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
    .domain([data[0].round, data[data.length - 1].round])
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
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', d => d === 0 ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(gridValues)
    .join('text')
    .attr('x', -6)
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
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round}`)

  // Positive area (above 0)
  const positiveArea = d3.area()
    .x(d => x(d.round))
    .y0(y(0))
    .y1(d => d.avgSentiment > 0 ? y(d.avgSentiment) : y(0))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', positiveArea)
    .attr('fill', 'rgba(0, 153, 0, 0.08)')

  // Negative area (below 0)
  const negativeArea = d3.area()
    .x(d => x(d.round))
    .y0(y(0))
    .y1(d => d.avgSentiment < 0 ? y(d.avgSentiment) : y(0))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', negativeArea)
    .attr('fill', 'rgba(255, 86, 0, 0.08)')

  // Sentiment line
  const line = d3.line()
    .x(d => x(d.round))
    .y(d => y(d.avgSentiment))
    .curve(d3.curveMonotoneX)

  // Line gradient
  const gradientId = 'sentiment-gradient'
  const defs = svg.append('defs')
  const gradient = defs.append('linearGradient')
    .attr('id', gradientId)
    .attr('gradientUnits', 'userSpaceOnUse')
    .attr('x1', 0).attr('y1', y(0.5))
    .attr('x2', 0).attr('y2', y(-0.5))

  gradient.append('stop').attr('offset', '0%').attr('stop-color', '#009900')
  gradient.append('stop').attr('offset', '50%').attr('stop-color', '#2068FF')
  gradient.append('stop').attr('offset', '100%').attr('stop-color', '#ff5600')

  const path = g.append('path')
    .datum(data)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', `url(#${gradientId})`)
    .attr('stroke-width', 2.5)

  // Animate line drawing
  const totalLength = path.node().getTotalLength()
  path
    .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(800)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)

  // Data points
  const dots = g.selectAll('.dot')
    .data(data)
    .join('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', d => y(d.avgSentiment))
    .attr('r', 0)
    .attr('fill', d => {
      if (d.avgSentiment > 0.1) return '#009900'
      if (d.avgSentiment < -0.1) return '#ff5600'
      return '#2068FF'
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)

  const dotRadius = mobile ? 6 : 4

  dots.transition()
    .duration(300)
    .delay((_, i) => 800 + i * 40)
    .attr('r', dotRadius)

  // Tooltip overlay
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

  // Invisible hover targets
  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round) : x(d.round)
      return (prev + x(d.round)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round) : x(d.round)
      const next = i < data.length - 1 ? x(data[i + 1].round) : x(d.round)
      return ((x(d.round) - prev) + (next - x(d.round))) / 2
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter touchstart', (event, d) => {
      if (event.type === 'touchstart') event.preventDefault()
      const sentimentLabel = d.avgSentiment > 0.1 ? 'Positive' : d.avgSentiment < -0.1 ? 'Negative' : 'Neutral'
      const color = d.avgSentiment > 0.1 ? '#009900' : d.avgSentiment < -0.1 ? '#ff5600' : '#2068FF'
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${d.round}</div>
          <div style="color:${color};font-weight:600">${sentimentLabel} (${d.avgSentiment >= 0 ? '+' : ''}${d.avgSentiment.toFixed(2)})</div>
          <div style="color:var(--color-text-muted,#888);margin-top:2px">
            ${d.agentCount} agents · ${d.total} actions
          </div>
          <div style="display:flex;gap:8px;margin-top:4px;font-size:11px">
            <span style="color:#009900">+${d.positive}</span>
            <span style="color:#888">${d.neutral} neutral</span>
            <span style="color:#ff5600">-${d.negative}</span>
          </div>
        `)
        .style('opacity', 1)

      const rect = container.getBoundingClientRect()
      const cx = event.touches ? event.touches[0].clientX : event.clientX
      const cy = event.touches ? event.touches[0].clientY : event.clientY
      tooltip
        .style('left', `${cx - rect.left + 12}px`)
        .style('top', `${cy - rect.top - 40}px`)

      dots.filter(dd => dd.round === d.round)
        .transition().duration(100)
        .attr('r', dotRadius + 2)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave touchend', (event, d) => {
      tooltip.style('opacity', 0)
      dots.filter(dd => dd.round === d.round)
        .transition().duration(100)
        .attr('r', dotRadius)
    })
}

function renderDistribution(container, data, containerWidth) {
  const mobile = isMobile.value
  const margin = mobile
    ? { top: 8, right: 12, bottom: 24, left: 30 }
    : { top: 12, right: 16, bottom: 28, left: 36 }
  const width = containerWidth - margin.left - margin.right
  const height = mobile ? 140 : 180
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Convert to percentages
  const stackData = data.map(d => ({
    round: d.round,
    positive: d.total ? d.positive / d.total : 0,
    neutral: d.total ? d.neutral / d.total : 0,
    negative: d.total ? d.negative / d.total : 0,
  }))

  const x = d3.scaleLinear()
    .domain([data[0].round, data[data.length - 1].round])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([0, 1])
    .range([height, 0])

  // Stack generator
  const stack = d3.stack()
    .keys(['negative', 'neutral', 'positive'])
    .order(d3.stackOrderNone)

  const series = stack(stackData)

  const colors = {
    positive: 'rgba(0, 153, 0, 0.5)',
    neutral: 'rgba(32, 104, 255, 0.3)',
    negative: 'rgba(255, 86, 0, 0.5)',
  }

  const area = d3.area()
    .x(d => x(d.data.round))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(d3.curveMonotoneX)

  // Stacked areas with animation
  g.selectAll('.area')
    .data(series)
    .join('path')
    .attr('d', area)
    .attr('fill', d => colors[d.key])
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((_, i) => i * 100)
    .style('opacity', 1)

  // Grid lines
  const gridValues = [0, 0.25, 0.5, 0.75, 1.0]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(255,255,255,0.4)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(gridValues.filter(d => d === 0 || d === 0.5 || d === 1))
    .join('text')
    .attr('x', -6)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `${Math.round(d * 100)}%`)

  // X-axis labels
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round}`)
}

// --- Lifecycle ---

watch([() => props.actions.length, () => props.timeline.length, viewMode, isMobile], () => {
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
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 sm:p-5">
    <div class="flex items-center justify-between mb-3 sm:mb-4">
      <h3 class="text-xs sm:text-sm font-semibold text-[var(--color-text)]">Sentiment Timeline</h3>
      <div v-if="sentimentData.length" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'trend'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'trend'"
        >
          Trend
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'distribution'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'distribution'"
        >
          Distribution
        </button>
      </div>
    </div>

    <div v-if="sentimentData.length" class="relative" ref="chartRef" :style="{ height: isMobile ? '172px' : '220px' }" />

    <div v-else class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm">
      <span>Sentiment data will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="sentimentData.length" class="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
      <template v-if="viewMode === 'trend'">
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-[#009900]" /> Positive
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-[#2068FF]" /> Neutral
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-[#ff5600]" /> Negative
        </span>
      </template>
      <template v-else>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm bg-[rgba(0,153,0,0.5)]" /> Positive
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm bg-[rgba(32,104,255,0.3)]" /> Neutral
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm bg-[rgba(255,86,0,0.5)]" /> Negative
        </span>
      </template>
    </div>
  </div>
</template>
