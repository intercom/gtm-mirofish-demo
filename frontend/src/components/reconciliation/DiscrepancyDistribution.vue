<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'
import { reconciliationApi } from '@/api/reconciliation'

const props = defineProps({
  simulationId: { type: String, default: null },
})

const chartRef = ref(null)
const loading = ref(true)
const error = ref(null)
const bins = ref([])
const statistics = ref(null)

let resizeObserver = null
let resizeTimer = null

const COLORS = {
  timing: '#2068FF',
  rounding: '#ff5600',
  missing: '#AA00FF',
  genuine: '#009900',
  text: '#050505',
  grid: 'rgba(0,0,0,0.06)',
  muted: '#888',
  avgLine: '#d4220a',
}

const TYPE_LABELS = {
  timing: 'Timing',
  rounding: 'Rounding',
  missing: 'Missing',
  genuine: 'Genuine',
}

const TYPES = ['timing', 'rounding', 'missing', 'genuine']

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await reconciliationApi.getDiscrepancyDistribution({
      simulation_id: props.simulationId,
    })
    const data = res.data?.data || res.data
    bins.value = data.bins || []
    statistics.value = data.statistics || null
  } catch (e) {
    error.value = e.message || 'Failed to load discrepancy data'
  } finally {
    loading.value = false
  }
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !bins.value.length) return

  const data = bins.value
  const stats = statistics.value

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 48, left: 52 }
  const width = containerWidth - margin.left - margin.right
  const height = 280
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  // Title
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Discrepancy Distribution')

  // Subtitle
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Account count by discrepancy amount, stacked by type')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // X scale — one band per bin range
  const x = d3.scaleBand()
    .domain(data.map(d => d.range))
    .range([0, width])
    .paddingInner(0.2)
    .paddingOuter(0.1)

  // Stack the data
  const stackedData = d3.stack()
    .keys(TYPES)
    .value((d, key) => d.by_type[key] || 0)(data)

  const maxY = d3.max(data, d => d.total) || 1
  const yMax = Math.ceil(maxY / 10) * 10 || 10

  const y = d3.scaleLinear()
    .domain([0, yMax])
    .range([height, 0])

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', COLORS.grid)
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => d)

  // Y-axis title
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -height / 2)
    .attr('y', -42)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text('Accounts')

  // Stacked bars
  const typeGroups = g.selectAll('.type-group')
    .data(stackedData)
    .join('g')
    .attr('class', 'type-group')
    .attr('fill', d => COLORS[d.key])
    .attr('opacity', 0.85)

  // Tooltip container
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('background', 'rgba(5,5,5,0.92)')
    .style('color', '#fff')
    .style('padding', '8px 12px')
    .style('border-radius', '6px')
    .style('font-size', '12px')
    .style('line-height', '1.5')
    .style('opacity', 0)
    .style('z-index', 10)
    .style('white-space', 'nowrap')

  typeGroups.selectAll('rect')
    .data(d => d.map(pt => ({ ...pt, key: d.key })))
    .join('rect')
    .attr('x', d => x(d.data.range))
    .attr('y', height)
    .attr('width', x.bandwidth())
    .attr('height', 0)
    .attr('rx', 2)
    .on('mouseenter', function (event, d) {
      const bin = d.data
      let html = `<strong>${bin.range}</strong><br/>`
      html += `Total: ${bin.total}<br/>`
      for (const t of TYPES) {
        const count = bin.by_type[t] || 0
        const dot = `<span style="color:${COLORS[t]}">●</span>`
        html += `${dot} ${TYPE_LABELS[t]}: ${count}<br/>`
      }
      tooltip.html(html).style('opacity', 1)
    })
    .on('mousemove', function (event) {
      const [mx, my] = d3.pointer(event, container)
      tooltip
        .style('left', `${mx + 12}px`)
        .style('top', `${my - 12}px`)
    })
    .on('mouseleave', function () {
      tooltip.style('opacity', 0)
    })
    .transition()
    .duration(600)
    .delay((d, i) => i * 60)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d[1]))
    .attr('height', d => y(d[0]) - y(d[1]))

  // X-axis labels
  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', d => x(d.range) + x.bandwidth() / 2)
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => d.range)

  // X-axis title
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height + 38)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text('Discrepancy Amount')

  // Average reference line
  if (stats?.mean != null) {
    const meanBinIndex = data.findIndex(d => {
      if (d.max === null) return stats.mean >= d.min
      return stats.mean >= d.min && stats.mean < d.max
    })
    if (meanBinIndex >= 0) {
      const bin = data[meanBinIndex]
      const binX = x(bin.range)
      const binW = x.bandwidth()
      const rangeSize = (bin.max || stats.mean * 2) - bin.min
      const fraction = rangeSize > 0 ? (stats.mean - bin.min) / rangeSize : 0.5
      const lineX = binX + fraction * binW

      g.append('line')
        .attr('x1', lineX)
        .attr('x2', lineX)
        .attr('y1', 0)
        .attr('y2', height)
        .attr('stroke', COLORS.avgLine)
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '6,4')
        .style('opacity', 0)
        .transition()
        .duration(400)
        .delay(600)
        .style('opacity', 0.8)

      g.append('text')
        .attr('x', lineX)
        .attr('y', -6)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', COLORS.avgLine)
        .style('opacity', 0)
        .text(`Avg $${stats.mean.toFixed(0)}`)
        .transition()
        .duration(300)
        .delay(700)
        .style('opacity', 1)
    }
  }

  // Legend
  const legendX = containerWidth - margin.right - 280
  const legend = svg.append('g')
    .attr('transform', `translate(${legendX}, 14)`)

  TYPES.forEach((type, i) => {
    const offset = i * 70
    legend.append('rect')
      .attr('x', offset)
      .attr('y', 0)
      .attr('width', 10)
      .attr('height', 10)
      .attr('rx', 2)
      .attr('fill', COLORS[type])
      .attr('opacity', 0.85)

    legend.append('text')
      .attr('x', offset + 14)
      .attr('y', 9)
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(TYPE_LABELS[type])
  })
}

watch(() => props.simulationId, () => {
  fetchData().then(() => nextTick(renderChart))
})

onMounted(async () => {
  await fetchData()
  nextTick(renderChart)

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderChart(), 200)
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
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16 text-sm text-[#888]">
      Loading discrepancy data…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center py-16 text-sm text-[#d4220a]">
      {{ error }}
    </div>

    <!-- Chart + Stats -->
    <template v-else>
      <div ref="chartRef" class="w-full relative" />

      <!-- Summary statistics -->
      <div
        v-if="statistics"
        class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t border-black/5"
      >
        <div v-for="stat in [
          { label: 'Mean', value: `$${statistics.mean.toFixed(2)}` },
          { label: 'Median', value: `$${statistics.median.toFixed(2)}` },
          { label: 'Max', value: `$${statistics.max.toLocaleString()}` },
          { label: 'Std Dev', value: `$${statistics.stddev.toFixed(2)}` },
        ]" :key="stat.label" class="text-center">
          <div class="text-[10px] uppercase tracking-wider text-[#888]">{{ stat.label }}</div>
          <div class="text-base font-semibold text-[#050505] mt-0.5">{{ stat.value }}</div>
        </div>
      </div>
    </template>
  </div>
</template>
