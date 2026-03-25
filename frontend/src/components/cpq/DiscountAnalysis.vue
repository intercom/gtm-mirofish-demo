<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  quotes: { type: Array, default: null },
})

const chartRef = ref(null)
const tooltipRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  text: '#050505',
  approved: '#009900',
  rejected: '#e53e3e',
  draft: '#999999',
  review: '#d69e2e',
}

const STATUS_COLORS = {
  Approved: COLORS.approved,
  Rejected: COLORS.rejected,
  Draft: COLORS.draft,
  Review: COLORS.review,
}

const DEMO_QUOTES = [
  { id: 'Q-1001', account: 'Acme Corp', total: 14200, discount_pct: 5.0, status: 'Approved', line_items: 2 },
  { id: 'Q-1002', account: 'TechNova Inc', total: 87500, discount_pct: 12.5, status: 'Approved', line_items: 4 },
  { id: 'Q-1003', account: 'GlobalRetail', total: 42000, discount_pct: 8.0, status: 'Review', line_items: 3 },
  { id: 'Q-1004', account: 'Meridian Health', total: 195000, discount_pct: 22.0, status: 'Rejected', line_items: 5 },
  { id: 'Q-1005', account: 'FinServ Partners', total: 63000, discount_pct: 15.0, status: 'Approved', line_items: 3 },
  { id: 'Q-1006', account: 'EduFirst', total: 8500, discount_pct: 3.0, status: 'Draft', line_items: 2 },
  { id: 'Q-1007', account: 'CloudScale', total: 125000, discount_pct: 18.0, status: 'Review', line_items: 4 },
  { id: 'Q-1008', account: 'DataDriven Co', total: 31500, discount_pct: 10.0, status: 'Approved', line_items: 3 },
  { id: 'Q-1009', account: 'Bright Logistics', total: 52000, discount_pct: 7.5, status: 'Draft', line_items: 2 },
  { id: 'Q-1010', account: 'Nexus Media', total: 175000, discount_pct: 20.0, status: 'Approved', line_items: 5 },
  { id: 'Q-1011', account: 'SafeGuard Sec', total: 28000, discount_pct: 6.0, status: 'Draft', line_items: 2 },
  { id: 'Q-1012', account: 'Omni Retail', total: 98000, discount_pct: 14.0, status: 'Approved', line_items: 4 },
  { id: 'Q-1013', account: 'Pioneer Labs', total: 145000, discount_pct: 19.5, status: 'Review', line_items: 5 },
  { id: 'Q-1014', account: 'Velocity SaaS', total: 55000, discount_pct: 11.0, status: 'Approved', line_items: 3 },
  { id: 'Q-1015', account: 'Greenfield Mfg', total: 210000, discount_pct: 24.0, status: 'Rejected', line_items: 5 },
  { id: 'Q-1016', account: 'Summit Analytics', total: 36000, discount_pct: 9.0, status: 'Draft', line_items: 3 },
  { id: 'Q-1017', account: 'UrbanTech', total: 72000, discount_pct: 13.0, status: 'Review', line_items: 3 },
  { id: 'Q-1018', account: 'Atlas Shipping', total: 19500, discount_pct: 4.0, status: 'Approved', line_items: 2 },
  { id: 'Q-1019', account: 'Quantum Finance', total: 158000, discount_pct: 21.0, status: 'Rejected', line_items: 4 },
  { id: 'Q-1020', account: 'CoreBuild Inc', total: 48000, discount_pct: 10.5, status: 'Approved', line_items: 3 },
]

function getData() {
  return props.quotes || DEMO_QUOTES
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('svg').remove()
}

function showTooltip(event, d) {
  const tip = tooltipRef.value
  if (!tip) return

  tip.innerHTML = `
    <div style="font-weight:600;margin-bottom:4px;">${d.id} — ${d.account}</div>
    <div>Total: <strong>$${d.total.toLocaleString()}</strong></div>
    <div>Discount: <strong>${d.discount_pct}%</strong></div>
    <div>Status: <span style="color:${STATUS_COLORS[d.status]};font-weight:600;">${d.status}</span></div>
  `
  tip.style.opacity = '1'

  const rect = chartRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left + 12
  const y = event.clientY - rect.top - 10

  const tipWidth = tip.offsetWidth
  const adjustedX = x + tipWidth > rect.width ? x - tipWidth - 24 : x

  tip.style.left = `${adjustedX}px`
  tip.style.top = `${y}px`
}

function hideTooltip() {
  const tip = tooltipRef.value
  if (tip) tip.style.opacity = '0'
}

function computeTrendLine(data) {
  const ranges = [
    [0, 50000],
    [50000, 100000],
    [100000, 150000],
    [150000, 200000],
    [200000, 250000],
  ]

  return ranges
    .map(([lo, hi]) => {
      const bucket = data.filter(d => d.total >= lo && d.total < hi)
      if (bucket.length === 0) return null
      return {
        x: (lo + hi) / 2,
        y: d3.mean(bucket, d => d.discount_pct),
      }
    })
    .filter(Boolean)
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const data = getData()
  if (!data.length) return

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 48, left: 56 }
  const width = containerWidth - margin.left - margin.right
  const height = 340
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  // Title
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Discount Analysis')

  // Subtitle
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Deal size vs. discount percentage by quote status')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const maxTotal = d3.max(data, d => d.total) * 1.1
  const x = d3.scaleLinear()
    .domain([0, Math.ceil(maxTotal / 50000) * 50000])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([0, 30])
    .range([height, 0])

  const r = d3.scaleSqrt()
    .domain([1, 5])
    .range([5, 14])

  // Grid lines
  const xTicks = x.ticks(5)
  const yTicks = y.ticks(6)

  g.selectAll('.grid-x')
    .data(xTicks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.grid-y')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Reference lines at 10% and 20%
  const refLines = [
    { pct: 10, label: '10% threshold', color: COLORS.primary },
    { pct: 20, label: '20% threshold', color: COLORS.orange },
  ]

  refLines.forEach(({ pct, label, color }) => {
    g.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', y(pct))
      .attr('y2', y(pct))
      .attr('stroke', color)
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '6,4')
      .attr('opacity', 0.5)

    g.append('text')
      .attr('x', width - 4)
      .attr('y', y(pct) - 6)
      .attr('text-anchor', 'end')
      .attr('font-size', '10px')
      .attr('font-weight', '500')
      .attr('fill', color)
      .attr('opacity', 0.8)
      .text(label)
  })

  // X-axis labels
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => d >= 1000 ? `$${d / 1000}k` : `$${d}`)

  // X-axis title
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height + 40)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Deal Size')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => `${d}%`)

  // Y-axis title
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -height / 2)
    .attr('y', -44)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Discount %')

  // Trend line
  const trendData = computeTrendLine(data)
  if (trendData.length >= 2) {
    const line = d3.line()
      .x(d => x(d.x))
      .y(d => y(d.y))
      .curve(d3.curveMonotoneX)

    const pathEl = g.append('path')
      .datum(trendData)
      .attr('fill', 'none')
      .attr('stroke', COLORS.primary)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', function () {
        return this.getTotalLength()
      })
      .attr('stroke-dashoffset', function () {
        return this.getTotalLength()
      })
      .attr('d', line)
      .attr('opacity', 0.6)

    pathEl.transition()
      .duration(800)
      .delay(400)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
  }

  // Data points (scatter dots)
  g.selectAll('.dot')
    .data(data)
    .join('circle')
    .attr('cx', d => x(d.total))
    .attr('cy', d => y(d.discount_pct))
    .attr('r', 0)
    .attr('fill', d => STATUS_COLORS[d.status] || COLORS.draft)
    .attr('opacity', 0.8)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .on('mouseenter', function (event, d) {
      d3.select(this)
        .transition().duration(150)
        .attr('opacity', 1)
        .attr('stroke-width', 2.5)
      showTooltip(event, d)
    })
    .on('mousemove', function (event, d) {
      showTooltip(event, d)
    })
    .on('mouseleave', function () {
      d3.select(this)
        .transition().duration(150)
        .attr('opacity', 0.8)
        .attr('stroke-width', 1.5)
      hideTooltip()
    })
    .transition()
    .duration(500)
    .delay((d, i) => i * 30)
    .ease(d3.easeCubicOut)
    .attr('r', d => r(d.line_items))

  // Legend
  const statuses = ['Approved', 'Review', 'Draft', 'Rejected']
  const legend = svg.append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 280}, 14)`)

  statuses.forEach((status, i) => {
    const xOff = i * 72

    legend.append('circle')
      .attr('cx', xOff + 5)
      .attr('cy', 5)
      .attr('r', 5)
      .attr('fill', STATUS_COLORS[status])
      .attr('opacity', 0.85)

    legend.append('text')
      .attr('x', xOff + 14)
      .attr('y', 9)
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(status)
  })
}

onMounted(() => {
  nextTick(() => renderChart())

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderChart(), 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
    <div ref="chartRef" class="w-full relative">
      <div
        ref="tooltipRef"
        class="absolute pointer-events-none z-10 bg-white border border-black/10 rounded-lg shadow-md px-3 py-2 text-xs leading-relaxed opacity-0 transition-opacity duration-150"
        style="max-width: 220px"
      />
    </div>
  </div>
</template>
