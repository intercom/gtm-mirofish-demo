<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  scorecard: { type: Object, default: null },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  amber: '#FFB800',
  text: '#050505',
  muted: '#888888',
}

const MEDAL_COLORS = ['#FFD700', '#C0C0C0', '#CD7F32']

function generateMockScorecard() {
  return {
    topic: 'Should we prioritize retention over acquisition?',
    format: 'oxford',
    overallScore: 7.8,
    winner: 'For',
    agents: [
      {
        id: 1,
        name: 'Sarah Chen',
        role: 'VP of Support',
        team: 'For',
        scores: { argumentQuality: 8.5, rebuttalEffectiveness: 7.8, persuasionScore: 9.1, overall: 8.5 },
        arguments: [
          { text: 'Our Fin pilot showed a 47% resolution rate — proof that AI-first support scales retention without scaling headcount.', score: 9.1, round: 'opening' },
          { text: 'Zendesk\'s own data shows acquisition costs 5x more than retention. Why chase new logos when existing ones churn?', score: 8.2, round: 'rebuttal' },
        ],
      },
      {
        id: 2,
        name: 'Marcus Rivera',
        role: 'CX Director',
        team: 'Against',
        scores: { argumentQuality: 7.9, rebuttalEffectiveness: 8.4, persuasionScore: 7.6, overall: 8.0 },
        arguments: [
          { text: 'Without new pipeline, the retention pool shrinks year over year. You can\'t retain customers you never acquired.', score: 8.4, round: 'opening' },
          { text: 'The market is shifting — competitors are outspending us 3:1 on acquisition. Standing still means falling behind.', score: 7.5, round: 'rebuttal' },
        ],
      },
      {
        id: 3,
        name: 'Priya Sharma',
        role: 'Head of Operations',
        team: 'For',
        scores: { argumentQuality: 7.4, rebuttalEffectiveness: 6.9, persuasionScore: 8.2, overall: 7.5 },
        arguments: [
          { text: 'Operational efficiency gains from retention focus compound quarterly. Our NPS is already trending up 12 points.', score: 7.8, round: 'opening' },
          { text: 'Acquisition without solid onboarding creates support debt. Fix the foundation first.', score: 7.1, round: 'rebuttal' },
        ],
      },
      {
        id: 4,
        name: 'David Kim',
        role: 'CFO',
        team: 'Against',
        scores: { argumentQuality: 7.1, rebuttalEffectiveness: 7.3, persuasionScore: 6.5, overall: 7.0 },
        arguments: [
          { text: 'Board expectations are tied to growth metrics, not retention. We need 40% YoY ARR growth to hit Series C targets.', score: 7.6, round: 'opening' },
          { text: 'Retention ROI is slower to materialize. The Q4 pipeline gap demands immediate acquisition investment.', score: 6.8, round: 'rebuttal' },
        ],
      },
      {
        id: 5,
        name: 'Elena Voss',
        role: 'IT Leader',
        team: 'For',
        scores: { argumentQuality: 6.8, rebuttalEffectiveness: 6.2, persuasionScore: 7.0, overall: 6.7 },
        arguments: [
          { text: 'Integration stability matters more than feature velocity. Retention-focused roadmaps reduce technical debt.', score: 6.9, round: 'opening' },
          { text: 'Every new customer acquired without proper infrastructure is a future support escalation.', score: 6.6, round: 'rebuttal' },
        ],
      },
    ],
    opinionChanges: [
      { agentName: 'David Kim', from: 'Against', to: 'Neutral', triggerAgent: 'Sarah Chen', round: 3 },
    ],
    bestMoment: {
      agentName: 'Sarah Chen',
      text: 'Our Fin pilot showed a 47% resolution rate — proof that AI-first support scales retention without scaling headcount.',
      score: 9.1,
      round: 'opening',
    },
  }
}

const data = computed(() => props.scorecard || generateMockScorecard())

const rankedAgents = computed(() =>
  [...data.value.agents].sort((a, b) => b.scores.overall - a.scores.overall)
)

const qualityLabel = computed(() => {
  const s = data.value.overallScore
  if (s >= 8.5) return 'Excellent'
  if (s >= 7) return 'Good'
  if (s >= 5) return 'Fair'
  return 'Needs Improvement'
})

const qualityColor = computed(() => {
  const s = data.value.overallScore
  if (s >= 8.5) return COLORS.green
  if (s >= 7) return COLORS.primary
  if (s >= 5) return COLORS.amber
  return COLORS.orange
})

function medalIcon(rank) {
  if (rank === 0) return '\uD83E\uDD47'
  if (rank === 1) return '\uD83E\uDD48'
  if (rank === 2) return '\uD83E\uDD49'
  return null
}

function teamBadgeClass(team) {
  return team === 'For'
    ? 'bg-[var(--color-primary-light)] text-[var(--color-primary)]'
    : 'bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]'
}

function scoreBarColor(index) {
  const palette = [COLORS.primary, COLORS.orange, COLORS.green, COLORS.purple, COLORS.amber]
  return palette[index % palette.length]
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function renderArgumentChart() {
  const container = chartRef.value
  if (!container) return
  clearChart()

  const agents = rankedAgents.value
  const allArgs = agents.flatMap((a, i) =>
    a.arguments.map(arg => ({ agent: a.name, score: arg.score, round: arg.round, color: scoreBarColor(i) }))
  )

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 48, right: 60, bottom: 24, left: 120 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 28
  const barGap = 6
  const height = allArgs.length * (barHeight + barGap) - barGap
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 20)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Argument Quality Scores')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 36)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Per-argument score breakdown by agent')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear().domain([0, 10]).range([0, width])

  // Grid lines
  g.selectAll('.grid-line')
    .data([0, 2, 4, 6, 8, 10])
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // X-axis labels
  g.selectAll('.x-label')
    .data([0, 2, 4, 6, 8, 10])
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => d)

  // Labels
  g.selectAll('.bar-label')
    .data(allArgs)
    .join('text')
    .attr('x', -8)
    .attr('y', (d, i) => i * (barHeight + barGap) + barHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text(d => `${d.agent} (${d.round})`)

  // Bar backgrounds
  g.selectAll('.bar-bg')
    .data(allArgs)
    .join('rect')
    .attr('x', 0)
    .attr('y', (d, i) => i * (barHeight + barGap))
    .attr('width', width)
    .attr('height', barHeight)
    .attr('rx', 4)
    .attr('fill', 'rgba(0,0,0,0.03)')

  // Bars with animation
  g.selectAll('.bar')
    .data(allArgs)
    .join('rect')
    .attr('x', 0)
    .attr('y', (d, i) => i * (barHeight + barGap))
    .attr('width', 0)
    .attr('height', barHeight)
    .attr('rx', 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => i * 60)
    .ease(d3.easeCubicOut)
    .attr('width', d => x(d.score))

  // Value labels
  g.selectAll('.bar-value')
    .data(allArgs)
    .join('text')
    .attr('x', d => x(d.score) + 8)
    .attr('y', (d, i) => i * (barHeight + barGap) + barHeight / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .style('opacity', 0)
    .text(d => d.score.toFixed(1))
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 60)
    .style('opacity', 1)
}

watch(() => props.scorecard, () => {
  nextTick(() => renderArgumentChart())
}, { deep: true })

onMounted(() => {
  nextTick(() => renderArgumentChart())

  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => renderArgumentChart(), 200)
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
  <div class="space-y-6">

    <!-- Overall Debate Quality -->
    <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-6" style="box-shadow: var(--card-shadow)">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-lg font-semibold text-[var(--color-text)]">Debate Scorecard</h2>
          <p class="text-sm text-[var(--color-text-muted)] mt-1">{{ data.topic }}</p>
          <div class="flex items-center gap-2 mt-2">
            <span class="text-xs font-medium px-2.5 py-1 rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)]">
              {{ data.format.charAt(0).toUpperCase() + data.format.slice(1) }} Format
            </span>
            <span class="text-xs font-medium px-2.5 py-1 rounded-full bg-[var(--color-success-light)] text-[var(--color-success)]">
              Winner: {{ data.winner }}
            </span>
          </div>
        </div>
        <div class="flex flex-col items-center">
          <div class="relative w-20 h-20">
            <svg viewBox="0 0 80 80" class="w-full h-full -rotate-90">
              <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="6" />
              <circle
                cx="40" cy="40" r="34" fill="none"
                :stroke="qualityColor"
                stroke-width="6"
                stroke-linecap="round"
                :stroke-dasharray="`${(data.overallScore / 10) * 213.6} 213.6`"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-xl font-bold text-[var(--color-text)]">{{ data.overallScore }}</span>
              <span class="text-[9px] text-[var(--color-text-muted)]">/10</span>
            </div>
          </div>
          <span class="text-xs font-medium mt-1" :style="{ color: qualityColor }">{{ qualityLabel }}</span>
        </div>
      </div>
    </div>

    <!-- Ranked Agent List -->
    <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-6" style="box-shadow: var(--card-shadow)">
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Agent Rankings</h3>
      <div class="space-y-3">
        <div
          v-for="(agent, idx) in rankedAgents"
          :key="agent.id"
          class="flex items-center gap-3 p-3 rounded-lg border border-transparent transition-colors"
          :class="idx < 3 ? 'bg-[var(--color-primary-lighter)] border-[var(--color-primary-light)]' : 'bg-[var(--color-tint)]'"
        >
          <!-- Rank -->
          <div class="w-8 h-8 flex items-center justify-center shrink-0">
            <span v-if="medalIcon(idx)" class="text-xl">{{ medalIcon(idx) }}</span>
            <span v-else class="text-sm font-semibold text-[var(--color-text-muted)]">#{{ idx + 1 }}</span>
          </div>

          <!-- Agent info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-[var(--color-text)]">{{ agent.name }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="teamBadgeClass(agent.team)">
                {{ agent.team }}
              </span>
            </div>
            <span class="text-xs text-[var(--color-text-muted)]">{{ agent.role }}</span>
          </div>

          <!-- Score breakdown -->
          <div class="hidden sm:flex items-center gap-4">
            <div class="text-center">
              <div class="text-xs text-[var(--color-text-muted)]">Argument</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ agent.scores.argumentQuality.toFixed(1) }}</div>
            </div>
            <div class="text-center">
              <div class="text-xs text-[var(--color-text-muted)]">Rebuttal</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ agent.scores.rebuttalEffectiveness.toFixed(1) }}</div>
            </div>
            <div class="text-center">
              <div class="text-xs text-[var(--color-text-muted)]">Persuasion</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ agent.scores.persuasionScore.toFixed(1) }}</div>
            </div>
          </div>

          <!-- Overall score -->
          <div class="text-right shrink-0">
            <div class="text-lg font-bold" :style="{ color: scoreBarColor(idx) }">
              {{ agent.scores.overall.toFixed(1) }}
            </div>
            <div class="text-[10px] text-[var(--color-text-muted)]">overall</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Argument Quality Chart (D3) -->
    <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-6" style="box-shadow: var(--card-shadow)">
      <div ref="chartRef" class="w-full" />
    </div>

    <!-- Opinion Change Tracker + Best Moment (side by side) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Opinion Change Tracker -->
      <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-6" style="box-shadow: var(--card-shadow)">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Opinion Changes</h3>
        <div v-if="data.opinionChanges.length" class="space-y-3">
          <div
            v-for="(change, idx) in data.opinionChanges"
            :key="idx"
            class="flex items-start gap-3 p-3 rounded-lg bg-[var(--color-tint)]"
          >
            <div class="w-8 h-8 rounded-full bg-[var(--color-accent-tint)] flex items-center justify-center shrink-0">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
            </div>
            <div>
              <p class="text-sm text-[var(--color-text)]">
                <span class="font-semibold">{{ change.agentName }}</span>
                shifted from
                <span class="font-medium text-[var(--color-fin-orange)]">{{ change.from }}</span>
                to
                <span class="font-medium text-[var(--color-primary)]">{{ change.to }}</span>
              </p>
              <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
                Influenced by {{ change.triggerAgent }} &middot; Round {{ change.round }}
              </p>
            </div>
          </div>
        </div>
        <div v-else class="flex flex-col items-center justify-center py-8 text-[var(--color-text-muted)]">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mb-2 opacity-40">
            <circle cx="12" cy="12" r="10" />
            <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
          </svg>
          <p class="text-sm">No opinion changes detected</p>
          <p class="text-xs mt-0.5">All agents held their positions throughout</p>
        </div>
      </div>

      <!-- Best Moment Highlight -->
      <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-6" style="box-shadow: var(--card-shadow)">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Best Moment</h3>
        <div v-if="data.bestMoment" class="relative">
          <div class="absolute -left-1 top-0 bottom-0 w-1 rounded-full bg-[var(--color-primary)]" />
          <div class="pl-4">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-2xl">&#x2B50;</span>
              <div>
                <span class="text-sm font-semibold text-[var(--color-text)]">{{ data.bestMoment.agentName }}</span>
                <span class="text-xs text-[var(--color-text-muted)] ml-1">&middot; {{ data.bestMoment.round }}</span>
              </div>
            </div>
            <blockquote class="text-sm text-[var(--color-text-secondary)] italic leading-relaxed">
              "{{ data.bestMoment.text }}"
            </blockquote>
            <div class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--color-primary-light)]">
              <span class="text-xs font-semibold text-[var(--color-primary)]">Score: {{ data.bestMoment.score.toFixed(1) }}</span>
              <span class="text-xs text-[var(--color-primary)]">/10</span>
            </div>
          </div>
        </div>
        <div v-else class="flex items-center justify-center py-8 text-sm text-[var(--color-text-muted)]">
          No standout moment identified
        </div>
      </div>

    </div>

  </div>
</template>
