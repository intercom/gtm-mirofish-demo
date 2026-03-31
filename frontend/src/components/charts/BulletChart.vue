<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useMobileChart } from '../../composables/useMobileChart'

const {
  isMobile, animationDuration, staggerDelay, fontSize,
} = useMobileChart()

const props = defineProps({
  metrics: {
    type: Array,
    default: () => [],
  },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  text: '#050505',
  target: '#ef4444',
  rangeBands: ['rgba(0,0,0,0.18)', 'rgba(0,0,0,0.10)', 'rgba(0,0,0,0.04)'],
  poor: '#ef4444',
  ok: '#f59e0b',
  good: '#009900',
}

function getActualColor(actual, ranges) {
  if (actual < ranges[0]) return COLORS.poor
  if (actual < ranges[1]) return COLORS.ok
  return COLORS.good
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function render() {
  clearChart()
  const container = chartRef.value
  if (!container || !props.metrics.length) return

  const mobile = isMobile.value
  const dur = animationDuration.value
  const stagger = staggerDelay.value
  const containerWidth = container.clientWidth
  const labelWidth = mobile
    ? Math.min(80, containerWidth * 0.2)
    : Math.min(140, containerWidth * 0.25)
  const fs = fontSize.value
  const margin = {
    top: props.title ? (mobile ? 40 : 52) : 12,
    right: mobile ? 24 : 32,
    bottom: 12,
    left: labelWidth + 16,
  }
  const width = containerWidth - margin.left - margin.right
  const rowHeight = mobile ? 22 : 28
  const rowGap = mobile ? 10 : 16
  const height = props.metrics.length * (rowHeight + rowGap) - rowGap
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  if (props.title) {
    svg.append('text')
      .attr('x', margin.left)
      .attr('y', mobile ? 16 : 22)
      .attr('font-size', fs.title)
      .attr('font-weight', '600')
      .attr('fill', COLORS.text)
      .text(props.title)
  }

  if (props.subtitle) {
    svg.append('text')
      .attr('x', margin.left)
      .attr('y', mobile ? 30 : 40)
      .attr('font-size', fs.subtitle)
      .attr('fill', '#888')
      .text(props.subtitle)
  }

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxValue = d3.max(props.metrics, d => d.ranges[2])

  const x = d3.scaleLinear()
    .domain([0, maxValue])
    .range([0, width])

  props.metrics.forEach((metric, i) => {
    const y = i * (rowHeight + rowGap)
    const row = g.append('g')
      .attr('transform', `translate(0,${y})`)

    // Label (truncated to fit)
    const label = svg.append('text')
      .attr('x', margin.left - 12)
      .attr('y', margin.top + y + rowHeight / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-size', fs.label)
      .attr('fill', '#555')

    const labelText = metric.label
    label.text(labelText)
    while (label.node().getComputedTextLength() > labelWidth && label.text().length > 3) {
      label.text(label.text().slice(0, -4) + '...')
    }

    // Range bands
    const bandData = [
      { value: metric.ranges[2], fill: COLORS.rangeBands[2] },
      { value: metric.ranges[1], fill: COLORS.rangeBands[1] },
      { value: metric.ranges[0], fill: COLORS.rangeBands[0] },
    ]

    bandData.forEach((band) => {
      const rect = row.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('height', rowHeight)
        .attr('rx', 3)
        .attr('fill', band.fill)

      if (dur > 0) {
        rect.attr('width', 0)
          .transition().duration(dur * 0.6).delay(i * stagger)
          .ease(d3.easeCubicOut)
          .attr('width', x(band.value))
      } else {
        rect.attr('width', x(band.value))
      }
    })

    // Actual value bar
    const barHeight = rowHeight * 0.45
    const barY = (rowHeight - barHeight) / 2
    const actualColor = getActualColor(metric.actual, metric.ranges)

    const actualBar = row.append('rect')
      .attr('x', 0)
      .attr('y', barY)
      .attr('height', barHeight)
      .attr('rx', 2)
      .attr('fill', actualColor)
      .attr('opacity', 0.9)

    if (dur > 0) {
      actualBar.attr('width', 0)
        .transition().duration(dur).delay(i * stagger + dur * 0.3)
        .ease(d3.easeCubicOut)
        .attr('width', x(Math.min(metric.actual, metric.ranges[2])))
    } else {
      actualBar.attr('width', x(Math.min(metric.actual, metric.ranges[2])))
    }

    // Target marker
    const markerWidth = 2.5
    const marker = row.append('rect')
      .attr('x', x(metric.target) - markerWidth / 2)
      .attr('y', rowHeight * 0.1)
      .attr('width', markerWidth)
      .attr('height', rowHeight * 0.8)
      .attr('rx', 1)
      .attr('fill', COLORS.target)

    if (dur > 0) {
      marker.style('opacity', 0)
        .transition().duration(dur / 2).delay(i * stagger + dur * 0.8)
        .style('opacity', 1)
    }

    // Value label
    const valLabel = row.append('text')
      .attr('x', width + 8)
      .attr('y', rowHeight / 2)
      .attr('dy', '0.35em')
      .attr('font-size', fs.value)
      .attr('font-weight', '600')
      .attr('fill', actualColor)
      .text(formatValue(metric.actual, metric.target))

    if (dur > 0) {
      valLabel.style('opacity', 0)
        .transition().duration(dur / 2).delay(i * stagger + dur)
        .style('opacity', 1)
    }
  })
}

function formatValue(actual, target) {
  if (target === 0) return `${actual}`
  const pct = Math.round((actual / target) * 100)
  return `${pct}%`
}

watch(() => props.metrics, () => nextTick(render), { deep: true })

watch(isMobile, () => nextTick(render))

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(render, 200)
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
    <div
      ref="chartRef"
      class="w-full"
      role="img"
      :aria-label="title ? `${title} bullet chart` : 'Bullet chart'"
    />
    <table v-if="metrics.length" class="sr-only">
      <caption>{{ title || 'Bullet chart data' }}</caption>
      <thead><tr><th scope="col">Metric</th><th scope="col">Actual</th><th scope="col">Target</th></tr></thead>
      <tbody>
        <tr v-for="m in metrics" :key="m.label">
          <td>{{ m.label }}</td>
          <td>{{ m.actual }}</td>
          <td>{{ m.target }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
