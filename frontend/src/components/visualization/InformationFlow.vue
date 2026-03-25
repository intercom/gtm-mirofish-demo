<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  agents: {
    type: Array,
    default: () => [
      { id: 0, name: 'Sarah Chen', role: 'VP Support', company: 'Acme SaaS' },
      { id: 1, name: 'Marcus Johnson', role: 'CX Director', company: 'MedFirst' },
      { id: 2, name: 'Priya Patel', role: 'Head of Ops', company: 'PayStream' },
      { id: 3, name: 'David Kim', role: 'IT Leader', company: 'ShopNova' },
      { id: 4, name: 'Rachel Torres', role: 'VP Support', company: 'CloudOps' },
      { id: 5, name: 'James Wright', role: 'CX Director', company: 'Retail Plus' },
      { id: 6, name: 'Anika Sharma', role: 'Support Eng Lead', company: 'DevStack' },
      { id: 7, name: 'Tom O\'Brien', role: 'VP CS', company: 'GrowthLoop' },
      { id: 8, name: 'Elena Vasquez', role: 'Dir Digital', company: 'HealthBridge' },
      { id: 9, name: 'Michael Chang', role: 'Head of Ops', company: 'FinEdge' },
      { id: 10, name: 'Lisa Park', role: 'VP CX', company: 'TravelNow' },
      { id: 11, name: 'Sofia Martinez', role: 'Support Mgr', company: 'QuickShip' },
      { id: 12, name: 'Nathan Lee', role: 'CTO', company: 'DataPulse' },
      { id: 13, name: 'Catherine Hayes', role: 'CFO', company: 'ScaleUp Corp' },
      { id: 14, name: 'Robert Williams', role: 'IT Director', company: 'EduSpark' },
    ],
  },
  totalRounds: { type: Number, default: 48 },
})

// --- Constants ---
const INFO_TYPES = {
  fact: { color: '#2068FF', label: 'Fact' },
  decision: { color: '#ef4444', label: 'Decision' },
  opinion: { color: '#f59e0b', label: 'Opinion' },
}

const SPEED_OPTIONS = [
  { key: 'slow', label: 'Slow', ms: 2000 },
  { key: 'medium', label: 'Medium', ms: 800 },
  { key: 'fast', label: 'Fast', ms: 300 },
]

// --- State ---
const svgRef = ref(null)
const containerRef = ref(null)
const playing = ref(false)
const currentRound = ref(0)
const speed = ref('medium')
const hoveredNode = ref(null)

let animFrameId = null
let lastTickTime = 0
let resizeObserver = null
let simulation = null
let nodes = []
let edges = []
let cascades = []

// --- Deterministic seeded random ---
function seededRandom(seed) {
  let s = seed
  return () => {
    s = (s * 16807 + 0) % 2147483647
    return (s - 1) / 2147483646
  }
}

// --- Generate network edges and cascade data ---
function generateNetworkData() {
  const rng = seededRandom(42)
  const agentCount = props.agents.length

  // Build edges: each agent connects to 2-4 others
  const edgeSet = new Set()
  edges = []
  for (let i = 0; i < agentCount; i++) {
    const numConnections = 2 + Math.floor(rng() * 3)
    for (let c = 0; c < numConnections; c++) {
      let target = Math.floor(rng() * agentCount)
      if (target === i) target = (target + 1) % agentCount
      const key = `${Math.min(i, target)}-${Math.max(i, target)}`
      if (!edgeSet.has(key)) {
        edgeSet.add(key)
        edges.push({ source: i, target })
      }
    }
  }

  // Build cascades: information pieces that spread through the network
  const types = Object.keys(INFO_TYPES)
  cascades = []
  const numCascades = 6 + Math.floor(rng() * 4)

  for (let ci = 0; ci < numCascades; ci++) {
    const type = types[Math.floor(rng() * types.length)]
    const originAgent = Math.floor(rng() * agentCount)
    const startRound = 1 + Math.floor(rng() * Math.floor(props.totalRounds * 0.6))

    // BFS-style spread through connected agents
    const reached = new Map() // agentId -> round reached
    reached.set(originAgent, startRound)
    const queue = [originAgent]
    let depth = 0

    while (queue.length > 0 && depth < 5) {
      const nextQueue = []
      for (const agentId of queue) {
        const reachRound = reached.get(agentId)
        // Find neighbors
        for (const e of edges) {
          let neighbor = -1
          if (e.source === agentId) neighbor = e.target
          else if (e.target === agentId) neighbor = e.source
          if (neighbor >= 0 && !reached.has(neighbor) && rng() > 0.3) {
            const spreadDelay = 1 + Math.floor(rng() * 4)
            const arrivalRound = reachRound + spreadDelay
            if (arrivalRound <= props.totalRounds) {
              reached.set(neighbor, arrivalRound)
              nextQueue.push(neighbor)
            }
          }
        }
      }
      queue.length = 0
      queue.push(...nextQueue)
      depth++
    }

    // Convert to cascade events (sender -> receiver transitions)
    const events = []
    for (const [agentId, round] of reached) {
      if (agentId === originAgent) continue
      // Find which already-reached neighbor sent it
      let sender = originAgent
      let senderRound = startRound
      for (const e of edges) {
        let neighbor = -1
        if (e.source === agentId) neighbor = e.target
        else if (e.target === agentId) neighbor = e.source
        if (neighbor >= 0 && reached.has(neighbor) && reached.get(neighbor) < round) {
          if (reached.get(neighbor) > senderRound) {
            sender = neighbor
            senderRound = reached.get(neighbor)
          }
        }
      }
      events.push({ from: sender, to: agentId, round })
    }

    cascades.push({ id: ci, type, origin: originAgent, startRound, reached, events })
  }
}

// --- Active cascades at current round ---
const activeCascadeInfo = computed(() => {
  const round = currentRound.value
  return cascades.map(c => {
    const reachedAgents = new Set()
    for (const [agentId, r] of c.reached) {
      if (r <= round) reachedAgents.add(agentId)
    }
    return { ...c, reachedAgents, active: c.startRound <= round }
  }).filter(c => c.active)
})

const speedMs = computed(() => SPEED_OPTIONS.find(s => s.key === speed.value)?.ms ?? 800)

// --- D3 rendering ---
function getContainerSize() {
  const el = containerRef.value
  if (!el) return { width: 600, height: 400 }
  return { width: el.clientWidth || 600, height: Math.max(350, Math.min(500, el.clientWidth * 0.6)) }
}

function initGraph() {
  const container = svgRef.value
  if (!container) return

  generateNetworkData()

  const { width, height } = getContainerSize()

  d3.select(container).selectAll('*').remove()

  const svg = d3.select(container)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const g = svg.append('g').attr('class', 'zoom-group')

  // Zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.5, 3])
    .on('zoom', (event) => g.attr('transform', event.transform))
  svg.call(zoom)

  // Prepare D3 force nodes
  nodes = props.agents.map((a, i) => ({ ...a, index: i }))

  const d3Edges = edges.map(e => ({ source: e.source, target: e.target }))

  // Edge lines
  const edgeGroup = g.append('g').attr('class', 'edges')
  edgeGroup.selectAll('line')
    .data(d3Edges)
    .join('line')
    .attr('stroke', 'rgba(0,0,0,0.08)')
    .attr('stroke-width', 1)

  // Node group
  const nodeGroup = g.append('g').attr('class', 'nodes')
  const nodeEls = nodeGroup.selectAll('g')
    .data(nodes)
    .join('g')
    .attr('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      })
    )
    .on('mouseenter', (event, d) => { hoveredNode.value = d })
    .on('mouseleave', () => { hoveredNode.value = null })

  // Node circles
  nodeEls.append('circle')
    .attr('r', 16)
    .attr('fill', '#fff')
    .attr('stroke', 'rgba(0,0,0,0.12)')
    .attr('stroke-width', 1.5)

  // Node initials
  nodeEls.append('text')
    .text(d => d.name.split(' ').map(w => w[0]).join(''))
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', '#555')
    .attr('pointer-events', 'none')

  // Name labels below nodes
  nodeEls.append('text')
    .text(d => d.name.split(' ')[0])
    .attr('text-anchor', 'middle')
    .attr('dy', '30px')
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .attr('pointer-events', 'none')

  // Particle layer
  g.append('g').attr('class', 'particles')

  // Force simulation
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(d3Edges).id((_, i) => i).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide(30))
    .on('tick', () => {
      edgeGroup.selectAll('line')
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      nodeEls.attr('transform', d => `translate(${d.x},${d.y})`)
    })

  // Let simulation settle
  simulation.alpha(1).restart()
}

function updateVisualization() {
  const container = svgRef.value
  if (!container) return

  const svg = d3.select(container)
  const g = svg.select('.zoom-group')
  if (g.empty()) return

  const round = currentRound.value

  // Update node highlighting — show which agents have received information
  const receivedByAgent = new Map()
  for (const cascade of activeCascadeInfo.value) {
    for (const agentId of cascade.reachedAgents) {
      if (!receivedByAgent.has(agentId)) receivedByAgent.set(agentId, [])
      receivedByAgent.get(agentId).push(cascade.type)
    }
  }

  g.select('.nodes').selectAll('g').select('circle')
    .attr('fill', (d) => {
      const types = receivedByAgent.get(d.index)
      if (!types || types.length === 0) return '#fff'
      // Use the first type's color with low opacity for the fill
      return INFO_TYPES[types[0]].color + '18'
    })
    .attr('stroke', (d) => {
      const types = receivedByAgent.get(d.index)
      if (!types || types.length === 0) return 'rgba(0,0,0,0.12)'
      return INFO_TYPES[types[0]].color
    })
    .attr('stroke-width', (d) => receivedByAgent.has(d.index) ? 2.5 : 1.5)

  // Build active particles: events happening at or near current round
  const activeParticles = []
  for (const cascade of cascades) {
    for (const event of cascade.events) {
      // Particle is visible while transitioning (event.round-1 to event.round)
      if (round >= event.round - 1 && round <= event.round + 1) {
        const progress = Math.max(0, Math.min(1, (round - (event.round - 1)) / 2))
        const fromNode = nodes[event.from]
        const toNode = nodes[event.to]
        if (fromNode && toNode) {
          activeParticles.push({
            key: `${cascade.id}-${event.from}-${event.to}`,
            x: fromNode.x + (toNode.x - fromNode.x) * progress,
            y: fromNode.y + (toNode.y - fromNode.y) * progress,
            color: INFO_TYPES[cascade.type].color,
            opacity: 1 - Math.abs(progress - 0.5) * 0.4,
          })
        }
      }
    }
  }

  // Render particles
  const particleGroup = g.select('.particles')
  const circles = particleGroup.selectAll('circle')
    .data(activeParticles, d => d.key)

  circles.exit().remove()

  circles.enter()
    .append('circle')
    .attr('r', 5)
    .attr('pointer-events', 'none')
    .merge(circles)
    .attr('cx', d => d.x)
    .attr('cy', d => d.y)
    .attr('fill', d => d.color)
    .attr('opacity', d => d.opacity)

  // Particle glow effect
  const glows = particleGroup.selectAll('.glow')
    .data(activeParticles, d => d.key)

  glows.exit().remove()

  glows.enter()
    .append('circle')
    .attr('class', 'glow')
    .attr('r', 10)
    .attr('pointer-events', 'none')
    .merge(glows)
    .attr('cx', d => d.x)
    .attr('cy', d => d.y)
    .attr('fill', d => d.color)
    .attr('opacity', d => d.opacity * 0.2)
}

// --- Playback ---
function tick(timestamp) {
  if (!playing.value) return

  if (timestamp - lastTickTime >= speedMs.value) {
    lastTickTime = timestamp
    if (currentRound.value < props.totalRounds) {
      currentRound.value++
      updateVisualization()
    } else {
      playing.value = false
    }
  }
  animFrameId = requestAnimationFrame(tick)
}

function togglePlay() {
  playing.value = !playing.value
  if (playing.value) {
    if (currentRound.value >= props.totalRounds) {
      currentRound.value = 0
    }
    lastTickTime = 0
    animFrameId = requestAnimationFrame(tick)
  } else if (animFrameId) {
    cancelAnimationFrame(animFrameId)
    animFrameId = null
  }
}

function reset() {
  playing.value = false
  if (animFrameId) {
    cancelAnimationFrame(animFrameId)
    animFrameId = null
  }
  currentRound.value = 0
  updateVisualization()
}

function onSliderInput(e) {
  currentRound.value = Number(e.target.value)
  updateVisualization()
}

// --- Resize ---
function handleResize() {
  const { width, height } = getContainerSize()
  const svg = d3.select(svgRef.value)
  svg.attr('width', width).attr('height', height).attr('viewBox', `0 0 ${width} ${height}`)
  if (simulation) {
    simulation.force('center', d3.forceCenter(width / 2, height / 2))
    simulation.alpha(0.3).restart()
  }
}

// --- Tooltip ---
const tooltipStyle = computed(() => {
  if (!hoveredNode.value) return { display: 'none' }
  return { display: 'block' }
})

const tooltipContent = computed(() => {
  if (!hoveredNode.value) return null
  const d = hoveredNode.value
  const types = []
  for (const cascade of activeCascadeInfo.value) {
    if (cascade.reachedAgents.has(d.index)) {
      types.push(cascade.type)
    }
  }
  const unique = [...new Set(types)]
  return {
    name: d.name,
    role: d.role,
    company: d.company,
    infoReceived: unique.length,
    types: unique,
  }
})

// --- Lifecycle ---
watch(currentRound, () => updateVisualization())

onMounted(() => {
  nextTick(() => {
    initGraph()
    // Let force simulation settle before starting
    setTimeout(() => updateVisualization(), 500)
  })

  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => handleResize())
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  playing.value = false
  if (animFrameId) cancelAnimationFrame(animFrameId)
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<template>
  <div ref="containerRef" class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 pt-4 pb-2">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Information Flow</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          How information cascades through the agent network
        </p>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-3">
        <div v-for="(info, key) in INFO_TYPES" :key="key" class="flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: info.color }" />
          <span class="text-[10px] text-[var(--color-text-muted)]">{{ info.label }}</span>
        </div>
      </div>
    </div>

    <!-- SVG Container -->
    <div class="relative">
      <svg ref="svgRef" class="w-full" />

      <!-- Tooltip -->
      <div
        v-if="tooltipContent"
        class="absolute top-3 right-3 bg-[var(--color-navy)] text-white rounded-lg px-3 py-2 text-xs shadow-lg pointer-events-none z-10"
        :style="tooltipStyle"
      >
        <div class="font-semibold">{{ tooltipContent.name }}</div>
        <div class="text-[var(--color-text-on-dark-secondary)] mt-0.5">
          {{ tooltipContent.role }} @ {{ tooltipContent.company }}
        </div>
        <div v-if="tooltipContent.infoReceived > 0" class="mt-1.5 pt-1.5 border-t border-white/10">
          <span class="text-[var(--color-text-on-dark-muted)]">Received:</span>
          <span
            v-for="t in tooltipContent.types"
            :key="t"
            class="inline-block ml-1.5 px-1.5 py-0.5 rounded text-[10px] font-medium"
            :style="{ backgroundColor: INFO_TYPES[t].color + '33', color: INFO_TYPES[t].color }"
          >{{ INFO_TYPES[t].label }}</span>
        </div>
        <div v-else class="mt-1 text-[var(--color-text-on-dark-muted)]">No information received yet</div>
      </div>
    </div>

    <!-- Controls -->
    <div class="flex items-center gap-4 px-5 py-3 border-t border-[var(--color-border)]">
      <!-- Play/Pause -->
      <button
        class="flex items-center justify-center w-8 h-8 rounded-lg transition-colors"
        :class="playing
          ? 'bg-[var(--color-primary)] text-white'
          : 'bg-[var(--color-primary-light)] text-[var(--color-primary)] hover:bg-[var(--color-primary-tint-hover)]'"
        @click="togglePlay"
      >
        <svg v-if="!playing" width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
          <polygon points="3,1 12,7 3,13" />
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
          <rect x="2" y="1" width="3.5" height="12" rx="1" />
          <rect x="8.5" y="1" width="3.5" height="12" rx="1" />
        </svg>
      </button>

      <!-- Reset -->
      <button
        class="flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
        @click="reset"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <path d="M1 1v4.5h4.5" />
          <path d="M2.5 9a5 5 0 1 0 1-5.2L1 5.5" />
        </svg>
      </button>

      <!-- Round Slider -->
      <div class="flex-1 flex items-center gap-3">
        <input
          type="range"
          :min="0"
          :max="totalRounds"
          :value="currentRound"
          class="flex-1 h-1.5 appearance-none rounded-full bg-[var(--color-tint)] accent-[var(--color-primary)] cursor-pointer"
          @input="onSliderInput"
        />
        <span class="text-xs font-mono text-[var(--color-text-muted)] min-w-[4.5rem] text-right tabular-nums">
          Round {{ currentRound }} / {{ totalRounds }}
        </span>
      </div>

      <!-- Speed Toggle -->
      <div class="flex gap-0.5 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          v-for="opt in SPEED_OPTIONS"
          :key="opt.key"
          class="px-2.5 py-1 text-[10px] font-medium rounded transition-colors"
          :class="speed === opt.key
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="speed = opt.key"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

input[type="range"]::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
</style>
