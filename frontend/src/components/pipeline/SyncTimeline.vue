<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  syncs: { type: Array, default: () => [] },
  connectors: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Status colors (Intercom brand-aligned) ---

const STATUS_COLORS = {
  success: '#009900',
  failed: '#ef4444',
  running: '#2068FF',
  scheduled: '#888888',
}

// --- Demo data ---

const DEMO_CONNECTORS = [
  { name: 'Salesforce', source: 'Salesforce', destination: 'Snowflake', type: 'fivetran' },
  { name: 'Stripe', source: 'Stripe', destination: 'Snowflake', type: 'fivetran' },
  { name: 'HubSpot', source: 'HubSpot', destination: 'Snowflake', type: 'fivetran' },
  { name: 'Zendesk', source: 'Zendesk', destination: 'Snowflake', type: 'fivetran' },
  { name: 'Intercom', source: 'Intercom', destination: 'Snowflake', type: 'fivetran' },
  { name: 'Lead Scoring', source: 'Snowflake', destination: 'Salesforce', type: 'census' },
  { name: 'Segments', source: 'Snowflake', destination: 'HubSpot', type: 'census' },
  { name: 'Tags', source: 'Snowflake', destination: 'Intercom', type: 'census' },
]

function seededRandom(seed) {
  let s = seed
  return () => {
    s = (s * 16807 + 0) % 2147483647
    return (s - 1) / 2147483646
  }
}

function generateDemoSyncs() {
  const now = Date.now()
  const dayMs = 24 * 60 * 60 * 1000
  const windowStart = now - dayMs
  const rand = seededRandom(42)
  const syncs = []

  for (const connector of DEMO_CONNECTORS) {
    const intervalHours = connector.type === 'fivetran' ? 1 : 4
    const intervalMs = intervalHours * 60 * 60 * 1000
    const durationBaseMin = connector.type === 'fivetran' ? 2 : 5
    const durationRangeMin = connector.type === 'fivetran' ? 8 : 15

    let t = windowStart + rand() * intervalMs * 0.5
    while (t < now + intervalMs) {
      const durationMs = (durationBaseMin + rand() * durationRangeMin) * 60 * 1000
      const startedAt = new Date(t)
      const completedAt = new Date(t + durationMs)

      let status
      if (t + durationMs > now) {
        status = t > now ? 'scheduled' : 'running'
      } else {
        const r = rand()
        status = r < 0.92 ? 'success' : r < 0.97 ? 'failed' : 'success'
      }

      const rowsSynced = status === 'success'
        ? Math.floor(500 + rand() * 50000)
        : status === 'failed' ? 0 : Math.floor(rand() * 20000)

      const errors = [
        'Authentication token expired — re-authorize in connector settings',
        'Rate limit exceeded (429) — retrying in 60s',
        'Schema change detected: column "plan_type" removed in source',
        'Connection timeout after 120s — check network/firewall',
      ]

      syncs.push({
        id: `sync-${connector.name.toLowerCase().replace(/\s+/g, '-')}-${syncs.length}`,
        connector_name: connector.name,
        source: connector.source,
        destination: connector.destination,
        status,
        rows_synced: rowsSynced,
        started_at: startedAt.toISOString(),
        completed_at: status !== 'running' ? completedAt.toISOString() : null,
        duration_seconds: status !== 'running'
          ? Math.round(durationMs / 1000)
          : Math.round((now - t) / 1000),
        error_message: status === 'failed' ? errors[Math.floor(rand() * errors.length)] : null,
      })

      t += intervalMs + (rand() - 0.3) * intervalMs * 0.2
    }
  }

  return syncs
}

function generateScheduleMarkers() {
  const now = Date.now()
  const dayMs = 24 * 60 * 60 * 1000
  const windowStart = now - dayMs
  const markers = []

  for (const connector of DEMO_CONNECTORS) {
    const intervalHours = connector.type === 'fivetran' ? 1 : 4
    const intervalMs = intervalHours * 60 * 60 * 1000
    let t = windowStart
    while (t <= now + intervalMs) {
      markers.push({ connector_name: connector.name, time: new Date(t) })
      t += intervalMs
    }
  }
  return markers
}

// --- Resolved data ---

const resolvedConnectors = computed(() =>
  props.connectors.length ? props.connectors : DEMO_CONNECTORS
)

const resolvedSyncs = computed(() =>
  props.syncs.length ? props.syncs : generateDemoSyncs()
)

const connectorNames = computed(() =>
  resolvedConnectors.value.map(c => c.name)
)

const scheduleMarkers = computed(() => generateScheduleMarkers())

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !resolvedSyncs.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const names = connectorNames.value
  const syncs = resolvedSyncs.value
  const now = new Date()
  const dayMs = 24 * 60 * 60 * 1000

  const margin = { top: 20, right: 24, bottom: 32, left: 110 }
  const rowHeight = 36
  const height = names.length * rowHeight
  const width = containerWidth - margin.left - margin.right
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const x = d3.scaleTime()
    .domain([new Date(now.getTime() - dayMs), new Date(now.getTime() + dayMs * 0.04)])
    .range([0, width])

  const y = d3.scaleBand()
    .domain(names)
    .range([0, height])
    .padding(0.3)

  // Row backgrounds (alternating)
  g.selectAll('.row-bg')
    .data(names)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d) - y.step() * y.padding() / 2)
    .attr('width', width)
    .attr('height', y.step())
    .attr('fill', (_, i) => i % 2 === 0 ? 'rgba(0,0,0,0.02)' : 'transparent')

  // Horizontal grid lines
  g.selectAll('.row-line')
    .data(names)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d) + y.bandwidth() + y.step() * y.padding() / 2)
    .attr('y2', d => y(d) + y.bandwidth() + y.step() * y.padding() / 2)
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.06))')

  // X-axis time ticks
  const xAxis = d3.axisBottom(x)
    .ticks(d3.timeHour.every(3))
    .tickFormat(d3.timeFormat('%H:%M'))
    .tickSize(-height)

  const xAxisG = g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(xAxis)

  xAxisG.select('.domain').remove()
  xAxisG.selectAll('.tick line')
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')
  xAxisG.selectAll('.tick text')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .attr('dy', '1em')

  // Y-axis connector labels
  g.selectAll('.connector-label')
    .data(names)
    .join('text')
    .attr('x', -10)
    .attr('y', d => y(d) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('font-weight', '500')
    .attr('fill', 'var(--color-text, #050505)')
    .text(d => d)

  // Connector type badges (small label)
  const connectorMap = new Map(resolvedConnectors.value.map(c => [c.name, c]))
  g.selectAll('.connector-type')
    .data(names)
    .join('text')
    .attr('x', -10)
    .attr('y', d => y(d) + y.bandwidth() / 2 + 12)
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => {
      const c = connectorMap.get(d)
      return c ? `${c.source} → ${c.destination}` : ''
    })

  // Schedule markers (small dots)
  const markers = scheduleMarkers.value.filter(m =>
    names.includes(m.connector_name) &&
    m.time >= x.domain()[0] && m.time <= x.domain()[1]
  )

  g.selectAll('.schedule-dot')
    .data(markers)
    .join('circle')
    .attr('cx', d => x(d.time))
    .attr('cy', d => y(d.connector_name) + y.bandwidth() / 2)
    .attr('r', 2.5)
    .attr('fill', 'none')
    .attr('stroke', 'var(--color-text-muted, #888)')
    .attr('stroke-width', 1)
    .attr('opacity', 0.5)

  // Sync bars
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
    .style('max-width', '280px')

  const visibleSyncs = syncs.filter(s =>
    names.includes(s.connector_name) &&
    new Date(s.started_at) <= x.domain()[1] &&
    (s.completed_at ? new Date(s.completed_at) >= x.domain()[0] : true)
  )

  const bars = g.selectAll('.sync-bar')
    .data(visibleSyncs)
    .join('rect')
    .attr('x', d => x(new Date(d.started_at)))
    .attr('y', d => y(d.connector_name))
    .attr('width', d => {
      const start = x(new Date(d.started_at))
      const end = d.completed_at ? x(new Date(d.completed_at)) : x(now)
      return Math.max(3, end - start)
    })
    .attr('height', y.bandwidth())
    .attr('rx', 3)
    .attr('fill', d => STATUS_COLORS[d.status] || STATUS_COLORS.scheduled)
    .attr('opacity', 0)
    .attr('cursor', 'pointer')

  bars.transition()
    .duration(400)
    .delay((_, i) => i * 15)
    .attr('opacity', d => d.status === 'scheduled' ? 0.4 : 0.85)

  // Running status pulse animation
  const runningBars = visibleSyncs.filter(s => s.status === 'running')
  if (runningBars.length) {
    g.selectAll('.running-pulse')
      .data(runningBars)
      .join('rect')
      .attr('x', d => x(new Date(d.started_at)))
      .attr('y', d => y(d.connector_name))
      .attr('width', d => {
        const start = x(new Date(d.started_at))
        return Math.max(3, x(now) - start)
      })
      .attr('height', y.bandwidth())
      .attr('rx', 3)
      .attr('fill', STATUS_COLORS.running)
      .attr('opacity', 0.3)
      .append('animate')
      .attr('attributeName', 'opacity')
      .attr('values', '0.3;0.1;0.3')
      .attr('dur', '2s')
      .attr('repeatCount', 'indefinite')
  }

  // Bar hover interactions
  bars
    .on('mouseenter', (event, d) => {
      d3.select(event.currentTarget)
        .transition().duration(100)
        .attr('opacity', 1)
        .attr('stroke', STATUS_COLORS[d.status])
        .attr('stroke-width', 1.5)

      const duration = d.duration_seconds
      const durationStr = duration >= 3600
        ? `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`
        : duration >= 60
          ? `${Math.floor(duration / 60)}m ${duration % 60}s`
          : `${duration}s`

      const statusLabel = d.status.charAt(0).toUpperCase() + d.status.slice(1)
      const color = STATUS_COLORS[d.status]

      let details = `
        <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:6px">
          ${d.connector_name}
        </div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color}"></span>
          <span style="font-weight:500;color:${color}">${statusLabel}</span>
        </div>
        <div style="color:var(--color-text-secondary,#555);line-height:1.5">
          Duration: ${durationStr}<br>
      `
      if (d.status !== 'scheduled') {
        details += `Rows synced: ${d.rows_synced?.toLocaleString() ?? '—'}<br>`
      }
      details += `Started: ${new Date(d.started_at).toLocaleTimeString()}`
      if (d.completed_at) {
        details += `<br>Completed: ${new Date(d.completed_at).toLocaleTimeString()}`
      }
      details += '</div>'

      if (d.error_message) {
        details += `
          <div style="margin-top:6px;padding:6px 8px;background:rgba(239,68,68,0.08);border-radius:4px;color:#ef4444;font-size:11px;line-height:1.4">
            ${d.error_message}
          </div>
        `
      }

      tooltip.html(details).style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      const tooltipNode = tooltip.node()
      const tooltipWidth = tooltipNode.offsetWidth
      let left = event.clientX - rect.left + 12
      if (left + tooltipWidth > containerWidth) {
        left = event.clientX - rect.left - tooltipWidth - 12
      }
      tooltip
        .style('left', `${left}px`)
        .style('top', `${event.clientY - rect.top - 20}px`)
    })
    .on('mouseleave', (event, d) => {
      d3.select(event.currentTarget)
        .transition().duration(100)
        .attr('opacity', d.status === 'scheduled' ? 0.4 : 0.85)
        .attr('stroke', 'none')
      tooltip.style('opacity', 0)
    })

  // "Now" vertical line
  const nowX = x(now)
  g.append('line')
    .attr('x1', nowX)
    .attr('x2', nowX)
    .attr('y1', -8)
    .attr('y2', height)
    .attr('stroke', '#ff5600')
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '4,3')

  g.append('text')
    .attr('x', nowX)
    .attr('y', -12)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', '#ff5600')
    .text('Now')
}

// --- Lifecycle ---

watch([() => props.syncs.length, () => props.connectors.length], () => {
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
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Sync Timeline</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">Last 24 hours</p>
      </div>
    </div>

    <div
      v-if="resolvedSyncs.length"
      ref="chartRef"
      class="relative"
      :style="{ height: `${connectorNames.length * 36 + 52}px` }"
    />

    <div
      v-else
      class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm"
    >
      <span>No sync data available</span>
    </div>

    <!-- Legend -->
    <div v-if="resolvedSyncs.length" class="flex items-center gap-5 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #009900; opacity: 0.85" /> Success
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #ef4444; opacity: 0.85" /> Failed
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #2068FF; opacity: 0.85" /> Running
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #888; opacity: 0.4" /> Scheduled
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full border border-[var(--color-text-muted)]" style="opacity: 0.5" /> Schedule
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5" style="background: #ff5600; border-top: 1.5px dashed #ff5600" /> Now
      </span>
    </div>
  </div>
</template>
