<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  agents: { type: Array, default: () => [] },
  relationships: { type: Array, default: () => [] },
  alliances: { type: Array, default: () => [] },
  conflicts: { type: Array, default: () => [] },
  isDemo: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const chartRef = ref(null)
const tooltipRef = ref(null)
const viewMode = ref('network') // 'network' | 'matrix'
const selectedEdge = ref(null)

let resizeObserver = null
let resizeTimer = null
let simulation = null

const hasData = computed(() => props.relationships.length > 0)

const stats = computed(() => {
  const rels = props.relationships
  if (!rels.length) return null
  const positive = rels.filter(r => r.affinity > 0.1).length
  const negative = rels.filter(r => r.affinity < -0.1).length
  const neutral = rels.length - positive - negative
  const avgAffinity = rels.reduce((s, r) => s + r.affinity, 0) / rels.length
  return { positive, negative, neutral, total: rels.length, avgAffinity }
})

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('svg').remove()
  }
}

function affinityColor(affinity) {
  if (affinity > 0.1) return '#009900'
  if (affinity < -0.1) return '#ff5600'
  return '#999'
}

function affinityOpacity(affinity) {
  return 0.3 + Math.abs(affinity) * 0.7
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !hasData.value) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  if (viewMode.value === 'matrix') {
    renderMatrix(container, containerWidth)
  } else {
    renderForceGraph(container, containerWidth)
  }
}

function renderForceGraph(container, containerWidth) {
  const height = 320
  const margin = { top: 8, right: 8, bottom: 8, left: 8 }
  const width = containerWidth - margin.left - margin.right

  // Build node and link data
  const agentSet = new Set()
  const nodes = []
  const links = []

  for (const r of props.relationships) {
    agentSet.add(r.agent_a_id)
    agentSet.add(r.agent_b_id)
    links.push({
      source: r.agent_a_id,
      target: r.agent_b_id,
      affinity: r.affinity,
      interaction_count: r.interaction_count,
      agreement_rate: r.agreement_rate,
      agent_a_name: r.agent_a_name,
      agent_b_name: r.agent_b_name,
      topics: r.topics || [],
    })
  }

  // Add agents from props.agents, or from relationship edges
  for (const agent of props.agents) {
    if (agentSet.has(agent.id)) {
      nodes.push({ id: agent.id, name: agent.name })
      agentSet.delete(agent.id)
    }
  }
  // Any remaining IDs not in props.agents
  for (const id of agentSet) {
    nodes.push({ id, name: `Agent ${id}` })
  }

  // Determine alliance membership for coloring
  const allianceMap = new Map()
  const allianceColors = ['#2068FF', '#ff5600', '#009900', '#9333EA', '#0891B2']
  props.alliances.forEach((a, i) => {
    for (const m of a.members) {
      if (!allianceMap.has(m.id)) {
        allianceMap.set(m.id, allianceColors[i % allianceColors.length])
      }
    }
  })

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', height + margin.top + margin.bottom)
    .attr('viewBox', `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Force simulation
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(d => {
      // Closer for stronger relationships
      return 80 + (1 - Math.abs(d.affinity)) * 60
    }))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(28))

  // Links (edges)
  const link = g.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', d => affinityColor(d.affinity))
    .attr('stroke-opacity', d => affinityOpacity(d.affinity))
    .attr('stroke-width', d => 1 + Math.abs(d.affinity) * 4)
    .attr('stroke-dasharray', d => d.affinity < -0.1 ? '4,3' : 'none')
    .attr('cursor', 'pointer')

  // Link hover/click
  link.on('mouseenter', function (event, d) {
    d3.select(this)
      .attr('stroke-width', 2 + Math.abs(d.affinity) * 5)
    showTooltip(event, d)
  })
  .on('mousemove', (event) => moveTooltip(event))
  .on('mouseleave', function (event, d) {
    d3.select(this)
      .attr('stroke-width', 1 + Math.abs(d.affinity) * 4)
    hideTooltip()
  })
  .on('click', (event, d) => {
    selectedEdge.value = d
  })

  // Nodes
  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('cursor', 'grab')
    .call(drag(simulation))

  // Node circles
  node.append('circle')
    .attr('r', 16)
    .attr('fill', d => allianceMap.get(d.id) || 'var(--color-primary, #2068FF)')
    .attr('fill-opacity', 0.15)
    .attr('stroke', d => allianceMap.get(d.id) || 'var(--color-primary, #2068FF)')
    .attr('stroke-width', 2)

  // Node labels
  node.append('text')
    .text(d => d.name?.split(' ')[0] || `A${d.id}`)
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text, #1a1a1a)')
    .attr('pointer-events', 'none')

  // Animate
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node.attr('transform', d => {
      d.x = Math.max(20, Math.min(width - 20, d.x))
      d.y = Math.max(20, Math.min(height - 20, d.y))
      return `translate(${d.x},${d.y})`
    })
  })
}

function renderMatrix(container, containerWidth) {
  const agents = [...new Map(
    props.relationships.flatMap(r => [
      [r.agent_a_id, r.agent_a_name],
      [r.agent_b_id, r.agent_b_name],
    ])
  ).entries()].map(([id, name]) => ({ id, name }))

  const n = agents.length
  if (n === 0) return

  const cellSize = Math.min(40, (containerWidth - 120) / n)
  const labelWidth = 80
  const margin = { top: labelWidth, right: 16, bottom: 16, left: labelWidth }
  const gridSize = cellSize * n
  const totalWidth = gridSize + margin.left + margin.right
  const totalHeight = gridSize + margin.top + margin.bottom

  // Build lookup
  const affinityLookup = new Map()
  for (const r of props.relationships) {
    const keyA = `${r.agent_a_id}-${r.agent_b_id}`
    const keyB = `${r.agent_b_id}-${r.agent_a_id}`
    affinityLookup.set(keyA, r)
    affinityLookup.set(keyB, r)
  }

  const svg = d3.select(container)
    .append('svg')
    .attr('width', Math.min(totalWidth, containerWidth))
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${totalWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const colorScale = d3.scaleLinear()
    .domain([-1, 0, 1])
    .range(['#ff5600', '#f5f5f5', '#009900'])

  // Cells
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i === j) {
        g.append('rect')
          .attr('x', j * cellSize)
          .attr('y', i * cellSize)
          .attr('width', cellSize - 1)
          .attr('height', cellSize - 1)
          .attr('fill', 'var(--color-tint, #f0f0f0)')
          .attr('rx', 2)
        continue
      }

      const key = `${agents[i].id}-${agents[j].id}`
      const rel = affinityLookup.get(key)
      const affinity = rel ? rel.affinity : 0

      const cell = g.append('rect')
        .attr('x', j * cellSize)
        .attr('y', i * cellSize)
        .attr('width', cellSize - 1)
        .attr('height', cellSize - 1)
        .attr('fill', rel ? colorScale(affinity) : 'var(--color-tint, #f0f0f0)')
        .attr('fill-opacity', rel ? 0.3 + Math.abs(affinity) * 0.7 : 0.3)
        .attr('rx', 2)
        .attr('cursor', rel ? 'pointer' : 'default')

      if (rel) {
        cell.on('mouseenter', function (event) {
          showTooltip(event, rel)
        })
        .on('mousemove', (event) => moveTooltip(event))
        .on('mouseleave', () => hideTooltip())
      }
    }
  }

  // Row labels
  g.selectAll('.row-label')
    .data(agents)
    .join('text')
    .attr('x', -6)
    .attr('y', (_, i) => i * cellSize + cellSize / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text, #1a1a1a)')
    .text(d => d.name?.split(' ')[0] || `A${d.id}`)

  // Column labels
  g.selectAll('.col-label')
    .data(agents)
    .join('text')
    .attr('x', (_, i) => i * cellSize + cellSize / 2)
    .attr('y', -6)
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text, #1a1a1a)')
    .attr('transform', (_, i) => `rotate(-45, ${i * cellSize + cellSize / 2}, -6)`)
    .text(d => d.name?.split(' ')[0] || `A${d.id}`)
}

function drag(sim) {
  return d3.drag()
    .on('start', (event, d) => {
      if (!event.active) sim.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    })
    .on('drag', (event, d) => {
      d.fx = event.x
      d.fy = event.y
    })
    .on('end', (event, d) => {
      if (!event.active) sim.alphaTarget(0)
      d.fx = null
      d.fy = null
    })
}

function showTooltip(event, d) {
  if (!tooltipRef.value) return
  const label = d.affinity > 0.1 ? 'Aligned' : d.affinity < -0.1 ? 'Conflicting' : 'Neutral'
  const color = affinityColor(d.affinity)
  tooltipRef.value.innerHTML = `
    <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">
      ${d.agent_a_name} — ${d.agent_b_name}
    </div>
    <div style="color:${color};font-weight:600">${label} (${d.affinity >= 0 ? '+' : ''}${d.affinity.toFixed(2)})</div>
    <div style="color:var(--color-text-muted,#888);margin-top:2px">
      ${d.interaction_count} interactions · ${Math.round(d.agreement_rate * 100)}% agreement
    </div>
    ${d.topics?.length ? `<div style="color:var(--color-text-muted,#888);margin-top:2px;font-size:11px">Topics: ${d.topics.slice(0, 3).join(', ')}</div>` : ''}
  `
  tooltipRef.value.style.opacity = '1'
  moveTooltip(event)
}

function moveTooltip(event) {
  if (!tooltipRef.value || !chartRef.value) return
  const rect = chartRef.value.getBoundingClientRect()
  tooltipRef.value.style.left = `${event.clientX - rect.left + 12}px`
  tooltipRef.value.style.top = `${event.clientY - rect.top - 40}px`
}

function hideTooltip() {
  if (tooltipRef.value) tooltipRef.value.style.opacity = '0'
}

watch([() => props.relationships.length, () => props.agents.length, viewMode], () => {
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
  if (simulation) simulation.stop()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Agent Relationships</h3>
        <span
          v-if="isDemo"
          class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]"
        >DEMO</span>
      </div>
      <div v-if="hasData" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'network'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'network'"
        >
          Network
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'matrix'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'matrix'"
        >
          Matrix
        </button>
      </div>
    </div>

    <!-- Summary stats -->
    <div v-if="stats" class="flex gap-4 mb-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#009900]" />
        {{ stats.positive }} aligned
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#999]" />
        {{ stats.neutral }} neutral
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#ff5600]" />
        {{ stats.negative }} conflicting
      </span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[320px] text-[var(--color-text-muted)] text-sm">
      <span>Loading relationships...</span>
    </div>

    <!-- Chart -->
    <div v-else-if="hasData" class="relative" ref="chartRef" style="min-height: 320px">
      <div
        ref="tooltipRef"
        class="absolute pointer-events-none opacity-0 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-xs shadow-lg z-10 transition-opacity"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Relationship data will appear as agents interact</span>
    </div>

    <!-- Alliance & Conflict badges -->
    <div v-if="hasData && (alliances.length || conflicts.length)" class="mt-4 space-y-2">
      <div v-if="alliances.length" class="flex flex-wrap gap-2">
        <span class="text-[11px] font-medium text-[var(--color-text-muted)]">Alliances:</span>
        <span
          v-for="(alliance, i) in alliances"
          :key="'a-' + i"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
        >
          {{ alliance.members.map(m => m.name.split(' ')[0]).join(', ') }}
          <span class="text-emerald-500">({{ alliance.avg_affinity >= 0 ? '+' : '' }}{{ alliance.avg_affinity.toFixed(2) }})</span>
        </span>
      </div>
      <div v-if="conflicts.length" class="flex flex-wrap gap-2">
        <span class="text-[11px] font-medium text-[var(--color-text-muted)]">Conflicts:</span>
        <span
          v-for="(conflict, i) in conflicts"
          :key="'c-' + i"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-orange-50 text-orange-700 border border-orange-200"
        >
          {{ conflict.agent_a.name.split(' ')[0] }} vs {{ conflict.agent_b.name.split(' ')[0] }}
          <span class="text-orange-500">({{ conflict.affinity.toFixed(2) }})</span>
        </span>
      </div>
    </div>

    <!-- Selected edge detail -->
    <div
      v-if="selectedEdge"
      class="mt-3 p-3 bg-[var(--color-tint)] rounded-lg text-xs"
    >
      <div class="flex items-center justify-between mb-2">
        <span class="font-semibold text-[var(--color-text)]">
          {{ selectedEdge.agent_a_name }} — {{ selectedEdge.agent_b_name }}
        </span>
        <button
          class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
          @click="selectedEdge = null"
        >
          &times;
        </button>
      </div>
      <div class="grid grid-cols-3 gap-2 text-center">
        <div>
          <div class="text-[var(--color-text-muted)]">Affinity</div>
          <div
            class="font-semibold"
            :style="{ color: affinityColor(selectedEdge.affinity) }"
          >
            {{ selectedEdge.affinity >= 0 ? '+' : '' }}{{ selectedEdge.affinity.toFixed(2) }}
          </div>
        </div>
        <div>
          <div class="text-[var(--color-text-muted)]">Interactions</div>
          <div class="font-semibold text-[var(--color-text)]">{{ selectedEdge.interaction_count }}</div>
        </div>
        <div>
          <div class="text-[var(--color-text-muted)]">Agreement</div>
          <div class="font-semibold text-[var(--color-text)]">{{ Math.round(selectedEdge.agreement_rate * 100) }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>
