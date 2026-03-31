<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, required: true },
  dimensions: {
    type: Array,
    required: true,
    validator: (v) => v.every((d) => d.key && d.label),
  },
  colorBy: { type: String, default: null },
})

const emit = defineEmits(['brush', 'hover'])

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
}

const CATEGORY_PALETTE = [
  COLORS.primary,
  COLORS.orange,
  COLORS.purple,
  COLORS.green,
  '#e6194b',
  '#3cb44b',
  '#ffe119',
  '#4363d8',
]

// Track dimension order (reorderable), brush state, and hover
const dimOrder = ref([])
const brushExtents = ref({})
const hoveredIndex = ref(null)

watch(
  () => props.dimensions,
  (dims) => {
    dimOrder.value = dims.map((d) => d.key)
    brushExtents.value = {}
  },
  { immediate: true },
)

const colorCategories = computed(() => {
  if (!props.colorBy) return []
  return [...new Set(props.data.map((d) => d[props.colorBy]))]
})

const colorScale = computed(() => {
  const cats = colorCategories.value
  if (!cats.length) return () => COLORS.primary
  return d3
    .scaleOrdinal()
    .domain(cats)
    .range(CATEGORY_PALETTE.slice(0, Math.max(cats.length, 1)))
})

// --- Rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.data.length || !dimOrder.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 40, right: 24, bottom: 12, left: 24 }
  const width = containerWidth - margin.left - margin.right
  const height = 320
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const dims = dimOrder.value
  const dimConfigs = new Map(props.dimensions.map((d) => [d.key, d]))

  // X scale: position each axis
  const x = d3.scalePoint().domain(dims).range([0, width]).padding(0.1)

  // Y scales per dimension
  const yScales = {}
  for (const key of dims) {
    const cfg = dimConfigs.get(key)
    const values = props.data.map((d) => d[key]).filter((v) => v != null)
    if (cfg && cfg.type === 'categorical') {
      const cats = [...new Set(values)]
      yScales[key] = d3.scalePoint().domain(cats).range([height, 0]).padding(0.5)
    } else {
      const extent = d3.extent(values)
      const pad = (extent[1] - extent[0]) * 0.05 || 1
      yScales[key] = d3
        .scaleLinear()
        .domain([extent[0] - pad, extent[1] + pad])
        .range([height, 0])
    }
  }

  // Line generator: for each data row, connect across axes
  function linePath(d) {
    const points = dims
      .map((key) => {
        const val = d[key]
        if (val == null || !yScales[key]) return null
        return [x(key), yScales[key](val)]
      })
      .filter(Boolean)
    if (points.length < 2) return null
    return d3.line().curve(d3.curveMonotoneX)(points)
  }

  // Determine which rows pass all brush filters
  function isActive(d) {
    for (const [key, ext] of Object.entries(brushExtents.value)) {
      if (!ext) continue
      const scale = yScales[key]
      if (!scale || !scale.invert) continue
      const lo = scale.invert(ext[1])
      const hi = scale.invert(ext[0])
      const val = d[key]
      if (val == null || val < lo || val > hi) return false
    }
    return true
  }

  // Draw lines (background: dimmed, foreground: active)
  g.append('g')
    .attr('class', 'bg-lines')
    .selectAll('path')
    .data(props.data)
    .join('path')
    .attr('d', linePath)
    .attr('fill', 'none')
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-width', 1)

  const fgLines = g
    .append('g')
    .attr('class', 'fg-lines')
    .selectAll('path')
    .data(props.data)
    .join('path')
    .attr('d', linePath)
    .attr('fill', 'none')
    .attr('stroke', (d) =>
      props.colorBy ? colorScale.value(d[props.colorBy]) : COLORS.primary,
    )
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.7)
    .style('pointer-events', 'stroke')
    .style('cursor', 'pointer')

  // Animate lines in
  fgLines.each(function () {
    const path = d3.select(this)
    const totalLength = this.getTotalLength()
    if (!totalLength) return
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(600)
      .delay((_, i) => i * 4)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
  })

  // Hover interaction on lines
  fgLines
    .on('mouseenter', function (event, d) {
      const idx = props.data.indexOf(d)
      hoveredIndex.value = idx
      fgLines
        .attr('stroke-opacity', (dd) => (dd === d ? 1 : 0.08))
        .attr('stroke-width', (dd) => (dd === d ? 3 : 1))
      emit('hover', { index: idx, data: d })
    })
    .on('mouseleave', () => {
      hoveredIndex.value = null
      updateLineVisibility()
      emit('hover', null)
    })

  // Draw axes
  const axisGroups = g
    .selectAll('.axis-group')
    .data(dims)
    .join('g')
    .attr('class', 'axis-group')
    .attr('transform', (d) => `translate(${x(d)},0)`)

  // Axis lines and ticks
  axisGroups.each(function (key) {
    const scale = yScales[key]
    const axis = d3.axisLeft(scale).ticks(5).tickSize(4)
    const cfg = dimConfigs.get(key)
    if (cfg && cfg.format) {
      axis.tickFormat(d3.format(cfg.format))
    }
    d3.select(this)
      .call(axis)
      .call((g) => g.select('.domain').attr('stroke', 'rgba(0,0,0,0.2)'))
      .call((g) =>
        g.selectAll('.tick line').attr('stroke', 'rgba(0,0,0,0.1)'),
      )
      .call((g) =>
        g
          .selectAll('.tick text')
          .attr('font-size', '10px')
          .attr('fill', '#888'),
      )
  })

  // Axis labels (draggable for reordering)
  axisGroups
    .append('text')
    .attr('y', -12)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .style('cursor', 'grab')
    .text((key) => dimConfigs.get(key)?.label || key)
    .call(
      d3
        .drag()
        .on('start', function () {
          d3.select(this).style('cursor', 'grabbing')
        })
        .on('drag', function (event, key) {
          // Find the closest axis position to drop
          const mouseX = event.x + x(key)
          let closestKey = key
          let closestDist = Infinity
          for (const k of dims) {
            const dist = Math.abs(x(k) - mouseX)
            if (dist < closestDist) {
              closestDist = dist
              closestKey = k
            }
          }
          if (closestKey !== key) {
            const order = [...dimOrder.value]
            const fromIdx = order.indexOf(key)
            const toIdx = order.indexOf(closestKey)
            order.splice(fromIdx, 1)
            order.splice(toIdx, 0, key)
            dimOrder.value = order
            nextTick(() => renderChart())
          }
        })
        .on('end', function () {
          d3.select(this).style('cursor', 'grab')
        }),
    )

  // Brushes on each axis
  axisGroups.each(function (key) {
    const scale = yScales[key]
    if (!scale.invert) return // skip categorical axes

    const brush = d3
      .brushY()
      .extent([
        [-10, 0],
        [10, height],
      ])
      .on('brush end', function (event) {
        if (event.selection) {
          brushExtents.value = { ...brushExtents.value, [key]: event.selection }
        } else {
          const updated = { ...brushExtents.value }
          delete updated[key]
          brushExtents.value = updated
        }
        updateLineVisibility()
        emit('brush', { ...brushExtents.value })
      })

    const brushG = d3.select(this).append('g').attr('class', 'brush').call(brush)

    // Style the brush selection
    brushG
      .selectAll('.selection')
      .attr('fill', COLORS.primary)
      .attr('fill-opacity', 0.15)
      .attr('stroke', COLORS.primary)
      .attr('stroke-width', 1)

    // Restore brush if we had one from a re-render
    const savedExtent = brushExtents.value[key]
    if (savedExtent) {
      brushG.call(brush.move, savedExtent)
    }
  })

  function updateLineVisibility() {
    const hasBrush = Object.keys(brushExtents.value).length > 0
    fgLines
      .attr('stroke-opacity', (d) => {
        if (hoveredIndex.value != null) {
          return props.data.indexOf(d) === hoveredIndex.value ? 1 : 0.08
        }
        if (!hasBrush) return 0.7
        return isActive(d) ? 0.85 : 0.05
      })
      .attr('stroke-width', (d) => {
        if (hoveredIndex.value != null) {
          return props.data.indexOf(d) === hoveredIndex.value ? 3 : 1
        }
        if (!hasBrush) return 1.5
        return isActive(d) ? 2 : 0.5
      })
  }

  // Tooltip
  const tooltip = d3
    .select(container)
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

  fgLines
    .on('mouseenter.tooltip', function (event, d) {
      const lines = dims
        .map((key) => {
          const cfg = dimConfigs.get(key)
          const label = cfg?.label || key
          let val = d[key]
          if (val != null && cfg?.format) {
            val = d3.format(cfg.format)(val)
          }
          return `<div style="display:flex;justify-content:space-between;gap:12px"><span style="color:#888">${label}</span><span style="font-weight:600">${val ?? '—'}</span></div>`
        })
        .join('')

      const colorLabel = props.colorBy ? d[props.colorBy] : null
      const header = colorLabel
        ? `<div style="font-weight:600;color:${colorScale.value(colorLabel)};margin-bottom:4px">${colorLabel}</div>`
        : ''

      tooltip.html(`${header}${lines}`).style('opacity', 1)
    })
    .on('mousemove.tooltip', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 20}px`)
    })
    .on('mouseleave.tooltip', () => {
      tooltip.style('opacity', 0)
    })
}

// --- Lifecycle ---

watch(
  [() => props.data, () => props.colorBy, dimOrder],
  () => nextTick(() => renderChart()),
  { deep: true },
)

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
      <slot name="header">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">
          Parallel Coordinates
        </h3>
      </slot>
    </div>

    <div
      v-if="data.length && dimensions.length"
      ref="chartRef"
      class="relative w-full"
      style="min-height: 372px"
      role="img"
      aria-label="Parallel coordinates chart"
    />

    <div
      v-else
      class="flex items-center justify-center h-[320px] text-[var(--color-text-muted)] text-sm"
    >
      <span>No data available</span>
    </div>

    <!-- Legend -->
    <div
      v-if="colorBy && colorCategories.length"
      class="flex flex-wrap items-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]"
    >
      <span
        v-for="cat in colorCategories"
        :key="cat"
        class="flex items-center gap-1.5"
      >
        <span
          class="inline-block w-3 h-[3px] rounded-full"
          :style="{ background: colorScale(cat) }"
        />
        {{ cat }}
      </span>
    </div>
  </div>
</template>
