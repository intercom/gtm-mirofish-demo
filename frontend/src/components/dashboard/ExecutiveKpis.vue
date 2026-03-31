<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useCountUp } from '../../composables/useCountUp'

const props = defineProps({
  data: { type: Array, default: null },
})

const DEMO_KPIS = [
  {
    key: 'arr',
    label: 'Total ARR',
    value: 2200000,
    format: 'currency-compact',
    trend: 8.3,
    sparkline: [1.6, 1.72, 1.81, 1.93, 2.05, 2.2],
  },
  {
    key: 'mrr-growth',
    label: 'MRR Growth',
    value: 4.2,
    format: 'percent-signed',
    trend: 1.1,
    sparkline: [2.8, 3.1, 3.5, 3.8, 3.9, 4.2],
  },
  {
    key: 'pipeline',
    label: 'Pipeline Value',
    value: 3100000,
    format: 'currency-compact',
    trend: 12.5,
    sparkline: [2.1, 2.3, 2.5, 2.7, 2.9, 3.1],
  },
  {
    key: 'win-rate',
    label: 'Win Rate',
    value: 35,
    format: 'percent',
    trend: 3.2,
    sparkline: [28, 30, 31, 33, 34, 35],
  },
  {
    key: 'nrr',
    label: 'Net Retention',
    value: 112,
    format: 'percent',
    trend: 2.0,
    sparkline: [106, 107, 109, 110, 111, 112],
  },
  {
    key: 'deal-size',
    label: 'Avg Deal Size',
    value: 48000,
    format: 'currency-compact',
    trend: -2.4,
    sparkline: [52, 51, 50, 49, 48, 48],
  },
  {
    key: 'cycle',
    label: 'Sales Cycle',
    value: 45,
    format: 'days',
    trend: -5.1,
    sparkline: [52, 50, 49, 47, 46, 45],
  },
  {
    key: 'customers',
    label: 'Active Customers',
    value: 500,
    format: 'number',
    trend: 6.8,
    sparkline: [420, 440, 455, 470, 485, 500],
  },
]

const kpis = computed(() => props.data ?? DEMO_KPIS)

const sparkRefs = ref([])
let resizeObserver = null

function formatValue(val, fmt) {
  switch (fmt) {
    case 'currency-compact':
      if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`
      if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`
      return `$${val}`
    case 'percent':
      return `${val}%`
    case 'percent-signed':
      return `${val > 0 ? '+' : ''}${val}%`
    case 'days':
      return `${val} days`
    case 'number':
      return val.toLocaleString()
    default:
      return String(val)
  }
}

function trendColor(trend, key) {
  // For sales cycle & deal size decrease, down = good (green)
  const invertedKeys = ['cycle']
  const isGood = invertedKeys.includes(key) ? trend < 0 : trend > 0
  return isGood ? 'var(--color-success)' : 'var(--color-error)'
}

function trendBg(trend, key) {
  const invertedKeys = ['cycle']
  const isGood = invertedKeys.includes(key) ? trend < 0 : trend > 0
  return isGood ? 'var(--color-success-light)' : 'var(--color-error-light)'
}

function drawSparkline(el, data, trend, key) {
  if (!el) return
  d3.select(el).selectAll('*').remove()

  const width = el.clientWidth || 80
  const height = 28

  const svg = d3.select(el)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const x = d3.scaleLinear()
    .domain([0, data.length - 1])
    .range([2, width - 2])

  const y = d3.scaleLinear()
    .domain([d3.min(data) * 0.95, d3.max(data) * 1.05])
    .range([height - 2, 2])

  const line = d3.line()
    .x((_, i) => x(i))
    .y(d => y(d))
    .curve(d3.curveMonotoneX)

  const invertedKeys = ['cycle']
  const isGood = invertedKeys.includes(key) ? trend < 0 : trend > 0
  const color = isGood ? '#009900' : '#ef4444'

  // Fill area
  const area = d3.area()
    .x((_, i) => x(i))
    .y0(height)
    .y1(d => y(d))
    .curve(d3.curveMonotoneX)

  svg.append('path')
    .datum(data)
    .attr('d', area)
    .attr('fill', color)
    .attr('opacity', 0.08)

  // Line
  svg.append('path')
    .datum(data)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', color)
    .attr('stroke-width', 1.5)
    .attr('stroke-linecap', 'round')

  // End dot
  svg.append('circle')
    .attr('cx', x(data.length - 1))
    .attr('cy', y(data[data.length - 1]))
    .attr('r', 2.5)
    .attr('fill', color)
}

function renderAllSparklines() {
  sparkRefs.value.forEach((el, i) => {
    const kpi = kpis.value[i]
    if (el && kpi) {
      drawSparkline(el, kpi.sparkline, kpi.trend, kpi.key)
    }
  })
}

onMounted(() => {
  nextTick(() => renderAllSparklines())

  resizeObserver = new ResizeObserver(() => {
    renderAllSparklines()
  })
  const firstEl = sparkRefs.value[0]
  if (firstEl?.parentElement) {
    resizeObserver.observe(firstEl.parentElement)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<template>
  <div class="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-8 gap-3">
    <div
      v-for="(kpi, i) in kpis"
      :key="kpi.key"
      class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 flex flex-col justify-between min-h-[120px] transition-shadow hover:shadow-md"
    >
      <!-- Label -->
      <div class="text-[11px] font-medium text-[var(--color-text-muted)] leading-tight mb-1">
        {{ kpi.label }}
      </div>

      <!-- Value + trend -->
      <div class="flex items-end justify-between gap-1 mb-2">
        <span class="text-xl font-semibold text-[var(--color-text)] leading-none tracking-tight">
          {{ formatValue(kpi.value, kpi.format) }}
        </span>
        <span
          class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full leading-none shrink-0"
          :style="{
            color: trendColor(kpi.trend, kpi.key),
            backgroundColor: trendBg(kpi.trend, kpi.key),
          }"
        >
          <template v-if="kpi.trend > 0">&#x25B2;</template>
          <template v-else>&#x25BC;</template>
          {{ Math.abs(kpi.trend) }}%
        </span>
      </div>

      <!-- Sparkline -->
      <div
        :ref="el => { if (el) sparkRefs[i] = el }"
        class="w-full"
        style="height: 28px"
      />
    </div>
  </div>
</template>
