<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  simulationId: { type: String, default: null },
  actions: { type: Array, default: () => [] },
})

const emit = defineEmits(['analyzed'])

// --- State ---
const selectedRound = ref(null)
const selectedAction = ref(null)
const alternative = ref('')
const loading = ref(false)
const error = ref(null)
const analysis = ref(null)
const impactChartRef = ref(null)

let resizeObserver = null
let resizeTimer = null

// --- Computed: decision points from actions ---
const decisionPoints = computed(() => {
  if (!props.actions.length) return []
  const meaningful = props.actions.filter(a => {
    const type = (a.action_type || '').toUpperCase()
    return type.includes('REPLY') || type.includes('CREATE_POST') || type.includes('COMMENT')
  })
  return meaningful.slice(0, 50)
})

const availableRounds = computed(() => {
  const rounds = new Set(decisionPoints.value.map(a => a.round_num))
  return Array.from(rounds).sort((a, b) => a - b)
})

const roundActions = computed(() => {
  if (selectedRound.value == null) return []
  return decisionPoints.value.filter(a => a.round_num === selectedRound.value)
})

const actionContent = computed(() => {
  if (!selectedAction.value) return ''
  return (selectedAction.value.action_args || {}).content || ''
})

const canAnalyze = computed(() => {
  return selectedAction.value && props.simulationId
})

const isMockData = computed(() => analysis.value?._mock === true)

// --- Methods ---
async function runAnalysis() {
  if (!canAnalyze.value) return

  loading.value = true
  error.value = null
  analysis.value = null

  try {
    const payload = {
      agent_name: selectedAction.value.agent_name || selectedAction.value.agent_id,
      round_num: selectedAction.value.round_num,
      action_type: selectedAction.value.action_type,
      content: actionContent.value,
      alternative: alternative.value || '',
    }
    const res = await simulationApi.analyzeCounterfactual(props.simulationId, payload)
    if (res.data?.success) {
      analysis.value = res.data.data
      emit('analyzed', analysis.value)
      nextTick(() => renderImpactChart())
    } else {
      error.value = res.data?.error || 'Analysis failed'
    }
  } catch (e) {
    error.value = e.message || 'Network error'
  } finally {
    loading.value = false
  }
}

function selectAction(action) {
  selectedAction.value = action
  alternative.value = ''
  analysis.value = null
}

function confidenceColor(val) {
  if (val >= 75) return '#009900'
  if (val >= 50) return '#f59e0b'
  return '#ff5600'
}

function sentimentColor(val) {
  if (val > 0.1) return '#009900'
  if (val < -0.1) return '#ff5600'
  return '#2068FF'
}

function formatSentiment(val) {
  if (val == null) return '—'
  return (val >= 0 ? '+' : '') + val.toFixed(2)
}

// --- D3 Impact Chart ---
function clearChart() {
  if (impactChartRef.value) {
    d3.select(impactChartRef.value).selectAll('*').remove()
  }
}

function renderImpactChart() {
  clearChart()
  if (!impactChartRef.value || !analysis.value) return

  const container = impactChartRef.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const a = analysis.value
  const actual = a.actual_outcome
  const cf = a.counterfactual_outcome

  const metrics = [
    {
      label: 'Sentiment',
      actual: actual.sentiment_impact || 0,
      counterfactual: cf.sentiment_impact || 0,
      domain: [-1, 1],
    },
    {
      label: 'Resolution (rounds)',
      actual: -(actual.rounds_to_resolution || 0),
      counterfactual: -(cf.rounds_to_resolution || 0),
      domain: [-20, 0],
      invert: true,
    },
  ]

  const margin = { top: 16, right: 20, bottom: 24, left: 90 }
  const barHeight = 28
  const groupGap = 20
  const width = containerWidth - margin.left - margin.right
  const height = metrics.length * (barHeight * 2 + groupGap) - groupGap

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', height + margin.top + margin.bottom)
    .attr('viewBox', `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  metrics.forEach((m, i) => {
    const yOffset = i * (barHeight * 2 + groupGap)
    const xScale = d3.scaleLinear()
      .domain(m.domain)
      .range([0, width])
      .clamp(true)

    // Zero line
    const zeroX = xScale(0)
    g.append('line')
      .attr('x1', zeroX).attr('x2', zeroX)
      .attr('y1', yOffset).attr('y2', yOffset + barHeight * 2)
      .attr('stroke', 'rgba(0,0,0,0.1)')
      .attr('stroke-dasharray', '3,3')

    // Label
    g.append('text')
      .attr('x', -8)
      .attr('y', yOffset + barHeight)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '12px')
      .attr('fill', 'var(--color-text, #1a1a1a)')
      .text(m.label)

    const actualVal = m.invert ? m.actual : m.actual
    const cfVal = m.invert ? m.counterfactual : m.counterfactual
    const displayActual = m.invert ? Math.abs(m.actual) : m.actual
    const displayCf = m.invert ? Math.abs(m.counterfactual) : m.counterfactual

    // Actual bar
    const actualWidth = Math.abs(xScale(actualVal) - zeroX)
    const actualX = actualVal >= 0 ? zeroX : zeroX - actualWidth
    g.append('rect')
      .attr('x', actualX)
      .attr('y', yOffset)
      .attr('width', 0)
      .attr('height', barHeight - 2)
      .attr('rx', 4)
      .attr('fill', '#ff5600')
      .attr('opacity', 0.75)
      .transition().duration(600).ease(d3.easeCubicOut)
      .attr('width', actualWidth)

    g.append('text')
      .attr('x', actualX + actualWidth + 6)
      .attr('y', yOffset + (barHeight - 2) / 2)
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '11px')
      .attr('fill', '#ff5600')
      .attr('font-weight', '600')
      .text(m.invert ? `${displayActual} rounds` : formatSentiment(displayActual))
      .style('opacity', 0)
      .transition().delay(400).duration(300)
      .style('opacity', 1)

    // Actual label
    g.append('text')
      .attr('x', actualX - 4)
      .attr('y', yOffset + (barHeight - 2) / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'var(--color-text-muted, #888)')
      .text('Actual')

    // Counterfactual bar
    const cfWidth = Math.abs(xScale(cfVal) - zeroX)
    const cfX = cfVal >= 0 ? zeroX : zeroX - cfWidth
    g.append('rect')
      .attr('x', cfX)
      .attr('y', yOffset + barHeight)
      .attr('width', 0)
      .attr('height', barHeight - 2)
      .attr('rx', 4)
      .attr('fill', '#2068FF')
      .attr('opacity', 0.75)
      .transition().duration(600).delay(200).ease(d3.easeCubicOut)
      .attr('width', cfWidth)

    g.append('text')
      .attr('x', cfX + cfWidth + 6)
      .attr('y', yOffset + barHeight + (barHeight - 2) / 2)
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '11px')
      .attr('fill', '#2068FF')
      .attr('font-weight', '600')
      .text(m.invert ? `${displayCf} rounds` : formatSentiment(displayCf))
      .style('opacity', 0)
      .transition().delay(600).duration(300)
      .style('opacity', 1)

    // CF label
    g.append('text')
      .attr('x', cfX - 4)
      .attr('y', yOffset + barHeight + (barHeight - 2) / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'var(--color-text-muted, #888)')
      .text('What-if')
  })
}

// --- Lifecycle ---
watch(() => analysis.value, (val) => {
  if (val) nextTick(() => renderImpactChart())
})

onMounted(() => {
  if (impactChartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => {
        if (analysis.value) renderImpactChart()
      }, 200)
    })
    resizeObserver.observe(impactChartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center gap-2 mb-4">
      <span class="text-base">&#x2696;</span>
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Counterfactual Analysis</h3>
      <span
        v-if="isMockData"
        class="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]"
      >
        Demo Mode
      </span>
    </div>

    <!-- Step 1: Select decision point -->
    <div v-if="!analysis" class="space-y-3">
      <p class="text-xs text-[var(--color-text-muted)]">
        Select a decision point to explore what would have happened differently.
      </p>

      <!-- Round selector -->
      <div>
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Round</label>
        <div v-if="availableRounds.length" class="flex flex-wrap gap-1.5">
          <button
            v-for="r in availableRounds"
            :key="r"
            class="px-2.5 py-1 text-xs rounded-md border transition-colors"
            :class="selectedRound === r
              ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
              : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]'"
            @click="selectedRound = r; selectedAction = null; analysis = null"
          >
            R{{ r }}
          </button>
        </div>
        <p v-else class="text-xs text-[var(--color-text-muted)] italic">
          No decision points available yet. Run a simulation first.
        </p>
      </div>

      <!-- Action selector -->
      <div v-if="roundActions.length">
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Decision Point</label>
        <div class="space-y-1.5 max-h-48 overflow-y-auto">
          <button
            v-for="(action, idx) in roundActions"
            :key="idx"
            class="w-full text-left p-2.5 rounded-md border text-xs transition-colors"
            :class="selectedAction === action
              ? 'bg-[rgba(32,104,255,0.06)] border-[var(--color-primary)]'
              : 'border-[var(--color-border)] hover:border-[var(--color-primary,#2068FF)] hover:bg-[var(--color-tint)]'"
            @click="selectAction(action)"
          >
            <div class="flex items-center gap-2 mb-0.5">
              <span class="font-medium text-[var(--color-text)]">
                {{ action.agent_name || action.agent_id }}
              </span>
              <span class="px-1.5 py-0.5 rounded bg-[var(--color-tint)] text-[var(--color-text-muted)] text-[10px]">
                {{ action.action_type }}
              </span>
            </div>
            <p class="text-[var(--color-text-muted)] line-clamp-2">
              {{ (action.action_args || {}).content || '(no content)' }}
            </p>
          </button>
        </div>
      </div>

      <!-- Alternative input -->
      <div v-if="selectedAction">
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">
          Alternative scenario <span class="font-normal text-[var(--color-text-muted)]">(optional)</span>
        </label>
        <input
          v-model="alternative"
          type="text"
          placeholder="e.g., 'expressed strong support instead'"
          class="w-full px-3 py-2 text-xs rounded-md border border-[var(--color-border)] bg-[var(--color-surface)]
                 text-[var(--color-text)] placeholder-[var(--color-text-muted)]
                 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-opacity-30
                 focus:border-[var(--color-primary)]"
        />
      </div>

      <!-- Analyze button -->
      <button
        :disabled="!canAnalyze || loading"
        class="w-full py-2 px-4 rounded-md text-xs font-medium transition-colors"
        :class="canAnalyze && !loading
          ? 'bg-[var(--color-primary)] text-white hover:bg-[#1a5ce0] cursor-pointer'
          : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] cursor-not-allowed'"
        @click="runAnalysis"
      >
        <span v-if="loading" class="flex items-center justify-center gap-2">
          <span class="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Analyzing...
        </span>
        <span v-else>Analyze What-If Scenario</span>
      </button>

      <p v-if="error" class="text-xs text-[var(--color-error)]">{{ error }}</p>
    </div>

    <!-- Step 2: Results -->
    <div v-if="analysis" class="space-y-4">
      <!-- Back button -->
      <button
        class="text-xs text-[var(--color-primary)] hover:underline"
        @click="analysis = null"
      >
        &larr; Choose different scenario
      </button>

      <!-- Side-by-side comparison -->
      <div class="grid grid-cols-2 gap-3">
        <!-- Actual outcome -->
        <div class="p-3 rounded-lg border border-[var(--color-border)] bg-[rgba(255,86,0,0.03)]">
          <div class="flex items-center gap-1.5 mb-2">
            <span class="w-2 h-2 rounded-full bg-[#ff5600]" />
            <span class="text-xs font-semibold text-[#ff5600]">What Happened</span>
          </div>
          <p class="text-xs text-[var(--color-text)] leading-relaxed mb-2">
            {{ analysis.actual_outcome.summary }}
          </p>
          <div class="flex items-center gap-3 text-[10px] text-[var(--color-text-muted)]">
            <span :style="{ color: sentimentColor(analysis.actual_outcome.sentiment_impact) }">
              Sentiment: {{ formatSentiment(analysis.actual_outcome.sentiment_impact) }}
            </span>
            <span v-if="analysis.actual_outcome.rounds_to_resolution">
              {{ analysis.actual_outcome.rounds_to_resolution }} rounds
            </span>
          </div>
          <ul class="mt-2 space-y-0.5">
            <li
              v-for="(effect, i) in analysis.actual_outcome.key_effects"
              :key="i"
              class="text-[11px] text-[var(--color-text-muted)] flex gap-1.5"
            >
              <span class="text-[#ff5600] shrink-0">&#x2022;</span>
              {{ effect }}
            </li>
          </ul>
        </div>

        <!-- Counterfactual outcome -->
        <div class="p-3 rounded-lg border border-[var(--color-border)] bg-[rgba(32,104,255,0.03)]">
          <div class="flex items-center gap-1.5 mb-2">
            <span class="w-2 h-2 rounded-full bg-[#2068FF]" />
            <span class="text-xs font-semibold text-[#2068FF]">What Could Have Happened</span>
          </div>
          <p class="text-xs text-[var(--color-text)] leading-relaxed mb-2">
            {{ analysis.counterfactual_outcome.summary }}
          </p>
          <div class="flex items-center gap-3 text-[10px] text-[var(--color-text-muted)]">
            <span :style="{ color: sentimentColor(analysis.counterfactual_outcome.sentiment_impact) }">
              Sentiment: {{ formatSentiment(analysis.counterfactual_outcome.sentiment_impact) }}
            </span>
            <span v-if="analysis.counterfactual_outcome.rounds_to_resolution">
              {{ analysis.counterfactual_outcome.rounds_to_resolution }} rounds
            </span>
          </div>
          <ul class="mt-2 space-y-0.5">
            <li
              v-for="(effect, i) in analysis.counterfactual_outcome.key_effects"
              :key="i"
              class="text-[11px] text-[var(--color-text-muted)] flex gap-1.5"
            >
              <span class="text-[#2068FF] shrink-0">&#x2022;</span>
              {{ effect }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Impact visualization -->
      <div>
        <h4 class="text-xs font-semibold text-[var(--color-text)] mb-2">Impact Comparison</h4>
        <div ref="impactChartRef" class="w-full" style="min-height: 140px" />
        <div class="flex items-center gap-4 mt-1 text-[10px] text-[var(--color-text-muted)]">
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-2 rounded-sm bg-[#ff5600] opacity-75" /> Actual
          </span>
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-2 rounded-sm bg-[#2068FF] opacity-75" /> What-if
          </span>
        </div>
      </div>

      <!-- Narrative + confidence -->
      <div class="p-3 rounded-lg bg-[var(--color-tint)]">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-[var(--color-text)]">Analysis Summary</span>
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] text-[var(--color-text-muted)]">Confidence:</span>
            <span
              class="text-xs font-bold"
              :style="{ color: confidenceColor(analysis.confidence) }"
            >
              {{ analysis.confidence }}%
            </span>
          </div>
        </div>
        <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">
          {{ analysis.narrative }}
        </p>

        <!-- Impact badges -->
        <div class="flex flex-wrap gap-2 mt-3">
          <span
            v-if="analysis.impact_assessment.pivotal"
            class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[rgba(255,86,0,0.1)] text-[#ff5600]"
          >
            Pivotal Moment
          </span>
          <span
            v-if="analysis.impact_assessment.consensus_delta"
            class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]"
          >
            {{ analysis.impact_assessment.consensus_delta }} round{{ analysis.impact_assessment.consensus_delta !== 1 ? 's' : '' }} faster
          </span>
          <span
            v-if="analysis.impact_assessment.sentiment_shift"
            class="px-2 py-0.5 rounded-full text-[10px] font-medium"
            :class="analysis.impact_assessment.sentiment_shift > 0
              ? 'bg-[rgba(0,153,0,0.1)] text-[#009900]'
              : 'bg-[rgba(255,86,0,0.1)] text-[#ff5600]'"
          >
            Sentiment {{ analysis.impact_assessment.sentiment_shift > 0 ? '+' : '' }}{{ analysis.impact_assessment.sentiment_shift.toFixed(2) }}
          </span>
        </div>

        <!-- Affected agents -->
        <div v-if="analysis.impact_assessment.affected_agents?.length" class="mt-2">
          <span class="text-[10px] text-[var(--color-text-muted)]">Affected agents: </span>
          <span
            v-for="(agent, i) in analysis.impact_assessment.affected_agents"
            :key="i"
            class="text-[10px] text-[var(--color-text-secondary)]"
          >
            {{ agent }}{{ i < analysis.impact_assessment.affected_agents.length - 1 ? ', ' : '' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
