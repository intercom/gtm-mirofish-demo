<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: {
    type: Object,
    default: null,
  },
  months: {
    type: Array,
    default: () => [
      'Oct 2025', 'Nov 2025', 'Dec 2025',
      'Jan 2026', 'Feb 2026', 'Mar 2026',
    ],
  },
})

const selectedMonth = ref(null)
const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  total: '#2068FF',
  positive: '#009900',
  negative: '#ef4444',
  connector: 'rgba(0, 0, 0, 0.15)',
  text: '#050505',
  textMuted: '#888888',
  grid: 'rgba(0, 0, 0, 0.06)',
}

const DEMO_DATA = {
  'Oct 2025': { startingMrr: 218000, newMrr: 24500, expansionMrr: 11200, contractionMrr: 5800, churnMrr: 9400 },
  'Nov 2025': { startingMrr: 238500, newMrr: 19800, expansionMrr: 14600, contractionMrr: 4200, churnMrr: 7700 },
  'Dec 2025': { startingMrr: 261000, newMrr: 15200, expansionMrr: 9800, contractionMrr: 6100, churnMrr: 11900 },
  'Jan 2026': { startingMrr: 268000, newMrr: 28300, expansionMrr: 16400, contractionMrr: 5500, churnMrr: 8200 },
  'Feb 2026': { startingMrr: 299000, newMrr: 22100, expansionMrr: 12800, contractionMrr: 7300, churnMrr: 9600 },
  'Mar 2026': { startingMrr: 317000, newMrr: 31500, expansionMrr: 18200, contractionMrr: 6400, churnMrr: 10300 },
}

const activeData = computed(() => {
  if (props.data) return props.data
  const month = selectedMonth.value
  return DEMO_DATA[month] || Object.values(DEMO_DATA)[0]
})

const endingMrr = computed(() => {
  const d = activeData.value
  return d.startingMrr + d.newMrr + d.expansionMrr - d.contractionMrr - d.churnMrr
})

const netNewMrr = computed(() => {
  const d = activeData.value
  return d.newMrr + d.expansionMrr - d.contractionMrr - d.churnMrr
})

function formatDollar(value) {
  const abs = Math.abs(value)
  if (abs >= 1000000) return `$${(value / 1000000).toFixed(1)}M`
  if (abs >= 1000) return `$${(value / 1000).toFixed(0)}K`
  return `$${value}`
}

function buildBars() {
  const d = activeData.value
  const ending = endingMrr.value

  return [
    { label: 'Starting\nMRR', value: d.startingMrr, type: 'total', base: 0 },
    { label: 'New', value: d.newMrr, type: 'positive', base: d.startingMrr },
    { label: 'Expansion', value: d.expansionMrr, type: 'positive', base: d.startingMrr + d.newMrr },
    { label: 'Contraction', value: d.contractionMrr, type: 'negative', base: d.startingMrr + d.newMrr + d.expansionMrr - d.contractionMrr },
    { label: 'Churn', value: d.churnMrr, type: 'negative', base: ending },
    { label: 'Ending\nMRR', value: ending, type: 'total', base: 0 },
  ]
}

function barColor(type) {
  if (type === 'total') return COLORS.total
  if (type === 'positive') return COLORS.positive
  return COLORS.negative
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const bars = buildBars()

  const containerWidth = container.clientWidth
  const margin = { top: 24, right: 24, bottom: 64, left: 56 }
  const width = containerWidth - margin.left - margin.right
  const height = 300
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleBand()
    .domain(bars.map(b => b.label))
    .range([0, width])
    .padding(0.35)

  const maxVal = Math.max(...bars.map(b => b.type === 'total' ? b.value : b.base + b.value)) * 1.12
  const y = d3.scaleLinear()
    .domain([0, maxVal])
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
    .attr('fill', COLORS.textMuted)
    .text(d => formatDollar(d))

  // Connector lines between bars
  bars.forEach((bar, i) => {
    if (i === bars.length - 1) return
    const next = bars[i + 1]
    const connectorY = bar.type === 'total'
      ? y(bar.value)
      : bar.type === 'positive'
        ? y(bar.base + bar.value)
        : y(bar.base)
    const x1Pos = x(bar.label) + x.bandwidth()
    const x2Pos = x(next.label)

    g.append('line')
      .attr('x1', x1Pos)
      .attr('x2', x2Pos)
      .attr('y1', connectorY)
      .attr('y2', connectorY)
      .attr('stroke', COLORS.connector)
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3')
  })

  // Bars with animation
  bars.forEach((bar, i) => {
    const barTop = bar.type === 'total'
      ? y(bar.value)
      : bar.type === 'positive'
        ? y(bar.base + bar.value)
        : y(bar.base + bar.value)
    const barHeight = bar.type === 'total'
      ? height - y(bar.value)
      : Math.abs(y(0) - y(bar.value))

    const barG = g.append('g')

    // Animated bar
    barG.append('rect')
      .attr('x', x(bar.label))
      .attr('y', height)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('rx', 3)
      .attr('fill', barColor(bar.type))
      .attr('opacity', 0.85)
      .transition()
      .duration(600)
      .delay(i * 80)
      .ease(d3.easeCubicOut)
      .attr('y', barTop)
      .attr('height', barHeight)

    // Value label on bar
    const displayValue = bar.type === 'total'
      ? formatDollar(bar.value)
      : `${bar.type === 'negative' ? '-' : '+'}${formatDollar(bar.value)}`

    barG.append('text')
      .attr('x', x(bar.label) + x.bandwidth() / 2)
      .attr('y', barTop - 8)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', barColor(bar.type))
      .style('opacity', 0)
      .text(displayValue)
      .transition()
      .duration(300)
      .delay(600 + i * 80)
      .style('opacity', 1)
  })

  // X-axis labels (handle multi-line with \n)
  bars.forEach(bar => {
    const lines = bar.label.split('\n')
    const textEl = g.append('text')
      .attr('x', x(bar.label) + x.bandwidth() / 2)
      .attr('y', height + 20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('fill', '#555')

    lines.forEach((line, j) => {
      textEl.append('tspan')
        .attr('x', x(bar.label) + x.bandwidth() / 2)
        .attr('dy', j === 0 ? 0 : '1.2em')
        .text(line)
    })
  })
}

// Lifecycle
onMounted(() => {
  selectedMonth.value = props.months[props.months.length - 1]

  nextTick(() => renderChart())

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

watch(selectedMonth, () => {
  nextTick(() => renderChart())
})

watch(() => props.data, () => {
  nextTick(() => renderChart())
}, { deep: true })
</script>

<template>
  <div
    class="rounded-lg border p-5"
    :style="{
      background: 'var(--card-bg)',
      borderColor: 'var(--card-border)',
      boxShadow: 'var(--card-shadow)',
    }"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3
          class="text-sm font-semibold"
          :style="{ color: 'var(--color-text)' }"
        >
          MRR Waterfall
        </h3>
        <p
          class="text-xs mt-0.5"
          :style="{ color: 'var(--color-text-muted)' }"
        >
          Monthly recurring revenue bridge
        </p>
      </div>

      <!-- Month selector -->
      <select
        v-model="selectedMonth"
        class="text-xs rounded-lg border px-3 py-1.5 outline-none"
        :style="{
          background: 'var(--input-bg)',
          borderColor: 'var(--input-border)',
          color: 'var(--color-text)',
        }"
      >
        <option v-for="month in months" :key="month" :value="month">
          {{ month }}
        </option>
      </select>
    </div>

    <!-- Net new MRR callout -->
    <div
      class="flex items-center gap-3 rounded-lg px-4 py-2.5 mb-4"
      :style="{
        background: netNewMrr >= 0
          ? 'var(--color-success-light)'
          : 'var(--color-error-light)',
      }"
    >
      <span
        class="text-xs font-medium"
        :style="{ color: 'var(--color-text-secondary)' }"
      >
        Net New MRR
      </span>
      <span
        class="text-sm font-bold"
        :style="{
          color: netNewMrr >= 0
            ? 'var(--color-success)'
            : 'var(--color-error)',
        }"
      >
        {{ netNewMrr >= 0 ? '+' : '' }}{{ formatDollar(netNewMrr) }}
      </span>
    </div>

    <!-- D3 chart container -->
    <div ref="chartRef" class="w-full" />

    <!-- Legend -->
    <div class="flex items-center gap-5 mt-3 pl-1">
      <div class="flex items-center gap-1.5">
        <span
          class="inline-block w-2.5 h-2.5 rounded-sm"
          :style="{ background: COLORS.total, opacity: 0.85 }"
        />
        <span
          class="text-xs"
          :style="{ color: 'var(--color-text-muted)' }"
        >Total</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span
          class="inline-block w-2.5 h-2.5 rounded-sm"
          :style="{ background: COLORS.positive, opacity: 0.85 }"
        />
        <span
          class="text-xs"
          :style="{ color: 'var(--color-text-muted)' }"
        >Growth</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span
          class="inline-block w-2.5 h-2.5 rounded-sm"
          :style="{ background: COLORS.negative, opacity: 0.85 }"
        />
        <span
          class="text-xs"
          :style="{ color: 'var(--color-text-muted)' }"
        >Loss</span>
      </div>
    </div>
  </div>
</template>
