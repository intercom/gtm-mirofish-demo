<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, toRef } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  series: {
    type: Array,
    required: true,
    // [{ name: 'Revenue', points: [{ x: 'Jan', y: 120 }, ...] }, ...]
  },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  colors: {
    type: Array,
    default: () => ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#888'],
  },
  height: { type: Number, default: 280 },
  yFormat: { type: Function, default: (v) => v },
  curved: { type: Boolean, default: true },
  showDots: { type: Boolean, default: true },
  showArea: { type: Boolean, default: false },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clear() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function render() {
  clear()
  const container = chartRef.value
  if (!container || !props.series.length) return

  const allPoints = props.series.flatMap((s) => s.points)
  if (!allPoints.length) return

  const containerWidth = container.clientWidth
  const hasTitle = props.title || props.subtitle
  const margin = {
    top: hasTitle ? 52 : 16,
    right: 24,
    bottom: 40,
    left: 48,
  }
  const width = containerWidth - margin.left - margin.right
  const height = props.height
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  if (props.title) {
    svg
      .append('text')
      .attr('x', margin.left)
      .attr('y', 22)
      .attr('font-size', '14px')
      .attr('font-weight', '600')
      .attr('fill', '#050505')
      .text(props.title)
  }
  if (props.subtitle) {
    svg
      .append('text')
      .attr('x', margin.left)
      .attr('y', 40)
      .attr('font-size', '11px')
      .attr('fill', '#888')
      .text(props.subtitle)
  }

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Determine if x values are numeric or categorical
  const xVals = allPoints.map((p) => p.x)
  const isNumeric = xVals.every((v) => typeof v === 'number')

  const x = isNumeric
    ? d3
        .scaleLinear()
        .domain(d3.extent(xVals))
        .range([0, width])
    : d3
        .scalePoint()
        .domain([...new Set(props.series[0].points.map((p) => p.x))])
        .range([0, width])
        .padding(0.1)

  const yMax = d3.max(allPoints, (p) => p.y) * 1.1 || 10
  const y = d3.scaleLinear().domain([0, yMax]).nice().range([height, 0])

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', (d) => y(d))
    .attr('y2', (d) => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', (d) => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text((d) => props.yFormat(d))

  // X-axis labels
  const xTicks = isNumeric ? x.ticks(6) : x.domain()
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', (d) => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text((d) => d)

  // Baseline
  g.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', height)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.1)')

  const curveType = props.curved ? d3.curveMonotoneX : d3.curveLinear

  // Draw each series
  props.series.forEach((series, si) => {
    const color = props.colors[si % props.colors.length]
    const lineGen = d3
      .line()
      .x((d) => x(d.x))
      .y((d) => y(d.y))
      .curve(curveType)

    // Optional area fill
    if (props.showArea) {
      const areaGen = d3
        .area()
        .x((d) => x(d.x))
        .y0(height)
        .y1((d) => y(d.y))
        .curve(curveType)

      g.append('path')
        .datum(series.points)
        .attr('fill', color)
        .attr('opacity', 0)
        .attr('d', areaGen)
        .transition()
        .duration(600)
        .delay(si * 100)
        .attr('opacity', 0.08)
    }

    // Line path with draw animation
    const path = g
      .append('path')
      .datum(series.points)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2.5)
      .attr('stroke-linejoin', 'round')
      .attr('stroke-linecap', 'round')
      .attr('d', lineGen)

    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .delay(si * 100)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Dots
    if (props.showDots) {
      g.selectAll(`.dot-${si}`)
        .data(series.points)
        .join('circle')
        .attr('cx', (d) => x(d.x))
        .attr('cy', (d) => y(d.y))
        .attr('r', 0)
        .attr('fill', '#fff')
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .transition()
        .duration(300)
        .delay((d, i) => 800 + si * 100 + i * 40)
        .attr('r', 3.5)
    }
  })

  // Legend (if multiple series)
  if (props.series.length > 1) {
    const legend = svg
      .append('g')
      .attr(
        'transform',
        `translate(${containerWidth - margin.right}, ${hasTitle ? 14 : 4})`,
      )

    let offsetX = 0
    props.series.forEach((s, i) => {
      const color = props.colors[i % props.colors.length]
      const textWidth = s.name.length * 7 + 24

      legend
        .append('line')
        .attr('x1', -offsetX - textWidth + 4)
        .attr('x2', -offsetX - textWidth + 18)
        .attr('y1', 6)
        .attr('y2', 6)
        .attr('stroke', color)
        .attr('stroke-width', 2.5)
        .attr('stroke-linecap', 'round')

      legend
        .append('text')
        .attr('x', -offsetX - textWidth + 24)
        .attr('y', 10)
        .attr('font-size', '11px')
        .attr('fill', '#555')
        .text(s.name)

      offsetX += textWidth + 12
    })
  }
}

watch(
  () => [props.series, props.colors, props.height],
  () => nextTick(render),
  { deep: true },
)

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
  <div
    ref="chartRef"
    class="w-full"
    role="img"
    :aria-label="title ? `${title} line chart` : 'Line chart'"
  />
  <table v-if="series.length" class="sr-only">
    <caption>{{ title || 'Line chart data' }}</caption>
    <thead>
      <tr>
        <th scope="col">X</th>
        <th v-for="s in series" :key="s.name" scope="col">{{ s.name }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(point, i) in series[0]?.points || []" :key="i">
        <td>{{ point.x }}</td>
        <td v-for="s in series" :key="s.name">{{ s.points[i]?.y }}</td>
      </tr>
    </tbody>
  </table>
</template>
