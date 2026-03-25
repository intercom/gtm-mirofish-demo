<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  deals: { type: Array, default: () => [] },
  autoPlay: { type: Boolean, default: false },
})

const chartRef = ref(null)
const currentStageIndex = ref(0)
const isPlaying = ref(false)
const selectedDealIndex = ref(0)
const compareMode = ref(false)

let resizeObserver = null
let resizeTimer = null
let playInterval = null
let stageXPositions = []

const STAGE_RADIUS = 9
const PLAY_INTERVAL_MS = 2500

// --- Mock deals for demo mode ---

const MOCK_DEALS = [
  {
    id: 'deal-1',
    name: 'Enterprise Platform',
    company: 'Acme Corp',
    value: 125000,
    outcome: 'won',
    stages: [
      {
        label: 'Lead',
        duration: '2 days',
        events: [
          { type: 'meeting', text: 'Inbound from webinar registration' },
          { type: 'document', text: 'Account research completed' },
        ],
        commentary: 'VP Engineering attended our AI webinar. High-intent signal — downloaded ROI calculator same day.',
      },
      {
        label: 'Discovery',
        duration: '5 days',
        events: [
          { type: 'meeting', text: 'Discovery call with VP Engineering' },
          { type: 'document', text: 'Sent case study (TechCo)' },
        ],
        branchPoints: [{ text: 'Competitor eval (Zendesk)', type: 'risk' }],
        commentary: 'Strong technical fit. VP mentioned Zendesk eval — sent competitive positioning deck.',
      },
      {
        label: 'Demo',
        duration: '3 days',
        events: [
          { type: 'technical', text: 'Live demo with engineering team' },
          { type: 'milestone', text: 'Technical validation passed' },
        ],
        commentary: 'Engineering team impressed with API flexibility. CTO joined for last 15 min — positive signal.',
      },
      {
        label: 'Proposal',
        duration: '4 days',
        events: [
          { type: 'document', text: 'Proposal sent — $125K/year' },
          { type: 'document', text: 'ROI analysis delivered' },
        ],
        branchPoints: [{ text: 'Budget freeze (Q4)', type: 'risk' }],
        commentary: 'CFO flagged Q4 budget freeze. Champion escalated with ROI data showing 6-month payback.',
      },
      {
        label: 'Negotiation',
        duration: '7 days',
        events: [
          { type: 'meeting', text: 'Negotiation with procurement' },
          { type: 'technical', text: 'Security review completed' },
          { type: 'document', text: 'Contract redlines resolved' },
        ],
        commentary: 'Standard procurement process. Security review added 3 days. Legal redlines on DPA resolved.',
      },
      {
        label: 'Closed Won',
        duration: '1 day',
        events: [
          { type: 'milestone', text: 'Contract signed' },
          { type: 'milestone', text: 'Onboarding kickoff scheduled' },
        ],
        commentary: 'Deal closed at full price. 24-day cycle — 40% faster than average. Champion drove alignment.',
      },
    ],
  },
  {
    id: 'deal-2',
    name: 'Mid-Market Support',
    company: 'GlobalTech Inc',
    value: 48000,
    outcome: 'lost',
    stages: [
      {
        label: 'Lead',
        duration: '1 day',
        events: [{ type: 'meeting', text: 'Outbound sequence reply' }],
        commentary: 'Responded to outbound email. Expressed interest in chat automation specifically.',
      },
      {
        label: 'Discovery',
        duration: '8 days',
        events: [
          { type: 'meeting', text: 'Discovery with Support Manager' },
          { type: 'meeting', text: 'Follow-up with IT Director' },
        ],
        commentary: 'Multi-threaded to IT. Support Manager enthusiastic but IT concerned about integration complexity.',
      },
      {
        label: 'Demo',
        duration: '5 days',
        events: [
          { type: 'technical', text: 'Standard demo' },
          { type: 'risk', text: 'Integration concerns raised' },
        ],
        branchPoints: [{ text: 'Legacy CRM gap', type: 'risk' }],
        commentary: 'Demo went well functionally but surfaced integration gap with their custom Salesforce fork.',
      },
      {
        label: 'Proposal',
        duration: '6 days',
        events: [
          { type: 'document', text: 'Proposal sent — $48K/year' },
          { type: 'technical', text: 'Custom integration scoping' },
        ],
        branchPoints: [{ text: 'Freshdesk bundled pricing', type: 'risk' }],
        commentary: 'Freshdesk came in 30% cheaper with pre-built CRM connector. Champion lost internal leverage.',
      },
      {
        label: 'Closed Lost',
        duration: '\u2014',
        events: [
          { type: 'risk', text: 'Lost to Freshdesk' },
          { type: 'document', text: 'Post-mortem logged' },
        ],
        commentary: 'Lost on integration + price. Key learning: qualify CRM stack earlier in discovery.',
      },
    ],
  },
  {
    id: 'deal-3',
    name: 'Scale-Up Expansion',
    company: 'RapidGrow AI',
    value: 72000,
    outcome: 'won',
    stages: [
      {
        label: 'Lead',
        duration: '1 day',
        events: [{ type: 'meeting', text: 'Referral from existing customer' }],
        commentary: 'Warm intro from TechCo (existing customer). CTO-to-CTO referral — highest quality lead source.',
      },
      {
        label: 'Discovery',
        duration: '3 days',
        events: [
          { type: 'meeting', text: 'Discovery with CTO' },
          { type: 'document', text: 'Shared product roadmap' },
        ],
        commentary: 'CTO already familiar with platform through referral. Fast-tracked with roadmap preview.',
      },
      {
        label: 'Demo',
        duration: '2 days',
        events: [
          { type: 'technical', text: 'Technical deep-dive' },
          { type: 'milestone', text: 'Sandbox access granted' },
        ],
        commentary: 'Hands-on eval instead of demo. Team built a POC in the sandbox within 48 hours.',
      },
      {
        label: 'Proposal',
        duration: '2 days',
        events: [{ type: 'document', text: 'Proposal — $72K/year' }],
        commentary: 'Straightforward pricing discussion. Multi-year discount offered for commitment.',
      },
      {
        label: 'Negotiation',
        duration: '3 days',
        events: [
          { type: 'meeting', text: 'Multi-year terms agreed' },
          { type: 'document', text: 'Legal fast-track' },
        ],
        commentary: 'Used standard enterprise agreement template. No redlines — fastest legal review this quarter.',
      },
      {
        label: 'Closed Won',
        duration: '1 day',
        events: [
          { type: 'milestone', text: '2-year contract signed' },
          { type: 'milestone', text: 'Joint press release planned' },
        ],
        commentary: 'Closed in 12 days — referral deals close 3x faster. Agreed to be reference customer.',
      },
    ],
  },
]

// --- Computed ---

const effectiveDeals = computed(() => (props.deals.length ? props.deals : MOCK_DEALS))
const activeDeal = computed(() => effectiveDeals.value[selectedDealIndex.value])
const activeStage = computed(() => activeDeal.value?.stages[currentStageIndex.value])

function formatValue(v) {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`
  return `$${v}`
}

function eventColor(type) {
  const map = {
    meeting: 'var(--color-primary)',
    document: 'var(--color-success)',
    milestone: 'var(--color-warning)',
    technical: 'var(--color-accent)',
    risk: 'var(--color-fin-orange)',
  }
  return map[type] || 'var(--color-text-muted)'
}

function dealColor(deal) {
  return deal.outcome === 'lost' ? '#ff5600' : '#2068FF'
}

// --- D3 Rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderTimeline() {
  clearChart()
  const container = chartRef.value
  if (!container || !effectiveDeals.value.length) return
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  if (compareMode.value) {
    renderCompare(container, containerWidth)
  } else {
    renderSingle(container, containerWidth)
  }
}

function renderSingle(container, containerWidth) {
  const deal = activeDeal.value
  if (!deal) return
  const stages = deal.stages
  const mainColor = dealColor(deal)
  const idx = currentStageIndex.value

  const margin = { top: 32, right: 32, bottom: 44, left: 32 }
  const width = containerWidth - margin.left - margin.right
  const height = 80
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  // Glow filter for active token
  const defs = svg.append('defs')
  const filter = defs.append('filter').attr('id', 'token-glow')
  filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'blur')
  const merge = filter.append('feMerge')
  merge.append('feMergeNode').attr('in', 'blur')
  merge.append('feMergeNode').attr('in', 'SourceGraphic')

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear().domain([0, stages.length - 1]).range([0, width])
  const y = height / 2
  stageXPositions = stages.map((_, i) => x(i))

  // Background track
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', y).attr('y2', y)
    .attr('stroke', 'var(--color-border)')
    .attr('stroke-width', 2)

  // Filled progress line
  g.append('line')
    .attr('class', 'progress-line')
    .attr('x1', 0).attr('x2', x(idx))
    .attr('y1', y).attr('y2', y)
    .attr('stroke', mainColor)
    .attr('stroke-width', 3)
    .attr('stroke-linecap', 'round')

  // Branch fork lines
  stages.forEach((stage, i) => {
    if (!stage.branchPoints?.length) return
    stage.branchPoints.forEach((bp, j) => {
      const cx = x(i)
      const forkLen = 36
      const angle = Math.PI / 4.5
      const ex = cx + forkLen * Math.cos(angle)
      const ey = y + STAGE_RADIUS + forkLen * Math.sin(angle) + j * 14

      g.append('line')
        .attr('x1', cx).attr('y1', y + STAGE_RADIUS)
        .attr('x2', ex).attr('y2', ey)
        .attr('stroke', '#ff5600')
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '4,3')
        .attr('opacity', 0.45)

      g.append('circle')
        .attr('cx', ex).attr('cy', ey)
        .attr('r', 2.5)
        .attr('fill', '#ff5600')
        .attr('opacity', 0.5)

      g.append('text')
        .attr('x', ex + 6).attr('y', ey + 3)
        .attr('font-size', '9px')
        .attr('fill', '#ff5600')
        .attr('opacity', 0.7)
        .text(bp.text)
    })
  })

  // Stage labels (above)
  g.selectAll('.stage-label')
    .data(stages)
    .join('text')
    .attr('class', 'stage-label')
    .attr('x', (_, i) => x(i))
    .attr('y', y - 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', (_, i) => (i === idx ? '600' : '400'))
    .attr('fill', (_, i) =>
      i === idx ? 'var(--color-text)' : 'var(--color-text-muted)',
    )
    .text((d) => d.label)

  // Duration labels (below)
  g.selectAll('.stage-duration')
    .data(stages)
    .join('text')
    .attr('class', 'stage-duration')
    .attr('x', (_, i) => x(i))
    .attr('y', y + 26)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted)')
    .text((d) => d.duration)

  // Stage nodes
  g.selectAll('.stage-node')
    .data(stages)
    .join('circle')
    .attr('class', 'stage-node')
    .attr('cx', (_, i) => x(i))
    .attr('cy', y)
    .attr('r', STAGE_RADIUS)
    .attr('fill', (d, i) => {
      if (i > idx) return 'var(--color-surface)'
      return d.branchPoints?.length ? '#ff5600' : mainColor
    })
    .attr('stroke', (d, i) => {
      if (i > idx) return 'var(--color-border)'
      return d.branchPoints?.length ? '#ff5600' : mainColor
    })
    .attr('stroke-width', 2)
    .attr('cursor', 'pointer')
    .on('click', (_, d) => goToStage(stages.indexOf(d)))

  // Active token ring
  g.append('circle')
    .attr('class', 'deal-token')
    .attr('cx', x(idx))
    .attr('cy', y)
    .attr('r', 17)
    .attr('fill', 'none')
    .attr('stroke', mainColor)
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '4,4')
    .attr('opacity', 0.7)
    .attr('filter', 'url(#token-glow)')
}

function renderCompare(container, containerWidth) {
  const deals = effectiveDeals.value
  const margin = { top: 28, right: 24, bottom: 16, left: 130 }
  const width = containerWidth - margin.left - margin.right
  const rowHeight = 56
  const totalHeight = margin.top + deals.length * rowHeight + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxStages = Math.max(...deals.map((d) => d.stages.length))
  const x = d3.scaleLinear().domain([0, maxStages - 1]).range([0, width])

  // Column labels at top
  const labels = deals.reduce(
    (longest, d) => (d.stages.length > longest.length ? d.stages : longest),
    [],
  )
  g.selectAll('.col-label')
    .data(labels)
    .join('text')
    .attr('x', (_, i) => x(i))
    .attr('y', -10)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted)')
    .text((d) => d.label)

  deals.forEach((deal, di) => {
    const row = g.append('g').attr('transform', `translate(0,${di * rowHeight})`)
    const y = rowHeight / 2
    const color = dealColor(deal)

    // Deal name label
    svg
      .append('text')
      .attr('x', margin.left - 12)
      .attr('y', margin.top + di * rowHeight + y - 6)
      .attr('text-anchor', 'end')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('fill', 'var(--color-text)')
      .text(deal.company)

    svg
      .append('text')
      .attr('x', margin.left - 12)
      .attr('y', margin.top + di * rowHeight + y + 8)
      .attr('text-anchor', 'end')
      .attr('font-size', '10px')
      .attr('fill', color)
      .text(
        `${formatValue(deal.value)} \u00B7 ${deal.outcome === 'won' ? 'Won' : 'Lost'}`,
      )

    // Track
    row
      .append('line')
      .attr('x1', 0).attr('x2', x(deal.stages.length - 1))
      .attr('y1', y).attr('y2', y)
      .attr('stroke', 'var(--color-border)')
      .attr('stroke-width', 2)

    // Filled line (animated)
    row
      .append('line')
      .attr('x1', 0).attr('x2', 0)
      .attr('y1', y).attr('y2', y)
      .attr('stroke', color)
      .attr('stroke-width', 3)
      .attr('stroke-linecap', 'round')
      .transition()
      .duration(800)
      .delay(di * 200)
      .ease(d3.easeCubicOut)
      .attr('x2', x(deal.stages.length - 1))

    // Stage dots
    deal.stages.forEach((stage, si) => {
      row
        .append('circle')
        .attr('cx', x(si))
        .attr('cy', y)
        .attr('r', 6)
        .attr('fill', stage.branchPoints?.length ? '#ff5600' : color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('cursor', 'pointer')
        .attr('opacity', 0)
        .on('click', () => {
          selectedDealIndex.value = di
          currentStageIndex.value = si
          compareMode.value = false
        })
        .transition()
        .duration(300)
        .delay(di * 200 + si * 60)
        .attr('opacity', 1)
    })
  })
}

function animateToStage(idx) {
  const container = chartRef.value
  if (!container) return
  const deal = activeDeal.value
  if (!deal) return

  const mainColor = dealColor(deal)
  const cx = stageXPositions[idx]
  if (cx == null) return

  const svg = d3.select(container).select('svg')
  if (svg.empty()) return

  // Move token ring
  svg
    .select('.deal-token')
    .transition()
    .duration(500)
    .ease(d3.easeCubicInOut)
    .attr('cx', cx)

  // Extend/retract progress line
  svg
    .select('.progress-line')
    .transition()
    .duration(500)
    .ease(d3.easeCubicInOut)
    .attr('x2', cx)

  // Update stage node fills
  svg
    .selectAll('.stage-node')
    .transition()
    .duration(300)
    .attr('fill', (d, i) => {
      if (i > idx) return 'var(--color-surface)'
      return d.branchPoints?.length ? '#ff5600' : mainColor
    })
    .attr('stroke', (d, i) => {
      if (i > idx) return 'var(--color-border)'
      return d.branchPoints?.length ? '#ff5600' : mainColor
    })

  // Update label emphasis
  svg
    .selectAll('.stage-label')
    .transition()
    .duration(300)
    .attr('font-weight', (_, i) => (i === idx ? '600' : '400'))
    .attr('fill', (_, i) =>
      i === idx ? 'var(--color-text)' : 'var(--color-text-muted)',
    )
}

// --- Playback ---

function play() {
  if (isPlaying.value) return
  isPlaying.value = true
  playInterval = setInterval(() => {
    const max = activeDeal.value.stages.length - 1
    if (currentStageIndex.value >= max) {
      pause()
      return
    }
    currentStageIndex.value++
  }, PLAY_INTERVAL_MS)
}

function pause() {
  isPlaying.value = false
  if (playInterval) {
    clearInterval(playInterval)
    playInterval = null
  }
}

function togglePlay() {
  isPlaying.value ? pause() : play()
}

function goToStage(idx) {
  pause()
  const max = activeDeal.value.stages.length - 1
  currentStageIndex.value = Math.max(0, Math.min(idx, max))
}

function toggleCompare() {
  pause()
  compareMode.value = !compareMode.value
}

// --- Watchers & Lifecycle ---

watch(selectedDealIndex, () => {
  currentStageIndex.value = 0
  pause()
  nextTick(renderTimeline)
})

watch(compareMode, () => {
  nextTick(renderTimeline)
})

watch(currentStageIndex, (newIdx) => {
  if (compareMode.value) return
  const svg = d3.select(chartRef.value)?.select('svg')
  if (!svg || svg.empty()) return
  animateToStage(newIdx)
})

onMounted(() => {
  nextTick(renderTimeline)
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderTimeline, 200)
    })
    resizeObserver.observe(chartRef.value)
  }
  if (props.autoPlay) play()
})

onUnmounted(() => {
  pause()
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg">
    <!-- Header -->
    <div class="flex items-center justify-between p-5 pb-2">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Deal Lifecycle</h3>
        <p v-if="!compareMode && activeDeal" class="text-xs text-[var(--color-text-muted)] mt-0.5">
          {{ activeDeal.company }} &middot; {{ formatValue(activeDeal.value) }}
          <span
            :class="activeDeal.outcome === 'won' ? 'text-[var(--color-success)]' : 'text-[var(--color-fin-orange)]'"
          >
            &middot; {{ activeDeal.outcome === 'won' ? 'Won' : 'Lost' }}
          </span>
        </p>
        <p v-else-if="compareMode" class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Comparing {{ effectiveDeals.length }} deals &middot; Click a stage to inspect
        </p>
      </div>
      <div class="flex items-center gap-1.5">
        <select
          v-if="effectiveDeals.length > 1 && !compareMode"
          :value="selectedDealIndex"
          class="text-xs bg-[var(--color-tint)] border-none rounded px-2 py-1 text-[var(--color-text)] cursor-pointer outline-none"
          @change="selectedDealIndex = Number($event.target.value)"
        >
          <option v-for="(deal, i) in effectiveDeals" :key="deal.id" :value="i">
            {{ deal.company }}
          </option>
        </select>
        <button
          v-if="!compareMode"
          class="px-2.5 py-1 text-[11px] rounded font-medium bg-[var(--color-tint)] text-[var(--color-text)] hover:bg-[var(--color-primary-light)] transition-colors"
          @click="togglePlay"
        >
          {{ isPlaying ? 'Pause' : 'Play' }}
        </button>
        <button
          v-if="effectiveDeals.length > 1"
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="
            compareMode
              ? 'bg-[var(--color-primary-light)] text-[var(--color-primary)]'
              : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
          "
          @click="toggleCompare"
        >
          Compare
        </button>
      </div>
    </div>

    <!-- Main content -->
    <div v-if="effectiveDeals.length" class="flex">
      <!-- SVG Timeline -->
      <div ref="chartRef" class="flex-1 min-w-0" />

      <!-- Side Panel (single-deal mode only) -->
      <div
        v-if="!compareMode && activeStage"
        class="w-64 flex-shrink-0 border-l border-[var(--color-border)] p-4 overflow-y-auto"
      >
        <div class="mb-3">
          <div class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
            Stage {{ currentStageIndex + 1 }} of {{ activeDeal.stages.length }}
          </div>
          <h4 class="text-sm font-semibold text-[var(--color-text)]">{{ activeStage.label }}</h4>
          <div class="text-xs text-[var(--color-text-muted)]">{{ activeStage.duration }}</div>
        </div>

        <!-- Events -->
        <div v-if="activeStage.events?.length" class="mb-3">
          <div class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
            Events
          </div>
          <div
            v-for="ev in activeStage.events"
            :key="ev.text"
            class="flex items-start gap-2 mb-1.5"
          >
            <span
              class="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0"
              :style="{ backgroundColor: eventColor(ev.type) }"
            />
            <span class="text-xs text-[var(--color-text-secondary)]">{{ ev.text }}</span>
          </div>
        </div>

        <!-- Branch Points -->
        <div v-if="activeStage.branchPoints?.length" class="mb-3">
          <div class="text-[10px] font-medium text-[var(--color-fin-orange)] uppercase tracking-wider mb-2">
            Decision Points
          </div>
          <div
            v-for="bp in activeStage.branchPoints"
            :key="bp.text"
            class="flex items-start gap-2 mb-1.5"
          >
            <span class="w-2 h-2 rotate-45 mt-1 flex-shrink-0 bg-[var(--color-fin-orange)] opacity-70" />
            <span class="text-xs text-[var(--color-fin-orange)]">{{ bp.text }}</span>
          </div>
        </div>

        <!-- Commentary -->
        <div v-if="activeStage.commentary" class="pt-3 border-t border-[var(--color-border)]">
          <p class="text-xs italic text-[var(--color-text-muted)] leading-relaxed">
            {{ activeStage.commentary }}
          </p>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else
      class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm"
    >
      No deal lifecycle data available
    </div>
  </div>
</template>
