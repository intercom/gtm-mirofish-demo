<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, default: () => [] },
  colorScheme: { type: Array, default: () => ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#f59e0b', '#888888', '#1a5ae0', '#ef4444'] },
  interpolation: { type: String, default: 'curveBasis' },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const isolatedCategory = ref(null)
const disabledCategories = ref(new Set())

const categories = computed(() => {
  if (!props.data.length) return []
  return Object.keys(props.data[0]).filter(k => k !== 'time')
})

const activeCategories = computed(() =>
  categories.value.filter(c => !disabledCategories.value.has(c)),
)

const colorMap = computed(() => {
  const map = {}
  categories.value.forEach((cat, i) => {
    map[cat] = props.colorScheme[i % props.colorScheme.length]
  })
  return map
})

function toggleCategory(cat) {
  if (isolatedCategory.value === cat) {
    isolatedCategory.value = null
    return
  }
  if (isolatedCategory.value) {
    isolatedCategory.value = null
    return
  }
  const next = new Set(disabledCategories.value)
  if (next.has(cat)) {
    next.delete(cat)
  } else {
    if (next.size >= categories.value.length - 1) return
    next.add(cat)
  }
  disabledCategories.value = next
}

function isolateCategory(cat) {
  isolatedCategory.value = isolatedCategory.value === cat ? null : cat
}

// --- D3 rendering ---

const curveMap = {
  curveBasis: d3.curveBasis,
  curveCardinal: d3.curveCardinal,
  curveMonotoneX: d3.curveMonotoneX,
  curveCatmullRom: d3.curveCatmullRom,
  curveNatural: d3.curveNatural,
}

function getCurve() {
  return curveMap[props.interpolation] || d3.curveBasis
}

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.data.length || !activeCategories.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const visibleKeys = isolatedCategory.value
    ? [isolatedCategory.value]
    : activeCategories.value

  const margin = { top: 12, right: 16, bottom: 28, left: 44 }
  const width = containerWidth - margin.left - margin.right
  const height = 240
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const defs = svg.append('defs')
  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const x = d3.scaleLinear()
    .domain(d3.extent(props.data, d => d.time))
    .range([0, width])

  const stack = d3.stack()
    .keys(visibleKeys)
    .offset(isolatedCategory.value ? d3.stackOffsetNone : d3.stackOffsetWiggle)
    .order(d3.stackOrderInsideOut)

  const series = stack(props.data)

  const yExtent = [
    d3.min(series, s => d3.min(s, d => d[0])),
    d3.max(series, s => d3.max(s, d => d[1])),
  ]

  const y = d3.scaleLinear()
    .domain(yExtent)
    .range([height, 0])

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // X-axis labels
  const xTicks = props.data.filter((_, i) => {
    const step = Math.max(1, Math.floor(props.data.length / 8))
    return i % step === 0 || i === props.data.length - 1
  })

  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d.time))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.time}`)

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -6)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => Math.round(d))

  // Area generator
  const area = d3.area()
    .x(d => x(d.data.time))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(getCurve())

  // Stream paths with gradients
  series.forEach((s, i) => {
    const color = colorMap.value[s.key]
    const gradientId = `stream-grad-${i}`

    const gradient = defs.append('linearGradient')
      .attr('id', gradientId)
      .attr('x1', '0%').attr('y1', '0%')
      .attr('x2', '0%').attr('y2', '100%')

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.7)

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.3)
  })

  // Render stream paths
  const paths = g.selectAll('.stream')
    .data(series)
    .join('path')
    .attr('class', 'stream')
    .attr('data-key', d => d.key)
    .attr('fill', (_, i) => `url(#stream-grad-${i})`)
    .attr('stroke', d => colorMap.value[d.key])
    .attr('stroke-width', 0.5)
    .attr('stroke-opacity', 0.3)

  // Animated mount — wipe from zero-height to full
  const zeroArea = d3.area()
    .x(d => x(d.data.time))
    .y0(y(0))
    .y1(y(0))
    .curve(getCurve())

  paths
    .attr('d', zeroArea)
    .transition()
    .duration(800)
    .ease(d3.easeCubicOut)
    .attr('d', area)

  // --- Hover interaction ---

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
    .style('max-width', '200px')

  // Vertical hover line
  const hoverLine = g.append('line')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-dasharray', '3,3')
    .style('opacity', 0)

  // Hover rect covering the chart area
  g.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'crosshair')
    .on('mousemove', function (event) {
      const [mx] = d3.pointer(event, this)
      const timeValue = x.invert(mx)
      const bisect = d3.bisector(d => d.time).left
      const idx = Math.min(bisect(props.data, timeValue), props.data.length - 1)
      const datum = props.data[idx]
      if (!datum) return

      hoverLine
        .attr('x1', x(datum.time))
        .attr('x2', x(datum.time))
        .style('opacity', 1)

      const total = visibleKeys.reduce((sum, k) => sum + (datum[k] || 0), 0)
      const rows = visibleKeys.map(k => {
        const val = datum[k] || 0
        const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0'
        const color = colorMap.value[k]
        return `<div style="display:flex;align-items:center;gap:6px;margin-top:2px">
          <span style="width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0"></span>
          <span style="flex:1;color:var(--color-text-secondary,#555)">${k}</span>
          <span style="font-weight:600;color:var(--color-text,#050505)">${val}</span>
          <span style="color:var(--color-text-muted,#888);font-size:11px">(${pct}%)</span>
        </div>`
      }).join('')

      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${datum.time}</div>
          ${rows}
        `)
        .style('opacity', 1)

      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 16}px`)
        .style('top', `${event.clientY - rect.top - 20}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
      hoverLine.style('opacity', 0)
      paths.transition().duration(200)
        .attr('opacity', 1)
    })

  // Hover highlight on individual streams
  paths
    .on('mouseenter', function (event, d) {
      paths.transition().duration(200)
        .attr('opacity', s => s.key === d.key ? 1 : 0.2)
    })
    .on('mouseleave', () => {
      paths.transition().duration(200)
        .attr('opacity', 1)
    })
    .on('click', (event, d) => {
      isolateCategory(d.key)
    })
    .style('cursor', 'pointer')
}

// --- Lifecycle ---

watch([() => props.data, () => props.colorScheme, () => props.interpolation, activeCategories, isolatedCategory], () => {
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
        <slot name="title">Topic Evolution</slot>
      </h3>
    </div>

    <div
      v-if="data.length && activeCategories.length"
      class="relative"
      ref="chartRef"
      style="height: 280px"
      role="img"
      aria-label="Topic evolution stream graph"
    />

    <div v-else class="flex items-center justify-center h-[240px] text-[var(--color-text-muted)] text-sm">
      <span>No stream data available</span>
    </div>

    <!-- Legend -->
    <div v-if="categories.length" class="flex flex-wrap items-center gap-3 mt-3">
      <button
        v-for="cat in categories"
        :key="cat"
        class="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full transition-all"
        :class="[
          disabledCategories.has(cat)
            ? 'opacity-40 line-through'
            : isolatedCategory === cat
              ? 'ring-1 ring-[var(--color-primary)] bg-[var(--color-primary-light)]'
              : 'hover:bg-[var(--color-tint)]',
        ]"
        :style="{ color: disabledCategories.has(cat) ? '#888' : colorMap[cat] }"
        @click="toggleCategory(cat)"
        @dblclick.prevent="isolateCategory(cat)"
      >
        <span
          class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
          :style="{ background: colorMap[cat], opacity: disabledCategories.has(cat) ? 0.3 : 1 }"
        />
        {{ cat }}
      </button>
    </div>
  </div>
</template>
