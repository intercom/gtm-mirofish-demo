<script setup>
import { ref, computed, inject, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useForceGraph3D } from '../../composables/useForceGraph3D'
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
const hoveredNode = ref(null)
const tooltipPos = ref(null)
const nodeCount = ref(0)
const edgeCount = ref(0)
const errorMsg = ref('')
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
    .map(([type, count]) => ({ type, count, color: getNodeColor([type]) }))
})

const buildMessage = computed(() => {
  const p = graphProgress.value
  const msgIdx = Math.min(
    Math.floor((p / 100) * BUILD_MESSAGES.length),
    BUILD_MESSAGES.length - 1,
  )
  return graphTask.value?.message || BUILD_MESSAGES[msgIdx] || 'Initializing...'
})

const tooltipStyle = computed(() => {
  if (!tooltipPos.value) return { display: 'none' }
  return {
    left: tooltipPos.value.x + 'px',
    top: (tooltipPos.value.y - 48) + 'px',
    transform: 'translateX(-50%)',
  }
})

const graph3D = useForceGraph3D({
  onNodeClick(id) {
    if (!id) { selectedNode.value = null; return }
    const raw = graphData.value.nodes.find(n => n.uuid === id)
    if (!raw) return
    const centrality = computeCentrality(graphData.value.nodes, graphData.value.edges)
    const connections = graphData.value.edges.filter(
      e => e.source_node_uuid === id || e.target_node_uuid === id,
    )
    selectedNode.value = {
      id,
      name: raw.name,
      labels: raw.labels,
      summary: raw.summary || '',
      attributes: raw.attributes || {},
      entityType: getEntityType(raw.labels),
      color: getNodeColor(raw.labels),
      centrality: centrality[id] || 0,
      connections: connections.map(e => ({
        name: e.name || e.fact_type || '',
        fact: e.fact || '',
        direction: e.source_node_uuid === id ? 'outgoing' : 'incoming',
        target: e.source_node_uuid === id
          ? graphData.value.nodes.find(n => n.uuid === e.target_node_uuid)?.name || ''
          : graphData.value.nodes.find(n => n.uuid === e.source_node_uuid)?.name || '',
      })),
    }
  },
  onNodeHover(id, data, pos) {
    if (!id) { hoveredNode.value = null; tooltipPos.value = null; return }
    hoveredNode.value = {
      name: data.name,
      color: data.color,
      entityType: getEntityType(data.labels),
    }
    tooltipPos.value = pos
  },
})

function renderGraph() {
  if (!graphData.value.nodes.length) return
  const centrality = computeCentrality(graphData.value.nodes, graphData.value.edges)
  const nodeMap = new Set(graphData.value.nodes.map(n => n.uuid))

  const nodes = graphData.value.nodes.map(n => ({
    id: n.uuid,
    name: n.name,
    labels: n.labels,
    summary: n.summary || '',
    attributes: n.attributes || {},
    color: getNodeColor(n.labels),
    radius: 3 + (centrality[n.uuid] || 0) * 8,
    centrality: centrality[n.uuid] || 0,
  }))

  const edges = graphData.value.edges
    .filter(e => nodeMap.has(e.source_node_uuid) && nodeMap.has(e.target_node_uuid))
    .map(e => ({
      sourceId: e.source_node_uuid,
      targetId: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
    }))

  nodeCount.value = nodes.length
  edgeCount.value = edges.length

  graph3D.setData(nodes, edges)
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
  if (containerRef.value) {
    graph3D.init(containerRef.value)
  }

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'class') {
        graph3D.setDarkMode(isDarkMode())
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
  if (demoBuildTimer) clearInterval(demoBuildTimer)
  if (themeObserver) themeObserver.disconnect()
  graph3D.dispose()
})
</script>

<template>
  <div ref="containerRef" class="w-full h-full relative overflow-hidden bg-[#f8f9fa] dark:bg-[#0a0a1a]">
    <!-- Status badge top-left -->
    <div class="absolute top-4 left-4 z-10 flex items-center gap-3">
      <span
        class="px-3 py-1 rounded-full text-xs font-medium"
        :class="{
          'bg-yellow-500/20 text-yellow-400': graphStatus === 'building',
          'bg-green-500/20 text-green-400': graphStatus === 'complete',
          'bg-red-500/20 text-red-400': graphStatus === 'failed',
        }"
      >
        <template v-if="graphStatus === 'building'">Building Graph... {{ graphProgress }}%</template>
        <template v-else-if="graphStatus === 'complete'">Complete</template>
        <template v-else>Failed</template>
      </span>
    </div>

    <!-- Build progress overlay -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'building'"
        class="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-black/60 dark:bg-black/70 backdrop-blur-sm rounded-xl px-5 py-3 flex items-center gap-4"
      >
        <svg viewBox="0 0 36 36" class="w-9 h-9 -rotate-90 flex-shrink-0">
          <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="3" />
          <circle
            cx="18" cy="18" r="14" fill="none" stroke="#2068FF" stroke-width="3"
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
        <div class="w-14 h-14 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
          <svg class="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        </div>
        <p class="text-[var(--color-text)] text-sm font-medium mb-2">Graph build failed</p>
        <p class="text-[var(--color-text-muted)] text-xs mb-6">{{ errorMsg }}</p>
      </div>
    </div>

    <!-- Hover tooltip -->
    <div
      v-if="hoveredNode"
      class="absolute z-20 pointer-events-none"
      :style="tooltipStyle"
    >
      <div class="bg-black/80 text-white text-xs rounded-lg px-3 py-2 shadow-lg backdrop-blur-sm whitespace-nowrap">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full flex-shrink-0" :style="{ backgroundColor: hoveredNode.color }" />
          <span class="font-medium">{{ hoveredNode.name }}</span>
        </div>
        <span class="text-white/50 text-[10px]">{{ hoveredNode.entityType }}</span>
      </div>
    </div>

    <!-- Entity type stats bottom-left -->
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

    <!-- Controls hint bottom-right -->
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
