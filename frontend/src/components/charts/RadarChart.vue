<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useMobileChart } from '../../composables/useMobileChart'

const {
  isMobile, animationDuration, fontSize,
} = useMobileChart()

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
  maxValue: { type: Number, default: 100 },
  levels: { type: Number, default: 5 },
  showLegend: { type: Boolean, default: true },
})

const chartRef = ref(null)
const tooltipRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = [
  '#2068FF',
  '#ff5600',
  '#AA00FF',
  '#009900',
  '#050505',
]

const seriesNames = computed(() => {
  if (!props.data.length) return []
  return Object.keys(props.data[0].values)
})

const hiddenSeries = ref(new Set())

function toggleSeries(name) {
  const next = new Set(hiddenSeries.value)
  if (next.has(name)) {
    next.delete(name)
  } else {
    next.add(name)
  }
  hiddenSeries.value = next
}

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('svg').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.data.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const mobile = isMobile.value
  const dur = animationDuration.value
  const gridLevels = mobile ? 3 : props.levels
  const size = Math.min(containerWidth, mobile ? 320 : 480)
  const margin = mobile ? 40 : 60
  const radius = (size - margin * 2) / 2
  const centerX = size / 2
  const centerY = size / 2

  const axes = props.data
  const angleSlice = (Math.PI * 2) / axes.length

  const rScale = d3.scaleLinear()
    .domain([0, props.maxValue])
    .range([0, radius])

  const svg = d3.select(container)
    .append('svg')
    .attr('width', size)
    .attr('height', size)
    .attr('viewBox', `0 0 ${size} ${size}`)
    .style('display', 'block')
    .style('margin', '0 auto')

  const g = svg.append('g')
    .attr('transform', `translate(${centerX},${centerY})`)

  // Grid circles
  for (let level = 1; level <= gridLevels; level++) {
    const r = (radius / gridLevels) * level
    g.append('circle')
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
      .attr('stroke-dasharray', '2,3')

    g.append('text')
      .attr('x', 4)
      .attr('y', -r)
      .attr('dy', '-0.3em')
      .attr('font-size', fontSize.value.tick)
      .attr('fill', 'var(--color-text-muted, #888)')
      .text(Math.round((props.maxValue / gridLevels) * level))
  }

  // Axis lines + labels
  axes.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x).attr('y2', y)
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')

    const labelDistance = radius + (mobile ? 12 : 18)
    const lx = Math.cos(angle) * labelDistance
    const ly = Math.sin(angle) * labelDistance

    g.append('text')
      .attr('x', lx)
      .attr('y', ly)
      .attr('text-anchor', () => {
        if (Math.abs(lx) < 5) return 'middle'
        return lx > 0 ? 'start' : 'end'
      })
      .attr('dy', '0.35em')
      .attr('font-size', fontSize.value.value)
      .attr('font-weight', '500')
      .attr('fill', 'var(--color-text-secondary, #555)')
      .text(() => {
        if (mobile && d.label.length > 10) return d.label.slice(0, 9) + '\u2026'
        return d.label
      })
  })

  // Series polygons
  const visibleSeries = seriesNames.value.filter(s => !hiddenSeries.value.has(s))
  const radarLine = d3.lineRadial()
    .radius(d => d.r)
    .angle(d => d.angle)
    .curve(d3.curveLinearClosed)

  visibleSeries.forEach((seriesName, si) => {
    const colorIndex = seriesNames.value.indexOf(seriesName)
    const color = COLORS[colorIndex % COLORS.length]

    const points = axes.map((axis, i) => ({
      angle: angleSlice * i,
      r: rScale(Math.min(axis.values[seriesName] ?? 0, props.maxValue)),
    }))

    const path = g.append('path')
      .datum(points)
      .attr('d', radarLine)
      .attr('fill', color)
      .attr('fill-opacity', 0.12)
      .attr('stroke', color)
      .attr('stroke-width', mobile ? 1.5 : 2)
      .attr('stroke-opacity', 0.8)

    if (dur > 0) {
      const finalD = path.attr('d')
      const zeroPoints = axes.map((_, i) => ({
        angle: angleSlice * i,
        r: 0,
      }))
      path
        .attr('d', radarLine(zeroPoints))
        .transition()
        .duration(dur * 0.8)
        .delay(si * 100)
        .ease(d3.easeCubicOut)
        .attr('d', finalD)
    }

    // Data point dots — fewer on mobile
    const dotRadius = mobile ? 2.5 : 3.5
    axes.forEach((axis, i) => {
      const angle = angleSlice * i - Math.PI / 2
      const val = Math.min(axis.values[seriesName] ?? 0, props.maxValue)
      const r = rScale(val)
      const cx = Math.cos(angle) * r
      const cy = Math.sin(angle) * r

      const dot = g.append('circle')
        .attr('cx', cx)
        .attr('cy', cy)
        .attr('fill', color)
        .attr('stroke', 'var(--color-surface, #fff)')
        .attr('stroke-width', 1.5)

      if (dur > 0) {
        dot.attr('r', 0)
          .transition()
          .duration(dur / 2)
          .delay(dur * 0.8 + si * 100)
          .attr('r', dotRadius)
      } else {
        dot.attr('r', dotRadius)
      }
    })
  })

  // Invisible hover/touch targets for tooltip per axis
  axes.forEach((axis, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius

    const target = g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x).attr('y2', y)
      .attr('stroke', 'transparent')
      .attr('stroke-width', mobile ? 24 : 16)
      .attr('cursor', 'pointer')

    // Mouse events
    target
      .on('mouseenter', (event) => showTooltip(event, axis))
      .on('mousemove', (event) => positionTooltip(event))
      .on('mouseleave', () => hideTooltip())

    // Touch events for mobile
    target
      .on('touchstart', (event) => {
        event.preventDefault()
        const touch = event.touches[0]
        showTooltip(touch, axis)
      }, { passive: false })
      .on('touchend', () => hideTooltip())
  })
}

function showTooltip(event, axis) {
  const tooltip = tooltipRef.value
  if (!tooltip) return

  const visibleSeries = seriesNames.value.filter(s => !hiddenSeries.value.has(s))
  let html = `<div style="font-weight:600;margin-bottom:4px;color:var(--color-text,#050505)">${axis.label}</div>`

  for (const name of visibleSeries) {
    const colorIndex = seriesNames.value.indexOf(name)
    const color = COLORS[colorIndex % COLORS.length]
    const val = axis.values[name] ?? 0
    html += `<div style="display:flex;align-items:center;gap:6px;margin-top:2px">
      <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block"></span>
      <span style="color:var(--color-text-secondary,#555)">${name}:</span>
      <span style="font-weight:600;color:var(--color-text,#050505)">${val}</span>
    </div>`
  }

  tooltip.innerHTML = html
  tooltip.style.opacity = '1'
  positionTooltip(event)
}

function positionTooltip(event) {
  const tooltip = tooltipRef.value
  const container = chartRef.value?.parentElement
  if (!tooltip || !container) return
  const rect = container.getBoundingClientRect()
  tooltip.style.left = `${event.clientX - rect.left + 12}px`
  tooltip.style.top = `${event.clientY - rect.top - 12}px`
}

function hideTooltip() {
  if (tooltipRef.value) {
    tooltipRef.value.style.opacity = '0'
  }
}

watch([() => props.data, () => props.maxValue, () => props.levels, hiddenSeries], () => {
  nextTick(() => renderChart())
}, { deep: true })

watch(isMobile, () => nextTick(renderChart))

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
  <div class="relative bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div ref="chartRef" role="img" aria-label="Radar chart" />
    <div
      ref="tooltipRef"
      class="absolute pointer-events-none opacity-0 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-xs shadow-md z-10"
      style="transition: opacity 0.15s ease"
    />

    <!-- Legend -->
    <div v-if="showLegend && seriesNames.length > 1" class="flex flex-wrap items-center gap-3 mt-3 justify-center">
      <button
        v-for="(name, i) in seriesNames"
        :key="name"
        class="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border transition-colors cursor-pointer"
        :class="hiddenSeries.has(name)
          ? 'border-[var(--color-border)] text-[var(--color-text-muted)] opacity-50'
          : 'border-[var(--color-border)] text-[var(--color-text-secondary)]'"
        @click="toggleSeries(name)"
      >
        <span
          class="inline-block w-2.5 h-2.5 rounded-full"
          :style="{ background: hiddenSeries.has(name) ? 'var(--color-text-muted)' : COLORS[i % COLORS.length] }"
        />
        {{ name }}
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="!data.length" class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      No data available
    </div>
  </div>
</template>
