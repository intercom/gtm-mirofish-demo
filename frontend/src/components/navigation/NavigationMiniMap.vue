<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { select, scaleLinear } from 'd3'
import { useSimulationStore } from '../../stores/simulation'
import { useTheme } from '../../composables/useTheme'

const route = useRoute()
const router = useRouter()
const simulation = useSimulationStore()
const { isDark } = useTheme()
const svgRef = ref(null)

const stages = [
  { key: 'scenario', label: 'Scenario' },
  { key: 'graph', label: 'Graph' },
  { key: 'simulation', label: 'Simulation' },
  { key: 'report', label: 'Report' },
  { key: 'chat', label: 'Chat' },
]

const W = 320
const H = 56
const PAD = 30
const CY = 20
const R = 5
const AR = 7

function currentStage() {
  const p = route.path
  if (p.startsWith('/chat/')) return 'chat'
  if (p.startsWith('/report/')) return 'report'
  if (p.startsWith('/workspace/')) return route.query.tab === 'simulation' ? 'simulation' : 'graph'
  if (p.startsWith('/scenarios/')) return 'scenario'
  return null
}

function stageStatus(i, activeIdx) {
  if (activeIdx < 0) return 'pending'
  if (i === activeIdx) return 'active'
  if (i < activeIdx) return 'completed'
  if (simulation.status === 'complete' && (stages[i].key === 'report' || stages[i].key === 'chat')) {
    return 'available'
  }
  return 'pending'
}

function nodeColor(status) {
  if (status === 'active' || status === 'completed') return '#2068FF'
  if (status === 'available') return '#ff5600'
  return isDark.value ? '#4b5563' : '#d1d5db'
}

function textColor(status) {
  if (status === 'active') return '#2068FF'
  if (status === 'completed') return isDark.value ? '#93c5fd' : '#6b7280'
  if (status === 'available') return '#ff5600'
  return isDark.value ? '#6b7280' : '#9ca3af'
}

function lineColor(completed) {
  return completed ? '#2068FF' : (isDark.value ? '#374151' : '#e5e7eb')
}

function navigate(stage) {
  const tid = route.params.taskId || route.params.id
  switch (stage.key) {
    case 'scenario': {
      const sid = simulation.scenarioConfig?.scenarioId
      if (sid) router.push(`/scenarios/${sid}`)
      break
    }
    case 'graph':
      if (tid) router.push(`/workspace/${tid}?tab=graph`)
      break
    case 'simulation':
      if (tid) router.push(`/workspace/${tid}?tab=simulation`)
      break
    case 'report':
      if (tid) router.push(`/report/${tid}`)
      break
    case 'chat':
      if (tid) router.push(`/chat/${tid}`)
      break
  }
}

function render() {
  if (!svgRef.value) return

  const svg = select(svgRef.value)
  const x = scaleLinear().domain([0, stages.length - 1]).range([PAD, W - PAD])
  const active = currentStage()
  const ai = stages.findIndex(s => s.key === active)

  const nodeData = stages.map((s, i) => ({
    ...s, i, x: x(i), status: stageStatus(i, ai),
  }))

  // --- Connectors ---
  const connData = nodeData.slice(0, -1).map((n, i) => ({
    i, x1: n.x + R + 3, x2: nodeData[i + 1].x - R - 3,
    completed: n.status === 'completed',
  }))

  svg.selectAll('.mm-conn')
    .data(connData, d => d.i)
    .join(
      enter => enter.append('line')
        .attr('class', 'mm-conn')
        .attr('y1', CY).attr('y2', CY)
        .attr('stroke-width', 2).attr('stroke-linecap', 'round')
        .attr('x1', d => d.x1).attr('x2', d => d.x2)
        .attr('stroke', d => lineColor(d.completed)),
    )
    .transition().duration(350)
    .attr('x1', d => d.x1).attr('x2', d => d.x2)
    .attr('stroke', d => lineColor(d.completed))

  // --- Node groups ---
  const nodes = svg.selectAll('.mm-node')
    .data(nodeData, d => d.key)
    .join(
      enter => {
        const g = enter.append('g').attr('class', 'mm-node')
        g.append('circle').attr('class', 'mm-pulse')
          .attr('cy', CY).attr('fill', 'none')
          .attr('stroke', '#2068FF').attr('stroke-width', 1.5)
          .attr('cx', d => d.x)
          .attr('r', d => d.status === 'active' ? AR + 5 : 0)
        g.append('circle').attr('class', 'mm-dot')
          .attr('cy', CY)
          .attr('cx', d => d.x)
          .attr('r', d => d.status === 'active' ? AR : R)
          .attr('fill', d => nodeColor(d.status))
        g.append('path').attr('class', 'mm-check')
          .attr('fill', 'none').attr('stroke', '#fff')
          .attr('stroke-width', 1.5)
          .attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round')
          .attr('transform', d => `translate(${d.x},${CY})`)
          .attr('d', 'M-2.5,0.5 L-0.5,2.5 L2.5,-1.5')
          .attr('opacity', d => d.status === 'completed' ? 1 : 0)
        g.append('text').attr('class', 'mm-label')
          .attr('y', CY + 18).attr('text-anchor', 'middle')
          .attr('font-size', '9px')
          .attr('font-family', 'system-ui, -apple-system, sans-serif')
          .attr('x', d => d.x)
          .attr('font-weight', d => d.status === 'active' ? 600 : 400)
          .attr('fill', d => textColor(d.status))
          .text(d => d.label)
        return g
      },
    )

  nodes.style('cursor', d => d.status !== 'pending' ? 'pointer' : 'default')
    .on('click', (_, d) => { if (d.status !== 'pending') navigate(d) })

  nodes.select('.mm-pulse')
    .attr('cx', d => d.x)
    .classed('mm-pulse-anim', d => d.status === 'active')
    .transition().duration(350)
    .attr('r', d => d.status === 'active' ? AR + 5 : 0)

  nodes.select('.mm-dot')
    .transition().duration(350)
    .attr('cx', d => d.x)
    .attr('r', d => d.status === 'active' ? AR : R)
    .attr('fill', d => nodeColor(d.status))

  nodes.select('.mm-check')
    .attr('transform', d => `translate(${d.x},${CY})`)
    .transition().duration(350)
    .attr('opacity', d => d.status === 'completed' ? 1 : 0)

  nodes.select('.mm-label')
    .attr('x', d => d.x)
    .text(d => d.label)
    .transition().duration(350)
    .attr('font-weight', d => d.status === 'active' ? 600 : 400)
    .attr('fill', d => textColor(d.status))
}

onMounted(() => nextTick(render))
watch(
  [() => route.path, () => route.query.tab, () => simulation.status, isDark],
  () => nextTick(render),
)
</script>

<template>
  <svg
    ref="svgRef"
    :viewBox="`0 0 ${W} ${H}`"
    class="mm-svg"
    role="navigation"
    aria-label="Workflow progress"
  />
</template>

<style scoped>
.mm-svg {
  width: 100%;
  max-width: 320px;
  height: auto;
  overflow: visible;
}

:deep(.mm-pulse-anim) {
  animation: mm-pulse 2s ease-in-out infinite;
}

@keyframes mm-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0; }
}

:deep(.mm-node:hover .mm-dot) {
  filter: brightness(1.15);
}
</style>
