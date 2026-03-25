<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import client from '../../api/client.js'
import { useCountUp } from '../../composables/useCountUp.js'

const chartRef = ref(null)
const stages = ref([])
const conversionRates = ref([])
const loading = ref(true)
const error = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  secondary: '#4D8AFF',
  orange: '#ff5600',
  green: '#009900',
  text: '#050505',
  muted: '#888',
  convArrow: '#bbb',
}

const totalValue = computed(() => stages.value[0]?.value ?? 0)
const totalCount = computed(() => stages.value[0]?.count ?? 0)
const displayCount = useCountUp(totalCount)

function formatCurrency(val) {
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`
  if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`
  return `$${val}`
}

function formatNumber(val) {
  return val.toLocaleString()
}

async function fetchFunnel() {
  loading.value = true
  error.value = null
  try {
    const { data } = await client.get('/v1/pipeline/funnel')
    stages.value = data.stages
    conversionRates.value = data.conversion_rates
  } catch (e) {
    error.value = e.message || 'Failed to load funnel data'
  } finally {
    loading.value = false
    nextTick(renderFunnel)
  }
}

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderFunnel() {
  clearChart()
  const container = chartRef.value
  if (!container || !stages.value.length) return

  const data = stages.value
  const rates = conversionRates.value
  const containerWidth = container.clientWidth
  const isWide = containerWidth > 480

  if (isWide) {
    renderHorizontal(container, data, rates, containerWidth)
  } else {
    renderVertical(container, data, rates, containerWidth)
  }
}

function renderHorizontal(container, data, rates, containerWidth) {
  const margin = { top: 8, right: 12, bottom: 8, left: 12 }
  const width = containerWidth - margin.left - margin.right
  const barMaxHeight = 72
  const barMinHeight = 20
  const totalHeight = 180

  const maxCount = d3.max(data, (d) => d.count)

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const stageCount = data.length
  const gapForArrows = 40
  const stageWidth = (width - gapForArrows * (stageCount - 1)) / stageCount
  const barY = 36

  data.forEach((stage, i) => {
    const x = i * (stageWidth + gapForArrows)
    const ratio = stage.count / maxCount
    const barHeight = barMinHeight + (barMaxHeight - barMinHeight) * ratio
    const yOffset = barY + (barMaxHeight - barHeight) / 2

    // Trapezoid bar — wider at top, narrower at bottom to suggest funnel narrowing
    const nextRatio = i < data.length - 1 ? data[i + 1].count / maxCount : ratio * 0.7
    const topWidth = stageWidth * 0.95
    const bottomWidth = stageWidth * (0.4 + 0.55 * nextRatio)
    const topX = x + (stageWidth - topWidth) / 2
    const bottomX = x + (stageWidth - bottomWidth) / 2

    const trapezoid = [
      [topX, yOffset],
      [topX + topWidth, yOffset],
      [bottomX + bottomWidth, yOffset + barHeight],
      [bottomX, yOffset + barHeight],
    ]

    g.append('path')
      .attr('d', `M${trapezoid.map((p) => p.join(',')).join('L')}Z`)
      .attr('fill', stage.color)
      .attr('opacity', 0)
      .attr('rx', 4)
      .transition()
      .duration(500)
      .delay(i * 100)
      .ease(d3.easeCubicOut)
      .attr('opacity', 0.85)

    // Stage name
    g.append('text')
      .attr('x', x + stageWidth / 2)
      .attr('y', barY - 8)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.text)
      .style('opacity', 0)
      .text(stage.name)
      .transition()
      .duration(300)
      .delay(i * 100 + 200)
      .style('opacity', 1)

    // Count
    g.append('text')
      .attr('x', x + stageWidth / 2)
      .attr('y', yOffset + barHeight + 18)
      .attr('text-anchor', 'middle')
      .attr('font-size', '13px')
      .attr('font-weight', '700')
      .attr('fill', stage.color)
      .style('opacity', 0)
      .text(formatNumber(stage.count))
      .transition()
      .duration(300)
      .delay(i * 100 + 300)
      .style('opacity', 1)

    // Value
    g.append('text')
      .attr('x', x + stageWidth / 2)
      .attr('y', yOffset + barHeight + 34)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', COLORS.muted)
      .style('opacity', 0)
      .text(formatCurrency(stage.value))
      .transition()
      .duration(300)
      .delay(i * 100 + 350)
      .style('opacity', 1)

    // Conversion arrow between stages
    if (i < data.length - 1 && rates[i]) {
      const arrowX = x + stageWidth + 4
      const arrowY = barY + barMaxHeight / 2

      // Arrow line
      g.append('line')
        .attr('x1', arrowX)
        .attr('x2', arrowX + gapForArrows - 8)
        .attr('y1', arrowY)
        .attr('y2', arrowY)
        .attr('stroke', COLORS.convArrow)
        .attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#arrowhead)')
        .style('opacity', 0)
        .transition()
        .duration(300)
        .delay(i * 100 + 400)
        .style('opacity', 1)

      // Rate label
      g.append('text')
        .attr('x', arrowX + gapForArrows / 2 - 4)
        .attr('y', arrowY - 8)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', COLORS.text)
        .style('opacity', 0)
        .text(`${rates[i].rate}%`)
        .transition()
        .duration(300)
        .delay(i * 100 + 400)
        .style('opacity', 1)
    }
  })

  // Arrowhead marker
  svg
    .append('defs')
    .append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 0 10 10')
    .attr('refX', 8)
    .attr('refY', 5)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,0 L10,5 L0,10 Z')
    .attr('fill', COLORS.convArrow)
}

function renderVertical(container, data, rates, containerWidth) {
  const margin = { top: 8, right: 12, bottom: 8, left: 12 }
  const width = containerWidth - margin.left - margin.right
  const stageHeight = 36
  const gapHeight = 24
  const totalHeight =
    data.length * stageHeight + (data.length - 1) * gapHeight + margin.top + margin.bottom

  const maxCount = d3.max(data, (d) => d.count)

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  data.forEach((stage, i) => {
    const y = i * (stageHeight + gapHeight)
    const ratio = stage.count / maxCount
    const barWidth = width * (0.4 + 0.6 * ratio)
    const x = (width - barWidth) / 2

    // Stage bar (rounded rect)
    g.append('rect')
      .attr('x', x)
      .attr('y', y)
      .attr('width', 0)
      .attr('height', stageHeight)
      .attr('rx', 6)
      .attr('fill', stage.color)
      .attr('opacity', 0.85)
      .transition()
      .duration(500)
      .delay(i * 120)
      .ease(d3.easeCubicOut)
      .attr('width', barWidth)

    // Stage name + count (inside bar)
    g.append('text')
      .attr('x', width / 2)
      .attr('y', y + stageHeight / 2 - 2)
      .attr('dy', '-0.15em')
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .style('opacity', 0)
      .text(`${stage.name}`)
      .transition()
      .duration(300)
      .delay(i * 120 + 250)
      .style('opacity', 1)

    g.append('text')
      .attr('x', width / 2)
      .attr('y', y + stageHeight / 2 + 2)
      .attr('dy', '0.9em')
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'rgba(255,255,255,0.85)')
      .style('opacity', 0)
      .text(`${formatNumber(stage.count)}  ·  ${formatCurrency(stage.value)}`)
      .transition()
      .duration(300)
      .delay(i * 120 + 300)
      .style('opacity', 1)

    // Conversion rate between stages
    if (i < data.length - 1 && rates[i]) {
      const arrowY = y + stageHeight + gapHeight / 2

      g.append('text')
        .attr('x', width / 2)
        .attr('y', arrowY + 1)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', COLORS.muted)
        .style('opacity', 0)
        .text(`▼ ${rates[i].rate}%`)
        .transition()
        .duration(300)
        .delay(i * 120 + 350)
        .style('opacity', 1)
    }
  })
}

onMounted(() => {
  fetchFunnel()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderFunnel(), 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div
    class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] cursor-pointer hover:border-[#2068FF]/40 transition-colors"
    style="box-shadow: var(--card-shadow); max-height: 300px"
    @click="$router.push('/simulations')"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-5 pt-4 pb-2">
      <div>
        <h3 class="text-sm font-semibold text-[#050505]">Pipeline Funnel</h3>
        <p class="text-xs text-[#888] mt-0.5">
          <span class="font-semibold text-[#2068FF]">{{ displayCount }}</span> MQLs ·
          {{ formatCurrency(totalValue) }} pipeline
        </p>
      </div>
      <span class="text-xs text-[#888] hover:text-[#2068FF] transition-colors">
        View →
      </span>
    </div>

    <!-- Loading / Error / Chart -->
    <div v-if="loading" class="flex items-center justify-center h-32 px-5 pb-4">
      <div class="w-5 h-5 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin" />
    </div>
    <div v-else-if="error" class="px-5 pb-4 text-xs text-red-500">{{ error }}</div>
    <div v-else ref="chartRef" class="w-full px-3 pb-3" />
  </div>
</template>
