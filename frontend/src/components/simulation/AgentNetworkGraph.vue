<script setup>
import { ref, computed, inject, watch, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  taskId: { type: String, required: true },
})

const polling = inject('polling')
const demoMode = inject('demoMode', ref(false))

// DOM refs
const svgRef = ref(null)
const containerRef = ref(null)

// D3 state (not reactive — managed imperatively)
let sim = null
let svg = null
let zoomGroup = null
let resizeObserver = null
let resizeTimer = null

// Reactive state
const networkData = ref({ nodes: [], links: [] })
const selectedAgent = ref(null)
const loading = ref(true)
const errorMsg = ref('')

// --- Role / color mapping ---
const ROLE_COLORS = {
  vp: '#ff5600',
  director: '#ff5600',
  head: '#ff5600',
  chief: '#ff5600',
  cro: '#ff5600',
  cfo: '#ff5600',
  manager: '#2068FF',
  lead: '#2068FF',
  engineer: '#AA00FF',
  architect: '#AA00FF',
}
const DEFAULT_COLOR = '#667'

function getAgentColor(name) {
  const lower = (name || '').toLowerCase()
  for (const [key, color] of Object.entries(ROLE_COLORS)) {
    if (lower.includes(key)) return color
  }
  // Hash fallback into brand palette
  const palette = ['#ff5600', '#2068FF', '#AA00FF']
  let hash = 0
  for (const ch of lower) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0
  return palette[Math.abs(hash) % palette.length]
}

function getShortName(name) {
  if (!name) return '?'
  const comma = name.indexOf(',')
  return comma > 0 ? name.slice(0, comma) : name
}

// --- Stats ---
const nodeCount = computed(() => networkData.value.nodes.length)
const linkCount = computed(() => networkData.value.links.length)

const roleStats = computed(() => {
  const counts = {}
  for (const n of networkData.value.nodes) {
    const color = getAgentColor(n.name)
    const label = color === '#ff5600' ? 'Leadership' : color === '#2068FF' ? 'Management' : 'Technical'
    counts[label] = counts[label] || { label, color, count: 0 }
    counts[label].count++
  }
  return Object.values(counts).sort((a, b) => b.count - a.count)
})

// --- Data fetching ---
async function fetchNetwork() {
  if (demoMode.value) {
    loadDemoData()
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await simulationApi.getAgentNetwork(props.taskId)
    if (res.data?.success && res.data.data.nodes.length) {
      networkData.value = res.data.data
    } else {
      loadDemoData()
    }
  } catch {
    loadDemoData()
  } finally {
    loading.value = false
  }
}

function loadDemoData() {
  const agentNames = [
    'Sarah Chen, VP Support @ Acme SaaS',
    'James Wright, CX Director @ Retail Plus',
    'Robert Williams, IT Director @ EduSpark',
    'Michael Chang, Head of Ops @ FinEdge',
    'Anika Sharma, Head of Support Engineering @ DevStack',
    'Sofia Martinez, Support Manager @ QuickShip',
    'Rachel Torres, VP Support @ CloudOps Inc',
    'David Park, CX Lead @ HealthFirst',
    'Emily Watson, IT Manager @ DataPulse',
    'Carlos Rivera, Director of Operations @ NovaPay',
    'Lisa Kim, Solutions Architect @ TechBridge',
    'Tom Bradley, Sales Engineer @ GrowthPath',
  ]

  const nodes = agentNames.map((name, i) => ({
    id: i,
    name,
    actions_count: Math.floor(Math.random() * 25) + 5,
    platforms: [Math.random() > 0.4 ? 'twitter' : 'reddit'],
    action_types: {
      CREATE_POST: Math.floor(Math.random() * 8) + 1,
      REPLY: Math.floor(Math.random() * 6),
      LIKE: Math.floor(Math.random() * 10),
    },
  }))

  const links = []
  for (let i = 0; i < nodes.length; i++) {
    // Each agent connects to 2-4 others
    const numLinks = 2 + Math.floor(Math.random() * 3)
    for (let k = 0; k < numLinks; k++) {
      let j = Math.floor(Math.random() * nodes.length)
      if (j === i) j = (j + 1) % nodes.length
      const key = `${Math.min(i, j)}-${Math.max(i, j)}`
      if (!links.find(l => `${Math.min(l.source, l.target)}-${Math.max(l.source, l.target)}` === key)) {
        links.push({
          source: i,
          target: j,
          weight: Math.floor(Math.random() * 5) + 1,
        })
      }
    }
  }

  networkData.value = { nodes, links }
  loading.value = false
}

// --- D3 rendering ---

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

function renderGraph() {
  const container = containerRef.value
  if (!container || !svgRef.value || !networkData.value.nodes.length) return

  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  // Cleanup
  if (sim) { sim.stop(); sim = null }
  d3.select(svgRef.value).selectAll('*').remove()

  const dark = isDarkMode()
  const maxActions = Math.max(1, ...networkData.value.nodes.map(n => n.actions_count))
  const maxWeight = Math.max(1, ...networkData.value.links.map(l => l.weight))

  // Build node objects
  const nodes = networkData.value.nodes.map(n => ({
    ...n,
    color: getAgentColor(n.name),
    radius: 8 + (n.actions_count / maxActions) * 16,
  }))

  const nodeById = new Map(nodes.map(n => [n.id, n]))

  const links = networkData.value.links
    .filter(l => nodeById.has(l.source) && nodeById.has(l.target))
    .map(l => ({ ...l }))

  svg = d3.select(svgRef.value).attr('width', width).attr('height', height)

  const zoom = d3.zoom()
    .scaleExtent([0.2, 5])
    .on('zoom', (event) => zoomGroup.attr('transform', event.transform))
  svg.call(zoom)

  zoomGroup = svg.append('g')

  // Force simulation
  sim = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-250))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 6))

  // Links
  const link = zoomGroup.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)')
    .attr('stroke-width', d => 0.5 + (d.weight / maxWeight) * 3)
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
      selectAgent(d)
    })

  // Glow ring
  node.append('circle')
    .attr('r', d => d.radius + 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.15)

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
    .text(d => getShortName(d.name))
    .attr('dy', d => d.radius + 14)
    .attr('text-anchor', 'middle')
    .attr('fill', dark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)')
    .attr('font-size', '10px')
    .style('pointer-events', 'none')

  // Staggered fade-in
  node.transition().delay((_, i) => i * 50).duration(400).style('opacity', 1)
  link.transition().delay((_, i) => nodes.length * 50 + i * 20).duration(300).style('opacity', 1)

  // Tick
  sim.on('tick', () => {
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  // Deselect on background click
  svg.on('click', () => { selectedAgent.value = null })
}

function dragstarted(event, d) {
  if (!event.active) sim.alphaTarget(0.3).restart()
  d.fx = d.x; d.fy = d.y
}
function dragged(event, d) {
  d.fx = event.x; d.fy = event.y
}
function dragended(event, d) {
  if (!event.active) sim.alphaTarget(0)
  d.fx = null; d.fy = null
}

function selectAgent(d) {
  const connections = networkData.value.links.filter(
    l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source
      const t = typeof l.target === 'object' ? l.target.id : l.target
      return s === d.id || t === d.id
    }
  )
  selectedAgent.value = {
    ...d,
    shortName: getShortName(d.name),
    connectionCount: connections.length,
    topActions: Object.entries(d.action_types || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5),
  }
}

// --- Lifecycle ---

function handleResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(renderGraph, 200)
}

watch(networkData, () => renderGraph(), { deep: true })

watch(() => polling.simStatus.value, (status) => {
  if (status === 'completed' || status === 'running') {
    fetchNetwork()
  }
})

onMounted(() => {
  fetchNetwork()

  resizeObserver = new ResizeObserver(handleResize)
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  if (sim) { sim.stop(); sim = null }
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header bar -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-[var(--color-border)]">
      <div class="flex items-center gap-3">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Agent Network</h3>
        <span v-if="nodeCount" class="text-xs text-[var(--color-text-muted)]">
          {{ nodeCount }} agents &middot; {{ linkCount }} connections
        </span>
      </div>

      <!-- Legend -->
      <div v-if="roleStats.length" class="flex items-center gap-3">
        <div
          v-for="stat in roleStats"
          :key="stat.label"
          class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]"
        >
          <span class="w-2 h-2 rounded-full" :style="{ background: stat.color }" />
          {{ stat.label }} ({{ stat.count }})
        </div>
      </div>
    </div>

    <!-- Graph container -->
    <div ref="containerRef" class="flex-1 relative bg-[var(--color-bg)] overflow-hidden">
      <!-- Loading skeleton -->
      <div
        v-if="loading"
        class="absolute inset-0 flex items-center justify-center"
      >
        <div class="flex flex-col items-center gap-3">
          <svg class="w-8 h-8 animate-spin text-[#2068FF]" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span class="text-sm text-[var(--color-text-muted)]">Loading agent network...</span>
        </div>
      </div>

      <!-- SVG graph -->
      <svg
        ref="svgRef"
        class="w-full h-full"
        :class="{ 'opacity-0': loading }"
      />

      <!-- Empty state -->
      <div
        v-if="!loading && !networkData.nodes.length"
        class="absolute inset-0 flex items-center justify-center"
      >
        <div class="text-center">
          <p class="text-sm text-[var(--color-text-muted)]">No agent network data available yet.</p>
          <p class="text-xs text-[var(--color-text-muted)] mt-1">Network will appear once the simulation starts running.</p>
        </div>
      </div>

      <!-- Selected agent panel -->
      <Transition name="slide-in">
        <div
          v-if="selectedAgent"
          class="absolute top-3 right-3 w-72 bg-[var(--card-bg,#fff)] border border-[var(--color-border)] rounded-xl shadow-lg p-4"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-2">
              <span
                class="w-3 h-3 rounded-full shrink-0"
                :style="{ background: selectedAgent.color }"
              />
              <span class="text-sm font-semibold text-[var(--color-text)] leading-tight">
                {{ selectedAgent.shortName }}
              </span>
            </div>
            <button
              @click.stop="selectedAgent = null"
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-lg leading-none"
            >&times;</button>
          </div>

          <p class="text-xs text-[var(--color-text-muted)] mb-3 truncate">{{ selectedAgent.name }}</p>

          <div class="grid grid-cols-2 gap-2 mb-3">
            <div class="bg-[var(--color-bg-subtle,#f8f8f8)] rounded-lg px-3 py-2">
              <div class="text-lg font-bold text-[var(--color-text)]">{{ selectedAgent.actions_count }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)]">Actions</div>
            </div>
            <div class="bg-[var(--color-bg-subtle,#f8f8f8)] rounded-lg px-3 py-2">
              <div class="text-lg font-bold text-[var(--color-text)]">{{ selectedAgent.connectionCount }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)]">Connections</div>
            </div>
          </div>

          <div v-if="selectedAgent.topActions.length">
            <div class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1.5">Activity</div>
            <div class="space-y-1">
              <div
                v-for="[type, count] in selectedAgent.topActions"
                :key="type"
                class="flex items-center justify-between text-xs"
              >
                <span class="text-[var(--color-text-secondary)]">{{ type.replace(/_/g, ' ') }}</span>
                <span class="font-medium text-[var(--color-text)]">{{ count }}</span>
              </div>
            </div>
          </div>

          <div v-if="selectedAgent.platforms?.length" class="mt-3 flex gap-1.5">
            <span
              v-for="p in selectedAgent.platforms"
              :key="p"
              class="text-[10px] px-2 py-0.5 rounded-full bg-[rgba(32,104,255,0.1)] text-[#2068FF] font-medium"
            >{{ p }}</span>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Error bar -->
    <div v-if="errorMsg" class="px-4 py-2 bg-red-50 border-t border-red-200 text-xs text-red-600">
      {{ errorMsg }}
    </div>
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
  transform: translateX(12px);
}
</style>
