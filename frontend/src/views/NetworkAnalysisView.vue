<script setup>
import { ref, computed, onMounted, onUnmounted, watch, inject, nextTick } from 'vue'
import * as d3 from 'd3'
import client from '../api/client'
import { useToast } from '../composables/useToast'
import { useTimelineScrubberInject } from '../composables/useTimelineScrubber'
import AgentNetwork3D from '../components/simulation/AgentNetwork3D.vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const toast = useToast()
const polling = inject('polling', null)
const scrubber = useTimelineScrubberInject()

const viewMode = ref('2d') // '2d' | '3d'

const networkData = ref(null)
const loading = ref(false)
const error = ref(null)
const selectedRound = ref(1)
const maxRound = computed(() => networkData.value?.max_round || 1)

// D3 container refs
const graphEl = ref(null)
const matrixEl = ref(null)
const clusterEl = ref(null)
const flowEl = ref(null)
const timelineEl = ref(null)

// Cleanup handles
let forceSimulation = null
let flowAnimating = false
let resizeObserver = null

// Centrality panel derived data
const topByCentrality = computed(() => {
  if (!networkData.value) return []
  return [...networkData.value.nodes]
    .sort((a, b) => b.centrality - a.centrality)
    .slice(0, 8)
})
const topByBetweenness = computed(() => {
  if (!networkData.value) return []
  return [...networkData.value.nodes]
    .sort((a, b) => b.betweenness - a.betweenness)
    .slice(0, 5)
})
const clusterColors = computed(() => {
  if (!networkData.value) return {}
  const map = {}
  networkData.value.clusters.forEach(c => c.members.forEach(m => (map[m] = c.color)))
  return map
})
const networkStats = computed(() => {
  if (!networkData.value) return null
  const { nodes, edges } = networkData.value
  const avgDegree = nodes.reduce((s, n) => s + n.degree, 0) / nodes.length
  const density = (2 * edges.length) / (nodes.length * (nodes.length - 1))
  return {
    nodes: nodes.length,
    edges: edges.length,
    avgDegree: avgDegree.toFixed(1),
    density: (density * 100).toFixed(1),
  }
})

// Fetch data
async function fetchNetwork(round) {
  loading.value = true
  error.value = null
  try {
    const res = await client.get(`/simulation/${props.taskId}/network`, {
      params: { round },
    })
    if (res.data?.success) {
      networkData.value = res.data.data
      selectedRound.value = res.data.data.selected_round
      await nextTick()
      renderAll()
    }
  } catch (e) {
    error.value = e.message || 'Failed to load network data'
  } finally {
    loading.value = false
  }
}

// Debounced round change
let roundDebounce = null
function onRoundChange(val) {
  selectedRound.value = val
  clearTimeout(roundDebounce)
  roundDebounce = setTimeout(() => fetchNetwork(val), 300)
}

// ─── Force-directed graph ────────────────────────────────────────────────
function renderForceGraph() {
  const el = graphEl.value
  if (!el || !networkData.value) return

  const { nodes, edges, clusters } = networkData.value
  const width = el.clientWidth
  const height = el.clientHeight || 420

  d3.select(el).selectAll('*').remove()
  if (forceSimulation) forceSimulation.stop()

  const colorMap = {}
  clusters.forEach(c => c.members.forEach(m => (colorMap[m] = c.color)))

  // Deep-clone nodes/edges so D3 mutation doesn't corrupt our reactive data
  const simNodes = nodes.map(n => ({ ...n }))
  const simEdges = edges.map(e => ({ source: e.source, target: e.target, weight: e.weight, type: e.type }))

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  const g = svg.append('g')

  svg.call(
    d3.zoom().scaleExtent([0.3, 5]).on('zoom', (event) => g.attr('transform', event.transform)),
  )

  forceSimulation = d3
    .forceSimulation(simNodes)
    .force('link', d3.forceLink(simEdges).id((d) => d.id).distance(90))
    .force('charge', d3.forceManyBody().strength(-180))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(22))

  const link = g
    .append('g')
    .selectAll('line')
    .data(simEdges)
    .join('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', (d) => 0.15 + d.weight * 0.12)
    .attr('stroke-width', (d) => Math.max(0.8, d.weight * 0.7))

  const node = g
    .append('g')
    .selectAll('circle')
    .data(simNodes)
    .join('circle')
    .attr('r', (d) => 6 + d.centrality * 12)
    .attr('fill', (d) => colorMap[d.id] || '#2068FF')
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('cursor', 'grab')
    .call(
      d3
        .drag()
        .on('start', (event, d) => {
          if (!event.active) forceSimulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) forceSimulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        }),
    )

  const label = g
    .append('g')
    .selectAll('text')
    .data(simNodes)
    .join('text')
    .text((d) => d.name.split(' ')[0])
    .attr('font-size', 9)
    .attr('dx', (d) => 8 + d.centrality * 12)
    .attr('dy', 3)
    .attr('fill', 'var(--color-text-secondary)')
    .attr('pointer-events', 'none')

  // Tooltip
  const tooltip = d3
    .select(el)
    .append('div')
    .attr('class', 'network-tooltip')
    .style('position', 'absolute')
    .style('visibility', 'hidden')
    .style('background', 'var(--color-surface)')
    .style('border', '1px solid var(--color-border)')
    .style('border-radius', '6px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', 'var(--shadow-md)')
    .style('pointer-events', 'none')
    .style('z-index', '10')

  node
    .on('mouseover', (event, d) => {
      tooltip
        .style('visibility', 'visible')
        .html(
          `<strong>${d.name}</strong><br/>${d.title} @ ${d.company}<br/>` +
            `Centrality: ${d.centrality} &middot; Degree: ${d.degree}`,
        )
    })
    .on('mousemove', (event) => {
      const rect = el.getBoundingClientRect()
      tooltip
        .style('left', event.clientX - rect.left + 12 + 'px')
        .style('top', event.clientY - rect.top - 10 + 'px')
    })
    .on('mouseout', () => tooltip.style('visibility', 'hidden'))

  forceSimulation.on('tick', () => {
    link
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y)
    node.attr('cx', (d) => d.x).attr('cy', (d) => d.y)
    label.attr('x', (d) => d.x).attr('y', (d) => d.y)
  })
}

// ─── Adjacency matrix heatmap ────────────────────────────────────────────
function renderAdjacencyMatrix() {
  const el = matrixEl.value
  if (!el || !networkData.value) return

  const { nodes, adjacency } = networkData.value
  const n = nodes.length
  const margin = { top: 70, right: 10, bottom: 10, left: 70 }
  const size = Math.min(el.clientWidth - 16, 420)
  const cellSize = (size - margin.left - margin.right) / n

  d3.select(el).selectAll('*').remove()

  const svg = d3.select(el).append('svg').attr('width', size).attr('height', size)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = Math.max(1, ...adjacency.flat())
  const color = d3.scaleSequential(d3.interpolateBlues).domain([0, maxVal])

  // Cells
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      g.append('rect')
        .attr('x', j * cellSize)
        .attr('y', i * cellSize)
        .attr('width', cellSize - 1)
        .attr('height', cellSize - 1)
        .attr('fill', adjacency[i][j] > 0 ? color(adjacency[i][j]) : '#f5f5f5')
        .attr('rx', 1)
    }
  }

  // Top labels (rotated)
  nodes.forEach((nd, i) => {
    g.append('text')
      .attr('x', i * cellSize + cellSize / 2)
      .attr('y', -6)
      .attr('text-anchor', 'start')
      .attr('transform', `rotate(-50, ${i * cellSize + cellSize / 2}, -6)`)
      .attr('font-size', 8)
      .attr('fill', 'var(--color-text-secondary)')
      .text(nd.name.split(' ')[0])
  })
  // Left labels
  nodes.forEach((nd, i) => {
    g.append('text')
      .attr('x', -6)
      .attr('y', i * cellSize + cellSize / 2 + 3)
      .attr('text-anchor', 'end')
      .attr('font-size', 8)
      .attr('fill', 'var(--color-text-secondary)')
      .text(nd.name.split(' ')[0])
  })
}

// ─── Cluster bubble pack ─────────────────────────────────────────────────
function renderClusterView() {
  const el = clusterEl.value
  if (!el || !networkData.value) return

  const { nodes, clusters } = networkData.value
  const width = el.clientWidth
  const height = el.clientHeight || 300

  d3.select(el).selectAll('*').remove()

  const root = d3.hierarchy({
    children: clusters.map((c) => ({
      name: c.label,
      color: c.color,
      children: c.members.map((m) => ({
        name: nodes[m].name,
        value: 1 + nodes[m].centrality * 4,
        color: c.color,
      })),
    })),
  }).sum((d) => d.value)

  d3.pack().size([width, height]).padding(12)(root)

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)

  // Cluster backgrounds
  svg
    .selectAll('circle.cluster-bg')
    .data(root.descendants().filter((d) => d.depth === 1))
    .join('circle')
    .attr('cx', (d) => d.x)
    .attr('cy', (d) => d.y)
    .attr('r', (d) => d.r)
    .attr('fill', (d) => d.data.color)
    .attr('fill-opacity', 0.08)
    .attr('stroke', (d) => d.data.color)
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '4,3')

  // Agent nodes
  svg
    .selectAll('circle.agent')
    .data(root.leaves())
    .join('circle')
    .attr('cx', (d) => d.x)
    .attr('cy', (d) => d.y)
    .attr('r', (d) => d.r)
    .attr('fill', (d) => d.data.color)
    .attr('fill-opacity', 0.65)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1)

  // Cluster labels
  svg
    .selectAll('text.cluster-label')
    .data(root.descendants().filter((d) => d.depth === 1))
    .join('text')
    .attr('x', (d) => d.x)
    .attr('y', (d) => d.y - d.r + 14)
    .attr('text-anchor', 'middle')
    .attr('font-size', 10)
    .attr('font-weight', 600)
    .attr('fill', (d) => d.data.color)
    .text((d) => d.data.name)
}

// ─── Information flow animation ──────────────────────────────────────────
function renderInformationFlow() {
  const el = flowEl.value
  if (!el || !networkData.value) return

  const { nodes, edges } = networkData.value
  const width = el.clientWidth
  const height = 180

  d3.select(el).selectAll('*').remove()
  flowAnimating = true

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  const n = nodes.length
  const xScale = d3.scaleLinear().domain([0, n - 1]).range([40, width - 40])
  const yCenter = height / 2

  // Nodes
  svg
    .selectAll('circle.flow-node')
    .data(nodes)
    .join('circle')
    .attr('cx', (_, i) => xScale(i))
    .attr('cy', yCenter)
    .attr('r', 7)
    .attr('fill', '#2068FF')
    .attr('opacity', 0.5)

  // Labels
  svg
    .selectAll('text.flow-label')
    .data(nodes)
    .join('text')
    .attr('x', (_, i) => xScale(i))
    .attr('y', yCenter + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', 7)
    .attr('fill', 'var(--color-text-muted)')
    .text((d) => d.name.split(' ')[0])

  // Animate particles along strongest edges
  const topEdges = [...edges].sort((a, b) => b.weight - a.weight).slice(0, 12)

  function animateParticle(edge) {
    if (!flowAnimating) return
    const sx = xScale(typeof edge.source === 'object' ? edge.source.id : edge.source)
    const tx = xScale(typeof edge.target === 'object' ? edge.target.id : edge.target)
    const arcHeight = Math.min(60, Math.abs(tx - sx) * 0.35)

    const particle = svg.append('circle').attr('r', 2.5).attr('fill', '#ff5600').attr('opacity', 0.85)

    particle
      .attr('cx', sx)
      .attr('cy', yCenter)
      .transition()
      .duration(1800 + Math.random() * 1200)
      .ease(d3.easeLinear)
      .attrTween('cx', () => d3.interpolateNumber(sx, tx))
      .attrTween('cy', () => {
        return (t) => yCenter - arcHeight * Math.sin(Math.PI * t)
      })
      .attr('opacity', 0)
      .remove()
      .on('end', () => {
        if (flowAnimating) setTimeout(() => animateParticle(edge), 500 + Math.random() * 2000)
      })
  }

  topEdges.forEach((edge, i) => {
    setTimeout(() => animateParticle(edge), i * 250)
  })
}

// ─── Communication pattern timeline ──────────────────────────────────────
function renderCommTimeline() {
  const el = timelineEl.value
  if (!el || !networkData.value) return

  const { nodes, comm_patterns, selected_round } = networkData.value
  const n = nodes.length
  const width = el.clientWidth - 16
  const height = 240
  const margin = { top: 16, right: 16, bottom: 30, left: 56 }

  d3.select(el).selectAll('*').remove()

  // Create unique pair keys
  const pairSet = new Set()
  comm_patterns.forEach((c) => {
    pairSet.add(`${Math.min(c.source, c.target)}-${Math.max(c.source, c.target)}`)
  })
  const pairs = [...pairSet].slice(0, 20) // cap for readability

  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const xScale = d3.scaleLinear().domain([0, selected_round]).range([0, innerW])
  const yScale = d3.scaleBand().domain(pairs).range([0, innerH]).padding(0.15)
  const sentimentColor = d3.scaleSequential(d3.interpolateRdYlGn).domain([-0.3, 1.0])

  // Axes
  g.append('g')
    .attr('transform', `translate(0,${innerH})`)
    .call(d3.axisBottom(xScale).ticks(6).tickFormat((d) => `R${d}`))
    .selectAll('text')
    .attr('font-size', 8)

  g.append('g')
    .call(
      d3.axisLeft(yScale).tickFormat((pair) => {
        const [a, b] = pair.split('-').map(Number)
        return `${nodes[a]?.name?.split(' ')[0] || '?'}-${nodes[b]?.name?.split(' ')[0] || '?'}`
      }),
    )
    .selectAll('text')
    .attr('font-size', 7)

  // Data marks
  const filteredPatterns = comm_patterns.filter((c) => {
    const key = `${Math.min(c.source, c.target)}-${Math.max(c.source, c.target)}`
    return pairs.includes(key)
  })

  g.selectAll('circle')
    .data(filteredPatterns)
    .join('circle')
    .attr('cx', (d) => xScale(d.round))
    .attr('cy', (d) => {
      const key = `${Math.min(d.source, d.target)}-${Math.max(d.source, d.target)}`
      return (yScale(key) || 0) + yScale.bandwidth() / 2
    })
    .attr('r', (d) => 2 + d.count * 1.5)
    .attr('fill', (d) => sentimentColor(d.sentiment))
    .attr('opacity', 0.75)
}

// ─── Render all ──────────────────────────────────────────────────────────
function renderAll() {
  if (!networkData.value) return
  if (viewMode.value === '2d') renderForceGraph()
  renderAdjacencyMatrix()
  renderClusterView()
  renderInformationFlow()
  renderCommTimeline()
}

// Re-render 2D graph when switching back from 3D
watch(viewMode, (mode) => {
  if (mode === '2d' && networkData.value) {
    nextTick(() => renderForceGraph())
  }
})

function cleanup() {
  flowAnimating = false
  if (forceSimulation) {
    forceSimulation.stop()
    forceSimulation = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
}

// Sync with timeline scrubber when round changes
if (scrubber) {
  watch(() => scrubber.currentRound.value, (round) => {
    if (round > 0 && round !== selectedRound.value) {
      onRoundChange(round)
    }
  })
}

onMounted(() => {
  const maxR = scrubber?.currentRound?.value
    || polling?.runStatus?.value?.current_round
    || polling?.runStatus?.value?.total_rounds
    || 144
  fetchNetwork(maxR)

  resizeObserver = new ResizeObserver(() => {
    if (viewMode.value === '2d') {
      clearTimeout(roundDebounce)
      roundDebounce = setTimeout(renderAll, 200)
    }
  })
  if (graphEl.value) resizeObserver.observe(graphEl.value)
})

onUnmounted(() => {
  cleanup()
  clearTimeout(roundDebounce)
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 md:px-6 py-6 space-y-5">
    <!-- Header + Round selector -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-[var(--color-text)]">Network Analysis</h1>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Agent influence and communication patterns
        </p>
      </div>
      <div class="flex items-center gap-3">
        <label class="text-xs text-[var(--color-text-secondary)]">Round</label>
        <input
          type="range"
          :value="selectedRound"
          :min="1"
          :max="maxRound"
          @input="onRoundChange(Number($event.target.value))"
          class="w-36 accent-[#2068FF]"
        />
        <span class="text-xs font-mono tabular-nums text-[var(--color-text)] min-w-[5ch] text-right">
          {{ selectedRound }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="loading && !networkData"
      class="flex items-center justify-center py-20 text-sm text-[var(--color-text-muted)]"
    >
      <svg class="w-5 h-5 animate-spin mr-2 text-[#2068FF]" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading network data...
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="rounded-lg border border-[var(--color-error)] bg-[var(--color-error-light)] p-4 text-sm text-[var(--color-error)]"
    >
      {{ error }}
    </div>

    <!-- Content -->
    <template v-if="networkData">
      <!-- Top: Force graph (2/3) + Centrality (1/3) -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Agent Network Graph -->
        <div
          class="lg:col-span-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden"
        >
          <div class="px-4 py-2.5 border-b border-[var(--color-border)] flex items-center justify-between">
            <h2 class="text-sm font-semibold text-[var(--color-text)]">Agent Network Graph</h2>
            <div class="flex items-center gap-3">
              <!-- 2D/3D toggle -->
              <div class="flex items-center bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-lg p-0.5">
                <button
                  @click="viewMode = '2d'"
                  class="px-2.5 py-0.5 text-xs font-medium rounded-md transition-all duration-200"
                  :class="viewMode === '2d'
                    ? 'bg-[#2068FF] text-white shadow-sm'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
                >2D</button>
                <button
                  @click="viewMode = '3d'"
                  class="px-2.5 py-0.5 text-xs font-medium rounded-md transition-all duration-200"
                  :class="viewMode === '3d'
                    ? 'bg-[#2068FF] text-white shadow-sm'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
                >3D</button>
              </div>
              <div v-if="networkStats" class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                <span>{{ networkStats.nodes }} nodes</span>
                <span>{{ networkStats.edges }} edges</span>
                <span>Density {{ networkStats.density }}%</span>
              </div>
            </div>
          </div>
          <div v-show="viewMode === '2d'" ref="graphEl" class="h-[420px] relative" />
          <AgentNetwork3D
            v-if="viewMode === '3d'"
            :networkData="networkData"
            :clusterColors="clusterColors"
            class="h-[420px]"
          />
        </div>

        <!-- Centrality Analysis -->
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
          <div class="px-4 py-2.5 border-b border-[var(--color-border)]">
            <h2 class="text-sm font-semibold text-[var(--color-text)]">Centrality Analysis</h2>
          </div>
          <div class="p-3 space-y-4 max-h-[420px] overflow-y-auto">
            <!-- Top by centrality -->
            <div>
              <h3 class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-2">
                Top by Degree Centrality
              </h3>
              <div class="space-y-1.5">
                <div
                  v-for="agent in topByCentrality"
                  :key="agent.id"
                  class="flex items-center gap-2 text-xs"
                >
                  <span
                    class="w-2.5 h-2.5 rounded-full shrink-0"
                    :style="{ background: clusterColors[agent.id] || '#2068FF' }"
                  />
                  <span class="flex-1 truncate text-[var(--color-text)]">{{ agent.name }}</span>
                  <span class="font-mono tabular-nums text-[var(--color-text-secondary)]">
                    {{ agent.centrality }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Top by betweenness -->
            <div>
              <h3 class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-2">
                Top by Betweenness
              </h3>
              <div class="space-y-1.5">
                <div
                  v-for="agent in topByBetweenness"
                  :key="agent.id"
                  class="flex items-center gap-2 text-xs"
                >
                  <span
                    class="w-2.5 h-2.5 rounded-full shrink-0"
                    :style="{ background: clusterColors[agent.id] || '#2068FF' }"
                  />
                  <span class="flex-1 truncate text-[var(--color-text)]">{{ agent.name }}</span>
                  <span class="font-mono tabular-nums text-[var(--color-text-secondary)]">
                    {{ agent.betweenness }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Cluster summary -->
            <div>
              <h3 class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-2">
                Clusters
              </h3>
              <div class="space-y-1.5">
                <div
                  v-for="cluster in networkData.clusters"
                  :key="cluster.id"
                  class="flex items-center gap-2 text-xs"
                >
                  <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: cluster.color }" />
                  <span class="flex-1 text-[var(--color-text)]">{{ cluster.label }}</span>
                  <span class="font-mono tabular-nums text-[var(--color-text-muted)]">
                    {{ cluster.members.length }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Stats -->
            <div v-if="networkStats" class="border-t border-[var(--color-border)] pt-3">
              <h3 class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-2">
                Network Stats
              </h3>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div class="bg-[var(--color-bg)] rounded px-2 py-1.5">
                  <div class="text-[var(--color-text-muted)]">Avg Degree</div>
                  <div class="font-semibold text-[var(--color-text)]">{{ networkStats.avgDegree }}</div>
                </div>
                <div class="bg-[var(--color-bg)] rounded px-2 py-1.5">
                  <div class="text-[var(--color-text-muted)]">Density</div>
                  <div class="font-semibold text-[var(--color-text)]">{{ networkStats.density }}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Middle: Adjacency (1/2) + Cluster view (1/2) -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
          <div class="px-4 py-2.5 border-b border-[var(--color-border)]">
            <h2 class="text-sm font-semibold text-[var(--color-text)]">Adjacency Matrix</h2>
          </div>
          <div ref="matrixEl" class="p-2 flex justify-center" />
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
          <div class="px-4 py-2.5 border-b border-[var(--color-border)]">
            <h2 class="text-sm font-semibold text-[var(--color-text)]">Cluster View</h2>
          </div>
          <div ref="clusterEl" class="h-[320px]" />
        </div>
      </div>

      <!-- Bottom: Information flow + Comm timeline -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        <div class="px-4 py-2.5 border-b border-[var(--color-border)]">
          <h2 class="text-sm font-semibold text-[var(--color-text)]">Information Flow</h2>
        </div>
        <div ref="flowEl" class="h-[180px]" />
      </div>

      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        <div class="px-4 py-2.5 border-b border-[var(--color-border)]">
          <h2 class="text-sm font-semibold text-[var(--color-text)]">Communication Pattern Timeline</h2>
        </div>
        <div ref="timelineEl" class="p-2" />
      </div>
    </template>
  </div>
</template>
