<script setup>
import { ref, computed, inject, watch, nextTick, onMounted, onUnmounted } from 'vue'
import ForceGraph3D from '3d-force-graph'
import { DEMO_NODES, DEMO_EDGES } from '../../data/demoGraphData'

const props = defineProps({
  taskId: { type: String, required: true },
  demoMode: { type: Boolean, default: false },
})

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

const polling = inject('polling')
const { graphStatus, graphProgress, graphData, graphTask, isDemoFallback } = polling

const containerRef = ref(null)
const selectedNode = ref(null)
const nodeCount = ref(0)
const edgeCount = ref(0)
const errorMsg = ref('')

let graph = null
let resizeObserver = null
let zoomTimer = null
let demoBuildTimer = null
let themeObserver = null

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

function buildGraphData() {
  const raw = graphData.value
  if (!raw.nodes.length) return null

  const centrality = computeCentrality(raw.nodes, raw.edges)

  const nodes = raw.nodes.map(n => ({
    id: n.uuid,
    name: n.name,
    labels: n.labels,
    summary: n.summary || '',
    attributes: n.attributes || {},
    centrality: centrality[n.uuid] || 0,
    color: getNodeColor(n.labels),
    val: 1 + (centrality[n.uuid] || 0) * 8,
  }))

  const nodeIds = new Set(nodes.map(n => n.id))
  const links = raw.edges
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
    }))

  nodeCount.value = nodes.length
  edgeCount.value = links.length

  return { nodes, links }
}

function renderGraph() {
  const container = containerRef.value
  if (!container) return

  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  const data = buildGraphData()
  if (!data) return

  const dark = isDarkMode()

  if (graph) {
    graph.graphData(data)
    graph.backgroundColor(dark ? '#0a0a1a' : '#f8f9fa')
    return
  }

  graph = ForceGraph3D()(container)
    .backgroundColor(dark ? '#0a0a1a' : '#f8f9fa')
    .showNavInfo(false)
    .width(width)
    .height(height)
    .nodeId('id')
    .nodeColor('color')
    .nodeVal('val')
    .nodeOpacity(0.9)
    .nodeResolution(16)
    .nodeLabel(n => [
      `<div style="padding:6px 10px;font-size:12px;line-height:1.4">`,
      `<div style="color:${n.color};font-weight:600">${n.name}</div>`,
      `<div style="color:rgba(255,255,255,0.5);font-size:11px">${getEntityType(n.labels)}</div>`,
      `</div>`,
    ].join(''))
    .linkColor(() => dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)')
    .linkWidth(0.4)
    .linkOpacity(0.6)
    .linkDirectionalArrowLength(3.5)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalArrowColor(() => dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')
    .linkDirectionalParticles(1)
    .linkDirectionalParticleWidth(1)
    .linkDirectionalParticleSpeed(0.005)
    .linkDirectionalParticleColor(link => {
      const src = typeof link.source === 'object' ? link.source : null
      return src?.color || '#667'
    })
    .onNodeClick(node => selectNode(node))
    .onBackgroundClick(() => { selectedNode.value = null })
    .graphData(data)

  zoomTimer = setTimeout(() => {
    if (graph) graph.zoomToFit(400, 60)
  }, 1500)
}

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
      name: e.name || '',
      fact: e.fact || '',
      direction: e.source_node_uuid === d.id ? 'outgoing' : 'incoming',
      target: e.source_node_uuid === d.id
        ? graphData.value.nodes.find(n => n.uuid === e.target_node_uuid)?.name || ''
        : graphData.value.nodes.find(n => n.uuid === e.source_node_uuid)?.name || '',
    })),
  }
}

function loadDemoData() {
  if (demoBuildTimer) clearInterval(demoBuildTimer)

  graphStatus.value = 'building'
  graphProgress.value = 0
  graphData.value = { nodes: [], edges: [] }
  nodeCount.value = 0
  edgeCount.value = 0

  let idx = 0
  const BATCH = 3
  const INTERVAL = 200

  demoBuildTimer = setInterval(() => {
    if (idx >= DEMO_NODES.length) {
      clearInterval(demoBuildTimer)
      demoBuildTimer = null
      graphStatus.value = 'complete'
      graphProgress.value = 100
      return
    }

    const end = Math.min(idx + BATCH, DEMO_NODES.length)
    graphData.value.nodes.push(...DEMO_NODES.slice(idx, end))

    const nodeIds = new Set(graphData.value.nodes.map(n => n.uuid))
    graphData.value.edges = DEMO_EDGES.filter(
      e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid),
    )

    idx = end
    graphProgress.value = Math.round((idx / DEMO_NODES.length) * 100)
    nodeCount.value = graphData.value.nodes.length
    edgeCount.value = graphData.value.edges.length

    const msgIdx = Math.min(
      Math.floor((idx / DEMO_NODES.length) * BUILD_MESSAGES.length),
      BUILD_MESSAGES.length - 1,
    )
    graphTask.value = { message: BUILD_MESSAGES[msgIdx] }
  }, INTERVAL)
}

watch(graphData, () => {
  if (graphStatus.value === 'complete' && graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }
}, { deep: true })

watch(graphStatus, (val) => {
  if (val === 'complete' && graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }
  if (val === 'failed') {
    errorMsg.value = graphTask.value?.message || 'Build failed'
  }
})

watch(() => props.demoMode, (val) => { if (val) loadDemoData() })
watch(isDemoFallback, (val) => { if (val) loadDemoData() })

onMounted(() => {
  if (graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }

  resizeObserver = new ResizeObserver(() => {
    if (graph && containerRef.value) {
      const w = containerRef.value.clientWidth
      const h = containerRef.value.clientHeight
      if (w && h) graph.width(w).height(h)
    }
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'class' && graph) {
        const dark = isDarkMode()
        graph.backgroundColor(dark ? '#0a0a1a' : '#f8f9fa')
        graph.linkColor(() => dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)')
        graph.linkDirectionalArrowColor(() => dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')
        break
      }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

  if (props.demoMode || isDemoFallback.value) {
    loadDemoData()
  }

  if (graphStatus.value === 'complete' && graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }
})

onUnmounted(() => {
  if (zoomTimer) clearTimeout(zoomTimer)
  if (demoBuildTimer) clearInterval(demoBuildTimer)
  if (graph) {
    graph.pauseAnimation()
    graph._destructor()
    graph = null
  }
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
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

    <!-- Build progress overlay center -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'building' && !graphData.nodes.length"
        class="absolute inset-0 flex items-center justify-center z-10"
      >
        <div class="bg-black/60 backdrop-blur-sm rounded-xl px-5 py-3 flex items-center gap-4">
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

    <!-- Entity type stats panel bottom-left -->
    <div
      v-if="entityTypeStats.length && graphStatus !== 'failed'"
      class="absolute bottom-6 left-4 z-10 bg-black/5 dark:bg-white/5 backdrop-blur-sm border border-black/10 dark:border-white/10 rounded-lg p-4 max-w-56"
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
        <span>{{ nodeCount }} nodes</span>
        <span>{{ edgeCount }} edges</span>
      </div>
    </div>

    <!-- Node detail panel right side -->
    <Transition name="slide">
      <div
        v-if="selectedNode"
        class="absolute top-0 right-0 z-20 h-full w-80 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border-l border-black/10 dark:border-white/10 overflow-y-auto"
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
          >
            {{ selectedNode.entityType }}
          </span>

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
    </Transition>

    <!-- Controls hint + count bottom-right -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'complete'"
        class="absolute bottom-6 right-6 z-10 flex flex-col items-end gap-1"
      >
        <span class="text-[10px] text-[var(--color-text-muted)] opacity-60">Drag to rotate &middot; Scroll to zoom</span>
        <span class="text-xs text-[var(--color-text-muted)]">{{ nodeCount }} nodes, {{ edgeCount }} edges</span>
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
