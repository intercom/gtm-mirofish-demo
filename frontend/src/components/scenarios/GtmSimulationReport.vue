<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'
import { API_BASE } from '../../api/client'

const props = defineProps({
  simulationId: { type: String, required: true },
})

const loading = ref(true)
const error = ref(null)
const activeSection = ref(0)
const reportData = ref(null)
const copySuccess = ref(false)

const pipelineChartRef = ref(null)
const revenueChartRef = ref(null)
const campaignChartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  primaryLight: 'rgba(32, 104, 255, 0.08)',
  orange: '#ff5600',
  orangeLight: 'rgba(255, 86, 0, 0.08)',
  green: '#009900',
  greenLight: 'rgba(0, 153, 0, 0.08)',
  purple: '#AA00FF',
  text: '#050505',
  muted: '#888',
}

const SECTIONS = [
  { key: 'executive', label: 'Executive Summary', icon: 'chart' },
  { key: 'decisions', label: 'Key Decisions', icon: 'lightbulb' },
  { key: 'actions', label: 'Action Items', icon: 'checklist' },
  { key: 'projections', label: 'Impact Projections', icon: 'trending' },
  { key: 'risks', label: 'Risks Identified', icon: 'warning' },
]

const PRIORITY_COLORS = {
  critical: { bg: 'bg-red-50 dark:bg-red-500/10', text: 'text-red-700 dark:text-red-400', border: 'border-red-200 dark:border-red-500/20' },
  high: { bg: 'bg-orange-50 dark:bg-orange-500/10', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-200 dark:border-orange-500/20' },
  medium: { bg: 'bg-blue-50 dark:bg-blue-500/10', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-500/20' },
  low: { bg: 'bg-gray-50 dark:bg-gray-500/10', text: 'text-gray-600 dark:text-gray-400', border: 'border-gray-200 dark:border-gray-500/20' },
}

const SEVERITY_STYLES = {
  high: { dot: 'bg-red-500', bg: 'border-l-red-500' },
  medium: { dot: 'bg-yellow-500', bg: 'border-l-yellow-500' },
  low: { dot: 'bg-green-500', bg: 'border-l-green-500' },
}

const summary = computed(() => reportData.value?.executive_summary || {})
const decisions = computed(() => reportData.value?.key_decisions || [])
const actionItems = computed(() => reportData.value?.action_items || [])
const projections = computed(() => reportData.value?.impact_projections || {})
const risks = computed(() => reportData.value?.risks || [])

const actionsByRole = computed(() => {
  const grouped = {}
  for (const item of actionItems.value) {
    const role = item.assigned_to || 'Unassigned'
    if (!grouped[role]) grouped[role] = []
    grouped[role].push(item)
  }
  return grouped
})

async function fetchReport() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`${API_BASE}/simulation/${props.simulationId}/gtm-summary`)
    if (!res.ok) throw new Error(`Failed to fetch report: ${res.status}`)
    const json = await res.json()
    reportData.value = json.data || json
  } catch (e) {
    error.value = e.message || 'Failed to load GTM summary report'
  } finally {
    loading.value = false
  }
}

function copyReportLink() {
  const url = `${window.location.origin}/report/${props.simulationId}?view=gtm`
  navigator.clipboard.writeText(url).then(() => {
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  })
}

function downloadAsHtml() {
  if (!reportData.value) return
  const html = generatePrintableHtml()
  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `gtm-report-${props.simulationId}.html`
  a.click()
  URL.revokeObjectURL(url)
}

function generatePrintableHtml() {
  const d = reportData.value
  const s = d.executive_summary
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GTM Simulation Report — ${props.simulationId}</title>
<style>
  @page { margin: 1in; }
  body { font-family: system-ui, -apple-system, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 40px; }
  h1 { font-size: 24px; color: #050505; border-bottom: 3px solid #2068FF; padding-bottom: 8px; }
  h2 { font-size: 18px; color: #2068FF; margin-top: 32px; }
  h3 { font-size: 15px; margin-top: 20px; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }
  th { text-align: left; padding: 8px; border-bottom: 2px solid #ddd; font-weight: 600; }
  td { padding: 8px; border-bottom: 1px solid #eee; }
  .kpi { display: inline-block; width: 23%; text-align: center; padding: 16px 8px; margin: 4px; border: 1px solid #e5e7eb; border-radius: 8px; }
  .kpi-value { font-size: 24px; font-weight: 700; color: #2068FF; }
  .kpi-label { font-size: 12px; color: #888; margin-top: 4px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .badge-critical { background: #fee2e2; color: #dc2626; }
  .badge-high { background: #ffedd5; color: #ea580c; }
  .badge-medium { background: #dbeafe; color: #2563eb; }
  .badge-low { background: #f3f4f6; color: #6b7280; }
  .risk-high { border-left: 4px solid #ef4444; padding-left: 12px; }
  .risk-medium { border-left: 4px solid #f59e0b; padding-left: 12px; }
  .risk-low { border-left: 4px solid #22c55e; padding-left: 12px; }
  .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #eee; font-size: 12px; color: #888; }
  @media print { .no-print { display: none; } }
</style>
</head>
<body>
<h1>GTM Simulation Summary Report</h1>
<p style="color:#888;font-size:14px">Simulation: ${props.simulationId} &bull; ${s.total_agents} agents &bull; ${s.simulation_hours}h simulation</p>

<h2>Executive Summary</h2>
<div>
  <div class="kpi"><div class="kpi-value">${(s.total_interactions || 0).toLocaleString()}</div><div class="kpi-label">Interactions</div></div>
  <div class="kpi"><div class="kpi-value">${s.top_open_rate}%</div><div class="kpi-label">Top Open Rate</div></div>
  <div class="kpi"><div class="kpi-value">${s.ai_resolution_rate}%</div><div class="kpi-label">AI Resolution</div></div>
  <div class="kpi"><div class="kpi-value">$${(s.estimated_savings / 1000).toFixed(0)}K</div><div class="kpi-label">Est. Savings</div></div>
</div>

<h2>Key Decisions</h2>
<table>
  <tr><th>Decision</th><th>Confidence</th><th>Impact</th></tr>
  ${d.key_decisions.map(k => `<tr><td><strong>${k.decision}</strong><br><small style="color:#888">${k.evidence}</small></td><td>${k.confidence}%</td><td><span class="badge badge-${k.impact}">${k.impact}</span></td></tr>`).join('')}
</table>

<h2>Action Items</h2>
<table>
  <tr><th>Action</th><th>Owner</th><th>Priority</th><th>Timeline</th></tr>
  ${d.action_items.map(a => `<tr><td>${a.title}</td><td>${a.assigned_to}</td><td><span class="badge badge-${a.priority}">${a.priority}</span></td><td>${a.timeline}</td></tr>`).join('')}
</table>

<h2>Impact Projections</h2>
<p>Estimated campaign effectiveness improvement: <strong>${d.impact_projections.estimated_improvement}</strong></p>
<table>
  <tr><th>Segment</th><th>Open Rate</th><th>Reply Rate</th><th>Meeting Rate</th></tr>
  ${d.impact_projections.campaign_effectiveness.map(c => `<tr><td>${c.segment}</td><td>${c.open_rate}%</td><td>${c.reply_rate}%</td><td>${c.meeting_rate}%</td></tr>`).join('')}
</table>

<h2>Risks Identified</h2>
${d.risks.map(r => `<div class="risk-${r.severity}" style="margin:12px 0"><strong>${r.title}</strong> <span class="badge badge-${r.severity === 'high' ? 'critical' : r.severity}">${r.severity}</span><br>${r.description}<br><small style="color:#009900"><strong>Mitigation:</strong> ${r.mitigation}</small></div>`).join('')}

<div class="footer">Generated by MiroFish GTM Simulation Engine &bull; Intercom</div>
</body>
</html>`
}

// --- D3 Charts ---

function clearChart(ref) {
  if (ref.value) d3.select(ref.value).selectAll('*').remove()
}

function renderPipelineChart() {
  clearChart(pipelineChartRef)
  const container = pipelineChartRef.value
  if (!container || !projections.value.pipeline_forecast?.length) return

  const data = projections.value.pipeline_forecast
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 48, right: 24, bottom: 36, left: 64 }
  const width = containerWidth - margin.left - margin.right
  const height = 220
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  svg.append('text')
    .attr('x', margin.left).attr('y', 22)
    .attr('font-size', '14px').attr('font-weight', '600').attr('fill', COLORS.text)
    .text('Pipeline Forecast')

  svg.append('text')
    .attr('x', margin.left).attr('y', 38)
    .attr('font-size', '11px').attr('fill', COLORS.muted)
    .text('Optimized vs. baseline monthly pipeline ($)')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleBand().domain(data.map(d => d.month)).range([0, width]).padding(0.3)
  const maxVal = d3.max(data, d => Math.max(d.optimized, d.baseline))
  const y = d3.scaleLinear().domain([0, maxVal * 1.15]).range([height, 0])

  // Grid
  const yTicks = y.ticks(5)
  g.selectAll('.grid').data(yTicks).join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)').attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label').data(yTicks).join('text')
    .attr('x', -8).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end').attr('font-size', '10px').attr('fill', '#aaa')
    .text(d => `$${(d / 1000).toFixed(0)}K`)

  g.selectAll('.x-label').data(data).join('text')
    .attr('x', d => x(d.month) + x.bandwidth() / 2)
    .attr('y', height + 18).attr('text-anchor', 'middle')
    .attr('font-size', '11px').attr('fill', '#888')
    .text(d => d.month)

  const barW = x.bandwidth() / 2 - 2

  // Baseline bars
  g.selectAll('.bar-baseline').data(data).join('rect')
    .attr('x', d => x(d.month)).attr('y', height).attr('width', barW).attr('height', 0)
    .attr('rx', 3).attr('fill', '#ddd').attr('opacity', 0.7)
    .transition().duration(500).delay((_, i) => i * 60)
    .attr('y', d => y(d.baseline)).attr('height', d => height - y(d.baseline))

  // Optimized bars
  g.selectAll('.bar-optimized').data(data).join('rect')
    .attr('x', d => x(d.month) + barW + 4).attr('y', height).attr('width', barW).attr('height', 0)
    .attr('rx', 3).attr('fill', COLORS.primary).attr('opacity', 0.85)
    .transition().duration(500).delay((_, i) => i * 60 + 30)
    .attr('y', d => y(d.optimized)).attr('height', d => height - y(d.optimized))

  // Value labels for optimized
  g.selectAll('.val-optimized').data(data).join('text')
    .attr('x', d => x(d.month) + barW + 4 + barW / 2)
    .attr('y', d => y(d.optimized) - 6)
    .attr('text-anchor', 'middle').attr('font-size', '10px')
    .attr('font-weight', '600').attr('fill', COLORS.primary)
    .style('opacity', 0)
    .text(d => `$${(d.optimized / 1000).toFixed(0)}K`)
    .transition().duration(300).delay((_, i) => 500 + i * 60)
    .style('opacity', 1)

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${containerWidth - margin.right - 190}, 14)`)
  legend.append('rect').attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', '#ddd')
  legend.append('text').attr('x', 14).attr('y', 9).attr('font-size', '11px').attr('fill', '#555').text('Baseline')
  legend.append('rect').attr('x', 80).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', COLORS.primary)
  legend.append('text').attr('x', 94).attr('y', 9).attr('font-size', '11px').attr('fill', '#555').text('Optimized')
}

function renderRevenueChart() {
  clearChart(revenueChartRef)
  const container = revenueChartRef.value
  if (!container || !projections.value.revenue_projection?.length) return

  const data = projections.value.revenue_projection
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 48, right: 24, bottom: 36, left: 64 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  svg.append('text')
    .attr('x', margin.left).attr('y', 22)
    .attr('font-size', '14px').attr('font-weight', '600').attr('fill', COLORS.text)
    .text('Revenue Projection')

  svg.append('text')
    .attr('x', margin.left).attr('y', 38)
    .attr('font-size', '11px').attr('fill', COLORS.muted)
    .text('Current trajectory vs. optimized campaign impact')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scalePoint().domain(data.map(d => d.quarter)).range([0, width]).padding(0.3)
  const allVals = data.flatMap(d => [d.current, d.projected])
  const y = d3.scaleLinear().domain([d3.min(allVals) * 0.9, d3.max(allVals) * 1.1]).range([height, 0])

  // Grid
  const yTicks = y.ticks(4)
  g.selectAll('.grid').data(yTicks).join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)').attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label').data(yTicks).join('text')
    .attr('x', -8).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end').attr('font-size', '10px').attr('fill', '#aaa')
    .text(d => `$${(d / 1000000).toFixed(1)}M`)

  g.selectAll('.x-label').data(data).join('text')
    .attr('x', d => x(d.quarter)).attr('y', height + 18)
    .attr('text-anchor', 'middle').attr('font-size', '11px').attr('fill', '#888')
    .text(d => d.quarter)

  // Area between lines
  const area = d3.area()
    .x(d => x(d.quarter))
    .y0(d => y(d.current))
    .y1(d => y(d.projected))
    .curve(d3.curveMonotoneX)

  g.append('path').datum(data).attr('d', area)
    .attr('fill', 'rgba(32, 104, 255, 0.08)')
    .style('opacity', 0)
    .transition().duration(600).style('opacity', 1)

  // Current line
  const currentLine = d3.line().x(d => x(d.quarter)).y(d => y(d.current)).curve(d3.curveMonotoneX)
  const cPath = g.append('path').datum(data).attr('d', currentLine)
    .attr('fill', 'none').attr('stroke', '#bbb').attr('stroke-width', 2).attr('stroke-dasharray', '6,4')

  // Projected line
  const projectedLine = d3.line().x(d => x(d.quarter)).y(d => y(d.projected)).curve(d3.curveMonotoneX)
  const pPath = g.append('path').datum(data).attr('d', projectedLine)
    .attr('fill', 'none').attr('stroke', COLORS.primary).attr('stroke-width', 2.5)

  // Animate lines
  for (const path of [cPath, pPath]) {
    const len = path.node().getTotalLength()
    path.attr('stroke-dasharray', `${len} ${len}`).attr('stroke-dashoffset', len)
      .transition().duration(700).ease(d3.easeCubicOut).attr('stroke-dashoffset', 0)
  }
  // Reset current line dash after animation
  cPath.transition().delay(700).attr('stroke-dasharray', '6,4')

  // Dots for projected
  g.selectAll('.dot-proj').data(data).join('circle')
    .attr('cx', d => x(d.quarter)).attr('cy', d => y(d.projected))
    .attr('r', 0).attr('fill', COLORS.primary).attr('stroke', '#fff').attr('stroke-width', 2)
    .transition().duration(300).delay((_, i) => 700 + i * 80).attr('r', 5)

  // Value labels for projected
  g.selectAll('.val-proj').data(data).join('text')
    .attr('x', d => x(d.quarter)).attr('y', d => y(d.projected) - 12)
    .attr('text-anchor', 'middle').attr('font-size', '10px')
    .attr('font-weight', '600').attr('fill', COLORS.primary)
    .style('opacity', 0)
    .text(d => `$${(d.projected / 1000000).toFixed(1)}M`)
    .transition().duration(300).delay((_, i) => 700 + i * 80).style('opacity', 1)

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${containerWidth - margin.right - 210}, 14)`)
  legend.append('line').attr('x1', 0).attr('x2', 20).attr('y1', 5).attr('y2', 5)
    .attr('stroke', '#bbb').attr('stroke-width', 2).attr('stroke-dasharray', '6,4')
  legend.append('text').attr('x', 26).attr('y', 9).attr('font-size', '11px').attr('fill', '#555').text('Current')
  legend.append('line').attr('x1', 90).attr('x2', 110).attr('y1', 5).attr('y2', 5)
    .attr('stroke', COLORS.primary).attr('stroke-width', 2.5)
  legend.append('text').attr('x', 116).attr('y', 9).attr('font-size', '11px').attr('fill', '#555').text('Optimized')
}

function renderCampaignChart() {
  clearChart(campaignChartRef)
  const container = campaignChartRef.value
  if (!container || !projections.value.campaign_effectiveness?.length) return

  const data = projections.value.campaign_effectiveness
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 48, right: 24, bottom: 40, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = 220
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  svg.append('text')
    .attr('x', margin.left).attr('y', 22)
    .attr('font-size', '14px').attr('font-weight', '600').attr('fill', COLORS.text)
    .text('Campaign Effectiveness by Segment')

  svg.append('text')
    .attr('x', margin.left).attr('y', 38)
    .attr('font-size', '11px').attr('fill', COLORS.muted)
    .text('Open rate, reply rate, and meeting booking rate per vertical')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x0 = d3.scaleBand().domain(data.map(d => d.segment)).range([0, width]).paddingInner(0.25).paddingOuter(0.1)
  const metrics = ['open_rate', 'reply_rate', 'meeting_rate']
  const x1 = d3.scaleBand().domain(metrics).range([0, x0.bandwidth()]).padding(0.08)
  const y = d3.scaleLinear().domain([0, 40]).range([height, 0])

  const metricColors = { open_rate: COLORS.primary, reply_rate: COLORS.orange, meeting_rate: COLORS.green }

  // Grid
  const yTicks = [0, 10, 20, 30, 40]
  g.selectAll('.grid').data(yTicks).join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)').attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label').data(yTicks).join('text')
    .attr('x', -8).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end').attr('font-size', '10px').attr('fill', '#aaa')
    .text(d => `${d}%`)

  g.selectAll('.x-label').data(data).join('text')
    .attr('x', d => x0(d.segment) + x0.bandwidth() / 2)
    .attr('y', height + 18).attr('text-anchor', 'middle')
    .attr('font-size', '11px').attr('fill', '#888')
    .text(d => d.segment)

  // Grouped bars
  const groups = g.selectAll('.group').data(data).join('g')
    .attr('transform', d => `translate(${x0(d.segment)},0)`)

  for (const metric of metrics) {
    groups.append('rect')
      .attr('x', x1(metric)).attr('y', height).attr('width', x1.bandwidth()).attr('height', 0)
      .attr('rx', 3).attr('fill', metricColors[metric]).attr('opacity', 0.85)
      .transition().duration(500).delay((_, i) => i * 80)
      .attr('y', d => y(d[metric])).attr('height', d => height - y(d[metric]))

    groups.append('text')
      .attr('x', x1(metric) + x1.bandwidth() / 2)
      .attr('y', d => y(d[metric]) - 5)
      .attr('text-anchor', 'middle').attr('font-size', '9px')
      .attr('font-weight', '600').attr('fill', metricColors[metric])
      .style('opacity', 0)
      .text(d => `${d[metric]}%`)
      .transition().duration(300).delay((_, i) => 500 + i * 80)
      .style('opacity', 1)
  }

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${containerWidth - margin.right - 280}, 14)`)
  const legendItems = [
    { label: 'Open Rate', color: COLORS.primary },
    { label: 'Reply Rate', color: COLORS.orange },
    { label: 'Meeting Rate', color: COLORS.green },
  ]
  legendItems.forEach((item, i) => {
    const xOff = i * 100
    legend.append('rect').attr('x', xOff).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', item.color).attr('opacity', 0.85)
    legend.append('text').attr('x', xOff + 14).attr('y', 9).attr('font-size', '11px').attr('fill', '#555').text(item.label)
  })
}

function renderAllCharts() {
  if (activeSection.value === 3) {
    nextTick(() => {
      renderPipelineChart()
      renderRevenueChart()
      renderCampaignChart()
    })
  }
}

watch(activeSection, () => { renderAllCharts() })

onMounted(async () => {
  await fetchReport()
  if (reportData.value) {
    nextTick(() => renderAllCharts())
  }

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(renderAllCharts, 200)
  })
  if (pipelineChartRef.value) resizeObserver.observe(pipelineChartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]" style="letter-spacing: -0.64px">
          GTM Simulation Report
        </h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1">
          Simulation {{ simulationId }} &bull; Structured analysis with actionable recommendations
        </p>
      </div>
      <div class="flex gap-2">
        <button
          @click="copyReportLink"
          class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text)] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          {{ copySuccess ? 'Copied!' : 'Share' }}
        </button>
        <button
          @click="downloadAsHtml"
          :disabled="!reportData"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export PDF
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg p-4 mb-6 text-sm text-red-700 dark:text-red-400">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
        <div class="animate-pulse space-y-3">
          <div class="h-4 bg-[var(--color-tint)] rounded w-1/3" />
          <div class="h-3 bg-[var(--color-tint)] rounded w-full" />
          <div class="h-3 bg-[var(--color-tint)] rounded w-4/5" />
        </div>
      </div>
    </div>

    <!-- Report Content -->
    <div v-else-if="reportData" class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Section Nav -->
      <nav class="space-y-1">
        <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3 px-3">Sections</h3>
        <button
          v-for="(section, i) in SECTIONS"
          :key="section.key"
          @click="activeSection = i"
          class="w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex items-center gap-2"
          :class="activeSection === i
            ? 'bg-[#2068FF] text-white'
            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)]'"
        >
          <span
            class="shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs"
            :class="activeSection === i
              ? 'bg-white/20 text-white'
              : 'bg-[rgba(32,104,255,0.08)] text-[#2068FF]'"
          >
            {{ i + 1 }}
          </span>
          <span class="truncate">{{ section.label }}</span>
        </button>
      </nav>

      <!-- Main Content -->
      <div class="md:col-span-3 space-y-6">

        <!-- Section 0: Executive Summary -->
        <div v-if="activeSection === 0" class="space-y-6">
          <!-- KPI Cards -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-[#2068FF]">{{ summary.total_interactions?.toLocaleString() }}</div>
              <div class="text-xs text-[var(--color-text-muted)] mt-1">Total Interactions</div>
            </div>
            <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-[#ff5600]">{{ summary.top_open_rate }}%</div>
              <div class="text-xs text-[var(--color-text-muted)] mt-1">Top Open Rate</div>
            </div>
            <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-[#009900]">{{ summary.ai_resolution_rate }}%</div>
              <div class="text-xs text-[var(--color-text-muted)] mt-1">AI Resolution Rate</div>
            </div>
            <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-[#AA00FF]">${{ (summary.estimated_savings / 1000).toFixed(0) }}K</div>
              <div class="text-xs text-[var(--color-text-muted)] mt-1">Est. Annual Savings</div>
            </div>
          </div>

          <!-- Summary Card -->
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
            <h2 class="text-lg font-semibold text-[var(--color-text)] mb-4">Executive Summary</h2>
            <div class="space-y-3 text-sm text-[var(--color-text-secondary)] leading-relaxed">
              <p>
                This report summarizes findings from a <strong class="text-[var(--color-text)]">{{ summary.simulation_hours }}-hour</strong> swarm intelligence simulation
                involving <strong class="text-[var(--color-text)]">{{ summary.total_agents }} AI agents</strong> representing synthetic buyer personas across SaaS, Healthcare,
                Fintech, and E-commerce verticals.
              </p>
              <p>
                The top-performing subject line — <em>"{{ summary.top_performing_subject }}"</em> — achieved a
                <strong class="text-[var(--color-text)]">{{ summary.top_open_rate }}% simulated open rate</strong>.
                The Fin AI agent's <strong class="text-[var(--color-text)]">{{ summary.ai_resolution_rate }}% automation rate</strong> was the single most persuasive data point,
                referenced in 67% of positive engagement signals.
              </p>
            </div>

            <!-- Confidence metrics -->
            <div class="mt-5 pt-4 border-t border-[var(--color-border)]">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div class="text-sm font-semibold text-[var(--color-text)]">{{ summary.conversation_threads }}</div>
                  <div class="text-xs text-[var(--color-text-muted)]">Conversation Threads</div>
                </div>
                <div>
                  <div class="text-sm font-semibold text-[var(--color-text)]">{{ summary.convergence_score }}</div>
                  <div class="text-xs text-[var(--color-text-muted)]">Convergence Score</div>
                </div>
                <div>
                  <div class="text-sm font-semibold text-[var(--color-text)]">{{ summary.confidence }}%</div>
                  <div class="text-xs text-[var(--color-text-muted)]">Statistical Confidence</div>
                </div>
                <div>
                  <div class="text-sm font-semibold text-[var(--color-text)]">{{ summary.total_agents }}</div>
                  <div class="text-xs text-[var(--color-text-muted)]">AI Agents</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 1: Key Decisions -->
        <div v-if="activeSection === 1" class="space-y-4">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
            <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Key Decisions Made</h2>
            <p class="text-sm text-[var(--color-text-muted)] mb-5">Critical findings from the simulation that should inform campaign strategy</p>

            <div class="space-y-4">
              <div
                v-for="decision in decisions"
                :key="decision.id"
                class="border border-[var(--color-border)] rounded-lg p-4 hover:bg-[var(--color-tint)] transition-colors"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span
                        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase"
                        :class="decision.impact === 'high'
                          ? 'bg-[rgba(255,86,0,0.1)] text-[#ff5600]'
                          : 'bg-[rgba(32,104,255,0.08)] text-[#2068FF]'"
                      >
                        {{ decision.impact }} impact
                      </span>
                    </div>
                    <p class="text-sm font-medium text-[var(--color-text)]">{{ decision.decision }}</p>
                    <p class="text-xs text-[var(--color-text-muted)] mt-1">{{ decision.evidence }}</p>
                  </div>
                  <div class="shrink-0 text-right">
                    <div class="text-lg font-bold text-[#2068FF]">{{ decision.confidence }}%</div>
                    <div class="text-[10px] text-[var(--color-text-muted)]">confidence</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 2: Action Items -->
        <div v-if="activeSection === 2" class="space-y-4">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
            <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Action Items</h2>
            <p class="text-sm text-[var(--color-text-muted)] mb-5">Prioritized actions assigned to GTM roles with timelines</p>

            <div v-for="(items, role) in actionsByRole" :key="role" class="mb-6 last:mb-0">
              <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-[#2068FF]" />
                {{ role }}
                <span class="text-[10px] font-normal lowercase">({{ items.length }} items)</span>
              </h3>

              <div class="space-y-2">
                <div
                  v-for="item in items"
                  :key="item.id"
                  class="border border-[var(--color-border)] rounded-lg p-3 hover:bg-[var(--color-tint)] transition-colors"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-0.5">
                        <span
                          class="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase"
                          :class="[PRIORITY_COLORS[item.priority]?.bg, PRIORITY_COLORS[item.priority]?.text]"
                        >
                          {{ item.priority }}
                        </span>
                        <span class="text-[10px] text-[var(--color-text-muted)]">{{ item.timeline }}</span>
                      </div>
                      <p class="text-sm font-medium text-[var(--color-text)]">{{ item.title }}</p>
                      <p class="text-xs text-[var(--color-text-muted)] mt-0.5">{{ item.description }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 3: Impact Projections -->
        <div v-if="activeSection === 3" class="space-y-4">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-6">
            <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Impact Projections</h2>
            <p class="text-sm text-[var(--color-text-muted)] mb-2">
              Estimated <strong class="text-[var(--color-text)]">{{ projections.estimated_improvement }}</strong> improvement in campaign effectiveness
            </p>
          </div>

          <!-- Pipeline chart -->
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-6">
            <div ref="pipelineChartRef" class="w-full" />
          </div>

          <!-- Revenue chart -->
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-6">
            <div ref="revenueChartRef" class="w-full" />
          </div>

          <!-- Campaign effectiveness chart -->
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-6">
            <div ref="campaignChartRef" class="w-full" />
          </div>
        </div>

        <!-- Section 4: Risks Identified -->
        <div v-if="activeSection === 4" class="space-y-4">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
            <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Risks Identified</h2>
            <p class="text-sm text-[var(--color-text-muted)] mb-5">Potential risks flagged by the simulation with recommended mitigations</p>

            <div class="space-y-4">
              <div
                v-for="risk in risks"
                :key="risk.id"
                class="border-l-4 rounded-lg p-4 bg-[var(--color-surface)] border border-[var(--color-border)]"
                :class="SEVERITY_STYLES[risk.severity]?.bg"
              >
                <div class="flex items-center gap-2 mb-2">
                  <span class="w-2 h-2 rounded-full" :class="SEVERITY_STYLES[risk.severity]?.dot" />
                  <h3 class="text-sm font-semibold text-[var(--color-text)]">{{ risk.title }}</h3>
                  <span
                    class="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded"
                    :class="risk.severity === 'high'
                      ? 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400'
                      : risk.severity === 'medium'
                        ? 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400'
                        : 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400'"
                  >
                    {{ risk.severity }}
                  </span>
                </div>
                <p class="text-sm text-[var(--color-text-secondary)] mb-2">{{ risk.description }}</p>
                <div class="flex items-start gap-1.5 text-xs">
                  <span class="font-semibold text-[#009900] shrink-0">Mitigation:</span>
                  <span class="text-[var(--color-text-muted)]">{{ risk.mitigation }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Section navigation footer -->
        <div class="flex items-center justify-between pt-2">
          <button
            :disabled="activeSection === 0"
            @click="activeSection--"
            class="text-sm text-[var(--color-primary)] hover:underline disabled:text-[var(--color-text-muted)] disabled:no-underline transition-colors"
          >
            &larr; {{ activeSection > 0 ? SECTIONS[activeSection - 1].label : 'Previous' }}
          </button>
          <span class="text-xs text-[var(--color-text-muted)]">{{ activeSection + 1 }} of {{ SECTIONS.length }}</span>
          <button
            :disabled="activeSection === SECTIONS.length - 1"
            @click="activeSection++"
            class="text-sm text-[var(--color-primary)] hover:underline disabled:text-[var(--color-text-muted)] disabled:no-underline transition-colors"
          >
            {{ activeSection < SECTIONS.length - 1 ? SECTIONS[activeSection + 1].label : 'Next' }} &rarr;
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
