<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  primaryLight: 'rgba(32, 104, 255, 0.15)',
  pipelineBar: 'rgba(32, 104, 255, 0.35)',
  orange: '#ff5600',
  text: '#050505',
  muted: '#888',
  gridLine: 'rgba(0, 0, 0, 0.06)',
  target: '#009900',
}

const DATA = [
  { month: 'Apr 25', arr: 1800, pipeline: 2400, conversion: 32 },
  { month: 'May 25', arr: 1840, pipeline: 2650, conversion: 30 },
  { month: 'Jun 25', arr: 1890, pipeline: 2500, conversion: 33 },
  { month: 'Jul 25', arr: 1920, pipeline: 2800, conversion: 31 },
  { month: 'Aug 25', arr: 1960, pipeline: 3000, conversion: 34 },
  { month: 'Sep 25', arr: 1990, pipeline: 2750, conversion: 36 },
  { month: 'Oct 25', arr: 2040, pipeline: 3200, conversion: 35 },
  { month: 'Nov 25', arr: 2080, pipeline: 3400, conversion: 37 },
  { month: 'Dec 25', arr: 2120, pipeline: 3600, conversion: 38 },
  { month: 'Jan 26', arr: 2140, pipeline: 2900, conversion: 33 },
  { month: 'Feb 26', arr: 2170, pipeline: 3100, conversion: 35 },
  { month: 'Mar 26', arr: 2200, pipeline: 3100, conversion: 36 },
]

const ARR_TARGET = 2200

function formatDollars(value) {
  return `$${(value / 1000).toFixed(1)}M`
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function render() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 64, bottom: 40, left: 64 }
  const width = containerWidth - margin.left - margin.right
  const height = 300
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
    .text('Revenue vs Pipeline')

  // Subtitle
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('ARR growth, pipeline value, and win rate over 12 months')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // --- Scales ---
  const x = d3.scaleBand()
    .domain(DATA.map(d => d.month))
    .range([0, width])
    .padding(0.3)

  const xPoint = d => x(d.month) + x.bandwidth() / 2

  const yLeft = d3.scaleLinear()
    .domain([1600, 2400])
    .range([height, 0])

  const yRight = d3.scaleLinear()
    .domain([0, 4000])
    .range([height, 0])

  const yConversion = d3.scaleLinear()
    .domain([20, 45])
    .range([height, 0])

  // --- Grid lines ---
  const leftTicks = [1600, 1800, 2000, 2200, 2400]
  g.selectAll('.grid-line')
    .data(leftTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => yLeft(d))
    .attr('y2', d => yLeft(d))
    .attr('stroke', COLORS.gridLine)
    .attr('stroke-dasharray', '2,3')

  // --- Left Y-axis labels (ARR) ---
  g.selectAll('.y-left-label')
    .data(leftTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => yLeft(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => formatDollars(d))

  g.append('text')
    .attr('x', -8)
    .attr('y', -12)
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.primary)
    .text('ARR')

  // --- Right Y-axis labels (Pipeline) ---
  const rightTicks = [0, 1000, 2000, 3000, 4000]
  g.selectAll('.y-right-label')
    .data(rightTicks)
    .join('text')
    .attr('x', width + 8)
    .attr('y', d => yRight(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'start')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => formatDollars(d))

  g.append('text')
    .attr('x', width + 8)
    .attr('y', -12)
    .attr('text-anchor', 'start')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.pipelineBar)
    .text('Pipeline')

  // --- X-axis labels ---
  g.selectAll('.x-label')
    .data(DATA)
    .join('text')
    .attr('x', d => xPoint(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => d.month)

  // --- ARR Target line (dashed) ---
  g.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', yLeft(ARR_TARGET))
    .attr('y2', yLeft(ARR_TARGET))
    .attr('stroke', COLORS.target)
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '6,4')
    .attr('opacity', 0.7)

  g.append('text')
    .attr('x', width)
    .attr('y', yLeft(ARR_TARGET) - 6)
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.target)
    .text(`Target ${formatDollars(ARR_TARGET)}`)

  // --- Area chart: ARR (left y-axis) ---
  const area = d3.area()
    .x(d => xPoint(d))
    .y0(height)
    .y1(d => yLeft(d.arr))
    .curve(d3.curveMonotoneX)

  const areaPath = g.append('path')
    .datum(DATA)
    .attr('fill', COLORS.primaryLight)
    .attr('d', area)
    .attr('opacity', 0)

  areaPath.transition()
    .duration(700)
    .ease(d3.easeCubicOut)
    .attr('opacity', 1)

  // ARR line on top of area
  const arrLine = d3.line()
    .x(d => xPoint(d))
    .y(d => yLeft(d.arr))
    .curve(d3.curveMonotoneX)

  const arrPath = g.append('path')
    .datum(DATA)
    .attr('fill', 'none')
    .attr('stroke', COLORS.primary)
    .attr('stroke-width', 2.5)
    .attr('d', arrLine)

  const arrPathLength = arrPath.node().getTotalLength()
  arrPath
    .attr('stroke-dasharray', `${arrPathLength} ${arrPathLength}`)
    .attr('stroke-dashoffset', arrPathLength)
    .transition()
    .duration(900)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)

  // --- Bar chart: Pipeline (right y-axis) ---
  g.selectAll('.pipeline-bar')
    .data(DATA)
    .join('rect')
    .attr('x', d => x(d.month))
    .attr('y', height)
    .attr('width', x.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', COLORS.pipelineBar)
    .transition()
    .duration(600)
    .delay((d, i) => i * 40)
    .ease(d3.easeCubicOut)
    .attr('y', d => yRight(d.pipeline))
    .attr('height', d => height - yRight(d.pipeline))

  // --- Conversion rate line overlay ---
  const convLine = d3.line()
    .x(d => xPoint(d))
    .y(d => yConversion(d.conversion))
    .curve(d3.curveMonotoneX)

  const convPath = g.append('path')
    .datum(DATA)
    .attr('fill', 'none')
    .attr('stroke', COLORS.orange)
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '4,3')
    .attr('d', convLine)

  const convPathLength = convPath.node().getTotalLength()
  convPath
    .attr('stroke-dasharray', `${convPathLength} ${convPathLength}`)
    .attr('stroke-dashoffset', convPathLength)
    .transition()
    .duration(900)
    .delay(200)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)
    .on('end', function () {
      d3.select(this).attr('stroke-dasharray', '4,3')
    })

  // Conversion rate dots
  g.selectAll('.conv-dot')
    .data(DATA)
    .join('circle')
    .attr('cx', d => xPoint(d))
    .attr('cy', d => yConversion(d.conversion))
    .attr('r', 0)
    .attr('fill', '#fff')
    .attr('stroke', COLORS.orange)
    .attr('stroke-width', 1.5)
    .transition()
    .duration(300)
    .delay((d, i) => 700 + i * 40)
    .ease(d3.easeCubicOut)
    .attr('r', 3)

  // --- Legend (top-right) ---
  const legend = svg.append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 280}, 10)`)

  const legendItems = [
    { label: 'ARR', color: COLORS.primary, type: 'line' },
    { label: 'Pipeline', color: COLORS.pipelineBar, type: 'rect' },
    { label: 'Win Rate', color: COLORS.orange, type: 'dash' },
    { label: 'Target', color: COLORS.target, type: 'target' },
  ]

  legendItems.forEach((item, i) => {
    const xOff = i * 72
    if (item.type === 'line') {
      legend.append('line')
        .attr('x1', xOff).attr('y1', 5)
        .attr('x2', xOff + 14).attr('y2', 5)
        .attr('stroke', item.color).attr('stroke-width', 2)
    } else if (item.type === 'rect') {
      legend.append('rect')
        .attr('x', xOff).attr('y', 0)
        .attr('width', 10).attr('height', 10)
        .attr('rx', 2).attr('fill', item.color)
    } else if (item.type === 'dash') {
      legend.append('line')
        .attr('x1', xOff).attr('y1', 5)
        .attr('x2', xOff + 14).attr('y2', 5)
        .attr('stroke', item.color).attr('stroke-width', 2)
        .attr('stroke-dasharray', '4,2')
    } else {
      legend.append('line')
        .attr('x1', xOff).attr('y1', 5)
        .attr('x2', xOff + 14).attr('y2', 5)
        .attr('stroke', item.color).attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '6,4')
    }
    legend.append('text')
      .attr('x', xOff + 18).attr('y', 9)
      .attr('font-size', '11px').attr('fill', '#555')
      .text(item.label)
  })

  // --- Tooltip ---
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('background', '#fff')
    .style('border', '1px solid rgba(0,0,0,0.1)')
    .style('border-radius', '8px')
    .style('padding', '10px 14px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.08)')
    .style('opacity', 0)
    .style('transition', 'opacity 0.15s')
    .style('z-index', 10)

  const hoverLine = g.append('line')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-width', 1)
    .style('opacity', 0)

  // Invisible rects for hover detection per bar
  g.selectAll('.hover-rect')
    .data(DATA)
    .join('rect')
    .attr('x', d => x(d.month) - x.step() * x.padding() / 2)
    .attr('y', 0)
    .attr('width', x.step())
    .attr('height', height)
    .attr('fill', 'transparent')
    .on('mouseenter', (event, d) => {
      const xPos = xPoint(d)
      hoverLine
        .attr('x1', xPos)
        .attr('x2', xPos)
        .style('opacity', 1)

      tooltip
        .html(`
          <div style="font-weight:600; margin-bottom:4px; color:${COLORS.text}">${d.month}</div>
          <div style="display:flex; align-items:center; gap:6px; margin-bottom:2px">
            <span style="width:8px;height:8px;border-radius:50%;background:${COLORS.primary};display:inline-block"></span>
            ARR: <strong>${formatDollars(d.arr)}</strong>
          </div>
          <div style="display:flex; align-items:center; gap:6px; margin-bottom:2px">
            <span style="width:8px;height:8px;border-radius:2px;background:${COLORS.pipelineBar};display:inline-block"></span>
            Pipeline: <strong>${formatDollars(d.pipeline)}</strong>
          </div>
          <div style="display:flex; align-items:center; gap:6px">
            <span style="width:8px;height:8px;border-radius:50%;background:${COLORS.orange};display:inline-block"></span>
            Win Rate: <strong>${d.conversion}%</strong>
          </div>
        `)
        .style('opacity', 1)

      const tooltipNode = tooltip.node()
      const tooltipWidth = tooltipNode.offsetWidth
      const svgRect = container.getBoundingClientRect()
      const mouseX = xPos + margin.left
      const left = mouseX + tooltipWidth + 16 > svgRect.width
        ? mouseX - tooltipWidth - 12
        : mouseX + 12
      tooltip
        .style('left', `${left}px`)
        .style('top', `${margin.top + 20}px`)
    })
    .on('mouseleave', () => {
      hoverLine.style('opacity', 0)
      tooltip.style('opacity', 0)
    })
}

onMounted(() => {
  nextTick(() => render())
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => render(), 200)
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
    class="bg-white border border-black/10 rounded-lg p-4 md:p-6"
  >
    <div ref="chartRef" class="w-full" style="position: relative" />
  </div>
</template>
