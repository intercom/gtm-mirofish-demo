<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Object, required: true },
  colorScheme: {
    type: Array,
    default: () => [
      '#2068FF', '#ff5600', '#AA00FF', '#009900',
      '#f59e0b', '#6366f1', '#ec4899', '#14b8a6',
    ],
  },
  centerLabel: { type: String, default: 'Total' },
})

const emit = defineEmits(['segment-click'])

const chartRef = ref(null)
const breadcrumbs = ref([])
let resizeObserver = null
let resizeTimer = null

// Persistent D3 state across renders (survives zoom without full re-render)
let svg = null
let arcGroup = null
let arcPaths = null
let rootNode = null
let currentFocus = null
let arcGen = null
let colorScale = null
let tooltip = null

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
  svg = null
  arcGroup = null
  arcPaths = null
  tooltip = null
}

// Determines whether an arc is visible in the current zoom level
function arcVisible(d) {
  return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0
}

// Determines whether a label should be visible
function labelVisible(d) {
  return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03
}

function labelTransform(d, radius) {
  const x = (d.x0 + d.x1) / 2 * 180 / Math.PI
  const y = (d.y0 + d.y1) / 2 * radius
  return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`
}

function formatValue(v) {
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`
  return v.toLocaleString()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.data) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 500)
  const radius = size / 6

  // Build hierarchy
  rootNode = d3.hierarchy(props.data)
    .sum(d => d.value || 0)
    .sort((a, b) => b.value - a.value)

  // Partition layout produces x0/x1 (angle 0..1) and y0/y1 (depth)
  const partition = d3.partition().size([2 * Math.PI, rootNode.height + 1])
  partition(rootNode)

  // Store initial positions for zoom transitions
  rootNode.each(d => {
    d.current = { x0: d.x0, x1: d.x1, y0: d.y0, y1: d.y1 }
  })

  currentFocus = rootNode
  breadcrumbs.value = [{ name: props.centerLabel, node: rootNode }]

  // Color scale: top-level children get distinct colors, descendants inherit
  colorScale = d3.scaleOrdinal()
    .domain(rootNode.children ? rootNode.children.map(d => d.data.name) : [])
    .range(props.colorScheme)

  function getColor(d) {
    // Walk up to the top-level ancestor to inherit its color
    let current = d
    while (current.depth > 1) current = current.parent
    return colorScale(current.data.name)
  }

  // Arc generator
  arcGen = d3.arc()
    .startAngle(d => d.x0)
    .endAngle(d => d.x1)
    .padAngle(d => Math.min((d.x1 - d.x0) / 2, 0.005))
    .padRadius(radius * 1.5)
    .innerRadius(d => d.y0 * radius)
    .outerRadius(d => Math.max(d.y0 * radius, d.y1 * radius - 1))

  // SVG
  svg = d3.select(container)
    .append('svg')
    .attr('width', size)
    .attr('height', size)
    .attr('viewBox', `${-size / 2} ${-size / 2} ${size} ${size}`)
    .style('display', 'block')
    .style('margin', '0 auto')
    .style('cursor', 'pointer')

  arcGroup = svg.append('g')

  // Arcs
  arcPaths = arcGroup.selectAll('path')
    .data(rootNode.descendants().slice(1)) // skip root
    .join('path')
    .attr('fill', d => {
      const c = getColor(d)
      return d3.interpolateRgb(c, '#ffffff')((d.depth - 1) * 0.15)
    })
    .attr('fill-opacity', d => arcVisible(d.current) ? (d.children ? 0.7 : 0.5) : 0)
    .attr('pointer-events', d => arcVisible(d.current) ? 'auto' : 'none')
    .attr('d', d => arcGen(d.current))
    .attr('stroke', 'var(--color-surface, #fff)')
    .attr('stroke-width', 0.5)

  // Hover + click handlers
  arcPaths
    .filter(d => d.children)
    .style('cursor', 'pointer')
    .on('click', (event, d) => clicked(d, radius))

  arcPaths
    .on('mouseenter', (event, d) => showTooltip(event, d, container))
    .on('mousemove', (event) => moveTooltip(event, container))
    .on('mouseleave', () => hideTooltip())

  // Labels on arcs
  arcGroup.selectAll('text')
    .data(rootNode.descendants().slice(1))
    .join('text')
    .attr('class', 'arc-label')
    .attr('dy', '0.35em')
    .attr('fill-opacity', d => +labelVisible(d.current))
    .attr('transform', d => labelTransform(d.current, radius))
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text, #050505)')
    .attr('pointer-events', 'none')
    .text(d => d.data.name)

  // Center circle (click to zoom out)
  svg.append('circle')
    .attr('r', radius)
    .attr('fill', 'var(--color-surface, #fff)')
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
    .attr('stroke-width', 1)
    .attr('pointer-events', 'all')
    .style('cursor', 'pointer')
    .on('click', () => {
      if (currentFocus.parent) {
        clicked(currentFocus.parent, radius)
      }
    })

  // Center label
  const centerGroup = svg.append('g').attr('text-anchor', 'middle').attr('pointer-events', 'none')

  centerGroup.append('text')
    .attr('class', 'center-value')
    .attr('dy', '-0.2em')
    .attr('font-size', '18px')
    .attr('font-weight', '700')
    .attr('fill', 'var(--color-text, #050505)')
    .text(formatValue(rootNode.value))

  centerGroup.append('text')
    .attr('class', 'center-label')
    .attr('dy', '1.2em')
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(props.centerLabel)

  // Tooltip element
  tooltip = d3.select(container)
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

  // Entrance animation: arcs grow from center
  arcPaths
    .attr('fill-opacity', 0)
    .transition()
    .duration(600)
    .delay((d, i) => i * 3)
    .ease(d3.easeCubicOut)
    .attr('fill-opacity', d => arcVisible(d.current) ? (d.children ? 0.7 : 0.5) : 0)
}

function clicked(p, radius) {
  currentFocus = p
  emit('segment-click', { name: p.data.name, value: p.value, depth: p.depth })

  // Build breadcrumb trail
  const trail = []
  let ancestor = p
  while (ancestor) {
    trail.unshift({
      name: ancestor.depth === 0 ? props.centerLabel : ancestor.data.name,
      node: ancestor,
    })
    ancestor = ancestor.parent
  }
  breadcrumbs.value = trail

  // Update center text
  svg.select('.center-value').text(formatValue(p.value))
  svg.select('.center-label').text(p.depth === 0 ? props.centerLabel : p.data.name)

  // Compute target positions for all nodes relative to new focus
  rootNode.each(d => {
    d.target = {
      x0: Math.max(0, Math.min(2 * Math.PI, (d.x0 - p.x0) / (p.x1 - p.x0) * 2 * Math.PI)),
      x1: Math.max(0, Math.min(2 * Math.PI, (d.x1 - p.x0) / (p.x1 - p.x0) * 2 * Math.PI)),
      y0: Math.max(0, d.y0 - p.depth),
      y1: Math.max(0, d.y1 - p.depth),
    }
  })

  const t = arcGroup.transition().duration(500).ease(d3.easeCubicInOut)

  arcPaths.transition(t)
    .tween('data', d => {
      const i = d3.interpolate(d.current, d.target)
      return t => { d.current = i(t) }
    })
    .filter(function (d) {
      return +this.getAttribute('fill-opacity') || arcVisible(d.target)
    })
    .attr('fill-opacity', d => arcVisible(d.target) ? (d.children ? 0.7 : 0.5) : 0)
    .attr('pointer-events', d => arcVisible(d.target) ? 'auto' : 'none')
    .attrTween('d', d => () => arcGen(d.current))

  arcGroup.selectAll('.arc-label').transition(t)
    .attr('fill-opacity', d => +labelVisible(d.target))
    .attrTween('transform', d => () => labelTransform(d.current, radius))
}

function showTooltip(event, d, container) {
  if (!tooltip) return
  const pct = d.parent ? ((d.value / d.parent.value) * 100).toFixed(1) : '100'
  tooltip
    .html(`
      <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:2px">${d.data.name}</div>
      <div style="color:var(--color-text-secondary,#555)">${formatValue(d.value)}</div>
      <div style="color:var(--color-text-muted,#888);font-size:11px;margin-top:2px">${pct}% of ${d.parent.data.name || props.centerLabel}</div>
    `)
    .style('opacity', 1)
  moveTooltip(event, container)
}

function moveTooltip(event, container) {
  if (!tooltip) return
  const rect = container.getBoundingClientRect()
  tooltip
    .style('left', `${event.clientX - rect.left + 12}px`)
    .style('top', `${event.clientY - rect.top - 40}px`)
}

function hideTooltip() {
  if (tooltip) tooltip.style('opacity', 0)
}

function navigateTo(crumb) {
  if (!arcGen || !crumb.node) return
  const container = chartRef.value
  if (!container) return
  const size = Math.min(container.clientWidth, 500)
  const radius = size / 6
  clicked(crumb.node, radius)
}

// Reactivity
watch(() => props.data, () => nextTick(renderChart), { deep: true })
watch(() => props.colorScheme, () => nextTick(renderChart))

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

const showBreadcrumbs = computed(() => breadcrumbs.value.length > 1)
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Breadcrumb trail -->
    <div
      v-if="showBreadcrumbs"
      class="flex items-center gap-1 mb-3 text-xs flex-wrap"
    >
      <template v-for="(crumb, i) in breadcrumbs" :key="i">
        <span
          v-if="i > 0"
          class="text-[var(--color-text-muted)]"
        >/</span>
        <button
          class="px-1.5 py-0.5 rounded transition-colors"
          :class="i === breadcrumbs.length - 1
            ? 'font-semibold text-[var(--color-text)] bg-[var(--color-tint)]'
            : 'text-[var(--color-primary)] hover:bg-[var(--color-tint)] cursor-pointer'"
          :disabled="i === breadcrumbs.length - 1"
          @click="navigateTo(crumb)"
        >
          {{ crumb.name }}
        </button>
      </template>
    </div>

    <!-- Chart container -->
    <div ref="chartRef" class="relative w-full" style="min-height: 300px" />

    <!-- Hint -->
    <p class="text-[11px] text-[var(--color-text-muted)] mt-3 text-center">
      Click a segment to zoom in · Click center to zoom out
    </p>
  </div>
</template>
