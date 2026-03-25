<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import { useGraphStore } from '@/stores/graph'

const props = defineProps({
  graphId: { type: String, default: 'demo' },
})

const store = useGraphStore()

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

// D3 refs
const svgRef = ref(null)
const containerRef = ref(null)
let simulation = null
let svg = null
let zoomGroup = null
let resizeObserver = null
let resizeTimer = null
let themeObserver = null

// Local UI state
const searchInput = ref('')
const showControls = ref(false)
let searchDebounce = null

// Centrality for the currently selected node
const centralityForSelected = computed(() => {
  if (!store.selectedNode) return 0
  const c = computeCentrality(store.nodes, store.edges)
  return c[store.selectedNode.uuid] || 0
})

// Entity type color mapping (same palette as GraphPanel)
const TYPE_COLORS = {
  persona: '#ff5600', person: '#ff5600', agent: '#ff5600', user: '#ff5600',
  customer: '#ff5600', stakeholder: '#ff5600', role: '#ff5600',
  topic: '#2068FF', theme: '#2068FF', subject: '#2068FF', concept: '#2068FF',
  category: '#2068FF', product: '#2068FF', feature: '#2068FF', technology: '#2068FF',
  relationship: '#AA00FF', interaction: '#AA00FF', connection: '#AA00FF',
  event: '#AA00FF', action: '#AA00FF', process: '#AA00FF',
}
const DEFAULT_COLOR = '#667'
const GENERIC_LABELS = new Set(['Entity', 'Node'])

function getNodeColor(labels) {
  const meaningful = (labels || []).filter(l => !GENERIC_LABELS.has(l))
  if (!meaningful.length) return DEFAULT_COLOR
  const label = meaningful[0].toLowerCase()
  for (const [key, color] of Object.entries(TYPE_COLORS)) {
    if (label.includes(key)) return color
  }
  const palette = ['#ff5600', '#2068FF', '#AA00FF']
  let hash = 0
  for (const ch of label) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0
  return palette[Math.abs(hash) % palette.length]
}

function getEntityType(labels) {
  const meaningful = (labels || []).filter(l => !GENERIC_LABELS.has(l))
  return meaningful[0] || 'Entity'
}

function computeCentrality(nodes, edges) {
  const degree = {}
  for (const n of nodes) degree[n.uuid] = 0
  for (const e of edges) {
    if (degree[e.source_node_uuid] !== undefined) degree[e.source_node_uuid]++
    if (degree[e.target_node_uuid] !== undefined) degree[e.target_node_uuid]++
  }
  const max = Math.max(1, ...Object.values(degree))
  const result = {}
  for (const [id, d] of Object.entries(degree)) result[id] = d / max
  return result
}

// Computed: entity type stats with colors
const entityTypeStats = computed(() =>
  store.entityTypes.map(({ type, count }) => ({
    type,
    count,
    color: getNodeColor([type]),
    active: !store.activeTypeFilters.length || store.activeTypeFilters.includes(type),
  })),
)

// Search handler with debounce
function onSearchInput() {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    store.searchQuery = searchInput.value
    if (searchInput.value.trim()) {
      store.searchGraph(props.graphId, searchInput.value)
    } else {
      store.highlightedNodeIds = new Set()
    }
    nextTick(() => updateNodeAppearance())
  }, 250)
}

function clearSearch() {
  searchInput.value = ''
  store.searchQuery = ''
  store.highlightedNodeIds = new Set()
  nextTick(() => updateNodeAppearance())
}

// Update node appearance without re-rendering the full graph
function updateNodeAppearance() {
  if (!zoomGroup) return
  const hasHighlight = store.highlightedNodeIds.size > 0

  zoomGroup.selectAll('.node-group')
    .transition()
    .duration(200)
    .style('opacity', d => {
      if (!hasHighlight) return 1
      return store.highlightedNodeIds.has(d.id) ? 1 : 0.15
    })

  zoomGroup.selectAll('.edge-line')
    .transition()
    .duration(200)
    .style('opacity', d => {
      if (!hasHighlight) return 1
      return (store.highlightedNodeIds.has(d.source.id || d.source) &&
              store.highlightedNodeIds.has(d.target.id || d.target)) ? 1 : 0.08
    })
}

// --- Main Graph Rendering ---

function renderGraph() {
  if (!svgRef.value) return

  const graphNodes = store.filteredNodes
  const graphEdges = store.filteredEdges

  if (!graphNodes.length) {
    d3.select(svgRef.value).selectAll('*').remove()
    return
  }

  const dark = isDarkMode()
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  const centrality = computeCentrality(graphNodes, graphEdges)

  const nodeMap = new Map()
  const nodes = graphNodes.map(n => {
    const obj = {
      id: n.uuid,
      name: n.name,
      labels: n.labels,
      summary: n.summary || '',
      attributes: n.attributes || {},
      centrality: centrality[n.uuid] || 0,
      color: getNodeColor(n.labels),
      radius: 6 + (centrality[n.uuid] || 0) * 18,
    }
    nodeMap.set(n.uuid, obj)
    return obj
  })

  const links = graphEdges
    .filter(e => nodeMap.has(e.source_node_uuid) && nodeMap.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
    }))

  // Clear previous render
  if (simulation) simulation.stop()
  d3.select(svgRef.value).selectAll('*').remove()

  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  const zoom = d3.zoom()
    .scaleExtent([0.2, 5])
    .on('zoom', (event) => {
      zoomGroup.attr('transform', event.transform)
    })
  svg.call(zoom)

  zoomGroup = svg.append('g')

  // Arrow marker
  svg.append('defs').append('marker')
    .attr('id', 'kg-arrow')
    .attr('viewBox', '0 -4 8 8')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-4L8,0L0,4')
    .attr('fill', dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')

  // Force simulation
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(store.linkDistance))
    .force('charge', d3.forceManyBody().strength(store.chargeStrength))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 4))

  // Edge lines
  const link = zoomGroup.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('class', 'edge-line')
    .attr('stroke', dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)')
    .attr('stroke-width', 1)
    .attr('marker-end', 'url(#kg-arrow)')
    .style('opacity', 0)

  // Edge labels
  const edgeLabel = zoomGroup.append('g')
    .selectAll('text')
    .data(links)
    .join('text')
    .text(d => d.name)
    .attr('fill', dark ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.3)')
    .attr('font-size', '8px')
    .attr('text-anchor', 'middle')
    .style('pointer-events', 'none')
    .style('opacity', 0)

  // Node groups
  const node = zoomGroup.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', 'node-group')
    .style('cursor', 'pointer')
    .style('opacity', 0)
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended)
    )
    .on('click', (event, d) => {
      event.stopPropagation()
      store.selectNode(d.id)
    })

  // Outer glow circle
  node.append('circle')
    .attr('r', d => d.radius + 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.2)

  // Main circle
  node.append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => d.color)
    .attr('stroke', d => d.color)
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.4)
    .attr('fill-opacity', 0.85)

  // Node label
  node.append('text')
    .text(d => d.name)
    .attr('dy', d => d.radius + 14)
    .attr('text-anchor', 'middle')
    .attr('fill', dark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)')
    .attr('font-size', '10px')
    .style('pointer-events', 'none')

  // Staggered entrance animations
  node.transition()
    .delay((d, i) => i * 50)
    .duration(400)
    .style('opacity', 1)

  link.transition()
    .delay((d, i) => nodes.length * 50 + i * 20)
    .duration(300)
    .style('opacity', 1)

  edgeLabel.transition()
    .delay((d, i) => nodes.length * 50 + i * 20)
    .duration(300)
    .style('opacity', 1)

  // Tick handler
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    edgeLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  // Click background to deselect
  svg.on('click', () => store.clearSelection())

  // Apply search highlights if active
  nextTick(() => updateNodeAppearance())
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

function dragged(event, d) {
  d.fx = event.x
  d.fy = event.y
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

// Physics controls: reheat simulation when changed
function onChargeChange(e) {
  store.chargeStrength = Number(e.target.value)
  if (simulation) {
    simulation.force('charge', d3.forceManyBody().strength(store.chargeStrength))
    simulation.alpha(0.5).restart()
  }
}

function onDistanceChange(e) {
  store.linkDistance = Number(e.target.value)
  if (simulation) {
    simulation.force('link').distance(store.linkDistance)
    simulation.alpha(0.5).restart()
  }
}

// Re-render when filtered data changes (covers type filter + data load)
watch(() => [store.filteredNodes.length, store.filteredEdges.length], () => {
  if (store.filteredNodes.length) {
    nextTick(() => renderGraph())
  }
})

// Lifecycle
onMounted(async () => {
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (store.filteredNodes.length) renderGraph()
    }, 200)
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'class' && store.nodes.length) {
        renderGraph()
        break
      }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

  await store.fetchGraphData(props.graphId)
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
  clearTimeout(resizeTimer)
  clearTimeout(searchDebounce)
})
</script>

<template>
  <div ref="containerRef" class="w-full h-full relative overflow-hidden bg-[#f8f9fa] dark:bg-[#0a0a1a] rounded-xl">

    <!-- Top toolbar -->
    <div class="absolute top-4 left-4 right-4 z-10 flex items-center gap-3">
      <!-- Search -->
      <div class="relative flex-1 max-w-xs">
        <input
          v-model="searchInput"
          @input="onSearchInput"
          type="text"
          placeholder="Search entities..."
          class="w-full pl-8 pr-8 py-1.5 text-xs rounded-lg bg-white/80 dark:bg-white/10 border border-black/10 dark:border-white/10 text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[#2068FF] backdrop-blur-sm"
        />
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        <button
          v-if="searchInput"
          @click="clearSearch"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-sm leading-none"
        >&times;</button>
      </div>

      <!-- Physics toggle -->
      <button
        @click="showControls = !showControls"
        class="px-2.5 py-1.5 text-xs rounded-lg bg-white/80 dark:bg-white/10 border border-black/10 dark:border-white/10 text-[var(--color-text-secondary)] hover:text-[var(--color-text)] backdrop-blur-sm transition-colors"
        :class="{ '!border-[#2068FF] !text-[#2068FF]': showControls }"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75" />
        </svg>
      </button>

      <!-- Node/edge count -->
      <span class="text-[10px] text-[var(--color-text-muted)] tabular-nums whitespace-nowrap">
        {{ store.filteredNodes.length }} nodes · {{ store.filteredEdges.length }} edges
      </span>
    </div>

    <!-- Physics controls dropdown -->
    <Transition name="fade">
      <div
        v-if="showControls"
        class="absolute top-14 right-4 z-20 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border border-black/10 dark:border-white/10 rounded-lg p-4 w-56"
      >
        <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-3">Physics</h4>
        <div class="space-y-3">
          <div>
            <div class="flex justify-between text-[10px] text-[var(--color-text-muted)] mb-1">
              <span>Charge</span>
              <span class="tabular-nums">{{ store.chargeStrength }}</span>
            </div>
            <input
              type="range" min="-800" max="-50" :value="store.chargeStrength"
              @input="onChargeChange"
              class="w-full h-1 rounded-full appearance-none bg-black/10 dark:bg-white/10 accent-[#2068FF]"
            />
          </div>
          <div>
            <div class="flex justify-between text-[10px] text-[var(--color-text-muted)] mb-1">
              <span>Link Distance</span>
              <span class="tabular-nums">{{ store.linkDistance }}</span>
            </div>
            <input
              type="range" min="40" max="300" :value="store.linkDistance"
              @input="onDistanceChange"
              class="w-full h-1 rounded-full appearance-none bg-black/10 dark:bg-white/10 accent-[#2068FF]"
            />
          </div>
        </div>
      </div>
    </Transition>

    <!-- Loading state -->
    <Transition name="fade">
      <div
        v-if="store.loading"
        class="absolute inset-0 flex items-center justify-center z-30 bg-[var(--color-surface)]/60 backdrop-blur-sm"
      >
        <div class="flex flex-col items-center gap-3">
          <div class="w-8 h-8 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin" />
          <span class="text-xs text-[var(--color-text-muted)]">Loading graph...</span>
        </div>
      </div>
    </Transition>

    <!-- Error state -->
    <div
      v-if="store.error && !store.loading"
      class="absolute inset-0 flex items-center justify-center z-20 bg-[var(--color-surface)]/80 backdrop-blur-sm"
    >
      <div class="flex flex-col items-center text-center max-w-md">
        <div class="w-14 h-14 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
          <svg class="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        </div>
        <p class="text-[var(--color-text)] text-sm font-medium mb-2">Failed to load graph</p>
        <p class="text-[var(--color-text-muted)] text-xs">{{ store.error }}</p>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-if="!store.loading && !store.error && !store.nodes.length"
      class="absolute inset-0 flex items-center justify-center z-10"
    >
      <div class="flex flex-col items-center text-center">
        <svg class="w-12 h-12 text-[var(--color-text-muted)] mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 3.75H6A2.25 2.25 0 0 0 3.75 6v1.5M16.5 3.75H18A2.25 2.25 0 0 1 20.25 6v1.5m0 9V18A2.25 2.25 0 0 1 18 20.25h-1.5m-9 0H6A2.25 2.25 0 0 1 3.75 18v-1.5M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
        </svg>
        <p class="text-sm text-[var(--color-text-muted)]">No graph data available</p>
      </div>
    </div>

    <!-- SVG canvas -->
    <svg ref="svgRef" class="w-full h-full" />

    <!-- Entity type legend (bottom-left) -->
    <div
      v-if="entityTypeStats.length && !store.loading"
      class="absolute bottom-6 left-4 z-10 bg-black/5 dark:bg-white/5 backdrop-blur-sm border border-black/10 dark:border-white/10 rounded-lg p-4 max-w-56"
    >
      <h3 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-3">Entity Types</h3>
      <div class="space-y-1.5">
        <button
          v-for="stat in entityTypeStats"
          :key="stat.type"
          @click="store.toggleTypeFilter(stat.type)"
          class="flex items-center gap-2 w-full text-left group"
        >
          <span
            class="w-2.5 h-2.5 rounded-full flex-shrink-0 transition-opacity"
            :style="{ backgroundColor: stat.color }"
            :class="{ 'opacity-30': !stat.active }"
          />
          <span
            class="text-xs flex-1 truncate transition-colors"
            :class="stat.active ? 'text-[var(--color-text-secondary)]' : 'text-[var(--color-text-muted)] line-through'"
          >{{ stat.type }}</span>
          <span class="text-xs text-[var(--color-text-muted)] tabular-nums">{{ stat.count }}</span>
        </button>
      </div>
      <button
        v-if="store.activeTypeFilters.length"
        @click="store.clearFilters"
        class="mt-3 pt-3 border-t border-black/10 dark:border-white/10 w-full text-[10px] text-[#2068FF] hover:text-[#2068FF]/80 text-left"
      >
        Clear filters
      </button>
    </div>

    <!-- Node detail panel (right side) -->
    <Transition name="slide">
      <div
        v-if="store.selectedNode"
        class="absolute top-0 right-0 z-20 h-full w-80 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border-l border-black/10 dark:border-white/10 overflow-y-auto"
      >
        <div class="p-5">
          <!-- Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-2.5">
              <span
                class="w-3.5 h-3.5 rounded-full"
                :style="{ backgroundColor: getNodeColor(store.selectedNode.labels) }"
              />
              <h3 class="text-[var(--color-text)] font-semibold text-sm">{{ store.selectedNode.name }}</h3>
            </div>
            <button
              @click="store.clearSelection"
              class="text-black/30 dark:text-white/30 hover:text-black/60 dark:hover:text-white/60 text-lg leading-none transition-colors"
            >&times;</button>
          </div>

          <!-- Type badge -->
          <span
            class="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-wider mb-4"
            :style="{
              backgroundColor: getNodeColor(store.selectedNode.labels) + '22',
              color: getNodeColor(store.selectedNode.labels),
            }"
          >
            {{ getEntityType(store.selectedNode.labels) }}
          </span>

          <!-- Summary -->
          <div v-if="store.selectedNode.summary" class="mb-5">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Summary</h4>
            <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">{{ store.selectedNode.summary }}</p>
          </div>

          <!-- Centrality -->
          <div class="mb-5">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Centrality</h4>
            <div class="flex items-center gap-2">
              <div class="flex-1 h-1.5 rounded-full bg-black/10 dark:bg-white/10">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :style="{
                    width: Math.round(centralityForSelected * 100) + '%',
                    backgroundColor: getNodeColor(store.selectedNode.labels),
                  }"
                />
              </div>
              <span class="text-xs text-[var(--color-text-muted)] tabular-nums">
                {{ Math.round(centralityForSelected * 100) }}%
              </span>
            </div>
          </div>

          <!-- Connections -->
          <div v-if="store.selectedNodeConnections.length">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-2">
              Connections ({{ store.selectedNodeConnections.length }})
            </h4>
            <div class="space-y-2">
              <div
                v-for="(conn, i) in store.selectedNodeConnections"
                :key="i"
                class="bg-black/5 dark:bg-white/5 rounded-lg p-3"
              >
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-[10px]" :class="conn.direction === 'outgoing' ? 'text-[#2068FF]' : 'text-[#ff5600]'">
                    {{ conn.direction === 'outgoing' ? '\u2192' : '\u2190' }}
                  </span>
                  <span class="text-xs text-[var(--color-text-muted)]">{{ conn.name }}</span>
                  <span class="text-xs text-[var(--color-text)] font-medium">{{ conn.targetName }}</span>
                </div>
                <p v-if="conn.fact" class="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{{ conn.fact }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
