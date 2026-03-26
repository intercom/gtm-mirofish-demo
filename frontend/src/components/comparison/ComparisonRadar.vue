<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, default: () => [] },
  simAName: { type: String, default: 'Sim A' },
  simBName: { type: String, default: 'Sim B' },
})

const emit = defineEmits(['selectDimension'])

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.data.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 320)
  const margin = 48
  const radius = (size - margin * 2) / 2
  const cx = size / 2
  const cy = size / 2

  const svg = d3.select(container)
    .append('svg')
    .attr('width', size)
    .attr('height', size)
    .attr('viewBox', `0 0 ${size} ${size}`)

  const g = svg.append('g').attr('transform', `translate(${cx},${cy})`)
  const dims = props.data
  const n = dims.length
  const angleSlice = (2 * Math.PI) / n

  // Grid circles
  const levels = 5
  for (let i = 1; i <= levels; i++) {
    const r = (radius / levels) * i
    g.append('circle')
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
      .attr('stroke-dasharray', i < levels ? '2,3' : 'none')
  }

  // Axis lines + labels
  dims.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x2 = radius * Math.cos(angle)
    const y2 = radius * Math.sin(angle)

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')

    const labelRadius = radius + 16
    const lx = labelRadius * Math.cos(angle)
    const ly = labelRadius * Math.sin(angle)

    g.append('text')
      .attr('x', lx).attr('y', ly)
      .attr('text-anchor', Math.abs(lx) < 5 ? 'middle' : lx > 0 ? 'start' : 'end')
      .attr('dy', Math.abs(ly) < 5 ? '0.35em' : ly > 0 ? '0.8em' : '-0.3em')
      .attr('font-size', '10px')
      .attr('fill', 'var(--color-text-muted, #888)')
      .attr('cursor', 'pointer')
      .text(d.dimension.length > 14 ? d.dimension.slice(0, 12) + '...' : d.dimension)
      .on('click', () => emit('selectDimension', d.dimension))
  })

  // Radar area helper
  const radarLine = d3.lineRadial()
    .radius(d => d)
    .angle((_, i) => angleSlice * i)
    .curve(d3.curveLinearClosed)

  // Sim A polygon
  const valuesA = dims.map(d => d.valueA * radius)
  const pathA = g.append('path')
    .datum(valuesA)
    .attr('d', radarLine)
    .attr('fill', 'rgba(32, 104, 255, 0.15)')
    .attr('stroke', '#2068FF')
    .attr('stroke-width', 2)
    .style('opacity', 0)

  pathA.transition().duration(600).style('opacity', 1)

  // Sim A dots
  dims.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const r = d.valueA * radius
    g.append('circle')
      .attr('cx', r * Math.cos(angle))
      .attr('cy', r * Math.sin(angle))
      .attr('r', 3.5)
      .attr('fill', '#2068FF')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
  })

  // Sim B polygon
  const valuesB = dims.map(d => d.valueB * radius)
  const pathB = g.append('path')
    .datum(valuesB)
    .attr('d', radarLine)
    .attr('fill', 'rgba(255, 86, 0, 0.15)')
    .attr('stroke', '#ff5600')
    .attr('stroke-width', 2)
    .style('opacity', 0)

  pathB.transition().duration(600).delay(200).style('opacity', 1)

  // Sim B dots
  dims.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const r = d.valueB * radius
    g.append('circle')
      .attr('cx', r * Math.cos(angle))
      .attr('cy', r * Math.sin(angle))
      .attr('r', 3.5)
      .attr('fill', '#ff5600')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
  })
}

watch(() => props.data, () => nextTick(renderChart), { deep: true })

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
    <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Performance Radar</h3>

    <div v-if="data.length" ref="chartRef" class="flex justify-center" style="min-height: 280px" />
    <div v-else class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      No comparison data available
    </div>

    <!-- Legend -->
    <div v-if="data.length" class="flex items-center justify-center gap-6 mt-2 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#2068FF] rounded" />
        {{ simAName }}
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-0.5 bg-[#ff5600] rounded" />
        {{ simBName }}
      </span>
    </div>
  </div>
</template>
