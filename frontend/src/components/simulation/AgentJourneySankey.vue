<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { sankey as d3Sankey, sankeyLinkHorizontal, sankeyCenter } from 'd3-sankey'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const ACTION_CATEGORIES = {
  observe: { label: 'Observe', types: ['LIKE', 'LIKE_POST', 'UPVOTE'], color: '#2068FF', depth: 0 },
  discuss: { label: 'Discuss', types: ['REPLY', 'COMMENT'], color: '#ff5600', depth: 1 },
  create: { label: 'Create', types: ['CREATE_POST', 'CREATE_THREAD'], color: '#AA00FF', depth: 2 },
  amplify: { label: 'Amplify', types: ['REPOST', 'RETWEET', 'SHARE'], color: '#009900', depth: 3 },
}

function categorizeAction(actionType) {
  const t = (actionType || '').toUpperCase()
  for (const [key, cat] of Object.entries(ACTION_CATEGORIES)) {
    if (cat.types.some(type => t.includes(type))) return key
  }
  return 'observe'
}

const sankeyData = computed(() => {
  if (!props.actions.length) return null

  const agentJourneys = new Map()

  for (const action of props.actions) {
    const agentKey = action.agent_name || action.agent_id
    if (!agentJourneys.has(agentKey)) {
      agentJourneys.set(agentKey, [])
    }
    agentJourneys.get(agentKey).push({
      round: action.round_num,
      category: categorizeAction(action.action_type),
    })
  }

  if (agentJourneys.size === 0) return null

  // For each agent, determine: first action, dominant action, last action
  const stages = { first: new Map(), dominant: new Map(), last: new Map() }
  const flows = { entry_to_first: new Map(), first_to_dominant: new Map(), dominant_to_last: new Map() }

  for (const [agent, actions] of agentJourneys) {
    actions.sort((a, b) => a.round - b.round)

    const first = actions[0].category
    const last = actions[actions.length - 1].category

    // Dominant = most frequent category
    const counts = {}
    for (const a of actions) {
      counts[a.category] = (counts[a.category] || 0) + 1
    }
    const dominant = Object.entries(counts).sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1]
      return ACTION_CATEGORIES[b[0]].depth - ACTION_CATEGORIES[a[0]].depth
    })[0][0]

    // Count flows
    const e2f = `entry-${first}`
    flows.entry_to_first.set(e2f, (flows.entry_to_first.get(e2f) || 0) + 1)

    const f2d = `first:${first}-dominant:${dominant}`
    flows.first_to_dominant.set(f2d, (flows.first_to_dominant.get(f2d) || 0) + 1)

    const d2l = `dominant:${dominant}-last:${last}`
    flows.dominant_to_last.set(d2l, (flows.dominant_to_last.get(d2l) || 0) + 1)
  }

  // Build nodes
  const nodeMap = new Map()
  const addNode = (id, label, column, color) => {
    if (!nodeMap.has(id)) {
      nodeMap.set(id, { id, label, column, color })
    }
  }

  addNode('entry', `All Agents (${agentJourneys.size})`, 0, '#666')

  const categories = Object.keys(ACTION_CATEGORIES)

  for (const cat of categories) {
    addNode(`first:${cat}`, ACTION_CATEGORIES[cat].label, 1, ACTION_CATEGORIES[cat].color)
    addNode(`dominant:${cat}`, ACTION_CATEGORIES[cat].label, 2, ACTION_CATEGORIES[cat].color)
    addNode(`last:${cat}`, ACTION_CATEGORIES[cat].label, 3, ACTION_CATEGORIES[cat].color)
  }

  // Build links
  const links = []

  for (const [key, value] of flows.entry_to_first) {
    const cat = key.replace('entry-', '')
    links.push({ source: 'entry', target: `first:${cat}`, value })
  }
  for (const [key, value] of flows.first_to_dominant) {
    const [src, tgt] = key.split('-')
    links.push({ source: src, target: tgt, value })
  }
  for (const [key, value] of flows.dominant_to_last) {
    const [src, tgt] = key.split('-')
    links.push({ source: src, target: tgt, value })
  }

  // Only include nodes that have at least one connected link
  const connectedIds = new Set()
  for (const link of links) {
    connectedIds.add(link.source)
    connectedIds.add(link.target)
  }

  const nodes = Array.from(nodeMap.values()).filter(n => connectedIds.has(n.id))

  if (nodes.length < 2 || links.length === 0) return null

  return { nodes, links }
})

const columnLabels = ['Entry', 'First Action', 'Primary Behavior', 'Exit Action']

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !sankeyData.value) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 24, right: 20, bottom: 12, left: 20 }
  const width = containerWidth - margin.left - margin.right
  const height = 320
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Column headers
  const colWidth = width / (columnLabels.length - 1 + 0.3)
  for (let i = 0; i < columnLabels.length; i++) {
    const x = i === 0 ? 8 : i * colWidth
    g.append('text')
      .attr('x', x)
      .attr('y', -10)
      .attr('text-anchor', i === 0 ? 'start' : 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', 'var(--color-text-muted, #888)')
      .text(columnLabels[i])
  }

  // Prepare data for d3-sankey (must use numeric indices)
  const nodesData = sankeyData.value.nodes.map(n => ({ ...n }))
  const nodeIdToIndex = new Map(nodesData.map((n, i) => [n.id, i]))

  const linksData = sankeyData.value.links
    .filter(l => nodeIdToIndex.has(l.source) && nodeIdToIndex.has(l.target))
    .map(l => ({
      source: nodeIdToIndex.get(l.source),
      target: nodeIdToIndex.get(l.target),
      value: l.value,
    }))

  if (linksData.length === 0) return

  const sankeyLayout = d3Sankey()
    .nodeId(d => d.index)
    .nodeWidth(16)
    .nodePadding(14)
    .nodeAlign(sankeyCenter)
    .extent([[0, 0], [width, height]])

  const { nodes, links } = sankeyLayout({
    nodes: nodesData.map((n, i) => ({ ...n, index: i })),
    links: linksData,
  })

  // Defs for link gradients
  const defs = svg.append('defs')

  // Draw links
  const linkGroup = g.append('g')
    .attr('fill', 'none')
    .attr('stroke-opacity', 0.35)

  const linkPaths = linkGroup.selectAll('path')
    .data(links)
    .join('path')
    .attr('d', sankeyLinkHorizontal())
    .attr('stroke-width', d => Math.max(1, d.width))
    .each(function (d, i) {
      const gradientId = `link-gradient-${i}`
      const gradient = defs.append('linearGradient')
        .attr('id', gradientId)
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', d.source.x1)
        .attr('x2', d.target.x0)

      gradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', nodesData[d.source.index]?.color || '#888')

      gradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', nodesData[d.target.index]?.color || '#888')

      d3.select(this).attr('stroke', `url(#${gradientId})`)
    })
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((_, i) => i * 30)
    .style('opacity', 1)

  // Draw nodes
  const nodeGroup = g.append('g')

  nodeGroup.selectAll('rect')
    .data(nodes)
    .join('rect')
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('height', d => Math.max(1, d.y1 - d.y0))
    .attr('fill', d => nodesData[d.index]?.color || '#888')
    .attr('rx', 3)
    .attr('opacity', 0)
    .transition()
    .duration(400)
    .delay((_, i) => i * 50)
    .attr('opacity', 0.9)

  // Node labels
  nodeGroup.selectAll('text')
    .data(nodes)
    .join('text')
    .attr('x', d => {
      if (d.x0 < width / 2) return d.x1 + 8
      return d.x0 - 8
    })
    .attr('y', d => (d.y0 + d.y1) / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', d => d.x0 < width / 2 ? 'start' : 'end')
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text-secondary, #555)')
    .text(d => {
      const node = nodesData[d.index]
      const totalValue = d.value || 0
      return `${node?.label || ''} (${totalValue})`
    })
    .attr('opacity', 0)
    .transition()
    .duration(400)
    .delay((_, i) => 200 + i * 50)
    .attr('opacity', 1)

  // Tooltip
  const tooltip = d3.select(container)
    .append('div')
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
    .style('max-width', '220px')

  // Link hover
  linkGroup.selectAll('path')
    .on('mouseenter', function (event, d) {
      d3.select(this)
        .transition().duration(100)
        .attr('stroke-opacity', 0.6)

      const src = nodesData[d.source.index]
      const tgt = nodesData[d.target.index]
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">
            ${src?.label || '?'} → ${tgt?.label || '?'}
          </div>
          <div style="color:var(--color-text-secondary,#555)">
            ${d.value} agent${d.value !== 1 ? 's' : ''}
          </div>
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', function () {
      d3.select(this)
        .transition().duration(100)
        .attr('stroke-opacity', 0.35)
      tooltip.style('opacity', 0)
    })

  // Node hover
  nodeGroup.selectAll('rect')
    .on('mouseenter', function (event, d) {
      d3.select(this)
        .transition().duration(100)
        .attr('opacity', 1)

      const node = nodesData[d.index]
      const inbound = links.filter(l => l.target.index === d.index).reduce((s, l) => s + l.value, 0)
      const outbound = links.filter(l => l.source.index === d.index).reduce((s, l) => s + l.value, 0)

      tooltip
        .html(`
          <div style="font-weight:600;color:${node?.color || '#050505'};margin-bottom:4px">
            ${node?.label || '?'}
          </div>
          <div style="color:var(--color-text-secondary,#555)">
            ${d.value || 0} agent${(d.value || 0) !== 1 ? 's' : ''}
          </div>
          ${inbound ? `<div style="color:var(--color-text-muted,#888);font-size:11px;margin-top:2px">← ${inbound} inbound</div>` : ''}
          ${outbound ? `<div style="color:var(--color-text-muted,#888);font-size:11px;margin-top:1px">→ ${outbound} outbound</div>` : ''}
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', function () {
      d3.select(this)
        .transition().duration(100)
        .attr('opacity', 0.9)
      tooltip.style('opacity', 0)
    })
}

watch(() => props.actions.length, () => {
  nextTick(() => renderChart())
})

onMounted(() => {
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
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Agent Journey Flow</h3>
      <span v-if="sankeyData" class="text-xs text-[var(--color-text-muted)]">
        {{ sankeyData.nodes[0]?.label || '' }}
      </span>
    </div>

    <div v-if="sankeyData" ref="chartRef" class="relative" style="height: 356px" />

    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Agent journey data will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="sankeyData" class="flex flex-wrap items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[#2068FF]" /> Observe
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[#ff5600]" /> Discuss
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[#AA00FF]" /> Create
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[#009900]" /> Amplify
      </span>
    </div>
  </div>
</template>
