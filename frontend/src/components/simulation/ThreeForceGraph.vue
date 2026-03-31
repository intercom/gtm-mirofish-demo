<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useForceGraph3D } from '../../composables/useForceGraph3D'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  isDark: { type: Boolean, default: false },
})

const emit = defineEmits(['select-node'])

const containerRef = ref(null)
const tooltip = ref(null)

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

function handleNodeClick(nodeId, nodeData) {
  if (!nodeId) {
    emit('select-node', null)
    return
  }
  const raw = props.nodes.find(n => n.uuid === nodeId)
  const connections = props.edges.filter(
    e => e.source_node_uuid === nodeId || e.target_node_uuid === nodeId,
  )
  emit('select-node', {
    id: nodeId,
    name: nodeData?.name || raw?.name || '',
    labels: raw?.labels || [],
    summary: raw?.summary || '',
    color: nodeData?.color || getNodeColor(raw?.labels),
    centrality: nodeData?.centrality || 0,
    entityType: getEntityType(raw?.labels),
    connections: connections.map(e => ({
      name: e.name || '',
      fact: e.fact || '',
      direction: e.source_node_uuid === nodeId ? 'outgoing' : 'incoming',
      target: e.source_node_uuid === nodeId
        ? props.nodes.find(n => n.uuid === e.target_node_uuid)?.name || ''
        : props.nodes.find(n => n.uuid === e.source_node_uuid)?.name || '',
    })),
  })
}

function handleNodeHover(nodeId, nodeData, screenPos) {
  if (!nodeId || !screenPos) {
    tooltip.value = null
    return
  }
  tooltip.value = {
    name: nodeData?.name || '',
    type: getEntityType(nodeData?.labels),
    color: nodeData?.color || DEFAULT_COLOR,
    x: screenPos.x,
    y: screenPos.y,
  }
}

const graph3d = useForceGraph3D({
  onNodeClick: handleNodeClick,
  onNodeHover: handleNodeHover,
})

function transformAndRender() {
  if (!props.nodes.length) return

  const centrality = computeCentrality(props.nodes, props.edges)

  const nodes = props.nodes.map(n => ({
    id: n.uuid,
    name: n.name,
    labels: n.labels,
    color: getNodeColor(n.labels),
    centrality: centrality[n.uuid] || 0,
    radius: 2 + (centrality[n.uuid] || 0) * 6,
  }))

  const nodeIds = new Set(nodes.map(n => n.id))
  const edges = props.edges
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
    .map(e => ({
      sourceId: e.source_node_uuid,
      targetId: e.target_node_uuid,
      name: e.name || '',
    }))

  graph3d.setData(nodes, edges)
}

watch(() => [props.nodes, props.edges], () => {
  if (props.nodes.length) {
    nextTick(transformAndRender)
  }
}, { deep: true })

watch(() => props.isDark, (isDark) => {
  graph3d.setDarkMode(isDark)
})

onMounted(() => {
  if (containerRef.value) {
    graph3d.init(containerRef.value)
    if (props.nodes.length) {
      nextTick(transformAndRender)
    }
    graph3d.setDarkMode(props.isDark)
  }
})

onUnmounted(() => {
  graph3d.dispose()
})
</script>

<template>
  <div class="w-full h-full relative overflow-hidden">
    <div ref="containerRef" class="w-full h-full" />

    <!-- Floating tooltip on hover -->
    <Transition name="tooltip-fade">
      <div
        v-if="tooltip"
        class="absolute z-30 pointer-events-none"
        :style="{
          left: tooltip.x + 'px',
          top: (tooltip.y - 8) + 'px',
          transform: 'translate(-50%, -100%)',
        }"
      >
        <div class="bg-black/80 backdrop-blur-sm rounded-lg px-3 py-2 shadow-lg">
          <div class="text-xs font-semibold text-white" :style="{ color: tooltip.color }">
            {{ tooltip.name }}
          </div>
          <div class="text-[10px] text-white/50">{{ tooltip.type }}</div>
        </div>
      </div>
    </Transition>

    <!-- Controls hint bottom-right -->
    <div class="absolute bottom-3 right-3 z-10">
      <span class="text-[10px] text-[var(--color-text-muted)] opacity-60">
        Drag to rotate &middot; Scroll to zoom &middot; Click node to inspect
      </span>
    </div>
  </div>
</template>

<style scoped>
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.15s ease;
}
.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
}
</style>
