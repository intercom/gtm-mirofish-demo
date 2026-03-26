<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  timelineA: { type: Array, default: () => [] },
  timelineB: { type: Array, default: () => [] },
  labelA: { type: String, default: 'Sim A' },
  labelB: { type: String, default: 'Sim B' },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || (!props.timelineA.length && !props.timelineB.length)) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 20, right: 20, bottom: 28, left: 44 }
  const laneHeight = 60
  const gap = 24
  const width = containerWidth - margin.left - margin.right
  const height = laneHeight * 2 + gap
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxRound = Math.max(
    props.timelineA.length ? props.timelineA[props.timelineA.length - 1].round : 0,
    props.timelineB.length ? props.timelineB[props.timelineB.length - 1].round : 0,
  )

  const x = d3.scaleLinear().domain([1, maxRound]).range([0, width])

  const maxActions = Math.max(
    d3.max(props.timelineA, d => d.actions) || 0,
    d3.max(props.timelineB, d => d.actions) || 0,
  )

  // Lane A (top)
  const yA = d3.scaleLinear().domain([0, maxActions]).range([laneHeight, 0])

  // Lane label
  g.append('text')
    .attr('x', -8).attr('y', laneHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', '#2068FF')
    .text('A')

  // Lane A background
  g.append('rect')
    .attr('width', width).attr('height', laneHeight)
    .attr('fill', 'rgba(32, 104, 255, 0.03)')
    .attr('rx', 4)

  // Lane A bars
  const barWidth = Math.max(1, width / maxRound - 1)

  g.selectAll('.bar-a')
    .data(props.timelineA)
    .join('rect')
    .attr('x', d => x(d.round) - barWidth / 2)
    .attr('y', d => yA(d.actions))
    .attr('width', barWidth)
    .attr('height', d => laneHeight - yA(d.actions))
    .attr('fill', '#2068FF')
    .attr('opacity', 0.6)
    .attr('rx', 1)

  // Lane B (bottom)
  const yBOffset = laneHeight + gap
  const yB = d3.scaleLinear().domain([0, maxActions]).range([0, laneHeight])

  g.append('text')
    .attr('x', -8).attr('y', yBOffset + laneHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', '#ff5600')
    .text('B')

  g.append('rect')
    .attr('y', yBOffset)
    .attr('width', width).attr('height', laneHeight)
    .attr('fill', 'rgba(255, 86, 0, 0.03)')
    .attr('rx', 4)

  g.selectAll('.bar-b')
    .data(props.timelineB)
    .join('rect')
    .attr('x', d => x(d.round) - barWidth / 2)
    .attr('y', yBOffset)
    .attr('width', barWidth)
    .attr('height', d => yB(d.actions))
    .attr('fill', '#ff5600')
    .attr('opacity', 0.6)
    .attr('rx', 1)

  // Shared x-axis in the gap
  const axisY = laneHeight + gap / 2
  g.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', axisY).attr('y2', axisY)
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.15))')

  const step = Math.max(1, Math.floor(maxRound / 10))
  const xLabels = []
  for (let r = 1; r <= maxRound; r += step) xLabels.push(r)
  if (xLabels[xLabels.length - 1] !== maxRound) xLabels.push(maxRound)

  g.selectAll('.x-label')
    .data(xLabels)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', axisY)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d}`)

  // Scrubber line on hover
  const scrubber = g.append('line')
    .attr('y1', 0).attr('y2', height)
    .attr('stroke', 'var(--color-text, #050505)')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')
    .style('opacity', 0)

  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')

  g.append('rect')
    .attr('width', width).attr('height', height)
    .attr('fill', 'transparent')
    .on('mousemove', (event) => {
      const [mx] = d3.pointer(event)
      const round = Math.round(x.invert(mx))
      const ptA = props.timelineA.find(d => d.round === round)
      const ptB = props.timelineB.find(d => d.round === round)
      if (!ptA && !ptB) return

      scrubber.attr('x1', x(round)).attr('x2', x(round)).style('opacity', 0.6)

      let html = `<div style="font-weight:600;color:var(--color-text);margin-bottom:3px">Round ${round}</div>`
      if (ptA) html += `<div style="color:#2068FF">${props.labelA}: ${ptA.actions} actions</div>`
      if (ptB) html += `<div style="color:#ff5600">${props.labelB}: ${ptB.actions} actions</div>`

      const rect = container.getBoundingClientRect()
      tooltip.html(html).style('opacity', 1)
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      scrubber.style('opacity', 0)
      tooltip.style('opacity', 0)
    })
}

watch([() => props.timelineA, () => props.timelineB], () => nextTick(renderChart), { deep: true })

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
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Activity Timeline</h3>
      <div class="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm bg-[#2068FF] opacity-60" />
          {{ labelA }}
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-2 rounded-sm bg-[#ff5600] opacity-60" />
          {{ labelB }}
        </span>
      </div>
    </div>

    <div v-if="timelineA.length || timelineB.length" ref="chartRef" class="relative" style="height: 192px" />
    <div v-else class="flex items-center justify-center h-[160px] text-[var(--color-text-muted)] text-sm">
      No timeline data available
    </div>
  </div>
</template>
