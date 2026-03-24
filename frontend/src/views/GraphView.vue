<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as d3 from 'd3'
import { graphApi } from '../api/graph'
import { useToast } from '../composables/useToast'
import PhaseNav from '../components/simulation/PhaseNav.vue'

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

const props = defineProps({ taskId: String })
const route = useRoute()
const toast = useToast()
const projectId = ref(route.query.projectId || '')
const graphId = ref('')

// Task polling state
const task = ref(null)
const status = ref('building')
const progress = ref(0)
const errorMsg = ref('')

// Graph data
const graphData = ref({ nodes: [], edges: [] })
const nodeCount = ref(0)
const edgeCount = ref(0)
const selectedNode = ref(null)
const loaded = ref(false)

// D3 visualization
const svgRef = ref(null)
const containerRef = ref(null)
let simulation = null
let svg = null
let zoomGroup = null
let pollTimer = null
let resizeObserver = null
let resizeTimer = null
let themeObserver = null

// Entity type color mapping
const TYPE_COLORS = {
  persona: '#ff5600',
  person: '#ff5600',
  agent: '#ff5600',
  user: '#ff5600',
  customer: '#ff5600',
  stakeholder: '#ff5600',
  role: '#ff5600',
  topic: '#2068FF',
  theme: '#2068FF',
  subject: '#2068FF',
  concept: '#2068FF',
  category: '#2068FF',
  product: '#2068FF',
  feature: '#2068FF',
  technology: '#2068FF',
  relationship: '#AA00FF',
  interaction: '#AA00FF',
  connection: '#AA00FF',
  event: '#AA00FF',
  action: '#AA00FF',
  process: '#AA00FF',
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
  // Deterministic color from a fixed palette for unknown types
  const palette = ['#ff5600', '#2068FF', '#AA00FF']
  let hash = 0
  for (const ch of label) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0
  return palette[Math.abs(hash) % palette.length]
}

function getEntityType(labels) {
  const meaningful = (labels || []).filter(l => !GENERIC_LABELS.has(l))
  return meaningful[0] || 'Entity'
}

// Centrality: count edges connected to each node
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

// Entity type stats for the stats panel
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

// --- Task Polling ---

async function pollTask() {
  if (!props.taskId) return

  try {
    const res = await graphApi.getTask(props.taskId)
    const json = res.data
    if (!json.success) {
      errorMsg.value = json.error || 'Unknown error'
      return
    }

    task.value = json.data
    progress.value = json.data.progress || 0

    if (json.data.status === 'completed') {
      status.value = 'complete'
      clearInterval(pollTimer)
      pollTimer = null
      const gid = json.data.result?.graph_id
      if (gid) {
        graphId.value = gid
        await loadGraphData(gid)
      }
      toast.success('Knowledge graph built successfully')
    } else if (json.data.status === 'failed') {
      status.value = 'failed'
      errorMsg.value = json.data.message || 'Build failed'
      clearInterval(pollTimer)
      pollTimer = null
      toast.error('Knowledge graph build failed')
    } else {
      status.value = 'building'
    }
  } catch {
    // Task not found or backend unreachable — try as graph_id or use demo data
    try {
      await loadGraphDirect(props.taskId)
    } catch {
      loadDemoData()
      toast.info('Using sample data — backend unavailable')
    }
  }
}

async function loadGraphDirect(gid) {
  clearInterval(pollTimer)
  pollTimer = null
  const res = await graphApi.getData(gid)
  if (res.data?.success) {
    graphId.value = gid
    applyGraphData(res.data.data)
    status.value = 'complete'
    toast.success('Knowledge graph loaded')
  } else {
    loadDemoData()
  }
}

async function loadGraphData(gid) {
  try {
    const res = await graphApi.getData(gid)
    if (res.data?.success) applyGraphData(res.data.data)
  } catch (e) {
    console.error('Failed to load graph data:', e)
  }
}

function applyGraphData(data) {
  graphData.value = data
  nodeCount.value = data.node_count || data.nodes.length
  edgeCount.value = data.edge_count || data.edges.length
  nextTick(() => renderGraph())
}

function retryBuild() {
  status.value = 'building'
  progress.value = 0
  errorMsg.value = ''
  selectedNode.value = null
  graphData.value = { nodes: [], edges: [] }
  if (simulation) simulation.stop()
  pollTask()
  pollTimer = setInterval(pollTask, 2000)
}

function loadDemoData() {
  clearInterval(pollTimer)
  pollTimer = null
  status.value = 'complete'

  const demoNodes = [
    { uuid: '1', name: 'Enterprise Buyer', labels: ['Entity', 'Persona'], summary: 'Decision-maker at large organizations evaluating platform purchases.' },
    { uuid: '2', name: 'SMB Founder', labels: ['Entity', 'Persona'], summary: 'Small business owner seeking affordable customer support tools.' },
    { uuid: '3', name: 'Customer Support', labels: ['Entity', 'Topic'], summary: 'Core product area for ticket management and live chat.' },
    { uuid: '4', name: 'AI Automation', labels: ['Entity', 'Topic'], summary: 'Machine learning-powered features like Fin AI agent.' },
    { uuid: '5', name: 'Pricing Strategy', labels: ['Entity', 'Topic'], summary: 'Seat-based vs usage-based pricing models.' },
    { uuid: '6', name: 'Competitor Analysis', labels: ['Entity', 'Topic'], summary: 'Comparative positioning against Zendesk, Freshdesk, HubSpot.' },
    { uuid: '7', name: 'Product-Led Growth', labels: ['Entity', 'Process'], summary: 'GTM motion focusing on self-serve onboarding and expansion.' },
    { uuid: '8', name: 'Sales-Led Motion', labels: ['Entity', 'Process'], summary: 'Enterprise sales cycle with demos, pilots, and procurement.' },
    { uuid: '9', name: 'Developer Advocate', labels: ['Entity', 'Persona'], summary: 'Technical influencer evaluating APIs and integrations.' },
    { uuid: '10', name: 'Onboarding Flow', labels: ['Entity', 'Feature'], summary: 'First-run experience guiding users through product setup.' },
    { uuid: '11', name: 'Churn Risk', labels: ['Entity', 'Event'], summary: 'Signals indicating potential customer attrition.' },
    { uuid: '12', name: 'Expansion Revenue', labels: ['Entity', 'Topic'], summary: 'Upsell and cross-sell motions within existing accounts.' },
  ]
  const demoEdges = [
    { uuid: 'e1', source_node_uuid: '1', target_node_uuid: '3', name: 'evaluates', fact: 'Enterprise buyers evaluate customer support platforms.' },
    { uuid: 'e2', source_node_uuid: '1', target_node_uuid: '8', name: 'engages_via', fact: 'Enterprise buyers engage through sales-led motions.' },
    { uuid: 'e3', source_node_uuid: '2', target_node_uuid: '7', name: 'converts_through', fact: 'SMB founders convert through product-led growth.' },
    { uuid: 'e4', source_node_uuid: '2', target_node_uuid: '5', name: 'influenced_by', fact: 'SMB founders are price-sensitive.' },
    { uuid: 'e5', source_node_uuid: '3', target_node_uuid: '4', name: 'enhanced_by', fact: 'Support is enhanced by AI automation.' },
    { uuid: 'e6', source_node_uuid: '4', target_node_uuid: '6', name: 'differentiates_in', fact: 'AI capabilities are a competitive differentiator.' },
    { uuid: 'e7', source_node_uuid: '9', target_node_uuid: '10', name: 'tests', fact: 'Developer advocates evaluate the onboarding flow.' },
    { uuid: 'e8', source_node_uuid: '9', target_node_uuid: '4', name: 'integrates', fact: 'Developers integrate AI features via APIs.' },
    { uuid: 'e9', source_node_uuid: '7', target_node_uuid: '10', name: 'depends_on', fact: 'PLG relies on smooth onboarding.' },
    { uuid: 'e10', source_node_uuid: '11', target_node_uuid: '3', name: 'triggered_by', fact: 'Churn risk signals relate to support quality.' },
    { uuid: 'e11', source_node_uuid: '12', target_node_uuid: '1', name: 'targets', fact: 'Expansion revenue targets enterprise accounts.' },
    { uuid: 'e12', source_node_uuid: '5', target_node_uuid: '12', name: 'enables', fact: 'Pricing strategy enables expansion revenue.' },
    { uuid: 'e13', source_node_uuid: '8', target_node_uuid: '1', name: 'serves', fact: 'Sales-led motion serves enterprise buyers.' },
    { uuid: 'e14', source_node_uuid: '6', target_node_uuid: '5', name: 'informs', fact: 'Competitor analysis informs pricing strategy.' },
    { uuid: 'e15', source_node_uuid: '11', target_node_uuid: '2', name: 'affects', fact: 'Churn risk is higher for SMB segment.' },
  ]

  applyGraphData({
    nodes: demoNodes,
    edges: demoEdges,
    node_count: demoNodes.length,
    edge_count: demoEdges.length,
  })
}

// --- D3 Rendering ---

function renderGraph() {
  if (!svgRef.value || !graphData.value.nodes.length) return

  const dark = isDarkMode()
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  // Compute centrality for node sizing
  const centrality = computeCentrality(graphData.value.nodes, graphData.value.edges)

  // Build D3 data structures
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

  // Clear previous
  d3.select(svgRef.value).selectAll('*').remove()

  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  // Zoom
  const zoom = d3.zoom()
    .scaleExtent([0.2, 5])
    .on('zoom', (event) => {
      zoomGroup.attr('transform', event.transform)
    })
  svg.call(zoom)

  zoomGroup = svg.append('g')

  // Arrow marker
  svg.append('defs').append('marker')
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

  // Force simulation
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 4))

  // Links
  const link = zoomGroup.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)')
    .attr('stroke-width', 1)
    .attr('marker-end', 'url(#arrow)')
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
    .style('cursor', 'pointer')
    .style('opacity', 0)
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended)
    )
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d)
    })

  // Node glow
  node.append('circle')
    .attr('r', d => d.radius + 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.2)

  // Node circle
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

  // Build animation: stagger node/edge appearance
  node.transition()
    .delay((d, i) => i * 60)
    .duration(400)
    .style('opacity', 1)

  link.transition()
    .delay((d, i) => nodes.length * 60 + i * 30)
    .duration(300)
    .style('opacity', 1)

  edgeLabel.transition()
    .delay((d, i) => nodes.length * 60 + i * 30)
    .duration(300)
    .style('opacity', 1)

  // Tick
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
  svg.on('click', () => { selectedNode.value = null })
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

function selectNode(d) {
  const raw = graphData.value.nodes.find(n => n.uuid === d.id)
  const connections = graphData.value.edges.filter(
    e => e.source_node_uuid === d.id || e.target_node_uuid === d.id
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

// Lifecycle

onMounted(() => {
  loaded.value = true
  pollTask()
  pollTimer = setInterval(pollTask, 2000)

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (graphData.value.nodes.length) renderGraph()
    }, 200)
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'class' && graphData.value.nodes.length) {
        renderGraph()
        break
      }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
  clearTimeout(resizeTimer)
})

watch(() => props.taskId, () => {
  status.value = 'building'
  progress.value = 0
  errorMsg.value = ''
  selectedNode.value = null
  graphData.value = { nodes: [], edges: [] }
  if (simulation) simulation.stop()
  if (pollTimer) clearInterval(pollTimer)
  pollTask()
  pollTimer = setInterval(pollTask, 2000)
})
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-120px)] bg-[#f8f9fa] dark:bg-[#0a0a1a]">
    <div class="px-4 md:px-6 pt-4 dark">
      <PhaseNav :taskId="taskId" activePhase="graph" />
    </div>
    <div ref="containerRef" class="flex-1 relative overflow-hidden">
    <!-- Status Bar -->
    <div
      class="absolute top-4 left-4 z-10 flex items-center gap-3"
      :class="loaded ? 'animate-fade-in' : 'opacity-0'"
    >
      <span class="px-3 py-1 rounded-full text-xs font-medium"
        :class="{
          'bg-yellow-500/20 text-yellow-400': status === 'building',
          'bg-green-500/20 text-green-400': status === 'complete',
          'bg-red-500/20 text-red-400': status === 'failed',
        }">
        <template v-if="status === 'building'">Building Graph... {{ progress }}%</template>
        <template v-else-if="status === 'complete'">Complete</template>
        <template v-else>Failed</template>
      </span>
    </div>

    <!-- Build Progress Overlay -->
    <div v-if="status === 'building'" class="absolute inset-0 flex items-center justify-center z-20">
      <div class="text-center">
        <div class="relative w-24 h-24 mx-auto mb-6">
          <svg viewBox="0 0 100 100" class="w-full h-full -rotate-90">
            <circle cx="50" cy="50" r="42" fill="none" class="stroke-black/6 dark:stroke-white/6" stroke-width="4" />
            <circle cx="50" cy="50" r="42" fill="none" stroke="#2068FF" stroke-width="4"
              stroke-linecap="round"
              :stroke-dasharray="264"
              :stroke-dashoffset="264 - (264 * progress / 100)" />
          </svg>
          <span class="absolute inset-0 flex items-center justify-center text-[var(--color-text)] text-lg font-semibold">
            {{ progress }}%
          </span>
        </div>
        <p class="text-[var(--color-text-secondary)] text-sm">{{ task?.message || 'Initializing...' }}</p>
        <p class="text-[var(--color-text-muted)] text-xs mt-2">Task: {{ taskId }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="status === 'failed'" class="absolute inset-0 flex items-center justify-center z-20 bg-[var(--color-surface)]/80 backdrop-blur-sm">
      <div class="flex flex-col items-center text-center max-w-md">
        <div class="w-14 h-14 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
          <svg class="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        </div>
        <p class="text-[var(--color-text)] text-sm font-medium mb-2">Graph build failed</p>
        <p class="text-[var(--color-text-muted)] text-xs mb-6">{{ errorMsg }}</p>
        <button
          @click="retryBuild"
          class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.992 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
          </svg>
          Try Again
        </button>
      </div>
    </div>

    <!-- D3 SVG Canvas -->
    <svg ref="svgRef" class="w-full h-full" />

    <!-- Stats Panel (bottom-left) -->
    <div v-if="status === 'complete' && entityTypeStats.length"
      class="absolute bottom-6 left-4 z-10 bg-black/5 dark:bg-white/5 backdrop-blur-sm border border-black/10 dark:border-white/10 rounded-lg p-4 max-w-56">
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

    <!-- Node Detail Panel (right side) -->
    <transition name="slide">
      <div v-if="selectedNode"
        class="absolute top-0 right-0 z-20 h-full w-80 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border-l border-black/10 dark:border-white/10 overflow-y-auto"
        data-testid="detail-panel">
        <div class="p-5">
          <!-- Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-2.5">
              <span class="w-3.5 h-3.5 rounded-full" :style="{ backgroundColor: selectedNode.color }" />
              <h3 class="text-[var(--color-text)] font-semibold text-sm">{{ selectedNode.name }}</h3>
            </div>
            <button @click="selectedNode = null"
              class="text-black/30 dark:text-white/30 hover:text-black/60 dark:hover:text-white/60 text-lg leading-none transition-colors">&times;</button>
          </div>

          <!-- Type badge -->
          <span class="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-wider mb-4"
            :style="{ backgroundColor: selectedNode.color + '22', color: selectedNode.color }">
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
                <div class="h-full rounded-full transition-all duration-300"
                  :style="{ width: (selectedNode.centrality * 100) + '%', backgroundColor: selectedNode.color }" />
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
              <div v-for="(conn, i) in selectedNode.connections" :key="i"
                class="bg-black/5 dark:bg-white/5 rounded-lg p-3">
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-[10px]" :class="conn.direction === 'outgoing' ? 'text-[#2068FF]' : 'text-[#ff5600]'">
                    {{ conn.direction === 'outgoing' ? '→' : '←' }}
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
    </transition>

    <!-- Continue to Simulation -->
    <Transition name="page">
      <div v-if="status === 'complete'" class="absolute bottom-6 left-4 right-4 md:left-auto md:right-6 z-10 text-center md:text-right">
        <router-link
          :to="{ path: `/simulation/${taskId}`, query: { projectId, graphId } }"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-6 py-3 rounded-lg font-semibold text-sm transition-colors no-underline inline-flex items-center gap-2"
        >
          Continue to Simulation
          <span class="text-white/60">&rarr;</span>
        </router-link>
      </div>
    </Transition>
    </div>
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
</style>
