<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
})

const emit = defineEmits(['cluster-change'])

const CLUSTER_COLORS = [
  '#2068FF', '#ff5600', '#AA00FF', '#009900', '#f59e0b',
  '#ef4444', '#06b6d4', '#ec4899', '#8b5cf6', '#14b8a6',
]

const STOP_WORDS = new Set([
  'the', 'and', 'for', 'with', 'from', 'that', 'this',
  'agent', 'node', 'entity', 'type', 'group',
])

const containerRef = ref(null)
const svgRef = ref(null)
let sim = null
let resizeObserver = null
let resizeTimer = null

const clusterMap = ref(new Map())
const selectedCluster = ref(null)
const dragTarget = ref(null)

// --- Community Detection (Label Propagation) ---

function detectCommunities(nodes, edges) {
  const labels = new Map()
  const adjacency = new Map()

  for (const n of nodes) {
    labels.set(n.id, n.cluster != null ? n.cluster : n.id)
    adjacency.set(n.id, [])
  }

  for (const e of edges) {
    const s = typeof e.source === 'object' ? e.source.id : e.source
    const t = typeof e.target === 'object' ? e.target.id : e.target
    const w = e.weight || 1
    if (adjacency.has(s)) adjacency.get(s).push({ id: t, weight: w })
    if (adjacency.has(t)) adjacency.get(t).push({ id: s, weight: w })
  }

  const nodeIds = [...labels.keys()]
  for (let iter = 0; iter < 20; iter++) {
    let changed = false
    const shuffled = [...nodeIds].sort(() => Math.random() - 0.5)

    for (const nid of shuffled) {
      const neighbors = adjacency.get(nid) || []
      if (!neighbors.length) continue

      const votes = new Map()
      for (const { id, weight } of neighbors) {
        const label = labels.get(id)
        votes.set(label, (votes.get(label) || 0) + weight)
      }

      let best = labels.get(nid)
      let bestCount = 0
      for (const [label, count] of votes) {
        if (count > bestCount) { bestCount = count; best = label }
      }

      if (best !== labels.get(nid)) {
        labels.set(nid, best)
        changed = true
      }
    }
    if (!changed) break
  }

  const unique = [...new Set(labels.values())]
  const remap = new Map(unique.map((v, i) => [v, i]))
  const result = new Map()
  for (const [nid, label] of labels) result.set(nid, remap.get(label))
  return result
}

// --- Auto-generated Cluster Labels ---

function generateLabel(clusterNodes) {
  const words = new Map()
  for (const n of clusterNodes) {
    for (const w of (n.name || '').split(/\s+/)) {
      const lower = w.toLowerCase()
      if (lower.length < 3 || STOP_WORDS.has(lower)) continue
      words.set(lower, (words.get(lower) || 0) + 1)
    }
  }
  const sorted = [...words.entries()].sort((a, b) => b[1] - a[1])
  if (sorted.length && sorted[0][1] > 1) {
    return sorted[0][0].charAt(0).toUpperCase() + sorted[0][0].slice(1) + '-focused'
  }
  const types = new Map()
  for (const n of clusterNodes) {
    const t = n.type || (n.labels && n.labels[0]) || 'Agent'
    types.set(t, (types.get(t) || 0) + 1)
  }
  const top = [...types.entries()].sort((a, b) => b[1] - a[1])[0]
  if (top && top[0] !== 'Agent') return top[0] + 's'
  return null
}

// --- Cluster Summary Data ---

const clusterData = computed(() => {
  if (!clusterMap.value.size) return []

  const groups = new Map()
  for (const n of props.nodes) {
    const cid = clusterMap.value.get(n.id) ?? 0
    if (!groups.has(cid)) groups.set(cid, { id: cid, nodes: [], intraEdges: 0 })
    groups.get(cid).nodes.push(n)
  }

  for (const e of props.edges) {
    const s = typeof e.source === 'object' ? e.source.id : e.source
    const t = typeof e.target === 'object' ? e.target.id : e.target
    const sc = clusterMap.value.get(s)
    const tc = clusterMap.value.get(t)
    if (sc === tc && groups.has(sc)) groups.get(sc).intraEdges++
  }

  return Array.from(groups.values()).map(g => {
    const n = g.nodes.length
    const possible = n > 1 ? (n * (n - 1)) / 2 : 1
    const cohesion = Math.min(1, g.intraEdges / possible)
    const label = generateLabel(g.nodes) || `Group ${g.id + 1}`

    const types = new Map()
    for (const node of g.nodes) {
      const t = node.type || (node.labels && node.labels[0]) || 'Agent'
      types.set(t, (types.get(t) || 0) + 1)
    }
    const topics = [...types.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3).map(([t]) => t)

    return {
      id: g.id,
      label,
      color: CLUSTER_COLORS[g.id % CLUSTER_COLORS.length],
      size: n,
      intraEdges: g.intraEdges,
      cohesion,
      topics,
      nodeNames: g.nodes.map(nd => nd.name),
    }
  }).sort((a, b) => b.size - a.size)
})

// --- Padded Convex Hull ---

function paddedHull(points, padding = 30) {
  if (!points.length) return null

  // For small point sets, expand each point into a circle of samples
  // then compute the hull — creates natural capsule/circle shapes
  if (points.length < 3) {
    const expanded = []
    for (const [x, y] of points) {
      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * Math.PI * 2
        expanded.push([x + padding * Math.cos(a), y + padding * Math.sin(a)])
      }
    }
    return d3.polygonHull(expanded)
  }

  const hull = d3.polygonHull(points)
  if (!hull) return null
  const cx = d3.mean(hull, p => p[0])
  const cy = d3.mean(hull, p => p[1])
  return hull.map(([x, y]) => {
    const dx = x - cx, dy = y - cy
    const dist = Math.sqrt(dx * dx + dy * dy) || 1
    return [cx + dx * (dist + padding) / dist, cy + dy * (dist + padding) / dist]
  })
}

// --- Custom Cluster Force ---

function forceCluster(strength = 0.12) {
  let nodes
  function force(alpha) {
    const centroids = new Map()
    for (const n of nodes) {
      if (!centroids.has(n.clusterId)) centroids.set(n.clusterId, { x: 0, y: 0, count: 0 })
      const c = centroids.get(n.clusterId)
      c.x += n.x
      c.y += n.y
      c.count++
    }
    for (const c of centroids.values()) {
      c.x /= c.count
      c.y /= c.count
    }
    for (const n of nodes) {
      const c = centroids.get(n.clusterId)
      if (!c) continue
      n.vx += (c.x - n.x) * alpha * strength
      n.vy += (c.y - n.y) * alpha * strength
    }
  }
  force.initialize = (n) => { nodes = n }
  return force
}

// --- Render ---

function clearGraph() {
  if (svgRef.value) d3.select(svgRef.value).selectAll('*').remove()
  if (sim) { sim.stop(); sim = null }
}

function renderGraph() {
  clearGraph()
  const container = containerRef.value
  if (!container || !props.nodes.length) return
  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  if (!clusterMap.value.size) {
    clusterMap.value = detectCommunities(props.nodes, props.edges)
  }

  const dark = document.documentElement.classList.contains('dark')

  const nodeData = props.nodes.map(n => ({
    id: n.id,
    name: n.name,
    type: n.type || (n.labels && n.labels[0]) || 'Agent',
    clusterId: clusterMap.value.get(n.id) ?? 0,
    radius: 7 + (n.weight || n.centrality || 0.3) * 10,
  }))

  const edgeData = props.edges
    .filter(e => {
      const s = typeof e.source === 'object' ? e.source.id : e.source
      const t = typeof e.target === 'object' ? e.target.id : e.target
      return nodeData.some(n => n.id === s) && nodeData.some(n => n.id === t)
    })
    .map(e => ({
      source: typeof e.source === 'object' ? e.source.id : e.source,
      target: typeof e.target === 'object' ? e.target.id : e.target,
      weight: e.weight || 1,
    }))

  const svg = d3.select(svgRef.value).attr('width', width).attr('height', height)

  const zoom = d3.zoom()
    .scaleExtent([0.3, 4])
    .on('zoom', (event) => g.attr('transform', event.transform))
  svg.call(zoom)

  const g = svg.append('g')
  const hullGroup = g.append('g')
  const edgeGroup = g.append('g')
  const nodeGroup = g.append('g')
  const labelGroup = g.append('g')

  sim = d3.forceSimulation(nodeData)
    .force('link', d3.forceLink(edgeData).id(d => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 5))
    .force('cluster', forceCluster(0.15))

  // Edges — thicker for intra-cluster, thinner for inter-cluster
  const edgeSel = edgeGroup.selectAll('line').data(edgeData).join('line')
    .attr('stroke', dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)')

  // Nodes
  const nodeSel = nodeGroup.selectAll('g').data(nodeData).join('g')
    .style('cursor', 'grab')

  nodeSel.append('circle')
    .attr('class', 'glow')
    .attr('r', d => d.radius + 3)
    .attr('fill', d => CLUSTER_COLORS[d.clusterId % CLUSTER_COLORS.length])
    .attr('opacity', 0.2)

  nodeSel.append('circle')
    .attr('class', 'body')
    .attr('r', d => d.radius)
    .attr('fill', d => CLUSTER_COLORS[d.clusterId % CLUSTER_COLORS.length])
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .attr('fill-opacity', 0.85)

  nodeSel.append('text')
    .text(d => d.name)
    .attr('dy', d => d.radius + 13)
    .attr('text-anchor', 'middle')
    .attr('fill', dark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)')
    .attr('font-size', '9px')
    .style('pointer-events', 'none')

  // Tooltip
  const tooltip = d3.select(container).append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')

  nodeSel.on('mouseenter', (event, d) => {
    const cluster = clusterData.value.find(c => c.id === d.clusterId)
    const color = CLUSTER_COLORS[d.clusterId % CLUSTER_COLORS.length]
    tooltip.html(`
      <div style="font-weight:600;color:var(--color-text,#050505)">${d.name}</div>
      <div style="color:${color};font-size:11px;margin-top:2px">
        ${cluster?.label || 'Cluster ' + (d.clusterId + 1)} &middot; ${cluster?.size || '?'} members
      </div>
      <div style="color:var(--color-text-muted,#888);font-size:11px;margin-top:2px">${d.type}</div>
    `).style('opacity', 1)
  })
  .on('mousemove', (event) => {
    const rect = container.getBoundingClientRect()
    tooltip
      .style('left', `${event.clientX - rect.left + 14}px`)
      .style('top', `${event.clientY - rect.top - 30}px`)
  })
  .on('mouseleave', () => tooltip.style('opacity', 0))

  // Entry animation
  nodeSel.style('opacity', 0).transition().delay((_, i) => i * 25).duration(300).style('opacity', 1)
  edgeSel.style('opacity', 0).transition().delay(nodeData.length * 25).duration(400).style('opacity', 1)

  // Drag handlers (closured to access selections)
  function onDragStart(event, d) {
    if (!event.active) sim.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }

  function onDrag(event, d) {
    d.fx = event.x
    d.fy = event.y

    const centroids = new Map()
    for (const n of sim.nodes()) {
      if (n.id === d.id) continue
      if (!centroids.has(n.clusterId)) centroids.set(n.clusterId, { x: 0, y: 0, count: 0 })
      const c = centroids.get(n.clusterId)
      c.x += n.x
      c.y += n.y
      c.count++
    }

    let target = null
    let minDist = 120
    for (const [cid, c] of centroids) {
      if (cid === d.clusterId) continue
      const dist = Math.sqrt((event.x - c.x / c.count) ** 2 + (event.y - c.y / c.count) ** 2)
      if (dist < minDist) { minDist = dist; target = cid }
    }
    dragTarget.value = target
  }

  function onDragEnd(event, d) {
    if (!event.active) sim.alphaTarget(0)
    d.fx = null
    d.fy = null

    if (dragTarget.value != null && dragTarget.value !== d.clusterId) {
      const from = d.clusterId
      d.clusterId = dragTarget.value
      clusterMap.value.set(d.id, dragTarget.value)
      clusterMap.value = new Map(clusterMap.value)

      // Update node colors
      const color = CLUSTER_COLORS[d.clusterId % CLUSTER_COLORS.length]
      nodeSel.filter(n => n.id === d.id)
        .select('.glow').attr('fill', color)
      nodeSel.filter(n => n.id === d.id)
        .select('.body').attr('fill', color)

      // Update edge thickness
      edgeSel
        .attr('stroke-width', e => e.source.clusterId === e.target.clusterId ? 2 : 0.7)
        .attr('stroke-opacity', e => e.source.clusterId === e.target.clusterId ? 0.5 : 0.2)

      // Briefly restart simulation to settle into new cluster
      sim.alphaTarget(0.2).restart()
      setTimeout(() => sim.alphaTarget(0), 1500)

      emit('cluster-change', { nodeId: d.id, from, to: dragTarget.value })
    }
    dragTarget.value = null
  }

  nodeSel.call(d3.drag()
    .on('start', onDragStart)
    .on('drag', onDrag)
    .on('end', onDragEnd)
  )

  // Tick handler
  sim.on('tick', () => {
    edgeSel
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      .attr('stroke-width', d => d.source.clusterId === d.target.clusterId ? 2 : 0.7)
      .attr('stroke-opacity', d => d.source.clusterId === d.target.clusterId ? 0.5 : 0.2)

    nodeSel.attr('transform', d => `translate(${d.x},${d.y})`)
    updateHulls(hullGroup, labelGroup, nodeData, dark)
  })

  svg.on('click', () => { selectedCluster.value = null })
}

function updateHulls(hullGroup, labelGroup, nodeData, dark) {
  const groups = new Map()
  for (const n of nodeData) {
    if (!groups.has(n.clusterId)) groups.set(n.clusterId, [])
    groups.get(n.clusterId).push([n.x, n.y])
  }

  const hullData = []
  const lblData = []
  for (const [cid, pts] of groups) {
    const hull = paddedHull(pts, 30)
    if (!hull) continue
    const color = CLUSTER_COLORS[cid % CLUSTER_COLORS.length]
    hullData.push({ id: cid, hull, color })
    const cx = d3.mean(pts, p => p[0])
    const minY = Math.min(...pts.map(p => p[1]))
    const cluster = clusterData.value.find(c => c.id === cid)
    lblData.push({ id: cid, x: cx, y: minY - 38, color, text: cluster?.label || `Group ${cid + 1}` })
  }

  const line = d3.line().curve(d3.curveCatmullRomClosed)

  hullGroup.selectAll('path').data(hullData, d => d.id).join('path')
    .attr('d', d => line(d.hull))
    .attr('fill', d => d.color)
    .attr('fill-opacity', d => dragTarget.value === d.id ? 0.2 : 0.07)
    .attr('stroke', d => d.color)
    .attr('stroke-width', d => dragTarget.value === d.id ? 2 : 1)
    .attr('stroke-opacity', 0.25)
    .attr('stroke-dasharray', '5,3')

  labelGroup.selectAll('text').data(lblData, d => d.id).join('text')
    .attr('x', d => d.x)
    .attr('y', d => d.y)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', d => d.color)
    .attr('opacity', 0.65)
    .text(d => d.text)
}

// --- Lifecycle ---

function initClusters() {
  if (!props.nodes.length) return
  const hasAssignments = props.nodes.some(n => n.cluster != null)
  if (hasAssignments) {
    const map = new Map()
    props.nodes.forEach(n => map.set(n.id, n.cluster))
    clusterMap.value = map
  } else {
    clusterMap.value = detectCommunities(props.nodes, props.edges)
  }
  nextTick(renderGraph)
}

watch([() => props.nodes.length, () => props.edges.length], initClusters)

onMounted(() => {
  initClusters()
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderGraph, 200)
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
  clearGraph()
})
</script>

<template>
  <div class="space-y-4">
    <!-- Main Visualization -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3 border-b border-[var(--color-border)]">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Cluster Analysis</h3>
        <div v-if="clusterData.length" class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
          <span v-for="cluster in clusterData.slice(0, 6)" :key="cluster.id" class="flex items-center gap-1.5">
            <span class="inline-block w-2.5 h-2.5 rounded-full" :style="{ background: cluster.color }" />
            {{ cluster.label }}
          </span>
        </div>
      </div>

      <div v-if="nodes.length" ref="containerRef" class="relative" style="height: 480px">
        <svg ref="svgRef" class="w-full h-full" />
      </div>

      <div v-else class="flex items-center justify-center h-[320px] text-[var(--color-text-muted)] text-sm">
        <span>Cluster data will appear after simulation completes</span>
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="clusterData.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="cluster in clusterData"
        :key="cluster.id"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 cursor-pointer transition-all hover:shadow-md"
        :class="selectedCluster === cluster.id ? 'ring-2' : ''"
        :style="selectedCluster === cluster.id ? { '--tw-ring-color': cluster.color } : {}"
        @click.stop="selectedCluster = selectedCluster === cluster.id ? null : cluster.id"
      >
        <div class="flex items-center gap-2 mb-2">
          <span class="w-3 h-3 rounded-full shrink-0" :style="{ background: cluster.color }" />
          <span class="text-sm font-semibold text-[var(--color-text)] truncate">{{ cluster.label }}</span>
          <span class="ml-auto text-xs text-[var(--color-text-muted)]">
            {{ cluster.size }} {{ cluster.size === 1 ? 'agent' : 'agents' }}
          </span>
        </div>

        <div class="mb-2">
          <div class="flex items-center justify-between text-[11px] text-[var(--color-text-muted)] mb-1">
            <span>Cohesion</span>
            <span>{{ (cluster.cohesion * 100).toFixed(0) }}%</span>
          </div>
          <div class="h-1.5 bg-[var(--color-tint)] rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :style="{ width: `${cluster.cohesion * 100}%`, background: cluster.color }"
            />
          </div>
        </div>

        <div v-if="cluster.topics.length" class="flex flex-wrap gap-1">
          <span
            v-for="topic in cluster.topics"
            :key="topic"
            class="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-tint)] text-[var(--color-text-secondary)]"
          >
            {{ topic }}
          </span>
        </div>

        <div v-if="selectedCluster === cluster.id" class="mt-3 pt-3 border-t border-[var(--color-border)]">
          <div class="text-[11px] text-[var(--color-text-muted)] mb-1">Members</div>
          <div class="flex flex-wrap gap-1">
            <span
              v-for="name in cluster.nodeNames"
              :key="name"
              class="text-[11px] px-2 py-0.5 rounded-full border border-[var(--color-border)] text-[var(--color-text-secondary)]"
            >
              {{ name }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="clusterData.length > 1" class="text-center text-[11px] text-[var(--color-text-muted)]">
      Drag nodes between clusters to reassign · Scroll to zoom · Drag background to pan
    </div>
  </div>
</template>
