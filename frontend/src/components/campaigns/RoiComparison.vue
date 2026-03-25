<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'
import { campaignsApi } from '../../api/campaigns'

const props = defineProps({
  simulationId: { type: String, default: null },
})

const chartRef = ref(null)
const activeView = ref('roi')
const loading = ref(false)
const error = ref(null)
const campaigns = ref([])
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  navy: '#050505',
  green: '#009900',
  red: '#ef4444',
  text: '#050505',
  muted: '#888888',
  gridLine: 'rgba(0,0,0,0.06)',
  barBg: 'rgba(0,0,0,0.03)',
}

const DEMO_CAMPAIGNS = [
  { name: 'Intercom AI Email Drip', spend: 42000, revenue: 186000, leads: 840, acquisitions: 68, channel: 'email' },
  { name: 'Google Ads — Support', spend: 85000, revenue: 221000, leads: 1200, acquisitions: 94, channel: 'paid' },
  { name: 'LinkedIn ABM Campaign', spend: 62000, revenue: 148000, leads: 520, acquisitions: 41, channel: 'paid' },
  { name: 'SaaStr Booth + Talk', spend: 95000, revenue: 310000, leads: 380, acquisitions: 52, channel: 'events' },
  { name: 'Partner Co-Sell (AWS)', spend: 18000, revenue: 92000, leads: 160, acquisitions: 22, channel: 'partner' },
  { name: 'Product Hunt Launch', spend: 5000, revenue: 34000, leads: 620, acquisitions: 38, channel: 'organic' },
  { name: 'Zendesk Displacement SEO', spend: 31000, revenue: 87000, leads: 950, acquisitions: 56, channel: 'organic' },
  { name: 'Facebook Retargeting', spend: 28000, revenue: 19000, leads: 310, acquisitions: 12, channel: 'paid' },
  { name: 'Webinar Series Q1', spend: 22000, revenue: 64000, leads: 440, acquisitions: 29, channel: 'events' },
  { name: 'Cold Outbound (SDR)', spend: 74000, revenue: 58000, leads: 280, acquisitions: 18, channel: 'outbound' },
]

const enrichedCampaigns = computed(() =>
  campaigns.value.map((c) => ({
    ...c,
    roi: ((c.revenue - c.spend) / c.spend) * 100,
    cpl: c.leads > 0 ? c.spend / c.leads : 0,
    cpa: c.acquisitions > 0 ? c.spend / c.acquisitions : 0,
  })),
)

const views = [
  { key: 'roi', label: 'ROI Ranking' },
  { key: 'scatter', label: 'Spend vs Revenue' },
  { key: 'efficiency', label: 'Efficiency (CPL/CPA)' },
]

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const { data } = await campaignsApi.roiComparison()
    if (data.campaigns?.length) {
      campaigns.value = data.campaigns
      return
    }
  } catch {
    // API not available — fall through to demo data
  }
  campaigns.value = DEMO_CAMPAIGNS
  loading.value = false
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function renderActiveView() {
  clearChart()
  if (!chartRef.value) return
  const renderers = { roi: renderRoiBar, scatter: renderScatter, efficiency: renderEfficiency }
  const fn = renderers[activeView.value]
  if (fn) nextTick(() => fn())
}

// ── View 1: Horizontal Bar Chart — ROI Ranking ──

function renderRoiBar() {
  const container = chartRef.value
  if (!container) return

  const data = [...enrichedCampaigns.value].sort((a, b) => b.roi - a.roi)
  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 80, bottom: 24, left: 180 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 32
  const barGap = 10
  const height = data.length * (barHeight + barGap) - barGap
  const totalHeight = height + margin.top + margin.bottom

  const maxAbs = d3.max(data, (d) => Math.abs(d.roi))
  const domainMax = Math.ceil(maxAbs / 50) * 50

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg
    .append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Campaign ROI Comparison')

  svg
    .append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Return on investment ranked by percentage')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear().domain([-domainMax, domainMax]).range([0, width])

  const y = d3
    .scaleBand()
    .domain(data.map((d) => d.name))
    .range([0, height])
    .padding(barGap / (barHeight + barGap))

  // Zero line
  g.append('line')
    .attr('x1', x(0))
    .attr('x2', x(0))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-width', 1)

  // Grid
  const ticks = x.ticks(6)
  g.selectAll('.grid-line')
    .data(ticks)
    .join('line')
    .attr('x1', (d) => x(d))
    .attr('x2', (d) => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', COLORS.gridLine)
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.x-label')
    .data(ticks)
    .join('text')
    .attr('x', (d) => x(d))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text((d) => `${d > 0 ? '+' : ''}${d}%`)

  // Labels
  g.selectAll('.bar-label')
    .data(data)
    .join('text')
    .attr('x', -8)
    .attr('y', (d) => y(d.name) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text((d) => d.name)

  // Bars
  g.selectAll('.bar')
    .data(data)
    .join('rect')
    .attr('x', (d) => (d.roi >= 0 ? x(0) : x(0)))
    .attr('y', (d) => y(d.name))
    .attr('width', 0)
    .attr('height', y.bandwidth())
    .attr('rx', 3)
    .attr('fill', (d) => (d.roi >= 0 ? COLORS.green : COLORS.red))
    .attr('opacity', 0.8)
    .transition()
    .duration(600)
    .delay((d, i) => i * 60)
    .ease(d3.easeCubicOut)
    .attr('x', (d) => (d.roi >= 0 ? x(0) : x(d.roi)))
    .attr('width', (d) => Math.abs(x(d.roi) - x(0)))

  // ROI value labels
  g.selectAll('.bar-value')
    .data(data)
    .join('text')
    .attr('x', (d) => (d.roi >= 0 ? x(d.roi) + 6 : x(d.roi) - 6))
    .attr('y', (d) => y(d.name) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', (d) => (d.roi >= 0 ? 'start' : 'end'))
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .style('opacity', 0)
    .text((d) => `${d.roi >= 0 ? '+' : ''}${d.roi.toFixed(0)}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 60)
    .style('opacity', 1)

  // Spend/Revenue annotations
  g.selectAll('.bar-meta')
    .data(data)
    .join('text')
    .attr('x', (d) => (d.roi >= 0 ? x(d.roi) + 6 : x(d.roi) - 6))
    .attr('y', (d) => y(d.name) + y.bandwidth() / 2 + 13)
    .attr('text-anchor', (d) => (d.roi >= 0 ? 'start' : 'end'))
    .attr('font-size', '9px')
    .attr('fill', COLORS.muted)
    .style('opacity', 0)
    .text((d) => `$${(d.spend / 1000).toFixed(0)}k → $${(d.revenue / 1000).toFixed(0)}k`)
    .transition()
    .duration(300)
    .delay((d, i) => 700 + i * 60)
    .style('opacity', 1)
}

// ── View 2: Scatter Plot — Spend vs Revenue ──

function renderScatter() {
  const container = chartRef.value
  if (!container) return

  const data = enrichedCampaigns.value
  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 40, bottom: 56, left: 64 }
  const width = containerWidth - margin.left - margin.right
  const height = 360
  const totalHeight = height + margin.top + margin.bottom

  const maxSpend = d3.max(data, (d) => d.spend) * 1.15
  const maxRevenue = d3.max(data, (d) => d.revenue) * 1.15
  const maxLeads = d3.max(data, (d) => d.leads)

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg
    .append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Spend vs Revenue')

  svg
    .append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Bubble size = lead volume · Diagonal = break-even line')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear().domain([0, maxSpend]).range([0, width])
  const y = d3.scaleLinear().domain([0, maxRevenue]).range([height, 0])
  const r = d3.scaleSqrt().domain([0, maxLeads]).range([6, 32])

  // Grid
  g.selectAll('.grid-x')
    .data(x.ticks(5))
    .join('line')
    .attr('x1', (d) => x(d))
    .attr('x2', (d) => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', COLORS.gridLine)
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.grid-y')
    .data(y.ticks(5))
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', (d) => y(d))
    .attr('y2', (d) => y(d))
    .attr('stroke', COLORS.gridLine)
    .attr('stroke-dasharray', '2,3')

  // Break-even diagonal
  const diagMax = Math.min(maxSpend, maxRevenue)
  g.append('line')
    .attr('x1', x(0))
    .attr('y1', y(0))
    .attr('x2', x(diagMax))
    .attr('y2', y(diagMax))
    .attr('stroke', 'rgba(0,0,0,0.12)')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '6,4')

  // Quadrant labels
  const midX = width / 2
  const midY = height / 2
  const quadrants = [
    { label: 'Low Spend / High Return', x: midX * 0.4, y: midY * 0.25, fill: COLORS.green },
    { label: 'High Spend / High Return', x: midX * 1.6, y: midY * 0.25, fill: COLORS.primary },
    { label: 'Low Spend / Low Return', x: midX * 0.4, y: midY * 1.75, fill: COLORS.muted },
    { label: 'High Spend / Low Return', x: midX * 1.6, y: midY * 1.75, fill: COLORS.red },
  ]

  g.selectAll('.quadrant-label')
    .data(quadrants)
    .join('text')
    .attr('x', (d) => d.x)
    .attr('y', (d) => d.y)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '500')
    .attr('fill', (d) => d.fill)
    .attr('opacity', 0.45)
    .text((d) => d.label)

  // Axis labels
  g.selectAll('.x-tick')
    .data(x.ticks(5))
    .join('text')
    .attr('x', (d) => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text((d) => `$${(d / 1000).toFixed(0)}k`)

  svg
    .append('text')
    .attr('x', margin.left + width / 2)
    .attr('y', totalHeight - 8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Spend')

  g.selectAll('.y-tick')
    .data(y.ticks(5))
    .join('text')
    .attr('x', -8)
    .attr('y', (d) => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text((d) => `$${(d / 1000).toFixed(0)}k`)

  svg
    .append('text')
    .attr('transform', `translate(14,${margin.top + height / 2}) rotate(-90)`)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Revenue')

  // Bubbles
  const bubbles = g
    .selectAll('.bubble')
    .data(data)
    .join('circle')
    .attr('cx', (d) => x(d.spend))
    .attr('cy', (d) => y(d.revenue))
    .attr('r', 0)
    .attr('fill', (d) => (d.revenue > d.spend ? COLORS.primary : COLORS.orange))
    .attr('opacity', 0.7)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)

  bubbles
    .transition()
    .duration(500)
    .delay((d, i) => i * 50)
    .ease(d3.easeCubicOut)
    .attr('r', (d) => r(d.leads))

  // Tooltip labels on hover (use title for simplicity)
  bubbles.append('title').text((d) => {
    const roi = ((d.revenue - d.spend) / d.spend * 100).toFixed(0)
    return `${d.name}\nSpend: $${(d.spend / 1000).toFixed(0)}k\nRevenue: $${(d.revenue / 1000).toFixed(0)}k\nLeads: ${d.leads}\nROI: ${roi}%`
  })

  // Campaign name labels for larger bubbles
  g.selectAll('.bubble-label')
    .data(data.filter((d) => r(d.leads) > 14))
    .join('text')
    .attr('x', (d) => x(d.spend))
    .attr('y', (d) => y(d.revenue) - r(d.leads) - 4)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', '#555')
    .style('opacity', 0)
    .text((d) => d.name.length > 20 ? d.name.slice(0, 18) + '…' : d.name)
    .transition()
    .duration(300)
    .delay((d, i) => 500 + i * 50)
    .style('opacity', 1)
}

// ── View 3: Efficiency — CPL & CPA ──

function renderEfficiency() {
  const container = chartRef.value
  if (!container) return

  const data = [...enrichedCampaigns.value].sort((a, b) => a.cpl - b.cpl)
  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 60, left: 180 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 24
  const groupGap = 16
  const groupHeight = barHeight * 2 + 4
  const height = data.length * (groupHeight + groupGap) - groupGap
  const totalHeight = height + margin.top + margin.bottom

  const maxCPA = d3.max(data, (d) => d.cpa)

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg
    .append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Cost Efficiency by Campaign')

  svg
    .append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Cost per lead (CPL) and cost per acquisition (CPA)')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3
    .scaleLinear()
    .domain([0, maxCPA * 1.1])
    .range([0, width])

  // Grid
  const ticks = x.ticks(5)
  g.selectAll('.grid-line')
    .data(ticks)
    .join('line')
    .attr('x1', (d) => x(d))
    .attr('x2', (d) => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', COLORS.gridLine)
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.x-label')
    .data(ticks)
    .join('text')
    .attr('x', (d) => x(d))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text((d) => `$${d.toFixed(0)}`)

  // Campaign groups
  data.forEach((campaign, i) => {
    const yOffset = i * (groupHeight + groupGap)

    // Label
    g.append('text')
      .attr('x', -8)
      .attr('y', yOffset + groupHeight / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(campaign.name)

    // CPL bar
    g.append('rect')
      .attr('x', 0)
      .attr('y', yOffset)
      .attr('width', 0)
      .attr('height', barHeight)
      .attr('rx', 3)
      .attr('fill', COLORS.primary)
      .attr('opacity', 0.8)
      .transition()
      .duration(600)
      .delay(i * 50)
      .ease(d3.easeCubicOut)
      .attr('width', x(campaign.cpl))

    // CPL value
    g.append('text')
      .attr('x', x(campaign.cpl) + 6)
      .attr('y', yOffset + barHeight / 2)
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.primary)
      .style('opacity', 0)
      .text(`$${campaign.cpl.toFixed(0)} CPL`)
      .transition()
      .duration(300)
      .delay(600 + i * 50)
      .style('opacity', 1)

    // CPA bar
    g.append('rect')
      .attr('x', 0)
      .attr('y', yOffset + barHeight + 4)
      .attr('width', 0)
      .attr('height', barHeight)
      .attr('rx', 3)
      .attr('fill', COLORS.orange)
      .attr('opacity', 0.8)
      .transition()
      .duration(600)
      .delay(i * 50 + 30)
      .ease(d3.easeCubicOut)
      .attr('width', x(campaign.cpa))

    // CPA value
    g.append('text')
      .attr('x', x(campaign.cpa) + 6)
      .attr('y', yOffset + barHeight + 4 + barHeight / 2)
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.orange)
      .style('opacity', 0)
      .text(`$${campaign.cpa.toFixed(0)} CPA`)
      .transition()
      .duration(300)
      .delay(630 + i * 50)
      .style('opacity', 1)
  })

  // Legend
  const legend = svg
    .append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 200}, 14)`)

  legend
    .append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', 10)
    .attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.8)
  legend.append('text').attr('x', 16).attr('y', 9).attr('font-size', '11px').attr('fill', '#555').text('Cost per Lead')

  legend
    .append('rect')
    .attr('x', 110)
    .attr('y', 0)
    .attr('width', 10)
    .attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0.8)
  legend.append('text').attr('x', 126).attr('y', 9).attr('font-size', '11px').attr('fill', '#555').text('Cost per Acq.')
}

// ── Lifecycle ──

watch(activeView, () => renderActiveView())

onMounted(async () => {
  await fetchData()
  renderActiveView()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderActiveView(), 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[--color-surface] border border-[--color-border] rounded-lg p-4 md:p-6">
    <!-- View toggle -->
    <div class="flex gap-1 mb-4 bg-black/5 rounded-lg p-1 w-fit">
      <button
        v-for="view in views"
        :key="view.key"
        :class="[
          'px-3 py-1.5 text-xs font-medium rounded-md transition-colors cursor-pointer',
          activeView === view.key
            ? 'bg-[--color-primary] text-white'
            : 'text-[--color-text-secondary] hover:text-[--color-text]',
        ]"
        @click="activeView = view.key"
      >
        {{ view.label }}
      </button>
    </div>

    <!-- Chart area -->
    <div v-if="loading" class="flex items-center justify-center h-48 text-[--color-text-muted] text-sm">
      Loading campaign data…
    </div>
    <div v-else-if="error" class="flex items-center justify-center h-48 text-[--color-error] text-sm">
      {{ error }}
    </div>
    <div v-else ref="chartRef" class="w-full" />
  </div>
</template>
