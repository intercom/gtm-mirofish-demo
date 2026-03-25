<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  simulationId: { type: String, default: null },
})

const chartRef = ref(null)
const loading = ref(false)
const error = ref(null)
const coalitionData = ref(null)
const selectedCoalition = ref(null)

let resizeObserver = null
let resizeTimer = null
let simulation = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
}

async function fetchCoalitions() {
  loading.value = true
  error.value = null
  try {
    const id = props.simulationId || 'demo'
    const { data } = await simulationApi.getCoalitions(id)
    coalitionData.value = data.data || data
  } catch (e) {
    error.value = e.message || 'Failed to load coalition data'
  } finally {
    loading.value = false
  }
}

const coalitions = computed(() => coalitionData.value?.coalitions || [])
const edges = computed(() => coalitionData.value?.edges || [])
const swingAgents = computed(() => coalitionData.value?.swing_agents || [])
const polarizationIndex = computed(() => coalitionData.value?.polarization_index ?? 0)

const swingAgentIds = computed(() => new Set(swingAgents.value.map(a => a.id)))

const allNodes = computed(() => {
  const nodes = []
  for (const c of coalitions.value) {
    for (const m of c.members) {
      nodes.push({
        ...m,
        coalitionId: c.id,
        coalitionColor: c.color,
        coalitionLabel: c.label,
        isSwing: swingAgentIds.value.has(m.id),
      })
    }
  }
  for (const s of swingAgents.value) {
    if (!nodes.find(n => n.id === s.id)) {
      const targetCoalition = coalitions.value.find(c => c.id === s.current_coalition)
      nodes.push({
        ...s,
        coalitionId: s.current_coalition,
        coalitionColor: targetCoalition?.color || '#888',
        coalitionLabel: targetCoalition?.label || 'Swing',
        isSwing: true,
      })
    }
  }
  return nodes
})

const allEdges = computed(() => {
  const intraEdges = []
  for (const c of coalitions.value) {
    const memberIds = c.members.map(m => m.id)
    for (let i = 0; i < memberIds.length; i++) {
      for (let j = i + 1; j < memberIds.length; j++) {
        intraEdges.push({
          source: memberIds[i],
          target: memberIds[j],
          weight: c.strength,
          intra: true,
          color: c.color,
        })
      }
    }
  }
  const interEdges = edges.value.map(e => ({
    ...e,
    intra: false,
    color: '#999',
  }))
  return [...intraEdges, ...interEdges]
})

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
  if (!container || !allNodes.value.length) return

  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight || 500
  if (containerWidth === 0) return

  const width = containerWidth
  const height = containerHeight

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const defs = svg.append('defs')

  // Glow filter for swing agents
  const filter = defs.append('filter').attr('id', 'glow')
  filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur')
  const feMerge = filter.append('feMerge')
  feMerge.append('feMergeNode').attr('in', 'coloredBlur')
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

  const g = svg.append('g')

  // Zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })
  svg.call(zoom)

  // Prepare node data with initial positions
  const nodeData = allNodes.value.map((n, i) => ({
    ...n,
    x: width / 2 + (Math.random() - 0.5) * 200,
    y: height / 2 + (Math.random() - 0.5) * 200,
    index: i,
  }))

  const nodeMap = new Map(nodeData.map(n => [n.id, n]))

  // Prepare edge data with resolved references
  const edgeData = allEdges.value
    .filter(e => nodeMap.has(e.source) && nodeMap.has(e.target))
    .map(e => ({
      ...e,
      source: nodeMap.get(e.source),
      target: nodeMap.get(e.target),
    }))

  // Coalition centroids for cluster force
  const coalitionCentroids = {}
  const coalitionCount = coalitions.value.length
  coalitions.value.forEach((c, i) => {
    const angle = (2 * Math.PI * i) / coalitionCount - Math.PI / 2
    coalitionCentroids[c.id] = {
      x: width / 2 + Math.cos(angle) * Math.min(width, height) * 0.25,
      y: height / 2 + Math.sin(angle) * Math.min(width, height) * 0.25,
    }
  })

  // Force simulation
  simulation = d3.forceSimulation(nodeData)
    .force('link', d3.forceLink(edgeData).id(d => d.id).distance(d => d.intra ? 60 : 150).strength(d => d.intra ? 0.4 : 0.05))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2).strength(0.05))
    .force('collision', d3.forceCollide().radius(28))
    .force('cluster', (alpha) => {
      for (const node of nodeData) {
        const centroid = coalitionCentroids[node.coalitionId]
        if (centroid) {
          node.vx += (centroid.x - node.x) * alpha * 0.3
          node.vy += (centroid.y - node.y) * alpha * 0.3
        }
      }
    })

  // Coalition hull groups (drawn behind everything)
  const hullGroup = g.append('g').attr('class', 'hulls')

  // Edge group
  const linkGroup = g.append('g').attr('class', 'links')
  const links = linkGroup.selectAll('line')
    .data(edgeData)
    .join('line')
    .attr('stroke', d => d.color)
    .attr('stroke-width', d => d.intra ? 2 : 1)
    .attr('stroke-opacity', d => d.intra ? 0.3 : 0.15)
    .attr('stroke-dasharray', d => d.intra ? 'none' : '4,4')

  // Node group
  const nodeGroup = g.append('g').attr('class', 'nodes')
  const nodes = nodeGroup.selectAll('g')
    .data(nodeData)
    .join('g')
    .attr('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      })
    )

  // Node circles
  nodes.append('circle')
    .attr('r', d => d.isSwing ? 14 : 12)
    .attr('fill', d => d.coalitionColor)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('filter', d => d.isSwing ? 'url(#glow)' : null)

  // Swing agent pulsing ring
  nodes.filter(d => d.isSwing)
    .append('circle')
    .attr('r', 18)
    .attr('fill', 'none')
    .attr('stroke', d => d.coalitionColor)
    .attr('stroke-width', 1.5)
    .attr('class', 'pulse-ring')

  // Node labels
  nodes.append('text')
    .text(d => d.name?.split(' ')[0] || d.id)
    .attr('dy', 24)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '500')
    .attr('fill', 'var(--color-text-secondary, #555)')
    .attr('pointer-events', 'none')

  // Role sublabels
  nodes.append('text')
    .text(d => d.role || '')
    .attr('dy', 36)
    .attr('text-anchor', 'middle')
    .attr('font-size', '8px')
    .attr('fill', 'var(--color-text-muted, #999)')
    .attr('pointer-events', 'none')

  // Node click handler
  nodes.on('click', (event, d) => {
    event.stopPropagation()
    const c = coalitions.value.find(c => c.id === d.coalitionId)
    selectedCoalition.value = selectedCoalition.value?.id === d.coalitionId ? null : c
  })

  // Background click to deselect
  svg.on('click', () => {
    selectedCoalition.value = null
  })

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
    .style('max-width', '200px')

  nodes.on('mouseenter', (event, d) => {
    const swingInfo = d.isSwing ? '<div style="color:#ff5600;margin-top:4px;font-size:11px">Swing Agent</div>' : ''
    tooltip
      .html(`
        <div style="font-weight:600;color:var(--color-text,#050505)">${d.name}</div>
        <div style="color:var(--color-text-muted,#888);margin-top:2px">${d.role}</div>
        <div style="display:flex;align-items:center;gap:4px;margin-top:4px">
          <span style="width:8px;height:8px;border-radius:50%;background:${d.coalitionColor};display:inline-block"></span>
          <span style="font-size:11px;color:var(--color-text-secondary,#555)">${d.coalitionLabel}</span>
        </div>
        ${swingInfo}
      `)
      .style('opacity', 1)

    d3.select(event.currentTarget).select('circle').transition().duration(100).attr('r', d.isSwing ? 17 : 15)
  })
  .on('mousemove', (event) => {
    const rect = container.getBoundingClientRect()
    tooltip
      .style('left', `${event.clientX - rect.left + 14}px`)
      .style('top', `${event.clientY - rect.top - 10}px`)
  })
  .on('mouseleave', (event, d) => {
    tooltip.style('opacity', 0)
    d3.select(event.currentTarget).select('circle').transition().duration(100).attr('r', d.isSwing ? 14 : 12)
  })

  // Hull drawing function
  function drawHulls() {
    hullGroup.selectAll('path').remove()
    hullGroup.selectAll('text').remove()

    for (const c of coalitions.value) {
      const memberNodes = nodeData.filter(n => n.coalitionId === c.id)
      if (memberNodes.length < 3) {
        // For 2 nodes, draw an ellipse-like shape around them
        if (memberNodes.length === 2) {
          const cx = (memberNodes[0].x + memberNodes[1].x) / 2
          const cy = (memberNodes[0].y + memberNodes[1].y) / 2
          const dx = memberNodes[1].x - memberNodes[0].x
          const dy = memberNodes[1].y - memberNodes[0].y
          const dist = Math.sqrt(dx * dx + dy * dy)

          hullGroup.append('ellipse')
            .attr('cx', cx)
            .attr('cy', cy)
            .attr('rx', dist / 2 + 40)
            .attr('ry', 40)
            .attr('transform', `rotate(${Math.atan2(dy, dx) * 180 / Math.PI}, ${cx}, ${cy})`)
            .attr('fill', c.color)
            .attr('fill-opacity', 0.06 + c.strength * 0.06)
            .attr('stroke', c.color)
            .attr('stroke-opacity', c.strength * 0.4)
            .attr('stroke-width', 1.5)
        }
        continue
      }

      const points = memberNodes.map(n => [n.x, n.y])
      // Expand hull outward for padding
      const hull = d3.polygonHull(points)
      if (!hull) continue

      const centroid = d3.polygonCentroid(hull)
      const expandedHull = hull.map(p => {
        const dx = p[0] - centroid[0]
        const dy = p[1] - centroid[1]
        const dist = Math.sqrt(dx * dx + dy * dy)
        const pad = 35
        return [
          p[0] + (dx / dist) * pad,
          p[1] + (dy / dist) * pad,
        ]
      })

      const hullLine = d3.line().curve(d3.curveCatmullRomClosed.alpha(0.8))

      hullGroup.append('path')
        .attr('d', hullLine(expandedHull))
        .attr('fill', c.color)
        .attr('fill-opacity', 0.06 + c.strength * 0.06)
        .attr('stroke', c.color)
        .attr('stroke-opacity', c.strength * 0.4)
        .attr('stroke-width', 1.5)

      // Coalition label above hull
      hullGroup.append('text')
        .attr('x', centroid[0])
        .attr('y', centroid[1] - Math.max(...memberNodes.map(n => Math.abs(n.y - centroid[1]))) - 30)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .attr('fill', c.color)
        .attr('opacity', 0.8)
        .text(c.label)
    }
  }

  // Simulation tick
  simulation.on('tick', () => {
    links
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodes.attr('transform', d => `translate(${d.x},${d.y})`)

    drawHulls()
  })

  // Cool down faster for responsive feel
  simulation.alpha(1).restart()
  setTimeout(() => simulation.alphaTarget(0), 3000)
}

function selectCoalition(c) {
  selectedCoalition.value = selectedCoalition.value?.id === c.id ? null : c
}

watch(coalitionData, () => {
  nextTick(() => renderChart())
})

onMounted(async () => {
  await fetchCoalitions()
  nextTick(() => renderChart())

  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderChart, 300)
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
  <div class="h-full flex flex-col bg-[var(--color-bg,#fafafa)]">
    <!-- Header bar -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-[var(--color-border)]">
      <div class="flex items-center gap-3">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Coalition Map</h3>
        <span v-if="coalitions.length" class="text-xs text-[var(--color-text-muted)]">
          {{ coalitions.length }} coalitions · {{ allNodes.length }} agents
        </span>
      </div>

      <div v-if="polarizationIndex > 0" class="flex items-center gap-2 text-xs">
        <span class="text-[var(--color-text-muted)]">Polarization</span>
        <div class="w-20 h-1.5 bg-[var(--color-tint)] rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :style="{
              width: `${polarizationIndex * 100}%`,
              background: polarizationIndex > 0.7 ? '#ff5600' : polarizationIndex > 0.4 ? '#FF9800' : '#009900',
            }"
          />
        </div>
        <span
          class="font-medium"
          :style="{ color: polarizationIndex > 0.7 ? '#ff5600' : polarizationIndex > 0.4 ? '#FF9800' : '#009900' }"
        >{{ (polarizationIndex * 100).toFixed(0) }}%</span>
      </div>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- D3 visualization area -->
      <div class="flex-1 relative" ref="chartRef">
        <!-- Loading state -->
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-[var(--color-surface)]/80">
          <div class="flex flex-col items-center gap-2">
            <div class="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
            <span class="text-sm text-[var(--color-text-muted)]">Detecting coalitions...</span>
          </div>
        </div>

        <!-- Error state -->
        <div v-if="error && !coalitionData" class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <p class="text-sm text-[var(--color-text-muted)]">{{ error }}</p>
            <button
              class="mt-2 px-3 py-1.5 text-xs font-medium text-[var(--color-primary)] hover:bg-[var(--color-tint)] rounded-md transition-colors"
              @click="fetchCoalitions"
            >Retry</button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="!loading && !error && !allNodes.length" class="absolute inset-0 flex items-center justify-center">
          <span class="text-sm text-[var(--color-text-muted)]">Coalition data will appear as agents interact</span>
        </div>
      </div>

      <!-- Side panel: selected coalition details -->
      <Transition name="slide-right">
        <div
          v-if="selectedCoalition"
          class="w-72 border-l border-[var(--color-border)] bg-[var(--color-surface)] overflow-y-auto p-4"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <span
                class="w-3 h-3 rounded-full"
                :style="{ background: selectedCoalition.color }"
              />
              <h4 class="text-sm font-semibold text-[var(--color-text)]">{{ selectedCoalition.label }}</h4>
            </div>
            <button
              class="p-1 hover:bg-[var(--color-tint)] rounded transition-colors"
              @click="selectedCoalition = null"
            >
              <svg class="w-4 h-4 text-[var(--color-text-muted)]" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>

          <!-- Strength -->
          <div class="mb-4">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="text-[var(--color-text-muted)]">Cohesion Strength</span>
              <span class="font-medium" :style="{ color: selectedCoalition.color }">
                {{ (selectedCoalition.strength * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="w-full h-1.5 bg-[var(--color-tint)] rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-300"
                :style="{
                  width: `${selectedCoalition.strength * 100}%`,
                  background: selectedCoalition.color,
                }"
              />
            </div>
          </div>

          <!-- Formation -->
          <div class="mb-4 text-xs text-[var(--color-text-muted)]">
            Formed at round {{ selectedCoalition.formation_round }}
          </div>

          <!-- Shared Positions -->
          <div v-if="selectedCoalition.shared_positions?.length" class="mb-4">
            <h5 class="text-xs font-semibold text-[var(--color-text)] mb-2">Shared Positions</h5>
            <ul class="space-y-1.5">
              <li
                v-for="(pos, i) in selectedCoalition.shared_positions"
                :key="i"
                class="text-xs text-[var(--color-text-secondary)] flex gap-2"
              >
                <span class="shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full" :style="{ background: selectedCoalition.color }" />
                {{ pos }}
              </li>
            </ul>
          </div>

          <!-- Members -->
          <div>
            <h5 class="text-xs font-semibold text-[var(--color-text)] mb-2">
              Members ({{ selectedCoalition.members?.length }})
            </h5>
            <div class="space-y-2">
              <div
                v-for="member in selectedCoalition.members"
                :key="member.id"
                class="flex items-center gap-2 p-2 rounded-md bg-[var(--color-tint)]"
              >
                <div
                  class="w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-semibold shrink-0"
                  :style="{ background: selectedCoalition.color }"
                >
                  {{ (member.name || member.id).charAt(0) }}
                </div>
                <div class="min-w-0">
                  <div class="text-xs font-medium text-[var(--color-text)] truncate">{{ member.name }}</div>
                  <div class="text-[10px] text-[var(--color-text-muted)] truncate">{{ member.role }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Bottom legend -->
    <div v-if="coalitions.length" class="flex items-center gap-4 px-5 py-2.5 border-t border-[var(--color-border)] text-xs text-[var(--color-text-muted)]">
      <button
        v-for="c in coalitions"
        :key="c.id"
        class="flex items-center gap-1.5 px-2 py-1 rounded-md transition-colors hover:bg-[var(--color-tint)]"
        :class="{ 'bg-[var(--color-tint)]': selectedCoalition?.id === c.id }"
        @click="selectCoalition(c)"
      >
        <span class="w-2.5 h-2.5 rounded-full" :style="{ background: c.color }" />
        <span>{{ c.label }}</span>
        <span class="text-[var(--color-text-muted)]">({{ c.members?.length }})</span>
      </button>

      <span v-if="swingAgents.length" class="ml-auto flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-full border-2 border-[#ff5600] animate-pulse" />
        {{ swingAgents.length }} swing agent{{ swingAgents.length !== 1 ? 's' : '' }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.2s ease;
}
.slide-right-enter-from,
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(16px);
}

:deep(.pulse-ring) {
  animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% { opacity: 0.3; r: 18; }
  50% { opacity: 0.7; r: 22; }
}
</style>
