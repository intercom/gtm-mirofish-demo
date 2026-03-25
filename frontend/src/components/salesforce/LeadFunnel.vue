<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  stages: {
    type: Array,
    default: () => [
      { name: 'New', count: 2340, avgDays: 3.2 },
      { name: 'Contacted', count: 1870, avgDays: 5.8 },
      { name: 'MQL', count: 1122, avgDays: 8.4 },
      { name: 'SQL', count: 561, avgDays: 12.1 },
      { name: 'Converted', count: 247, avgDays: 6.5 },
    ],
    validator: (v) => v.length >= 2 && v.every(s => s.name && typeof s.count === 'number'),
  },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  text: '#050505',
  muted: '#888',
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function renderFunnel() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const data = props.stages
  const total = data[0].count
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 16, right: 24, bottom: 16, left: 24 }
  const stageHeight = 52
  const gapHeight = 28
  const width = containerWidth - margin.left - margin.right
  const innerHeight = data.length * stageHeight + (data.length - 1) * gapHeight
  const totalHeight = innerHeight + margin.top + margin.bottom

  const maxBarWidth = width * 0.85
  const minBarWidth = maxBarWidth * 0.18

  const widthScale = d3.scaleLinear()
    .domain([0, total])
    .range([minBarWidth, maxBarWidth])

  const colorScale = d3.scaleLinear()
    .domain([0, data.length - 1])
    .range(['#7EB0FF', '#0A3880'])
    .interpolate(d3.interpolateRgb)

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const centerX = width / 2

  // Render each funnel stage as a trapezoid
  data.forEach((stage, i) => {
    const y = i * (stageHeight + gapHeight)
    const currentWidth = widthScale(stage.count)
    const nextWidth = i < data.length - 1 ? widthScale(data[i + 1].count) : currentWidth * 0.7
    const pct = ((stage.count / total) * 100).toFixed(1)

    // Trapezoid: wide at top, narrows at bottom
    const topLeft = centerX - currentWidth / 2
    const topRight = centerX + currentWidth / 2
    const bottomLeft = centerX - nextWidth / 2
    const bottomRight = centerX + nextWidth / 2

    const path = `
      M ${topLeft} ${y}
      L ${topRight} ${y}
      L ${bottomRight} ${y + stageHeight}
      L ${bottomLeft} ${y + stageHeight}
      Z
    `

    // Stage trapezoid with animation
    g.append('path')
      .attr('d', path)
      .attr('fill', colorScale(i))
      .attr('rx', 4)
      .attr('opacity', 0)
      .transition()
      .duration(500)
      .delay(i * 100)
      .ease(d3.easeCubicOut)
      .attr('opacity', 0.9)

    // Stage label (name + count) — centered
    const labelGroup = g.append('g')
      .attr('transform', `translate(${centerX}, ${y + stageHeight / 2})`)
      .style('opacity', 0)

    labelGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.3em')
      .attr('font-size', '13px')
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .text(stage.name)

    labelGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.1em')
      .attr('font-size', '11px')
      .attr('fill', 'rgba(255,255,255,0.85)')
      .text(`${stage.count.toLocaleString()} leads · ${pct}%`)

    labelGroup.transition()
      .duration(300)
      .delay(500 + i * 100)
      .style('opacity', 1)

    // Conversion rate between stages
    if (i < data.length - 1) {
      const nextStage = data[i + 1]
      const convRate = ((nextStage.count / stage.count) * 100).toFixed(1)
      const arrowY = y + stageHeight + gapHeight / 2

      const convGroup = g.append('g')
        .attr('transform', `translate(${centerX}, ${arrowY})`)
        .style('opacity', 0)

      // Arrow indicator
      convGroup.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '-0.2em')
        .attr('font-size', '10px')
        .attr('fill', COLORS.muted)
        .text('▼')

      convGroup.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '1.1em')
        .attr('font-size', '12px')
        .attr('font-weight', '600')
        .attr('fill', COLORS.text)
        .text(`${convRate}%`)

      convGroup.transition()
        .duration(300)
        .delay(600 + i * 100)
        .style('opacity', 1)
    }
  })

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
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.12)')
    .style('z-index', '10')
    .style('white-space', 'nowrap')

  // Invisible hover targets for each stage
  data.forEach((stage, i) => {
    const y = i * (stageHeight + gapHeight)
    const currentWidth = widthScale(stage.count)
    const pct = ((stage.count / total) * 100).toFixed(1)
    const convFromPrev = i > 0
      ? ((stage.count / data[i - 1].count) * 100).toFixed(1)
      : null

    g.append('rect')
      .attr('x', centerX - currentWidth / 2)
      .attr('y', y)
      .attr('width', currentWidth)
      .attr('height', stageHeight)
      .attr('fill', 'transparent')
      .attr('cursor', 'pointer')
      .on('mouseenter', () => {
        tooltip
          .html(`
            <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px;font-size:13px">${stage.name}</div>
            <div style="color:var(--color-text-secondary,#555)">
              <strong>${stage.count.toLocaleString()}</strong> leads · ${pct}% of total
            </div>
            ${convFromPrev ? `<div style="color:#2068FF;margin-top:3px">${convFromPrev}% conversion from ${data[i - 1].name}</div>` : ''}
            <div style="color:var(--color-text-muted,#888);margin-top:3px">Avg. ${stage.avgDays} days in stage</div>
          `)
          .style('opacity', 1)

        g.selectAll('path').filter((_, idx) => idx === i)
          .transition().duration(100)
          .attr('opacity', 1)
      })
      .on('mousemove', (event) => {
        const rect = container.getBoundingClientRect()
        tooltip
          .style('left', `${event.clientX - rect.left + 14}px`)
          .style('top', `${event.clientY - rect.top - 10}px`)
      })
      .on('mouseleave', () => {
        tooltip.style('opacity', 0)
        g.selectAll('path').filter((_, idx) => idx === i)
          .transition().duration(100)
          .attr('opacity', 0.9)
      })
  })
}

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
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Lead Funnel</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">Progression from New to Converted</p>
      </div>
      <div class="text-right">
        <span class="text-xs text-[var(--color-text-muted)]">Overall conversion</span>
        <p class="text-lg font-bold text-[#2068FF]">
          {{ stages.length >= 2 ? ((stages[stages.length - 1].count / stages[0].count) * 100).toFixed(1) : 0 }}%
        </p>
      </div>
    </div>

    <div ref="chartRef" class="relative w-full" />
  </div>
</template>
