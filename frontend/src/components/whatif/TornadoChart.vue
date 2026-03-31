<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
    // Each item: { parameter, low_value, high_value, low_outcome, high_outcome, base_outcome, low_scenario_id?, high_scenario_id? }
  },
  baseOutcome: { type: Number, default: null },
  outcomeLabel: { type: String, default: 'Outcome' },
  title: { type: String, default: 'Parameter Sensitivity' },
  subtitle: { type: String, default: 'Impact of each parameter on simulation outcome' },
})

const emit = defineEmits(['bar-click'])

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  decrease: '#ff5600',
  increase: '#009900',
  text: '#050505',
  muted: '#888',
  grid: 'rgba(0,0,0,0.06)',
  baseline: '#2068FF',
}

const DEMO_DATA = [
  { parameter: 'Agent Count', low_value: 5, high_value: 25, low_outcome: 0.32, high_outcome: 0.78, base_outcome: 0.55 },
  { parameter: 'Round Count', low_value: 48, high_value: 288, low_outcome: 0.38, high_outcome: 0.71, base_outcome: 0.55 },
  { parameter: 'Temperature', low_value: 0.2, high_value: 1.0, low_outcome: 0.61, high_outcome: 0.42, base_outcome: 0.55 },
  { parameter: 'Personality Mix', low_value: 0.1, high_value: 0.9, low_outcome: 0.44, high_outcome: 0.68, base_outcome: 0.55 },
  { parameter: 'Initial Sentiment', low_value: -0.5, high_value: 0.5, low_outcome: 0.41, high_outcome: 0.65, base_outcome: 0.55 },
  { parameter: 'Constraint Level', low_value: 1, high_value: 5, low_outcome: 0.52, high_outcome: 0.49, base_outcome: 0.55 },
]

const chartData = computed(() => {
  const items = props.data.length ? props.data : DEMO_DATA
  const base = props.baseOutcome ?? items[0]?.base_outcome ?? 0

  return items
    .map(d => ({
      ...d,
      base: d.base_outcome ?? base,
      deltaLow: (d.low_outcome ?? base) - (d.base_outcome ?? base),
      deltaHigh: (d.high_outcome ?? base) - (d.base_outcome ?? base),
    }))
    .map(d => ({
      ...d,
      totalImpact: Math.abs(d.deltaLow) + Math.abs(d.deltaHigh),
    }))
    .sort((a, b) => b.totalImpact - a.totalImpact)
})

const isDemo = computed(() => !props.data.length)

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !chartData.value.length) return

  const data = chartData.value
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 56, right: 80, bottom: 32, left: 140 }
  const barHeight = 32
  const barGap = 10
  const width = containerWidth - margin.left - margin.right
  const height = data.length * (barHeight + barGap) - barGap
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
    .text(props.title)

  // Subtitle
  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text(props.subtitle)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Determine symmetric domain from max absolute delta
  const maxAbsDelta = d3.max(data, d => Math.max(Math.abs(d.deltaLow), Math.abs(d.deltaHigh)))
  const domainPad = maxAbsDelta * 1.15
  const xDomain = [-domainPad, domainPad]

  const x = d3.scaleLinear()
    .domain(xDomain)
    .range([0, width])

  const y = d3.scaleBand()
    .domain(data.map(d => d.parameter))
    .range([0, height])
    .padding(barGap / (barHeight + barGap))

  const centerX = x(0)

  // Grid lines
  const ticks = x.ticks(8)
  g.selectAll('.grid-line')
    .data(ticks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', d => d === 0 ? COLORS.baseline : COLORS.grid)
    .attr('stroke-width', d => d === 0 ? 1.5 : 1)
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,3')

  // X-axis tick labels
  g.selectAll('.x-label')
    .data(ticks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', COLORS.muted)
    .text(d => {
      if (d === 0) return 'Base'
      return d > 0 ? `+${d.toFixed(2)}` : d.toFixed(2)
    })

  // Parameter labels (left side)
  g.selectAll('.param-label')
    .data(data)
    .join('text')
    .attr('x', -10)
    .attr('y', d => y(d.parameter) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '12px')
    .attr('fill', '#555')
    .text(d => d.parameter)

  // Tooltip
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '10px 14px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('max-width', '260px')

  function showTooltip(event, d, side) {
    const isLow = side === 'low'
    const delta = isLow ? d.deltaLow : d.deltaHigh
    const outcome = isLow ? d.low_outcome : d.high_outcome
    const paramValue = isLow ? d.low_value : d.high_value
    const color = delta < 0 ? COLORS.decrease : COLORS.increase
    const sign = delta >= 0 ? '+' : ''

    tooltip
      .html(`
        <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">${d.parameter}</div>
        <div style="color:${COLORS.muted};font-size:11px;margin-bottom:6px">
          ${isLow ? 'Low' : 'High'} value: ${formatValue(paramValue)}
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px">
          <span style="color:${COLORS.muted}">${props.outcomeLabel}:</span>
          <span style="font-weight:600">${outcome.toFixed(2)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px">
          <span style="color:${COLORS.muted}">vs Base:</span>
          <span style="font-weight:600;color:${color}">${sign}${delta.toFixed(3)}</span>
        </div>
      `)
      .style('opacity', 1)
  }

  function moveTooltip(event) {
    const rect = container.getBoundingClientRect()
    tooltip
      .style('left', `${event.clientX - rect.left + 14}px`)
      .style('top', `${event.clientY - rect.top - 20}px`)
  }

  function hideTooltip() {
    tooltip.style('opacity', 0)
  }

  // Draw bars for each parameter
  data.forEach((d, i) => {
    const barY = y(d.parameter)
    const bh = y.bandwidth()

    // Low-side bar (deltaLow: usually negative, extends left)
    const lowX = d.deltaLow < 0 ? x(d.deltaLow) : centerX
    const lowW = Math.abs(x(d.deltaLow) - centerX)

    g.append('rect')
      .attr('x', centerX)
      .attr('y', barY)
      .attr('width', 0)
      .attr('height', bh)
      .attr('rx', 3)
      .attr('fill', d.deltaLow < 0 ? COLORS.decrease : COLORS.increase)
      .attr('opacity', 0.8)
      .attr('cursor', d.low_scenario_id ? 'pointer' : 'default')
      .on('mouseenter', (event) => showTooltip(event, d, 'low'))
      .on('mousemove', moveTooltip)
      .on('mouseleave', hideTooltip)
      .on('click', () => {
        if (d.low_scenario_id) emit('bar-click', { scenarioId: d.low_scenario_id, parameter: d.parameter, side: 'low' })
      })
      .transition()
      .duration(600)
      .delay(i * 60)
      .ease(d3.easeCubicOut)
      .attr('x', lowX)
      .attr('width', lowW)

    // High-side bar (deltaHigh: usually positive, extends right)
    const highX = d.deltaHigh >= 0 ? centerX : x(d.deltaHigh)
    const highW = Math.abs(x(d.deltaHigh) - centerX)

    g.append('rect')
      .attr('x', centerX)
      .attr('y', barY)
      .attr('width', 0)
      .attr('height', bh)
      .attr('rx', 3)
      .attr('fill', d.deltaHigh >= 0 ? COLORS.increase : COLORS.decrease)
      .attr('opacity', 0.8)
      .attr('cursor', d.high_scenario_id ? 'pointer' : 'default')
      .on('mouseenter', (event) => showTooltip(event, d, 'high'))
      .on('mousemove', moveTooltip)
      .on('mouseleave', hideTooltip)
      .on('click', () => {
        if (d.high_scenario_id) emit('bar-click', { scenarioId: d.high_scenario_id, parameter: d.parameter, side: 'high' })
      })
      .transition()
      .duration(600)
      .delay(i * 60 + 30)
      .ease(d3.easeCubicOut)
      .attr('x', highX)
      .attr('width', highW)

    // Value labels at bar ends
    // Low side
    const lowLabelX = d.deltaLow < 0 ? x(d.deltaLow) - 6 : x(d.deltaLow) + 6
    const lowAnchor = d.deltaLow < 0 ? 'end' : 'start'
    g.append('text')
      .attr('x', lowLabelX)
      .attr('y', barY + bh / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', lowAnchor)
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', d.deltaLow < 0 ? COLORS.decrease : COLORS.increase)
      .style('opacity', 0)
      .text(formatValue(d.low_value))
      .transition()
      .duration(300)
      .delay(600 + i * 60)
      .style('opacity', 1)

    // High side
    const highLabelX = d.deltaHigh >= 0 ? x(d.deltaHigh) + 6 : x(d.deltaHigh) - 6
    const highAnchor = d.deltaHigh >= 0 ? 'start' : 'end'
    g.append('text')
      .attr('x', highLabelX)
      .attr('y', barY + bh / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', highAnchor)
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', d.deltaHigh >= 0 ? COLORS.increase : COLORS.decrease)
      .style('opacity', 0)
      .text(formatValue(d.high_value))
      .transition()
      .duration(300)
      .delay(630 + i * 60)
      .style('opacity', 1)
  })

  // Baseline annotation
  g.append('text')
    .attr('x', centerX)
    .attr('y', -8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.baseline)
    .text(`Base: ${(data[0]?.base ?? 0).toFixed(2)}`)
}

function formatValue(v) {
  if (v == null) return '—'
  if (Number.isInteger(v)) return String(v)
  return v.toFixed(2)
}

watch(chartData, () => nextTick(renderChart))

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
    <div v-if="isDemo" class="mb-3 px-3 py-2 bg-[var(--color-tint,rgba(32,104,255,0.06))] rounded text-xs text-[var(--color-text-muted)]">
      Showing demo data — run a sensitivity analysis to see real results
    </div>

    <div v-if="chartData.length" ref="chartRef" class="w-full relative" />

    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      No sensitivity data available
    </div>

    <!-- Legend -->
    <div v-if="chartData.length" class="flex items-center gap-5 mt-3 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #ff5600; opacity: 0.8" /> Decreases outcome
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" style="background: #009900; opacity: 0.8" /> Increases outcome
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-0.5 h-3 rounded-sm bg-[#2068FF]" /> Base scenario
      </span>
    </div>
  </div>
</template>
