<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'
import { revenueApi } from '../../api/revenue'

const chartRef = ref(null)
const loading = ref(true)
const error = ref(null)
const cohortData = ref(null)
const selectedCohort = ref(null)

let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  navy: '#050505',
  orange: '#ff5600',
  text: '#1a1a1a',
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await revenueApi.getCohortRetention()
    cohortData.value = res.data
  } catch (e) {
    error.value = e.message || 'Failed to load cohort data'
  } finally {
    loading.value = false
  }
}

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderHeatmap() {
  clearChart()
  const data = cohortData.value
  if (!data || !chartRef.value) return

  const container = chartRef.value
  const { cohorts, months, values, row_averages, column_averages } = data

  const rows = cohorts.length
  const cols = months.length

  const cellSize = 52
  const labelLeft = 48
  const labelTop = 44
  const avgColWidth = 60
  const avgRowHeight = 32
  const totalWidth = labelLeft + cols * cellSize + avgColWidth
  const totalHeight = labelTop + rows * cellSize + avgRowHeight

  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${totalWidth} ${totalHeight}`)
    .attr('preserveAspectRatio', 'xMinYMin meet')
    .style('font-family', 'system-ui, -apple-system, sans-serif')

  // Title
  svg.append('text')
    .attr('x', labelLeft)
    .attr('y', 16)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Revenue Retention by Cohort')

  // Subtitle
  svg.append('text')
    .attr('x', labelLeft)
    .attr('y', 32)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('% of initial MRR retained, by signup month')

  // Color scale: red (<80%) → white (90%) → green (>100%)
  const colorScale = d3.scaleLinear()
    .domain([60, 80, 95, 100, 110])
    .range(['#dc2626', '#fca5a5', '#f5f5f5', '#bbf7d0', '#16a34a'])
    .clamp(true)

  // Column headers (M0, M1, ...)
  svg.selectAll('.col-header')
    .data(months)
    .join('text')
    .attr('x', (_, i) => labelLeft + i * cellSize + cellSize / 2)
    .attr('y', labelTop - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '500')
    .attr('fill', '#666')
    .text(d => d)

  // "Avg" column header
  svg.append('text')
    .attr('x', labelLeft + cols * cellSize + avgColWidth / 2)
    .attr('y', labelTop - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', '#555')
    .text('Avg')

  // Row headers (Jan, Feb, ...)
  svg.selectAll('.row-header')
    .data(cohorts)
    .join('text')
    .attr('x', labelLeft - 8)
    .attr('y', (_, i) => labelTop + i * cellSize + cellSize / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('font-weight', '500')
    .attr('fill', '#555')
    .text(d => d)

  // Heatmap cells
  const cellGroup = svg.append('g')
    .attr('transform', `translate(${labelLeft}, ${labelTop})`)

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const val = values[row][col]
      if (val === null) continue

      const g = cellGroup.append('g')
        .attr('transform', `translate(${col * cellSize}, ${row * cellSize})`)
        .style('cursor', 'pointer')

      // Cell background
      g.append('rect')
        .attr('width', cellSize - 2)
        .attr('height', cellSize - 2)
        .attr('x', 1)
        .attr('y', 1)
        .attr('rx', 4)
        .attr('fill', colorScale(val))
        .attr('stroke', 'rgba(0,0,0,0.06)')
        .attr('stroke-width', 0.5)
        .style('opacity', 0)
        .transition()
        .duration(400)
        .delay(row * 30 + col * 20)
        .style('opacity', 1)

      // Cell text
      const textColor = val < 70 || val > 108 ? '#fff' : COLORS.text
      g.append('text')
        .attr('x', cellSize / 2)
        .attr('y', cellSize / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'middle')
        .attr('font-size', col === 0 ? '11px' : '10px')
        .attr('font-weight', col === 0 ? '600' : '400')
        .attr('fill', textColor)
        .style('opacity', 0)
        .text(`${val}%`)
        .transition()
        .duration(300)
        .delay(row * 30 + col * 20 + 200)
        .style('opacity', 1)

      // Click handler for cohort details
      g.on('click', () => {
        selectedCohort.value = {
          cohort: cohorts[row],
          month: months[col],
          retention: val,
          rowData: values[row],
        }
      })

      // Hover effect
      g.on('mouseenter', function () {
        d3.select(this).select('rect')
          .attr('stroke', COLORS.primary)
          .attr('stroke-width', 2)
      })
      g.on('mouseleave', function () {
        d3.select(this).select('rect')
          .attr('stroke', 'rgba(0,0,0,0.06)')
          .attr('stroke-width', 0.5)
      })
    }
  }

  // Row averages (right column)
  const avgGroup = svg.append('g')
    .attr('transform', `translate(${labelLeft + cols * cellSize}, ${labelTop})`)

  row_averages.forEach((avg, i) => {
    if (avg === null) return
    const g = avgGroup.append('g')
      .attr('transform', `translate(0, ${i * cellSize})`)

    g.append('rect')
      .attr('width', avgColWidth - 4)
      .attr('height', cellSize - 2)
      .attr('x', 2)
      .attr('y', 1)
      .attr('rx', 4)
      .attr('fill', '#f0f4ff')
      .attr('stroke', 'rgba(32,104,255,0.15)')
      .attr('stroke-width', 0.5)

    g.append('text')
      .attr('x', avgColWidth / 2)
      .attr('y', cellSize / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.primary)
      .text(`${avg}%`)
  })

  // Column averages (bottom row)
  const colAvgGroup = svg.append('g')
    .attr('transform', `translate(${labelLeft}, ${labelTop + rows * cellSize})`)

  // "Avg" row label
  svg.append('text')
    .attr('x', labelLeft - 8)
    .attr('y', labelTop + rows * cellSize + avgRowHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', '#555')
    .text('Avg')

  column_averages.forEach((avg, i) => {
    if (avg === null) return
    const g = colAvgGroup.append('g')
      .attr('transform', `translate(${i * cellSize}, 4)`)

    g.append('rect')
      .attr('width', cellSize - 2)
      .attr('height', avgRowHeight - 6)
      .attr('x', 1)
      .attr('rx', 4)
      .attr('fill', '#f0f4ff')
      .attr('stroke', 'rgba(32,104,255,0.15)')
      .attr('stroke-width', 0.5)

    g.append('text')
      .attr('x', cellSize / 2)
      .attr('y', (avgRowHeight - 6) / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.primary)
      .text(`${avg}%`)
  })

  // Color legend
  const legendWidth = 200
  const legendHeight = 10
  const legendX = labelLeft + cols * cellSize - legendWidth
  const legendY = labelTop + rows * cellSize + avgRowHeight + 12

  const defs = svg.append('defs')
  const gradient = defs.append('linearGradient')
    .attr('id', 'retention-gradient')

  const stops = [
    { offset: '0%', color: '#dc2626' },
    { offset: '30%', color: '#fca5a5' },
    { offset: '50%', color: '#f5f5f5' },
    { offset: '70%', color: '#bbf7d0' },
    { offset: '100%', color: '#16a34a' },
  ]
  stops.forEach(s => {
    gradient.append('stop').attr('offset', s.offset).attr('stop-color', s.color)
  })

  svg.append('rect')
    .attr('x', legendX)
    .attr('y', legendY)
    .attr('width', legendWidth)
    .attr('height', legendHeight)
    .attr('rx', 3)
    .attr('fill', 'url(#retention-gradient)')

  svg.append('text')
    .attr('x', legendX)
    .attr('y', legendY + legendHeight + 12)
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text('60%')

  svg.append('text')
    .attr('x', legendX + legendWidth / 2)
    .attr('y', legendY + legendHeight + 12)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text('90%')

  svg.append('text')
    .attr('x', legendX + legendWidth)
    .attr('y', legendY + legendHeight + 12)
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .text('110%+')
}

function dismissDetail() {
  selectedCohort.value = null
}

watch(cohortData, () => {
  if (cohortData.value) nextTick(() => renderHeatmap())
})

onMounted(async () => {
  await fetchData()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (cohortData.value) renderHeatmap()
    }, 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="w-6 h-6 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin" />
      <span class="ml-3 text-sm text-gray-500">Loading cohort data…</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-sm text-red-600">{{ error }}</p>
      <button
        class="mt-3 px-4 py-1.5 text-sm bg-[#2068FF] text-white rounded-md hover:bg-[#1a5ae0] transition-colors"
        @click="fetchData"
      >
        Retry
      </button>
    </div>

    <!-- Chart -->
    <div v-else ref="chartRef" class="w-full overflow-x-auto" />

    <!-- Cohort detail panel -->
    <div
      v-if="selectedCohort"
      class="mt-4 p-4 bg-gray-50 border border-black/10 rounded-lg"
    >
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-sm font-semibold text-[#1a1a1a]">
          {{ selectedCohort.cohort }} Cohort — {{ selectedCohort.month }}
        </h4>
        <button
          class="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          @click="dismissDetail"
        >
          Dismiss
        </button>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="text-center">
          <div class="text-lg font-bold text-[#1a1a1a]">{{ selectedCohort.retention }}%</div>
          <div class="text-xs text-gray-500">Retention</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-bold" :class="selectedCohort.retention >= 100 ? 'text-green-600' : 'text-red-600'">
            {{ selectedCohort.retention >= 100 ? '+' : '' }}{{ (selectedCohort.retention - 100).toFixed(1) }}%
          </div>
          <div class="text-xs text-gray-500">Net Change</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-bold text-[#1a1a1a]">
            {{ selectedCohort.rowData.filter(v => v !== null).length }}
          </div>
          <div class="text-xs text-gray-500">Months Active</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-bold text-[#2068FF]">
            {{ selectedCohort.rowData.filter(v => v !== null).at(-1) }}%
          </div>
          <div class="text-xs text-gray-500">Latest Retention</div>
        </div>
      </div>
    </div>
  </div>
</template>
