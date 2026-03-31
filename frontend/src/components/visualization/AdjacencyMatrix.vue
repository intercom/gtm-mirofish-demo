<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { simulationApi } from '@/api/simulation'
import { useTheme } from '@/composables/useTheme'

const props = defineProps({
  simulationId: { type: String, required: true },
})

const emit = defineEmits(['cell-click'])

const { isDark } = useTheme()

const containerRef = ref(null)
const svgRef = ref(null)
const tooltipRef = ref(null)

const loading = ref(true)
const error = ref(null)
const sortMode = ref('alphabetical')
const matrixData = ref(null)

let resizeObserver = null
let resizeTimer = null

const SORT_OPTIONS = [
  { value: 'alphabetical', label: 'A-Z' },
  { value: 'cluster', label: 'By Cluster' },
  { value: 'influence', label: 'By Influence' },
]

const CLUSTER_COLORS = ['#2068FF', '#ff5600', '#AA00FF']

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const { data } = await simulationApi.getAdjacencyMatrix(props.simulationId)
    matrixData.value = data.data || data
  } catch (e) {
    error.value = e.message || 'Failed to load adjacency matrix'
  } finally {
    loading.value = false
  }
}

const sortedIndices = computed(() => {
  if (!matrixData.value) return []
  return matrixData.value.sort_orders[sortMode.value] || []
})

function render() {
  if (!svgRef.value || !containerRef.value || !matrixData.value) return

  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  const { agents, values, row_totals, col_totals, clusters } = matrixData.value
  const order = sortedIndices.value
  const n = agents.length

  const dark = isDark.value
  const textColor = dark ? '#e0e0e0' : '#1a1a1a'
  const mutedColor = dark ? '#666' : '#888'
  const bgColor = dark ? '#1a1a2e' : '#ffffff'
  const gridColor = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'

  const containerWidth = containerRef.value.clientWidth
  const labelWidth = 110
  const barWidth = 40
  const barGap = 8
  const topBarHeight = 40
  const margin = { top: 48 + topBarHeight, right: barWidth + barGap + 8, bottom: 8, left: labelWidth }

  const available = containerWidth - margin.left - margin.right
  const cellSize = Math.max(16, Math.min(36, Math.floor(available / n)))
  const gridSize = cellSize * n
  const totalWidth = margin.left + gridSize + margin.right
  const totalHeight = margin.top + gridSize + margin.bottom + 80

  svg
    .attr('width', totalWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${totalWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Color scale for off-diagonal cells
  const colorScale = dark
    ? d3.scaleSequential(d3.interpolateBlues).domain([0, 1])
    : d3.scaleSequential(t => d3.interpolateBlues(t * 0.85 + 0.05)).domain([0, 1])

  // --- Column totals bar chart (top) ---
  const maxColTotal = d3.max(col_totals) || 1
  const colBarScale = d3.scaleLinear().domain([0, maxColTotal]).range([0, topBarHeight - 4])
  const colBarG = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top - topBarHeight - 4})`)

  order.forEach((ci, x) => {
    colBarG.append('rect')
      .attr('x', x * cellSize + 1)
      .attr('y', topBarHeight - colBarScale(col_totals[ci]))
      .attr('width', cellSize - 2)
      .attr('height', colBarScale(col_totals[ci]))
      .attr('rx', 2)
      .attr('fill', '#2068FF')
      .attr('opacity', 0.5)
  })

  // --- Row totals bar chart (right) ---
  const maxRowTotal = d3.max(row_totals) || 1
  const rowBarScale = d3.scaleLinear().domain([0, maxRowTotal]).range([0, barWidth])
  const rowBarG = g.append('g')
    .attr('transform', `translate(${gridSize + barGap},0)`)

  order.forEach((ri, y) => {
    rowBarG.append('rect')
      .attr('x', 0)
      .attr('y', y * cellSize + 1)
      .attr('width', rowBarScale(row_totals[ri]))
      .attr('height', cellSize - 2)
      .attr('rx', 2)
      .attr('fill', '#2068FF')
      .attr('opacity', 0.5)
  })

  // --- Grid lines ---
  for (let i = 0; i <= n; i++) {
    g.append('line')
      .attr('x1', i * cellSize).attr('x2', i * cellSize)
      .attr('y1', 0).attr('y2', gridSize)
      .attr('stroke', gridColor)
    g.append('line')
      .attr('x1', 0).attr('x2', gridSize)
      .attr('y1', i * cellSize).attr('y2', i * cellSize)
      .attr('stroke', gridColor)
  }

  // --- Heatmap cells ---
  const tooltip = d3.select(tooltipRef.value)

  order.forEach((ri, y) => {
    order.forEach((ci, x) => {
      const val = values[ri][ci]
      const isDiagonal = ri === ci

      const cell = g.append('rect')
        .attr('x', x * cellSize)
        .attr('y', y * cellSize)
        .attr('width', cellSize)
        .attr('height', cellSize)
        .attr('fill', isDiagonal ? '#ff5600' : (val === 0 ? bgColor : colorScale(val)))
        .attr('opacity', isDiagonal ? (0.3 + val * 0.7) : 1)
        .style('cursor', 'pointer')

      cell
        .on('mouseenter', (event) => {
          cell.attr('stroke', textColor).attr('stroke-width', 2)
          const isDiag = ri === ci
          const label = isDiag
            ? `${agents[ri]} — self-activity`
            : `${agents[ri]} ↔ ${agents[ci]}`
          tooltip
            .style('display', 'block')
            .style('left', `${event.offsetX + 12}px`)
            .style('top', `${event.offsetY - 8}px`)
            .html(`
              <div style="font-weight:600;margin-bottom:2px">${label}</div>
              <div>Intensity: ${(val * 100).toFixed(1)}%</div>
              ${!isDiag ? `<div style="color:${mutedColor};font-size:11px;margin-top:2px">Click for details</div>` : ''}
            `)
        })
        .on('mouseleave', () => {
          cell.attr('stroke', 'none')
          tooltip.style('display', 'none')
        })
        .on('click', () => {
          if (ri !== ci) {
            emit('cell-click', {
              agentA: agents[ri],
              agentB: agents[ci],
              intensity: val,
            })
          }
        })
    })
  })

  // --- Row labels (left) ---
  order.forEach((ri, y) => {
    const truncated = agents[ri].length > 15 ? agents[ri].slice(0, 14) + '…' : agents[ri]
    g.append('text')
      .attr('x', -6)
      .attr('y', y * cellSize + cellSize / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-size', '11px')
      .attr('fill', textColor)
      .text(truncated)

    // Cluster dot
    g.append('circle')
      .attr('cx', -labelWidth + 8)
      .attr('cy', y * cellSize + cellSize / 2)
      .attr('r', 3)
      .attr('fill', CLUSTER_COLORS[clusters[ri]] || '#888')
  })

  // --- Column labels (bottom, rotated) ---
  order.forEach((ci, x) => {
    const truncated = agents[ci].length > 15 ? agents[ci].slice(0, 14) + '…' : agents[ci]
    g.append('text')
      .attr('x', 0)
      .attr('y', 0)
      .attr('transform', `translate(${x * cellSize + cellSize / 2},${gridSize + 6}) rotate(45)`)
      .attr('text-anchor', 'start')
      .attr('font-size', '11px')
      .attr('fill', textColor)
      .text(truncated)
  })

  // --- Color legend ---
  const legendWidth = 120
  const legendHeight = 10
  const legendG = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top - topBarHeight - 32})`)

  const legendScale = d3.scaleLinear().domain([0, 1]).range([0, legendWidth])
  const legendData = d3.range(0, 1.01, 0.02)

  legendG.selectAll('.legend-cell')
    .data(legendData)
    .join('rect')
    .attr('x', d => legendScale(d))
    .attr('y', 0)
    .attr('width', legendWidth / legendData.length + 1)
    .attr('height', legendHeight)
    .attr('fill', d => colorScale(d))

  legendG.append('text')
    .attr('x', 0).attr('y', -3)
    .attr('font-size', '9px').attr('fill', mutedColor)
    .text('None')
  legendG.append('text')
    .attr('x', legendWidth).attr('y', -3)
    .attr('text-anchor', 'end')
    .attr('font-size', '9px').attr('fill', mutedColor)
    .text('Many')

  // Diagonal legend swatch
  legendG.append('rect')
    .attr('x', legendWidth + 16).attr('y', 0)
    .attr('width', legendHeight).attr('height', legendHeight)
    .attr('fill', '#ff5600').attr('opacity', 0.7).attr('rx', 2)
  legendG.append('text')
    .attr('x', legendWidth + 16 + legendHeight + 4).attr('y', legendHeight - 1)
    .attr('font-size', '9px').attr('fill', mutedColor)
    .text('Self-activity')
}

function handleResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => render(), 200)
}

watch(sortMode, () => nextTick(render))
watch(isDark, () => nextTick(render))
watch(matrixData, () => nextTick(render))

onMounted(async () => {
  await fetchData()

  resizeObserver = new ResizeObserver(handleResize)
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="rounded-lg border p-4 md:p-6 bg-[var(--card-bg)] border-[var(--card-border)]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Agent Interaction Matrix</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">All agent-to-agent interaction intensities</p>
      </div>
      <div class="flex items-center gap-1">
        <span class="text-xs text-[var(--color-text-muted)] mr-1">Sort:</span>
        <button
          v-for="opt in SORT_OPTIONS"
          :key="opt.value"
          class="px-2 py-1 text-xs rounded transition-colors"
          :class="sortMode === opt.value
            ? 'bg-[var(--color-primary)] text-white'
            : 'bg-[var(--color-primary-light)] text-[var(--color-text-secondary)] hover:bg-[var(--color-primary-tint-hover)]'"
          @click="sortMode = opt.value"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="w-6 h-6 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-12 text-sm text-[var(--color-text-muted)]">
      {{ error }}
    </div>

    <!-- Matrix -->
    <div v-else ref="containerRef" class="relative w-full overflow-x-auto">
      <svg ref="svgRef" class="block" />
      <div
        ref="tooltipRef"
        class="absolute pointer-events-none px-3 py-2 rounded-md text-xs shadow-lg z-10
               bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)]"
        style="display: none"
      />
    </div>
  </div>
</template>
