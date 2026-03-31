<script setup>
import { ref, computed, inject, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { select } from 'd3-selection'
import { forceSimulation, forceCenter, forceManyBody, forceCollide, forceLink } from 'd3-force'
import { zoom as d3zoom, zoomIdentity } from 'd3-zoom'
import { drag as d3drag } from 'd3-drag'
import { easeBackOut } from 'd3-ease'
import 'd3-transition'
import GraphSearch from './GraphSearch.vue'
import Graph3DPanel from './Graph3DPanel.vue'
import { useMobileChart } from '../../composables/useMobileChart'
import { useD3PerfMonitor } from '@/composables/useD3PerfMonitor'
import { DEMO_NODES, DEMO_EDGES } from '../../data/demoGraphData'

const { isMobile } = useMobileChart()
const { measure, trackFrame, countDomNodes } = useD3PerfMonitor()

const props = defineProps({
  taskId: { type: String, required: true },
  demoMode: { type: Boolean, default: false },
})

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

// Injected polling data
const polling = inject('polling')
const { graphStatus, graphProgress, graphData, graphId, graphTask, isDemoFallback } = polling

// D3 refs
const svgRef = ref(null)
const containerRef = ref(null)
let simulation = null
let skeletonSim = null
let svg = null
let zoomGroup = null
let zoomBehavior = null
let resizeObserver = null
let resizeTimer = null
let themeObserver = null
let demoBuildTimer = null
let nodeSelection = null
let linkSelection = null
let edgeLabelSelection = null

// Local state
const selectedNode = ref(null)
const nodeCount = ref(0)
const edgeCount = ref(0)
const errorMsg = ref('')
const viewMode = ref('2d')
const darkMode = ref(isDarkMode())

// Entity type color mapping
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

const BUILD_MESSAGES = [
  'Parsing seed document...',
  'Extracting entities...',
  'Building persona nodes...',
  'Mapping topic clusters...',
  'Computing relationships...',
  'Finalizing graph...',
]

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

const entityTypeStats = computed(() => {
  const counts = {}
  for (const n of graphData.value.nodes) {
    const type = getEntityType(n.labels)
    counts[type] = (counts[type] || 0) + 1
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([type, count]) => ({
      type,
      count,
      color: getNodeColor([type]),
    }))
})

const buildMessage = computed(() => {
  const p = graphProgress.value
  const msgIdx = Math.min(
    Math.floor((p / 100) * BUILD_MESSAGES.length),
    BUILD_MESSAGES.length - 1,
  )
  return graphTask.value?.message || BUILD_MESSAGES[msgIdx] || 'Initializing...'
})

// --- Skeleton Graph (Phase 4A) ---

function renderSkeletonGraph() {
  const container = containerRef.value
  if (!container) return
  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  select(svgRef.value).selectAll('*').remove()

  svg = select(svgRef.value).attr('width', width).attr('height', height)
  zoomGroup = svg.append('g')

  const baseCount = 4
  const progressBonus = Math.floor((graphProgress.value / 100) * 8)
  const count = Math.min(baseCount + progressBonus, 12)

  const skeletonNodes = Array.from({ length: count }, (_, i) => ({
    id: `sk-${i}`,
    x: width / 2 + (Math.random() - 0.5) * width * 0.6,
    y: height / 2 + (Math.random() - 0.5) * height * 0.6,
    radius: 8 + Math.random() * 12,
  }))

  const skeletonEdges = []
  for (let i = 1; i < count; i++) {
    const source = Math.floor(Math.random() * i)
    skeletonEdges.push({ source: skeletonNodes[source], target: skeletonNodes[i] })
  }

  zoomGroup.selectAll('line').data(skeletonEdges).join('line')
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    .attr('stroke', 'rgba(32,104,255,0.1)').attr('stroke-width', 1)

  const nodeG = zoomGroup.selectAll('circle').data(skeletonNodes).join('circle')
    .attr('cx', d => d.x).attr('cy', d => d.y)
    .attr('r', d => d.radius)
    .attr('fill', 'rgba(32,104,255,0.15)')
    .attr('class', 'skeleton-pulse')

  skeletonSim = forceSimulation(skeletonNodes)
    .force('center', forceCenter(width / 2, height / 2).strength(0.02))
    .force('charge', forceManyBody().strength(-30))
    .force('collision', forceCollide(20))
    .alphaTarget(0.3)
    .on('tick', () => {
      nodeG.attr('cx', d => d.x).attr('cy', d => d.y)
      zoomGroup.selectAll('line')
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    })
}

// --- Real Graph Rendering ---

function renderGraph() {
  if (!svgRef.value || !graphData.value.nodes.length) return

  // Stop skeleton simulation before drawing real graph
  if (skeletonSim) {
    skeletonSim.stop()
    skeletonSim = null
  }

  const dark = isDarkMode()
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  if (!width || !height) return

  const centrality = computeCentrality(graphData.value.nodes, graphData.value.edges)

  const nodeMap = new Map()
  const nodes = graphData.value.nodes.map(n => {
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

  const links = graphData.value.edges
    .filter(e => nodeMap.has(e.source_node_uuid) && nodeMap.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
    }))

  nodeCount.value = nodes.length
  edgeCount.value = links.length

  measure('GraphPanel', () => {
    select(svgRef.value).selectAll('*').remove()

    svg = select(svgRef.value)
      .attr('width', width)
      .attr('height', height)

    zoomBehavior = d3zoom()
      .scaleExtent([0.2, 5])
      .on('zoom', (event) => {
        zoomGroup.attr('transform', event.transform)
      })
    svg.call(zoomBehavior)

    zoomGroup = svg.append('g')

    const defs = svg.append('defs')

    defs.append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -4 8 8')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-4L8,0L0,4')
      .attr('fill', dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')

    const glowFilter = defs.append('filter')
      .attr('id', 'drag-glow')
      .attr('x', '-50%').attr('y', '-50%')
      .attr('width', '200%').attr('height', '200%')
    glowFilter.append('feGaussianBlur')
      .attr('in', 'SourceGraphic')
      .attr('stdDeviation', '3')
      .attr('result', 'blur')
    const glowMerge = glowFilter.append('feMerge')
    glowMerge.append('feMergeNode').attr('in', 'blur')
    glowMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    const mobile = isMobile.value
    simulation = forceSimulation(nodes)
      .force('link', forceLink(links).id(d => d.id).distance(mobile ? 70 : 120))
      .force('charge', forceManyBody().strength(mobile ? -150 : -300))
      .force('center', forceCenter(width / 2, height / 2))
      .force('collision', forceCollide().radius(d => d.radius + (mobile ? 2 : 4)))

    const link = zoomGroup.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)')
      .attr('stroke-width', 1)
      .attr('marker-end', 'url(#arrow)')
      .style('opacity', 0)

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

    const node = zoomGroup.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'grab')
      .style('opacity', 0)
      .call(d3drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
      )
      .on('click', (event, d) => {
        event.stopPropagation()
        selectNode(d)
      })

    node.append('circle')
      .attr('r', d => d.radius + 4)
      .attr('fill', d => d.color)
      .attr('opacity', 0.2)

    node.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => d.color)
      .attr('stroke', d => d.color)
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.4)
      .attr('fill-opacity', 0.85)

    node.append('text')
      .text(d => d.name)
      .attr('dy', d => d.radius + 14)
      .attr('text-anchor', 'middle')
      .attr('fill', dark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)')
      .attr('font-size', '10px')
      .style('pointer-events', 'none')

    const nodeDelay = mobile ? 20 : 60
    const linkBaseDelay = nodes.length * nodeDelay

    node.transition()
      .delay((d, i) => i * nodeDelay)
      .duration(mobile ? 250 : 400)
      .style('opacity', 1)

    link.transition()
      .delay((d, i) => linkBaseDelay + i * (mobile ? 10 : 30))
      .duration(300)
      .style('opacity', 1)

    edgeLabel.transition()
      .delay((d, i) => linkBaseDelay + i * (mobile ? 10 : 30))
      .duration(300)
      .style('opacity', 1)

    nodeSelection = node
    linkSelection = link
    edgeLabelSelection = edgeLabel

    simulation.on('tick', () => {
      trackFrame('GraphPanel')

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

    svg.on('click', () => { selectedNode.value = null })
  })
  countDomNodes('GraphPanel', containerRef.value)
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y

  const el = select(this)
  el.raise()

  el.select('circle:nth-child(2)')
    .transition().duration(150)
    .attr('r', d.radius * 1.15)
    .attr('fill-opacity', 1)
    .style('filter', 'url(#drag-glow)')

  el.select('circle:first-child')
    .transition().duration(150)
    .attr('r', (d.radius + 4) * 1.15)
    .attr('opacity', 0.35)

  svg.style('cursor', 'grabbing')
  el.style('cursor', 'grabbing')

  if (nodeSelection) {
    nodeSelection.filter(n => n !== d)
      .transition().duration(200)
      .style('opacity', 0.3)
  }

  if (linkSelection) {
    linkSelection.transition().duration(200)
      .style('opacity', l => (l.source === d || l.target === d) ? 1 : 0.08)
      .attr('stroke-width', l => (l.source === d || l.target === d) ? 1.5 : 1)
  }

  if (edgeLabelSelection) {
    edgeLabelSelection.transition().duration(200)
      .style('opacity', l => (l.source === d || l.target === d) ? 1 : 0.05)
  }
}

function dragged(event, d) {
  d.fx = event.x
  d.fy = event.y
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null

  const el = select(this)

  el.select('circle:nth-child(2)')
    .transition().duration(300).ease(easeBackOut.overshoot(1.5))
    .attr('r', d.radius)
    .attr('fill-opacity', 0.85)
    .style('filter', null)

  el.select('circle:first-child')
    .transition().duration(300).ease(easeBackOut.overshoot(1.5))
    .attr('r', d.radius + 4)
    .attr('opacity', 0.2)

  svg.style('cursor', null)
  el.style('cursor', 'grab')

  if (nodeSelection) {
    nodeSelection.transition().duration(300)
      .style('opacity', 1)
  }

  if (linkSelection) {
    linkSelection.transition().duration(300)
      .style('opacity', 1)
      .attr('stroke-width', 1)
  }

  if (edgeLabelSelection) {
    edgeLabelSelection.transition().duration(300)
      .style('opacity', 1)
  }
}

// --- Node Selection ---

function selectNode(d) {
  const raw = graphData.value.nodes.find(n => n.uuid === d.id)
  const connections = graphData.value.edges.filter(
    e => e.source_node_uuid === d.id || e.target_node_uuid === d.id,
  )
  selectedNode.value = {
    ...d,
    summary: raw?.summary || d.summary,
    attributes: raw?.attributes || {},
    entityType: getEntityType(d.labels),
    connections: connections.map(e => ({
      name: e.name || e.fact_type || '',
      fact: e.fact || '',
      direction: e.source_node_uuid === d.id ? 'outgoing' : 'incoming',
      target: e.source_node_uuid === d.id
        ? graphData.value.nodes.find(n => n.uuid === e.target_node_uuid)?.name || ''
        : graphData.value.nodes.find(n => n.uuid === e.source_node_uuid)?.name || '',
    })),
  }
}

function handleSearchSelect(uuid) {
  if (!zoomGroup || !simulation) return
  const simNodes = simulation.nodes()
  const target = simNodes.find(n => n.id === uuid)
  if (!target) {
    const raw = graphData.value.nodes.find(n => n.uuid === uuid)
    if (raw) selectNode({ id: raw.uuid, name: raw.name, labels: raw.labels, summary: raw.summary || '', centrality: 0, color: getNodeColor(raw.labels), radius: 10 })
    return
  }
  selectNode(target)
  if (!containerRef.value || !svg || !zoomBehavior) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight
  const transform = zoomIdentity.translate(width / 2 - target.x, height / 2 - target.y)
  svg.transition().duration(500).call(zoomBehavior.transform, transform)
}

function handleNode3DSelect(node) {
  if (!node) {
    selectedNode.value = null
    return
  }
  selectNode(node)
}

// --- Demo Data ---

function loadDemoData() {
  if (demoBuildTimer) clearInterval(demoBuildTimer)

  const allNodes = DEMO_NODES
  const allEdges = DEMO_EDGES

  graphStatus.value = 'building'
  graphProgress.value = 0
  graphData.value = { nodes: [], edges: [] }
  nodeCount.value = 0
  edgeCount.value = 0

  let idx = 0
  const BATCH = 3
  const INTERVAL = 200

  demoBuildTimer = setInterval(() => {
    if (idx >= allNodes.length) {
      clearInterval(demoBuildTimer)
      demoBuildTimer = null
      graphStatus.value = 'complete'
      graphProgress.value = 100
      return
    }

    const end = Math.min(idx + BATCH, allNodes.length)
    const newNodes = allNodes.slice(idx, end)
    graphData.value.nodes.push(...newNodes)

    const nodeIds = new Set(graphData.value.nodes.map(n => n.uuid))
    graphData.value.edges = allEdges.filter(
      e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid),
    )

    idx = end
    graphProgress.value = Math.round((idx / allNodes.length) * 100)
    nodeCount.value = graphData.value.nodes.length
    edgeCount.value = graphData.value.edges.length

    const msgIdx = Math.min(
      Math.floor((idx / allNodes.length) * BUILD_MESSAGES.length),
      BUILD_MESSAGES.length - 1,
    )
    graphTask.value = { message: BUILD_MESSAGES[msgIdx] }

    nextTick(() => renderGraph())
  }, INTERVAL)
}

// --- Watchers ---

// When graphData changes and status is complete, render the real graph
watch(graphData, () => {
  if (graphStatus.value === 'complete' && graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }
}, { deep: true })

// When status transitions to complete, ensure graph is rendered
watch(graphStatus, (val) => {
  if (val === 'complete' && graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }
  if (val === 'failed') {
    errorMsg.value = graphTask.value?.message || 'Build failed'
  }
})

// When building, update skeleton at progress milestones
watch(graphProgress, (val) => {
  if (graphStatus.value === 'building' && !graphData.value.nodes.length) {
    if (val % 25 === 0 || val === 0) {
      renderSkeletonGraph()
    }
  }
})

// Demo mode triggers
watch(() => props.demoMode, (val) => {
  if (val) loadDemoData()
})

watch(isDemoFallback, (val) => {
  if (val) loadDemoData()
})

// --- Lifecycle ---

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (graphData.value.nodes.length && graphStatus.value === 'complete') {
        renderGraph()
      } else if (graphStatus.value === 'building' && !graphData.value.nodes.length) {
        renderSkeletonGraph()
      }
    }, 200)
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'class') {
        darkMode.value = isDarkMode()
        if (graphData.value.nodes.length) {
          renderGraph()
        }
        break
      }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

  if (graphStatus.value === 'building') {
    renderSkeletonGraph()
  }

  if (props.demoMode || isDemoFallback.value) {
    loadDemoData()
  }
})

onUnmounted(() => {
  if (demoBuildTimer) clearInterval(demoBuildTimer)
  if (simulation) simulation.stop()
  if (skeletonSim) skeletonSim.stop()
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
  clearTimeout(resizeTimer)
  nodeSelection = null
  linkSelection = null
  edgeLabelSelection = null
})
</script>

<template>
  <div ref="containerRef" class="w-full h-full relative overflow-hidden bg-[#f8f9fa] dark:bg-[#0a0a1a]">
    <!-- Status badge top-left -->
    <div class="absolute top-4 left-4 z-10 flex items-center gap-3">
      <span
        class="px-3 py-1 rounded-full text-xs font-medium"
        :class="{
          'bg-[var(--color-warning-light)] text-[var(--color-warning)]': graphStatus === 'building',
          'bg-[var(--color-success-light)] text-[var(--color-success)]': graphStatus === 'complete',
          'bg-[var(--color-error-light)] text-[var(--color-error)]': graphStatus === 'failed',
        }"
      >
        <template v-if="graphStatus === 'building'">Building Graph... {{ graphProgress }}%</template>
        <template v-else-if="graphStatus === 'complete'">Complete</template>
        <template v-else>Failed</template>
      </span>
    </div>

    <!-- Search (top-right, shown when graph is complete) -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'complete'"
        class="absolute top-4 right-4 z-10 w-64"
      >
        <GraphSearch
          :graph-id="graphId"
          :graph-data="graphData"
          @select-node="handleSearchSelect"
        />
      </div>
    </Transition>

    <!-- Build progress overlay center -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'building' && !demoMode && !isDemoFallback"
        class="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-black/60 dark:bg-black/70 backdrop-blur-sm rounded-xl px-3 py-2 sm:px-5 sm:py-3 flex items-center gap-2 sm:gap-4 max-w-[90vw]"
      >
        <svg viewBox="0 0 36 36" class="w-9 h-9 -rotate-90 flex-shrink-0">
          <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="3" />
          <circle
            cx="18" cy="18" r="14" fill="none" stroke="var(--color-primary)" stroke-width="3"
            stroke-linecap="round" :stroke-dasharray="88" :stroke-dashoffset="88 - (88 * graphProgress / 100)"
            class="transition-[stroke-dashoffset] duration-300"
          />
        </svg>
        <div>
          <p class="text-white text-sm font-medium">Building Graph... {{ graphProgress }}%</p>
          <p class="text-white/50 text-xs">{{ buildMessage }}</p>
        </div>
      </div>
    </Transition>

    <!-- Error state -->
    <div
      v-if="graphStatus === 'failed'"
      class="absolute inset-0 flex items-center justify-center z-20 bg-[var(--color-surface)]/80 backdrop-blur-sm"
    >
      <div class="flex flex-col items-center text-center max-w-md">
        <div class="w-14 h-14 rounded-full bg-[var(--color-error-light)] flex items-center justify-center mb-4">
          <svg class="w-7 h-7 text-[var(--color-error)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        </div>
        <p class="text-[var(--color-text)] text-sm font-medium mb-2">Graph build failed</p>
        <p class="text-[var(--color-text-muted)] text-xs mb-6">{{ errorMsg }}</p>
      </div>
    </div>

    <!-- 2D SVG canvas -->
    <svg v-show="viewMode === '2d'" ref="svgRef" class="w-full h-full graph-canvas" />

    <!-- 3D WebGL canvas -->
    <Graph3DPanel
      v-if="viewMode === '3d' && graphData.nodes.length"
      :nodes="graphData.nodes"
      :edges="graphData.edges"
      :isDark="darkMode"
      @select-node="handleNode3DSelect"
    />

    <!-- Entity type stats panel bottom-left (hidden on mobile to avoid overlap) -->
    <div
      v-if="entityTypeStats.length && graphStatus !== 'failed'"
      class="absolute bottom-6 left-4 z-10 bg-black/5 dark:bg-white/5 backdrop-blur-sm border border-black/10 dark:border-white/10 rounded-lg p-4 max-w-56 hidden sm:block"
    >
      <h3 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-3">Entity Types</h3>
      <div class="space-y-2">
        <div v-for="stat in entityTypeStats" :key="stat.type" class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: stat.color }" />
          <span class="text-xs text-[var(--color-text-secondary)] flex-1 truncate">{{ stat.type }}</span>
          <span class="text-xs text-[var(--color-text-muted)] tabular-nums">{{ stat.count }}</span>
        </div>
      </div>
      <div class="mt-3 pt-3 border-t border-black/10 dark:border-white/10 flex justify-between text-xs text-[var(--color-text-muted)]">
        <span data-testid="node-count">{{ nodeCount }} nodes</span>
        <span data-testid="edge-count">{{ edgeCount }} edges</span>
      </div>
    </div>

    <!-- Node detail panel right side -->
    <Transition name="panel-right">
      <div
        v-if="selectedNode"
        class="absolute top-0 right-0 z-20 h-full w-full sm:w-80 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border-l border-black/10 dark:border-white/10 overflow-y-auto"
        data-testid="detail-panel"
      >
        <div class="p-5">
          <!-- Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-2.5">
              <span class="w-3.5 h-3.5 rounded-full" :style="{ backgroundColor: selectedNode.color }" />
              <h3 class="text-[var(--color-text)] font-semibold text-sm">{{ selectedNode.name }}</h3>
            </div>
            <button
              @click="selectedNode = null"
              class="text-black/30 dark:text-white/30 hover:text-black/60 dark:hover:text-white/60 text-lg leading-none transition-colors"
            >&times;</button>
          </div>

          <!-- Type badge -->
          <span
            class="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-wider mb-4"
            :style="{ backgroundColor: selectedNode.color + '22', color: selectedNode.color }"
          >
            {{ selectedNode.entityType }}
          </span>

          <!-- Summary -->
          <div v-if="selectedNode.summary" class="mb-5">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Summary</h4>
            <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">{{ selectedNode.summary }}</p>
          </div>

          <!-- Centrality -->
          <div class="mb-5">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Centrality</h4>
            <div class="flex items-center gap-2">
              <div class="flex-1 h-1.5 rounded-full bg-black/10 dark:bg-white/10">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :style="{ width: (selectedNode.centrality * 100) + '%', backgroundColor: selectedNode.color }"
                />
              </div>
              <span class="text-xs text-[var(--color-text-muted)] tabular-nums">{{ Math.round(selectedNode.centrality * 100) }}%</span>
            </div>
          </div>

          <!-- Connections -->
          <div v-if="selectedNode.connections.length">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-2">
              Connections ({{ selectedNode.connections.length }})
            </h4>
            <div class="space-y-2">
              <div
                v-for="(conn, i) in selectedNode.connections"
                :key="i"
                class="bg-black/5 dark:bg-white/5 rounded-lg p-3"
              >
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-[10px]" :class="conn.direction === 'outgoing' ? 'text-[#2068FF]' : 'text-[#ff5600]'">
                    {{ conn.direction === 'outgoing' ? '\u2192' : '\u2190' }}
                  </span>
                  <span class="text-xs text-[var(--color-text-muted)]">{{ conn.name }}</span>
                  <span class="text-xs text-[var(--color-text)] font-medium">{{ conn.target }}</span>
                </div>
                <p v-if="conn.fact" class="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{{ conn.fact }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- View mode toggle + stats bottom-right -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'complete' || graphData.nodes.length"
        class="absolute bottom-6 right-6 z-10 flex items-center gap-3"
      >
        <span class="text-xs text-[var(--color-text-muted)]">{{ nodeCount }} nodes, {{ edgeCount }} edges</span>
        <div class="flex bg-black/10 dark:bg-white/10 rounded-lg p-0.5">
          <button
            @click="viewMode = '2d'"
            class="px-2.5 py-1 rounded-md text-xs font-medium transition-all"
            :class="viewMode === '2d'
              ? 'bg-white dark:bg-white/20 text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
          >2D</button>
          <button
            @click="viewMode = '3d'"
            class="px-2.5 py-1 rounded-md text-xs font-medium transition-all"
            :class="viewMode === '3d'
              ? 'bg-white dark:bg-white/20 text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
          >3D</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.skeleton-pulse {
  animation: skeleton-pulse 2s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.15; }
  50% { opacity: 0.35; }
}

.graph-canvas {
  transition: opacity 0.4s ease;
  touch-action: none;
}

</style>
