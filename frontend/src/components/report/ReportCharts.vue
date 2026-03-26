<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { select } from 'd3-selection'
import { scaleLinear, scaleBand, scaleOrdinal } from 'd3-scale'
import { easeCubicOut } from 'd3-ease'
import { pie as d3Pie, arc as d3Arc } from 'd3-shape'
import { interpolate as d3Interpolate } from 'd3-interpolate'
import { hierarchy, treemap } from 'd3-hierarchy'
import 'd3-transition'
import { getChartColors, useChartColors } from '../../lib/chartUtils'
import { useMobileChart } from '../../composables/useMobileChart'
import { useD3PerfMonitor } from '@/composables/useD3PerfMonitor'

const { isMobile } = useMobileChart()
const { measure, countDomNodes } = useD3PerfMonitor()

const props = defineProps({
  chapterIndex: { type: Number, required: true },
  offlineCachedAt: { type: Number, default: null },
})

const offlineDateLabel = computed(() => {
  if (!props.offlineCachedAt) return ''
  return new Date(props.offlineCachedAt).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  })
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null
const { isDark } = useChartColors()

const CHART_MAP = {
  1: renderPersonaEngagement,
  2: renderSubjectLinePerformance,
  3: renderBehavioralClusters,
  4: renderTopicTreemap,
  5: renderCampaignSpendAllocation,
}

function getColors() {
  const s = getComputedStyle(document.documentElement)
  const dark = document.documentElement.classList.contains('dark')
  return {
    primary: s.getPropertyValue('--color-primary').trim() || '#2068FF',
    orange: s.getPropertyValue('--color-fin-orange').trim() || '#ff5600',
    purple: s.getPropertyValue('--color-accent').trim() || '#AA00FF',
    green: s.getPropertyValue('--color-success').trim() || '#009900',
    text: s.getPropertyValue('--color-text').trim() || '#050505',
    textSecondary: s.getPropertyValue('--color-text-secondary').trim() || '#555555',
    textMuted: s.getPropertyValue('--color-text-muted').trim() || '#888888',
    grid: dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
    subtle: dark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
    connector: dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)',
    surface: s.getPropertyValue('--color-surface').trim() || '#ffffff',
  }
}

function hasChart(index) {
  return index in CHART_MAP
}

function clearChart() {
  if (!chartRef.value) return
  select(chartRef.value).selectAll('*').remove()
}

function renderActiveChart() {
  clearChart()
  const renderFn = CHART_MAP[props.chapterIndex]
  if (renderFn && chartRef.value) {
    nextTick(() => {
      measure('ReportCharts', renderFn)
      countDomNodes('ReportCharts', chartRef.value)
    })
  }
}

// --- Chart 1: Horizontal Bar — Persona Engagement Rates ---

function renderPersonaEngagement() {
  const container = chartRef.value
  if (!container) return
  const COLORS = getColors()

  const c = getChartColors()
  const data = [
    { label: 'VP Support', value: 38.4 },
    { label: 'Head of Ops', value: 35.6 },
    { label: 'CX Director', value: 31.2 },
    { label: 'CFO', value: 28.9 },
    { label: 'IT Leader', value: 22.8 },
  ]

  const containerWidth = container.clientWidth
  const mobile = isMobile.value
  const margin = mobile
    ? { top: 48, right: 40, bottom: 20, left: 72 }
    : { top: 56, right: 60, bottom: 24, left: 100 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = mobile ? 28 : 36
  const barGap = mobile ? 8 : 12
  const height = data.length * (barHeight + barGap) - barGap
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', mobile ? 18 : 22)
    .attr('font-size', mobile ? '12px' : '14px')
    .attr('font-weight', '600')
    .attr('fill', c.text)
    .text('Persona Engagement Rates')
    .style('opacity', 0)
    .transition()
    .duration(350)
    .style('opacity', 1)

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', mobile ? 34 : 40)
    .attr('font-size', mobile ? '10px' : '11px')
    .attr('fill', c.textMuted)
    .text('Average email open rate by target persona')
    .style('opacity', 0)
    .transition()
    .duration(350)
    .delay(60)
    .style('opacity', 1)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleLinear()
    .domain([0, 50])
    .range([0, width])

  const y = scaleBand()
    .domain(data.map(d => d.label))
    .range([0, height])
    .padding(barGap / (barHeight + barGap))

  const gridTicks = [0, 10, 20, 30, 40, 50]
  g.selectAll('.grid-line')
    .data(gridTicks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', c.gridLine)
    .attr('stroke-dasharray', '2,3')
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 80 + i * 30)
    .style('opacity', 1)

  g.selectAll('.x-label')
    .data(gridTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', c.textMuted)
    .text(d => `${d}%`)
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 100 + i * 25)
    .style('opacity', 1)

  g.selectAll('.bar-label')
    .data(data)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', mobile ? '10px' : '12px')
    .attr('fill', c.textSecondary)
    .text(d => mobile && d.label.length > 10 ? d.label.slice(0, 10) + '…' : d.label)
    .style('opacity', 0)
    .transition()
    .duration(300)
    .delay((_, i) => 120 + i * 40)
    .style('opacity', 1)

  g.selectAll('.bar-bg')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.label))
    .attr('width', width)
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', c.barBg)
    .style('opacity', 0)
    .transition()
    .duration(300)
    .delay((_, i) => 120 + i * 40)
    .style('opacity', 1)

  const barColors = [c.primary, c.primary, c.orange, c.purple, c.textMuted]

  g.selectAll('.bar')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.label))
    .attr('width', 0)
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', (d, i) => barColors[i])
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => 200 + i * 80)
    .ease(easeCubicOut)
    .attr('width', d => x(d.value))

  g.selectAll('.bar-value')
    .data(data)
    .join('text')
    .attr('x', d => x(d.value) + 6)
    .attr('y', d => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('font-size', mobile ? '10px' : '12px')
    .attr('font-weight', '600')
    .attr('fill', c.text)
    .style('opacity', 0)
    .text(d => `${d.value}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 800 + i * 80)
    .style('opacity', 1)
}

// --- Chart 2: Grouped Bar — Subject Line Performance ---

function renderSubjectLinePerformance() {
  const container = chartRef.value
  if (!container) return
  const COLORS = getColors()

  const c = getChartColors()
  const data = [
    { label: '"Your Zendesk bill is 3x..."', open: 34.7, spam: 8.2 },
    { label: '"How [Company] cut costs 40%..."', open: 31.2, spam: 3.1 },
    { label: '"The AI agent your team wants"', open: 28.9, spam: 2.4 },
    { label: '"Replace Zendesk in 30 days"', open: 24.3, spam: 11.7 },
  ]

  const containerWidth = container.clientWidth
  const mobile = isMobile.value
  const margin = mobile
    ? { top: 48, right: 16, bottom: 72, left: 36 }
    : { top: 56, right: 24, bottom: 80, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = mobile ? 200 : 260
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', mobile ? 18 : 22)
    .attr('font-size', mobile ? '12px' : '14px')
    .attr('font-weight', '600')
    .attr('fill', c.text)
    .text('Subject Line Performance')
    .style('opacity', 0)
    .transition()
    .duration(350)
    .style('opacity', 1)

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', mobile ? 34 : 40)
    .attr('font-size', mobile ? '10px' : '11px')
    .attr('fill', c.textMuted)
    .text('Open rate vs. spam flag rate by subject variant')
    .style('opacity', 0)
    .transition()
    .duration(350)
    .delay(60)
    .style('opacity', 1)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x0 = scaleBand()
    .domain(data.map(d => d.label))
    .range([0, width])
    .paddingInner(0.3)
    .paddingOuter(0.15)

  const x1 = scaleBand()
    .domain(['open', 'spam'])
    .range([0, x0.bandwidth()])
    .padding(0.1)

  const y = scaleLinear()
    .domain([0, 40])
    .range([height, 0])

  const yTicks = [0, 10, 20, 30, 40]
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', c.gridLine)
    .attr('stroke-dasharray', '2,3')
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 80 + i * 30)
    .style('opacity', 1)

  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', c.textMuted)
    .text(d => `${d}%`)
    .style('opacity', 0)
    .transition()
    .duration(250)
    .delay((_, i) => 100 + i * 25)
    .style('opacity', 1)

  const groups = g.selectAll('.group')
    .data(data)
    .join('g')
    .attr('transform', d => `translate(${x0(d.label)},0)`)

  groups.append('rect')
    .attr('x', x1('open'))
    .attr('y', height)
    .attr('width', x1.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', c.primary)
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => 200 + i * 100)
    .ease(easeCubicOut)
    .attr('y', d => y(d.open))
    .attr('height', d => height - y(d.open))

  groups.append('rect')
    .attr('x', x1('spam'))
    .attr('y', height)
    .attr('width', x1.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', c.orange)
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => 250 + i * 100)
    .ease(easeCubicOut)
    .attr('y', d => y(d.spam))
    .attr('height', d => height - y(d.spam))

  groups.append('text')
    .attr('x', x1('open') + x1.bandwidth() / 2)
    .attr('y', d => y(d.open) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', c.primary)
    .style('opacity', 0)
    .text(d => `${d.open}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 800 + i * 100)
    .style('opacity', 1)

  groups.append('text')
    .attr('x', x1('spam') + x1.bandwidth() / 2)
    .attr('y', d => y(d.spam) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', c.orange)
    .style('opacity', 0)
    .text(d => `${d.spam}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 850 + i * 100)
    .style('opacity', 1)

  const labelY = height + 14
  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', d => x0(d.label) + x0.bandwidth() / 2)
    .attr('y', labelY)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', c.textMuted)
    .style('opacity', 0)
    .each(function (d) {
      const el = select(this)
      const maxWidth = x0.bandwidth() + 10
      const words = d.label.replace(/"/g, '').split(' ')
      let line = ''
      let lineNum = 0

      for (const word of words) {
        const testLine = line ? `${line} ${word}` : word
        if (testLine.length > Math.floor(maxWidth / 5.5) && line) {
          el.append('tspan')
            .attr('x', x0(d.label) + x0.bandwidth() / 2)
            .attr('dy', lineNum === 0 ? 0 : '1.1em')
            .text(line)
          line = word
          lineNum++
        } else {
          line = testLine
        }
      }
      if (line) {
        el.append('tspan')
          .attr('x', x0(d.label) + x0.bandwidth() / 2)
          .attr('dy', lineNum === 0 ? 0 : '1.1em')
          .text(line)
      }
    })
    .transition()
    .duration(300)
    .delay((_, i) => 200 + i * 60)
    .style('opacity', 1)

  const legendFontSize = mobile ? '10px' : '11px'
  const legendX = mobile ? margin.left : containerWidth - margin.right - 180
  const legend = svg.append('g')
    .attr('transform', `translate(${legendX}, ${mobile ? totalHeight - 10 : 14})`)
    .style('opacity', 0)

  legend.append('rect')
    .attr('x', 0).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', c.primary)
    .attr('opacity', 0.85)

  legend.append('text')
    .attr('x', 16).attr('y', 9)
    .attr('font-size', legendFontSize)
    .attr('fill', c.textSecondary)
    .text('Open Rate')

  legend.append('rect')
    .attr('x', 90).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', c.orange)
    .attr('opacity', 0.85)

  legend.append('text')
    .attr('x', 106).attr('y', 9)
    .attr('font-size', legendFontSize)
    .attr('fill', c.textSecondary)
    .text('Spam Flag')

  legend.transition()
    .duration(350)
    .delay(100)
    .style('opacity', 1)
}

// --- Chart 3: Donut — Behavioral Cluster Distribution ---

function renderBehavioralClusters() {
  const container = chartRef.value
  if (!container) return
  const COLORS = getColors()

  const c = getChartColors()
  const data = [
    { label: 'Active Evaluators', value: 31 },
    { label: 'Passive Observers', value: 24 },
    { label: 'Quick Converters', value: 19 },
    { label: 'Skeptical Evaluators', value: 18 },
    { label: 'Budget Blockers', value: 8 },
  ]

  const segmentColors = [c.primary, c.orange, c.green, c.purple, c.textMuted]

  const containerWidth = container.clientWidth
  const mobile = isMobile.value
  const size = Math.min(containerWidth, mobile ? 260 : 400)
  const radius = size / 2 - (mobile ? 24 : 40)
  const innerRadius = radius * 0.55
  const legendHeight = mobile ? data.length * 22 + 16 : 0
  const totalHeight = size + 60 + legendHeight

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', containerWidth / 2)
    .attr('y', mobile ? 18 : 22)
    .attr('text-anchor', 'middle')
    .attr('font-size', mobile ? '12px' : '14px')
    .attr('font-weight', '600')
    .attr('fill', c.text)
    .text('Behavioral Cluster Distribution')
    .style('opacity', 0)
    .transition()
    .duration(350)
    .style('opacity', 1)

  svg.append('text')
    .attr('x', containerWidth / 2)
    .attr('y', mobile ? 34 : 40)
    .attr('text-anchor', 'middle')
    .attr('font-size', mobile ? '10px' : '11px')
    .attr('fill', c.textMuted)
    .text(mobile ? 'Prospect segmentation by engagement' : 'Prospect segmentation by observed engagement pattern')
    .style('opacity', 0)
    .transition()
    .duration(350)
    .delay(60)
    .style('opacity', 1)

  const g = svg.append('g')
    .attr('transform', `translate(${containerWidth / 2},${size / 2 + 50})`)

  const pie = d3Pie()
    .value(d => d.value)
    .sort(null)
    .padAngle(0.02)

  const arc = d3Arc()
    .innerRadius(innerRadius)
    .outerRadius(radius)
    .cornerRadius(4)

  const labelArc = d3Arc()
    .innerRadius(radius + 16)
    .outerRadius(radius + 16)

  const arcs = pie(data)

  const paths = g.selectAll('.arc')
    .data(arcs)
    .join('path')
    .attr('fill', (d, i) => segmentColors[i])
    .attr('opacity', 0.85)
    .attr('stroke', c.surface)
    .attr('stroke-width', 2)

  paths.transition()
    .duration(600)
    .delay((d, i) => 200 + i * 80)
    .ease(easeCubicOut)
    .attrTween('d', function (d) {
      const interp = d3Interpolate({ startAngle: d.startAngle, endAngle: d.startAngle }, d)
      return t => arc(interp(t))
    })

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .attr('font-size', '24px')
    .attr('font-weight', '700')
    .attr('fill', c.text)
    .style('opacity', 0)
    .text('100%')
    .transition()
    .duration(400)
    .delay(800)
    .style('opacity', 1)

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .attr('font-size', '11px')
    .attr('fill', c.textMuted)
    .style('opacity', 0)
    .text('of prospects')
    .transition()
    .duration(400)
    .delay(850)
    .style('opacity', 1)

  if (mobile) {
    const legendG = svg.append('g')
      .attr('transform', `translate(24,${size + 50})`)

    data.forEach((d, i) => {
      const row = legendG.append('g')
        .attr('transform', `translate(0,${i * 22})`)
        .style('opacity', 0)

      row.append('rect')
        .attr('width', 10).attr('height', 10)
        .attr('rx', 2)
        .attr('fill', segmentColors[i])
        .attr('opacity', 0.85)

      row.append('text')
        .attr('x', 16).attr('y', 9)
        .attr('font-size', '11px')
        .attr('fill', c.textSecondary)
        .text(d.label)

      row.append('text')
        .attr('x', containerWidth - 48).attr('y', 9)
        .attr('text-anchor', 'end')
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .attr('fill', segmentColors[i])
        .text(`${d.value}%`)

      row.transition()
        .duration(300)
        .delay(600 + i * 60)
        .style('opacity', 1)
    })
  } else {
    const labelGroups = g.selectAll('.label-group')
      .data(arcs)
      .join('g')
      .style('opacity', 0)

    labelGroups.each(function (d, i) {
      const group = select(this)
      const pos = labelArc.centroid(d)
      const midAngle = (d.startAngle + d.endAngle) / 2
      const isRight = midAngle < Math.PI
      const xOffset = isRight ? 12 : -12

      const arcMid = arc.centroid(d)
      group.append('line')
        .attr('x1', arcMid[0] * 1.15)
        .attr('y1', arcMid[1] * 1.15)
        .attr('x2', pos[0] + xOffset)
        .attr('y2', pos[1])
        .attr('stroke', c.connectorLine)
        .attr('stroke-width', 1)

      group.append('text')
        .attr('x', pos[0] + xOffset * 2)
        .attr('y', pos[1])
        .attr('dy', '-0.3em')
        .attr('text-anchor', isRight ? 'start' : 'end')
        .attr('font-size', '11px')
        .attr('fill', c.textSecondary)
        .text(data[i].label)

      group.append('text')
        .attr('x', pos[0] + xOffset * 2)
        .attr('y', pos[1])
        .attr('dy', '0.9em')
        .attr('text-anchor', isRight ? 'start' : 'end')
        .attr('font-size', '12px')
        .attr('font-weight', '600')
        .attr('fill', segmentColors[i])
        .text(`${data[i].value}%`)
    })

    labelGroups.transition()
      .duration(300)
      .delay((d, i) => 800 + i * 80)
      .style('opacity', 1)
  }
}

// --- Chart 4: Treemap — Topic Distribution ---

function renderTopicTreemap() {
  const container = chartRef.value
  if (!container) return
  const COLORS = getColors()

  const treeData = {
    name: 'Topics',
    children: [
      {
        name: 'Product',
        children: [
          { name: 'AI Agent Capabilities', value: 28 },
          { name: 'Pricing & Packaging', value: 19 },
          { name: 'Platform Integration', value: 14 },
          { name: 'Self-Serve Onboarding', value: 8 },
        ],
      },
      {
        name: 'Market',
        children: [
          { name: 'Competitive Displacement', value: 22 },
          { name: 'Enterprise Expansion', value: 16 },
          { name: 'SMB Acquisition', value: 11 },
        ],
      },
      {
        name: 'Customer',
        children: [
          { name: 'Support Automation ROI', value: 25 },
          { name: 'Churn Risk Signals', value: 13 },
          { name: 'NPS & Satisfaction', value: 9 },
        ],
      },
      {
        name: 'Operations',
        children: [
          { name: 'Sales Cycle Length', value: 17 },
          { name: 'Pipeline Velocity', value: 12 },
          { name: 'Rep Enablement', value: 6 },
        ],
      },
    ],
  }

  const treemapColors = [
    COLORS.primary, COLORS.orange, COLORS.purple, COLORS.green,
    '#1a5ae0', '#e04d00', '#8800cc', '#007700',
  ]

  const containerWidth = container.clientWidth
  const margin = { top: 52, right: 4, bottom: 4, left: 4 }
  const width = containerWidth - margin.left - margin.right
  const height = 360
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left + 8)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Topic Distribution')

  svg.append('text')
    .attr('x', margin.left + 8)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Relative weight of discussion topics across simulation')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const root = hierarchy(treeData)
    .sum(d => d.value || 0)
    .sort((a, b) => b.value - a.value)

  treemap()
    .size([width, height])
    .paddingOuter(3)
    .paddingInner(2)
    .paddingTop(22)
    .round(true)(root)

  const categoryColor = scaleOrdinal()
    .domain(root.children.map(d => d.data.name))
    .range(treemapColors)

  // Category group backgrounds
  const groups = g.selectAll('.group')
    .data(root.children)
    .join('g')

  groups.append('rect')
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('height', d => d.y1 - d.y0)
    .attr('rx', 4)
    .attr('fill', d => categoryColor(d.data.name))
    .attr('opacity', 0.08)
    .style('opacity', 0)
    .transition()
    .duration(400)
    .style('opacity', 1)

  groups.append('text')
    .attr('x', d => d.x0 + 6)
    .attr('y', d => d.y0 + 14)
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', d => categoryColor(d.data.name))
    .attr('opacity', 0.7)
    .text(d => (d.x1 - d.x0 > 30) ? d.data.name.toUpperCase() : '')

  // Leaf cells
  const totalValue = root.value
  const cells = g.selectAll('.cell')
    .data(root.leaves())
    .join('g')
    .attr('transform', d => `translate(${d.x0},${d.y0})`)

  cells.append('rect')
    .attr('width', d => Math.max(0, d.x1 - d.x0))
    .attr('height', d => Math.max(0, d.y1 - d.y0))
    .attr('rx', 3)
    .attr('fill', d => categoryColor(d.parent.data.name))
    .attr('opacity', 0)
    .transition()
    .duration(500)
    .delay((d, i) => i * 30)
    .ease(easeCubicOut)
    .attr('opacity', 0.75)

  cells.append('text')
    .attr('x', 5)
    .attr('y', 15)
    .attr('font-size', '11px')
    .attr('font-weight', '500')
    .attr('fill', '#fff')
    .style('opacity', 0)
    .text(d => {
      const w = d.x1 - d.x0
      if (w < 40) return ''
      const max = Math.floor((w - 10) / 6)
      const name = d.data.name
      return name.length > max ? name.slice(0, max - 1) + '\u2026' : name
    })
    .transition()
    .duration(300)
    .delay((d, i) => 300 + i * 30)
    .style('opacity', 1)

  cells.append('text')
    .attr('x', 5)
    .attr('y', 29)
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', 'rgba(255,255,255,0.8)')
    .style('opacity', 0)
    .text(d => {
      const w = d.x1 - d.x0
      const h = d.y1 - d.y0
      if (w < 36 || h < 34) return ''
      return `${((d.value / totalValue) * 100).toFixed(1)}%`
    })
    .transition()
    .duration(300)
    .delay((d, i) => 400 + i * 30)
    .style('opacity', 1)

  cells.append('title')
    .text(d => {
      const pct = ((d.value / totalValue) * 100).toFixed(1)
      return `${d.data.name}\n${d.parent.data.name} \u2022 ${pct}%`
    })
}

// --- Chart 5: Treemap — Campaign Spend Allocation ---

function renderCampaignSpendAllocation() {
  const container = chartRef.value
  if (!container) return
  const COLORS = getColors()

  const campaigns = [
    { name: 'Zendesk Displacement Email', channel: 'Email', spend: 45000 },
    { name: 'LinkedIn Sponsored Content', channel: 'Paid Social', spend: 38000 },
    { name: 'AI Agent Launch Email', channel: 'Email', spend: 32000 },
    { name: 'Google Search — Competitor', channel: 'Search', spend: 29000 },
    { name: 'Enterprise Webinar Series', channel: 'Events', spend: 25000 },
    { name: 'LinkedIn InMail', channel: 'Paid Social', spend: 22000 },
    { name: 'Content SEO Program', channel: 'Content', spend: 18000 },
    { name: 'Google Display Retargeting', channel: 'Search', spend: 15000 },
    { name: 'SDR Direct Outreach', channel: 'Outbound', spend: 12000 },
  ]

  const channelColors = {
    'Email': COLORS.primary,
    'Paid Social': COLORS.orange,
    'Search': COLORS.purple,
    'Events': COLORS.green,
    'Content': '#1a5ae0',
    'Outbound': '#888',
  }

  const totalSpend = campaigns.reduce((sum, c) => sum + c.spend, 0)

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 16, bottom: 56, left: 16 }
  const width = containerWidth - margin.left - margin.right
  const height = 300
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Campaign Spend Allocation')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(`Budget distribution across GTM campaigns ($${(totalSpend / 1000).toFixed(0)}K total)`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const root = hierarchy({
    name: 'root',
    children: campaigns.map(c => ({ ...c, value: c.spend })),
  }).sum(d => d.value)

  treemap()
    .size([width, height])
    .padding(3)
    .round(true)(root)

  const leaves = root.leaves()

  const cells = g.selectAll('.cell')
    .data(leaves)
    .join('g')
    .attr('transform', d => `translate(${d.x0},${d.y0})`)

  cells.append('rect')
    .attr('width', d => d.x1 - d.x0)
    .attr('height', d => d.y1 - d.y0)
    .attr('rx', 4)
    .attr('fill', d => channelColors[d.data.channel])
    .attr('opacity', 0)
    .transition()
    .duration(600)
    .delay((d, i) => i * 60)
    .ease(easeCubicOut)
    .attr('opacity', 0.85)

  cells.each(function (d, i) {
    const w = d.x1 - d.x0
    const h = d.y1 - d.y0
    const cell = select(this)
    const baseDelay = 600 + i * 60

    if (w > 70 && h > 44) {
      const maxChars = Math.floor((w - 16) / 6.5)
      cell.append('text')
        .attr('x', 8)
        .attr('y', 20)
        .attr('font-size', w > 130 ? '11px' : '9px')
        .attr('font-weight', '600')
        .attr('fill', '#fff')
        .style('opacity', 0)
        .text(d.data.name.length > maxChars
          ? d.data.name.slice(0, maxChars) + '…'
          : d.data.name)
        .transition().duration(300).delay(baseDelay)
        .style('opacity', 1)

      cell.append('text')
        .attr('x', 8)
        .attr('y', 36)
        .attr('font-size', '10px')
        .attr('fill', 'rgba(255,255,255,0.75)')
        .style('opacity', 0)
        .text(`$${(d.data.spend / 1000).toFixed(0)}K`)
        .transition().duration(300).delay(baseDelay + 50)
        .style('opacity', 1)
    } else if (w > 36 && h > 22) {
      cell.append('text')
        .attr('x', 5)
        .attr('y', 15)
        .attr('font-size', '9px')
        .attr('font-weight', '600')
        .attr('fill', '#fff')
        .style('opacity', 0)
        .text(`$${(d.data.spend / 1000).toFixed(0)}K`)
        .transition().duration(300).delay(baseDelay)
        .style('opacity', 1)
    }
  })

  // Legend
  const channels = Object.keys(channelColors)
  const legendG = g.append('g')
    .attr('transform', `translate(0, ${height + 16})`)

  let lx = 0
  channels.forEach((ch) => {
    legendG.append('rect')
      .attr('x', lx)
      .attr('y', 0)
      .attr('width', 10)
      .attr('height', 10)
      .attr('rx', 2)
      .attr('fill', channelColors[ch])
      .attr('opacity', 0.85)

    const label = legendG.append('text')
      .attr('x', lx + 14)
      .attr('y', 9)
      .attr('font-size', '10px')
      .attr('fill', '#888')
      .text(ch)

    lx += 14 + label.node().getComputedTextLength() + 16
  })
}

// --- Lifecycle ---

watch(() => props.chapterIndex, () => {
  if (hasChart(props.chapterIndex)) {
    nextTick(() => renderActiveChart())
  }
})

watch([isDark, isMobile], () => {
  if (hasChart(props.chapterIndex)) {
    nextTick(() => renderActiveChart())
  }
})

onMounted(() => {
  if (hasChart(props.chapterIndex)) {
    renderActiveChart()
  }

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (hasChart(props.chapterIndex)) {
        renderActiveChart()
      }
    }, 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div
    v-if="hasChart(chapterIndex)"
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-6 relative"
  >
    <div ref="chartRef" class="w-full" />
    <div
      v-if="offlineCachedAt"
      class="absolute bottom-3 right-3 flex items-center gap-1.5 bg-amber-50 border border-amber-200 rounded px-2.5 py-1 text-[11px] text-amber-600 font-medium"
    >
      <svg class="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      Offline — data from {{ offlineDateLabel }}
    </div>
  </div>
</template>
