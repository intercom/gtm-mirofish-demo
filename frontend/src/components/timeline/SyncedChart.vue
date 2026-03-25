<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useTimelineSync } from '@/composables/useTimelineSync'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  chartComponent: { type: [Object, Function], default: null },
  data: { type: Array, default: () => [] },
  timeField: { type: String, required: true },
  highlightMode: {
    type: String,
    default: 'crosshair',
    validator: v => ['point', 'range', 'crosshair'].includes(v),
  },
  chartPadding: {
    type: Object,
    default: () => ({ left: 36, right: 16, top: 12, bottom: 28 }),
  },
})

const emit = defineEmits(['position-change'])

const { position, setPosition } = useTimelineSync()

const containerRef = ref(null)
const overlayRef = ref(null)
const dims = ref({ width: 0, height: 0 })
let resizeObserver = null
let resizeTimer = null

// Compute time extent from data
const timeExtent = computed(() => {
  if (!props.data.length) return [0, 1]
  const values = props.data.map(d => d[props.timeField]).filter(v => v != null)
  if (!values.length) return [0, 1]
  return d3.extent(values)
})

// Map normalized position (0–1) to pixel X within the chart area
const timeScale = computed(() => {
  const { left, right } = props.chartPadding
  return d3.scaleLinear()
    .domain([0, 1])
    .range([left, dims.value.width - right])
})

// Chart area bounds (inside padding)
const chartArea = computed(() => {
  const { left, right, top, bottom } = props.chartPadding
  return {
    x: left,
    y: top,
    width: Math.max(0, dims.value.width - left - right),
    height: Math.max(0, dims.value.height - top - bottom),
  }
})

// For 'point' mode: snap to the nearest data point
const snappedPosition = computed(() => {
  if (props.highlightMode !== 'point' || !props.data.length) return position.value

  const [min, max] = timeExtent.value
  const range = max - min
  if (range === 0) return position.value

  const targetTime = min + position.value * range

  let closest = props.data[0]
  let closestDist = Infinity
  for (const d of props.data) {
    const dist = Math.abs(d[props.timeField] - targetTime)
    if (dist < closestDist) {
      closestDist = dist
      closest = d
    }
  }
  return (closest[props.timeField] - min) / range
})

// Pixel X for the current indicator
const indicatorX = computed(() => {
  const pos = props.highlightMode === 'point' ? snappedPosition.value : position.value
  return timeScale.value(pos)
})

function renderOverlay() {
  if (!overlayRef.value || !dims.value.width) return

  const svg = d3.select(overlayRef.value)
  svg.selectAll('*').remove()

  const { width, height } = dims.value
  svg.attr('width', width).attr('height', height)

  if (!props.data.length) return

  const area = chartArea.value
  const x = indicatorX.value

  if (props.highlightMode === 'crosshair') {
    renderCrosshair(svg, x, area)
  } else if (props.highlightMode === 'range') {
    renderRange(svg, x, area)
  } else if (props.highlightMode === 'point') {
    renderPoint(svg, x, area)
  }
}

function renderCrosshair(svg, x, area) {
  svg.append('line')
    .attr('x1', x).attr('x2', x)
    .attr('y1', area.y).attr('y2', area.y + area.height)
    .attr('stroke', 'var(--color-primary, #2068FF)')
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '4,3')
    .attr('opacity', 0.8)

  // Diamond marker at top
  svg.append('path')
    .attr('d', d3.symbol().type(d3.symbolDiamond).size(48)())
    .attr('transform', `translate(${x}, ${area.y})`)
    .attr('fill', 'var(--color-primary, #2068FF)')
}

function renderRange(svg, x, area) {
  const rangeWidth = Math.max(0, x - area.x)

  svg.append('rect')
    .attr('x', area.x).attr('y', area.y)
    .attr('width', rangeWidth).attr('height', area.height)
    .attr('fill', 'var(--color-primary, #2068FF)')
    .attr('opacity', 0.08)

  // Edge line
  svg.append('line')
    .attr('x1', x).attr('x2', x)
    .attr('y1', area.y).attr('y2', area.y + area.height)
    .attr('stroke', 'var(--color-primary, #2068FF)')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.7)

  // Small triangle marker at top
  const markerSize = 6
  svg.append('path')
    .attr('d', `M${x},${area.y} L${x - markerSize},${area.y - markerSize} L${x + markerSize},${area.y - markerSize} Z`)
    .attr('fill', 'var(--color-primary, #2068FF)')
}

function renderPoint(svg, x, area) {
  // Vertical guide line (subtle)
  svg.append('line')
    .attr('x1', x).attr('x2', x)
    .attr('y1', area.y).attr('y2', area.y + area.height)
    .attr('stroke', 'var(--color-primary, #2068FF)')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '2,4')
    .attr('opacity', 0.4)

  // Pulse ring
  svg.append('circle')
    .attr('cx', x).attr('cy', area.y)
    .attr('r', 10)
    .attr('fill', 'none')
    .attr('stroke', 'var(--color-primary, #2068FF)')
    .attr('stroke-width', 1)
    .attr('opacity', 0.3)

  // Solid dot at top
  svg.append('circle')
    .attr('cx', x).attr('cy', area.y)
    .attr('r', 4)
    .attr('fill', 'var(--color-primary, #2068FF)')
}

// Bidirectional: click on chart area updates timeline position
function handleClick(event) {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const { left, right } = props.chartPadding
  const chartWidth = dims.value.width - left - right

  if (chartWidth <= 0) return
  const normalized = Math.max(0, Math.min(1, (clickX - left) / chartWidth))

  setPosition(normalized)
  emit('position-change', normalized)
}

function updateDimensions() {
  if (!containerRef.value) return
  const { width, height } = containerRef.value.getBoundingClientRect()
  dims.value = { width, height }
  nextTick(() => renderOverlay())
}

watch(position, () => renderOverlay())
watch(() => props.highlightMode, () => renderOverlay())
watch(() => props.data, () => nextTick(() => renderOverlay()), { deep: true })

onMounted(() => {
  updateDimensions()
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(updateDimensions, 150)
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div
    ref="containerRef"
    class="synced-chart"
    @click="handleClick"
  >
    <component
      v-if="chartComponent"
      :is="chartComponent"
      :data="data"
      v-bind="$attrs"
    />
    <slot v-else />
    <svg ref="overlayRef" class="synced-chart__overlay" />
  </div>
</template>

<style scoped>
.synced-chart {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: crosshair;
}

.synced-chart__overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
