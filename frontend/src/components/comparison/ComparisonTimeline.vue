<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  timelineA: { type: Array, default: () => [] },
  timelineB: { type: Array, default: () => [] },
  labelA: { type: String, default: 'Scenario A' },
  labelB: { type: String, default: 'Scenario B' },
})

const COLOR_A = '#2068FF'
const COLOR_B = '#ff5600'
const COLOR_A_LIGHT = 'rgba(32, 104, 255, 0.12)'
const COLOR_B_LIGHT = 'rgba(255, 86, 0, 0.12)'
const COLOR_DIVERGENCE = '#ef4444'

const chartRef = ref(null)
const scrubberRound = ref(null)
let resizeObserver = null
let resizeTimer = null

// Normalize events into { round, type, label, detail } shape
function normalizeEvents(timeline) {
  const events = []
  for (const item of timeline) {
    const round = item.round_num ?? item.round
    if (round == null) continue
    events.push({
      round,
      type: (item.action_type || item.type || 'event').toLowerCase(),
      label: item.action_type || item.type || 'Event',
      agent: item.agent_name || item.agent_id || '',
      detail: item.action_args?.content || item.content || item.description || '',
    })
  }
  return events
}

// Group events by round
function groupByRound(events) {
  const map = new Map()
  for (const e of events) {
    if (!map.has(e.round)) map.set(e.round, [])
    map.get(e.round).push(e)
  }
  return map
}

// Find matching event types across A and B at any round
function findConnections(groupA, groupB) {
  const connections = []
  for (const [round, eventsA] of groupA) {
    if (!groupB.has(round)) continue
    const eventsB = groupB.get(round)
    const typesA = new Set(eventsA.map(e => e.type))
    const typesB = new Set(eventsB.map(e => e.type))
    for (const t of typesA) {
      if (typesB.has(t)) {
        connections.push({ round, type: t })
      }
    }
  }
  return connections
}

// Find rounds where only one timeline has events, or event types diverge
function findDivergences(groupA, groupB, allRounds) {
  const divergences = []
  for (const round of allRounds) {
    const a = groupA.get(round)
    const b = groupB.get(round)
    if ((a && !b) || (!a && b)) {
      divergences.push({ round, reason: a ? 'only_a' : 'only_b' })
      continue
    }
    if (a && b) {
      const typesA = new Set(a.map(e => e.type))
      const typesB = new Set(b.map(e => e.type))
      const onlyInA = [...typesA].filter(t => !typesB.has(t))
      const onlyInB = [...typesB].filter(t => !typesA.has(t))
      if (onlyInA.length > 0 || onlyInB.length > 0) {
        divergences.push({ round, reason: 'different_types', onlyInA, onlyInB })
      }
    }
  }
  return divergences
}

const eventsA = computed(() => normalizeEvents(props.timelineA))
const eventsB = computed(() => normalizeEvents(props.timelineB))
const hasData = computed(() => eventsA.value.length > 0 || eventsB.value.length > 0)

// Aggregate round-level counts for the lane dots
function roundSummaries(events) {
  const map = new Map()
  for (const e of events) {
    if (!map.has(e.round)) map.set(e.round, { round: e.round, count: 0, types: new Set() })
    const entry = map.get(e.round)
    entry.count++
    entry.types.add(e.type)
  }
  return Array.from(map.values()).sort((a, b) => a.round - b.round)
}

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !hasData.value) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const eA = eventsA.value
  const eB = eventsB.value
  const groupA = groupByRound(eA)
  const groupB = groupByRound(eB)
  const summA = roundSummaries(eA)
  const summB = roundSummaries(eB)

  const allRounds = [...new Set([...eA.map(e => e.round), ...eB.map(e => e.round)])].sort((a, b) => a - b)
  if (allRounds.length === 0) return

  const connections = findConnections(groupA, groupB)
  const divergences = findDivergences(groupA, groupB, allRounds)
  const divergenceRounds = new Set(divergences.map(d => d.round))

  const margin = { top: 24, right: 20, bottom: 44, left: 20 }
  const laneHeight = 100
  const gapHeight = 32
  const width = containerWidth - margin.left - margin.right
  const totalHeight = margin.top + laneHeight + gapHeight + laneHeight + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const x = d3.scaleLinear()
    .domain([allRounds[0], allRounds[allRounds.length - 1]])
    .range([0, width])

  const rScale = d3.scaleSqrt()
    .domain([1, d3.max([...summA, ...summB], d => d.count) || 1])
    .range([4, 14])

  const yA = laneHeight / 2
  const yB = laneHeight + gapHeight + laneHeight / 2

  // Lane backgrounds
  g.append('rect')
    .attr('x', -4).attr('y', 0)
    .attr('width', width + 8).attr('height', laneHeight)
    .attr('rx', 6).attr('fill', COLOR_A_LIGHT)

  g.append('rect')
    .attr('x', -4).attr('y', laneHeight + gapHeight)
    .attr('width', width + 8).attr('height', laneHeight)
    .attr('rx', 6).attr('fill', COLOR_B_LIGHT)

  // Lane labels
  g.append('text')
    .attr('x', 4).attr('y', 14)
    .attr('font-size', '11px').attr('font-weight', '600')
    .attr('fill', COLOR_A)
    .text(props.labelA)

  g.append('text')
    .attr('x', 4).attr('y', laneHeight + gapHeight + 14)
    .attr('font-size', '11px').attr('font-weight', '600')
    .attr('fill', COLOR_B)
    .text(props.labelB)

  // Center axis line
  const axisY = laneHeight + gapHeight / 2
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', axisY).attr('y2', axisY)
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
    .attr('stroke-width', 1)

  // Round tick marks on center axis
  const tickStep = Math.max(1, Math.floor(allRounds.length / 12))
  const tickRounds = allRounds.filter((_, i) => i % tickStep === 0 || i === allRounds.length - 1)
  g.selectAll('.tick-mark')
    .data(tickRounds)
    .join('line')
    .attr('x1', d => x(d)).attr('x2', d => x(d))
    .attr('y1', axisY - 4).attr('y2', axisY + 4)
    .attr('stroke', 'var(--color-border-strong, rgba(0,0,0,0.2))')

  g.selectAll('.tick-label')
    .data(tickRounds)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', axisY + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d}`)

  // Divergence highlights (vertical stripes)
  g.selectAll('.divergence')
    .data(divergences)
    .join('rect')
    .attr('x', d => x(d.round) - 8)
    .attr('y', 0)
    .attr('width', 16)
    .attr('height', laneHeight * 2 + gapHeight)
    .attr('rx', 3)
    .attr('fill', COLOR_DIVERGENCE)
    .attr('opacity', 0.06)

  // Connector lines between matching events
  g.selectAll('.connector')
    .data(connections)
    .join('path')
    .attr('d', d => {
      const cx = x(d.round)
      return `M ${cx} ${yA + 10} C ${cx} ${axisY - 4}, ${cx} ${axisY + 4}, ${cx} ${yB - 10}`
    })
    .attr('fill', 'none')
    .attr('stroke', 'var(--color-border-strong, rgba(0,0,0,0.2))')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')
    .attr('opacity', 0.5)

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

  function showTooltip(event, d, color, label) {
    const types = [...d.types].map(t => `<span style="background:${color}20;color:${color};padding:1px 5px;border-radius:3px;font-size:10px">${t}</span>`).join(' ')
    tooltip
      .html(`
        <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:3px">Round ${d.round}</div>
        <div style="color:${color};font-size:11px;font-weight:500;margin-bottom:3px">${label}</div>
        <div style="margin-bottom:2px">${d.count} event${d.count !== 1 ? 's' : ''}</div>
        <div style="display:flex;flex-wrap:wrap;gap:3px">${types}</div>
        ${divergenceRounds.has(d.round) ? '<div style="color:#ef4444;font-size:10px;margin-top:4px;font-weight:500">Divergence point</div>' : ''}
      `)
      .style('opacity', 1)
    const rect = container.getBoundingClientRect()
    tooltip
      .style('left', `${event.clientX - rect.left + 14}px`)
      .style('top', `${event.clientY - rect.top - 10}px`)
  }

  function hideTooltip() {
    tooltip.style('opacity', 0)
  }

  // Event dots — Timeline A
  const dotsA = g.selectAll('.dot-a')
    .data(summA)
    .join('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', yA)
    .attr('r', 0)
    .attr('fill', d => divergenceRounds.has(d.round) ? COLOR_DIVERGENCE : COLOR_A)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .attr('cursor', 'pointer')
    .on('mouseenter', function (event, d) {
      d3.select(this).transition().duration(100).attr('r', rScale(d.count) + 2)
      showTooltip(event, d, COLOR_A, props.labelA)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip.style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 10}px`)
    })
    .on('mouseleave', function (event, d) {
      d3.select(this).transition().duration(100).attr('r', rScale(d.count))
      hideTooltip()
    })

  dotsA.transition()
    .duration(400)
    .delay((_, i) => i * 30)
    .ease(d3.easeCubicOut)
    .attr('r', d => rScale(d.count))

  // Event dots — Timeline B
  const dotsB = g.selectAll('.dot-b')
    .data(summB)
    .join('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', yB)
    .attr('r', 0)
    .attr('fill', d => divergenceRounds.has(d.round) ? COLOR_DIVERGENCE : COLOR_B)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .attr('cursor', 'pointer')
    .on('mouseenter', function (event, d) {
      d3.select(this).transition().duration(100).attr('r', rScale(d.count) + 2)
      showTooltip(event, d, COLOR_B, props.labelB)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip.style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 10}px`)
    })
    .on('mouseleave', function (event, d) {
      d3.select(this).transition().duration(100).attr('r', rScale(d.count))
      hideTooltip()
    })

  dotsB.transition()
    .duration(400)
    .delay((_, i) => i * 30)
    .ease(d3.easeCubicOut)
    .attr('r', d => rScale(d.count))

  // --- Scrubber ---
  const scrubberGroup = g.append('g').attr('class', 'scrubber')
  const initialRound = scrubberRound.value ?? allRounds[0]

  const scrubberLine = scrubberGroup.append('line')
    .attr('x1', x(initialRound)).attr('x2', x(initialRound))
    .attr('y1', 0).attr('y2', laneHeight * 2 + gapHeight)
    .attr('stroke', 'var(--color-text, #050505)')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.6)

  const scrubberHandle = scrubberGroup.append('circle')
    .attr('cx', x(initialRound))
    .attr('cy', axisY)
    .attr('r', 7)
    .attr('fill', 'var(--color-text, #050505)')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('cursor', 'ew-resize')

  // Scrubber round label
  const scrubberLabel = scrubberGroup.append('text')
    .attr('x', x(initialRound))
    .attr('y', laneHeight * 2 + gapHeight + 14)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text, #050505)')
    .text(`R${initialRound}`)

  function snapToRound(px) {
    const rawRound = x.invert(Math.max(0, Math.min(width, px)))
    let closest = allRounds[0]
    let minDist = Infinity
    for (const r of allRounds) {
      const dist = Math.abs(r - rawRound)
      if (dist < minDist) { minDist = dist; closest = r }
    }
    return closest
  }

  function moveScrubber(round) {
    scrubberRound.value = round
    const cx = x(round)
    scrubberLine.attr('x1', cx).attr('x2', cx)
    scrubberHandle.attr('cx', cx)
    scrubberLabel.attr('x', cx).text(`R${round}`)

    // Highlight active dots
    dotsA.attr('opacity', d => d.round === round ? 1 : 0.5)
    dotsB.attr('opacity', d => d.round === round ? 1 : 0.5)
  }

  // Drag behavior
  const drag = d3.drag()
    .on('drag', (event) => {
      const localX = event.x - margin.left
      moveScrubber(snapToRound(localX))
    })

  scrubberHandle.call(drag)

  // Click on chart to move scrubber
  svg.on('click', (event) => {
    const [mx] = d3.pointer(event, g.node())
    moveScrubber(snapToRound(mx))
  })
}

// --- Lifecycle ---

watch([() => props.timelineA.length, () => props.timelineB.length], () => {
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
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Comparison Timeline</h3>
      <div class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full" :style="{ background: '#2068FF' }" />
          {{ labelA }}
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full" :style="{ background: '#ff5600' }" />
          {{ labelB }}
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full" :style="{ background: '#ef4444' }" />
          Divergence
        </span>
      </div>
    </div>

    <div v-if="hasData" ref="chartRef" class="relative" style="height: 320px" />

    <div v-else class="flex flex-col items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm gap-2">
      <svg class="w-8 h-8 opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M3 12h4l3-9 4 18 3-9h4" />
      </svg>
      <span>Load two scenarios to compare timelines</span>
    </div>

    <div v-if="hasData" class="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
      <span>Click or drag the scrubber to inspect individual rounds</span>
      <span class="ml-auto flex items-center gap-1">
        <span class="inline-block w-3 border-t border-dashed border-[var(--color-border-strong)]" />
        Matched events
      </span>
    </div>
  </div>
</template>
