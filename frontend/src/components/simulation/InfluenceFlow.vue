<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
const currentRound = ref(0)
const isPlaying = ref(false)
const selectedNodeId = ref(null)
let resizeObserver = null
let resizeTimer = null
let sim = null
let playTimer = null

const INFLUENCE_TYPES = {
  reply: { color: '#2068FF', label: 'Opinion Change' },
  topic_adoption: { color: '#ff5600', label: 'Topic Adoption' },
  sentiment_alignment: { color: '#009900', label: 'Sentiment Alignment' },
}

function shortName(fullName) {
  if (!fullName) return '?'
  return fullName.split(',')[0].trim()
}

function personaType(fullName) {
  const lower = (fullName || '').toLowerCase()
  if (lower.includes('vp') || lower.includes('director') || lower.includes('head')) return 'leader'
  if (lower.includes('manager') || lower.includes('lead')) return 'manager'
  return 'contributor'
}

function addEdge(map, source, target, type, round, weight) {
  const key = `${source}→${target}→${type}`
  if (!map.has(key)) {
    map.set(key, { source, target, type, weight: 0, rounds: [] })
  }
  const e = map.get(key)
  e.weight += weight
  if (!e.rounds.includes(round)) e.rounds.push(round)
}

// Derive influence graph from actions
const influenceGraph = computed(() => {
  if (!props.actions.length) return { nodes: [], edges: [], maxRound: 0 }

  const agentMap = new Map()
  const edgeMap = new Map()
  let maxRound = 0

  const roundActions = new Map()
  for (const action of props.actions) {
    const round = action.round_num
    if (round == null) continue
    maxRound = Math.max(maxRound, round)

    if (!roundActions.has(round)) roundActions.set(round, [])
    roundActions.get(round).push(action)

    const agentId = action.agent_name || `Agent #${action.agent_id}`
    if (!agentMap.has(agentId)) {
      agentMap.set(agentId, {
        id: agentId,
        name: shortName(agentId),
        influence_score: 0,
        direct_influence: 0,
        indirect_influence: 0,
        action_count: 0,
        persona_type: personaType(agentId),
      })
    }
    agentMap.get(agentId).action_count++
  }

  // Build edges: posters influence repliers, engagers, sharers
  for (const [round, actions] of roundActions) {
    const classify = (a) => (a.action_type || '').toUpperCase()
    const posters = actions.filter(a => {
      const t = classify(a)
      return t.includes('POST') || t.includes('THREAD')
    })
    const repliers = actions.filter(a => {
      const t = classify(a)
      return t.includes('REPLY') || t.includes('COMMENT')
    })
    const engagers = actions.filter(a => {
      const t = classify(a)
      return t.includes('LIKE') || t.includes('UPVOTE')
    })
    const sharers = actions.filter(a => {
      const t = classify(a)
      return t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')
    })

    if (!posters.length) continue

    for (let i = 0; i < repliers.length; i++) {
      const src = posters[i % posters.length]
      const tgt = repliers[i]
      const srcId = src.agent_name || `Agent #${src.agent_id}`
      const tgtId = tgt.agent_name || `Agent #${tgt.agent_id}`
      if (srcId !== tgtId) addEdge(edgeMap, srcId, tgtId, 'reply', round, 3)
    }

    for (let i = 0; i < engagers.length; i++) {
      const src = posters[i % posters.length]
      const tgt = engagers[i]
      const srcId = src.agent_name || `Agent #${src.agent_id}`
      const tgtId = tgt.agent_name || `Agent #${tgt.agent_id}`
      if (srcId !== tgtId) addEdge(edgeMap, srcId, tgtId, 'sentiment_alignment', round, 1)
    }

    for (let i = 0; i < sharers.length; i++) {
      const src = posters[i % posters.length]
      const tgt = sharers[i]
      const srcId = src.agent_name || `Agent #${src.agent_id}`
      const tgtId = tgt.agent_name || `Agent #${tgt.agent_id}`
      if (srcId !== tgtId) addEdge(edgeMap, srcId, tgtId, 'topic_adoption', round, 2)
    }
  }

  // Compute influence scores
  const directMap = new Map()
  for (const edge of edgeMap.values()) {
    if (!directMap.has(edge.source)) directMap.set(edge.source, new Set())
    directMap.get(edge.source).add(edge.target)
  }

  for (const [id, targets] of directMap) {
    if (agentMap.has(id)) agentMap.get(id).direct_influence = targets.size
  }

  for (const [id, targets] of directMap) {
    const indirect = new Set()
    for (const t of targets) {
      const second = directMap.get(t)
      if (second) {
        for (const s of second) {
          if (s !== id && !targets.has(s)) indirect.add(s)
        }
      }
    }
    if (agentMap.has(id)) agentMap.get(id).indirect_influence = indirect.size
  }

  for (const agent of agentMap.values()) {
    agent.influence_score = agent.direct_influence + agent.indirect_influence * 0.5
  }

  return {
    nodes: Array.from(agentMap.values()),
    edges: Array.from(edgeMap.values()),
    maxRound,
  }
})

// Edges visible at current round (0 = show all)
const visibleEdges = computed(() => {
  if (currentRound.value === 0) return influenceGraph.value.edges
  return influenceGraph.value.edges.filter(e =>
    e.rounds.some(r => r <= currentRound.value)
  )
})

// Find chain from a selected node (BFS outgoing, max depth 3)
const influenceChain = computed(() => {
  if (!selectedNodeId.value) return new Set()
  const chain = new Set([selectedNodeId.value])
  let frontier = [selectedNodeId.value]
  for (let depth = 0; depth < 3 && frontier.length; depth++) {
    const next = []
    for (const nodeId of frontier) {
      for (const edge of influenceGraph.value.edges) {
        if (edge.source === nodeId && !chain.has(edge.target)) {
          chain.add(edge.target)
          next.push(edge.target)
        }
      }
    }
    frontier = next
  }
  return chain
})

// Top influencers for the summary panel
const topInfluencers = computed(() => {
  return [...influenceGraph.value.nodes]
    .sort((a, b) => b.influence_score - a.influence_score)
    .slice(0, 5)
})

// --- D3 Rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  if (sim) { sim.stop(); sim = null }

  const container = chartRef.value
  if (!container) return
  const { nodes, edges } = influenceGraph.value
  if (!nodes.length) return

  const width = container.clientWidth
  const height = container.clientHeight || 340
  if (width === 0) return

  const maxScore = Math.max(...nodes.map(n => n.influence_score), 1)
  const radiusScale = d3.scaleSqrt().domain([0, maxScore]).range([8, 28])
  const edgeWidthScale = d3.scaleLinear()
    .domain([0, Math.max(...edges.map(e => e.weight), 1)])
    .range([1, 5])

  // Deep-clone nodes/edges for D3 mutation
  const simNodes = nodes.map(n => ({ ...n }))
  const nodeIndex = new Map(simNodes.map(n => [n.id, n]))
  const simEdges = edges.map(e => ({
    ...e,
    source: nodeIndex.get(e.source) || e.source,
    target: nodeIndex.get(e.target) || e.target,
  }))

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  // Arrow markers per influence type
  const defs = svg.append('defs')
  for (const [type, cfg] of Object.entries(INFLUENCE_TYPES)) {
    defs.append('marker')
      .attr('id', `arrow-${type}`)
      .attr('viewBox', '0 -4 8 8')
      .attr('refX', 12)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-4L8,0L0,4Z')
      .attr('fill', cfg.color)
  }

  // Zoom group
  const g = svg.append('g')
  svg.call(
    d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => g.attr('transform', event.transform))
  )

  // Edges
  const edgeGroup = g.append('g').attr('class', 'edges')
  const edgeElements = edgeGroup.selectAll('line')
    .data(simEdges)
    .join('line')
    .attr('stroke', d => INFLUENCE_TYPES[d.type]?.color || '#ccc')
    .attr('stroke-width', d => edgeWidthScale(d.weight))
    .attr('stroke-opacity', 0.5)
    .attr('marker-end', d => `url(#arrow-${d.type})`)

  // Node groups
  const nodeGroup = g.append('g').attr('class', 'nodes')
  const nodeElements = nodeGroup.selectAll('g')
    .data(simNodes)
    .join('g')
    .attr('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) sim.alphaTarget(0)
        d.fx = null
        d.fy = null
      })
    )

  // Node circles
  nodeElements.append('circle')
    .attr('r', d => radiusScale(d.influence_score))
    .attr('fill', d => {
      if (d.persona_type === 'leader') return '#2068FF'
      if (d.persona_type === 'manager') return '#ff5600'
      return '#AA00FF'
    })
    .attr('fill-opacity', 0.15)
    .attr('stroke', d => {
      if (d.persona_type === 'leader') return '#2068FF'
      if (d.persona_type === 'manager') return '#ff5600'
      return '#AA00FF'
    })
    .attr('stroke-width', 2)

  // Node labels
  nodeElements.append('text')
    .text(d => d.name)
    .attr('text-anchor', 'middle')
    .attr('dy', d => radiusScale(d.influence_score) + 14)
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-secondary, #555)')
    .attr('pointer-events', 'none')

  // Tooltip
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '10px 14px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '20')
    .style('max-width', '220px')

  // Node interactions
  nodeElements
    .on('mouseenter', (event, d) => {
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">${d.name}</div>
          <div style="font-size:11px;color:var(--color-text-muted,#888);margin-bottom:6px">${d.id.split(',').slice(1).join(',').trim() || ''}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;font-size:11px">
            <span style="color:var(--color-text-muted,#888)">Influence</span>
            <span style="font-weight:600;color:var(--color-text,#050505)">${d.influence_score.toFixed(1)}</span>
            <span style="color:var(--color-text-muted,#888)">Direct</span>
            <span style="color:#2068FF;font-weight:500">${d.direct_influence}</span>
            <span style="color:var(--color-text-muted,#888)">Indirect</span>
            <span style="color:#ff5600;font-weight:500">${d.indirect_influence}</span>
            <span style="color:var(--color-text-muted,#888)">Actions</span>
            <span>${d.action_count}</span>
          </div>
        `)
        .style('opacity', 1)

      nodeElements.select('circle')
        .transition().duration(150)
        .attr('fill-opacity', n => n.id === d.id ? 0.3 : 0.08)
        .attr('stroke-opacity', n => n.id === d.id ? 1 : 0.3)

      edgeElements
        .transition().duration(150)
        .attr('stroke-opacity', e =>
          (e.source.id || e.source) === d.id || (e.target.id || e.target) === d.id ? 0.8 : 0.1
        )
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 10}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
      nodeElements.select('circle')
        .transition().duration(150)
        .attr('fill-opacity', 0.15)
        .attr('stroke-opacity', 1)
      edgeElements
        .transition().duration(150)
        .attr('stroke-opacity', 0.5)
    })
    .on('click', (event, d) => {
      event.stopPropagation()
      selectedNodeId.value = selectedNodeId.value === d.id ? null : d.id
    })

  // Click background to deselect
  svg.on('click', () => { selectedNodeId.value = null })

  // Force simulation
  sim = d3.forceSimulation(simNodes)
    .force('link', d3.forceLink(simEdges).id(d => d.id).distance(100).strength(0.4))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(d => radiusScale(d.influence_score) + 10))
    .alphaDecay(0.02)
    .on('tick', () => {
      edgeElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => {
          const r = radiusScale(d.target.influence_score)
          const dx = d.target.x - d.source.x
          const dy = d.target.y - d.source.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          return d.target.x - (dx / dist) * (r + 4)
        })
        .attr('y2', d => {
          const r = radiusScale(d.target.influence_score)
          const dx = d.target.x - d.source.x
          const dy = d.target.y - d.source.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          return d.target.y - (dy / dist) * (r + 4)
        })

      nodeElements.attr('transform', d => `translate(${d.x},${d.y})`)
    })

  // Update edge visibility when round changes
  watch([currentRound, selectedNodeId], () => {
    const round = currentRound.value
    const chain = influenceChain.value
    const hasSelection = !!selectedNodeId.value

    edgeElements
      .attr('stroke-opacity', d => {
        const visible = round === 0 || d.rounds.some(r => r <= round)
        if (!visible) return 0
        if (hasSelection) {
          const srcId = d.source.id || d.source
          const tgtId = d.target.id || d.target
          return chain.has(srcId) && chain.has(tgtId) ? 0.8 : 0.08
        }
        return 0.5
      })

    nodeElements.select('circle')
      .attr('fill-opacity', d => {
        if (hasSelection) return chain.has(d.id) ? 0.25 : 0.04
        return 0.15
      })
      .attr('stroke-opacity', d => {
        if (hasSelection) return chain.has(d.id) ? 1 : 0.2
        return 1
      })

    nodeElements.select('text')
      .attr('fill-opacity', d => {
        if (hasSelection) return chain.has(d.id) ? 1 : 0.25
        return 1
      })
  }, { immediate: true })
}

// --- Playback ---

function togglePlay() {
  if (isPlaying.value) {
    stopPlay()
  } else {
    const max = influenceGraph.value.maxRound
    if (!max) return
    if (currentRound.value >= max) currentRound.value = 0
    isPlaying.value = true
    playTimer = setInterval(() => {
      if (currentRound.value >= max) {
        stopPlay()
        return
      }
      currentRound.value++
    }, 800)
  }
}

function stopPlay() {
  isPlaying.value = false
  if (playTimer) { clearInterval(playTimer); playTimer = null }
}

// --- Lifecycle ---

watch(() => props.actions.length, () => {
  nextTick(() => renderChart())
})

onMounted(() => {
  if (influenceGraph.value.maxRound) {
    currentRound.value = 0
  }
  renderChart()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderChart, 200)
    })
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
  stopPlay()
  if (sim) { sim.stop(); sim = null }
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Influence Flow</h3>
      <div v-if="influenceGraph.maxRound" class="flex items-center gap-3">
        <!-- Play/pause -->
        <button
          class="w-7 h-7 flex items-center justify-center rounded-md border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-text-secondary)] transition-colors"
          :title="isPlaying ? 'Pause' : 'Play propagation'"
          @click="togglePlay"
        >
          <svg v-if="!isPlaying" width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <path d="M2 1l9 5-9 5z" />
          </svg>
          <svg v-else width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <rect x="1" y="1" width="3.5" height="10" rx="0.5" />
            <rect x="7.5" y="1" width="3.5" height="10" rx="0.5" />
          </svg>
        </button>
        <!-- Round slider -->
        <div class="flex items-center gap-2">
          <span class="text-[11px] text-[var(--color-text-muted)] whitespace-nowrap">
            {{ currentRound === 0 ? 'All rounds' : `Round ${currentRound}` }}
          </span>
          <input
            type="range"
            :min="0"
            :max="influenceGraph.maxRound"
            v-model.number="currentRound"
            class="w-20 h-1 accent-[var(--color-primary)]"
            @input="stopPlay()"
          />
        </div>
      </div>
    </div>

    <!-- Chart -->
    <div
      v-if="influenceGraph.nodes.length"
      ref="chartRef"
      class="relative"
      style="height: 340px"
    />

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      <span>Influence data will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="influenceGraph.nodes.length" class="flex flex-wrap items-center gap-x-5 gap-y-2 mt-4">
      <div class="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
        <span class="font-medium text-[var(--color-text-secondary)]">Edges:</span>
        <span v-for="(cfg, key) in INFLUENCE_TYPES" :key="key" class="flex items-center gap-1.5">
          <span class="inline-block w-4 h-0.5 rounded" :style="{ backgroundColor: cfg.color }" />
          {{ cfg.label }}
        </span>
      </div>
      <div class="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
        <span class="font-medium text-[var(--color-text-secondary)]">Nodes:</span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full border-2 border-[#2068FF]" /> Leader
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full border-2 border-[#ff5600]" /> Manager
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full border-2 border-[#AA00FF]" /> Contributor
        </span>
      </div>
    </div>

    <!-- Top influencers summary -->
    <div v-if="topInfluencers.length" class="mt-4 pt-4 border-t border-[var(--color-border)]">
      <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Key Influencers</h4>
      <div class="grid grid-cols-1 sm:grid-cols-5 gap-2">
        <div
          v-for="(agent, idx) in topInfluencers"
          :key="agent.id"
          class="flex items-center gap-2 px-3 py-2 rounded-md transition-colors cursor-pointer"
          :class="selectedNodeId === agent.id
            ? 'bg-[rgba(32,104,255,0.08)] border border-[var(--color-primary)]'
            : 'bg-[var(--color-tint)] border border-transparent hover:border-[var(--color-border)]'"
          @click="selectedNodeId = selectedNodeId === agent.id ? null : agent.id"
        >
          <span class="text-sm font-semibold text-[var(--color-primary)] w-5 shrink-0">#{{ idx + 1 }}</span>
          <div class="min-w-0 flex-1">
            <div class="text-xs font-medium text-[var(--color-text)] truncate">{{ agent.name }}</div>
            <div class="text-[10px] text-[var(--color-text-muted)]">
              {{ agent.direct_influence }} direct · {{ agent.indirect_influence }} indirect
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
