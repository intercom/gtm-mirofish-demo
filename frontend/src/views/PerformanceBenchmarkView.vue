<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'
import { perfMonitor } from '../lib/perfMonitor'

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  amber: '#FFB800',
  text: '#050505',
  muted: '#888',
  gridLine: 'rgba(0,0,0,0.06)',
}

const waterfallRef = ref(null)
const routeChartRef = ref(null)
const apiChartRef = ref(null)
const refreshKey = ref(0)
let resizeObserver = null

const webVitals = computed(() => {
  void refreshKey.value
  return perfMonitor.getWebVitals()
})

const allStats = computed(() => {
  void refreshKey.value
  return perfMonitor.getAllStats()
})

const routeEntries = computed(() => {
  void refreshKey.value
  return perfMonitor.getRawEntries('routeNavigation')
})

const apiEntries = computed(() => {
  void refreshKey.value
  return perfMonitor.getRawEntries('apiResponse')
})

function refresh() {
  refreshKey.value++
  nextTick(renderAll)
}

function clearMetrics() {
  perfMonitor.clear()
  refresh()
}

function renderAll() {
  renderWaterfall()
  renderRouteChart()
  renderApiChart()
}

// ── Page Load Waterfall ────────────────────────────────────
function renderWaterfall() {
  const container = waterfallRef.value
  if (!container) return
  d3.select(container).selectAll('svg').remove()

  const vitals = perfMonitor.getWebVitals()
  if (!vitals) return

  const phases = [
    { label: 'DNS Lookup', value: vitals.dns, color: COLORS.purple },
    { label: 'TCP Connect', value: vitals.tcp, color: COLORS.amber },
    { label: 'TTFB', value: vitals.ttfb, color: COLORS.orange },
    { label: 'Download', value: vitals.download, color: COLORS.primary },
    { label: 'DOM Parsing', value: vitals.domParsing, color: COLORS.green },
  ]

  const milestones = [
    { label: 'FCP', value: vitals.fcp, color: COLORS.orange },
    { label: 'DOMContentLoaded', value: vitals.domContentLoaded, color: COLORS.purple },
    { label: 'Load', value: vitals.load, color: COLORS.green },
  ].filter((m) => m.value > 0)

  const margin = { top: 20, right: 20, bottom: 30, left: 110 }
  const w = container.clientWidth
  const barHeight = 28
  const h = phases.length * barHeight + margin.top + margin.bottom + milestones.length * 18 + 20

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', h)

  const maxVal = Math.max(vitals.load, vitals.domContentLoaded, vitals.fcp, 1)
  const x = d3.scaleLinear().domain([0, maxVal * 1.1]).range([margin.left, w - margin.right])

  // Cumulative offset for waterfall
  let cumulative = 0
  const bars = phases.map((p) => {
    const start = cumulative
    cumulative += p.value
    return { ...p, start }
  })

  // Bars
  svg
    .selectAll('rect.bar')
    .data(bars)
    .enter()
    .append('rect')
    .attr('x', (d) => x(d.start))
    .attr('y', (_, i) => margin.top + i * barHeight + 4)
    .attr('width', (d) => Math.max(1, x(d.start + d.value) - x(d.start)))
    .attr('height', barHeight - 8)
    .attr('rx', 3)
    .attr('fill', (d) => d.color)
    .attr('opacity', 0.85)

  // Labels
  svg
    .selectAll('text.label')
    .data(bars)
    .enter()
    .append('text')
    .attr('x', margin.left - 8)
    .attr('y', (_, i) => margin.top + i * barHeight + barHeight / 2 + 1)
    .attr('text-anchor', 'end')
    .attr('dominant-baseline', 'middle')
    .attr('font-size', '12px')
    .attr('fill', COLORS.text)
    .text((d) => d.label)

  // Value labels
  svg
    .selectAll('text.value')
    .data(bars)
    .enter()
    .append('text')
    .attr('x', (d) => x(d.start + d.value) + 6)
    .attr('y', (_, i) => margin.top + i * barHeight + barHeight / 2 + 1)
    .attr('dominant-baseline', 'middle')
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text((d) => `${d.value.toFixed(1)}ms`)

  // Milestone markers
  const milestoneY = margin.top + phases.length * barHeight + 12
  milestones.forEach((m, i) => {
    const my = milestoneY + i * 18
    svg
      .append('line')
      .attr('x1', x(m.value))
      .attr('x2', x(m.value))
      .attr('y1', margin.top)
      .attr('y2', my)
      .attr('stroke', m.color)
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '4,3')

    svg
      .append('text')
      .attr('x', x(m.value) + 4)
      .attr('y', my + 4)
      .attr('font-size', '11px')
      .attr('font-weight', 600)
      .attr('fill', m.color)
      .text(`${m.label}: ${m.value.toFixed(0)}ms`)
  })

  // X axis
  svg
    .append('g')
    .attr('transform', `translate(0,${h - margin.bottom})`)
    .call(
      d3
        .axisBottom(x)
        .ticks(6)
        .tickFormat((d) => `${d.toFixed(0)}ms`),
    )
    .call((g) => g.select('.domain').attr('stroke', COLORS.gridLine))
    .call((g) => g.selectAll('.tick line').attr('stroke', COLORS.gridLine))
    .call((g) => g.selectAll('.tick text').attr('fill', COLORS.muted).attr('font-size', '10px'))
}

// ── Route Navigation Times ─────────────────────────────────
function renderRouteChart() {
  const container = routeChartRef.value
  if (!container) return
  d3.select(container).selectAll('svg').remove()

  const entries = perfMonitor.getRawEntries('routeNavigation')
  if (!entries.length) return

  // Aggregate by route
  const byRoute = new Map()
  for (const e of entries) {
    const route = e.meta?.route || 'unknown'
    if (!byRoute.has(route)) byRoute.set(route, [])
    byRoute.get(route).push(e.value)
  }
  const data = Array.from(byRoute, ([route, values]) => ({
    route,
    avg: d3.mean(values),
    p95: d3.quantile(values.sort(d3.ascending), 0.95) || d3.mean(values),
    count: values.length,
  })).sort((a, b) => b.avg - a.avg)

  const margin = { top: 10, right: 60, bottom: 30, left: 130 }
  const w = container.clientWidth
  const barH = 24
  const h = Math.max(120, data.length * barH + margin.top + margin.bottom)

  const svg = d3.select(container).append('svg').attr('width', w).attr('height', h)

  const maxVal = d3.max(data, (d) => d.p95) || 1
  const x = d3.scaleLinear().domain([0, maxVal * 1.15]).range([margin.left, w - margin.right])
  const y = d3
    .scaleBand()
    .domain(data.map((d) => d.route))
    .range([margin.top, h - margin.bottom])
    .padding(0.25)

  // p95 bars (lighter)
  svg
    .selectAll('rect.p95')
    .data(data)
    .enter()
    .append('rect')
    .attr('x', margin.left)
    .attr('y', (d) => y(d.route))
    .attr('width', (d) => Math.max(1, x(d.p95) - margin.left))
    .attr('height', y.bandwidth())
    .attr('rx', 3)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.2)

  // Avg bars
  svg
    .selectAll('rect.avg')
    .data(data)
    .enter()
    .append('rect')
    .attr('x', margin.left)
    .attr('y', (d) => y(d.route))
    .attr('width', (d) => Math.max(1, x(d.avg) - margin.left))
    .attr('height', y.bandwidth())
    .attr('rx', 3)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.75)

  // Route labels
  svg
    .selectAll('text.route')
    .data(data)
    .enter()
    .append('text')
    .attr('x', margin.left - 6)
    .attr('y', (d) => y(d.route) + y.bandwidth() / 2)
    .attr('text-anchor', 'end')
    .attr('dominant-baseline', 'middle')
    .attr('font-size', '11px')
    .attr('fill', COLORS.text)
    .text((d) => d.route)

  // Value labels
  svg
    .selectAll('text.val')
    .data(data)
    .enter()
    .append('text')
    .attr('x', (d) => x(d.p95) + 4)
    .attr('y', (d) => y(d.route) + y.bandwidth() / 2)
    .attr('dominant-baseline', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text((d) => `${d.avg.toFixed(1)}ms (×${d.count})`)
}

// ── API Response Histogram ─────────────────────────────────
function renderApiChart() {
  const container = apiChartRef.value
  if (!container) return
  d3.select(container).selectAll('svg').remove()

  const entries = perfMonitor.getRawEntries('apiResponse')
  if (!entries.length) return

  const values = entries.map((e) => e.value)
  const margin = { top: 10, right: 20, bottom: 36, left: 50 }
  const w = container.clientWidth
  const h = 180

  const svg = d3.select(container).append('svg').attr('width', w).attr('height', h)

  const maxVal = d3.max(values) || 1
  const x = d3.scaleLinear().domain([0, maxVal * 1.05]).range([margin.left, w - margin.right])

  const bins = d3.bin().domain(x.domain()).thresholds(20)(values)

  const y = d3
    .scaleLinear()
    .domain([0, d3.max(bins, (d) => d.length)])
    .range([h - margin.bottom, margin.top])

  svg
    .selectAll('rect')
    .data(bins)
    .enter()
    .append('rect')
    .attr('x', (d) => x(d.x0) + 1)
    .attr('y', (d) => y(d.length))
    .attr('width', (d) => Math.max(0, x(d.x1) - x(d.x0) - 1))
    .attr('height', (d) => y(0) - y(d.length))
    .attr('rx', 2)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.7)

  // X axis
  svg
    .append('g')
    .attr('transform', `translate(0,${h - margin.bottom})`)
    .call(
      d3
        .axisBottom(x)
        .ticks(8)
        .tickFormat((d) => `${d.toFixed(0)}ms`),
    )
    .call((g) => g.select('.domain').attr('stroke', COLORS.gridLine))
    .call((g) => g.selectAll('.tick line').attr('stroke', COLORS.gridLine))
    .call((g) => g.selectAll('.tick text').attr('fill', COLORS.muted).attr('font-size', '10px'))

  // Y axis
  svg
    .append('g')
    .attr('transform', `translate(${margin.left},0)`)
    .call(d3.axisLeft(y).ticks(4))
    .call((g) => g.select('.domain').remove())
    .call((g) => g.selectAll('.tick line').attr('stroke', COLORS.gridLine))
    .call((g) => g.selectAll('.tick text').attr('fill', COLORS.muted).attr('font-size', '10px'))

  // Label
  svg
    .append('text')
    .attr('x', w / 2)
    .attr('y', h - 4)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text('Response time (ms)')
}

function formatMs(val) {
  if (!val && val !== 0) return '—'
  return val < 1 ? '<1ms' : `${val.toFixed(1)}ms`
}

function ratingClass(metric, value) {
  if (!value) return 'text-[var(--color-text-muted)]'
  const thresholds = {
    avg: [100, 300],
    p95: [200, 500],
    p99: [500, 1000],
  }
  const [good, warn] = thresholds[metric] || [200, 500]
  if (value <= good) return 'text-[var(--color-success)]'
  if (value <= warn) return 'text-[var(--color-warning)]'
  return 'text-[var(--color-fin-orange)]'
}

onMounted(() => {
  nextTick(renderAll)
  resizeObserver = new ResizeObserver(() => nextTick(renderAll))
  if (waterfallRef.value) resizeObserver.observe(waterfallRef.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 md:mb-8">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">
          Performance Benchmark
        </h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1">
          Page load times and navigation metrics
        </p>
      </div>
      <div class="flex gap-2">
        <button
          @click="clearMetrics"
          class="px-3 py-1.5 text-sm border border-[var(--color-border)] rounded-lg text-[var(--color-text-secondary)] hover:border-[var(--color-border-strong)] transition-colors"
        >
          Clear
        </button>
        <button
          @click="refresh"
          class="px-3 py-1.5 text-sm bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- Summary Stats Cards -->
    <section class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
      <div
        v-for="(stat, key) in allStats"
        :key="key"
        class="border border-[var(--color-border)] rounded-lg p-3 bg-[var(--color-surface)]"
      >
        <div class="text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
          {{ key.replace(/([A-Z])/g, ' $1').trim() }}
        </div>
        <div class="text-lg font-semibold" :class="ratingClass('avg', stat.avg)">
          {{ formatMs(stat.avg) }}
        </div>
        <div class="text-xs text-[var(--color-text-muted)] mt-1">
          p95 {{ formatMs(stat.p95) }} · {{ stat.count }} samples
        </div>
      </div>
    </section>

    <!-- Web Vitals Waterfall -->
    <section class="mb-8">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-3">Page Load Waterfall</h2>
      <div
        ref="waterfallRef"
        class="border border-[var(--color-border)] rounded-lg p-4 bg-[var(--color-surface)] min-h-[160px]"
      >
        <p v-if="!webVitals" class="text-sm text-[var(--color-text-muted)] text-center py-8">
          No page load data yet. Timing is captured on initial page load.
        </p>
      </div>
      <div v-if="webVitals" class="flex flex-wrap gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
        <span>TTFB: <strong class="text-[var(--color-text)]">{{ formatMs(webVitals.ttfb) }}</strong></span>
        <span>FCP: <strong class="text-[var(--color-text)]">{{ formatMs(webVitals.fcp) }}</strong></span>
        <span>DCL: <strong class="text-[var(--color-text)]">{{ formatMs(webVitals.domContentLoaded) }}</strong></span>
        <span>Load: <strong class="text-[var(--color-text)]">{{ formatMs(webVitals.load) }}</strong></span>
        <span v-if="webVitals.transferSize">Transfer: <strong class="text-[var(--color-text)]">{{ (webVitals.transferSize / 1024).toFixed(1) }}KB</strong></span>
      </div>
    </section>

    <!-- Route Navigation Times -->
    <section class="mb-8">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-3">Route Navigation Times</h2>
      <div
        ref="routeChartRef"
        class="border border-[var(--color-border)] rounded-lg p-4 bg-[var(--color-surface)] min-h-[120px]"
      >
        <p
          v-if="!routeEntries.length"
          class="text-sm text-[var(--color-text-muted)] text-center py-8"
        >
          Navigate between pages to collect route timing data.
        </p>
      </div>
    </section>

    <!-- API Response Distribution -->
    <section class="mb-8">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-3">
        API Response Distribution
      </h2>
      <div
        ref="apiChartRef"
        class="border border-[var(--color-border)] rounded-lg p-4 bg-[var(--color-surface)] min-h-[120px]"
      >
        <p
          v-if="!apiEntries.length"
          class="text-sm text-[var(--color-text-muted)] text-center py-8"
        >
          Make API requests to collect response time data.
        </p>
      </div>
    </section>

    <!-- Info -->
    <section
      class="bg-[var(--color-primary-light)] border border-[#2068FF]/20 rounded-lg p-3 md:p-4"
    >
      <p class="text-xs text-[var(--color-text-secondary)]">
        Metrics are collected client-side via the
        <code class="bg-[var(--color-border)] px-1 rounded">Navigation Timing API</code>
        and in-app instrumentation. Data resets on page reload. Navigate between pages and make API
        calls to populate the charts.
      </p>
    </section>
  </div>
</template>
