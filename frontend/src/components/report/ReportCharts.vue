<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { select } from 'd3-selection'
import { scaleLinear, scaleBand } from 'd3-scale'
import { easeCubicOut } from 'd3-ease'
import { pie as d3Pie, arc as d3Arc } from 'd3-shape'
import { interpolate as d3Interpolate } from 'd3-interpolate'
import 'd3-transition'

const props = defineProps({
  chapterIndex: { type: Number, required: true },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const CHART_MAP = {
  1: renderPersonaEngagement,
  2: renderSubjectLinePerformance,
  3: renderBehavioralClusters,
}

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
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
    nextTick(() => renderFn())
  }
}

// --- Chart 1: Horizontal Bar — Persona Engagement Rates ---

function renderPersonaEngagement() {
  const container = chartRef.value
  if (!container) return

  const data = [
    { label: 'VP Support', value: 38.4 },
    { label: 'Head of Ops', value: 35.6 },
    { label: 'CX Director', value: 31.2 },
    { label: 'CFO', value: 28.9 },
    { label: 'IT Leader', value: 22.8 },
  ]

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 60, bottom: 24, left: 100 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 36
  const barGap = 12
  const height = data.length * (barHeight + barGap) - barGap
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
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
    .text('Persona Engagement Rates')

  // Subtitle
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Average email open rate by target persona')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleLinear()
    .domain([0, 50])
    .range([0, width])

  const y = scaleBand()
    .domain(data.map(d => d.label))
    .range([0, height])
    .padding(barGap / (barHeight + barGap))

  // Grid lines
  const gridTicks = [0, 10, 20, 30, 40, 50]
  g.selectAll('.grid-line')
    .data(gridTicks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // X-axis labels
  g.selectAll('.x-label')
    .data(gridTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => `${d}%`)

  // Labels
  g.selectAll('.bar-label')
    .data(data)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '12px')
    .attr('fill', '#555')
    .text(d => d.label)

  // Bar background
  g.selectAll('.bar-bg')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.label))
    .attr('width', width)
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', 'rgba(0,0,0,0.03)')

  // Bars with animation
  const barColors = [COLORS.primary, COLORS.primary, COLORS.orange, COLORS.purple, '#888']

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
    .delay((d, i) => i * 80)
    .ease(easeCubicOut)
    .attr('width', d => x(d.value))

  // Value labels
  g.selectAll('.bar-value')
    .data(data)
    .join('text')
    .attr('x', d => x(d.value) + 8)
    .attr('y', d => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .style('opacity', 0)
    .text(d => `${d.value}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 80)
    .style('opacity', 1)
}

// --- Chart 2: Grouped Bar — Subject Line Performance ---

function renderSubjectLinePerformance() {
  const container = chartRef.value
  if (!container) return

  const data = [
    { label: '"Your Zendesk bill is 3x..."', open: 34.7, spam: 8.2 },
    { label: '"How [Company] cut costs 40%..."', open: 31.2, spam: 3.1 },
    { label: '"The AI agent your team wants"', open: 28.9, spam: 2.4 },
    { label: '"Replace Zendesk in 30 days"', open: 24.3, spam: 11.7 },
  ]

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 80, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = 260
  const totalHeight = height + margin.top + margin.bottom

  const svg = select(container)
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
    .text('Subject Line Performance')

  // Subtitle
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Open rate vs. spam flag rate by subject variant')

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

  // Grid lines
  const yTicks = [0, 10, 20, 30, 40]
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

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

  // Grouped bars
  const groups = g.selectAll('.group')
    .data(data)
    .join('g')
    .attr('transform', d => `translate(${x0(d.label)},0)`)

  // Open rate bars
  groups.append('rect')
    .attr('x', x1('open'))
    .attr('y', height)
    .attr('width', x1.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => i * 100)
    .ease(easeCubicOut)
    .attr('y', d => y(d.open))
    .attr('height', d => height - y(d.open))

  // Spam rate bars
  groups.append('rect')
    .attr('x', x1('spam'))
    .attr('y', height)
    .attr('width', x1.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => i * 100 + 50)
    .ease(easeCubicOut)
    .attr('y', d => y(d.spam))
    .attr('height', d => height - y(d.spam))

  // Value labels for open rate
  groups.append('text')
    .attr('x', x1('open') + x1.bandwidth() / 2)
    .attr('y', d => y(d.open) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.primary)
    .style('opacity', 0)
    .text(d => `${d.open}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 100)
    .style('opacity', 1)

  // Value labels for spam rate
  groups.append('text')
    .attr('x', x1('spam') + x1.bandwidth() / 2)
    .attr('y', d => y(d.spam) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.orange)
    .style('opacity', 0)
    .text(d => `${d.spam}%`)
    .transition()
    .duration(300)
    .delay((d, i) => 650 + i * 100)
    .style('opacity', 1)

  // X-axis labels (wrapped)
  const labelY = height + 14
  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', d => x0(d.label) + x0.bandwidth() / 2)
    .attr('y', labelY)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
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

  // Legend
  const legend = svg.append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 180}, 14)`)

  // Open rate legend
  legend.append('rect')
    .attr('x', 0).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.85)

  legend.append('text')
    .attr('x', 16).attr('y', 9)
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text('Open Rate')

  // Spam rate legend
  legend.append('rect')
    .attr('x', 90).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0.85)

  legend.append('text')
    .attr('x', 106).attr('y', 9)
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text('Spam Flag')
}

// --- Chart 3: Donut — Behavioral Cluster Distribution ---

function renderBehavioralClusters() {
  const container = chartRef.value
  if (!container) return

  const data = [
    { label: 'Active Evaluators', value: 31 },
    { label: 'Passive Observers', value: 24 },
    { label: 'Quick Converters', value: 19 },
    { label: 'Skeptical Evaluators', value: 18 },
    { label: 'Budget Blockers', value: 8 },
  ]

  const colors = [COLORS.primary, COLORS.orange, COLORS.green, COLORS.purple, '#888']

  const containerWidth = container.clientWidth
  const size = Math.min(containerWidth, 400)
  const radius = size / 2 - 40
  const innerRadius = radius * 0.55
  const totalHeight = size + 60

  const svg = select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  // Title
  svg.append('text')
    .attr('x', containerWidth / 2)
    .attr('y', 22)
    .attr('text-anchor', 'middle')
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Behavioral Cluster Distribution')

  // Subtitle
  svg.append('text')
    .attr('x', containerWidth / 2)
    .attr('y', 40)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Prospect segmentation by observed engagement pattern')

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

  // Animate arcs
  const paths = g.selectAll('.arc')
    .data(arcs)
    .join('path')
    .attr('fill', (d, i) => colors[i])
    .attr('opacity', 0.85)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)

  paths.transition()
    .duration(600)
    .delay((d, i) => i * 80)
    .ease(easeCubicOut)
    .attrTween('d', function (d) {
      const interpolate = d3Interpolate({ startAngle: d.startAngle, endAngle: d.startAngle }, d)
      return t => arc(interpolate(t))
    })

  // Center text
  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .attr('font-size', '24px')
    .attr('font-weight', '700')
    .attr('fill', COLORS.text)
    .style('opacity', 0)
    .text('100%')
    .transition()
    .duration(400)
    .delay(600)
    .style('opacity', 1)

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .style('opacity', 0)
    .text('of prospects')
    .transition()
    .duration(400)
    .delay(650)
    .style('opacity', 1)

  // Labels with lines
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

    // Connector line
    const arcMid = arc.centroid(d)
    group.append('line')
      .attr('x1', arcMid[0] * 1.15)
      .attr('y1', arcMid[1] * 1.15)
      .attr('x2', pos[0] + xOffset)
      .attr('y2', pos[1])
      .attr('stroke', 'rgba(0,0,0,0.15)')
      .attr('stroke-width', 1)

    // Label text
    group.append('text')
      .attr('x', pos[0] + xOffset * 2)
      .attr('y', pos[1])
      .attr('dy', '-0.3em')
      .attr('text-anchor', isRight ? 'start' : 'end')
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(data[i].label)

    // Value text
    group.append('text')
      .attr('x', pos[0] + xOffset * 2)
      .attr('y', pos[1])
      .attr('dy', '0.9em')
      .attr('text-anchor', isRight ? 'start' : 'end')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', colors[i])
      .text(`${data[i].value}%`)
  })

  labelGroups.transition()
    .duration(300)
    .delay((d, i) => 600 + i * 80)
    .style('opacity', 1)
}

// --- Lifecycle ---

watch(() => props.chapterIndex, () => {
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
    class="bg-white border border-black/10 rounded-lg p-4 md:p-6"
  >
    <div ref="chartRef" class="w-full" />
  </div>
</template>
