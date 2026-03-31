<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as d3 from 'd3'
import client from '../../api/client.js'

const svgRef = ref(null)
const containerRef = ref(null)
const timePoint = ref(0)
const playing = ref(false)
const selectedNode = ref(null)
const loading = ref(true)
const error = ref('')

const orgData = ref(null)
const flows = ref([])
const bottlenecks = ref([])
const totalTimePoints = ref(11)

let svg = null
let zoomGroup = null
let resizeObserver = null
let animationFrame = null
let playInterval = null
let particles = []

const FLOW_COLORS = {
  data: '#2068FF',
  decision: '#ef4444',
  feedback: '#009900',
}
const FLOW_LABELS = {
  data: 'Data',
  decision: 'Decision',
  feedback: 'Feedback',
}

const nodeFlows = computed(() => {
  if (!selectedNode.value || !flows.value.length) return []
  const id = selectedNode.value
  return flows.value.filter((f) => f.source === id || f.target === id)
})

async function fetchData() {
  try {
    const res = await client.get('/org-chart', { params: { time: timePoint.value } })
    const d = res.data.data || res.data
    orgData.value = d.tree
    flows.value = d.flows
    bottlenecks.value = d.bottlenecks
    totalTimePoints.value = d.time_points
    error.value = ''
  } catch (e) {
    error.value = e.message || 'Failed to load org chart data'
    // Fallback mock data so visualization still works
    orgData.value = _fallbackTree()
    flows.value = _fallbackFlows()
    bottlenecks.value = []
  } finally {
    loading.value = false
  }
}

function _fallbackTree() {
  return {
    id: 'ceo-1', name: 'CEO', title: 'CEO',
    children: [
      { id: 'vp-sales', name: 'VP Sales', title: 'VP Sales', children: [
        { id: 's1', name: 'AE 1', title: 'AE' },
        { id: 's2', name: 'AE 2', title: 'AE' },
      ]},
      { id: 'vp-mktg', name: 'VP Marketing', title: 'VP Marketing', children: [
        { id: 'm1', name: 'Demand Gen', title: 'Demand Gen' },
        { id: 'm2', name: 'Content', title: 'Content' },
      ]},
      { id: 'vp-cs', name: 'VP CS', title: 'VP CS', children: [
        { id: 'c1', name: 'CSM 1', title: 'CSM' },
        { id: 'c2', name: 'CSM 2', title: 'CSM' },
      ]},
      { id: 'vp-prod', name: 'VP Product', title: 'VP Product', children: [
        { id: 'p1', name: 'PM 1', title: 'PM' },
        { id: 'p2', name: 'UX Lead', title: 'UX' },
      ]},
    ],
  }
}

function _fallbackFlows() {
  return [
    { source: 's1', target: 'vp-sales', type: 'data', label: 'Pipeline', direction: 'up', volume: 5 },
    { source: 'vp-sales', target: 'ceo-1', type: 'data', label: 'Revenue', direction: 'up', volume: 8 },
    { source: 'ceo-1', target: 'vp-mktg', type: 'decision', label: 'Budget', direction: 'down', volume: 4 },
    { source: 'vp-cs', target: 'vp-prod', type: 'feedback', label: 'Requests', direction: 'horizontal', volume: 6 },
  ]
}

function buildViz() {
  if (!svgRef.value || !orgData.value) return

  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight || 600

  // Clear previous
  d3.select(svgRef.value).selectAll('*').remove()
  particles = []

  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  // Defs for arrow markers and glow
  const defs = svg.append('defs')

  Object.entries(FLOW_COLORS).forEach(([type, color]) => {
    defs.append('marker')
      .attr('id', `arrow-${type}`)
      .attr('viewBox', '0 0 10 6')
      .attr('refX', 10)
      .attr('refY', 3)
      .attr('markerWidth', 8)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,0 L10,3 L0,6 Z')
      .attr('fill', color)
      .attr('opacity', 0.7)
  })

  // Drop shadow for nodes
  const filter = defs.append('filter').attr('id', 'node-shadow').attr('x', '-20%').attr('y', '-20%').attr('width', '140%').attr('height', '140%')
  filter.append('feDropShadow').attr('dx', 0).attr('dy', 2).attr('stdDeviation', 3).attr('flood-color', 'rgba(0,0,0,0.12)')

  // Glow filter for bottleneck
  const glow = defs.append('filter').attr('id', 'bottleneck-glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%')
  glow.append('feGaussianBlur').attr('stdDeviation', 4).attr('result', 'blur')
  glow.append('feFlood').attr('flood-color', '#ef4444').attr('flood-opacity', 0.4).attr('result', 'color')
  glow.append('feComposite').attr('in', 'color').attr('in2', 'blur').attr('operator', 'in').attr('result', 'glow')
  const merge = glow.append('feMerge')
  merge.append('feMergeNode').attr('in', 'glow')
  merge.append('feMergeNode').attr('in', 'SourceGraphic')

  zoomGroup = svg.append('g')

  svg.call(
    d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        zoomGroup.attr('transform', event.transform)
      })
  )

  // Build tree layout
  const root = d3.hierarchy(orgData.value)
  const treeLayout = d3.tree()
    .size([width - 200, height - 160])
    .separation((a, b) => (a.parent === b.parent ? 1.2 : 1.8))

  treeLayout(root)

  // Center the tree
  const offsetX = 100
  const offsetY = 60

  // Build a lookup of node positions by id
  const nodeMap = {}
  root.descendants().forEach((d) => {
    nodeMap[d.data.id] = { x: d.x + offsetX, y: d.y + offsetY, data: d.data, depth: d.depth }
  })

  // Draw flow paths (behind nodes)
  const flowGroup = zoomGroup.append('g').attr('class', 'flows')
  const pathData = flows.value.filter((f) => nodeMap[f.source] && nodeMap[f.target])

  pathData.forEach((f) => {
    const src = nodeMap[f.source]
    const tgt = nodeMap[f.target]
    const pathD = _flowPath(src, tgt, f.direction)

    flowGroup.append('path')
      .attr('d', pathD)
      .attr('fill', 'none')
      .attr('stroke', FLOW_COLORS[f.type] || '#888')
      .attr('stroke-width', Math.max(1, Math.min(f.volume || 1, 6)))
      .attr('stroke-opacity', 0.25)
      .attr('marker-end', `url(#arrow-${f.type})`)
      .attr('data-source', f.source)
      .attr('data-target', f.target)
  })

  // Draw tree links
  const linkGroup = zoomGroup.append('g').attr('class', 'links')
  root.links().forEach((link) => {
    linkGroup.append('path')
      .attr('d', d3.linkVertical()
        .x((d) => d.x + offsetX)
        .y((d) => d.y + offsetY)({ source: link.source, target: link.target }))
      .attr('fill', 'none')
      .attr('stroke', 'var(--color-border-strong, #ccc)')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '4,3')
  })

  // Draw nodes
  const nodeGroup = zoomGroup.append('g').attr('class', 'nodes')
  const descendants = root.descendants()

  const nodeWidth = 130
  const nodeHeight = 52

  descendants.forEach((d) => {
    const isBottleneck = bottlenecks.value.includes(d.data.id)
    const isSelected = selectedNode.value === d.data.id
    const nx = d.x + offsetX
    const ny = d.y + offsetY

    const g = nodeGroup.append('g')
      .attr('transform', `translate(${nx},${ny})`)
      .attr('cursor', 'pointer')
      .on('click', () => {
        selectedNode.value = selectedNode.value === d.data.id ? null : d.data.id
      })

    // Node background
    g.append('rect')
      .attr('x', -nodeWidth / 2)
      .attr('y', -nodeHeight / 2)
      .attr('width', nodeWidth)
      .attr('height', nodeHeight)
      .attr('rx', 10)
      .attr('fill', d.depth === 0 ? '#050505' : 'var(--color-surface, #fff)')
      .attr('stroke', isSelected ? '#2068FF' : isBottleneck ? '#ef4444' : 'var(--color-border, #ddd)')
      .attr('stroke-width', isSelected ? 2.5 : isBottleneck ? 2 : 1)
      .attr('filter', isBottleneck ? 'url(#bottleneck-glow)' : 'url(#node-shadow)')

    // Name
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('y', -4)
      .attr('fill', d.depth === 0 ? '#fff' : 'var(--color-text, #1a1a1a)')
      .attr('font-size', '12px')
      .attr('font-weight', 600)
      .text(d.data.name)

    // Title
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('y', 14)
      .attr('fill', d.depth === 0 ? 'rgba(255,255,255,0.7)' : 'var(--color-text-secondary, #666)')
      .attr('font-size', '10px')
      .text(d.data.title)

    // Bottleneck indicator
    if (isBottleneck) {
      g.append('circle')
        .attr('cx', nodeWidth / 2 - 6)
        .attr('cy', -nodeHeight / 2 + 6)
        .attr('r', 7)
        .attr('fill', '#ef4444')
      g.append('text')
        .attr('x', nodeWidth / 2 - 6)
        .attr('y', -nodeHeight / 2 + 10)
        .attr('text-anchor', 'middle')
        .attr('fill', '#fff')
        .attr('font-size', '10px')
        .attr('font-weight', 700)
        .text('!')
    }
  })

  // Create particles for animation
  const particleGroup = zoomGroup.append('g').attr('class', 'particles')
  particles = pathData.map((f) => {
    const src = nodeMap[f.source]
    const tgt = nodeMap[f.target]
    const pathD = _flowPath(src, tgt, f.direction)
    const tempPath = document.createElementNS('http://www.w3.org/2000/svg', 'path')
    tempPath.setAttribute('d', pathD)
    const totalLength = tempPath.getTotalLength()
    const count = Math.min(Math.max(1, Math.floor((f.volume || 1) / 2)), 4)
    const items = []
    for (let i = 0; i < count; i++) {
      const circle = particleGroup.append('circle')
        .attr('r', 3)
        .attr('fill', FLOW_COLORS[f.type] || '#888')
        .attr('opacity', 0.85)
      items.push({
        el: circle,
        path: tempPath,
        totalLength,
        offset: i / count,
        speed: 0.003 + Math.random() * 0.002,
        progress: i / count,
      })
    }
    return items
  }).flat()

  startAnimation()
}

function _flowPath(src, tgt, direction) {
  const sx = src.x
  const sy = src.y
  const tx = tgt.x
  const ty = tgt.y

  if (direction === 'horizontal') {
    const midX = (sx + tx) / 2
    const cpOffset = Math.abs(ty - sy) * 0.5 + 30
    return `M${sx},${sy} C${midX},${sy - cpOffset} ${midX},${ty - cpOffset} ${tx},${ty}`
  }
  // Vertical (up/down) — curved link
  const midY = (sy + ty) / 2
  return `M${sx},${sy} C${sx},${midY} ${tx},${midY} ${tx},${ty}`
}

function startAnimation() {
  if (animationFrame) cancelAnimationFrame(animationFrame)

  function tick() {
    particles.forEach((p) => {
      p.progress += p.speed
      if (p.progress > 1) p.progress -= 1
      try {
        const pt = p.path.getPointAtLength(p.progress * p.totalLength)
        p.el.attr('cx', pt.x).attr('cy', pt.y)
      } catch {
        // path may be invalid during rebuild
      }
    })
    animationFrame = requestAnimationFrame(tick)
  }
  animationFrame = requestAnimationFrame(tick)
}

function togglePlay() {
  playing.value = !playing.value
  if (playing.value) {
    playInterval = setInterval(() => {
      timePoint.value = (timePoint.value + 1) % totalTimePoints.value
    }, 2000)
  } else {
    clearInterval(playInterval)
    playInterval = null
  }
}

watch(timePoint, async () => {
  await fetchData()
  buildViz()
})

onMounted(async () => {
  await fetchData()
  buildViz()

  resizeObserver = new ResizeObserver(() => {
    buildViz()
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  if (animationFrame) cancelAnimationFrame(animationFrame)
  if (playInterval) clearInterval(playInterval)
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<template>
  <div class="org-info-flow">
    <!-- Header -->
    <div class="oif-header">
      <h3 class="oif-title">Organization Information Flow</h3>
      <div class="oif-legend">
        <span v-for="(color, type) in FLOW_COLORS" :key="type" class="oif-legend-item">
          <span class="oif-legend-dot" :style="{ background: color }"></span>
          {{ FLOW_LABELS[type] }}
        </span>
        <span class="oif-legend-item">
          <span class="oif-legend-dot oif-legend-bottleneck"></span>
          Bottleneck
        </span>
      </div>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="oif-loading">
      <div class="oif-spinner"></div>
      Loading org chart...
    </div>
    <div v-else-if="error && !orgData" class="oif-error">{{ error }}</div>

    <!-- Visualization -->
    <div v-show="!loading" ref="containerRef" class="oif-canvas">
      <svg ref="svgRef"></svg>
    </div>

    <!-- Timeline Controls -->
    <div class="oif-controls">
      <button class="oif-play-btn" @click="togglePlay" :title="playing ? 'Pause' : 'Play'">
        <svg v-if="!playing" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4 2l10 6-10 6V2z" />
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <rect x="3" y="2" width="4" height="12" /><rect x="9" y="2" width="4" height="12" />
        </svg>
      </button>
      <input
        type="range"
        :min="0"
        :max="totalTimePoints - 1"
        v-model.number="timePoint"
        class="oif-slider"
      />
      <span class="oif-time-label">T{{ timePoint }}</span>
    </div>

    <!-- Node detail panel -->
    <transition name="oif-slide">
      <div v-if="selectedNode" class="oif-detail">
        <div class="oif-detail-header">
          <span class="oif-detail-title">Information at this node</span>
          <button class="oif-close" @click="selectedNode = null">&times;</button>
        </div>
        <div v-if="nodeFlows.length === 0" class="oif-detail-empty">No active flows at T{{ timePoint }}</div>
        <ul v-else class="oif-flow-list">
          <li v-for="(f, i) in nodeFlows" :key="i" class="oif-flow-item">
            <span class="oif-flow-dot" :style="{ background: FLOW_COLORS[f.type] }"></span>
            <span class="oif-flow-label">{{ f.label }}</span>
            <span class="oif-flow-dir">{{ f.direction === 'up' ? '↑' : f.direction === 'down' ? '↓' : '↔' }}</span>
            <span class="oif-flow-vol">vol {{ f.volume }}</span>
          </li>
        </ul>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.org-info-flow {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 500px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, rgba(0,0,0,0.1));
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
}

.oif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border, rgba(0,0,0,0.1));
  flex-shrink: 0;
}
.oif-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text, #1a1a1a);
  margin: 0;
}
.oif-legend {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: var(--color-text-secondary, #555);
}
.oif-legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.oif-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.oif-legend-bottleneck {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.5);
}

.oif-loading, .oif-error {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 10px;
  color: var(--color-text-secondary, #666);
  font-size: 14px;
}
.oif-error { color: var(--color-error, #ef4444); }
.oif-spinner {
  width: 20px; height: 20px;
  border: 2px solid var(--color-border, #ddd);
  border-top-color: var(--color-primary, #2068FF);
  border-radius: 50%;
  animation: oif-spin 0.7s linear infinite;
}
@keyframes oif-spin { to { transform: rotate(360deg); } }

.oif-canvas {
  flex: 1;
  min-height: 0;
}
.oif-canvas svg {
  display: block;
  width: 100%;
  height: 100%;
}

/* Timeline controls */
.oif-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  border-top: 1px solid var(--color-border, rgba(0,0,0,0.1));
  flex-shrink: 0;
}
.oif-play-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 1px solid var(--color-border, #ddd);
  background: var(--color-surface, #fff);
  color: var(--color-text, #1a1a1a);
  cursor: pointer;
  transition: background 0.15s;
}
.oif-play-btn:hover {
  background: var(--color-primary-light, rgba(32,104,255,0.08));
}
.oif-slider {
  flex: 1;
  accent-color: var(--color-primary, #2068FF);
}
.oif-time-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary, #555);
  min-width: 28px;
}

/* Node detail panel */
.oif-detail {
  position: absolute;
  right: 12px;
  top: 60px;
  width: 260px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, rgba(0,0,0,0.1));
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  z-index: 10;
  overflow: hidden;
}
.oif-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border, rgba(0,0,0,0.1));
}
.oif-detail-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text, #1a1a1a);
}
.oif-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--color-text-muted, #888);
  line-height: 1;
}
.oif-detail-empty {
  padding: 16px 14px;
  font-size: 13px;
  color: var(--color-text-muted, #888);
}
.oif-flow-list {
  list-style: none;
  margin: 0;
  padding: 6px 0;
}
.oif-flow-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  font-size: 12px;
  color: var(--color-text, #1a1a1a);
}
.oif-flow-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.oif-flow-label { flex: 1; }
.oif-flow-dir {
  font-size: 14px;
  color: var(--color-text-muted, #888);
}
.oif-flow-vol {
  font-size: 11px;
  color: var(--color-text-muted, #888);
  background: var(--color-tint, rgba(0,0,0,0.05));
  padding: 1px 6px;
  border-radius: 4px;
}

/* Slide transition */
.oif-slide-enter-active, .oif-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.oif-slide-enter-from, .oif-slide-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
