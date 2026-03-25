<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { select, scaleLinear, area as d3Area, line as d3Line, curveMonotoneX, stack as d3Stack, stackOrderNone, easeCubicOut } from 'd3'
import { useChartEntrance } from '../../composables/useChartEntrance'
import { getChartColors, useChartColors } from '../../lib/chartUtils'

const props = defineProps({
  actions: { type: Array, default: () => [] },
  timeline: { type: Array, default: () => [] },
})

const chartRef = ref(null)
const wrapperRef = ref(null)
let resizeObserver = null
let resizeTimer = null
const { colors: themeColors, isDark } = useChartColors()

const { isVisible } = useChartEntrance(wrapperRef)

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
    select(chartRef.value).selectAll('*').remove()
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
  const c = getChartColors()
  const margin = { top: 12, right: 16, bottom: 28, left: 36 }
  const width = containerWidth - margin.left - margin.right
  const height = 180
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleLinear()
    .domain([data[0].round, data[data.length - 1].round])
    .range([0, width])

  const y = scaleLinear()
    .domain([-0.6, 0.6])
    .range([height, 0])
    .clamp(true)

  const gridValues = [-0.4, -0.2, 0, 0.2, 0.4]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', d => d === 0 ? c.gridLineStrong : c.gridLine)
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,3')
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => i * 30)
    .style('opacity', 1)

  g.selectAll('.y-label')
    .data(gridValues)
    .join('text')
    .attr('x', -6)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', d => {
      if (d > 0) return c.green
      if (d < 0) return c.orange
      return c.textMuted
    })
    .text(d => {
      if (d === 0) return '0'
      return d > 0 ? `+${d.toFixed(1)}` : d.toFixed(1)
    })
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 50 + i * 25)
    .style('opacity', 1)

  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', c.textMuted)
    .text(d => `R${d.round}`)
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 80 + i * 20)
    .style('opacity', 1)

  const positiveArea = d3Area()
    .x(d => x(d.round))
    .y0(y(0))
    .y1(d => d.avgSentiment > 0 ? y(d.avgSentiment) : y(0))
    .curve(curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', positiveArea)
    .attr('fill', c.areaPositive)
    .style('opacity', 0)
    .transition()
    .duration(400)
    .delay(100)
    .style('opacity', 1)

  const negativeArea = d3Area()
    .x(d => x(d.round))
    .y0(y(0))
    .y1(d => d.avgSentiment < 0 ? y(d.avgSentiment) : y(0))
    .curve(curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', negativeArea)
    .attr('fill', c.areaNegative)
    .style('opacity', 0)
    .transition()
    .duration(400)
    .delay(100)
    .style('opacity', 1)

  const sentimentLine = d3Line()
    .x(d => x(d.round))
    .y(d => y(d.avgSentiment))
    .curve(curveMonotoneX)

  const gradientId = 'sentiment-gradient'
  const defs = svg.append('defs')
  const gradient = defs.append('linearGradient')
    .attr('id', gradientId)
    .attr('gradientUnits', 'userSpaceOnUse')
    .attr('x1', 0).attr('y1', y(0.5))
    .attr('x2', 0).attr('y2', y(-0.5))

  gradient.append('stop').attr('offset', '0%').attr('stop-color', c.green)
  gradient.append('stop').attr('offset', '50%').attr('stop-color', c.primary)
  gradient.append('stop').attr('offset', '100%').attr('stop-color', c.orange)

  const path = g.append('path')
    .datum(data)
    .attr('d', sentimentLine)
    .attr('fill', 'none')
    .attr('stroke', `url(#${gradientId})`)
    .attr('stroke-width', 2.5)

  const totalLength = path.node().getTotalLength()
  path
    .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(800)
    .ease(easeCubicOut)
    .attr('stroke-dashoffset', 0)

  const dots = g.selectAll('.dot')
    .data(data)
    .join('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', d => y(d.avgSentiment))
    .attr('r', 0)
    .attr('fill', d => {
      if (d.avgSentiment > 0.1) return c.green
      if (d.avgSentiment < -0.1) return c.orange
      return c.primary
    })
    .attr('stroke', c.surface)
    .attr('stroke-width', 1.5)

  dots.transition()
    .duration(300)
    .delay((_, i) => 800 + i * 40)
    .attr('r', 4)

  const tooltip = select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', c.surface)
    .style('border', `1px solid ${c.border}`)
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')

  // Invisible interaction targets (pointer events for mouse + touch)
  let activeRound = null

  function showTooltip(event, d) {
    const sentimentLabel = d.avgSentiment > 0.1 ? 'Positive' : d.avgSentiment < -0.1 ? 'Negative' : 'Neutral'
    const color = d.avgSentiment > 0.1 ? c.green : d.avgSentiment < -0.1 ? c.orange : c.primary
    tooltip
      .html(`
        <div style="font-weight:600;color:${c.text};margin-bottom:4px">Round ${d.round}</div>
        <div style="color:${color};font-weight:600">${sentimentLabel} (${d.avgSentiment >= 0 ? '+' : ''}${d.avgSentiment.toFixed(2)})</div>
        <div style="color:${c.textMuted};margin-top:2px">
          ${d.agentCount} agents · ${d.total} actions
        </div>
        <div style="display:flex;gap:8px;margin-top:4px;font-size:11px">
          <span style="color:${c.green}">+${d.positive}</span>
          <span style="color:${c.textMuted}">${d.neutral} neutral</span>
          <span style="color:${c.orange}">-${d.negative}</span>
        </div>
      `)
      .style('opacity', 1)

    const rect = container.getBoundingClientRect()
    const cx = x(d.round) + margin.left
    tooltip
      .style('left', `${cx + 12}px`)
      .style('top', `${event.clientY - rect.top - 40}px`)

    dots.filter(dd => dd.round === d.round)
      .transition().duration(100)
      .attr('r', 6)
    activeRound = d.round
  }

  function hideTooltip() {
    tooltip.style('opacity', 0)
    if (activeRound != null) {
      dots.filter(dd => dd.round === activeRound)
        .transition().duration(100)
        .attr('r', 4)
      activeRound = null
    }
  }

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
    .style('touch-action', 'none')
    .on('pointerenter', showTooltip)
    .on('pointermove', (event, d) => {
      if (activeRound !== d.round) showTooltip(event, d)
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('pointerleave', hideTooltip)
    .on('pointercancel', hideTooltip)
}

function renderDistribution(container, data, containerWidth) {
  const c = getChartColors()
  const margin = { top: 12, right: 16, bottom: 28, left: 36 }
  const width = containerWidth - margin.left - margin.right
  const height = 180
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const stackData = data.map(d => ({
    round: d.round,
    positive: d.total ? d.positive / d.total : 0,
    neutral: d.total ? d.neutral / d.total : 0,
    negative: d.total ? d.negative / d.total : 0,
  }))

  const x = scaleLinear()
    .domain([data[0].round, data[data.length - 1].round])
    .range([0, width])

  const y = scaleLinear()
    .domain([0, 1])
    .range([height, 0])

  const stackGen = d3Stack()
    .keys(['negative', 'neutral', 'positive'])
    .order(stackOrderNone)

  const series = stackGen(stackData)

  const stackColors = {
    positive: c.stackPositive,
    neutral: c.stackNeutral,
    negative: c.stackNegative,
  }

  const areaGen = d3Area()
    .x(d => x(d.data.round))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(curveMonotoneX)

  // Clip-path for left-to-right reveal animation
  const clipId = `dist-reveal-${Date.now()}`
  svg.append('defs')
    .append('clipPath')
    .attr('id', clipId)
    .append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', 0)
    .attr('height', totalHeight)
    .transition()
    .duration(800)
    .delay(100)
    .ease(easeCubicOut)
    .attr('width', width)

  // Stacked areas with clip reveal
  g.append('g')
    .attr('clip-path', `url(#${clipId})`)
    .selectAll('.area')
    .data(series)
    .join('path')
    .attr('d', areaGen)
    .attr('fill', d => stackColors[d.key])

  const gridValues = [0, 0.25, 0.5, 0.75, 1.0]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', c.stackGrid)
    .attr('stroke-dasharray', '2,3')
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => i * 30)
    .style('opacity', 1)

  g.selectAll('.y-label')
    .data(gridValues.filter(d => d === 0 || d === 0.5 || d === 1))
    .join('text')
    .attr('x', -6)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', c.textMuted)
    .text(d => `${Math.round(d * 100)}%`)
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 50 + i * 25)
    .style('opacity', 1)

  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', c.textMuted)
    .text(d => `R${d.round}`)
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 80 + i * 20)
    .style('opacity', 1)
}

// --- Lifecycle ---

watch([() => props.actions.length, () => props.timeline.length, viewMode, isVisible, isDark], () => {
  if (isVisible.value) {
    nextTick(() => renderChart())
  }
})

onMounted(() => {
  if (isVisible.value) renderChart()
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
  <div
    ref="wrapperRef"
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 transition-all duration-500 ease-out"
    :class="isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'"
  >
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Sentiment Timeline</h3>
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

    <div v-if="sentimentData.length" class="relative" ref="chartRef" style="height: 220px; touch-action: pan-y" />

    <div v-else class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm">
      <span>Sentiment data will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="sentimentData.length" class="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
      <template v-if="viewMode === 'trend'">
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full" :style="{ background: themeColors.green }" /> Positive
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full" :style="{ background: themeColors.primary }" /> Neutral
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full" :style="{ background: themeColors.orange }" /> Negative
        </span>
      </template>
      <template v-else>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm" :style="{ background: themeColors.stackPositive }" /> Positive
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm" :style="{ background: themeColors.stackNeutral }" /> Neutral
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm" :style="{ background: themeColors.stackNegative }" /> Negative
        </span>
      </template>
    </div>
  </div>
</template>
