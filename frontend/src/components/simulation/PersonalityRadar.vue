<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { usePersonalityStore } from '@/stores/personality'
import { useSimulationStore } from '@/stores/simulation'

const props = defineProps({
  simulationId: { type: String, default: null },
})

const personalityStore = usePersonalityStore()
const simStore = useSimulationStore()

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const TRAIT_LABELS = {
  analytical: 'Analytical',
  creative: 'Creative',
  assertive: 'Assertive',
  empathetic: 'Empathetic',
  risk_tolerant: 'Risk Tolerant',
}

const AGENT_COLORS = ['#2068FF', '#ff5600', '#009900', '#8B5CF6', '#F59E0B']

const simId = computed(() => props.simulationId || simStore.simulationId || 'demo')

const hasData = computed(() => personalityStore.agentIds.length > 0)

const viewMode = ref('radar') // 'radar' | 'trajectory'

// Fetch data on mount or when simulation changes
async function loadData() {
  await personalityStore.fetchAgents(simId.value)
  if (personalityStore.selectedAgentId) {
    await personalityStore.fetchTrajectory(simId.value, personalityStore.selectedAgentId)
  }
}

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !hasData.value) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  if (viewMode.value === 'trajectory') {
    renderTrajectory(container, containerWidth)
  } else {
    renderRadar(container, containerWidth)
  }
}

function renderRadar(container, containerWidth) {
  const size = Math.min(containerWidth, 320)
  const margin = 40
  const radius = (size - margin * 2) / 2
  const center = size / 2

  const svg = d3.select(container)
    .append('svg')
    .attr('width', size)
    .attr('height', size)
    .attr('viewBox', `0 0 ${size} ${size}`)
    .style('margin', '0 auto')
    .style('display', 'block')

  const g = svg.append('g')
    .attr('transform', `translate(${center},${center})`)

  const traits = personalityStore.traits
  const numTraits = traits.length
  const angleSlice = (Math.PI * 2) / numTraits

  const rScale = d3.scaleLinear()
    .domain([0, 100])
    .range([0, radius])

  // Grid circles
  const gridLevels = [20, 40, 60, 80]
  g.selectAll('.grid-circle')
    .data(gridLevels)
    .join('circle')
    .attr('r', d => rScale(d))
    .attr('fill', 'none')
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
    .attr('stroke-dasharray', '2,3')

  // Grid level labels
  g.selectAll('.grid-label')
    .data(gridLevels)
    .join('text')
    .attr('x', 4)
    .attr('y', d => -rScale(d))
    .attr('dy', '-0.2em')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => d)

  // Axis lines & labels
  traits.forEach((trait, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius
    const labelX = Math.cos(angle) * (radius + 20)
    const labelY = Math.sin(angle) * (radius + 20)

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x).attr('y2', y)
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')

    g.append('text')
      .attr('x', labelX)
      .attr('y', labelY)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('fill', 'var(--color-text-secondary, #555)')
      .text(TRAIT_LABELS[trait] || trait)
  })

  // Draw personality polygons for each agent
  const radarLine = d3.lineRadial()
    .radius(d => rScale(d.value))
    .angle((d, i) => i * angleSlice)
    .curve(d3.curveLinearClosed)

  const agents = personalityStore.agents
  const agentIds = personalityStore.agentIds

  agentIds.forEach((agentId, idx) => {
    const vector = agents[agentId]
    const dataPoints = traits.map(t => ({ trait: t, value: vector[t] || 50 }))
    const color = AGENT_COLORS[idx % AGENT_COLORS.length]
    const isSelected = agentId === personalityStore.selectedAgentId

    // Fill area
    g.append('path')
      .datum(dataPoints)
      .attr('d', radarLine)
      .attr('fill', color)
      .attr('fill-opacity', isSelected ? 0.2 : 0.05)
      .attr('stroke', color)
      .attr('stroke-width', isSelected ? 2.5 : 1)
      .attr('stroke-opacity', isSelected ? 1 : 0.4)
      .style('cursor', 'pointer')
      .on('click', () => personalityStore.selectAgent(agentId))
      .append('title')
      .text(agentId)

    // Data points for selected agent
    if (isSelected) {
      dataPoints.forEach((d, i) => {
        const angle = angleSlice * i - Math.PI / 2
        const cx = Math.cos(angle) * rScale(d.value)
        const cy = Math.sin(angle) * rScale(d.value)

        g.append('circle')
          .attr('cx', cx)
          .attr('cy', cy)
          .attr('r', 4)
          .attr('fill', color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.5)

        g.append('text')
          .attr('x', cx)
          .attr('y', cy - 10)
          .attr('text-anchor', 'middle')
          .attr('font-size', '10px')
          .attr('font-weight', '600')
          .attr('fill', color)
          .text(d.value)
      })
    }
  })
}

function renderTrajectory(container, containerWidth) {
  const trajectory = personalityStore.selectedTrajectory
  if (!trajectory.length) return

  const margin = { top: 16, right: 16, bottom: 28, left: 36 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const traits = personalityStore.traits
  const rounds = trajectory.map(s => s.round_num)

  const x = d3.scaleLinear()
    .domain([d3.min(rounds), d3.max(rounds)])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([personalityStore.bounds.min - 5, personalityStore.bounds.max + 5])
    .range([height, 0])

  // Grid
  const gridVals = [20, 40, 50, 60, 80]
  g.selectAll('.grid')
    .data(gridVals)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', d => d === 50 ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.05)')
    .attr('stroke-dasharray', d => d === 50 ? 'none' : '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(gridVals)
    .join('text')
    .attr('x', -6).attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => d)

  // X-axis labels
  const step = Math.max(1, Math.floor(rounds.length / 8))
  g.selectAll('.x-label')
    .data(rounds.filter((_, i) => i % step === 0 || i === rounds.length - 1))
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d}`)

  // One line per trait
  const traitColors = {
    analytical: '#2068FF',
    creative: '#8B5CF6',
    assertive: '#ff5600',
    empathetic: '#009900',
    risk_tolerant: '#F59E0B',
  }

  traits.forEach(trait => {
    const lineData = trajectory.map(s => ({
      round: s.round_num,
      value: s.vector[trait],
    }))

    const line = d3.line()
      .x(d => x(d.round))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX)

    const path = g.append('path')
      .datum(lineData)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', traitColors[trait] || '#888')
      .attr('stroke-width', 2)

    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // End label
    const lastPoint = lineData[lineData.length - 1]
    g.append('text')
      .attr('x', x(lastPoint.round) + 4)
      .attr('y', y(lastPoint.value))
      .attr('dy', '0.35em')
      .attr('font-size', '9px')
      .attr('font-weight', '600')
      .attr('fill', traitColors[trait] || '#888')
      .text(TRAIT_LABELS[trait] || trait)
      .style('opacity', 0)
      .transition()
      .delay(800)
      .duration(200)
      .style('opacity', 1)
  })
}

// --- Agent selection handler ---
async function onSelectAgent(agentId) {
  personalityStore.selectAgent(agentId)
  await personalityStore.fetchTrajectory(simId.value, agentId)
  nextTick(() => renderChart())
}

// --- Lifecycle ---
watch([hasData, viewMode], () => {
  nextTick(() => renderChart())
})

watch(() => personalityStore.selectedAgentId, () => {
  nextTick(() => renderChart())
})

onMounted(async () => {
  await loadData()
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
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Personality Dynamics</h3>
      <div v-if="hasData" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'radar'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'radar'"
        >
          Radar
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'trajectory'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'trajectory'"
        >
          Trajectory
        </button>
      </div>
    </div>

    <!-- Agent selector pills -->
    <div v-if="hasData" class="flex flex-wrap gap-1.5 mb-4">
      <button
        v-for="(agentId, idx) in personalityStore.agentIds"
        :key="agentId"
        class="px-2.5 py-1 text-[11px] rounded-full font-medium transition-all border"
        :style="{
          borderColor: personalityStore.selectedAgentId === agentId
            ? ['#2068FF', '#ff5600', '#009900', '#8B5CF6', '#F59E0B'][idx % 5]
            : 'var(--color-border)',
          backgroundColor: personalityStore.selectedAgentId === agentId
            ? ['#2068FF', '#ff5600', '#009900', '#8B5CF6', '#F59E0B'][idx % 5] + '15'
            : 'transparent',
          color: personalityStore.selectedAgentId === agentId
            ? ['#2068FF', '#ff5600', '#009900', '#8B5CF6', '#F59E0B'][idx % 5]
            : 'var(--color-text-muted)',
        }"
        @click="onSelectAgent(agentId)"
      >
        {{ agentId }}
      </button>
    </div>

    <!-- Chart -->
    <div v-if="hasData" ref="chartRef" class="relative" style="min-height: 260px" />

    <!-- Loading / empty -->
    <div v-else-if="personalityStore.loading" class="flex items-center justify-center h-[260px] text-[var(--color-text-muted)] text-sm">
      <span>Loading personality data...</span>
    </div>
    <div v-else class="flex items-center justify-center h-[260px] text-[var(--color-text-muted)] text-sm">
      <span>Personality data will appear when simulation runs</span>
    </div>

    <!-- Legend -->
    <div v-if="hasData && viewMode === 'trajectory'" class="flex flex-wrap items-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#2068FF]" /> Analytical
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#8B5CF6]" /> Creative
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#ff5600]" /> Assertive
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#009900]" /> Empathetic
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#F59E0B]" /> Risk Tolerant
      </span>
    </div>
  </div>
</template>
