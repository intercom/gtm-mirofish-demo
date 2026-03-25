<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, default: () => [] },
  colorScheme: { type: String, default: 'blue' },
  monthsToShow: { type: Number, default: 12 },
  tooltipFormatter: { type: Function, default: null },
})

const emit = defineEmits(['date-click'])

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLOR_SCHEMES = {
  blue: { empty: 'rgba(32, 104, 255, 0.04)', low: 'rgba(32, 104, 255, 0.15)', high: '#2068FF' },
  green: { empty: 'rgba(0, 153, 0, 0.04)', low: 'rgba(0, 153, 0, 0.15)', high: '#009900' },
  orange: { empty: 'rgba(255, 86, 0, 0.04)', low: 'rgba(255, 86, 0, 0.15)', high: '#ff5600' },
}

const dateRange = computed(() => {
  const end = d3.timeDay.ceil(new Date())
  const start = d3.timeMonth.offset(d3.timeMonth.floor(end), -props.monthsToShow)
  return { start, end }
})

const valueMap = computed(() => {
  const map = new Map()
  for (const d of props.data) {
    const key = d3.timeFormat('%Y-%m-%d')(new Date(d.date))
    map.set(key, (map.get(key) || 0) + d.value)
  }
  return map
})

const maxValue = computed(() => {
  if (!valueMap.value.size) return 1
  return Math.max(1, d3.max(Array.from(valueMap.value.values())))
})

const legendColors = computed(() => {
  const scheme = COLOR_SCHEMES[props.colorScheme] || COLOR_SCHEMES.blue
  const interp = t => {
    if (t === 0) return scheme.empty
    return d3.interpolateRgb(scheme.low, scheme.high)(Math.pow(t, 0.6))
  }
  return [0, 0.25, 0.5, 0.75, 1].map(interp)
})

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const { start, end } = dateRange.value
  const scheme = COLOR_SCHEMES[props.colorScheme] || COLOR_SCHEMES.blue
  const cellSize = 13
  const cellGap = 3
  const step = cellSize + cellGap
  const dayLabelWidth = 28
  const monthLabelHeight = 18
  const margin = { top: monthLabelHeight + 4, right: 8, bottom: 4, left: dayLabelWidth }

  const weeks = d3.timeWeeks(d3.timeWeek.floor(start), end)
  const svgWidth = margin.left + weeks.length * step + margin.right
  const svgHeight = margin.top + 7 * step + margin.bottom

  const colorScale = d3.scaleSequential()
    .domain([0, maxValue.value])
    .interpolator(t => {
      if (t === 0) return scheme.empty
      return d3.interpolateRgb(scheme.low, scheme.high)(Math.pow(t, 0.6))
    })

  const svg = d3.select(container)
    .append('svg')
    .attr('width', svgWidth)
    .attr('height', svgHeight)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Day-of-week labels
  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const labelIndices = [1, 3, 5]
  g.selectAll('.day-label')
    .data(labelIndices)
    .join('text')
    .attr('x', -6)
    .attr('y', d => d * step + cellSize / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => dayLabels[d])

  // Month labels
  const months = d3.timeMonths(d3.timeMonth.ceil(start), end)
  g.selectAll('.month-label')
    .data(months)
    .join('text')
    .attr('x', d => {
      const weekIndex = d3.timeWeek.count(d3.timeWeek.floor(start), d)
      return weekIndex * step
    })
    .attr('y', -8)
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => d3.timeFormat('%b')(d))

  // Day cells
  const days = d3.timeDays(start, end)
  const fmt = d3.timeFormat('%Y-%m-%d')
  const weekFloor = d3.timeWeek.floor(start)

  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '6px 10px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('white-space', 'nowrap')

  g.selectAll('.day')
    .data(days)
    .join('rect')
    .attr('x', d => d3.timeWeek.count(weekFloor, d) * step)
    .attr('y', d => d.getDay() * step)
    .attr('width', cellSize)
    .attr('height', cellSize)
    .attr('rx', 2)
    .attr('fill', d => {
      const val = valueMap.value.get(fmt(d)) || 0
      return colorScale(val)
    })
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.06))')
    .attr('stroke-width', 0.5)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const key = fmt(d)
      const val = valueMap.value.get(key) || 0
      const label = props.tooltipFormatter
        ? props.tooltipFormatter({ date: d, value: val })
        : `<div style="font-weight:600;color:var(--color-text,#050505)">${d3.timeFormat('%b %d, %Y')(d)}</div>
           <div style="color:var(--color-text-secondary,#555)">${val} ${val === 1 ? 'activity' : 'activities'}</div>`
      tooltip.html(label).style('opacity', 1)

      d3.select(event.target)
        .attr('stroke', 'var(--color-text, #050505)')
        .attr('stroke-width', 1.5)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 36}px`)
    })
    .on('mouseleave', (event) => {
      tooltip.style('opacity', 0)
      d3.select(event.target)
        .attr('stroke', 'var(--color-border, rgba(0,0,0,0.06))')
        .attr('stroke-width', 0.5)
    })
    .on('click', (event, d) => {
      emit('date-click', { date: d, value: valueMap.value.get(fmt(d)) || 0 })
    })

  // Entrance animation
  g.selectAll('rect')
    .style('opacity', 0)
    .transition()
    .duration(400)
    .delay((d, i) => Math.min(i * 2, 600))
    .ease(d3.easeCubicOut)
    .style('opacity', 1)
}

watch([() => props.data.length, () => props.colorScheme, () => props.monthsToShow], () => {
  nextTick(() => renderChart())
})

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
        <slot name="title">Activity</slot>
      </h3>
      <slot name="actions" />
    </div>

    <div
      v-if="data.length"
      ref="chartRef"
      class="relative overflow-x-auto"
    />

    <div v-else class="flex items-center justify-center h-[120px] text-[var(--color-text-muted)] text-sm">
      <span>No activity data available</span>
    </div>

    <!-- Legend -->
    <div v-if="data.length" class="flex items-center gap-2 mt-3 text-xs text-[var(--color-text-muted)]">
      <span>Less</span>
      <span
        v-for="(color, i) in legendColors"
        :key="i"
        class="inline-block w-[13px] h-[13px] rounded-sm"
        :style="{ background: color }"
      />
      <span>More</span>
    </div>
  </div>
</template>
