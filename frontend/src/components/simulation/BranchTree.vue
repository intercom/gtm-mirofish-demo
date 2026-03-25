<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as d3 from 'd3'

const props = defineProps({
  treeData: { type: Object, default: null },
  simulationId: { type: String, default: '' },
})

const emit = defineEmits(['select-node'])

const router = useRouter()
const containerRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// Outcome → color mapping using brand tokens
const OUTCOME_COLORS = {
  positive: '#009900',
  neutral: '#2068FF',
  negative: '#ff5600',
  running: '#AA00FF',
  pending: '#888',
}

const STATUS_LABELS = {
  completed: 'Done',
  running: 'Running',
  pending: 'Pending',
  failed: 'Failed',
}

// Demo data matching expected API shape from GET /api/simulation/<id>/branch-tree
const DEMO_TREE = {
  id: 'sim-root',
  label: 'Enterprise GTM Launch',
  round: 0,
  status: 'completed',
  outcome: 'neutral',
  metrics: { engagement: 64, conversion: 12 },
  children: [
    {
      id: 'sim-branch-a',
      label: 'Added Finance Persona',
      branchRound: 5,
      modification: 'Added finance decision-maker agent',
      status: 'completed',
      outcome: 'positive',
      metrics: { engagement: 85, conversion: 22 },
      children: [
        {
          id: 'sim-branch-a1',
          label: 'Price Reduction',
          branchRound: 8,
          modification: 'Reduced pricing by 20%',
          status: 'completed',
          outcome: 'positive',
          metrics: { engagement: 91, conversion: 28 },
          children: [],
        },
        {
          id: 'sim-branch-a2',
          label: 'Premium Positioning',
          branchRound: 8,
          modification: 'Emphasized ROI messaging',
          status: 'completed',
          outcome: 'neutral',
          metrics: { engagement: 78, conversion: 18 },
          children: [],
        },
      ],
    },
    {
      id: 'sim-branch-b',
      label: 'Competitor Event Injected',
      branchRound: 3,
      modification: 'Injected competitor launch event',
      status: 'completed',
      outcome: 'negative',
      metrics: { engagement: 42, conversion: 6 },
      children: [],
    },
    {
      id: 'sim-branch-c',
      label: 'Extended to 20 Rounds',
      branchRound: 10,
      modification: 'Extended simulation duration',
      status: 'running',
      outcome: 'neutral',
      metrics: { engagement: 70, conversion: 14 },
      children: [],
    },
  ],
}

const activeTree = computed(() => props.treeData || DEMO_TREE)
const isDemo = computed(() => !props.treeData)

// Track collapsed node IDs
const collapsedIds = ref(new Set())

function toggleCollapse(nodeId) {
  const next = new Set(collapsedIds.value)
  if (next.has(nodeId)) {
    next.delete(nodeId)
  } else {
    next.add(nodeId)
  }
  collapsedIds.value = next
}

// Build a pruned copy of the tree that hides collapsed children
function pruneTree(node) {
  const copy = { ...node }
  if (collapsedIds.value.has(node.id) || !node.children?.length) {
    copy.children = []
    copy._childCount = node.children?.length || 0
  } else {
    copy.children = node.children.map(pruneTree)
    copy._childCount = 0
  }
  return copy
}

// --- D3 Rendering ---

function clearChart() {
  if (containerRef.value) {
    d3.select(containerRef.value).selectAll('*').remove()
  }
}

function renderTree() {
  clearChart()
  const container = containerRef.value
  if (!container) return

  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight || 400
  if (containerWidth === 0) return

  const data = pruneTree(activeTree.value)
  const root = d3.hierarchy(data)

  // Count leaf nodes to size the tree height
  const leafCount = root.leaves().length
  const nodeSpacingY = 80
  const treeHeight = Math.max(leafCount * nodeSpacingY, 200)
  const margin = { top: 20, right: 180, bottom: 20, left: 40 }
  const width = containerWidth - margin.left - margin.right
  const height = Math.max(treeHeight, containerHeight - margin.top - margin.bottom)

  const treeLayout = d3.tree().size([height, width])
  treeLayout(root)

  const svgHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', svgHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${svgHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // --- Links (edges) ---
  const linkGenerator = d3.linkHorizontal()
    .x(d => d.y)
    .y(d => d.x)

  const links = g.selectAll('.link')
    .data(root.links())
    .join('path')
    .attr('class', 'link')
    .attr('d', linkGenerator)
    .attr('fill', 'none')
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.15))')
    .attr('stroke-width', 2)
    .attr('stroke-opacity', 0)

  links.transition()
    .duration(500)
    .attr('stroke-opacity', 1)

  // --- Edge labels (modification text) ---
  g.selectAll('.edge-label')
    .data(root.links().filter(l => l.target.data.modification))
    .join('text')
    .attr('class', 'edge-label')
    .attr('x', d => (d.source.y + d.target.y) / 2)
    .attr('y', d => (d.source.x + d.target.x) / 2 - 8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => truncateLabel(d.target.data.modification, 30))
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay(200)
    .style('opacity', 1)

  // --- Nodes ---
  const nodeWidth = 160
  const nodeHeight = 56

  const nodes = g.selectAll('.node')
    .data(root.descendants())
    .join('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.y - nodeWidth / 2},${d.x - nodeHeight / 2})`)
    .style('cursor', 'pointer')
    .style('opacity', 0)

  nodes.transition()
    .duration(400)
    .delay((_, i) => i * 60)
    .style('opacity', 1)

  // Node background rect
  nodes.append('rect')
    .attr('width', nodeWidth)
    .attr('height', nodeHeight)
    .attr('rx', 10)
    .attr('ry', 10)
    .attr('fill', 'var(--color-surface, #fff)')
    .attr('stroke', d => {
      if (d.data.id === props.simulationId) return 'var(--color-primary, #2068FF)'
      return 'var(--color-border, rgba(0,0,0,0.12))'
    })
    .attr('stroke-width', d => d.data.id === props.simulationId ? 2 : 1)

  // Outcome indicator dot
  nodes.append('circle')
    .attr('cx', 16)
    .attr('cy', nodeHeight / 2)
    .attr('r', 5)
    .attr('fill', d => OUTCOME_COLORS[d.data.outcome] || OUTCOME_COLORS.pending)

  // Node label
  nodes.append('text')
    .attr('x', 28)
    .attr('y', 20)
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text, #050505)')
    .text(d => truncateLabel(d.data.label, 16))

  // Round badge + status
  nodes.append('text')
    .attr('x', 28)
    .attr('y', 36)
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => {
      const round = d.data.branchRound != null ? `R${d.data.branchRound}` : 'Root'
      const status = STATUS_LABELS[d.data.status] || ''
      return `${round} · ${status}`
    })

  // Metrics (engagement/conversion) for leaf nodes
  nodes.filter(d => d.data.metrics && !d.data.children?.length && !d.data._childCount)
    .append('text')
    .attr('x', 28)
    .attr('y', 50)
    .attr('font-size', '9px')
    .attr('fill', d => OUTCOME_COLORS[d.data.outcome] || '#888')
    .text(d => {
      const m = d.data.metrics
      return `${m.engagement}% eng · ${m.conversion}% conv`
    })

  // Collapse/expand indicator for nodes with children
  nodes.filter(d => (d.data._childCount > 0) || (d.data.children?.length > 0 && d.depth > 0))
    .append('g')
    .attr('transform', `translate(${nodeWidth - 18}, ${nodeHeight / 2})`)
    .each(function (d) {
      const el = d3.select(this)
      const isCollapsed = collapsedIds.value.has(d.data.id)
      el.append('circle')
        .attr('r', 9)
        .attr('fill', 'var(--color-tint, rgba(0,0,0,0.04))')
        .attr('stroke', 'var(--color-border, rgba(0,0,0,0.12))')
        .attr('stroke-width', 1)
      el.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('font-size', '11px')
        .attr('fill', 'var(--color-text-secondary, #555)')
        .text(isCollapsed ? `+${d.data._childCount}` : '−')
    })

  // --- Tooltip ---
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
    .style('z-index', '10')
    .style('max-width', '240px')

  // --- Interaction handlers ---
  nodes
    .on('mouseenter', (event, d) => {
      const n = d.data
      const outcomeColor = OUTCOME_COLORS[n.outcome] || '#888'
      let metricsHtml = ''
      if (n.metrics) {
        metricsHtml = `
          <div style="display:flex;gap:12px;margin-top:6px;font-size:11px">
            <span><strong>${n.metrics.engagement}%</strong> engagement</span>
            <span><strong>${n.metrics.conversion}%</strong> conversion</span>
          </div>`
      }
      let modHtml = ''
      if (n.modification) {
        modHtml = `<div style="color:var(--color-text-muted,#888);margin-top:4px;font-size:11px;font-style:italic">"${n.modification}"</div>`
      }
      tooltip.html(`
        <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">${n.label}</div>
        <div style="display:flex;align-items:center;gap:6px">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${outcomeColor}"></span>
          <span style="color:${outcomeColor};font-weight:500;text-transform:capitalize">${n.outcome || 'unknown'}</span>
          <span style="color:var(--color-text-muted,#888)">· ${n.branchRound != null ? 'Round ' + n.branchRound : 'Origin'}</span>
        </div>
        ${modHtml}
        ${metricsHtml}
      `).style('opacity', 1)

      d3.select(event.currentTarget).select('rect')
        .transition().duration(150)
        .attr('stroke', 'var(--color-primary, #2068FF)')
        .attr('stroke-width', 2)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 16}px`)
        .style('top', `${event.clientY - rect.top - 12}px`)
    })
    .on('mouseleave', (event, d) => {
      tooltip.style('opacity', 0)
      const isCurrent = d.data.id === props.simulationId
      d3.select(event.currentTarget).select('rect')
        .transition().duration(150)
        .attr('stroke', isCurrent ? 'var(--color-primary, #2068FF)' : 'var(--color-border, rgba(0,0,0,0.12))')
        .attr('stroke-width', isCurrent ? 2 : 1)
    })
    .on('click', (event, d) => {
      // Check if click is on the collapse toggle
      const collapseBtn = d3.select(event.currentTarget).select('g')
      if (!collapseBtn.empty() && event.target.closest('g') === collapseBtn.node()) {
        toggleCollapse(d.data.id)
        return
      }
      emit('select-node', d.data)
      navigateToSimulation(d.data.id)
    })
}

function navigateToSimulation(simId) {
  if (!simId || simId === props.simulationId) return
  router.push({ name: 'workspace', params: { taskId: simId } })
}

function truncateLabel(str, max = 20) {
  if (!str || str.length <= max) return str || ''
  return str.slice(0, max) + '…'
}

// --- Lifecycle ---

watch([activeTree, collapsedIds], () => {
  nextTick(() => renderTree())
}, { deep: true })

onMounted(() => {
  renderTree()
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderTree, 200)
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Branch Tree</h3>
        <span
          v-if="isDemo"
          class="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)] font-medium"
        >
          Demo
        </span>
      </div>
      <div class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-[#009900]" /> Positive
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-[#2068FF]" /> Neutral
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-[#ff5600]" /> Negative
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-[#AA00FF]" /> Running
        </span>
      </div>
    </div>

    <div
      ref="containerRef"
      class="relative overflow-x-auto"
      style="min-height: 300px"
    />
  </div>
</template>
