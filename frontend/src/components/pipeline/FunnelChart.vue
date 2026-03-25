<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  stages: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const DEMO_STAGES = [
  { name: 'Raw Lead', count: 1000, value: 2500000, avg_days: 7, conversion_rate_to_next: 25 },
  { name: 'MQL', count: 250, value: 1875000, avg_days: 14, conversion_rate_to_next: 40 },
  { name: 'SQL', count: 100, value: 1200000, avg_days: 21, conversion_rate_to_next: 60 },
  { name: 'SAO', count: 60, value: 900000, avg_days: 14, conversion_rate_to_next: 70 },
  { name: 'Proposal', count: 42, value: 756000, avg_days: 10, conversion_rate_to_next: 35 },
  { name: 'Closed Won', count: 15, value: 450000, avg_days: 0, conversion_rate_to_next: null },
]

const data = computed(() => props.stages.length ? props.stages : DEMO_STAGES)

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function formatCurrency(value) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value}`
}

function renderFunnel() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const stages = data.value
  if (!stages.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const n = stages.length
  const margin = { top: 16, right: 20, bottom: 36, left: 20 }
  const width = containerWidth - margin.left - margin.right
  const funnelHeight = 200
  const totalHeight = funnelHeight + margin.top + margin.bottom

  const gapWidth = Math.max(36, Math.min(52, width * 0.06))
  const stageWidth = (width - gapWidth * (n - 1)) / n

  const maxCount = d3.max(stages, d => d.count)
  const minBarHeight = 30
  const maxBarHeight = funnelHeight - 16

  const heightScale = d3.scaleLinear()
    .domain([0, maxCount])
    .range([minBarHeight, maxBarHeight])

  const colorScale = d3.scaleLinear()
    .domain([0, n - 1])
    .range(['#93b8ff', '#1444aa'])
    .interpolate(d3.interpolateRgb)

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const centerY = funnelHeight / 2

  // Tooltip div
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
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.12)')
    .style('z-index', '10')
    .style('max-width', '220px')
    .style('white-space', 'nowrap')

  function showTooltip(event, stage) {
    const daysLine = stage.avg_days > 0
      ? `<div style="color:var(--color-text-muted,#888)">Avg ${stage.avg_days}d in stage</div>`
      : ''
    const convLine = stage.conversion_rate_to_next != null
      ? `<div style="margin-top:4px;padding-top:4px;border-top:1px solid var(--color-border,rgba(0,0,0,0.08));color:var(--color-text-muted,#888)">\u2192 ${stage.conversion_rate_to_next}% convert to next</div>`
      : ''

    tooltip.html(`
      <div style="font-weight:600;color:var(--color-text,#1a1a1a);margin-bottom:4px">${stage.name}</div>
      <div><strong>${stage.count.toLocaleString()}</strong> leads</div>
      <div style="color:#2068FF;font-weight:600">${formatCurrency(stage.value)}</div>
      ${daysLine}
      ${convLine}
    `)
    .style('opacity', 1)
    moveTooltip(event)
  }

  function moveTooltip(event) {
    const rect = container.getBoundingClientRect()
    const x = event.clientX - rect.left + 14
    const y = event.clientY - rect.top - 70
    tooltip
      .style('left', `${x}px`)
      .style('top', `${Math.max(0, y)}px`)
  }

  function hideTooltip() {
    tooltip.style('opacity', 0)
  }

  // Draw each stage
  stages.forEach((stage, i) => {
    const x = i * (stageWidth + gapWidth)
    const leftH = heightScale(stage.count)
    const rightH = i < n - 1
      ? heightScale(stages[i + 1].count)
      : leftH * 0.55

    const expandedPath = `
      M ${x} ${centerY - leftH / 2}
      L ${x + stageWidth} ${centerY - rightH / 2}
      L ${x + stageWidth} ${centerY + rightH / 2}
      L ${x} ${centerY + leftH / 2}
      Z`

    const collapsedPath = `
      M ${x} ${centerY}
      L ${x + stageWidth} ${centerY}
      L ${x + stageWidth} ${centerY}
      L ${x} ${centerY}
      Z`

    // Trapezoid
    g.append('path')
      .attr('d', collapsedPath)
      .attr('fill', colorScale(i))
      .attr('opacity', 0.88)
      .style('cursor', 'pointer')
      .on('mouseenter', function (event) {
        d3.select(this).transition().duration(100).attr('opacity', 1)
        showTooltip(event, stage)
      })
      .on('mousemove', moveTooltip)
      .on('mouseleave', function () {
        d3.select(this).transition().duration(100).attr('opacity', 0.88)
        hideTooltip()
      })
      .transition()
      .duration(600)
      .delay(i * 80)
      .ease(d3.easeCubicOut)
      .attr('d', expandedPath)

    // Stage name (inside trapezoid)
    g.append('text')
      .attr('x', x + stageWidth / 2)
      .attr('y', centerY - 4)
      .attr('text-anchor', 'middle')
      .attr('font-size', stageWidth > 80 ? '12px' : '10px')
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .text(stage.name)
      .transition()
      .duration(300)
      .delay(600 + i * 80)
      .style('opacity', 1)

    // Count (inside trapezoid)
    g.append('text')
      .attr('x', x + stageWidth / 2)
      .attr('y', centerY + 13)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('fill', 'rgba(255,255,255,0.85)')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .text(stage.count.toLocaleString())
      .transition()
      .duration(300)
      .delay(650 + i * 80)
      .style('opacity', 1)

    // Value label below
    g.append('text')
      .attr('x', x + stageWidth / 2)
      .attr('y', funnelHeight + 16)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'var(--color-text-muted, #888)')
      .style('opacity', 0)
      .text(formatCurrency(stage.value))
      .transition()
      .duration(300)
      .delay(700 + i * 80)
      .style('opacity', 1)

    // Conversion arrow + rate between stages
    if (i < n - 1 && stage.conversion_rate_to_next != null) {
      const arrowCenterX = x + stageWidth + gapWidth / 2

      // Conversion rate label
      g.append('text')
        .attr('x', arrowCenterX)
        .attr('y', centerY - 10)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', 'var(--color-text, #1a1a1a)')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .text(`${stage.conversion_rate_to_next}%`)
        .transition()
        .duration(300)
        .delay(700 + i * 80)
        .style('opacity', 1)

      // Arrow line
      const arrowLeft = x + stageWidth + 6
      const arrowRight = x + stageWidth + gapWidth - 6
      const arrowY = centerY + 5

      const arrowGroup = g.append('g')
        .style('opacity', 0)

      arrowGroup.append('line')
        .attr('x1', arrowLeft)
        .attr('y1', arrowY)
        .attr('x2', arrowRight)
        .attr('y2', arrowY)
        .attr('stroke', 'var(--color-text-muted, #999)')
        .attr('stroke-width', 1.5)

      // Arrowhead
      arrowGroup.append('path')
        .attr('d', `M${arrowRight - 5},${arrowY - 3} L${arrowRight},${arrowY} L${arrowRight - 5},${arrowY + 3}`)
        .attr('stroke', 'var(--color-text-muted, #999)')
        .attr('stroke-width', 1.5)
        .attr('fill', 'none')

      arrowGroup.transition()
        .duration(300)
        .delay(700 + i * 80)
        .style('opacity', 1)
    }
  })
}

// Lifecycle

watch(() => props.stages, () => {
  nextTick(() => renderFunnel())
}, { deep: true })

onMounted(() => {
  renderFunnel()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderFunnel, 200)
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
    <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Pipeline Funnel</h3>

    <div
      v-if="data.length"
      ref="chartRef"
      class="w-full relative"
      style="height: 252px"
    />

    <div
      v-else
      class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm"
    >
      No funnel data available
    </div>
  </div>
</template>
