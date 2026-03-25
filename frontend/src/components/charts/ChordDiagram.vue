<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  matrix: { type: Array, required: true },
  labels: { type: Array, required: true },
  colors: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const DEFAULT_COLORS = [
  '#2068FF', '#ff5600', '#009900', '#AA00FF',
  '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6',
  '#ec4899', '#14b8a6',
]

function getColor(i) {
  const palette = props.colors.length ? props.colors : DEFAULT_COLORS
  return palette[i % palette.length]
}

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.matrix.length || !props.labels.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 500)
  const outerRadius = size / 2 - 40
  const innerRadius = outerRadius - 20
  const totalHeight = size + 60

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg.append('g')
    .attr('transform', `translate(${containerWidth / 2},${size / 2 + 30})`)

  // Compute chord layout
  const chord = d3.chord()
    .padAngle(0.04)
    .sortSubgroups(d3.descending)

  const chords = chord(props.matrix)

  // Arc generator for outer groups
  const arc = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius)

  // Ribbon generator for chords
  const ribbon = d3.ribbon()
    .radius(innerRadius)

  // --- Tooltip ---
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
    .style('max-width', '220px')

  // --- Draw chord ribbons (behind arcs) ---
  const chordPaths = g.selectAll('.chord')
    .data(chords)
    .join('path')
    .attr('class', 'chord')
    .attr('fill', d => getColor(d.source.index))
    .attr('fill-opacity', 0.55)
    .attr('stroke', 'none')

  // Animate chords growing from zero
  chordPaths
    .transition()
    .duration(800)
    .delay((d, i) => i * 30)
    .ease(d3.easeCubicOut)
    .attrTween('d', function (d) {
      const zeroSource = { startAngle: d.source.startAngle, endAngle: d.source.startAngle }
      const zeroTarget = { startAngle: d.target.startAngle, endAngle: d.target.startAngle }
      const interpolateSource = d3.interpolate(zeroSource, d.source)
      const interpolateTarget = d3.interpolate(zeroTarget, d.target)
      return t => ribbon({ source: interpolateSource(t), target: interpolateTarget(t) })
    })

  // --- Draw outer arcs (on top of ribbons) ---
  const arcPaths = g.selectAll('.arc')
    .data(chords.groups)
    .join('path')
    .attr('class', 'arc')
    .attr('fill', d => getColor(d.index))
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')

  // Animate arcs from zero angular extent
  arcPaths
    .transition()
    .duration(600)
    .ease(d3.easeCubicOut)
    .attrTween('d', function (d) {
      const interp = d3.interpolate(
        { startAngle: d.startAngle, endAngle: d.startAngle },
        d
      )
      return t => arc(interp(t))
    })

  // --- Hover interactions (bound after both selections exist) ---
  chordPaths
    .on('mouseenter', (event, d) => {
      chordPaths.attr('fill-opacity', c => c === d ? 0.8 : 0.1)
      arcPaths.attr('opacity', c =>
        c.index === d.source.index || c.index === d.target.index ? 1 : 0.3
      )
      const src = props.labels[d.source.index] || d.source.index
      const tgt = props.labels[d.target.index] || d.target.index
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">${src} → ${tgt}</div>
          <div style="color:var(--color-text-secondary,#555)">Flow: <strong>${d.source.value}</strong></div>
          ${d.source.index !== d.target.index ? `<div style="color:var(--color-text-muted,#888);margin-top:2px">${tgt} → ${src}: <strong>${d.target.value}</strong></div>` : ''}
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      chordPaths.attr('fill-opacity', 0.55)
      arcPaths.attr('opacity', 1)
      tooltip.style('opacity', 0)
    })

  arcPaths
    .on('mouseenter', (event, d) => {
      arcPaths.attr('opacity', c => c.index === d.index ? 1 : 0.3)
      chordPaths.attr('fill-opacity', c =>
        c.source.index === d.index || c.target.index === d.index ? 0.8 : 0.05
      )
      const label = props.labels[d.index] || d.index
      const total = props.matrix[d.index].reduce((sum, v) => sum + v, 0)
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">${label}</div>
          <div style="color:var(--color-text-secondary,#555)">Total flow: <strong>${total}</strong></div>
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      arcPaths.attr('opacity', 1)
      chordPaths.attr('fill-opacity', 0.55)
      tooltip.style('opacity', 0)
    })

  // --- Arc labels ---
  const labelArc = d3.arc()
    .innerRadius(outerRadius + 8)
    .outerRadius(outerRadius + 8)

  g.selectAll('.arc-label')
    .data(chords.groups)
    .join('text')
    .attr('class', 'arc-label')
    .attr('transform', d => {
      const pos = labelArc.centroid(d)
      const midAngle = (d.startAngle + d.endAngle) / 2
      // Flip text on the left side so it reads left-to-right
      const rotate = midAngle > Math.PI
        ? (midAngle * 180 / Math.PI - 90 - 180)
        : (midAngle * 180 / Math.PI - 90)
      return `translate(${pos}) rotate(${rotate})`
    })
    .attr('text-anchor', d => {
      const midAngle = (d.startAngle + d.endAngle) / 2
      return midAngle > Math.PI ? 'end' : 'start'
    })
    .attr('dy', '0.35em')
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text-secondary, #555)')
    .style('opacity', 0)
    .text(d => props.labels[d.index] || '')
    .transition()
    .duration(300)
    .delay(600)
    .style('opacity', 1)
}

// --- Lifecycle ---

watch([() => props.matrix, () => props.labels, () => props.colors], () => {
  nextTick(() => renderChart())
}, { deep: true })

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
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">
        <slot name="title">Communication Flow</slot>
      </h3>
    </div>

    <div v-if="matrix.length && labels.length" ref="chartRef" class="relative w-full" style="min-height: 320px" />

    <div v-else class="flex items-center justify-center h-[280px] text-[var(--color-text-muted)] text-sm">
      <span>No flow data available</span>
    </div>

    <!-- Legend -->
    <div v-if="matrix.length && labels.length" class="flex flex-wrap items-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
      <span
        v-for="(label, i) in labels"
        :key="i"
        class="flex items-center gap-1.5"
      >
        <span
          class="inline-block w-2.5 h-2.5 rounded-full"
          :style="{ backgroundColor: getColor(i) }"
        />
        {{ label }}
      </span>
    </div>
  </div>
</template>
