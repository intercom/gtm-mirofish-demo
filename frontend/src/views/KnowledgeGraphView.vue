<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import * as d3 from 'd3'
import { graphApi } from '../api/graph'
import { useToast } from '../composables/useToast'

const route = useRoute()
const toast = useToast()

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

// --- State ---
const containerRef = ref(null)
const svgRef = ref(null)
const searchQuery = ref('')
const loading = ref(true)
const error = ref(null)
const graphData = ref({ nodes: [], edges: [] })
const selectedNode = ref(null)
const activeFilters = ref(new Set())
const nodeCount = ref(0)
const edgeCount = ref(0)

// D3 internals
let simulation = null
let svg = null
let zoomGroup = null
let zoomBehavior = null
let resizeObserver = null
let resizeTimer = null
let themeObserver = null

// --- Entity type color mapping (matches GraphPanel) ---
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

// --- Computed ---
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

const allEntityTypes = computed(() => entityTypeStats.value.map(s => s.type))

const filteredData = computed(() => {
  const nodes = graphData.value.nodes
  const edges = graphData.value.edges
  if (!activeFilters.value.size && !searchQuery.value) return { nodes, edges }

  const filtered = nodes.filter(n => {
    const type = getEntityType(n.labels)
    if (activeFilters.value.size && !activeFilters.value.has(type)) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      return n.name.toLowerCase().includes(q) ||
        (n.summary || '').toLowerCase().includes(q)
    }
    return true
  })

  const ids = new Set(filtered.map(n => n.uuid))
  const filteredEdges = edges.filter(
    e => ids.has(e.source_node_uuid) && ids.has(e.target_node_uuid),
  )
  return { nodes: filtered, edges: filteredEdges }
})

// --- Data Loading ---
async function loadGraphData() {
  loading.value = true
  error.value = null

  const graphId = route.query.graphId

  if (graphId) {
    try {
      const { data } = await graphApi.getData(graphId)
      if (data.success && data.data) {
        graphData.value = data.data
        loading.value = false
        return
      }
    } catch {
      // fall through to demo
    }
  }

  // Try listing projects to find a graph
  try {
    const { data } = await graphApi.listProjects()
    if (data.success && data.data?.length) {
      const project = data.data.find(p => p.graph_id) || data.data[0]
      if (project?.graph_id) {
        const res = await graphApi.getData(project.graph_id)
        if (res.data.success && res.data.data) {
          graphData.value = res.data.data
          loading.value = false
          return
        }
      }
    }
  } catch {
    // fall through to demo
  }

  loadDemoData()
  loading.value = false
}

function loadDemoData() {
  graphData.value = {
    nodes: [
      { uuid: 'p1', name: 'Enterprise Buyer', labels: ['Entity', 'Persona'], summary: 'Decision-maker at large organizations evaluating platform purchases.' },
      { uuid: 'p2', name: 'SMB Founder', labels: ['Entity', 'Persona'], summary: 'Small business owner seeking affordable customer support tools.' },
      { uuid: 'p3', name: 'Developer Advocate', labels: ['Entity', 'Persona'], summary: 'Technical influencer evaluating APIs and integrations.' },
      { uuid: 'p4', name: 'VP of Support', labels: ['Entity', 'Persona'], summary: 'Senior leader responsible for support team performance and tooling.' },
      { uuid: 'p5', name: 'CX Director', labels: ['Entity', 'Persona'], summary: 'Owns end-to-end customer experience strategy and metrics.' },
      { uuid: 'p6', name: 'IT Leader', labels: ['Entity', 'Persona'], summary: 'Oversees technology stack, security, and vendor compliance.' },
      { uuid: 'p7', name: 'Head of Operations', labels: ['Entity', 'Persona'], summary: 'Drives operational efficiency across business processes.' },
      { uuid: 'p8', name: 'CFO', labels: ['Entity', 'Persona'], summary: 'Financial decision-maker focused on ROI and cost management.' },
      { uuid: 'p9', name: 'Product Manager', labels: ['Entity', 'Persona'], summary: 'Defines product roadmap based on customer and market insights.' },
      { uuid: 'p10', name: 'Sales Engineer', labels: ['Entity', 'Persona'], summary: 'Technical pre-sales resource supporting enterprise deal cycles.' },
      { uuid: 'p11', name: 'Marketing Director', labels: ['Entity', 'Persona'], summary: 'Leads demand generation, positioning, and campaign strategy.' },
      { uuid: 'p12', name: 'Customer Success Manager', labels: ['Entity', 'Persona'], summary: 'Manages post-sale relationships and drives adoption and retention.' },
      { uuid: 't1', name: 'Customer Support', labels: ['Entity', 'Topic'], summary: 'Core product area for ticket management and live chat.' },
      { uuid: 't2', name: 'AI Automation', labels: ['Entity', 'Topic'], summary: 'Machine learning-powered features like Fin AI agent.' },
      { uuid: 't3', name: 'Pricing Strategy', labels: ['Entity', 'Topic'], summary: 'Seat-based vs usage-based pricing models and packaging.' },
      { uuid: 't4', name: 'Competitor Analysis', labels: ['Entity', 'Topic'], summary: 'Comparative positioning against Zendesk, Freshdesk, HubSpot.' },
      { uuid: 't5', name: 'Fin AI Agent', labels: ['Entity', 'Topic'], summary: 'AI-powered resolution engine handling frontline support queries.' },
      { uuid: 't6', name: 'Resolution Rate', labels: ['Entity', 'Topic'], summary: 'Percentage of support queries resolved without human escalation.' },
      { uuid: 't7', name: 'CSAT Score', labels: ['Entity', 'Topic'], summary: 'Customer satisfaction metric collected post-interaction.' },
      { uuid: 't8', name: 'Knowledge Base', labels: ['Entity', 'Topic'], summary: 'Self-service article library powering AI and human agents.' },
      { uuid: 't9', name: 'Self-Serve Onboarding', labels: ['Entity', 'Topic'], summary: 'Guided setup flows enabling customers to activate without sales.' },
      { uuid: 't10', name: 'API Integration', labels: ['Entity', 'Topic'], summary: 'REST and webhook APIs for connecting external systems.' },
      { uuid: 'e1', name: 'Product-Led Growth', labels: ['Entity', 'Process'], summary: 'GTM motion focusing on self-serve onboarding and expansion.' },
      { uuid: 'e2', name: 'Sales-Led Motion', labels: ['Entity', 'Process'], summary: 'Enterprise sales cycle with demos, pilots, and procurement.' },
      { uuid: 'e3', name: 'Outbound Campaign', labels: ['Entity', 'Process'], summary: 'Targeted outreach sequences for prospecting and re-engagement.' },
      { uuid: 'e4', name: 'Churn Risk', labels: ['Entity', 'Event'], summary: 'Signals indicating potential customer attrition.' },
      { uuid: 'e5', name: 'Contract Renewal', labels: ['Entity', 'Event'], summary: 'Annual or multi-year renewal negotiation and close.' },
      { uuid: 'f1', name: 'Messenger Widget', labels: ['Entity', 'Feature'], summary: 'Embeddable chat widget for web and mobile apps.' },
      { uuid: 'f2', name: 'Help Center', labels: ['Entity', 'Feature'], summary: 'Public-facing knowledge base and article search.' },
      { uuid: 'f3', name: 'Team Inbox', labels: ['Entity', 'Feature'], summary: 'Shared workspace for collaborative conversation handling.' },
      { uuid: 'f4', name: 'Workflow Automation', labels: ['Entity', 'Feature'], summary: 'Rules and triggers that automate repetitive support tasks.' },
    ],
    edges: [
      { uuid: 'ed1', source_node_uuid: 'p1', target_node_uuid: 't1', name: 'evaluates', fact: 'Enterprise buyers evaluate customer support platforms for scale.' },
      { uuid: 'ed2', source_node_uuid: 'p1', target_node_uuid: 'e2', name: 'engages_via', fact: 'Enterprise buyers engage through sales-led motions with demos.' },
      { uuid: 'ed3', source_node_uuid: 'p2', target_node_uuid: 'e1', name: 'converts_through', fact: 'SMB founders convert through product-led self-serve flows.' },
      { uuid: 'ed4', source_node_uuid: 'p2', target_node_uuid: 't3', name: 'influenced_by', fact: 'SMB founders are highly price-sensitive in vendor selection.' },
      { uuid: 'ed5', source_node_uuid: 'p2', target_node_uuid: 't9', name: 'depends_on', fact: 'SMB founders rely on self-serve onboarding to get started.' },
      { uuid: 'ed6', source_node_uuid: 'p3', target_node_uuid: 't10', name: 'integrates', fact: 'Developer advocates evaluate and build on API integrations.' },
      { uuid: 'ed7', source_node_uuid: 'p3', target_node_uuid: 'f1', name: 'integrates', fact: 'Developer advocates embed the Messenger widget in apps.' },
      { uuid: 'ed8', source_node_uuid: 'p4', target_node_uuid: 't1', name: 'owns', fact: 'VP of Support owns the customer support function.' },
      { uuid: 'ed9', source_node_uuid: 'p4', target_node_uuid: 't6', name: 'monitors', fact: 'VP of Support tracks resolution rate as a key metric.' },
      { uuid: 'ed10', source_node_uuid: 'p4', target_node_uuid: 'f3', name: 'depends_on', fact: 'VP of Support depends on Team Inbox for agent management.' },
      { uuid: 'ed11', source_node_uuid: 'p5', target_node_uuid: 't7', name: 'monitors', fact: 'CX Director tracks CSAT scores across all touchpoints.' },
      { uuid: 'ed12', source_node_uuid: 'p6', target_node_uuid: 't10', name: 'evaluates', fact: 'IT Leader evaluates API integration security and compliance.' },
      { uuid: 'ed13', source_node_uuid: 'p7', target_node_uuid: 'f4', name: 'drives', fact: 'Head of Operations drives workflow automation adoption.' },
      { uuid: 'ed14', source_node_uuid: 'p8', target_node_uuid: 'e5', name: 'approves', fact: 'CFO approves contract renewals after reviewing financials.' },
      { uuid: 'ed15', source_node_uuid: 'p9', target_node_uuid: 't5', name: 'drives', fact: 'Product Manager drives Fin AI Agent roadmap and priorities.' },
      { uuid: 'ed16', source_node_uuid: 'p9', target_node_uuid: 't2', name: 'drives', fact: 'Product Manager shapes AI automation strategy.' },
      { uuid: 'ed17', source_node_uuid: 'p10', target_node_uuid: 'e2', name: 'supports', fact: 'Sales Engineer provides technical demos in sales-led motion.' },
      { uuid: 'ed18', source_node_uuid: 'p11', target_node_uuid: 'e3', name: 'drives', fact: 'Marketing Director drives outbound campaign strategy.' },
      { uuid: 'ed19', source_node_uuid: 'p11', target_node_uuid: 't4', name: 'informs', fact: 'Marketing Director uses competitor analysis for positioning.' },
      { uuid: 'ed20', source_node_uuid: 'p12', target_node_uuid: 'e5', name: 'drives', fact: 'CSM drives contract renewal through proactive engagement.' },
      { uuid: 'ed21', source_node_uuid: 'p12', target_node_uuid: 'e4', name: 'monitors', fact: 'CSM monitors churn risk signals across the book of business.' },
      { uuid: 'ed22', source_node_uuid: 't1', target_node_uuid: 't2', name: 'enhanced_by', fact: 'Customer support is enhanced by AI automation capabilities.' },
      { uuid: 'ed23', source_node_uuid: 't2', target_node_uuid: 't5', name: 'enables', fact: 'AI automation powers the Fin AI Agent product.' },
      { uuid: 'ed24', source_node_uuid: 't5', target_node_uuid: 't6', name: 'produces', fact: 'Fin AI Agent directly produces resolution rate improvements.' },
      { uuid: 'ed25', source_node_uuid: 't8', target_node_uuid: 't5', name: 'supports', fact: 'Knowledge base articles power Fin AI Agent responses.' },
      { uuid: 'ed26', source_node_uuid: 't8', target_node_uuid: 'f2', name: 'enables', fact: 'Knowledge base content enables the Help Center experience.' },
      { uuid: 'ed27', source_node_uuid: 'e1', target_node_uuid: 't9', name: 'depends_on', fact: 'Product-led growth relies on self-serve onboarding.' },
      { uuid: 'ed28', source_node_uuid: 'e4', target_node_uuid: 'e5', name: 'blocks', fact: 'Churn risk threatens contract renewal success.' },
      { uuid: 'ed29', source_node_uuid: 't4', target_node_uuid: 't3', name: 'informs', fact: 'Competitor analysis informs pricing strategy decisions.' },
      { uuid: 'ed30', source_node_uuid: 'f2', target_node_uuid: 't6', name: 'drives', fact: 'Help Center deflects tickets, improving resolution rate.' },
    ],
  }
}

// --- Graph Rendering ---
function renderGraph() {
  const data = filteredData.value
  if (!svgRef.value || !data.nodes.length) return

  const dark = isDarkMode()
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  const centrality = computeCentrality(data.nodes, data.edges)

  const nodeMap = new Map()
  const nodes = data.nodes.map(n => {
    const obj = {
      id: n.uuid,
      name: n.name,
      labels: n.labels,
      summary: n.summary || '',
      centrality: centrality[n.uuid] || 0,
      color: getNodeColor(n.labels),
      radius: 6 + (centrality[n.uuid] || 0) * 18,
    }
    nodeMap.set(n.uuid, obj)
    return obj
  })

  const links = data.edges
    .filter(e => nodeMap.has(e.source_node_uuid) && nodeMap.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
    }))

  nodeCount.value = nodes.length
  edgeCount.value = links.length

  // Stop previous simulation
  if (simulation) simulation.stop()
  d3.select(svgRef.value).selectAll('*').remove()

  svg = d3.select(svgRef.value).attr('width', width).attr('height', height)

  zoomBehavior = d3.zoom()
    .scaleExtent([0.1, 8])
    .on('zoom', (event) => { zoomGroup.attr('transform', event.transform) })
  svg.call(zoomBehavior)

  zoomGroup = svg.append('g')

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

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 4))

  const link = zoomGroup.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)')
    .attr('stroke-width', 1)
    .attr('marker-end', 'url(#kg-arrow)')

  const edgeLabel = zoomGroup.append('g')
    .selectAll('text')
    .data(links)
    .join('text')
    .text(d => d.name)
    .attr('fill', dark ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.3)')
    .attr('font-size', '8px')
    .attr('text-anchor', 'middle')
    .style('pointer-events', 'none')

  const node = zoomGroup.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .style('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x; d.fy = d.y
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null; d.fy = null
      })
    )
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d)
    })

  // Glow circle
  node.append('circle')
    .attr('r', d => d.radius + 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.2)

  // Main circle
  node.append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => d.color)
    .attr('fill-opacity', 0.85)
    .attr('stroke', d => d.color)
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.4)

  // Label
  node.append('text')
    .text(d => d.name)
    .attr('dy', d => d.radius + 14)
    .attr('text-anchor', 'middle')
    .attr('fill', dark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)')
    .attr('font-size', '10px')
    .style('pointer-events', 'none')

  // Animate in
  node.style('opacity', 0).transition().delay((d, i) => i * 40).duration(300).style('opacity', 1)
  link.style('opacity', 0).transition().delay((d, i) => nodes.length * 40 + i * 20).duration(200).style('opacity', 1)
  edgeLabel.style('opacity', 0).transition().delay((d, i) => nodes.length * 40 + i * 20).duration(200).style('opacity', 1)

  simulation.on('tick', () => {
    link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    edgeLabel.attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2)
    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  svg.on('click', () => { selectedNode.value = null })
}

// --- Node Selection ---
function selectNode(d) {
  const raw = filteredData.value.nodes.find(n => n.uuid === d.id)
  const connections = filteredData.value.edges.filter(
    e => e.source_node_uuid === d.id || e.target_node_uuid === d.id,
  )
  selectedNode.value = {
    ...d,
    summary: raw?.summary || d.summary,
    entityType: getEntityType(d.labels),
    connections: connections.map(e => ({
      name: e.name || '',
      fact: e.fact || '',
      direction: e.source_node_uuid === d.id ? 'outgoing' : 'incoming',
      target: e.source_node_uuid === d.id
        ? filteredData.value.nodes.find(n => n.uuid === e.target_node_uuid)?.name || ''
        : filteredData.value.nodes.find(n => n.uuid === e.source_node_uuid)?.name || '',
    })),
  }
}

// --- Zoom Controls ---
function zoomIn() {
  if (!svg || !zoomBehavior) return
  svg.transition().duration(300).call(zoomBehavior.scaleBy, 1.5)
}

function zoomOut() {
  if (!svg || !zoomBehavior) return
  svg.transition().duration(300).call(zoomBehavior.scaleBy, 0.67)
}

function zoomReset() {
  if (!svg || !zoomBehavior) return
  svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity)
}

// --- Filter Toggle ---
function toggleFilter(type) {
  const next = new Set(activeFilters.value)
  if (next.has(type)) {
    next.delete(type)
  } else {
    next.add(type)
  }
  activeFilters.value = next
}

function clearFilters() {
  activeFilters.value = new Set()
  searchQuery.value = ''
}

// --- Watchers ---
watch(filteredData, () => {
  nextTick(() => renderGraph())
}, { deep: true })

// --- Lifecycle ---
onMounted(async () => {
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (filteredData.value.nodes.length) renderGraph()
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

  await loadGraphData()
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-56px)]">
    <!-- Header bar -->
    <div class="px-4 md:px-6 py-3 border-b border-black/10 dark:border-white/10 flex items-center gap-4 flex-wrap">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-[#2068FF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3" />
          <circle cx="5" cy="5" r="2" />
          <circle cx="19" cy="5" r="2" />
          <circle cx="19" cy="19" r="2" />
          <circle cx="5" cy="19" r="2" />
          <line x1="9.5" y1="9.5" x2="6.5" y2="6.5" />
          <line x1="14.5" y1="9.5" x2="17.5" y2="6.5" />
          <line x1="14.5" y1="14.5" x2="17.5" y2="17.5" />
          <line x1="9.5" y1="14.5" x2="6.5" y2="17.5" />
        </svg>
        <h1 class="text-sm font-semibold text-[var(--color-text)]">Knowledge Graph</h1>
      </div>

      <!-- Search -->
      <div class="relative flex-1 max-w-xs">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-muted)]" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clip-rule="evenodd" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search nodes..."
          class="w-full pl-8 pr-3 py-1.5 text-xs bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-lg text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[#2068FF] focus:border-[#2068FF]"
        />
      </div>

      <!-- Entity type filters -->
      <div class="flex items-center gap-1.5 flex-wrap">
        <button
          v-for="stat in entityTypeStats"
          :key="stat.type"
          @click="toggleFilter(stat.type)"
          class="flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium transition-all"
          :class="!activeFilters.size || activeFilters.has(stat.type)
            ? 'bg-black/5 dark:bg-white/10 text-[var(--color-text)]'
            : 'bg-black/[0.02] dark:bg-white/[0.03] text-[var(--color-text-muted)] opacity-50'"
        >
          <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: stat.color }" />
          {{ stat.type }}
          <span class="text-[var(--color-text-muted)]">({{ stat.count }})</span>
        </button>
        <button
          v-if="activeFilters.size || searchQuery"
          @click="clearFilters"
          class="px-2 py-1 rounded-md text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
        >Clear</button>
      </div>

      <!-- Stats -->
      <div class="ml-auto flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
        <span>{{ nodeCount }} nodes</span>
        <span>{{ edgeCount }} edges</span>
      </div>
    </div>

    <!-- Graph canvas -->
    <div ref="containerRef" class="flex-1 relative overflow-hidden bg-[#f8f9fa] dark:bg-[#0a0a1a]">
      <!-- Loading state -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-10">
        <div class="flex flex-col items-center gap-3">
          <div class="w-8 h-8 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin" />
          <span class="text-xs text-[var(--color-text-muted)]">Loading graph data...</span>
        </div>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="absolute inset-0 flex items-center justify-center z-10">
        <div class="text-center">
          <p class="text-sm text-[var(--color-text)] mb-2">Failed to load graph</p>
          <p class="text-xs text-[var(--color-text-muted)] mb-4">{{ error }}</p>
          <button @click="loadGraphData" class="px-3 py-1.5 text-xs bg-[#2068FF] text-white rounded-lg hover:bg-[#1a5ae0] transition-colors">Retry</button>
        </div>
      </div>

      <!-- Empty filtered state -->
      <div v-else-if="!filteredData.nodes.length && graphData.nodes.length" class="absolute inset-0 flex items-center justify-center z-10">
        <div class="text-center">
          <p class="text-sm text-[var(--color-text)] mb-2">No matching nodes</p>
          <p class="text-xs text-[var(--color-text-muted)] mb-4">Adjust your search or filters</p>
          <button @click="clearFilters" class="px-3 py-1.5 text-xs bg-[#2068FF] text-white rounded-lg hover:bg-[#1a5ae0] transition-colors">Clear Filters</button>
        </div>
      </div>

      <svg ref="svgRef" class="w-full h-full" />

      <!-- Zoom controls -->
      <div class="absolute bottom-6 right-6 z-10 flex flex-col gap-1">
        <button
          @click="zoomIn"
          class="w-8 h-8 flex items-center justify-center bg-white dark:bg-[#1a1a2e] border border-black/10 dark:border-white/10 rounded-lg shadow-sm hover:bg-black/5 dark:hover:bg-white/10 transition-colors text-[var(--color-text)]"
          title="Zoom in"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" /></svg>
        </button>
        <button
          @click="zoomOut"
          class="w-8 h-8 flex items-center justify-center bg-white dark:bg-[#1a1a2e] border border-black/10 dark:border-white/10 rounded-lg shadow-sm hover:bg-black/5 dark:hover:bg-white/10 transition-colors text-[var(--color-text)]"
          title="Zoom out"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path d="M6 10a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1z" /></svg>
        </button>
        <button
          @click="zoomReset"
          class="w-8 h-8 flex items-center justify-center bg-white dark:bg-[#1a1a2e] border border-black/10 dark:border-white/10 rounded-lg shadow-sm hover:bg-black/5 dark:hover:bg-white/10 transition-colors text-[var(--color-text)] text-xs font-medium"
          title="Reset zoom"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg>
        </button>
      </div>

      <!-- Node detail panel -->
      <Transition name="slide">
        <div
          v-if="selectedNode"
          class="absolute top-0 right-0 z-20 h-full w-full sm:w-80 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border-l border-black/10 dark:border-white/10 overflow-y-auto"
        >
          <div class="p-5">
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

            <span
              class="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-wider mb-4"
              :style="{ backgroundColor: selectedNode.color + '22', color: selectedNode.color }"
            >{{ selectedNode.entityType }}</span>

            <div v-if="selectedNode.summary" class="mb-5">
              <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Summary</h4>
              <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">{{ selectedNode.summary }}</p>
            </div>

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
