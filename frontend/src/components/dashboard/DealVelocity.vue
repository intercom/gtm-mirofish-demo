<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  pipeline: { type: Number, default: 48 },
  winRate: { type: Number, default: 0.32 },
  avgDealSize: { type: Number, default: 42_000 },
  salesCycleDays: { type: Number, default: 45 },
  target: { type: Number, default: 12_000 },
  pipelineTrend: { type: Number, default: 8.2 },
  winRateTrend: { type: Number, default: -1.5 },
  avgDealSizeTrend: { type: Number, default: 3.1 },
  salesCycleTrend: { type: Number, default: -5.0 },
})

const gaugeRef = ref(null)
const showTooltip = ref(false)
let resizeObserver = null
let resizeTimer = null

const velocity = computed(() => {
  if (!props.salesCycleDays) return 0
  return (props.pipeline * props.winRate * props.avgDealSize) / props.salesCycleDays
})

const gaugeMax = computed(() => Math.max(props.target * 2, velocity.value * 1.5))

const breakdownItems = computed(() => [
  {
    label: 'Pipeline',
    formatted: `${props.pipeline} deals`,
    trend: props.pipelineTrend,
    positiveIsGood: true,
  },
  {
    label: 'Win Rate',
    formatted: `${(props.winRate * 100).toFixed(0)}%`,
    trend: props.winRateTrend,
    positiveIsGood: true,
  },
  {
    label: 'Avg Deal Size',
    formatted: formatCurrency(props.avgDealSize),
    trend: props.avgDealSizeTrend,
    positiveIsGood: true,
  },
  {
    label: 'Sales Cycle',
    formatted: `${props.salesCycleDays} days`,
    trend: props.salesCycleTrend,
    positiveIsGood: false,
  },
])

const COLORS = {
  red: '#ef4444',
  yellow: '#f59e0b',
  green: '#009900',
  primary: '#2068FF',
  text: '#050505',
  muted: '#888888',
}

function formatCurrency(value) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${Math.round(value)}`
}

function formatVelocity(value) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`
  return `$${Math.round(value)}`
}

function trendIcon(trend) {
  if (trend > 0.5) return '↑'
  if (trend < -0.5) return '↓'
  return '→'
}

function trendColor(trend, positiveIsGood) {
  const isUp = trend > 0.5
  const isDown = trend < -0.5
  if (isUp) return positiveIsGood ? 'var(--color-success)' : 'var(--color-error)'
  if (isDown) return positiveIsGood ? 'var(--color-error)' : 'var(--color-success)'
  return 'var(--color-text-muted)'
}

function clearGauge() {
  if (!gaugeRef.value) return
  d3.select(gaugeRef.value).selectAll('*').remove()
}

function renderGauge() {
  clearGauge()
  const container = gaugeRef.value
  if (!container) return

  const containerWidth = container.clientWidth
  if (containerWidth <= 0) return

  const size = Math.min(containerWidth, 360)
  const radius = size / 2 - 24
  const innerRadius = radius * 0.72
  const centerX = containerWidth / 2
  const centerY = radius + 36
  const totalHeight = centerY + 36

  const startAngle = -Math.PI * 0.75
  const endAngle = Math.PI * 0.75
  const max = gaugeMax.value

  const angleScale = d3.scaleLinear()
    .domain([0, max])
    .range([startAngle, endAngle])
    .clamp(true)

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${centerX},${centerY})`)

  // Background track
  const bgArc = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(radius)
    .startAngle(startAngle)
    .endAngle(endAngle)
    .cornerRadius(3)

  g.append('path')
    .attr('d', bgArc)
    .attr('fill', 'rgba(0,0,0,0.04)')

  // Color zone arcs
  const zoneArc = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(radius)
    .cornerRadius(2)

  const zones = [
    { start: 0, end: 0.33, color: COLORS.red },
    { start: 0.33, end: 0.66, color: COLORS.yellow },
    { start: 0.66, end: 1.0, color: COLORS.green },
  ]

  zones.forEach(zone => {
    g.append('path')
      .datum({
        startAngle: angleScale(max * zone.start),
        endAngle: angleScale(max * zone.end),
      })
      .attr('d', zoneArc)
      .attr('fill', zone.color)
      .attr('opacity', 0.18)
  })

  // Tick marks and labels
  const numTicks = 5
  for (let i = 0; i <= numTicks; i++) {
    const val = (max / numTicks) * i
    const angle = angleScale(val)
    const x1 = Math.sin(angle) * (radius + 2)
    const y1 = -Math.cos(angle) * (radius + 2)
    const x2 = Math.sin(angle) * (radius + 7)
    const y2 = -Math.cos(angle) * (radius + 7)

    g.append('line')
      .attr('x1', x1).attr('y1', y1)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', COLORS.muted)
      .attr('stroke-width', 1.5)

    const lx = Math.sin(angle) * (radius + 18)
    const ly = -Math.cos(angle) * (radius + 18)
    g.append('text')
      .attr('x', lx).attr('y', ly)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '9px')
      .attr('fill', COLORS.muted)
      .text(formatCurrency(val))
  }

  // Target marker (dashed line across the arc)
  const targetAngle = angleScale(props.target)
  const tInner = innerRadius - 4
  const tOuter = radius + 4

  g.append('line')
    .attr('x1', Math.sin(targetAngle) * tInner)
    .attr('y1', -Math.cos(targetAngle) * tInner)
    .attr('x2', Math.sin(targetAngle) * tOuter)
    .attr('y2', -Math.cos(targetAngle) * tOuter)
    .attr('stroke', COLORS.primary)
    .attr('stroke-width', 2.5)
    .attr('stroke-dasharray', '4,2')
    .attr('opacity', 0)
    .transition()
    .duration(400)
    .delay(800)
    .attr('opacity', 1)

  // Target label
  const tLabelR = radius + 30
  g.append('text')
    .attr('x', Math.sin(targetAngle) * tLabelR)
    .attr('y', -Math.cos(targetAngle) * tLabelR)
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('font-size', '9px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.primary)
    .attr('opacity', 0)
    .text('Target')
    .transition()
    .duration(400)
    .delay(800)
    .attr('opacity', 1)

  // Needle
  const needleLen = radius - 8
  const needle = g.append('g')

  needle.append('path')
    .attr('d', `M -3.5,6 L 0,${-needleLen} L 3.5,6 Z`)
    .attr('fill', COLORS.text)

  needle.append('circle')
    .attr('r', 6)
    .attr('fill', COLORS.text)

  needle.append('circle')
    .attr('r', 2.5)
    .attr('fill', '#fff')

  // Animate needle from start position to current value
  const startDeg = (startAngle * 180) / Math.PI
  const currentDeg = (angleScale(velocity.value) * 180) / Math.PI

  needle
    .attr('transform', `rotate(${startDeg})`)
    .transition()
    .duration(1200)
    .ease(d3.easeCubicOut)
    .attr('transform', `rotate(${currentDeg})`)

  // Center value text with animated count-up
  const valueText = g.append('text')
    .attr('text-anchor', 'middle')
    .attr('y', -innerRadius * 0.28)
    .attr('font-size', '26px')
    .attr('font-weight', '700')
    .attr('fill', COLORS.text)

  valueText.transition()
    .duration(1200)
    .ease(d3.easeCubicOut)
    .tween('text', function () {
      const interp = d3.interpolateNumber(0, velocity.value)
      return function (t) {
        d3.select(this).text(formatVelocity(interp(t)))
      }
    })

  // Subtitle below value
  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('y', -innerRadius * 0.28 + 20)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .attr('opacity', 0)
    .text('velocity / day')
    .transition()
    .duration(400)
    .delay(600)
    .attr('opacity', 1)
}

watch(
  [() => props.pipeline, () => props.winRate, () => props.avgDealSize, () => props.salesCycleDays, () => props.target],
  () => nextTick(() => renderGauge()),
)

onMounted(() => {
  renderGauge()
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderGauge(), 200)
  })
  if (gaugeRef.value) resizeObserver.observe(gaugeRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div
    class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-6"
    style="box-shadow: var(--card-shadow)"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Deal Velocity</h3>
      <div class="relative">
        <button
          class="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
          @mouseenter="showTooltip = true"
          @mouseleave="showTooltip = false"
          aria-label="Velocity formula"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5" />
            <path d="M8 7v4M8 5.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </button>
        <div
          v-if="showTooltip"
          class="absolute right-0 top-7 z-10 w-64 rounded-lg border border-[var(--card-border)] bg-[var(--color-surface)] p-3 text-xs text-[var(--color-text-secondary)] leading-relaxed"
          style="box-shadow: var(--shadow-md)"
        >
          <p class="font-semibold text-[var(--color-text)] mb-1">Deal Velocity Formula</p>
          <p class="font-mono text-[10px] bg-[var(--color-tint)] rounded px-2 py-1">
            velocity = (pipeline × win_rate × avg_deal_size) / sales_cycle_days
          </p>
        </div>
      </div>
    </div>

    <!-- Gauge -->
    <div ref="gaugeRef" class="w-full" />

    <!-- Breakdown Grid -->
    <div class="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-[var(--card-border)]">
      <div
        v-for="item in breakdownItems"
        :key="item.label"
        class="rounded-lg bg-[var(--color-tint)] px-3 py-2.5"
      >
        <div class="text-[10px] text-[var(--color-text-muted)] mb-0.5">{{ item.label }}</div>
        <div class="text-sm font-semibold text-[var(--color-text)]">{{ item.formatted }}</div>
        <div
          class="text-xs mt-0.5"
          :style="{ color: trendColor(item.trend, item.positiveIsGood) }"
        >
          {{ item.trend > 0 ? '+' : '' }}{{ item.trend }}% {{ trendIcon(item.trend) }}
        </div>
      </div>
    </div>
  </div>
</template>
