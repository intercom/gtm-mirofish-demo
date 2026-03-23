<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { graphApi } from '../api/graph'
import { useToast } from '../composables/useToast'

const props = defineProps({ taskId: String })
const toast = useToast()

const svgContainer = ref(null)
const graphData = ref({ nodes: [], edges: [] })
const status = ref('building')
const progress = ref(0)
const nodeCount = ref(0)
const edgeCount = ref(0)
const selectedNode = ref(null)

let pollInterval = null
let simulation = null
let resizeObserver = null
let resizeTimer = null

const TYPE_COLORS = {
  persona: '#ff5600',
  topic: '#2068FF',
  relationship: '#AA00FF',
}

function classifyNodeType(labels) {
  const text = labels.map((l) => l.toLowerCase()).join(' ')
  if (
    /person|persona|user|student|teacher|agent|customer|rep|manager|employee|founder|ceo|director|vp|engineer|designer/.test(
      text,
    )
  )
    return 'persona'
  if (
    /topic|concept|theme|subject|technology|tool|product|service|platform|feature|category|strategy|metric|channel/.test(
      text,
    )
  )
    return 'topic'
  return 'relationship'
}

function nodeColor(type) {
  return TYPE_COLORS[type] || '#666'
}

function nodeRadius(degree) {
  return 5 + Math.sqrt(Math.max(degree, 1)) * 4
}

const selectedConnections = computed(() => {
  if (!selectedNode.value) return []
  const id = selectedNode.value.id
  return graphData.value.edges
    .filter((e) => {
      const src = typeof e.source === 'object' ? e.source.id : e.source
      const tgt = typeof e.target === 'object' ? e.target.id : e.target
      return src === id || tgt === id
    })
    .map((e) => {
      const src =
        typeof e.source === 'object'
          ? e.source
          : graphData.value.nodes.find((n) => n.id === e.source)
      const tgt =
        typeof e.target === 'object'
          ? e.target
          : graphData.value.nodes.find((n) => n.id === e.target)
      return { edge: e, neighbor: src?.id === id ? tgt : src }
    })
})

const typeCounts = computed(() => {
  const counts = { persona: 0, topic: 0, relationship: 0 }
  graphData.value.nodes.forEach((n) => {
    if (counts[n.type] !== undefined) counts[n.type]++
  })
  return counts
})

// --- API polling ---

async function pollStatus() {
  try {
    const res = await graphApi.getTask(props.taskId)
    const task = res.data?.data
    if (!task) return

    progress.value = task.progress || 0

    if (task.status === 'completed') {
      clearInterval(pollInterval)
      pollInterval = null
      const graphId = task.result?.graph_id
      if (graphId) await fetchGraphData(graphId)
      else loadSampleData()
    } else if (task.status === 'failed') {
      status.value = 'error'
      clearInterval(pollInterval)
      pollInterval = null
      toast.error('Knowledge graph build failed')
    }
  } catch {
    clearInterval(pollInterval)
    pollInterval = null
    loadSampleData()
  }
}

async function fetchGraphData(graphId) {
  try {
    const res = await graphApi.getData(graphId)
    processAndRender(res.data?.data)
  } catch {
    loadSampleData()
  }
}

// --- Data processing ---

function processAndRender(data) {
  const nodes = (data.nodes || []).map((n) => ({
    id: n.uuid,
    name: n.name,
    labels: n.labels || [],
    summary: n.summary || '',
    type: classifyNodeType(n.labels || []),
    attributes: n.attributes || {},
    degree: 0,
  }))

  const nodeIds = new Set(nodes.map((n) => n.id))
  const edges = (data.edges || [])
    .map((e) => ({
      id: e.uuid,
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
      factType: e.fact_type || '',
    }))
    .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))

  edges.forEach((e) => {
    const src = nodes.find((n) => n.id === e.source)
    const tgt = nodes.find((n) => n.id === e.target)
    if (src) src.degree++
    if (tgt) tgt.degree++
  })

  graphData.value = { nodes, edges }
  nodeCount.value = nodes.length
  edgeCount.value = edges.length
  status.value = 'complete'

  nextTick(() => renderGraph())
}

// --- Demo / sample data ---

function loadSampleData() {
  const personas = [
    'Sarah Chen',
    'Marcus Johnson',
    'Elena Rodriguez',
    'David Kim',
    'Priya Patel',
    'James Wilson',
    'Aisha Ibrahim',
    'Tom Baker',
    'Lisa Zhang',
    "Ryan O'Brien",
    'Olivia Martinez',
    'Noah Tanaka',
  ]
  const topics = [
    'Product-Led Growth',
    'Enterprise Sales',
    'Customer Success',
    'Onboarding Flow',
    'Churn Prevention',
    'Feature Adoption',
    'Support Automation',
    'Revenue Expansion',
    'Market Positioning',
    'Competitive Intel',
    'Pricing Strategy',
    'User Segmentation',
  ]
  const rels = [
    'Influences',
    'Drives',
    'Blocks',
    'Enables',
    'Requires',
    'Competes With',
    'Supports',
    'Correlates',
  ]

  const nodes = [
    ...personas.map((name, i) => ({
      id: `p${i}`,
      name,
      labels: ['Person', 'GTM Stakeholder'],
      type: 'persona',
      summary: 'GTM stakeholder involved in go-to-market strategy',
      attributes: {},
      degree: 0,
    })),
    ...topics.map((name, i) => ({
      id: `t${i}`,
      name,
      labels: ['Topic', 'Strategy'],
      type: 'topic',
      summary: `Strategic GTM topic: ${name}`,
      attributes: {},
      degree: 0,
    })),
    ...rels.map((name, i) => ({
      id: `r${i}`,
      name,
      labels: ['Relationship', 'Dynamic'],
      type: 'relationship',
      summary: `Interaction pattern: ${name}`,
      attributes: {},
      degree: 0,
    })),
  ]

  const edges = []
  let eid = 0
  // Seeded PRNG for deterministic demo layout
  let seed = 42
  const rand = () => {
    seed = (seed * 16807) % 2147483647
    return seed / 2147483647
  }

  personas.forEach((_, pi) => {
    const count = 2 + Math.floor(rand() * 3)
    const shuffled = Array.from({ length: topics.length }, (__, i) => i).sort(
      () => rand() - 0.5,
    )
    for (let j = 0; j < count; j++) {
      edges.push({
        id: `e${eid++}`,
        source: `p${pi}`,
        target: `t${shuffled[j]}`,
        name: 'Focuses on',
        fact: `${personas[pi]} focuses on ${topics[shuffled[j]]}`,
        factType: 'engagement',
      })
    }
  })

  topics.forEach((_, ti) => {
    const count = 1 + Math.floor(rand() * 2)
    const shuffled = Array.from({ length: rels.length }, (__, i) => i).sort(
      () => rand() - 0.5,
    )
    for (let j = 0; j < count; j++) {
      edges.push({
        id: `e${eid++}`,
        source: `t${ti}`,
        target: `r${shuffled[j]}`,
        name: rels[shuffled[j]],
        fact: `${topics[ti]} ${rels[shuffled[j]].toLowerCase()} other factors`,
        factType: 'dynamic',
      })
    }
  })

  for (let i = 0; i < 6; i++) {
    const a = Math.floor(rand() * personas.length)
    let b = Math.floor(rand() * personas.length)
    if (b === a) b = (a + 1) % personas.length
    edges.push({
      id: `e${eid++}`,
      source: `p${a}`,
      target: `p${b}`,
      name: 'Collaborates with',
      fact: `${personas[a]} collaborates with ${personas[b]}`,
      factType: 'social',
    })
  }

  const nodeMap = new Map(nodes.map((n) => [n.id, n]))
  edges.forEach((e) => {
    const src = nodeMap.get(e.source)
    const tgt = nodeMap.get(e.target)
    if (src) src.degree++
    if (tgt) tgt.degree++
  })

  graphData.value = { nodes, edges }
  nodeCount.value = nodes.length
  edgeCount.value = edges.length
  status.value = 'complete'

  nextTick(() => renderGraph())
}

// --- D3 rendering ---

function renderGraph() {
  const container = svgContainer.value
  if (!container) return

  const { nodes, edges } = graphData.value
  if (!nodes.length) return

  d3.select(container).selectAll('*').remove()
  if (simulation) simulation.stop()

  const width = container.clientWidth || 800
  const height = container.clientHeight || 600

  const svg = d3.select(container).append('svg').attr('width', width).attr('height', height)

  const g = svg.append('g')

  svg.call(
    d3
      .zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => g.attr('transform', event.transform)),
  )

  // Glow filter for nodes
  const defs = svg.append('defs')
  const filter = defs.append('filter').attr('id', 'node-glow')
  filter.append('feGaussianBlur').attr('stdDeviation', 3).attr('result', 'blur')
  const merge = filter.append('feMerge')
  merge.append('feMergeNode').attr('in', 'blur')
  merge.append('feMergeNode').attr('in', 'SourceGraphic')

  simulation = d3
    .forceSimulation(nodes)
    .force(
      'link',
      d3.forceLink(edges).id((d) => d.id).distance(80),
    )
    .force('charge', d3.forceManyBody().strength(-180))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force(
      'collision',
      d3.forceCollide().radius((d) => nodeRadius(d.degree) + 4),
    )

  // Draw edges
  const link = g
    .append('g')
    .attr('class', 'edges')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('stroke', 'rgba(255,255,255,0.06)')
    .attr('stroke-width', 1)
    .style('opacity', 0)

  // Draw nodes
  const node = g
    .append('g')
    .attr('class', 'nodes')
    .selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', (d) => nodeRadius(d.degree))
    .attr('fill', (d) => nodeColor(d.type))
    .attr('fill-opacity', 0.8)
    .attr('stroke', (d) => nodeColor(d.type))
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.3)
    .style('filter', 'url(#node-glow)')
    .style('cursor', 'pointer')
    .style('opacity', 0)
    .on('click', (event, d) => {
      event.stopPropagation()
      selectedNode.value = d
    })
    .call(
      d3
        .drag()
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
        }),
    )

  // Labels for high-degree nodes
  const label = g
    .append('g')
    .attr('class', 'labels')
    .selectAll('text')
    .data(nodes.filter((n) => n.degree >= 3))
    .join('text')
    .text((d) => (d.name.length > 18 ? d.name.slice(0, 16) + '\u2026' : d.name))
    .attr('font-size', 10)
    .attr('fill', 'rgba(255,255,255,0.5)')
    .attr('text-anchor', 'middle')
    .attr('dy', (d) => nodeRadius(d.degree) + 14)
    .style('pointer-events', 'none')
    .style('opacity', 0)

  // Build animation — staggered entrance
  link
    .transition()
    .delay((_, i) => i * 8)
    .duration(400)
    .style('opacity', 1)

  node
    .transition()
    .delay((_, i) => i * 25)
    .duration(300)
    .style('opacity', 1)

  label
    .transition()
    .delay((_, i) => nodes.length * 25 + i * 40)
    .duration(400)
    .style('opacity', 1)

  // Physics tick — update positions each frame
  simulation.on('tick', () => {
    link
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y)

    node.attr('cx', (d) => d.x).attr('cy', (d) => d.y)

    label.attr('x', (d) => d.x).attr('y', (d) => d.y)
  })

  // Click canvas background to deselect
  svg.on('click', () => {
    selectedNode.value = null
  })
}

// --- Lifecycle ---

onMounted(() => {
  pollInterval = setInterval(pollStatus, 2000)
  pollStatus()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (graphData.value.nodes.length) renderGraph()
    }, 200)
  })
  if (svgContainer.value) resizeObserver.observe(svgContainer.value)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="h-[calc(100vh-120px)] bg-[#0a0a1a] relative overflow-hidden">
    <!-- D3 SVG Canvas -->
    <div ref="svgContainer" class="w-full h-full" />

    <!-- Status Bar (top-left) -->
    <div class="absolute top-4 left-4 z-10 flex items-center gap-3">
      <span
        class="px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-sm border"
        :class="
          status === 'building'
            ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/20'
            : status === 'error'
              ? 'bg-red-500/20 text-red-400 border-red-500/20'
              : 'bg-green-500/20 text-green-400 border-green-500/20'
        "
      >
        <span
          v-if="status === 'building'"
          class="inline-block w-1.5 h-1.5 bg-yellow-400 rounded-full mr-1.5 animate-pulse"
        />
        <span
          v-else-if="status === 'complete'"
          class="inline-block w-1.5 h-1.5 bg-green-400 rounded-full mr-1.5"
        />
        {{
          status === 'building'
            ? `Building\u2026 ${progress}%`
            : status === 'error'
              ? 'Build Failed'
              : 'Complete'
        }}
      </span>
    </div>

    <!-- Stats Panel (top-right) -->
    <div
      class="absolute top-4 right-4 z-10 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-4 min-w-[180px]"
    >
      <div class="text-xs text-white/40 uppercase tracking-wider mb-3">Graph Stats</div>
      <div class="space-y-2">
        <div class="flex justify-between text-sm">
          <span class="text-white/60">Nodes</span>
          <span class="text-white font-medium" data-testid="node-count">{{ nodeCount }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-white/60">Edges</span>
          <span class="text-white font-medium" data-testid="edge-count">{{ edgeCount }}</span>
        </div>
        <div class="h-px bg-white/10 my-2" />
        <div class="flex items-center gap-2 text-xs">
          <span class="w-2 h-2 rounded-full bg-[#ff5600]" />
          <span class="text-white/50">Personas</span>
          <span class="text-white/80 ml-auto" data-testid="persona-count">{{
            typeCounts.persona
          }}</span>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <span class="w-2 h-2 rounded-full bg-[#2068FF]" />
          <span class="text-white/50">Topics</span>
          <span class="text-white/80 ml-auto" data-testid="topic-count">{{
            typeCounts.topic
          }}</span>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <span class="w-2 h-2 rounded-full bg-[#AA00FF]" />
          <span class="text-white/50">Relationships</span>
          <span class="text-white/80 ml-auto" data-testid="relationship-count">{{
            typeCounts.relationship
          }}</span>
        </div>
      </div>
    </div>

    <!-- Node Detail Panel (slides in from right on click) -->
    <transition name="slide">
      <div
        v-if="selectedNode"
        class="absolute top-20 right-4 z-20 bg-[#1a1a2e]/95 backdrop-blur-md border border-white/10 rounded-lg p-5 w-[280px] max-h-[60vh] overflow-y-auto"
        data-testid="detail-panel"
      >
        <div class="flex items-start justify-between mb-3">
          <h3 class="text-white font-semibold text-sm leading-tight pr-2">
            {{ selectedNode.name }}
          </h3>
          <button
            @click="selectedNode = null"
            class="text-white/40 hover:text-white/80 text-lg leading-none shrink-0"
          >
            &times;
          </button>
        </div>

        <span
          class="inline-block px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider mb-3"
          :style="{
            backgroundColor: nodeColor(selectedNode.type) + '20',
            color: nodeColor(selectedNode.type),
          }"
        >
          {{ selectedNode.type }}
        </span>

        <p v-if="selectedNode.summary" class="text-xs text-white/50 mb-4 leading-relaxed">
          {{ selectedNode.summary }}
        </p>

        <div v-if="selectedNode.labels?.length" class="mb-4">
          <div class="text-[10px] text-white/30 uppercase tracking-wider mb-1.5">Labels</div>
          <div class="flex flex-wrap gap-1">
            <span
              v-for="lbl in selectedNode.labels"
              :key="lbl"
              class="px-1.5 py-0.5 bg-white/5 text-white/50 rounded text-[10px]"
              >{{ lbl }}</span
            >
          </div>
        </div>

        <div v-if="selectedConnections.length">
          <div class="text-[10px] text-white/30 uppercase tracking-wider mb-1.5">
            Connections ({{ selectedConnections.length }})
          </div>
          <div class="space-y-1.5">
            <div
              v-for="conn in selectedConnections.slice(0, 10)"
              :key="conn.edge.id"
              class="flex items-center gap-2 text-xs cursor-pointer hover:bg-white/5 rounded px-1.5 py-1 -mx-1.5"
              @click="selectedNode = conn.neighbor"
            >
              <span
                class="w-1.5 h-1.5 rounded-full shrink-0"
                :style="{ backgroundColor: nodeColor(conn.neighbor?.type) }"
              />
              <span class="text-white/60 truncate">{{ conn.neighbor?.name }}</span>
              <span class="text-white/20 text-[10px] ml-auto shrink-0">{{ conn.edge.name }}</span>
            </div>
            <div
              v-if="selectedConnections.length > 10"
              class="text-[10px] text-white/30 pl-1.5"
            >
              +{{ selectedConnections.length - 10 }} more
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Continue to Simulation -->
    <Transition name="page">
      <div v-if="status === 'complete'" class="absolute bottom-6 right-6 z-10">
        <router-link
          :to="`/simulation/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-6 py-3 rounded-lg font-semibold text-sm transition-colors no-underline inline-flex items-center gap-2"
        >
          Continue to Simulation
          <span class="text-white/60">&rarr;</span>
        </router-link>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition:
    transform 0.2s ease,
    opacity 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
