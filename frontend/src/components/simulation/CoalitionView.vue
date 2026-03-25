<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  coalitions: { type: Array, default: () => [] },
  polarizationIndex: { type: Number, default: 0 },
})

const emit = defineEmits(['select-coalition', 'select-agent'])

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null
let simulation = null

const COALITION_COLORS = [
  '#2068FF', '#ff5600', '#009900', '#9333ea', '#ea580c',
  '#0891b2', '#be185d', '#4f46e5', '#059669', '#d97706',
]

const selectedCoalition = ref(null)

const stats = computed(() => {
  const total = props.coalitions.reduce((s, c) => s + c.members.length, 0)
  const strongest = props.coalitions.length
    ? props.coalitions.reduce((a, b) => a.strength > b.strength ? a : b)
    : null
  return { totalAgents: total, strongest }
})

function getColor(coalitionId) {
  return COALITION_COLORS[coalitionId % COALITION_COLORS.length]
}

function clearChart() {
  if (simulation) {
    simulation.stop()
    simulation = null
  }
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.coalitions.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const width = containerWidth
  const height = 380
  const margin = { top: 10, right: 10, bottom: 10, left: 10 }

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const innerWidth = width - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom

  // Build nodes and links from coalition data
  const nodes = []
  const links = []

  for (const coalition of props.coalitions) {
    const color = getColor(coalition.coalition_id)
    for (const member of coalition.members) {
      nodes.push({
        id: member.agent_id,
        name: member.agent_name,
        coalitionId: coalition.coalition_id,
        color,
        strength: coalition.strength,
      })
    }
    // Intra-coalition links
    for (let i = 0; i < coalition.members.length; i++) {
      for (let j = i + 1; j < coalition.members.length; j++) {
        links.push({
          source: coalition.members[i].agent_id,
          target: coalition.members[j].agent_id,
          strength: coalition.strength,
          color,
        })
      }
    }
  }

  // Weak cross-coalition links for layout tension
  for (let i = 0; i < props.coalitions.length; i++) {
    for (let j = i + 1; j < props.coalitions.length; j++) {
      const a = props.coalitions[i].members[0]
      const b = props.coalitions[j].members[0]
      if (a && b) {
        links.push({
          source: a.agent_id,
          target: b.agent_id,
          strength: 0.05,
          color: 'rgba(0,0,0,0.05)',
        })
      }
    }
  }

  // Force simulation
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).strength(d => d.strength * 0.3))
    .force('charge', d3.forceManyBody().strength(-80))
    .force('center', d3.forceCenter(innerWidth / 2, innerHeight / 2))
    .force('collision', d3.forceCollide().radius(20))
    .force('x', d3.forceX(innerWidth / 2).strength(0.05))
    .force('y', d3.forceY(innerHeight / 2).strength(0.05))

  // Convex hull groups
  const hullGroup = g.append('g').attr('class', 'hulls')

  // Links
  const link = g.append('g')
    .selectAll('line')
    .data(links.filter(l => l.strength > 0.1))
    .join('line')
    .attr('stroke', d => d.color)
    .attr('stroke-opacity', d => Math.max(0.1, d.strength * 0.4))
    .attr('stroke-width', d => Math.max(0.5, d.strength * 2))

  // Nodes
  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('cursor', 'pointer')
    .call(d3.drag()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded)
    )

  node.append('circle')
    .attr('r', 8)
    .attr('fill', d => d.color)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .on('mouseenter', function (event, d) {
      d3.select(this).transition().duration(100).attr('r', 12)
      showTooltip(event, d)
    })
    .on('mouseleave', function () {
      d3.select(this).transition().duration(100).attr('r', 8)
      hideTooltip()
    })
    .on('click', (event, d) => {
      emit('select-agent', d)
    })

  node.append('text')
    .text(d => d.name.split(' ')[0])
    .attr('dy', -14)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-secondary, #666)')
    .attr('pointer-events', 'none')

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

  function showTooltip(event, d) {
    const coalition = props.coalitions.find(c => c.coalition_id === d.coalitionId)
    tooltip.html(`
      <div style="font-weight:600;color:var(--color-text,#050505)">${d.name}</div>
      <div style="color:${d.color};font-size:11px;margin-top:2px">
        ${coalition?.label || `Coalition ${d.coalitionId}`}
      </div>
      <div style="color:var(--color-text-muted,#888);font-size:11px;margin-top:2px">
        Strength: ${(d.strength * 100).toFixed(0)}%
      </div>
    `).style('opacity', 1)
    positionTooltip(event)
  }

  function positionTooltip(event) {
    const rect = container.getBoundingClientRect()
    tooltip
      .style('left', `${event.clientX - rect.left + 12}px`)
      .style('top', `${event.clientY - rect.top - 40}px`)
  }

  function hideTooltip() {
    tooltip.style('opacity', 0)
  }

  // Tick handler: update positions + draw convex hulls
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node.attr('transform', d => {
      d.x = Math.max(16, Math.min(innerWidth - 16, d.x))
      d.y = Math.max(16, Math.min(innerHeight - 16, d.y))
      return `translate(${d.x},${d.y})`
    })

    // Draw convex hulls around each coalition
    hullGroup.selectAll('path').remove()
    const groups = d3.group(nodes, d => d.coalitionId)
    for (const [coalitionId, members] of groups) {
      if (members.length < 3) {
        // For 2 members, draw an ellipse-like shape
        if (members.length === 2) {
          const [a, b] = members
          const mx = (a.x + b.x) / 2
          const my = (a.y + b.y) / 2
          const dx = b.x - a.x
          const dy = b.y - a.y
          const len = Math.sqrt(dx * dx + dy * dy)
          const pad = 24
          hullGroup.append('ellipse')
            .attr('cx', mx)
            .attr('cy', my)
            .attr('rx', len / 2 + pad)
            .attr('ry', pad)
            .attr('transform', `rotate(${Math.atan2(dy, dx) * 180 / Math.PI}, ${mx}, ${my})`)
            .attr('fill', getColor(coalitionId))
            .attr('fill-opacity', 0.06)
            .attr('stroke', getColor(coalitionId))
            .attr('stroke-opacity', 0.2)
            .attr('stroke-width', 1.5)
            .attr('stroke-dasharray', '4,3')
        }
        continue
      }
      const points = members.map(d => [d.x, d.y])
      const hull = d3.polygonHull(points)
      if (hull) {
        // Expand hull slightly for padding
        const centroid = d3.polygonCentroid(hull)
        const expandedHull = hull.map(([x, y]) => {
          const dx = x - centroid[0]
          const dy = y - centroid[1]
          const len = Math.sqrt(dx * dx + dy * dy)
          const pad = 20
          return [x + (dx / len) * pad, y + (dy / len) * pad]
        })

        hullGroup.append('path')
          .attr('d', `M${expandedHull.join('L')}Z`)
          .attr('fill', getColor(coalitionId))
          .attr('fill-opacity', 0.06)
          .attr('stroke', getColor(coalitionId))
          .attr('stroke-opacity', 0.2)
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '4,3')
      }
    }
  })

  // Drag handlers
  function dragStarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }

  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
    positionTooltip(event.sourceEvent)
  }

  function dragEnded(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
}

function selectCoalition(coalition) {
  selectedCoalition.value = selectedCoalition.value?.coalition_id === coalition.coalition_id
    ? null
    : coalition
  emit('select-coalition', selectedCoalition.value)
}

watch(() => props.coalitions, () => nextTick(renderChart), { deep: true })

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
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Coalition Map</h3>
      <div v-if="coalitions.length" class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
        <span>{{ stats.totalAgents }} agents</span>
        <span class="text-[var(--color-border)]">|</span>
        <span>{{ coalitionCount }} coalitions</span>
        <span class="text-[var(--color-border)]">|</span>
        <span>Polarization: {{ (polarizationIndex * 100).toFixed(0) }}%</span>
      </div>
    </div>

    <!-- D3 Canvas -->
    <div v-if="coalitions.length" ref="chartRef" class="relative" style="height: 380px" />

    <div v-else class="flex items-center justify-center h-[380px] text-[var(--color-text-muted)] text-sm">
      <span>Coalition data will appear after simulation completes</span>
    </div>

    <!-- Coalition Legend -->
    <div v-if="coalitions.length" class="mt-4 flex flex-wrap gap-2">
      <button
        v-for="c in coalitions"
        :key="c.coalition_id"
        class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all"
        :class="selectedCoalition?.coalition_id === c.coalition_id
          ? 'border-current shadow-sm'
          : 'border-[var(--color-border)] hover:border-[var(--color-text-muted)]'"
        :style="{ color: getColor(c.coalition_id) }"
        @click="selectCoalition(c)"
      >
        <span
          class="w-2.5 h-2.5 rounded-full"
          :style="{ background: getColor(c.coalition_id) }"
        />
        {{ c.label || `Coalition ${c.coalition_id}` }}
        <span class="text-[var(--color-text-muted)]">({{ c.size }})</span>
      </button>
    </div>
  </div>
</template>
