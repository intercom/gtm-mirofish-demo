<script setup>
import { ref, computed, watch, onMounted, onUnmounted, inject, nextTick } from 'vue'
import * as d3 from 'd3'
import client from '../../api/client'

const props = defineProps({
  taskId: { type: String, required: true },
})

const GROUP_COLORS = {
  support: '#ff5600',
  cx: '#2068FF',
  ops: '#009900',
  it: '#AA00FF',
  finance: '#FFB800',
}

const svgRef = ref(null)
const containerRef = ref(null)
const loading = ref(true)
const error = ref('')

// Data
const nodes = ref([])
const snapshots = ref([])
const edgeHistory = ref({})

// Animation state
const currentBucket = ref(0)
const playing = ref(false)
const speed = ref(1)
let animTimer = null

// Side panel state
const selectedEdge = ref(null)

// D3 refs
let simulation = null
let svg = null
let zoomGroup = null
let resizeObserver = null

const totalBuckets = computed(() => snapshots.value.length)
const currentSnapshot = computed(() => snapshots.value[currentBucket.value] || null)
const currentRound = computed(() => currentSnapshot.value?.round || 0)

const selectedEdgeHistory = computed(() => {
  if (!selectedEdge.value) return []
  const key = `${selectedEdge.value.source}-${selectedEdge.value.target}`
  const altKey = `${selectedEdge.value.target}-${selectedEdge.value.source}`
  return edgeHistory.value[key] || edgeHistory.value[altKey] || []
})

const selectedSourceName = computed(() => {
  if (!selectedEdge.value) return ''
  return nodes.value.find(n => n.id === selectedEdge.value.source)?.name || ''
})

const selectedTargetName = computed(() => {
  if (!selectedEdge.value) return ''
  return nodes.value.find(n => n.id === selectedEdge.value.target)?.name || ''
})

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await client.get(`/simulation/${props.taskId}/relationships`)
    const d = data.data || data
    nodes.value = d.nodes
    snapshots.value = d.snapshots
    edgeHistory.value = d.edge_history
    currentBucket.value = 0
    await nextTick()
    renderGraph()
  } catch (e) {
    error.value = e.message || 'Failed to load relationship data'
  } finally {
    loading.value = false
  }
}

function edgeColor(affinity) {
  if (affinity > 0.1) return d3.interpolateRgb('#888888', '#009900')(Math.min(1, affinity))
  if (affinity < -0.1) return d3.interpolateRgb('#888888', '#dc2626')(Math.min(1, Math.abs(affinity)))
  return '#888888'
}

function edgeWidth(strength) {
  return 1 + strength * 5
}

function renderGraph() {
  if (!svgRef.value || !nodes.value.length) return

  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  d3.select(svgRef.value).selectAll('*').remove()
  svg = d3.select(svgRef.value).attr('width', width).attr('height', height)

  // Defs for arrowheads
  const defs = svg.append('defs')
  ;['positive', 'negative', 'neutral'].forEach(type => {
    defs.append('marker')
      .attr('id', `arrow-${type}`)
      .attr('viewBox', '0 -3 6 6')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-3L6,0L0,3')
      .attr('fill', type === 'positive' ? '#009900' : type === 'negative' ? '#dc2626' : '#888888')
  })

  zoomGroup = svg.append('g')

  svg.call(d3.zoom()
    .scaleExtent([0.3, 4])
    .on('zoom', (event) => {
      zoomGroup.attr('transform', event.transform)
    })
  )

  // Alliance hulls layer (below edges)
  zoomGroup.append('g').attr('class', 'alliances')
  // Edges layer
  zoomGroup.append('g').attr('class', 'edges')
  // Nodes layer
  zoomGroup.append('g').attr('class', 'nodes')

  const nodeData = nodes.value.map(n => ({
    ...n,
    x: width / 2 + (Math.random() - 0.5) * width * 0.4,
    y: height / 2 + (Math.random() - 0.5) * height * 0.4,
  }))

  // Render nodes
  const nodeGroup = zoomGroup.select('.nodes')
    .selectAll('g')
    .data(nodeData, d => d.id)
    .join('g')
    .attr('cursor', 'grab')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x; d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x; d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null; d.fy = null
      })
    )

  nodeGroup.append('circle')
    .attr('r', 14)
    .attr('fill', d => GROUP_COLORS[d.group] || '#667')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.9)

  nodeGroup.append('text')
    .text(d => d.name.split(' ')[0])
    .attr('text-anchor', 'middle')
    .attr('dy', 28)
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted)')
    .attr('pointer-events', 'none')

  // Tooltip on hover
  nodeGroup
    .on('mouseenter', function(event, d) {
      d3.select(this).select('circle')
        .transition().duration(150)
        .attr('r', 18).attr('stroke-width', 3)
      showTooltip(event, `${d.name}\n${d.role} @ ${d.company}`)
    })
    .on('mouseleave', function() {
      d3.select(this).select('circle')
        .transition().duration(150)
        .attr('r', 14).attr('stroke-width', 2)
      hideTooltip()
    })

  simulation = d3.forceSimulation(nodeData)
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('collision', d3.forceCollide(30))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05))
    .on('tick', () => {
      nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`)
      updateEdges()
      updateAlliances()
    })

  // Initial edge render
  updateSnapshot()
}

function updateSnapshot() {
  if (!zoomGroup || !currentSnapshot.value) return

  const snap = currentSnapshot.value
  const edgesData = snap.edges || []

  // Update link force
  if (simulation) {
    const nodeMap = new Map()
    simulation.nodes().forEach(n => nodeMap.set(n.id, n))

    const links = edgesData
      .filter(e => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map(e => ({
        source: nodeMap.get(e.source),
        target: nodeMap.get(e.target),
        affinity: e.affinity,
        strength: e.strength,
      }))

    simulation.force('link', d3.forceLink(links).distance(120).strength(d => d.strength * 0.3))
    simulation.alpha(0.3).restart()
  }

  updateEdges()
  updateAlliances()
}

function updateEdges() {
  if (!zoomGroup || !currentSnapshot.value) return

  const snap = currentSnapshot.value
  const edgesData = snap.edges || []
  const nodeMap = new Map()
  if (simulation) simulation.nodes().forEach(n => nodeMap.set(n.id, n))

  const edgeGroup = zoomGroup.select('.edges')
  const lines = edgeGroup.selectAll('line')
    .data(edgesData, d => `${d.source}-${d.target}`)

  lines.exit().transition().duration(200).attr('opacity', 0).remove()

  const enter = lines.enter().append('line')
    .attr('opacity', 0)
    .attr('cursor', 'pointer')
    .on('click', (event, d) => {
      selectedEdge.value = d
    })

  enter.merge(lines)
    .transition().duration(300)
    .attr('x1', d => nodeMap.get(d.source)?.x || 0)
    .attr('y1', d => nodeMap.get(d.source)?.y || 0)
    .attr('x2', d => nodeMap.get(d.target)?.x || 0)
    .attr('y2', d => nodeMap.get(d.target)?.y || 0)
    .attr('stroke', d => edgeColor(d.affinity))
    .attr('stroke-width', d => edgeWidth(d.strength))
    .attr('opacity', 0.7)

  // Also update non-transitioning positions during tick
  edgeGroup.selectAll('line')
    .attr('x1', d => nodeMap.get(d.source)?.x || 0)
    .attr('y1', d => nodeMap.get(d.source)?.y || 0)
    .attr('x2', d => nodeMap.get(d.target)?.x || 0)
    .attr('y2', d => nodeMap.get(d.target)?.y || 0)
}

function updateAlliances() {
  if (!zoomGroup || !currentSnapshot.value) return

  const snap = currentSnapshot.value
  const allianceData = snap.alliances || []
  const nodeMap = new Map()
  if (simulation) simulation.nodes().forEach(n => nodeMap.set(n.id, n))

  const allianceGroup = zoomGroup.select('.alliances')
  const hulls = allianceGroup.selectAll('path')
    .data(allianceData, d => d.label)

  hulls.exit().transition().duration(200).attr('opacity', 0).remove()

  hulls.enter().append('path')
    .attr('fill', d => GROUP_COLORS[d.label] || '#888')
    .attr('opacity', 0)
    .merge(hulls)
    .each(function(d) {
      const points = d.members
        .map(id => nodeMap.get(id))
        .filter(Boolean)
        .map(n => [n.x, n.y])
      if (points.length < 3) {
        d3.select(this).attr('d', '')
        return
      }
      const hull = d3.polygonHull(points)
      if (!hull) {
        d3.select(this).attr('d', '')
        return
      }
      // Expand hull outward by padding
      const cx = d3.mean(hull, p => p[0])
      const cy = d3.mean(hull, p => p[1])
      const expanded = hull.map(([x, y]) => {
        const dx = x - cx, dy = y - cy
        const len = Math.sqrt(dx * dx + dy * dy) || 1
        return [x + dx / len * 25, y + dy / len * 25]
      })
      d3.select(this).attr('d', `M${expanded.map(p => p.join(',')).join('L')}Z`)
    })
    .transition().duration(300)
    .attr('opacity', 0.08)
}

// Tooltip helpers
const tooltipRef = ref(null)

function showTooltip(event, text) {
  if (!tooltipRef.value) return
  const el = tooltipRef.value
  el.textContent = text
  el.style.display = 'block'
  el.style.left = `${event.pageX + 12}px`
  el.style.top = `${event.pageY - 10}px`
}

function hideTooltip() {
  if (tooltipRef.value) tooltipRef.value.style.display = 'none'
}

// Playback controls
function play() {
  if (currentBucket.value >= totalBuckets.value - 1) {
    currentBucket.value = 0
  }
  playing.value = true
  tick()
}

function pause() {
  playing.value = false
  if (animTimer) { clearTimeout(animTimer); animTimer = null }
}

function tick() {
  if (!playing.value) return
  if (currentBucket.value >= totalBuckets.value - 1) {
    playing.value = false
    return
  }
  currentBucket.value++
  const delay = Math.max(100, 600 / speed.value)
  animTimer = setTimeout(tick, delay)
}

function seekTo(bucket) {
  pause()
  currentBucket.value = bucket
}

function setSpeed(s) {
  speed.value = s
  if (playing.value) {
    if (animTimer) clearTimeout(animTimer)
    tick()
  }
}

function closeSidePanel() {
  selectedEdge.value = null
}

watch(currentBucket, () => {
  updateSnapshot()
})

onMounted(() => {
  fetchData()
  resizeObserver = new ResizeObserver(() => {
    if (nodes.value.length) renderGraph()
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  pause()
  if (simulation) { simulation.stop(); simulation = null }
  if (resizeObserver) resizeObserver.disconnect()
})

function affinityLabel(v) {
  if (v > 0.3) return 'Strong positive'
  if (v > 0.1) return 'Positive'
  if (v > -0.1) return 'Neutral'
  if (v > -0.3) return 'Negative'
  return 'Strong negative'
}

function affinityColor(v) {
  if (v > 0.1) return '#009900'
  if (v < -0.1) return '#dc2626'
  return '#888888'
}
</script>

<template>
  <div class="flex h-full relative overflow-hidden">
    <!-- Main graph area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Loading state -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <svg class="w-8 h-8 animate-spin text-[#2068FF]" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span class="text-sm text-[var(--color-text-muted)]">Loading relationship data...</span>
        </div>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <p class="text-sm text-[var(--color-error)]">{{ error }}</p>
          <button @click="fetchData" class="mt-2 text-xs text-[#2068FF] hover:underline">Retry</button>
        </div>
      </div>

      <!-- Graph -->
      <template v-else>
        <div ref="containerRef" class="flex-1 relative min-h-0">
          <svg ref="svgRef" class="w-full h-full" />
          <div
            ref="tooltipRef"
            class="fixed z-50 px-2.5 py-1.5 text-xs bg-[#050505] text-white rounded-md shadow-lg pointer-events-none whitespace-pre-line"
            style="display: none"
          />

          <!-- Legend -->
          <div class="absolute top-3 left-3 flex flex-col gap-1.5 text-xs bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 shadow-sm">
            <span class="font-medium text-[var(--color-text)]">Groups</span>
            <div v-for="(color, group) in GROUP_COLORS" :key="group" class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full inline-block" :style="{ background: color }" />
              <span class="text-[var(--color-text-muted)] capitalize">{{ group }}</span>
            </div>
            <hr class="border-[var(--color-border)] my-1">
            <span class="font-medium text-[var(--color-text)]">Edges</span>
            <div class="flex items-center gap-1.5"><span class="w-4 h-0.5 inline-block bg-[#009900]" /> <span class="text-[var(--color-text-muted)]">Positive</span></div>
            <div class="flex items-center gap-1.5"><span class="w-4 h-0.5 inline-block bg-[#888]" /> <span class="text-[var(--color-text-muted)]">Neutral</span></div>
            <div class="flex items-center gap-1.5"><span class="w-4 h-0.5 inline-block bg-[#dc2626]" /> <span class="text-[var(--color-text-muted)]">Negative</span></div>
          </div>

          <!-- Round indicator -->
          <div class="absolute top-3 right-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 shadow-sm text-center">
            <div class="text-xs text-[var(--color-text-muted)]">Round</div>
            <div class="text-lg font-semibold text-[var(--color-text)]">{{ currentRound }}</div>
            <div class="text-xs text-[var(--color-text-muted)]">/ 144</div>
          </div>

          <!-- Alliance / conflict badges -->
          <div v-if="currentSnapshot" class="absolute bottom-16 left-3 flex flex-col gap-1 text-xs">
            <div
              v-for="a in currentSnapshot.alliances"
              :key="'a-' + a.label"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border"
              :style="{ borderColor: GROUP_COLORS[a.label] || '#888', color: GROUP_COLORS[a.label] || '#888', background: (GROUP_COLORS[a.label] || '#888') + '10' }"
            >
              <span class="w-1.5 h-1.5 rounded-full" :style="{ background: GROUP_COLORS[a.label] || '#888' }" />
              {{ a.label }} alliance
            </div>
            <div
              v-for="c in currentSnapshot.conflicts"
              :key="'c-' + c.agents.join('-')"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-red-300 text-red-600 bg-red-50"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-red-500" />
              conflict ({{ c.intensity.toFixed(2) }})
            </div>
          </div>
        </div>

        <!-- Timeline controls -->
        <div class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
          <div class="flex items-center gap-3">
            <!-- Play / Pause -->
            <button
              @click="playing ? pause() : play()"
              class="w-8 h-8 flex items-center justify-center rounded-md border border-[var(--color-border)] hover:bg-[var(--color-bg)] transition-colors"
              :aria-label="playing ? 'Pause' : 'Play'"
            >
              <svg v-if="!playing" class="w-4 h-4 text-[var(--color-text)]" viewBox="0 0 20 20" fill="currentColor">
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
              <svg v-else class="w-4 h-4 text-[var(--color-text)]" viewBox="0 0 20 20" fill="currentColor">
                <path d="M5.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75A.75.75 0 007.25 3h-1.5zM12.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75a.75.75 0 00-.75-.75h-1.5z" />
              </svg>
            </button>

            <!-- Scrubber -->
            <input
              type="range"
              :min="0"
              :max="Math.max(0, totalBuckets - 1)"
              :value="currentBucket"
              @input="seekTo(Number($event.target.value))"
              class="flex-1 h-1.5 accent-[#2068FF] cursor-pointer"
            />

            <!-- Speed selector -->
            <div class="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
              <button
                v-for="s in [1, 2, 5]"
                :key="s"
                @click="setSpeed(s)"
                class="px-1.5 py-0.5 rounded transition-colors"
                :class="speed === s
                  ? 'bg-[#2068FF] text-white'
                  : 'hover:bg-[var(--color-bg)]'"
              >{{ s }}x</button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Side panel: edge detail -->
    <Transition name="slide-right">
      <div
        v-if="selectedEdge"
        class="w-72 shrink-0 border-l border-[var(--color-border)] bg-[var(--color-surface)] overflow-y-auto"
      >
        <div class="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
          <span class="text-sm font-medium text-[var(--color-text)]">Relationship</span>
          <button @click="closeSidePanel" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]">&times;</button>
        </div>
        <div class="px-4 py-3">
          <div class="text-sm font-medium text-[var(--color-text)]">{{ selectedSourceName }}</div>
          <div class="flex items-center gap-2 my-2">
            <span class="flex-1 h-px" :style="{ background: affinityColor(selectedEdge.affinity) }" />
            <span class="text-xs px-2 py-0.5 rounded-full border" :style="{ color: affinityColor(selectedEdge.affinity), borderColor: affinityColor(selectedEdge.affinity) }">
              {{ affinityLabel(selectedEdge.affinity) }}
            </span>
            <span class="flex-1 h-px" :style="{ background: affinityColor(selectedEdge.affinity) }" />
          </div>
          <div class="text-sm font-medium text-[var(--color-text)]">{{ selectedTargetName }}</div>

          <div class="mt-1 text-xs text-[var(--color-text-muted)]">
            Affinity: {{ selectedEdge.affinity.toFixed(3) }} &middot; Strength: {{ selectedEdge.strength.toFixed(3) }}
          </div>
        </div>

        <!-- Timeline of interactions -->
        <div class="px-4 pb-4">
          <div class="text-xs font-medium text-[var(--color-text)] mb-2">Interaction History</div>
          <div class="space-y-2">
            <div
              v-for="(entry, idx) in selectedEdgeHistory"
              :key="idx"
              class="flex gap-2 text-xs"
            >
              <div class="flex flex-col items-center">
                <span
                  class="w-2 h-2 rounded-full shrink-0 mt-1"
                  :style="{ background: affinityColor(entry.affinity) }"
                />
                <span v-if="idx < selectedEdgeHistory.length - 1" class="w-px flex-1 bg-[var(--color-border)]" />
              </div>
              <div class="pb-2">
                <div class="text-[var(--color-text-muted)]">Round {{ entry.round }}</div>
                <div class="text-[var(--color-text)]">{{ entry.interaction }}</div>
                <div class="text-[var(--color-text-muted)]">
                  Affinity: <span :style="{ color: affinityColor(entry.affinity) }">{{ entry.affinity.toFixed(3) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.25s ease;
}
.slide-right-enter-from,
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(16px);
}
</style>
