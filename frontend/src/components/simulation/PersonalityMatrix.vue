<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import client from '../../api/client.js'

const props = defineProps({
  simulationId: { type: String, default: '' },
  agents: { type: Array, default: () => [] },
})

const emit = defineEmits(['select-agent', 'select-trait'])

const matrixRef = ref(null)
const loading = ref(false)
const error = ref(null)
const agentData = ref([])
const traits = ref([])
const sortKey = ref(null)
const sortDir = ref('desc')
const hoveredAgent = ref(null)
const hoveredTrait = ref(null)
const showDelta = ref(true)

let resizeObserver = null
let resizeTimer = null

// Trait display labels
const TRAIT_LABELS = {
  confidence: 'Confidence',
  openness: 'Openness',
  risk_aversion: 'Risk Aversion',
  empathy: 'Empathy',
  aggressiveness: 'Aggressiveness',
}

// Fetch personality data from backend
async function fetchPersonalities() {
  if (props.agents.length) {
    agentData.value = props.agents
    if (props.agents[0]?.initial_personality) {
      traits.value = Object.keys(props.agents[0].initial_personality)
    }
    return
  }
  if (!props.simulationId) return

  loading.value = true
  error.value = null
  try {
    const res = await client.get(`/simulation/${props.simulationId}/agent-personalities`)
    const json = res.data
    if (json.success) {
      agentData.value = json.data.agents
      traits.value = json.data.traits
    } else {
      error.value = json.error || 'Failed to load personality data'
    }
  } catch (e) {
    error.value = e.message || 'Network error'
  } finally {
    loading.value = false
  }
}

// Sort logic
const sortedAgents = computed(() => {
  const list = [...agentData.value]
  if (!sortKey.value) return list

  return list.sort((a, b) => {
    let aVal, bVal
    if (sortKey.value === 'delta') {
      aVal = maxDelta(a)
      bVal = maxDelta(b)
    } else {
      aVal = a.current_personality[sortKey.value] ?? 0
      bVal = b.current_personality[sortKey.value] ?? 0
    }
    return sortDir.value === 'desc' ? bVal - aVal : aVal - bVal
  })
})

function maxDelta(agent) {
  let max = 0
  for (const t of traits.value) {
    const d = Math.abs((agent.current_personality[t] ?? 0) - (agent.initial_personality[t] ?? 0))
    if (d > max) max = d
  }
  return max
}

function toggleSort(trait) {
  if (sortKey.value === trait) {
    sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortKey.value = trait
    sortDir.value = 'desc'
  }
}

function handleAgentClick(agent) {
  emit('select-agent', agent)
}

function handleTraitClick(trait) {
  emit('select-trait', trait, agentData.value)
}

// Color scale: brand-aligned gradient from orange (low) through blue (mid) to green (high)
function traitColor(value) {
  if (value <= 50) {
    const t = value / 50
    return d3.interpolateRgb('#ff5600', '#2068FF')(t)
  }
  const t = (value - 50) / 50
  return d3.interpolateRgb('#2068FF', '#009900')(t)
}

function deltaColor(delta) {
  if (delta > 0) return '#009900'
  if (delta < 0) return '#ff5600'
  return 'var(--color-text-muted, #888)'
}

function deltaArrow(delta) {
  if (delta > 0) return '▲'
  if (delta < 0) return '▼'
  return '—'
}

function shortName(fullName) {
  // "Sarah Chen, VP Support @ Acme SaaS" → "Sarah Chen"
  const comma = fullName.indexOf(',')
  return comma > -1 ? fullName.substring(0, comma) : fullName
}

function roleName(fullName) {
  const comma = fullName.indexOf(',')
  return comma > -1 ? fullName.substring(comma + 2) : ''
}

// D3 distribution popover rendering
const distributionRef = ref(null)
const distributionTrait = ref(null)

function showDistribution(trait) {
  distributionTrait.value = trait
  nextTick(() => renderDistribution(trait))
}

function closeDistribution() {
  distributionTrait.value = null
}

function renderDistribution(trait) {
  const container = distributionRef.value
  if (!container) return
  d3.select(container).selectAll('*').remove()

  const values = agentData.value.map(a => a.current_personality[trait] ?? 0)
  const margin = { top: 8, right: 12, bottom: 24, left: 32 }
  const width = 260 - margin.left - margin.right
  const height = 120 - margin.top - margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Histogram bins
  const bins = d3.bin().domain([0, 100]).thresholds(10)(values)

  const x = d3.scaleLinear().domain([0, 100]).range([0, width])
  const y = d3.scaleLinear().domain([0, d3.max(bins, d => d.length)]).nice().range([height, 0])

  // Bars
  g.selectAll('rect')
    .data(bins)
    .join('rect')
    .attr('x', d => x(d.x0) + 1)
    .attr('width', d => Math.max(0, x(d.x1) - x(d.x0) - 2))
    .attr('y', height)
    .attr('height', 0)
    .attr('fill', d => traitColor((d.x0 + d.x1) / 2))
    .attr('rx', 2)
    .transition()
    .duration(400)
    .delay((_, i) => i * 30)
    .attr('y', d => y(d.length))
    .attr('height', d => height - y(d.length))

  // X axis
  g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(5).tickSize(0))
    .selectAll('text')
    .attr('font-size', '9px')
    .attr('fill', '#888')

  g.select('.domain').attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')

  // Y axis
  g.append('g')
    .call(d3.axisLeft(y).ticks(3).tickSize(0))
    .selectAll('text')
    .attr('font-size', '9px')
    .attr('fill', '#888')

  g.selectAll('.domain').attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
}

// Lifecycle
watch([() => props.simulationId, () => props.agents.length], () => {
  fetchPersonalities()
})

onMounted(() => {
  fetchPersonalities()
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Personality Comparison Matrix</h3>
      <div class="flex items-center gap-2">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="showDelta
            ? 'bg-[var(--color-primary)] text-white'
            : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="showDelta = !showDelta"
        >
          {{ showDelta ? 'Deltas On' : 'Deltas Off' }}
        </button>
        <button
          v-if="sortKey"
          class="px-2.5 py-1 text-[11px] rounded font-medium bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
          @click="sortKey = null"
        >
          Clear Sort
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Loading personality data…</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-[200px] text-[var(--color-error)] text-sm">
      <span>{{ error }}</span>
    </div>

    <!-- Empty -->
    <div v-else-if="!agentData.length" class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Personality data will appear as agents are generated</span>
    </div>

    <!-- Matrix Table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th class="text-left py-2 px-3 font-semibold text-[var(--color-text-muted)] sticky left-0 bg-[var(--color-surface)] z-10 min-w-[160px]">
              Agent
            </th>
            <th
              v-for="trait in traits"
              :key="trait"
              class="py-2 px-2 font-semibold text-center cursor-pointer select-none transition-colors hover:text-[var(--color-primary)] min-w-[110px]"
              :class="sortKey === trait ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'"
              @click="toggleSort(trait)"
            >
              <div class="flex items-center justify-center gap-1">
                <span>{{ TRAIT_LABELS[trait] || trait }}</span>
                <span v-if="sortKey === trait" class="text-[10px]">{{ sortDir === 'desc' ? '▼' : '▲' }}</span>
              </div>
              <button
                class="mt-0.5 text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-primary)] underline"
                @click.stop="showDistribution(trait)"
              >
                dist
              </button>
            </th>
            <th
              v-if="showDelta"
              class="py-2 px-2 font-semibold text-center cursor-pointer select-none transition-colors hover:text-[var(--color-primary)] min-w-[70px]"
              :class="sortKey === 'delta' ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'"
              @click="toggleSort('delta')"
            >
              <div class="flex items-center justify-center gap-1">
                <span>Max Δ</span>
                <span v-if="sortKey === 'delta'" class="text-[10px]">{{ sortDir === 'desc' ? '▼' : '▲' }}</span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="agent in sortedAgents"
            :key="agent.agent_id"
            class="border-t border-[var(--color-border)] cursor-pointer transition-colors hover:bg-[var(--color-tint)]"
            :class="{ 'bg-[var(--color-tint)]': hoveredAgent === agent.agent_id }"
            @mouseenter="hoveredAgent = agent.agent_id"
            @mouseleave="hoveredAgent = null"
            @click="handleAgentClick(agent)"
          >
            <!-- Agent name -->
            <td class="py-2.5 px-3 sticky left-0 bg-[var(--color-surface)] z-10">
              <div class="font-semibold text-[var(--color-text)]">{{ shortName(agent.agent_name) }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)] mt-0.5 truncate max-w-[180px]">{{ roleName(agent.agent_name) }}</div>
            </td>

            <!-- Trait cells -->
            <td
              v-for="trait in traits"
              :key="trait"
              class="py-2.5 px-2"
              @mouseenter="hoveredTrait = trait"
              @mouseleave="hoveredTrait = null"
            >
              <div class="flex flex-col items-center gap-1">
                <!-- Bar visualization: initial (faded) vs current (solid) -->
                <div class="w-full h-5 bg-[rgba(0,0,0,0.04)] rounded-sm relative overflow-hidden">
                  <!-- Initial personality (thin line marker) -->
                  <div
                    class="absolute top-0 h-full w-[2px] opacity-40 z-[1]"
                    :style="{
                      left: `${agent.initial_personality[trait]}%`,
                      backgroundColor: traitColor(agent.initial_personality[trait]),
                    }"
                  />
                  <!-- Current personality (filled bar) -->
                  <div
                    class="h-full rounded-sm transition-all duration-500"
                    :style="{
                      width: `${agent.current_personality[trait]}%`,
                      backgroundColor: traitColor(agent.current_personality[trait]),
                      opacity: 0.7,
                    }"
                  />
                </div>
                <!-- Value + delta -->
                <div class="flex items-center gap-1 text-[10px]">
                  <span class="font-medium text-[var(--color-text)]">{{ agent.current_personality[trait] }}</span>
                  <span
                    v-if="showDelta"
                    class="font-medium"
                    :style="{ color: deltaColor(agent.current_personality[trait] - agent.initial_personality[trait]) }"
                  >
                    {{ deltaArrow(agent.current_personality[trait] - agent.initial_personality[trait]) }}{{ Math.abs(agent.current_personality[trait] - agent.initial_personality[trait]) }}
                  </span>
                </div>
              </div>
            </td>

            <!-- Max delta column -->
            <td v-if="showDelta" class="py-2.5 px-2 text-center">
              <span
                class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-semibold"
                :class="maxDelta(agent) >= 10
                  ? 'bg-[rgba(255,86,0,0.1)] text-[#ff5600]'
                  : 'bg-[rgba(0,0,0,0.04)] text-[var(--color-text-muted)]'"
              >
                {{ maxDelta(agent) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Distribution popover -->
    <Transition name="fade">
      <div
        v-if="distributionTrait"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/20"
        @click.self="closeDistribution"
      >
        <div class="bg-[var(--color-surface)] rounded-lg shadow-xl border border-[var(--color-border)] p-4 min-w-[280px]">
          <div class="flex items-center justify-between mb-3">
            <h4 class="text-sm font-semibold text-[var(--color-text)]">
              {{ TRAIT_LABELS[distributionTrait] || distributionTrait }} Distribution
            </h4>
            <button
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-lg leading-none"
              @click="closeDistribution"
            >
              ×
            </button>
          </div>
          <div ref="distributionRef" style="height: 120px" />
          <div class="mt-2 flex items-center justify-between text-[10px] text-[var(--color-text-muted)]">
            <span>Low (0)</span>
            <span>High (100)</span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Legend -->
    <div v-if="agentData.length" class="flex items-center gap-4 mt-4 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #ff5600; opacity: 0.7" /> Low (0-33)
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #2068FF; opacity: 0.7" /> Mid (34-66)
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #009900; opacity: 0.7" /> High (67-100)
      </span>
      <span class="flex items-center gap-1.5 ml-2">
        <span class="inline-block w-[2px] h-3 bg-[var(--color-text-muted)] opacity-40" /> Initial value
      </span>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
