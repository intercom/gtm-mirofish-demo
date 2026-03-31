<script setup>
import { ref, computed, inject, watch, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import { communitiesApi } from '../../api/communities'

const props = defineProps({
  taskId: { type: String, required: true },
  demoMode: { type: Boolean, default: false },
})

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

const polling = inject('polling')
const { graphData, graphId, graphStatus } = polling

// D3 refs
const svgRef = ref(null)
const containerRef = ref(null)
let simulation = null
let svg = null
let zoomGroup = null
let resizeObserver = null
let resizeTimer = null
let themeObserver = null

// State
const communities = ref([])
const loading = ref(false)
const errorMsg = ref('')
const selectedCommunity = ref(null)
const collapsedIds = ref(new Set())

// Role -> color mapping (Intercom brand palette)
const ROLE_COLORS = {
  persona: '#ff5600',
  topic: '#2068FF',
  process: '#AA00FF',
  entity: '#667788',
}

// Community hull fill colors (low opacity)
const COMMUNITY_COLORS = [
  '#2068FF', '#ff5600', '#AA00FF', '#10B981',
  '#F59E0B', '#EC4899', '#6366F1', '#14B8A6',
]

const hasCommunities = computed(() => communities.value.length > 0)

const isGraphReady = computed(() =>
  graphStatus.value === 'complete' && graphData.value?.nodes?.length > 0
)

// Fetch communities when graph is ready
watch(isGraphReady, async (ready) => {
  if (ready) await fetchCommunities()
}, { immediate: true })

async function fetchCommunities() {
  const id = graphId.value
  if (!id && !props.demoMode) return

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await communitiesApi.detect(id || 'demo')
    if (res.data?.success) {
      communities.value = res.data.data.communities || []
      await renderCommunityGraph()
    } else {
      errorMsg.value = res.data?.error || 'Failed to detect communities'
    }
  } catch (err) {
    if (props.demoMode || !graphId.value) {
      loadDemoCommunities()
    } else {
      errorMsg.value = err.message || 'Failed to load communities'
    }
  } finally {
    loading.value = false
  }
}

function loadDemoCommunities() {
  communities.value = [
    {
      id: 0,
      label: 'Customer Support',
      members: [
        { uuid: 'p4', name: 'VP of Support', labels: ['Persona'], role: 'persona' },
        { uuid: 'p5', name: 'CX Director', labels: ['Persona'], role: 'persona' },
        { uuid: 't1', name: 'Customer Support', labels: ['Topic'], role: 'topic' },
        { uuid: 't4', name: 'Fin AI Agent', labels: ['Topic'], role: 'topic' },
        { uuid: 't5', name: 'Resolution Rate', labels: ['Topic'], role: 'topic' },
      ],
      member_count: 5,
      topics: ['Customer Support', 'Fin AI Agent', 'Resolution Rate'],
      sentiment: 'positive',
      cohesion: 0.6,
    },
    {
      id: 1,
      label: 'Growth & Acquisition',
      members: [
        { uuid: 'p1', name: 'Enterprise Buyer', labels: ['Persona'], role: 'persona' },
        { uuid: 'p2', name: 'SMB Founder', labels: ['Persona'], role: 'persona' },
        { uuid: 'p3', name: 'Developer Advocate', labels: ['Persona'], role: 'persona' },
        { uuid: 'e1', name: 'Product-Led Growth', labels: ['Process'], role: 'process' },
        { uuid: 'e2', name: 'Sales-Led Motion', labels: ['Process'], role: 'process' },
      ],
      member_count: 5,
      topics: ['Product-Led Growth', 'Sales-Led Motion'],
      sentiment: 'positive',
      cohesion: 0.45,
    },
    {
      id: 2,
      label: 'Financial & Strategy',
      members: [
        { uuid: 'p6', name: 'CFO', labels: ['Persona'], role: 'persona' },
        { uuid: 't3', name: 'Pricing Strategy', labels: ['Topic'], role: 'topic' },
        { uuid: 't6', name: 'Cost Reduction', labels: ['Topic'], role: 'topic' },
        { uuid: 't2', name: 'AI Automation', labels: ['Topic'], role: 'topic' },
        { uuid: 'e3', name: 'ROI Analysis', labels: ['Process'], role: 'process' },
        { uuid: 'e4', name: 'Contract Renewal', labels: ['Event'], role: 'process' },
      ],
      member_count: 6,
      topics: ['Pricing Strategy', 'Cost Reduction', 'AI Automation'],
      sentiment: 'mixed',
      cohesion: 0.38,
    },
  ]
  renderCommunityGraph()
}

function toggleCollapse(commId) {
  const s = new Set(collapsedIds.value)
  if (s.has(commId)) {
    s.delete(commId)
  } else {
    s.add(commId)
  }
  collapsedIds.value = s
  renderCommunityGraph()
}

function selectCommunity(comm) {
  selectedCommunity.value = selectedCommunity.value?.id === comm.id ? null : comm
}

// --- D3 Rendering ---

function renderCommunityGraph() {
  if (!svgRef.value || !communities.value.length) return
  if (simulation) { simulation.stop(); simulation = null }

  const dark = isDarkMode()
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  d3.select(svgRef.value).selectAll('*').remove()

  svg = d3.select(svgRef.value).attr('width', width).attr('height', height)

  const zoom = d3.zoom()
    .scaleExtent([0.2, 5])
    .on('zoom', (event) => { zoomGroup.attr('transform', event.transform) })
  svg.call(zoom)
  zoomGroup = svg.append('g')

  // Build nodes and links from communities
  const nodes = []
  const links = []
  const nodeCommMap = {}
  const collapsed = collapsedIds.value

  communities.value.forEach((comm, ci) => {
    if (collapsed.has(comm.id)) {
      // Collapsed: single proxy node
      nodes.push({
        id: `comm-${comm.id}`,
        name: comm.label,
        role: 'community',
        communityId: comm.id,
        communityIndex: ci,
        radius: 18 + comm.member_count * 2,
        isProxy: true,
        memberCount: comm.member_count,
      })
      comm.members.forEach(m => { nodeCommMap[m.uuid] = `comm-${comm.id}` })
    } else {
      comm.members.forEach(m => {
        nodes.push({
          id: m.uuid,
          name: m.name,
          role: m.role,
          communityId: comm.id,
          communityIndex: ci,
          radius: 8,
          isProxy: false,
        })
        nodeCommMap[m.uuid] = m.uuid
      })
    }
  })

  // Build inter-community edges from original graph data
  const graphEdges = graphData.value?.edges || []
  const nodeIdSet = new Set(nodes.map(n => n.id))
  const linkSet = new Set()

  graphEdges.forEach(e => {
    let sourceId = nodeCommMap[e.source_node_uuid] || e.source_node_uuid
    let targetId = nodeCommMap[e.target_node_uuid] || e.target_node_uuid
    if (!nodeIdSet.has(sourceId) || !nodeIdSet.has(targetId)) return
    if (sourceId === targetId) return

    const key = [sourceId, targetId].sort().join('--')
    if (linkSet.has(key)) return
    linkSet.add(key)

    const sourceComm = nodes.find(n => n.id === sourceId)?.communityId
    const targetComm = nodes.find(n => n.id === targetId)?.communityId
    links.push({
      source: sourceId,
      target: targetId,
      interCommunity: sourceComm !== targetComm,
    })
  })

  // Also add intra-community edges from graph data
  graphEdges.forEach(e => {
    let sourceId = nodeCommMap[e.source_node_uuid] || e.source_node_uuid
    let targetId = nodeCommMap[e.target_node_uuid] || e.target_node_uuid
    if (!nodeIdSet.has(sourceId) || !nodeIdSet.has(targetId)) return
    if (sourceId === targetId) return

    const key = [sourceId, targetId].sort().join('--')
    if (linkSet.has(key)) return
    linkSet.add(key)

    const sourceComm = nodes.find(n => n.id === sourceId)?.communityId
    const targetComm = nodes.find(n => n.id === targetId)?.communityId
    links.push({
      source: sourceId,
      target: targetId,
      interCommunity: sourceComm !== targetComm,
    })
  })

  // Force simulation with community clustering
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(d =>
      d.interCommunity ? 180 : 60
    ))
    .force('charge', d3.forceManyBody().strength(d => d.isProxy ? -400 : -150))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 6))
    .force('cluster', clusterForce(nodes, 0.15))

  // Draw layers: hulls -> links -> nodes

  // Hull group (drawn first, behind everything)
  const hullGroup = zoomGroup.append('g').attr('class', 'hulls')

  // Links
  const link = zoomGroup.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', d => {
      if (d.interCommunity) return dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'
      return dark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.15)'
    })
    .attr('stroke-width', d => d.interCommunity ? 0.5 : 1.5)
    .attr('stroke-dasharray', d => d.interCommunity ? '4,4' : 'none')
    .style('opacity', 0)

  // Nodes
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
      if (d.isProxy) {
        toggleCollapse(d.communityId)
      } else {
        const comm = communities.value.find(c => c.id === d.communityId)
        if (comm) selectCommunity(comm)
      }
    })

  // Proxy nodes (collapsed communities)
  node.filter(d => d.isProxy)
    .append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => COMMUNITY_COLORS[d.communityIndex % COMMUNITY_COLORS.length])
    .attr('fill-opacity', 0.25)
    .attr('stroke', d => COMMUNITY_COLORS[d.communityIndex % COMMUNITY_COLORS.length])
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '6,3')

  node.filter(d => d.isProxy)
    .append('text')
    .text(d => d.name)
    .attr('text-anchor', 'middle')
    .attr('dy', 4)
    .attr('fill', dark ? 'rgba(255,255,255,0.9)' : '#1a1a1a')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .style('pointer-events', 'none')

  node.filter(d => d.isProxy)
    .append('text')
    .text(d => `${d.memberCount} members`)
    .attr('text-anchor', 'middle')
    .attr('dy', 18)
    .attr('fill', dark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)')
    .attr('font-size', '9px')
    .style('pointer-events', 'none')

  // Regular nodes
  node.filter(d => !d.isProxy)
    .append('circle')
    .attr('r', d => d.radius + 3)
    .attr('fill', d => ROLE_COLORS[d.role] || ROLE_COLORS.entity)
    .attr('opacity', 0.2)

  node.filter(d => !d.isProxy)
    .append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => ROLE_COLORS[d.role] || ROLE_COLORS.entity)
    .attr('fill-opacity', 0.85)
    .attr('stroke', d => ROLE_COLORS[d.role] || ROLE_COLORS.entity)
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.4)

  node.filter(d => !d.isProxy)
    .append('text')
    .text(d => d.name)
    .attr('dy', d => d.radius + 14)
    .attr('text-anchor', 'middle')
    .attr('fill', dark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)')
    .attr('font-size', '9px')
    .style('pointer-events', 'none')

  // Entrance animations
  node.transition().delay((d, i) => i * 40).duration(400).style('opacity', 1)
  link.transition().delay((d, i) => nodes.length * 40 + i * 20).duration(300).style('opacity', 1)

  // Tick: update positions and hulls
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y)

    node.attr('transform', d => `translate(${d.x},${d.y})`)

    // Redraw community hulls
    drawHulls(hullGroup, nodes, dark)
  })

  svg.on('click', () => { selectedCommunity.value = null })
}

function drawHulls(hullGroup, nodes, dark) {
  hullGroup.selectAll('path').remove()
  hullGroup.selectAll('text').remove()

  const grouped = {}
  nodes.forEach(n => {
    if (n.isProxy) return
    if (!grouped[n.communityId]) grouped[n.communityId] = []
    grouped[n.communityId].push(n)
  })

  Object.entries(grouped).forEach(([commId, members]) => {
    if (members.length < 2) return
    const points = members.map(m => [m.x, m.y])
    const hull = d3.polygonHull(points)
    if (!hull) return

    const padding = 28
    const padded = expandHull(hull, padding)
    const color = COMMUNITY_COLORS[members[0].communityIndex % COMMUNITY_COLORS.length]

    hullGroup.append('path')
      .attr('d', `M${padded.map(p => p.join(',')).join('L')}Z`)
      .attr('fill', color)
      .attr('fill-opacity', dark ? 0.06 : 0.04)
      .attr('stroke', color)
      .attr('stroke-opacity', dark ? 0.25 : 0.2)
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '8,4')
      .attr('rx', 12)

    // Community label at centroid
    const centroid = d3.polygonCentroid(hull)
    const minY = Math.min(...hull.map(p => p[1]))
    const comm = communities.value.find(c => c.id === Number(commId))
    if (comm) {
      hullGroup.append('text')
        .attr('x', centroid[0])
        .attr('y', minY - padding - 6)
        .attr('text-anchor', 'middle')
        .attr('fill', color)
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .attr('opacity', 0.7)
        .text(comm.label)
    }
  })
}

function expandHull(hull, padding) {
  const centroid = d3.polygonCentroid(hull)
  return hull.map(point => {
    const dx = point[0] - centroid[0]
    const dy = point[1] - centroid[1]
    const dist = Math.sqrt(dx * dx + dy * dy) || 1
    return [
      point[0] + (dx / dist) * padding,
      point[1] + (dy / dist) * padding,
    ]
  })
}

function clusterForce(nodes, strength) {
  const centroids = {}
  return (alpha) => {
    // Compute cluster centroids
    for (const k in centroids) delete centroids[k]
    const counts = {}
    nodes.forEach(n => {
      const key = n.communityId
      if (!centroids[key]) { centroids[key] = { x: 0, y: 0 }; counts[key] = 0 }
      centroids[key].x += n.x || 0
      centroids[key].y += n.y || 0
      counts[key]++
    })
    for (const k in centroids) {
      centroids[k].x /= counts[k]
      centroids[k].y /= counts[k]
    }
    // Pull nodes toward their community centroid
    nodes.forEach(n => {
      const c = centroids[n.communityId]
      if (!c) return
      n.vx += (c.x - n.x) * strength * alpha
      n.vy += (c.y - n.y) * strength * alpha
    })
  }
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x; d.fy = d.y
}
function dragged(event, d) {
  d.fx = event.x; d.fy = event.y
}
function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null; d.fy = null
}

// Sentiment badge helpers
function sentimentColor(s) {
  if (s === 'positive') return 'text-emerald-600 bg-emerald-50'
  if (s === 'negative') return 'text-red-600 bg-red-50'
  if (s === 'mixed') return 'text-amber-600 bg-amber-50'
  return 'text-gray-500 bg-gray-50'
}

function sentimentIcon(s) {
  if (s === 'positive') return '↑'
  if (s === 'negative') return '↓'
  if (s === 'mixed') return '↕'
  return '–'
}

// Responsive + theme
onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderCommunityGraph(), 200)
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'class') { renderCommunityGraph(); break }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="relative w-full h-full flex">
    <!-- D3 Canvas -->
    <div ref="containerRef" class="flex-1 relative overflow-hidden bg-[var(--color-surface)]">
      <!-- Loading overlay -->
      <div
        v-if="loading"
        class="absolute inset-0 flex items-center justify-center bg-white/60 dark:bg-black/40 z-10"
      >
        <div class="flex items-center gap-3 px-4 py-3 rounded-lg bg-white dark:bg-gray-800 shadow-lg">
          <svg class="w-5 h-5 animate-spin text-[#2068FF]" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span class="text-sm font-medium text-[var(--color-text)]">Detecting communities...</span>
        </div>
      </div>

      <!-- Error overlay -->
      <div
        v-if="errorMsg && !loading"
        class="absolute inset-0 flex items-center justify-center z-10"
      >
        <div class="text-center px-6">
          <p class="text-sm text-red-500 mb-2">{{ errorMsg }}</p>
          <button
            @click="fetchCommunities"
            class="text-xs text-[#2068FF] hover:underline"
          >Retry</button>
        </div>
      </div>

      <!-- Waiting for graph -->
      <div
        v-if="!isGraphReady && !loading && !hasCommunities"
        class="absolute inset-0 flex items-center justify-center z-10"
      >
        <p class="text-sm text-[var(--color-text-muted)]">
          Waiting for graph data to detect communities...
        </p>
      </div>

      <svg ref="svgRef" class="w-full h-full" />

      <!-- Legend -->
      <div
        v-if="hasCommunities"
        class="absolute bottom-4 left-4 flex items-center gap-4 px-3 py-2 rounded-lg bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm text-xs border border-[var(--color-border)]"
      >
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-full bg-[#ff5600]" />
          <span class="text-[var(--color-text-secondary)]">Persona</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-full bg-[#2068FF]" />
          <span class="text-[var(--color-text-secondary)]">Topic</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-full bg-[#AA00FF]" />
          <span class="text-[var(--color-text-secondary)]">Process</span>
        </div>
        <div class="text-[var(--color-text-muted)] ml-2">
          <span class="border border-dashed border-current px-1.5 py-0.5 rounded text-[10px]">
            ─ ─ community boundary
          </span>
        </div>
      </div>
    </div>

    <!-- Community Summary Panel -->
    <Transition name="slide-in">
      <div
        v-if="selectedCommunity"
        class="w-full sm:w-72 border-l border-[var(--color-border)] bg-white dark:bg-gray-900 overflow-y-auto shrink-0"
      >
        <div class="p-4">
          <!-- Header -->
          <div class="flex items-start justify-between mb-3">
            <div>
              <h3 class="text-sm font-semibold text-[var(--color-text)]">
                {{ selectedCommunity.label }}
              </h3>
              <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
                Community #{{ selectedCommunity.id }}
              </p>
            </div>
            <button
              @click="selectedCommunity = null"
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] p-0.5"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Stats grid -->
          <div class="grid grid-cols-2 gap-2 mb-4">
            <div class="px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800">
              <p class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Members</p>
              <p class="text-lg font-semibold text-[var(--color-text)]">{{ selectedCommunity.member_count }}</p>
            </div>
            <div class="px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800">
              <p class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Cohesion</p>
              <p class="text-lg font-semibold text-[var(--color-text)]">{{ (selectedCommunity.cohesion * 100).toFixed(0) }}%</p>
            </div>
          </div>

          <!-- Sentiment -->
          <div class="mb-4">
            <p class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Sentiment</p>
            <span
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
              :class="sentimentColor(selectedCommunity.sentiment)"
            >
              {{ sentimentIcon(selectedCommunity.sentiment) }}
              {{ selectedCommunity.sentiment }}
            </span>
          </div>

          <!-- Topics -->
          <div v-if="selectedCommunity.topics?.length" class="mb-4">
            <p class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">Key Topics</p>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="topic in selectedCommunity.topics"
                :key="topic"
                class="px-2 py-0.5 text-xs rounded-full bg-[#2068FF]/10 text-[#2068FF] font-medium"
              >{{ topic }}</span>
            </div>
          </div>

          <!-- Members list -->
          <div>
            <p class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">Members</p>
            <ul class="space-y-1.5">
              <li
                v-for="member in selectedCommunity.members"
                :key="member.uuid"
                class="flex items-center gap-2 text-xs"
              >
                <span
                  class="w-2 h-2 rounded-full shrink-0"
                  :style="{ backgroundColor: ROLE_COLORS[member.role] || ROLE_COLORS.entity }"
                />
                <span class="text-[var(--color-text)] truncate">{{ member.name }}</span>
                <span class="text-[var(--color-text-muted)] ml-auto text-[10px] capitalize">{{ member.role }}</span>
              </li>
            </ul>
          </div>

          <!-- Collapse/Expand -->
          <button
            @click="toggleCollapse(selectedCommunity.id)"
            class="mt-4 w-full text-center text-xs text-[#2068FF] hover:text-[#1a5ae0] font-medium py-2 border border-[#2068FF]/20 rounded-lg hover:bg-[#2068FF]/5 transition-colors"
          >
            {{ collapsedIds.has(selectedCommunity.id) ? 'Expand' : 'Collapse' }} Community
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-in-enter-active,
.slide-in-leave-active {
  transition: all 0.25s ease;
}
.slide-in-enter-from,
.slide-in-leave-to {
  opacity: 0;
  transform: translateX(16px);
}
</style>
