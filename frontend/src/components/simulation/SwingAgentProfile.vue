<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  agent: { type: Object, default: null },
  coalitionData: { type: Array, default: () => [] },
  totalRounds: { type: Number, default: 10 },
})

const emit = defineEmits(['go-to-round'])

const timelineRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Coalition definitions ---

const COALITIONS = [
  { id: 'advocates', label: 'Advocates', color: '#2068FF' },
  { id: 'skeptics', label: 'Skeptics', color: '#ff5600' },
  { id: 'evaluators', label: 'Evaluators', color: '#f59e0b' },
  { id: 'champions', label: 'Champions', color: '#009900' },
]

const COALITION_MAP = Object.fromEntries(COALITIONS.map(c => [c.id, c]))

// --- Deterministic seeding ---

function hashCode(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

function seededPick(arr, seed) {
  return arr[seed % arr.length]
}

// --- Demo data generation ---

const agentInfo = computed(() => {
  if (props.agent) return props.agent
  return {
    id: 'demo-swing-1',
    name: 'Sarah Chen',
    role: 'VP of Engineering',
    company: 'Acme Corp',
    personality: 'Analytical',
  }
})

const initial = computed(() => (agentInfo.value.name || '?')[0].toUpperCase())

const coalitionHistory = computed(() => {
  if (props.coalitionData.length) return props.coalitionData

  const seed = hashCode(agentInfo.value.name || 'demo')
  const rounds = props.totalRounds
  const history = []

  // Generate a realistic coalition journey with 1-3 switches
  const switchCount = 1 + (seed % 3)
  const switchRounds = []
  for (let i = 0; i < switchCount; i++) {
    switchRounds.push(Math.floor(rounds * (0.2 + (i * 0.3) + ((seed >> (i + 1)) % 10) * 0.02)))
  }
  switchRounds.sort((a, b) => a - b)

  // Pick coalitions — ensure switches actually change coalition
  const coalitionIds = COALITIONS.map(c => c.id)
  let currentCoalition = seededPick(coalitionIds, seed)

  for (let r = 1; r <= rounds; r++) {
    if (switchRounds.includes(r)) {
      const remaining = coalitionIds.filter(c => c !== currentCoalition)
      currentCoalition = seededPick(remaining, seed + r)
    }
    history.push({ round: r, coalition: currentCoalition })
  }
  return history
})

// --- Derived data ---

const switchPoints = computed(() => {
  const switches = []
  for (let i = 1; i < coalitionHistory.value.length; i++) {
    const prev = coalitionHistory.value[i - 1]
    const curr = coalitionHistory.value[i]
    if (prev.coalition !== curr.coalition) {
      switches.push({
        round: curr.round,
        from: prev.coalition,
        to: curr.coalition,
        fromLabel: COALITION_MAP[prev.coalition]?.label || prev.coalition,
        toLabel: COALITION_MAP[curr.coalition]?.label || curr.coalition,
        fromColor: COALITION_MAP[prev.coalition]?.color || '#888',
        toColor: COALITION_MAP[curr.coalition]?.color || '#888',
      })
    }
  }
  return switches
})

const coalitionSegments = computed(() => {
  if (!coalitionHistory.value.length) return []

  const segments = []
  let current = coalitionHistory.value[0]
  let start = current.round

  for (let i = 1; i < coalitionHistory.value.length; i++) {
    const entry = coalitionHistory.value[i]
    if (entry.coalition !== current.coalition) {
      segments.push({
        coalition: current.coalition,
        startRound: start,
        endRound: coalitionHistory.value[i - 1].round,
        color: COALITION_MAP[current.coalition]?.color || '#888',
        label: COALITION_MAP[current.coalition]?.label || current.coalition,
      })
      current = entry
      start = entry.round
    }
  }
  // Final segment
  segments.push({
    coalition: current.coalition,
    startRound: start,
    endRound: coalitionHistory.value[coalitionHistory.value.length - 1].round,
    color: COALITION_MAP[current.coalition]?.color || '#888',
    label: COALITION_MAP[current.coalition]?.label || current.coalition,
  })
  return segments
})

const influenceData = computed(() => {
  const seed = hashCode(agentInfo.value.name || 'demo')
  const influenced = 1 + (seed % 4)
  const total = 3 + (seed % 8)
  return {
    agentsInfluenced: influenced,
    totalSwingAgents: total,
    influenceScore: Math.round((influenced / total) * 100),
    direction: influenced > total / 2 ? 'high' : 'moderate',
  }
})

const keyMoments = computed(() => {
  const seed = hashCode(agentInfo.value.name || 'demo')
  const MOMENT_TEMPLATES = [
    { verb: 'Shared', object: 'competitive analysis data with the group' },
    { verb: 'Challenged', object: 'the incumbent vendor\'s pricing model' },
    { verb: 'Referenced', object: 'a peer company\'s successful migration' },
    { verb: 'Raised concerns', object: 'about integration timeline risks' },
    { verb: 'Endorsed', object: 'the pilot program proposal' },
    { verb: 'Questioned', object: 'ROI projections in the business case' },
    { verb: 'Presented', object: 'customer feedback data supporting the switch' },
    { verb: 'Cited', object: 'security compliance requirements as a blocker' },
  ]

  return switchPoints.value.map((sp, idx) => {
    const template = MOMENT_TEMPLATES[(seed + idx * 3) % MOMENT_TEMPLATES.length]
    return {
      round: sp.round,
      from: sp.from,
      to: sp.to,
      fromLabel: sp.fromLabel,
      toLabel: sp.toLabel,
      fromColor: sp.fromColor,
      toColor: sp.toColor,
      message: `${template.verb} ${template.object}`,
      impact: (seed + idx) % 3 === 0 ? 'high' : 'moderate',
    }
  })
})

// --- D3 timeline rendering ---

function clearChart() {
  if (timelineRef.value) {
    d3.select(timelineRef.value).selectAll('*').remove()
  }
}

function renderTimeline() {
  clearChart()
  const container = timelineRef.value
  if (!container || !coalitionHistory.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 8, right: 16, bottom: 28, left: 16 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 32
  const height = barHeight
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const rounds = coalitionHistory.value
  const x = d3.scaleLinear()
    .domain([rounds[0].round, rounds[rounds.length - 1].round])
    .range([0, width])

  const segmentWidth = (r) => {
    const totalRoundSpan = rounds[rounds.length - 1].round - rounds[0].round
    if (totalRoundSpan === 0) return width
    return width / totalRoundSpan
  }

  // Coalition segments as colored bars
  g.selectAll('.segment')
    .data(coalitionSegments.value)
    .join('rect')
    .attr('x', d => x(d.startRound) - segmentWidth() / 2)
    .attr('y', 0)
    .attr('width', d => (d.endRound - d.startRound + 1) * segmentWidth())
    .attr('height', barHeight)
    .attr('rx', 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.2)
    .transition()
    .duration(500)
    .delay((_, i) => i * 100)
    .attr('opacity', 0.25)

  // Segment label text
  g.selectAll('.segment-label')
    .data(coalitionSegments.value.filter(d => (d.endRound - d.startRound + 1) >= 2))
    .join('text')
    .attr('x', d => x((d.startRound + d.endRound) / 2))
    .attr('y', barHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', d => d.color)
    .text(d => d.label)
    .style('opacity', 0)
    .transition()
    .duration(400)
    .delay(300)
    .style('opacity', 1)

  // Switch point markers (diamond icons)
  const switchData = switchPoints.value
  if (switchData.length) {
    g.selectAll('.switch-marker')
      .data(switchData)
      .join('g')
      .attr('class', 'switch-marker')
      .attr('transform', d => `translate(${x(d.round)},${barHeight / 2})`)
      .each(function (d) {
        const group = d3.select(this)
        // Diamond shape
        group.append('path')
          .attr('d', d3.symbol().type(d3.symbolDiamond).size(120))
          .attr('fill', '#fff')
          .attr('stroke', d.toColor)
          .attr('stroke-width', 2)
          .style('opacity', 0)
          .transition()
          .duration(300)
          .delay(600)
          .style('opacity', 1)
      })
  }

  // X-axis round labels
  const labelStep = Math.max(1, Math.floor(rounds.length / 10))
  g.selectAll('.x-label')
    .data(rounds.filter((_, i) => i % labelStep === 0 || i === rounds.length - 1))
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', barHeight + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round}`)

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

  // Hover targets per round
  g.selectAll('.hover-target')
    .data(rounds)
    .join('rect')
    .attr('x', d => x(d.round) - segmentWidth() / 2)
    .attr('y', 0)
    .attr('width', segmentWidth())
    .attr('height', barHeight)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const coal = COALITION_MAP[d.coalition]
      const isSwitch = switchData.some(s => s.round === d.round)
      const switchInfo = switchData.find(s => s.round === d.round)
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${d.round}</div>
          <div style="display:flex;align-items:center;gap:6px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${coal?.color || '#888'}"></span>
            <span style="color:${coal?.color || '#888'};font-weight:600">${coal?.label || d.coalition}</span>
          </div>
          ${isSwitch ? `<div style="color:var(--color-fin-orange,#ff5600);margin-top:4px;font-size:11px">&#9670; Switched from ${switchInfo.fromLabel}</div>` : ''}
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 50}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
    })
    .on('click', (event, d) => {
      emit('go-to-round', d.round)
    })
}

// --- Lifecycle ---

watch([() => props.coalitionData.length, () => props.totalRounds], () => {
  nextTick(() => renderTimeline())
})

onMounted(() => {
  renderTimeline()
  if (timelineRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderTimeline, 200)
    })
    resizeObserver.observe(timelineRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Agent Header -->
    <div class="p-5 border-b border-[var(--color-border)]">
      <div class="flex items-start gap-4">
        <div
          class="w-11 h-11 rounded-full flex items-center justify-center text-white font-semibold text-base shrink-0"
          :style="{ background: COALITION_MAP[coalitionHistory[coalitionHistory.length - 1]?.coalition]?.color || 'var(--color-primary)' }"
        >
          {{ initial }}
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-base font-semibold text-[var(--color-text)] truncate">{{ agentInfo.name }}</h3>
          <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
            {{ agentInfo.role }}
            <span v-if="agentInfo.company"> @ {{ agentInfo.company }}</span>
          </p>
          <div class="flex items-center gap-2 mt-2">
            <span
              v-if="agentInfo.personality"
              class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-[var(--color-accent-tint)] text-[var(--color-accent)]"
            >
              {{ agentInfo.personality }}
            </span>
            <span class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]">
              Swing Agent &middot; {{ switchPoints.length }} switch{{ switchPoints.length !== 1 ? 'es' : '' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Coalition Journey Summary -->
    <div class="px-5 py-4 border-b border-[var(--color-border)]">
      <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Coalition Journey</h4>
      <div class="flex items-center gap-1.5 flex-wrap">
        <template v-for="(seg, idx) in coalitionSegments" :key="idx">
          <span
            class="text-[11px] font-medium px-2.5 py-1 rounded-full"
            :style="{ background: seg.color + '18', color: seg.color }"
          >
            {{ seg.label }}
            <span class="opacity-60">R{{ seg.startRound }}{{ seg.startRound !== seg.endRound ? `–${seg.endRound}` : '' }}</span>
          </span>
          <span v-if="idx < coalitionSegments.length - 1" class="text-[var(--color-text-muted)] text-xs">&rarr;</span>
        </template>
      </div>
    </div>

    <!-- D3 Timeline -->
    <div class="px-5 py-4 border-b border-[var(--color-border)]">
      <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Membership Timeline</h4>
      <div
        v-if="coalitionHistory.length"
        ref="timelineRef"
        class="relative"
        style="height: 68px"
      />
      <div v-else class="flex items-center justify-center h-16 text-[var(--color-text-muted)] text-sm">
        No coalition data available
      </div>
      <!-- Legend -->
      <div v-if="coalitionHistory.length" class="flex items-center gap-4 mt-2 text-xs text-[var(--color-text-muted)]">
        <span
          v-for="coal in COALITIONS.filter(c => coalitionHistory.some(h => h.coalition === c.id))"
          :key="coal.id"
          class="flex items-center gap-1.5"
        >
          <span class="inline-block w-2 h-2 rounded-full" :style="{ background: coal.color }" />
          {{ coal.label }}
        </span>
        <span class="flex items-center gap-1.5 ml-auto">
          <span class="text-[var(--color-text-muted)]">&#9670;</span> Switch point
        </span>
      </div>
    </div>

    <!-- Influence Analysis -->
    <div class="px-5 py-4 border-b border-[var(--color-border)]">
      <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Influence Analysis</h4>
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-[var(--color-tint)] rounded-lg p-3 text-center">
          <div class="text-lg font-semibold text-[var(--color-text)]">{{ influenceData.agentsInfluenced }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Agents Influenced</div>
        </div>
        <div class="bg-[rgba(32,104,255,0.06)] rounded-lg p-3 text-center">
          <div class="text-lg font-semibold text-[var(--color-primary)]">{{ influenceData.totalSwingAgents }}</div>
          <div class="text-[10px] text-[var(--color-primary)]">Total Swing</div>
        </div>
        <div class="rounded-lg p-3 text-center" :class="influenceData.direction === 'high' ? 'bg-[rgba(0,153,0,0.06)]' : 'bg-[rgba(245,158,11,0.06)]'">
          <div class="text-lg font-semibold" :style="{ color: influenceData.direction === 'high' ? 'var(--color-success)' : 'var(--color-warning)' }">
            {{ influenceData.influenceScore }}%
          </div>
          <div class="text-[10px]" :style="{ color: influenceData.direction === 'high' ? 'var(--color-success)' : 'var(--color-warning)' }">
            Influence Score
          </div>
        </div>
      </div>
    </div>

    <!-- Key Moments -->
    <div class="px-5 py-4">
      <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Key Moments</h4>
      <div v-if="keyMoments.length" class="space-y-3">
        <div
          v-for="(moment, idx) in keyMoments"
          :key="idx"
          class="flex items-start gap-3 group cursor-pointer"
          @click="emit('go-to-round', moment.round)"
        >
          <!-- Round indicator -->
          <div class="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-semibold border-2"
            :style="{ borderColor: moment.toColor, color: moment.toColor }"
          >
            R{{ moment.round }}
          </div>
          <div class="flex-1 min-w-0">
            <!-- Switch badge -->
            <div class="flex items-center gap-1.5 mb-1">
              <span class="text-[11px] font-medium px-1.5 py-0.5 rounded" :style="{ background: moment.fromColor + '18', color: moment.fromColor }">
                {{ moment.fromLabel }}
              </span>
              <span class="text-[var(--color-text-muted)] text-xs">&rarr;</span>
              <span class="text-[11px] font-medium px-1.5 py-0.5 rounded" :style="{ background: moment.toColor + '18', color: moment.toColor }">
                {{ moment.toLabel }}
              </span>
              <span
                v-if="moment.impact === 'high'"
                class="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-[var(--color-error-light)] text-[var(--color-error)] ml-auto"
              >
                High Impact
              </span>
            </div>
            <!-- Message -->
            <p class="text-xs text-[var(--color-text-secondary)] group-hover:text-[var(--color-text)] transition-colors">
              {{ moment.message }}
            </p>
            <p class="text-[10px] text-[var(--color-primary)] mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
              View round messages &rarr;
            </p>
          </div>
        </div>
      </div>
      <div v-else class="text-sm text-[var(--color-text-muted)] text-center py-4">
        No coalition switches detected
      </div>
    </div>
  </div>
</template>
