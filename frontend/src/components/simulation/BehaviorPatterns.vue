<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Sentiment scoring (same approach as SentimentTimeline) ---

const POSITIVE_WORDS = [
  'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
  'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
  'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
]

const NEGATIVE_WORDS = [
  'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
  'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
  'problem', 'unclear', 'frustrated', 'poor', 'slow', 'lacks',
]

function scoreSentiment(content) {
  if (!content) return 0
  const lower = content.toLowerCase()
  let pos = 0, neg = 0
  for (const w of POSITIVE_WORDS) if (lower.includes(w)) pos++
  for (const w of NEGATIVE_WORDS) if (lower.includes(w)) neg++
  if (pos + neg === 0) return 0
  return (pos - neg) / (pos + neg)
}

// --- Pattern detection ---

const TYPE_COLORS = {
  engagement: '#2068FF',
  sentiment: '#ff5600',
  platform: '#009900',
  interaction: '#AA00FF',
  escalation: '#e6194B',
}

const patterns = computed(() => {
  if (!props.actions.length) return []

  const detected = []

  // Group actions by agent
  const byAgent = new Map()
  for (const a of props.actions) {
    const name = a.agent_name || `Agent #${a.agent_id}`
    if (!byAgent.has(name)) byAgent.set(name, [])
    byAgent.get(name).push(a)
  }

  const allRounds = [...new Set(props.actions.map(a => a.round_num).filter(r => r != null))].sort((a, b) => a - b)
  if (allRounds.length < 2) return []
  const midRound = allRounds[Math.floor(allRounds.length / 2)]

  for (const [agent, actions] of byAgent) {
    if (actions.length < 3) continue

    const rounds = actions.map(a => a.round_num).filter(r => r != null)
    const uniqueRounds = [...new Set(rounds)].sort((a, b) => a - b)

    // Round-level action counts
    const roundCounts = new Map()
    for (const r of rounds) roundCounts.set(r, (roundCounts.get(r) || 0) + 1)

    // 1. Consistent engagement — active in >70% of rounds
    const activeRatio = uniqueRounds.length / allRounds.length
    if (activeRatio > 0.7) {
      detected.push({
        agent,
        description: 'Active every round — consistent engagement',
        frequency: uniqueRounds.length,
        consistency: Math.min(1, activeRatio),
        rounds: uniqueRounds,
        type: 'engagement',
      })
    }

    // 2. Sentiment arc — early vs late sentiment shift
    const earlyActions = actions.filter(a => a.round_num != null && a.round_num <= midRound)
    const lateActions = actions.filter(a => a.round_num != null && a.round_num > midRound)

    if (earlyActions.length >= 2 && lateActions.length >= 2) {
      const earlySent = earlyActions.reduce((s, a) => s + scoreSentiment(a.action_args?.content), 0) / earlyActions.length
      const lateSent = lateActions.reduce((s, a) => s + scoreSentiment(a.action_args?.content), 0) / lateActions.length
      const shift = lateSent - earlySent

      if (Math.abs(shift) > 0.15) {
        detected.push({
          agent,
          description: shift > 0 ? 'Shifts positive over time' : 'Agrees early, pushes back later',
          frequency: earlyActions.length + lateActions.length,
          consistency: Math.min(1, Math.abs(shift) * 2),
          rounds: [...new Set([...earlyActions, ...lateActions].map(a => a.round_num))],
          type: 'sentiment',
        })
      }
    }

    // 3. Platform preference — >75% on one platform
    const platforms = actions.map(a => a.platform).filter(Boolean)
    if (platforms.length >= 3) {
      const counts = {}
      for (const p of platforms) counts[p] = (counts[p] || 0) + 1
      for (const [platform, count] of Object.entries(counts)) {
        const ratio = count / platforms.length
        if (ratio > 0.75) {
          detected.push({
            agent,
            description: `Prefers ${platform} (${Math.round(ratio * 100)}% of actions)`,
            frequency: count,
            consistency: ratio,
            rounds: [...new Set(actions.filter(a => a.platform === platform).map(a => a.round_num))],
            type: 'platform',
          })
        }
      }
    }

    // 4. Reply-heavy — >50% of actions are replies/comments
    const replies = actions.filter(a => {
      const t = (a.action_type || '').toUpperCase()
      return t.includes('REPLY') || t.includes('COMMENT')
    })
    if (replies.length >= 3 && replies.length / actions.length > 0.5) {
      detected.push({
        agent,
        description: `Reply-focused — ${Math.round(replies.length / actions.length * 100)}% replies`,
        frequency: replies.length,
        consistency: replies.length / actions.length,
        rounds: [...new Set(replies.map(a => a.round_num))],
        type: 'interaction',
      })
    }

    // 5. Escalation — action rate increases over time
    if (uniqueRounds.length >= 4) {
      const half = Math.floor(uniqueRounds.length / 2)
      const firstHalf = uniqueRounds.slice(0, half)
      const secondHalf = uniqueRounds.slice(half)
      const firstRate = firstHalf.reduce((s, r) => s + (roundCounts.get(r) || 0), 0) / firstHalf.length
      const secondRate = secondHalf.reduce((s, r) => s + (roundCounts.get(r) || 0), 0) / secondHalf.length

      if (secondRate > firstRate * 1.5 && firstRate > 0) {
        detected.push({
          agent,
          description: 'Escalates engagement over time',
          frequency: uniqueRounds.length,
          consistency: Math.min(1, secondRate / firstRate - 1),
          rounds: uniqueRounds,
          type: 'escalation',
        })
      }
    }
  }

  return detected.sort((a, b) => b.consistency - a.consistency)
})

// --- D3 rendering ---

const MAX_CHART_ROWS = 8
const ROW_HEIGHT = 32

const chartPatterns = computed(() => patterns.value.slice(0, MAX_CHART_ROWS))

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !chartPatterns.value.length) return

  const data = chartPatterns.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const allRounds = [...new Set(props.actions.map(a => a.round_num).filter(r => r != null))].sort((a, b) => a - b)
  if (allRounds.length < 2) return

  const margin = { top: 12, right: 16, bottom: 28, left: Math.min(160, containerWidth * 0.25) }
  const width = containerWidth - margin.left - margin.right
  const height = data.length * ROW_HEIGHT
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // X scale
  const x = d3.scaleLinear()
    .domain([allRounds[0], allRounds[allRounds.length - 1]])
    .range([0, width])

  // Vertical grid lines
  const step = Math.max(1, Math.floor(allRounds.length / 10))
  const gridRounds = allRounds.filter((_, i) => i % step === 0 || i === allRounds.length - 1)

  g.selectAll('.grid-line')
    .data(gridRounds)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // X-axis labels
  g.selectAll('.x-label')
    .data(gridRounds)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d}`)

  // Alternating row backgrounds
  g.selectAll('.row-bg')
    .data(data)
    .join('rect')
    .attr('x', -margin.left)
    .attr('y', (_, i) => i * ROW_HEIGHT)
    .attr('width', containerWidth)
    .attr('height', ROW_HEIGHT)
    .attr('fill', (_, i) => i % 2 === 0 ? 'transparent' : 'rgba(0,0,0,0.02)')

  // Row labels (truncated agent name)
  g.selectAll('.row-label')
    .data(data)
    .join('text')
    .attr('x', -8)
    .attr('y', (_, i) => i * ROW_HEIGHT + ROW_HEIGHT / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text, #050505)')
    .text(d => {
      const name = d.agent.split(',')[0].trim()
      return name.length > 18 ? name.slice(0, 16) + '\u2026' : name
    })

  // Pattern motif lines and dots
  data.forEach((pattern, i) => {
    const cy = i * ROW_HEIGHT + ROW_HEIGHT / 2
    const color = TYPE_COLORS[pattern.type] || '#2068FF'
    const rounds = pattern.rounds.filter(r => r != null).sort((a, b) => a - b)
    if (!rounds.length) return

    // Connecting line between first and last occurrence
    if (rounds.length >= 2) {
      g.append('line')
        .attr('x1', x(rounds[0]))
        .attr('x2', x(rounds[rounds.length - 1]))
        .attr('y1', cy)
        .attr('y2', cy)
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.2)
    }

    // Dots at each active round
    g.selectAll(null)
      .data(rounds)
      .join('circle')
      .attr('cx', d => x(d))
      .attr('cy', cy)
      .attr('r', 0)
      .attr('fill', color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .transition()
      .duration(300)
      .delay((_, j) => i * 80 + j * 25)
      .attr('r', 4)
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
    .style('max-width', '260px')

  // Invisible hover targets per row
  g.selectAll('.hover-row')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', (_, i) => i * ROW_HEIGHT)
    .attr('width', width)
    .attr('height', ROW_HEIGHT)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const color = TYPE_COLORS[d.type] || '#2068FF'
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">${d.agent.split(',')[0].trim()}</div>
          <div style="color:${color};font-size:11px;margin-bottom:4px">${d.description}</div>
          <div style="color:var(--color-text-muted,#888);font-size:11px">
            ${d.frequency} occurrences &middot; ${Math.round(d.consistency * 100)}% consistent
          </div>
        `)
        .style('opacity', 1)
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
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Behavior Patterns</h3>
      <span v-if="patterns.length" class="text-xs text-[var(--color-text-muted)]">
        {{ patterns.length }} pattern{{ patterns.length === 1 ? '' : 's' }} detected
      </span>
    </div>

    <!-- D3 Pattern Timeline -->
    <div
      v-if="chartPatterns.length"
      class="relative"
      ref="chartRef"
      :style="{ height: `${chartPatterns.length * ROW_HEIGHT + 40}px` }"
    />

    <div v-else class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm">
      <span>Patterns will emerge as agents interact across rounds</span>
    </div>

    <!-- Legend -->
    <div v-if="chartPatterns.length" class="flex flex-wrap items-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#2068FF]" /> Engagement
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#ff5600]" /> Sentiment
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#009900]" /> Platform
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#AA00FF]" /> Interaction
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#e6194B]" /> Escalation
      </span>
    </div>

    <!-- Summary Table -->
    <div v-if="patterns.length" class="mt-5 border-t border-[var(--color-border)] pt-4">
      <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Pattern Summary</h4>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <th class="py-2 pr-4 font-medium">Agent</th>
              <th class="py-2 pr-4 font-medium">Pattern</th>
              <th class="py-2 pr-4 font-medium text-right">Frequency</th>
              <th class="py-2 font-medium text-right">Consistency</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(p, i) in patterns.slice(0, 12)"
              :key="i"
              class="border-b border-[var(--color-border)] last:border-0"
            >
              <td class="py-2 pr-4 font-medium text-[var(--color-text)]">
                {{ p.agent.split(',')[0].trim() }}
              </td>
              <td class="py-2 pr-4 text-[var(--color-text-secondary)]">
                {{ p.description }}
              </td>
              <td class="py-2 pr-4 text-right text-[var(--color-text)]">
                {{ p.frequency }}
              </td>
              <td class="py-2 text-right">
                <div class="flex items-center justify-end gap-2">
                  <div class="w-16 h-1.5 bg-[var(--color-tint)] rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :class="p.consistency > 0.8 ? 'bg-[#009900]' : p.consistency > 0.5 ? 'bg-[#2068FF]' : 'bg-[#ff5600]'"
                      :style="{ width: `${Math.round(p.consistency * 100)}%` }"
                    />
                  </div>
                  <span class="text-[var(--color-text-muted)] w-8 text-right">
                    {{ Math.round(p.consistency * 100) }}%
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
