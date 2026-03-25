<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  dataA: {
    type: Object,
    default: null,
  },
  dataB: {
    type: Object,
    default: null,
  },
  labelA: { type: String, default: 'Simulation A' },
  labelB: { type: String, default: 'Simulation B' },
  maxValue: { type: Number, default: 100 },
  levels: { type: Number, default: 5 },
})

const emit = defineEmits(['dimension-click'])

const COLORS = {
  a: '#2068FF',
  b: '#ff5600',
  text: '#050505',
  grid: 'rgba(0,0,0,0.08)',
  gridLabel: '#aaa',
}

const DIMENSIONS = [
  { key: 'sentiment', label: 'Overall Sentiment' },
  { key: 'consensus', label: 'Consensus Reached' },
  { key: 'decisionQuality', label: 'Decision Quality' },
  { key: 'engagement', label: 'Agent Engagement' },
  { key: 'informationSpread', label: 'Information Spread' },
  { key: 'satisfaction', label: 'Outcome Satisfaction' },
]

const DEMO_DATA_A = {
  sentiment: 72,
  consensus: 65,
  decisionQuality: 81,
  engagement: 88,
  informationSpread: 56,
  satisfaction: 74,
}

const DEMO_DATA_B = {
  sentiment: 58,
  consensus: 79,
  decisionQuality: 63,
  engagement: 71,
  informationSpread: 82,
  satisfaction: 66,
}

const chartRef = ref(null)
const selectedDimension = ref(null)
let resizeObserver = null
let resizeTimer = null

const seriesA = computed(() => props.dataA || DEMO_DATA_A)
const seriesB = computed(() => props.dataB || DEMO_DATA_B)

const summaryText = computed(() => {
  const a = seriesA.value
  const b = seriesB.value
  let bestA = null
  let bestB = null
  let maxDiffA = -Infinity
  let maxDiffB = -Infinity

  for (const dim of DIMENSIONS) {
    const diff = a[dim.key] - b[dim.key]
    if (diff > maxDiffA) {
      maxDiffA = diff
      bestA = dim.label
    }
    if (-diff > maxDiffB) {
      maxDiffB = -diff
      bestB = dim.label
    }
  }

  if (maxDiffA <= 0 && maxDiffB <= 0) return 'Both simulations perform equally across all dimensions.'
  if (maxDiffA <= 0) return `${props.labelB} outperforms across all dimensions, especially in ${bestB}.`
  if (maxDiffB <= 0) return `${props.labelA} outperforms across all dimensions, especially in ${bestA}.`
  return `${props.labelA} excels at ${bestA}, while ${props.labelB} performs better on ${bestB}.`
})

const dimensionDetail = computed(() => {
  if (!selectedDimension.value) return null
  const dim = DIMENSIONS.find(d => d.key === selectedDimension.value)
  if (!dim) return null
  const valA = seriesA.value[dim.key]
  const valB = seriesB.value[dim.key]
  const diff = Math.abs(valA - valB)
  const winner = valA > valB ? props.labelA : valB > valA ? props.labelB : 'Tie'
  return { label: dim.label, valA, valB, diff, winner }
})

function onDimensionClick(key) {
  selectedDimension.value = selectedDimension.value === key ? null : key
  emit('dimension-click', selectedDimension.value)
}

function renderChart() {
  const container = chartRef.value
  if (!container) return
  d3.select(container).selectAll('*').remove()

  const containerWidth = container.clientWidth
  const size = Math.min(containerWidth, 480)
  const margin = 80
  const radius = (size - margin * 2) / 2
  const cx = containerWidth / 2
  const cy = size / 2
  const totalHeight = size + 16

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const g = svg.append('g')
    .attr('transform', `translate(${cx},${cy})`)

  const angleSlice = (Math.PI * 2) / DIMENSIONS.length
  const rScale = d3.scaleLinear().domain([0, props.maxValue]).range([0, radius])

  // Grid circles
  for (let lvl = 1; lvl <= props.levels; lvl++) {
    const r = (radius / props.levels) * lvl
    g.append('circle')
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', COLORS.grid)
      .attr('stroke-dasharray', '3,3')

    g.append('text')
      .attr('x', 4)
      .attr('y', -r + 3)
      .attr('font-size', '9px')
      .attr('fill', COLORS.gridLabel)
      .text(Math.round((props.maxValue / props.levels) * lvl))
  }

  // Axis spokes + labels
  DIMENSIONS.forEach((dim, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x).attr('y2', y)
      .attr('stroke', COLORS.grid)

    const labelDist = radius + 20
    const lx = Math.cos(angle) * labelDist
    const ly = Math.sin(angle) * labelDist

    const isSelected = selectedDimension.value === dim.key
    g.append('text')
      .attr('x', lx)
      .attr('y', ly)
      .attr('dy', '0.35em')
      .attr('text-anchor', Math.abs(angle + Math.PI / 2) < 0.01 ? 'middle'
        : Math.cos(angle) > 0.01 ? 'start' : 'end')
      .attr('font-size', '11px')
      .attr('font-weight', isSelected ? '700' : '500')
      .attr('fill', isSelected ? COLORS.a : '#555')
      .style('cursor', 'pointer')
      .text(dim.label)
      .on('click', () => onDimensionClick(dim.key))
  })

  // Polygon path generator
  function polygonPoints(data) {
    return DIMENSIONS.map((dim, i) => {
      const angle = angleSlice * i - Math.PI / 2
      const val = Math.min(data[dim.key] || 0, props.maxValue)
      const r = rScale(val)
      return [Math.cos(angle) * r, Math.sin(angle) * r]
    })
  }

  const lineGen = d3.line().curve(d3.curveLinearClosed)

  // Series B polygon (orange, drawn first so A overlays)
  const pointsB = polygonPoints(seriesB.value)
  const pathB = g.append('path')
    .datum(pointsB)
    .attr('d', lineGen(pointsB.map(() => [0, 0])))
    .attr('fill', COLORS.b)
    .attr('fill-opacity', 0.12)
    .attr('stroke', COLORS.b)
    .attr('stroke-width', 2)
    .attr('stroke-opacity', 0.8)

  pathB.transition()
    .duration(700)
    .delay(100)
    .ease(d3.easeCubicOut)
    .attr('d', lineGen(pointsB))

  // Series A polygon (blue)
  const pointsA = polygonPoints(seriesA.value)
  const pathA = g.append('path')
    .datum(pointsA)
    .attr('d', lineGen(pointsA.map(() => [0, 0])))
    .attr('fill', COLORS.a)
    .attr('fill-opacity', 0.12)
    .attr('stroke', COLORS.a)
    .attr('stroke-width', 2)
    .attr('stroke-opacity', 0.8)

  pathA.transition()
    .duration(700)
    .ease(d3.easeCubicOut)
    .attr('d', lineGen(pointsA))

  // Data point dots — Series A
  pointsA.forEach(([x, y], i) => {
    g.append('circle')
      .attr('cx', 0).attr('cy', 0)
      .attr('r', 4)
      .attr('fill', COLORS.a)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .style('cursor', 'pointer')
      .on('click', () => onDimensionClick(DIMENSIONS[i].key))
      .transition()
      .duration(700)
      .ease(d3.easeCubicOut)
      .attr('cx', x).attr('cy', y)
  })

  // Data point dots — Series B
  pointsB.forEach(([x, y], i) => {
    g.append('circle')
      .attr('cx', 0).attr('cy', 0)
      .attr('r', 4)
      .attr('fill', COLORS.b)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .style('cursor', 'pointer')
      .on('click', () => onDimensionClick(DIMENSIONS[i].key))
      .transition()
      .duration(700)
      .delay(100)
      .ease(d3.easeCubicOut)
      .attr('cx', x).attr('cy', y)
  })
}

watch([seriesA, seriesB, selectedDimension], () => {
  nextTick(() => renderChart())
})

onMounted(() => {
  renderChart()
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
    <!-- Header -->
    <div class="mb-4">
      <h3 class="text-sm font-semibold text-[--color-navy]">
        Simulation Comparison
      </h3>
      <p class="text-xs text-[#888] mt-0.5">
        Multi-dimensional performance overlay
      </p>
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-5 mb-4">
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-sm" style="background: #2068FF; opacity: 0.85" />
        <span class="text-xs text-[#555]">{{ labelA }}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-sm" style="background: #ff5600; opacity: 0.85" />
        <span class="text-xs text-[#555]">{{ labelB }}</span>
      </div>
    </div>

    <!-- Chart -->
    <div ref="chartRef" class="w-full" />

    <!-- Summary -->
    <p class="text-xs text-[#555] mt-3 italic">
      {{ summaryText }}
    </p>

    <!-- Dimension detail breakdown -->
    <transition name="fade">
      <div
        v-if="dimensionDetail"
        class="mt-3 p-3 rounded-md bg-black/[0.03] border border-black/[0.06]"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-[--color-navy]">
            {{ dimensionDetail.label }}
          </span>
          <button
            class="text-xs text-[#888] hover:text-[--color-navy] transition-colors"
            @click="selectedDimension = null"
          >
            Close
          </button>
        </div>
        <div class="grid grid-cols-3 gap-2 text-center">
          <div>
            <div class="text-lg font-bold" style="color: #2068FF">
              {{ dimensionDetail.valA }}
            </div>
            <div class="text-[10px] text-[#888]">{{ labelA }}</div>
          </div>
          <div>
            <div class="text-lg font-bold" style="color: #ff5600">
              {{ dimensionDetail.valB }}
            </div>
            <div class="text-[10px] text-[#888]">{{ labelB }}</div>
          </div>
          <div>
            <div class="text-lg font-bold text-[--color-navy]">
              {{ dimensionDetail.diff.toFixed(1) }}
            </div>
            <div class="text-[10px] text-[#888]">
              Δ ({{ dimensionDetail.winner }})
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
