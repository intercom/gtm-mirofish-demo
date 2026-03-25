<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import client from '../../api/client.js'

const props = defineProps({
  simulationId: { type: String, default: '' },
  demoMode: { type: Boolean, default: false },
})

const chartRef = ref(null)
const loading = ref(false)
const error = ref(null)
const evolutionData = ref(null)
const selectedRound = ref(null)
let resizeObserver = null
let resizeTimer = null

// Color map built from API response
const coalitionColorMap = computed(() => {
  if (!evolutionData.value?.coalition_labels) return {}
  const map = {}
  for (const c of evolutionData.value.coalition_labels) {
    map[c.id] = c.color
  }
  return map
})

const coalitionNameMap = computed(() => {
  if (!evolutionData.value?.coalition_labels) return {}
  const map = {}
  for (const c of evolutionData.value.coalition_labels) {
    map[c.id] = c.name
  }
  return map
})

// Summary stats
const summary = computed(() => evolutionData.value?.summary || null)

// Coalition state for selected round
const selectedRoundState = computed(() => {
  if (!selectedRound.value || !evolutionData.value?.rounds) return null
  return evolutionData.value.rounds.find(r => r.round === selectedRound.value)
})

// --- Data fetching ---

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const id = props.simulationId || 'demo'
    const { data: resp } = await client.get(`/simulation/${id}/coalitions/evolution`)
    if (resp.success) {
      evolutionData.value = resp.data
    } else {
      error.value = resp.error || 'Failed to load coalition data'
    }
  } catch (e) {
    error.value = e.message || 'Network error'
  } finally {
    loading.value = false
  }
}

// --- D3 alluvial rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !evolutionData.value) return

  const { rounds, flows, events, coalition_labels } = evolutionData.value
  if (!rounds.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 20, right: 20, bottom: 32, left: 20 }
  const width = containerWidth - margin.left - margin.right
  const height = 280
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const coalitionIds = coalition_labels.map(c => c.id)
  const colorMap = {}
  for (const c of coalition_labels) {
    colorMap[c.id] = c.color
  }

  // X scale: one column per round
  const roundNums = rounds.map(r => r.round)
  const x = d3.scalePoint()
    .domain(roundNums)
    .range([0, width])
    .padding(0.1)

  const columnWidth = roundNums.length > 1
    ? x(roundNums[1]) - x(roundNums[0])
    : width

  // For each round, compute stacked positions for each coalition
  // Total agents across all coalitions (constant)
  const totalAgents = Object.values(rounds[0].coalitions).reduce((s, m) => s + m.length, 0)

  const yScale = d3.scaleLinear()
    .domain([0, totalAgents])
    .range([0, height])

  // Compute node positions: for each round, stack coalitions vertically
  const nodePositions = {} // { "round:coalitionId" -> { y0, y1, round, cid } }

  for (const round of rounds) {
    let yOffset = 0
    for (const cid of coalitionIds) {
      const members = round.coalitions[cid] || []
      const h = yScale(members.length)
      const key = `${round.round}:${cid}`
      nodePositions[key] = {
        y0: yOffset,
        y1: yOffset + h,
        round: round.round,
        cid,
        members,
        height: h,
      }
      yOffset += h
    }
  }

  // Draw flow ribbons between consecutive rounds
  const ribbonGroup = g.append('g').attr('class', 'ribbons')

  // For each flow, draw a curved ribbon from source stack to target stack
  // We need sub-offsets within each node to avoid overlapping ribbons
  const sourceOffsets = {} // track cumulative offset per source node
  const targetOffsets = {} // track cumulative offset per target node

  // Sort flows by source coalition then target coalition for consistent stacking
  const sortedFlows = [...flows].sort((a, b) => {
    const ai = coalitionIds.indexOf(a.from_coalition)
    const bi = coalitionIds.indexOf(b.from_coalition)
    if (ai !== bi) return ai - bi
    return coalitionIds.indexOf(a.to_coalition) - coalitionIds.indexOf(b.to_coalition)
  })

  for (const flow of sortedFlows) {
    const srcKey = `${flow.from_round}:${flow.from_coalition}`
    const dstKey = `${flow.to_round}:${flow.to_coalition}`
    const src = nodePositions[srcKey]
    const dst = nodePositions[dstKey]
    if (!src || !dst) continue

    const ribbonH = yScale(flow.count)
    if (ribbonH < 0.5) continue

    const srcOff = sourceOffsets[srcKey] || 0
    const dstOff = targetOffsets[dstKey] || 0

    const x0 = x(flow.from_round) + columnWidth * 0.18
    const x1 = x(flow.to_round) - columnWidth * 0.18
    const midX = (x0 + x1) / 2

    const sy0 = src.y0 + srcOff
    const sy1 = sy0 + ribbonH
    const dy0 = dst.y0 + dstOff
    const dy1 = dy0 + ribbonH

    // Determine ribbon color: use source coalition color, lighter if switching
    const isSwitching = flow.from_coalition !== flow.to_coalition
    const baseColor = colorMap[flow.from_coalition] || '#888'

    const path = d3.path()
    path.moveTo(x0, sy0)
    path.bezierCurveTo(midX, sy0, midX, dy0, x1, dy0)
    path.lineTo(x1, dy1)
    path.bezierCurveTo(midX, dy1, midX, sy1, x0, sy1)
    path.closePath()

    ribbonGroup.append('path')
      .attr('d', path.toString())
      .attr('fill', baseColor)
      .attr('fill-opacity', isSwitching ? 0.35 : 0.18)
      .attr('stroke', isSwitching ? baseColor : 'none')
      .attr('stroke-width', isSwitching ? 1 : 0)
      .attr('stroke-opacity', 0.5)
      .style('opacity', 0)
      .transition()
      .duration(600)
      .delay(flow.from_round * 50)
      .style('opacity', 1)

    sourceOffsets[srcKey] = srcOff + ribbonH
    targetOffsets[dstKey] = dstOff + ribbonH
  }

  // Draw coalition nodes (stacked bars at each round)
  const nodeGroup = g.append('g').attr('class', 'nodes')

  for (const round of rounds) {
    for (const cid of coalitionIds) {
      const key = `${round.round}:${cid}`
      const node = nodePositions[key]
      if (!node || node.height < 1) continue

      const barWidth = Math.min(columnWidth * 0.28, 18)

      nodeGroup.append('rect')
        .attr('x', x(round.round) - barWidth / 2)
        .attr('y', node.y0)
        .attr('width', barWidth)
        .attr('height', node.height)
        .attr('rx', 3)
        .attr('fill', colorMap[cid])
        .attr('fill-opacity', 0.85)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)
        .style('cursor', 'pointer')
        .on('click', () => {
          selectedRound.value = selectedRound.value === round.round ? null : round.round
        })
    }
  }

  // Event annotations
  const eventGroup = g.append('g').attr('class', 'events')
  const switchEvents = events.filter(e => e.type === 'agent_switched')
  const formEvents = events.filter(e => e.type === 'coalition_formed')

  // Coalition formed markers (diamond at round 1)
  for (const evt of formEvents) {
    const node = nodePositions[`${evt.round}:${evt.coalition}`]
    if (!node) continue
    const cx = x(evt.round)
    const cy = node.y0 + node.height / 2
    const size = 5

    eventGroup.append('path')
      .attr('d', `M${cx},${cy - size} L${cx + size},${cy} L${cx},${cy + size} L${cx - size},${cy} Z`)
      .attr('fill', '#fff')
      .attr('stroke', colorMap[evt.coalition])
      .attr('stroke-width', 1.5)
      .style('opacity', 0)
      .transition()
      .duration(300)
      .delay(200)
      .style('opacity', 1)
  }

  // Highlight rounds with agent switches (small dot above the round column)
  const switchRounds = [...new Set(switchEvents.map(e => e.round))]
  for (const r of switchRounds) {
    const switchCount = switchEvents.filter(e => e.round === r).length
    eventGroup.append('circle')
      .attr('cx', x(r))
      .attr('cy', -8)
      .attr('r', Math.min(3 + switchCount, 7))
      .attr('fill', '#ff5600')
      .attr('fill-opacity', 0.7)
      .style('opacity', 0)
      .transition()
      .duration(300)
      .delay(r * 50)
      .style('opacity', 1)
  }

  // X-axis round labels
  g.selectAll('.x-label')
    .data(roundNums)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', d => d === selectedRound.value ? 'var(--color-text, #050505)' : '#888')
    .attr('font-weight', d => d === selectedRound.value ? '600' : '400')
    .style('cursor', 'pointer')
    .text(d => `R${d}`)
    .on('click', (event, d) => {
      selectedRound.value = selectedRound.value === d ? null : d
    })

  // Selected round highlight
  if (selectedRound.value) {
    const sx = x(selectedRound.value)
    g.append('rect')
      .attr('x', sx - columnWidth * 0.22)
      .attr('y', -12)
      .attr('width', columnWidth * 0.44)
      .attr('height', height + 14)
      .attr('rx', 4)
      .attr('fill', 'var(--color-primary, #2068FF)')
      .attr('fill-opacity', 0.06)
      .attr('stroke', 'var(--color-primary, #2068FF)')
      .attr('stroke-opacity', 0.2)
      .attr('stroke-width', 1)
  }

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

  // Hover targets per round column
  g.selectAll('.hover-col')
    .data(roundNums)
    .join('rect')
    .attr('x', d => x(d) - columnWidth * 0.4)
    .attr('y', 0)
    .attr('width', columnWidth * 0.8)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, round) => {
      const rd = rounds.find(r => r.round === round)
      if (!rd) return
      const switchesHere = switchEvents.filter(e => e.round === round)
      let html = `<div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${round}</div>`
      for (const cid of coalitionIds) {
        const members = rd.coalitions[cid] || []
        if (!members.length) continue
        const name = coalitionNameMap.value[cid] || cid
        html += `<div style="display:flex;align-items:center;gap:4px;margin-top:2px">
          <span style="width:8px;height:8px;border-radius:50%;background:${colorMap[cid]};display:inline-block"></span>
          <span style="color:var(--color-text,#050505)">${name}</span>
          <span style="color:var(--color-text-muted,#888);margin-left:auto">${members.length}</span>
        </div>`
      }
      if (switchesHere.length) {
        html += `<div style="margin-top:6px;padding-top:4px;border-top:1px solid var(--color-border,rgba(0,0,0,0.1));color:#ff5600;font-size:11px">${switchesHere.length} agent switch${switchesHere.length > 1 ? 'es' : ''}</div>`
      }
      tooltip.html(html).style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
    })
    .on('click', (event, round) => {
      selectedRound.value = selectedRound.value === round ? null : round
    })
}

// --- Lifecycle ---

watch(() => props.simulationId, () => {
  fetchData()
})

watch([evolutionData, selectedRound], () => {
  nextTick(() => renderChart())
})

onMounted(async () => {
  await fetchData()
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
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Coalition Evolution</h3>
      <div v-if="evolutionData" class="flex items-center gap-3">
        <span
          v-for="c in evolutionData.coalition_labels"
          :key="c.id"
          class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]"
        >
          <span
            class="inline-block w-2 h-2 rounded-full"
            :style="{ background: c.color }"
          />
          {{ c.name }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      Loading coalition data...
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-[280px] text-[var(--color-error)] text-sm">
      {{ error }}
    </div>

    <!-- Chart -->
    <div v-else-if="evolutionData" class="relative" ref="chartRef" style="height: 332px" />

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      Coalition data will appear as the simulation progresses
    </div>

    <!-- Selected round detail panel -->
    <div
      v-if="selectedRoundState"
      class="mt-3 p-3 rounded-md bg-[var(--color-tint)] border border-[var(--color-border)]"
    >
      <div class="text-xs font-semibold text-[var(--color-text)] mb-2">
        Round {{ selectedRoundState.round }} Coalitions
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div
          v-for="(members, cid) in selectedRoundState.coalitions"
          :key="cid"
          class="text-xs"
        >
          <div class="flex items-center gap-1.5 mb-1">
            <span
              class="inline-block w-2 h-2 rounded-full"
              :style="{ background: coalitionColorMap[cid] || '#888' }"
            />
            <span class="font-medium text-[var(--color-text)]">{{ coalitionNameMap[cid] || cid }}</span>
            <span class="text-[var(--color-text-muted)]">({{ members.length }})</span>
          </div>
          <div class="pl-3.5 text-[var(--color-text-muted)] leading-relaxed">
            {{ members.join(', ') }}
          </div>
        </div>
      </div>
    </div>

    <!-- Summary stats -->
    <div
      v-if="summary"
      class="flex items-center gap-5 mt-3 text-xs text-[var(--color-text-muted)]"
    >
      <span>
        <span class="font-medium text-[var(--color-text)]">{{ summary.total_changes }}</span> coalition changes
      </span>
      <span>
        Most stable:
        <span class="font-medium text-[var(--color-text)]">{{ coalitionNameMap[summary.most_stable_coalition] || summary.most_stable_coalition }}</span>
      </span>
      <span>
        Most dynamic:
        <span class="font-medium text-[var(--color-text)]">{{ summary.most_dynamic_agent }}</span>
      </span>
    </div>
  </div>
</template>
