<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import ForceGraph3D from '3d-force-graph'

const props = defineProps({
  networkData: { type: Object, default: null },
  clusterColors: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['node-hover'])

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

const containerRef = ref(null)
const selectedAgent = ref(null)

let graph = null
let resizeObserver = null
let zoomTimer = null
let themeObserver = null

function getNodeColor(node) {
  return props.clusterColors[node.id] || '#2068FF'
}

function getShortName(name) {
  if (!name) return '?'
  return name.split(' ')[0]
}

const graphNodes = computed(() => {
  if (!props.networkData?.nodes?.length) return null

  const nodes = props.networkData.nodes.map(n => ({
    id: n.id,
    name: n.name,
    title: n.title,
    company: n.company,
    centrality: n.centrality,
    betweenness: n.betweenness,
    degree: n.degree,
    color: getNodeColor(n),
    val: 1 + (n.centrality || 0) * 8,
  }))

  const nodeIds = new Set(nodes.map(n => n.id))
  const links = (props.networkData.edges || [])
    .filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
    .map(e => ({
      source: e.source,
      target: e.target,
      weight: e.weight || 1,
      type: e.type || '',
    }))

  return { nodes, links }
})

function renderGraph() {
  const container = containerRef.value
  if (!container) return

  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  const data = graphNodes.value
  if (!data) return

  const dark = isDarkMode()
  const maxWeight = Math.max(1, ...data.links.map(l => l.weight))

  if (graph) {
    graph.graphData({ nodes: [...data.nodes], links: [...data.links] })
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
      n.title ? `<div style="color:rgba(255,255,255,0.6);font-size:11px">${n.title} @ ${n.company}</div>` : '',
      `<div style="color:rgba(255,255,255,0.4);font-size:10px">Centrality: ${n.centrality} · Degree: ${n.degree}</div>`,
      `</div>`,
    ].join(''))
    .linkColor(() => dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)')
    .linkWidth(l => 0.3 + (l.weight / maxWeight) * 2)
    .linkOpacity(0.6)
    .linkDirectionalArrowLength(3.5)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalArrowColor(() => dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')
    .linkDirectionalParticles(l => Math.min(3, Math.ceil(l.weight / 2)))
    .linkDirectionalParticleWidth(1.2)
    .linkDirectionalParticleSpeed(0.004)
    .linkDirectionalParticleColor(link => {
      const src = typeof link.source === 'object' ? link.source : null
      return src?.color || '#2068FF'
    })
    .onNodeClick(node => selectAgent(node))
    .onBackgroundClick(() => { selectedAgent.value = null })
    .graphData({ nodes: [...data.nodes], links: [...data.links] })

  zoomTimer = setTimeout(() => {
    if (graph) graph.zoomToFit(400, 60)
  }, 1500)
}

function selectAgent(node) {
  const connections = (props.networkData?.edges || []).filter(
    e => e.source === node.id || e.target === node.id,
  )
  selectedAgent.value = {
    ...node,
    shortName: getShortName(node.name),
    connectionCount: connections.length,
    connections: connections.slice(0, 8).map(e => {
      const otherId = e.source === node.id ? e.target : e.source
      const other = props.networkData.nodes.find(n => n.id === otherId)
      return {
        name: other?.name || `Agent ${otherId}`,
        weight: e.weight,
        type: e.type,
      }
    }),
  }
}

function destroyGraph() {
  if (zoomTimer) clearTimeout(zoomTimer)
  if (graph) {
    graph.pauseAnimation()
    graph._destructor()
    graph = null
  }
}

watch(() => props.networkData, () => {
  if (props.networkData?.nodes?.length) {
    // Destroy and recreate to handle full data changes (new round)
    destroyGraph()
    nextTick(() => renderGraph())
  }
}, { deep: true })

watch(() => props.clusterColors, () => {
  if (graph && props.networkData?.nodes?.length) {
    destroyGraph()
    nextTick(() => renderGraph())
  }
}, { deep: true })

onMounted(() => {
  if (props.networkData?.nodes?.length) {
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
})

onUnmounted(() => {
  destroyGraph()
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
})
</script>

<template>
  <div ref="containerRef" class="w-full h-full relative overflow-hidden bg-[#f8f9fa] dark:bg-[#0a0a1a]">
    <!-- Empty state -->
    <div
      v-if="!networkData?.nodes?.length"
      class="absolute inset-0 flex items-center justify-center"
    >
      <div class="text-center">
        <p class="text-sm text-[var(--color-text-muted)]">No network data available</p>
        <p class="text-xs text-[var(--color-text-muted)] mt-1">Network will appear once simulation data loads.</p>
      </div>
    </div>

    <!-- Selected agent detail panel -->
    <Transition name="slide">
      <div
        v-if="selectedAgent"
        class="absolute top-0 right-0 z-20 h-full w-72 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border-l border-black/10 dark:border-white/10 overflow-y-auto"
      >
        <div class="p-4">
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full shrink-0" :style="{ backgroundColor: selectedAgent.color }" />
              <h3 class="text-[var(--color-text)] font-semibold text-sm">{{ selectedAgent.shortName }}</h3>
            </div>
            <button
              @click="selectedAgent = null"
              class="text-black/30 dark:text-white/30 hover:text-black/60 dark:hover:text-white/60 text-lg leading-none transition-colors"
            >&times;</button>
          </div>

          <p class="text-xs text-[var(--color-text-muted)] mb-3 truncate">{{ selectedAgent.name }}</p>

          <div v-if="selectedAgent.title" class="mb-3">
            <span class="inline-block px-2 py-0.5 rounded text-[10px] bg-[rgba(32,104,255,0.1)] text-[#2068FF] font-medium">
              {{ selectedAgent.title }} @ {{ selectedAgent.company }}
            </span>
          </div>

          <div class="grid grid-cols-3 gap-2 mb-4">
            <div class="bg-black/5 dark:bg-white/5 rounded-lg px-2 py-1.5 text-center">
              <div class="text-sm font-bold text-[var(--color-text)]">{{ selectedAgent.centrality }}</div>
              <div class="text-[9px] text-[var(--color-text-muted)]">Central.</div>
            </div>
            <div class="bg-black/5 dark:bg-white/5 rounded-lg px-2 py-1.5 text-center">
              <div class="text-sm font-bold text-[var(--color-text)]">{{ selectedAgent.degree }}</div>
              <div class="text-[9px] text-[var(--color-text-muted)]">Degree</div>
            </div>
            <div class="bg-black/5 dark:bg-white/5 rounded-lg px-2 py-1.5 text-center">
              <div class="text-sm font-bold text-[var(--color-text)]">{{ selectedAgent.connectionCount }}</div>
              <div class="text-[9px] text-[var(--color-text-muted)]">Links</div>
            </div>
          </div>

          <div v-if="selectedAgent.betweenness != null" class="mb-4">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Betweenness</h4>
            <div class="flex items-center gap-2">
              <div class="flex-1 h-1.5 rounded-full bg-black/10 dark:bg-white/10">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :style="{ width: Math.min(100, selectedAgent.betweenness * 100) + '%', backgroundColor: selectedAgent.color }"
                />
              </div>
              <span class="text-xs text-[var(--color-text-muted)] tabular-nums">
                {{ typeof selectedAgent.betweenness === 'number' ? selectedAgent.betweenness.toFixed(2) : selectedAgent.betweenness }}
              </span>
            </div>
          </div>

          <div v-if="selectedAgent.connections?.length">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-2">
              Connections ({{ selectedAgent.connectionCount }})
            </h4>
            <div class="space-y-1.5">
              <div
                v-for="(conn, i) in selectedAgent.connections"
                :key="i"
                class="flex items-center justify-between bg-black/5 dark:bg-white/5 rounded-lg px-3 py-2"
              >
                <span class="text-xs text-[var(--color-text)] truncate flex-1">{{ conn.name.split(' ')[0] }}</span>
                <span class="text-[10px] text-[var(--color-text-muted)] ml-2">w={{ conn.weight }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Controls hint bottom-right -->
    <div
      v-if="networkData?.nodes?.length"
      class="absolute bottom-4 right-4 z-10 flex flex-col items-end gap-1"
    >
      <span class="text-[10px] text-[var(--color-text-muted)] opacity-60">Drag to rotate &middot; Scroll to zoom</span>
      <span class="text-xs text-[var(--color-text-muted)]">
        {{ networkData.nodes.length }} agents, {{ networkData.edges.length }} connections
      </span>
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
