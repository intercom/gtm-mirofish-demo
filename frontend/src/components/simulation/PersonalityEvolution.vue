<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  simulationId: { type: String, default: '' },
})

const TRAITS = ['analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant']
const TRAIT_LABELS = {
  analytical: 'Analytical',
  creative: 'Creative',
  assertive: 'Assertive',
  empathetic: 'Empathetic',
  risk_tolerant: 'Risk Tolerant',
}

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const personalityData = ref(null)
const loading = ref(false)
const error = ref(null)

const currentRound = ref(1)
const playing = ref(false)
let playInterval = null

const selectedAgents = ref([])
const comparisonMode = ref(false)

// Colors: blue → purple gradient for temporal progression
const COLOR_START = '#2068FF'
const COLOR_END = '#AA00FF'

const AGENT_COLORS = ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#f59e0b']

const totalRounds = computed(() => personalityData.value?.total_rounds || 1)
const agents = computed(() => personalityData.value?.agents || [])

const activeAgents = computed(() => {
  if (!agents.value.length) return []
  if (comparisonMode.value && selectedAgents.value.length) {
    return agents.value.filter(a => selectedAgents.value.includes(String(a.agent_id)))
  }
  return agents.value.slice(0, 1)
})

const roundColor = computed(() => {
  const t = totalRounds.value > 1 ? (currentRound.value - 1) / (totalRounds.value - 1) : 0
  return d3.interpolateRgb(COLOR_START, COLOR_END)(t)
})

// --- Data fetching ---

async function fetchData() {
  if (!props.simulationId) return
  loading.value = true
  error.value = null
  try {
    const res = await simulationApi.getPersonalityEvolution(props.simulationId)
    personalityData.value = res.data?.data || res.data
    if (agents.value.length && !selectedAgents.value.length) {
      selectedAgents.value = [String(agents.value[0].agent_id)]
    }
  } catch (e) {
    error.value = e.message || 'Failed to load personality data'
  } finally {
    loading.value = false
  }
}

// --- Playback ---

function togglePlay() {
  if (playing.value) {
    stopPlay()
  } else {
    startPlay()
  }
}

function startPlay() {
  playing.value = true
  if (currentRound.value >= totalRounds.value) currentRound.value = 1
  playInterval = setInterval(() => {
    if (currentRound.value >= totalRounds.value) {
      stopPlay()
      return
    }
    currentRound.value++
  }, 600)
}

function stopPlay() {
  playing.value = false
  if (playInterval) {
    clearInterval(playInterval)
    playInterval = null
  }
}

function toggleAgent(agentId) {
  const id = String(agentId)
  const idx = selectedAgents.value.indexOf(id)
  if (idx >= 0) {
    if (selectedAgents.value.length > 1) {
      selectedAgents.value = selectedAgents.value.filter(a => a !== id)
    }
  } else {
    selectedAgents.value = [...selectedAgents.value, id]
  }
}

// --- Trait change detection ---

function getTraitChanges(agent) {
  if (currentRound.value <= 1) return {}
  const curr = agent.history.find(h => h.round === currentRound.value)
  const prev = agent.history.find(h => h.round === currentRound.value - 1)
  if (!curr || !prev) return {}
  const changes = {}
  for (const trait of TRAITS) {
    const diff = Math.abs((curr.traits[trait] || 0) - (prev.traits[trait] || 0))
    if (diff > 3) changes[trait] = diff
  }
  return changes
}

// --- D3 Radar Chart ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !activeAgents.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 360)
  const margin = 50
  const radius = (size - margin * 2) / 2
  const cx = size / 2
  const cy = size / 2

  const svg = d3.select(container)
    .append('svg')
    .attr('width', size)
    .attr('height', size)
    .attr('viewBox', `0 0 ${size} ${size}`)
    .style('display', 'block')
    .style('margin', '0 auto')

  const g = svg.append('g').attr('transform', `translate(${cx},${cy})`)

  const angleSlice = (Math.PI * 2) / TRAITS.length

  // Radial scale
  const rScale = d3.scaleLinear().domain([0, 100]).range([0, radius])

  // Grid circles
  const levels = [20, 40, 60, 80, 100]
  levels.forEach(level => {
    const r = rScale(level)
    g.append('circle')
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
      .attr('stroke-dasharray', level === 100 ? 'none' : '2,3')

    g.append('text')
      .attr('x', 4)
      .attr('y', -r)
      .attr('dy', '0.35em')
      .attr('font-size', '9px')
      .attr('fill', 'var(--color-text-muted, #888)')
      .text(level)
  })

  // Axis lines + labels
  TRAITS.forEach((trait, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x2 = Math.cos(angle) * radius
    const y2 = Math.sin(angle) * radius
    const labelR = radius + 20

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')

    const lx = Math.cos(angle) * labelR
    const ly = Math.sin(angle) * labelR

    g.append('text')
      .attr('x', lx)
      .attr('y', ly)
      .attr('dy', '0.35em')
      .attr('text-anchor', Math.abs(lx) < 5 ? 'middle' : lx > 0 ? 'start' : 'end')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', 'var(--color-text, #050505)')
      .text(TRAIT_LABELS[trait])
  })

  // Ghost trail: show previous rounds faintly for the first agent
  if (!comparisonMode.value && activeAgents.value.length === 1) {
    const agent = activeAgents.value[0]
    const trailRounds = agent.history
      .filter(h => h.round < currentRound.value && h.round >= Math.max(1, currentRound.value - 3))

    trailRounds.forEach((roundData, idx) => {
      const t = totalRounds.value > 1 ? (roundData.round - 1) / (totalRounds.value - 1) : 0
      const color = d3.interpolateRgb(COLOR_START, COLOR_END)(t)
      const opacity = 0.1 + (idx / trailRounds.length) * 0.15

      const points = TRAITS.map((trait, i) => {
        const angle = angleSlice * i - Math.PI / 2
        const val = roundData.traits[trait] || 0
        return [Math.cos(angle) * rScale(val), Math.sin(angle) * rScale(val)]
      })

      const lineGen = d3.lineRadial()
        .angle((_, i) => angleSlice * i)
        .radius((_, i) => rScale(TRAITS.map(t => roundData.traits[t] || 0)[i]))
        .curve(d3.curveLinearClosed)

      g.append('path')
        .datum(TRAITS)
        .attr('d', lineGen)
        .attr('fill', color)
        .attr('fill-opacity', opacity * 0.3)
        .attr('stroke', color)
        .attr('stroke-opacity', opacity)
        .attr('stroke-width', 1)
    })
  }

  // Main polygons
  activeAgents.value.forEach((agent, agentIdx) => {
    const roundData = agent.history.find(h => h.round === currentRound.value)
    if (!roundData) return

    const color = comparisonMode.value ? AGENT_COLORS[agentIdx % AGENT_COLORS.length] : roundColor.value
    const changes = getTraitChanges(agent)

    const lineGen = d3.lineRadial()
      .angle((_, i) => angleSlice * i)
      .radius((_, i) => rScale(roundData.traits[TRAITS[i]] || 0))
      .curve(d3.curveLinearClosed)

    // Filled polygon
    const polygon = g.append('path')
      .datum(TRAITS)
      .attr('fill', color)
      .attr('fill-opacity', comparisonMode.value ? 0.08 : 0.12)
      .attr('stroke', color)
      .attr('stroke-width', comparisonMode.value ? 1.5 : 2.5)
      .attr('stroke-opacity', 0.9)

    // Animate from center on initial render
    const lineGenZero = d3.lineRadial()
      .angle((_, i) => angleSlice * i)
      .radius(0)
      .curve(d3.curveLinearClosed)

    polygon
      .attr('d', lineGenZero)
      .transition()
      .duration(400)
      .ease(d3.easeCubicOut)
      .attr('d', lineGen)

    // Vertex dots + value labels
    TRAITS.forEach((trait, i) => {
      const angle = angleSlice * i - Math.PI / 2
      const val = roundData.traits[trait] || 0
      const px = Math.cos(angle) * rScale(val)
      const py = Math.sin(angle) * rScale(val)
      const hasChange = changes[trait]

      const dot = g.append('circle')
        .attr('cx', px).attr('cy', py)
        .attr('r', hasChange ? 5 : 3.5)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)

      // Flash animation for changed traits
      if (hasChange) {
        dot
          .attr('r', 8)
          .attr('fill-opacity', 0.6)
          .transition().duration(400).ease(d3.easeCubicOut)
          .attr('r', 5)
          .attr('fill-opacity', 1)
      }

      // Value tooltip near dot (only in single-agent mode or few agents)
      if (activeAgents.value.length <= 2) {
        const valOffset = rScale(val) + 12
        const vx = Math.cos(angle) * valOffset
        const vy = Math.sin(angle) * valOffset

        g.append('text')
          .attr('x', vx).attr('y', vy)
          .attr('dy', '0.35em')
          .attr('text-anchor', 'middle')
          .attr('font-size', '10px')
          .attr('font-weight', '500')
          .attr('fill', color)
          .text(Math.round(val))
      }
    })
  })
}

// --- Lifecycle ---

watch([currentRound, selectedAgents, comparisonMode], () => {
  nextTick(() => renderChart())
})

watch(() => props.simulationId, () => {
  currentRound.value = 1
  stopPlay()
  fetchData()
})

onMounted(() => {
  fetchData()
  nextTick(() => {
    renderChart()
    if (chartRef.value) {
      resizeObserver = new ResizeObserver(() => {
        clearTimeout(resizeTimer)
        resizeTimer = setTimeout(renderChart, 200)
      })
      resizeObserver.observe(chartRef.value)
    }
  })
})

onUnmounted(() => {
  stopPlay()
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})

// Re-render when data arrives
watch(personalityData, () => {
  nextTick(() => renderChart())
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Personality Evolution</h3>
      <button
        v-if="agents.length > 1"
        class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
        :class="comparisonMode
          ? 'bg-[var(--color-primary)] text-white'
          : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
        @click="comparisonMode = !comparisonMode"
      >
        Compare Agents
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[320px] text-[var(--color-text-muted)] text-sm">
      Loading personality data...
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-[320px] text-[var(--color-error)] text-sm">
      {{ error }}
    </div>

    <!-- Empty -->
    <div v-else-if="!agents.length" class="flex items-center justify-center h-[320px] text-[var(--color-text-muted)] text-sm">
      Personality data will appear as agents interact
    </div>

    <!-- Chart -->
    <template v-else>
      <!-- Agent selector (comparison mode) -->
      <div v-if="comparisonMode" class="flex flex-wrap gap-2 mb-3">
        <button
          v-for="(agent, idx) in agents"
          :key="agent.agent_id"
          class="flex items-center gap-1.5 px-2 py-1 text-[11px] rounded-md border transition-colors"
          :class="selectedAgents.includes(String(agent.agent_id))
            ? 'border-transparent text-white'
            : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-text-muted)]'"
          :style="selectedAgents.includes(String(agent.agent_id))
            ? { backgroundColor: AGENT_COLORS[idx % AGENT_COLORS.length] }
            : {}"
          @click="toggleAgent(agent.agent_id)"
        >
          {{ agent.agent_name }}
        </button>
      </div>

      <!-- Radar chart -->
      <div ref="chartRef" style="min-height: 300px" />

      <!-- Timeline scrubber -->
      <div class="mt-4 flex items-center gap-3">
        <button
          class="w-8 h-8 flex items-center justify-center rounded-full transition-colors"
          :class="playing
            ? 'bg-[var(--color-primary)] text-white'
            : 'bg-[var(--color-tint)] text-[var(--color-text)] hover:bg-[var(--color-primary-light)]'"
          @click="togglePlay"
        >
          <svg v-if="!playing" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 ml-0.5">
            <path d="M6 4l10 6-10 6V4z" />
          </svg>
          <svg v-else viewBox="0 0 20 20" fill="currentColor" class="w-3.5 h-3.5">
            <rect x="5" y="4" width="3" height="12" rx="1" />
            <rect x="12" y="4" width="3" height="12" rx="1" />
          </svg>
        </button>

        <input
          type="range"
          :min="1"
          :max="totalRounds"
          v-model.number="currentRound"
          class="flex-1 h-1.5 accent-[var(--color-primary)] cursor-pointer"
          @mousedown="stopPlay"
        />

        <span
          class="text-xs font-semibold px-2 py-0.5 rounded-md min-w-[60px] text-center"
          :style="{ backgroundColor: roundColor + '18', color: roundColor }"
        >
          R{{ currentRound }} / {{ totalRounds }}
        </span>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
        <template v-if="comparisonMode">
          <span
            v-for="agent in activeAgents"
            :key="agent.agent_id"
            class="flex items-center gap-1.5"
          >
            <span
              class="inline-block w-3 h-0.5 rounded"
              :style="{ backgroundColor: AGENT_COLORS[agents.indexOf(agent) % AGENT_COLORS.length] }"
            />
            {{ agent.agent_name }}
          </span>
        </template>
        <template v-else>
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-full bg-[#2068FF]" /> Start
          </span>
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-full bg-[#AA00FF]" /> End
          </span>
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-full border-2 border-current" style="animation: pulse 1s ease-in-out infinite" /> Trait changed
          </span>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-border, rgba(0, 0, 0, 0.1));
  border-radius: 4px;
  outline: none;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary, #2068FF);
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
</style>
