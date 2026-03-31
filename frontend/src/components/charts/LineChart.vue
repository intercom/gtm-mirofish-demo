<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useMobileChart } from '../../composables/useMobileChart'

const {
  isMobile, animationDuration, staggerDelay, fontSize, tickCount,
} = useMobileChart()

const props = defineProps({
  series: {
    type: Array,
    required: true,
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

  const mobile = isMobile.value
  const dur = animationDuration.value
  const containerWidth = container.clientWidth
  const hasTitle = props.title || props.subtitle
  const margin = mobile
    ? { top: hasTitle ? 40 : 12, right: 16, bottom: 32, left: 36 }
    : { top: hasTitle ? 52 : 16, right: 24, bottom: 40, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = mobile ? Math.min(props.height, 200) : props.height
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const fs = fontSize.value
  if (props.title) {
    svg
      .append('text')
      .attr('x', margin.left)
      .attr('y', mobile ? 16 : 22)
      .attr('font-size', fs.title)
      .attr('font-weight', '600')
      .attr('fill', '#050505')
      .text(props.title)
  }
  if (props.subtitle) {
    svg
      .append('text')
      .attr('x', margin.left)
      .attr('y', mobile ? 30 : 40)
      .attr('font-size', fs.subtitle)
      .attr('fill', '#888')
      .text(props.subtitle)
  }

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

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

  const yTicks = y.ticks(tickCount.value)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', (d) => y(d))
    .attr('y2', (d) => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', (d) => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', fs.tick)
    .attr('fill', '#aaa')
    .text((d) => props.yFormat(d))

  const xTickCount = mobile ? 4 : 6
  const xTicks = isNumeric ? x.ticks(xTickCount) : x.domain()
  // On mobile with many categorical labels, show every Nth
  const xTickData = mobile && !isNumeric && xTicks.length > 5
    ? xTicks.filter((_, i) => i % Math.ceil(xTicks.length / 5) === 0)
    : xTicks

  g.selectAll('.x-label')
    .data(xTickData)
    .join('text')
    .attr('x', (d) => x(d))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', fs.tick)
    .attr('fill', '#aaa')
    .text((d) => d)

  g.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', height)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.1)')

  const curveType = props.curved ? d3.curveMonotoneX : d3.curveLinear
  // On mobile with many data points, skip dots to reduce DOM nodes
  const shouldShowDots = props.showDots && (!mobile || props.series[0].points.length <= 12)

  props.series.forEach((series, si) => {
    const color = props.colors[si % props.colors.length]
    const lineGen = d3
      .line()
      .x((d) => x(d.x))
      .y((d) => y(d.y))
      .curve(curveType)

    if (props.showArea) {
      const areaGen = d3
        .area()
        .x((d) => x(d.x))
        .y0(height)
        .y1((d) => y(d.y))
        .curve(curveType)

      const area = g.append('path')
        .datum(series.points)
        .attr('fill', color)
        .attr('d', areaGen)

      if (dur > 0) {
        area
          .attr('opacity', 0)
          .transition()
          .duration(dur)
          .delay(si * 100)
          .attr('opacity', 0.08)
      } else {
        area.attr('opacity', 0.08)
      }
    }

    const path = g
      .append('path')
      .datum(series.points)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', mobile ? 2 : 2.5)
      .attr('stroke-linejoin', 'round')
      .attr('stroke-linecap', 'round')
      .attr('d', lineGen)

    if (dur > 0) {
      const totalLength = path.node().getTotalLength()
      path
        .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
        .attr('stroke-dashoffset', totalLength)
        .transition()
        .duration(dur + 200)
        .delay(si * 100)
        .ease(d3.easeCubicOut)
        .attr('stroke-dashoffset', 0)
    }

    if (shouldShowDots) {
      const dots = g.selectAll(`.dot-${si}`)
        .data(series.points)
        .join('circle')
        .attr('cx', (d) => x(d.x))
        .attr('cy', (d) => y(d.y))
        .attr('fill', '#fff')
        .attr('stroke', color)
        .attr('stroke-width', mobile ? 1.5 : 2)

      if (dur > 0) {
        dots
          .attr('r', 0)
          .transition()
          .duration(dur / 2)
          .delay((d, i) => dur + 200 + si * 100 + i * (mobile ? 20 : 40))
          .attr('r', mobile ? 2.5 : 3.5)
      } else {
        dots.attr('r', mobile ? 2.5 : 3.5)
      }
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
        .attr('font-size', fontSize.value.value)
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
  <div ref="chartRef" class="w-full" />
</template>
