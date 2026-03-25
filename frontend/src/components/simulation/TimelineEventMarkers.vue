<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  timeline: { type: Array, default: () => [] },
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const EVENT_TYPES = {
  milestone: { color: '#2068FF', label: 'Milestones' },
  spike: { color: '#ff5600', label: 'Spikes' },
  competitive: { color: '#AA00FF', label: 'Competitive' },
  agent_entry: { color: '#009900', label: 'Agents' },
}

const activeFilters = ref(new Set(Object.keys(EVENT_TYPES)))

function toggleFilter(type) {
  const next = new Set(activeFilters.value)
  if (next.has(type)) next.delete(type)
  else next.add(type)
  activeFilters.value = next
}

// --- Derive notable events from timeline + actions data ---

const computedEvents = computed(() => {
  const tl = props.timeline
  if (!tl.length) return []

  const events = []
  const maxRound = tl[tl.length - 1].round_num

  // Milestones at fixed positions
  events.push({
    round: 1,
    type: 'milestone',
    label: 'Simulation Started',
    detail: '15 agents begin monitoring GTM channels',
  })

  for (const [frac, label, detail] of [
    [0.25, '25% Complete', 'Initial discussion patterns forming'],
    [0.50, 'Halfway Point', 'Agent networks established'],
    [0.75, '75% Complete', 'Competitive evaluations solidifying'],
  ]) {
    const r = Math.round(maxRound * frac)
    if (r > 1 && r <= maxRound) {
      events.push({ round: r, type: 'milestone', label, detail })
    }
  }

  // Activity spikes: rounds exceeding mean + 1 stddev (first in consecutive run only)
  if (tl.length > 5) {
    const totals = tl.map(d => d.total_actions ?? (d.twitter_actions + d.reddit_actions))
    const avg = totals.reduce((s, v) => s + v, 0) / totals.length
    const std = Math.sqrt(totals.reduce((s, v) => s + (v - avg) ** 2, 0) / totals.length)
    const threshold = avg + std
    let prevSpike = false

    for (let i = 0; i < tl.length; i++) {
      if (totals[i] > threshold) {
        if (!prevSpike) {
          events.push({
            round: tl[i].round_num,
            type: 'spike',
            label: 'Activity Spike',
            detail: `${totals[i]} actions (avg: ${avg.toFixed(0)})`,
          })
        }
        prevSpike = true
      } else {
        prevSpike = false
      }
    }
  }

  // Agent first appearances + competitive mentions from actions
  if (props.actions.length) {
    const sorted = [...props.actions].sort((a, b) => a.round_num - b.round_num)

    const seenAgents = new Set()
    let entryCount = 0
    for (const a of sorted) {
      const name = a.agent_name?.split('(')[0]?.trim()
      if (name && !seenAgents.has(name)) {
        seenAgents.add(name)
        if (entryCount < 4) {
          events.push({
            round: a.round_num,
            type: 'agent_entry',
            label: name,
            detail: `First activity on ${a.platform}`,
          })
          entryCount++
        }
      }
    }

    const competitors = ['Zendesk', 'Freshdesk', 'HubSpot', 'Salesforce', 'Help Scout']
    const mentioned = new Set()
    for (const a of sorted) {
      const content = (a.action_args?.content || '').toLowerCase()
      for (const comp of competitors) {
        if (!mentioned.has(comp) && content.includes(comp.toLowerCase())) {
          mentioned.add(comp)
          events.push({
            round: a.round_num,
            type: 'competitive',
            label: comp,
            detail: `First reference to ${comp} in discussion`,
          })
        }
      }
    }
  }

  return events.sort((a, b) => a.round - b.round)
})

const filteredEvents = computed(() =>
  computedEvents.value.filter(e => activeFilters.value.has(e.type)),
)

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.timeline.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const data = props.timeline
  const events = filteredEvents.value
  const margin = { top: 8, right: 16, bottom: 28, left: 16 }
  const width = containerWidth - margin.left - margin.right
  const markerBand = 24
  const areaHeight = 100
  const height = markerBand + areaHeight
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Shared x-scale
  const x = d3.scaleLinear()
    .domain([data[0].round_num, data[data.length - 1].round_num])
    .range([0, width])

  const totalAt = d => d.total_actions ?? (d.twitter_actions + d.reddit_actions)
  const maxActions = d3.max(data, totalAt) || 1

  const yArea = d3.scaleLinear()
    .domain([0, maxActions * 1.2])
    .range([height, markerBand])

  // Activity area (subtle context background)
  const areaGen = d3.area()
    .x(d => x(d.round_num))
    .y0(height)
    .y1(d => yArea(totalAt(d)))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', areaGen)
    .attr('fill', 'rgba(32, 104, 255, 0.04)')

  const lineGen = d3.line()
    .x(d => x(d.round_num))
    .y(d => yArea(totalAt(d)))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', lineGen)
    .attr('fill', 'none')
    .attr('stroke', 'rgba(32, 104, 255, 0.15)')
    .attr('stroke-width', 1.5)

  // X-axis baseline
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', height).attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')

  // X-axis round labels
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round_num))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round_num}`)

  // Marker rail (subtle horizontal line)
  const railY = markerBand / 2
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', railY).attr('y2', railY)
    .attr('stroke', 'rgba(0,0,0,0.04)')

  // Drop lines from each marker to the x-axis
  g.selectAll('.drop')
    .data(events)
    .join('line')
    .attr('x1', d => x(d.round)).attr('x2', d => x(d.round))
    .attr('y1', railY + 6).attr('y2', height)
    .attr('stroke', d => EVENT_TYPES[d.type]?.color || '#888')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '2,4')
    .attr('opacity', 0.25)

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
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.12)')
    .style('z-index', '10')
    .style('max-width', '240px')
    .style('transition', 'opacity 0.15s ease')

  // Event marker groups
  const markerG = g.selectAll('.marker')
    .data(events)
    .join('g')
    .attr('class', 'marker')
    .attr('transform', d => `translate(${x(d.round)},${railY})`)

  // Visible marker circles (animated in)
  markerG.append('circle')
    .attr('r', 0)
    .attr('fill', d => EVENT_TYPES[d.type]?.color || '#888')
    .attr('stroke', 'var(--color-surface, #fff)')
    .attr('stroke-width', 2)
    .transition()
    .duration(300)
    .delay((_, i) => i * 40)
    .attr('r', 5)

  // Invisible hover targets (larger for easier interaction)
  markerG.append('circle')
    .attr('r', 12)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const cfg = EVENT_TYPES[d.type] || {}
      tooltip
        .html(`
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
            <span style="width:8px;height:8px;border-radius:50%;background:${cfg.color || '#888'};flex-shrink:0"></span>
            <span style="font-weight:600;color:var(--color-text,#050505)">${d.label}</span>
          </div>
          <div style="color:var(--color-text-secondary,#555);line-height:1.4">${d.detail}</div>
          <div style="color:var(--color-text-muted,#888);margin-top:4px;font-size:11px">Round ${d.round}</div>
        `)
        .style('opacity', 1)

      d3.select(event.currentTarget.parentNode).select('circle:first-child')
        .transition().duration(100).attr('r', 7)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      let left = event.clientX - rect.left + 12
      if (left + 240 > containerWidth) left = event.clientX - rect.left - 252
      let top = event.clientY - rect.top - 70
      if (top < 0) top = event.clientY - rect.top + 12
      tooltip.style('left', `${left}px`).style('top', `${top}px`)
    })
    .on('mouseleave', (event) => {
      tooltip.style('opacity', 0)
      d3.select(event.currentTarget.parentNode).select('circle:first-child')
        .transition().duration(100).attr('r', 5)
    })
}

// --- Lifecycle ---

watch([() => props.timeline.length, () => props.actions.length, activeFilters], () => {
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
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Timeline Events</h3>
      <span v-if="computedEvents.length" class="text-xs text-[var(--color-text-muted)]">
        {{ filteredEvents.length }} events
      </span>
    </div>

    <!-- Filter chips -->
    <div v-if="computedEvents.length" class="flex flex-wrap gap-1.5 mb-4">
      <button
        v-for="(cfg, key) in EVENT_TYPES"
        :key="key"
        class="flex items-center gap-1.5 px-2.5 py-1 text-[11px] rounded-full font-medium transition-colors border"
        :class="activeFilters.has(key)
          ? 'border-transparent text-white'
          : 'border-[var(--color-border)] text-[var(--color-text-muted)] bg-transparent'"
        :style="activeFilters.has(key) ? { background: cfg.color } : {}"
        @click="toggleFilter(key)"
      >
        {{ cfg.label }}
        <span class="text-[10px] opacity-80">
          ({{ computedEvents.filter(e => e.type === key).length }})
        </span>
      </button>
    </div>

    <!-- D3 chart container -->
    <div v-if="computedEvents.length" ref="chartRef" class="relative" style="height: 160px" />

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[140px] text-[var(--color-text-muted)] text-sm">
      <span>Event markers will appear as the simulation progresses</span>
    </div>
  </div>
</template>
