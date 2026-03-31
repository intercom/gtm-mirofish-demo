<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Object, default: null },
})

const donutRef = ref(null)
const lineRef = ref(null)
const barRef = ref(null)

let resizeObserver = null
let resizeTimer = null

// ── Color palette (red-focused for churn) ──────────────────────────────
const COLORS = {
  churnDark: '#b91c1c',
  churnPrimary: '#ef4444',
  churnMedium: '#f87171',
  churnLight: '#fca5a5',
  churnLighter: '#fecaca',
  grossLine: '#ef4444',
  netLine: '#2068FF',
  text: '#050505',
  textSecondary: '#555',
  textMuted: '#888',
  grid: 'rgba(0,0,0,0.06)',
  reasons: ['#b91c1c', '#ef4444', '#f97316', '#f59e0b', '#8b5cf6', '#6b7280'],
  tiers: ['#fecaca', '#fca5a5', '#f87171', '#ef4444', '#dc2626'],
}

// ── Mock data (used when no prop data is provided) ─────────────────────
const DEFAULT_DATA = {
  summary: {
    logoChurnRate: 3.2,
    revenueChurnRate: 2.8,
    avgChurnedMrr: 4250,
  },
  reasons: [
    { label: 'Competitor switch', value: 28 },
    { label: 'Budget cuts', value: 22 },
    { label: 'Poor onboarding', value: 18 },
    { label: 'Missing features', value: 15 },
    { label: 'Support issues', value: 10 },
    { label: 'Other', value: 7 },
  ],
  monthlyTrend: [
    { month: 'Jul', gross: 4.1, net: 2.3 },
    { month: 'Aug', gross: 3.8, net: 2.0 },
    { month: 'Sep', gross: 4.5, net: 2.8 },
    { month: 'Oct', gross: 3.9, net: 1.9 },
    { month: 'Nov', gross: 3.6, net: 1.5 },
    { month: 'Dec', gross: 4.2, net: 2.4 },
    { month: 'Jan', gross: 3.4, net: 1.2 },
    { month: 'Feb', gross: 3.7, net: 1.6 },
    { month: 'Mar', gross: 3.3, net: 1.1 },
    { month: 'Apr', gross: 3.1, net: 0.8 },
    { month: 'May', gross: 3.5, net: 1.3 },
    { month: 'Jun', gross: 3.2, net: 1.0 },
  ],
  byTier: [
    { label: 'Starter', value: 5.8, mrr: 12400 },
    { label: 'Growth', value: 3.9, mrr: 28600 },
    { label: 'Scale', value: 2.4, mrr: 15200 },
    { label: 'Enterprise', value: 1.1, mrr: 8300 },
  ],
}

const chartData = computed(() => props.data || DEFAULT_DATA)

// ── Summary formatting ─────────────────────────────────────────────────
function formatMrr(value) {
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`
  return `$${value}`
}

// ── Render all charts ──────────────────────────────────────────────────
function renderAll() {
  renderDonut()
  renderLineChart()
  renderBarChart()
}

function clearAll() {
  ;[donutRef, lineRef, barRef].forEach((r) => {
    if (r.value) d3.select(r.value).selectAll('*').remove()
  })
}

// ── Donut chart: churn reasons distribution ────────────────────────────
function renderDonut() {
  const container = donutRef.value
  if (!container) return
  d3.select(container).selectAll('*').remove()

  const data = chartData.value.reasons
  const containerWidth = container.clientWidth
  const size = Math.min(containerWidth, 360)
  const radius = size / 2 - 40
  const innerRadius = radius * 0.55
  const totalHeight = size + 40

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg
    .append('g')
    .attr('transform', `translate(${containerWidth / 2},${size / 2 + 20})`)

  const pie = d3.pie().value((d) => d.value).sort(null).padAngle(0.02)

  const arc = d3.arc().innerRadius(innerRadius).outerRadius(radius).cornerRadius(3)

  const labelArc = d3
    .arc()
    .innerRadius(radius + 14)
    .outerRadius(radius + 14)

  const arcs = pie(data)

  // Animate arcs
  g.selectAll('.arc')
    .data(arcs)
    .join('path')
    .attr('fill', (d, i) => COLORS.reasons[i])
    .attr('opacity', 0.9)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .transition()
    .duration(600)
    .delay((d, i) => i * 70)
    .ease(d3.easeCubicOut)
    .attrTween('d', function (d) {
      const interp = d3.interpolate({ startAngle: d.startAngle, endAngle: d.startAngle }, d)
      return (t) => arc(interp(t))
    })

  // Center label
  const total = d3.sum(data, (d) => d.value)
  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .attr('font-size', '22px')
    .attr('font-weight', '700')
    .attr('fill', COLORS.churnPrimary)
    .style('opacity', 0)
    .text(`${total}%`)
    .transition()
    .duration(400)
    .delay(500)
    .style('opacity', 1)

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .attr('font-size', '11px')
    .attr('fill', COLORS.textMuted)
    .style('opacity', 0)
    .text('of churned accounts')
    .transition()
    .duration(400)
    .delay(550)
    .style('opacity', 1)

  // Labels with connector lines
  const labelGroups = g
    .selectAll('.label-group')
    .data(arcs)
    .join('g')
    .style('opacity', 0)

  labelGroups.each(function (d, i) {
    const group = d3.select(this)
    const pos = labelArc.centroid(d)
    const midAngle = (d.startAngle + d.endAngle) / 2
    const isRight = midAngle < Math.PI
    const xOff = isRight ? 10 : -10
    const arcMid = arc.centroid(d)

    group
      .append('line')
      .attr('x1', arcMid[0] * 1.12)
      .attr('y1', arcMid[1] * 1.12)
      .attr('x2', pos[0] + xOff)
      .attr('y2', pos[1])
      .attr('stroke', 'rgba(0,0,0,0.12)')
      .attr('stroke-width', 1)

    group
      .append('text')
      .attr('x', pos[0] + xOff * 2)
      .attr('y', pos[1])
      .attr('dy', '-0.3em')
      .attr('text-anchor', isRight ? 'start' : 'end')
      .attr('font-size', '11px')
      .attr('fill', COLORS.textSecondary)
      .text(data[i].label)

    group
      .append('text')
      .attr('x', pos[0] + xOff * 2)
      .attr('y', pos[1])
      .attr('dy', '0.9em')
      .attr('text-anchor', isRight ? 'start' : 'end')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.reasons[i])
      .text(`${data[i].value}%`)
  })

  labelGroups
    .transition()
    .duration(300)
    .delay((d, i) => 500 + i * 70)
    .style('opacity', 1)
}

// ── Line chart: monthly gross & net churn rate ─────────────────────────
function renderLineChart() {
  const container = lineRef.value
  if (!container) return
  d3.select(container).selectAll('*').remove()

  const data = chartData.value.monthlyTrend
  const containerWidth = container.clientWidth
  const margin = { top: 16, right: 24, bottom: 32, left: 44 }
  const width = containerWidth - margin.left - margin.right
  const height = 220
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3
    .scalePoint()
    .domain(data.map((d) => d.month))
    .range([0, width])
    .padding(0.3)

  const yMax = Math.ceil(d3.max(data, (d) => d.gross) + 0.5)
  const y = d3.scaleLinear().domain([0, yMax]).range([height, 0])

  // Grid
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', (d) => y(d))
    .attr('y2', (d) => y(d))
    .attr('stroke', COLORS.grid)
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', (d) => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', COLORS.textMuted)
    .text((d) => `${d}%`)

  // X-axis labels
  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', (d) => x(d.month))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.textMuted)
    .text((d) => d.month)

  // Line generators
  const lineGen = d3
    .line()
    .x((d) => x(d.month))
    .curve(d3.curveMonotoneX)

  // Gross churn line
  const grossLine = lineGen.y((d) => y(d.gross))
  const grossPath = g
    .append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', COLORS.grossLine)
    .attr('stroke-width', 2.5)
    .attr('d', grossLine)

  const grossLen = grossPath.node().getTotalLength()
  grossPath
    .attr('stroke-dasharray', `${grossLen} ${grossLen}`)
    .attr('stroke-dashoffset', grossLen)
    .transition()
    .duration(800)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)

  // Net churn line
  const netLine = lineGen.y((d) => y(d.net))
  const netPath = g
    .append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', COLORS.netLine)
    .attr('stroke-width', 2.5)
    .attr('stroke-dasharray', '6,3')
    .attr('d', netLine)

  const netLen = netPath.node().getTotalLength()
  netPath
    .attr('stroke-dasharray', `${netLen} ${netLen}`)
    .attr('stroke-dashoffset', netLen)
    .transition()
    .duration(800)
    .delay(200)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)
    .on('end', function () {
      d3.select(this).attr('stroke-dasharray', '6,3')
    })

  // Dots — gross
  g.selectAll('.dot-gross')
    .data(data)
    .join('circle')
    .attr('cx', (d) => x(d.month))
    .attr('cy', (d) => y(d.gross))
    .attr('r', 0)
    .attr('fill', '#fff')
    .attr('stroke', COLORS.grossLine)
    .attr('stroke-width', 2)
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 40)
    .attr('r', 3.5)

  // Dots — net
  g.selectAll('.dot-net')
    .data(data)
    .join('circle')
    .attr('cx', (d) => x(d.month))
    .attr('cy', (d) => y(d.net))
    .attr('r', 0)
    .attr('fill', '#fff')
    .attr('stroke', COLORS.netLine)
    .attr('stroke-width', 2)
    .transition()
    .duration(300)
    .delay((d, i) => 800 + i * 40)
    .attr('r', 3.5)

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${containerWidth - margin.right - 200}, 8)`)

  legend.append('line').attr('x1', 0).attr('y1', 6).attr('x2', 18).attr('y2', 6).attr('stroke', COLORS.grossLine).attr('stroke-width', 2.5)
  legend.append('text').attr('x', 24).attr('y', 10).attr('font-size', '11px').attr('fill', COLORS.textSecondary).text('Gross Churn')

  legend.append('line').attr('x1', 100).attr('y1', 6).attr('x2', 118).attr('y2', 6).attr('stroke', COLORS.netLine).attr('stroke-width', 2.5).attr('stroke-dasharray', '4,2')
  legend.append('text').attr('x', 124).attr('y', 10).attr('font-size', '11px').attr('fill', COLORS.textSecondary).text('Net Churn')
}

// ── Bar chart: churn rate by plan tier ─────────────────────────────────
function renderBarChart() {
  const container = barRef.value
  if (!container) return
  d3.select(container).selectAll('*').remove()

  const data = chartData.value.byTier
  const containerWidth = container.clientWidth
  const margin = { top: 16, right: 24, bottom: 40, left: 44 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3
    .scaleBand()
    .domain(data.map((d) => d.label))
    .range([0, width])
    .padding(0.35)

  const yMax = Math.ceil(d3.max(data, (d) => d.value) + 1)
  const y = d3.scaleLinear().domain([0, yMax]).range([height, 0])

  // Grid
  const yTicks = y.ticks(4)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', (d) => y(d))
    .attr('y2', (d) => y(d))
    .attr('stroke', COLORS.grid)
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', (d) => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', COLORS.textMuted)
    .text((d) => `${d}%`)

  // X-axis labels
  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', (d) => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', COLORS.textSecondary)
    .text((d) => d.label)

  // MRR sub-labels
  g.selectAll('.mrr-label')
    .data(data)
    .join('text')
    .attr('x', (d) => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 30)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', COLORS.textMuted)
    .text((d) => formatMrr(d.mrr))

  // Color scale: higher churn = darker red
  const colorScale = d3
    .scaleLinear()
    .domain([d3.min(data, (d) => d.value), d3.max(data, (d) => d.value)])
    .range([COLORS.churnLighter, COLORS.churnDark])

  // Bars with animation
  g.selectAll('.bar')
    .data(data)
    .join('rect')
    .attr('x', (d) => x(d.label))
    .attr('y', height)
    .attr('width', x.bandwidth())
    .attr('height', 0)
    .attr('rx', 4)
    .attr('fill', (d) => colorScale(d.value))
    .attr('opacity', 0.9)
    .transition()
    .duration(600)
    .delay((d, i) => i * 100)
    .ease(d3.easeCubicOut)
    .attr('y', (d) => y(d.value))
    .attr('height', (d) => height - y(d.value))

  // Value labels on bars
  g.selectAll('.bar-value')
    .data(data)
    .join('text')
    .attr('x', (d) => x(d.label) + x.bandwidth() / 2)
    .attr('y', (d) => y(d.value) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.churnPrimary)
    .style('opacity', 0)
    .text((d) => `${d.value}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 100)
    .style('opacity', 1)
}

// ── Lifecycle ──────────────────────────────────────────────────────────
watch(() => props.data, () => {
  nextTick(() => {
    clearAll()
    renderAll()
  })
}, { deep: true })

onMounted(() => {
  nextTick(() => renderAll())

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      clearAll()
      renderAll()
    }, 200)
  })
  if (donutRef.value) resizeObserver.observe(donutRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="bg-white border border-black/10 rounded-lg p-4">
        <p class="text-xs text-[#888] uppercase tracking-wide font-medium">Logo Churn Rate</p>
        <p class="text-2xl font-bold text-[#ef4444] mt-1">
          {{ chartData.summary.logoChurnRate }}%
        </p>
        <p class="text-xs text-[#888] mt-1">monthly</p>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-4">
        <p class="text-xs text-[#888] uppercase tracking-wide font-medium">Revenue Churn Rate</p>
        <p class="text-2xl font-bold text-[#ef4444] mt-1">
          {{ chartData.summary.revenueChurnRate }}%
        </p>
        <p class="text-xs text-[#888] mt-1">monthly</p>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-4">
        <p class="text-xs text-[#888] uppercase tracking-wide font-medium">Avg Churned MRR</p>
        <p class="text-2xl font-bold text-[#b91c1c] mt-1">
          {{ formatMrr(chartData.summary.avgChurnedMrr) }}
        </p>
        <p class="text-xs text-[#888] mt-1">per account</p>
      </div>
    </div>

    <!-- Donut: Churn Reasons -->
    <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
      <h3 class="text-sm font-semibold text-[#050505] mb-1">Churn Reasons</h3>
      <p class="text-xs text-[#888] mb-4">Distribution of why customers leave</p>
      <div ref="donutRef" class="w-full" />
    </div>

    <!-- Line: Monthly Churn Rate Trend -->
    <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
      <h3 class="text-sm font-semibold text-[#050505] mb-1">Monthly Churn Rate Trend</h3>
      <p class="text-xs text-[#888] mb-4">Gross vs net churn over the past 12 months</p>
      <div ref="lineRef" class="w-full" />
    </div>

    <!-- Bar: Churn by Plan Tier -->
    <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
      <h3 class="text-sm font-semibold text-[#050505] mb-1">Churn by Plan Tier</h3>
      <p class="text-xs text-[#888] mb-4">Which plans churn most? (churned MRR shown below tier)</p>
      <div ref="barRef" class="w-full" />
    </div>
  </div>
</template>
