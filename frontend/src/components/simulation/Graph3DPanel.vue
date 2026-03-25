<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import ForceGraph3D from '3d-force-graph'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  isDark: { type: Boolean, default: false },
})

const emit = defineEmits(['select-node'])

const containerRef = ref(null)
let graph = null
let resizeObserver = null
let zoomTimer = null

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

function buildGraphData() {
  if (!props.nodes.length) return { nodes: [], links: [] }

  const centrality = computeCentrality(props.nodes, props.edges)
  const nodeSet = new Set(props.nodes.map(n => n.uuid))

  const nodes = props.nodes.map(n => ({
    id: n.uuid,
    name: n.name,
    labels: n.labels,
    summary: n.summary || '',
    attributes: n.attributes || {},
    color: getNodeColor(n.labels),
    val: 1 + (centrality[n.uuid] || 0) * 8,
    centrality: centrality[n.uuid] || 0,
  }))

  const links = props.edges
    .filter(e => nodeSet.has(e.source_node_uuid) && nodeSet.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
    }))

  return { nodes, links }
}

function scheduleZoomToFit() {
  clearTimeout(zoomTimer)
  zoomTimer = setTimeout(() => {
    if (graph) graph.zoomToFit(600, 60)
  }, 1500)
}

function initGraph() {
  const el = containerRef.value
  if (!el) return

  if (graph) {
    graph._destructor()
    graph = null
  }

  const width = el.clientWidth
  const height = el.clientHeight
  if (!width || !height) return

  graph = new ForceGraph3D(el, { controlType: 'orbit' })
    .width(width)
    .height(height)
    .backgroundColor(props.isDark ? '#0a0a1a00' : '#f8f9fa00')
    .showNavInfo(false)
    .nodeId('id')
    .nodeLabel(n => `<div style="background:rgba(0,0,0,0.85);color:#fff;padding:8px 12px;border-radius:8px;font-size:12px;max-width:220px;line-height:1.4;pointer-events:none">
      <b>${n.name}</b>${n.summary ? `<br><span style="opacity:0.65;font-size:11px">${n.summary}</span>` : ''}
    </div>`)
    .nodeColor(n => n.color)
    .nodeOpacity(0.92)
    .nodeResolution(16)
    .linkLabel(l => l.name)
    .linkColor(() => props.isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)')
    .linkWidth(0.4)
    .linkOpacity(0.6)
    .linkDirectionalArrowLength(3.5)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalArrowColor(() => props.isDark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')
    .linkDirectionalParticles(2)
    .linkDirectionalParticleWidth(0.8)
    .linkDirectionalParticleSpeed(0.004)
    .linkDirectionalParticleColor(() => props.isDark ? 'rgba(32,104,255,0.7)' : 'rgba(32,104,255,0.5)')
    .warmupTicks(40)
    .cooldownTime(5000)
    .onNodeClick(node => {
      emit('select-node', node)
      const distance = 120
      const distRatio = 1 + distance / Math.hypot(node.x || 1, node.y || 1, node.z || 1)
      graph.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node,
        800,
      )
    })
    .onBackgroundClick(() => {
      emit('select-node', null)
    })

  graph.d3Force('charge').strength(-150)
  graph.d3Force('link').distance(70)

  const data = buildGraphData()
  graph.graphData(data)
  scheduleZoomToFit()
}

watch(() => [props.nodes.length, props.edges.length], () => {
  if (!props.nodes.length) return
  if (!graph) {
    nextTick(() => initGraph())
    return
  }
  const data = buildGraphData()
  graph.graphData(data)
  scheduleZoomToFit()
})

watch(() => props.isDark, (dark) => {
  if (!graph) return
  graph.backgroundColor(dark ? '#0a0a1a00' : '#f8f9fa00')
  graph.linkColor(() => dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)')
  graph.linkDirectionalArrowColor(() => dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')
  graph.linkDirectionalParticleColor(() => dark ? 'rgba(32,104,255,0.7)' : 'rgba(32,104,255,0.5)')
})

onMounted(() => {
  nextTick(() => {
    if (props.nodes.length) initGraph()
  })

  resizeObserver = new ResizeObserver(() => {
    if (graph && containerRef.value) {
      graph.width(containerRef.value.clientWidth)
      graph.height(containerRef.value.clientHeight)
    }
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  clearTimeout(zoomTimer)
  if (graph) {
    graph._destructor()
    graph = null
  }
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<template>
  <div ref="containerRef" class="w-full h-full graph-3d-container" />
</template>

<style scoped>
.graph-3d-container {
  position: relative;
}
.graph-3d-container :deep(canvas) {
  outline: none;
}
</style>
