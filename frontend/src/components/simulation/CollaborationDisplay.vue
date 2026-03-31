<script setup>
import { ref, computed, watch, onMounted, onUnmounted, inject, nextTick } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '../../api/simulation'

const polling = inject('polling')
const demoMode = inject('demoMode', ref(false))

const svgContainer = ref(null)
const collabData = ref(null)
const loading = ref(true)
const error = ref(null)
const selectedNode = ref(null)
const hoveredEdge = ref(null)

let fetchTimer = null
let d3Simulation = null
let animationFrame = null

const nodes = computed(() => collabData.value?.nodes || [])
const edges = computed(() => collabData.value?.edges || [])
const messages = computed(() => collabData.value?.messages || [])
const collaborationScore = computed(() => collabData.value?.collaborationScore || 0)
const totalInteractions = computed(() => collabData.value?.totalInteractions || 0)
const activeTopic = computed(() => collabData.value?.activeTopic || '')
const currentRound = computed(() => collabData.value?.currentRound || 0)

const scoreColor = computed(() => {
  const s = collaborationScore.value
  if (s >= 0.7) return 'var(--color-success)'
  if (s >= 0.4) return 'var(--color-warning)'
  return 'var(--color-error)'
})

const isActive = computed(() => {
  const rs = polling?.runStatus?.value?.runner_status
  return rs === 'running' || rs === 'starting' || demoMode.value
})

const recentMessages = computed(() => messages.value.slice(-5).reverse())

async function fetchCollaboration() {
  const simId = polling?.runStatus?.value?.simulation_id
  if (!simId && !demoMode.value) return

  try {
    const res = await simulationApi.getCollaboration(simId || 'demo')
    if (res.data?.success) {
      collabData.value = res.data.data
      error.value = null
      await nextTick()
      renderGraph()
    }
  } catch (e) {
    error.value = e.message || 'Failed to load collaboration data'
  } finally {
    loading.value = false
  }
}

function startPolling() {
  stopPolling()
  fetchCollaboration()
  fetchTimer = setInterval(fetchCollaboration, 5000)
}

function stopPolling() {
  if (fetchTimer) {
    clearInterval(fetchTimer)
    fetchTimer = null
  }
}

function renderGraph() {
  if (!svgContainer.value || !nodes.value.length) return

  const container = svgContainer.value
  const width = container.clientWidth
  const height = container.clientHeight || 320

  d3.select(container).selectAll('svg').remove()

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const defs = svg.append('defs')

  // Glow filter for active nodes
  const filter = defs.append('filter').attr('id', 'glow')
  filter.append('feGaussianBlur')
    .attr('stdDeviation', '3')
    .attr('result', 'coloredBlur')
  const feMerge = filter.append('feMerge')
  feMerge.append('feMergeNode').attr('in', 'coloredBlur')
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

  // Arrow markers
  edges.value.forEach((e, i) => {
    const sourceNode = nodes.value.find(n => n.id === e.source || n.id === e.source?.id)
    defs.append('marker')
      .attr('id', `arrow-${i}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 28)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', sourceNode?.color || 'var(--color-border)')
      .attr('opacity', 0.5)
  })

  const graphNodes = nodes.value.map(n => ({ ...n }))
  const graphEdges = edges.value.map(e => ({
    ...e,
    source: e.source,
    target: e.target,
  }))

  d3Simulation = d3.forceSimulation(graphNodes)
    .force('link', d3.forceLink(graphEdges)
      .id(d => d.id)
      .distance(d => 100 - d.weight * 30)
      .strength(d => 0.3 + d.weight * 0.4))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide(35))

  // Edge lines
  const links = svg.append('g')
    .selectAll('line')
    .data(graphEdges)
    .join('line')
    .attr('stroke', (d) => {
      const src = graphNodes.find(n => n.id === (d.source?.id || d.source))
      return src?.color || 'var(--color-border)'
    })
    .attr('stroke-opacity', d => 0.15 + d.weight * 0.35)
    .attr('stroke-width', d => 1 + d.weight * 2.5)
    .attr('marker-end', (d, i) => `url(#arrow-${i})`)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      hoveredEdge.value = d
    })
    .on('mouseleave', () => {
      hoveredEdge.value = null
    })

  // Animated particles along edges
  const particles = svg.append('g')
    .selectAll('circle')
    .data(graphEdges.filter(e => e.weight > 0.3))
    .join('circle')
    .attr('r', 3)
    .attr('fill', (d) => {
      const src = graphNodes.find(n => n.id === (d.source?.id || d.source))
      return src?.color || '#2068FF'
    })
    .attr('opacity', 0.7)

  // Node groups
  const nodeGroups = svg.append('g')
    .selectAll('g')
    .data(graphNodes)
    .join('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      selectedNode.value = selectedNode.value?.id === d.id ? null : d
    })
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) d3Simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) d3Simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      }))

  // Outer ring (pulse for active agents)
  nodeGroups.append('circle')
    .attr('r', 24)
    .attr('fill', 'none')
    .attr('stroke', d => d.color)
    .attr('stroke-width', 2)
    .attr('stroke-opacity', d => d.activeRound >= currentRound.value - 1 ? 0.4 : 0)
    .attr('class', d => d.activeRound >= currentRound.value - 1 ? 'pulse-ring' : '')

  // Main circle
  nodeGroups.append('circle')
    .attr('r', 20)
    .attr('fill', d => d.color)
    .attr('filter', 'url(#glow)')
    .attr('opacity', 0.9)

  // Initials text
  nodeGroups.append('text')
    .text(d => d.initials)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'central')
    .attr('fill', 'white')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('pointer-events', 'none')

  // Name labels
  nodeGroups.append('text')
    .text(d => d.name)
    .attr('text-anchor', 'middle')
    .attr('y', 34)
    .attr('fill', 'var(--color-text)')
    .attr('font-size', '10px')
    .attr('font-weight', '500')
    .attr('pointer-events', 'none')

  // Message count badge
  nodeGroups.append('circle')
    .attr('cx', 14)
    .attr('cy', -14)
    .attr('r', 8)
    .attr('fill', 'var(--color-surface)')
    .attr('stroke', d => d.color)
    .attr('stroke-width', 1.5)

  nodeGroups.append('text')
    .text(d => d.messageCount)
    .attr('x', 14)
    .attr('y', -14)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'central')
    .attr('fill', 'var(--color-text)')
    .attr('font-size', '8px')
    .attr('font-weight', '600')
    .attr('pointer-events', 'none')

  let particleT = 0
  d3Simulation.on('tick', () => {
    links
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`)

    // Animate particles along edges
    particleT = (particleT + 0.008) % 1
    particles
      .attr('cx', d => d.source.x + (d.target.x - d.source.x) * ((particleT + d.weight) % 1))
      .attr('cy', d => d.source.y + (d.target.y - d.source.y) * ((particleT + d.weight) % 1))
  })
}

function interactionIcon(type) {
  switch (type) {
    case 'reply': return '\uD83D\uDCAC'
    case 'mention': return '\uD83D\uDCE2'
    case 'shared_topic': return '\uD83E\uDD1D'
    case 'thread_collab': return '\uD83E\uDDF5'
    case 'endorsement': return '\u2B50'
    default: return '\u26A1'
  }
}

function getNodeName(id) {
  const node = nodes.value.find(n => n.id === id)
  return node?.name || id
}

function getNodeColor(id) {
  const node = nodes.value.find(n => n.id === id)
  return node?.color || '#2068FF'
}

watch(isActive, (active) => {
  if (active) startPolling()
  else stopPolling()
}, { immediate: true })

onMounted(() => {
  if (!isActive.value) {
    fetchCollaboration()
  }
})

onUnmounted(() => {
  stopPolling()
  if (d3Simulation) d3Simulation.stop()
  if (animationFrame) cancelAnimationFrame(animationFrame)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden flex flex-col">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-[var(--color-border)]">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Collaboration Network</h3>
          <span
            v-if="isActive"
            class="flex items-center gap-1.5 text-[11px] text-[var(--color-text-muted)]"
          >
            <span class="inline-block w-1.5 h-1.5 rounded-full bg-[var(--color-success)] animate-pulse" />
            Live
          </span>
        </div>

        <div class="flex items-center gap-3">
          <!-- Collaboration score -->
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">Score</span>
            <span
              class="text-sm font-bold"
              :style="{ color: scoreColor }"
            >
              {{ Math.round(collaborationScore * 100) }}%
            </span>
          </div>

          <!-- Interaction count -->
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">Interactions</span>
            <span class="text-sm font-semibold text-[var(--color-text)]">{{ totalInteractions }}</span>
          </div>

          <!-- Round -->
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)] font-medium">
            R{{ currentRound }}
          </span>
        </div>
      </div>

      <!-- Active topic -->
      <div
        v-if="activeTopic"
        class="mt-2 flex items-center gap-1.5"
      >
        <span class="text-[10px] text-[var(--color-text-muted)]">Discussing:</span>
        <span class="text-[11px] text-[var(--color-primary)] font-medium">{{ activeTopic }}</span>
      </div>
    </div>

    <!-- Graph area -->
    <div class="relative flex-1 min-h-[320px]">
      <!-- Loading -->
      <div
        v-if="loading"
        class="absolute inset-0 flex items-center justify-center bg-[var(--color-surface)]"
      >
        <div class="text-center">
          <div class="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p class="text-xs text-[var(--color-text-muted)]">Loading collaboration data...</p>
        </div>
      </div>

      <!-- Error -->
      <div
        v-else-if="error && !collabData"
        class="absolute inset-0 flex items-center justify-center"
      >
        <div class="text-center">
          <p class="text-sm text-[var(--color-error)]">{{ error }}</p>
          <button
            class="mt-2 text-xs text-[var(--color-primary)] hover:underline"
            @click="fetchCollaboration"
          >
            Retry
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!nodes.length"
        class="absolute inset-0 flex flex-col items-center justify-center text-[var(--color-text-muted)]"
      >
        <div class="text-3xl mb-2">\uD83E\uDD1D</div>
        <p class="text-sm">Waiting for agent interactions...</p>
        <p class="text-xs mt-1">Collaboration patterns will appear as agents communicate</p>
      </div>

      <!-- D3 graph container -->
      <div
        v-show="nodes.length && !loading"
        ref="svgContainer"
        class="w-full h-full min-h-[320px]"
      />

      <!-- Selected node detail overlay -->
      <Transition name="slide-up">
        <div
          v-if="selectedNode"
          class="absolute bottom-3 left-3 right-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 shadow-lg"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div
                class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold"
                :style="{ backgroundColor: selectedNode.color }"
              >
                {{ selectedNode.initials }}
              </div>
              <div>
                <p class="text-sm font-semibold text-[var(--color-text)]">{{ selectedNode.name }}</p>
                <p class="text-[10px] text-[var(--color-text-muted)]">
                  {{ selectedNode.role }}{{ selectedNode.company ? ` @ ${selectedNode.company}` : '' }}
                </p>
              </div>
            </div>
            <button
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-lg leading-none"
              @click="selectedNode = null"
            >
              &times;
            </button>
          </div>
          <div class="flex gap-4 text-xs">
            <div>
              <span class="text-[var(--color-text-muted)]">Messages:</span>
              <span class="ml-1 font-semibold text-[var(--color-text)]">{{ selectedNode.messageCount }}</span>
            </div>
            <div>
              <span class="text-[var(--color-text-muted)]">Active round:</span>
              <span class="ml-1 font-semibold text-[var(--color-text)]">R{{ selectedNode.activeRound }}</span>
            </div>
            <div>
              <span class="text-[var(--color-text-muted)]">Connections:</span>
              <span class="ml-1 font-semibold text-[var(--color-text)]">
                {{ edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id || e.source?.id === selectedNode.id || e.target?.id === selectedNode.id).length }}
              </span>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Recent messages feed -->
    <div
      v-if="recentMessages.length"
      class="border-t border-[var(--color-border)] px-4 py-2 max-h-[140px] overflow-y-auto"
    >
      <p class="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">Recent Exchanges</p>
      <div class="space-y-1.5">
        <div
          v-for="(msg, i) in recentMessages"
          :key="i"
          class="flex items-center gap-2 text-[11px]"
        >
          <span class="text-xs">{{ interactionIcon(msg.type) }}</span>
          <span
            class="font-medium"
            :style="{ color: getNodeColor(msg.sender) }"
          >
            {{ getNodeName(msg.sender) }}
          </span>
          <span class="text-[var(--color-text-muted)]">&rarr;</span>
          <span
            class="font-medium"
            :style="{ color: getNodeColor(msg.receiver) }"
          >
            {{ getNodeName(msg.receiver) }}
          </span>
          <span class="text-[var(--color-text-muted)] truncate flex-1">{{ msg.topic }}</span>
          <span class="text-[10px] text-[var(--color-text-muted)] shrink-0">R{{ msg.round }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pulse-ring {
  animation: collab-ring-pulse 2s ease-in-out infinite;
}

@keyframes collab-ring-pulse {
  0%, 100% { r: 24; stroke-opacity: 0.4; }
  50% { r: 27; stroke-opacity: 0.15; }
}

.slide-up-enter-active {
  transition: all 0.25s ease-out;
}
.slide-up-leave-active {
  transition: all 0.15s ease-in;
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
