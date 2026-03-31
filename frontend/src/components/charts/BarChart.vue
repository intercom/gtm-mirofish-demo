<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useMobileChart } from '../../composables/useMobileChart'

const {
  isMobile, animationDuration, staggerDelay, fontSize, tickCount,
} = useMobileChart()

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  colors: {
    type: Array,
    default: () => ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#888'],
  },
  height: { type: Number, default: 260 },
  horizontal: { type: Boolean, default: false },
  yFormat: { type: Function, default: (v) => v },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clear() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function isGrouped() {
  return props.data.length > 0 && props.data[0].values != null
}

function render() {
  clear()
  const container = chartRef.value
  if (!container || !props.data.length) return

  if (props.horizontal) {
    renderHorizontal(container)
  } else if (isGrouped()) {
    renderGrouped(container)
  } else {
    renderVertical(container)
  }
}

function renderVertical(container) {
  const containerWidth = container.clientWidth
  const mobile = isMobile.value
  const dur = animationDuration.value
  const stagger = staggerDelay.value
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

  appendTitles(svg, margin)

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3
    .scaleBand()
    .domain(props.data.map((d) => d.label))
    .range([0, width])
    .padding(0.3)

  const yMax = d3.max(props.data, (d) => d.value) * 1.1 || 10
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
    .attr('font-size', fontSize.value.tick)
    .attr('fill', '#aaa')
    .text((d) => props.yFormat(d))

  g.selectAll('.x-label')
    .data(props.data)
    .join('text')
    .attr('x', (d) => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', fontSize.value.tick)
    .attr('fill', '#888')
    .text((d) => {
      if (mobile && d.label.length > 8) return d.label.slice(0, 7) + '\u2026'
      return d.label
    })

  const bars = g.selectAll('.bar')
    .data(props.data)
    .join('rect')
    .attr('x', (d) => x(d.label))
    .attr('width', x.bandwidth())
    .attr('rx', 3)
    .attr('fill', (d, i) => props.colors[i % props.colors.length])
    .attr('opacity', 0.85)

  if (dur > 0) {
    bars
      .attr('y', height)
      .attr('height', 0)
      .transition()
      .duration(dur)
      .delay((d, i) => i * stagger)
      .ease(d3.easeCubicOut)
      .attr('y', (d) => y(d.value))
      .attr('height', (d) => height - y(d.value))
  } else {
    bars
      .attr('y', (d) => y(d.value))
      .attr('height', (d) => height - y(d.value))
  }

  const vals = g.selectAll('.val')
    .data(props.data)
    .join('text')
    .attr('x', (d) => x(d.label) + x.bandwidth() / 2)
    .attr('y', (d) => y(d.value) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', fontSize.value.value)
    .attr('font-weight', '600')
    .attr('fill', '#050505')
    .text((d) => props.yFormat(d.value))

  if (dur > 0) {
    vals
      .style('opacity', 0)
      .transition()
      .duration(dur / 2)
      .delay((d, i) => dur + i * stagger)
      .style('opacity', 1)
  }
}

function renderHorizontal(container) {
  const containerWidth = container.clientWidth
  const mobile = isMobile.value
  const dur = animationDuration.value
  const stagger = staggerDelay.value
  const hasTitle = props.title || props.subtitle
  const barHeight = mobile ? 28 : 36
  const barGap = mobile ? 8 : 12
  const calcHeight = props.data.length * (barHeight + barGap) - barGap
  const margin = mobile
    ? { top: hasTitle ? 40 : 12, right: 40, bottom: 20, left: 72 }
    : { top: hasTitle ? 52 : 16, right: 60, bottom: 24, left: 100 }
  const width = containerWidth - margin.left - margin.right
  const totalHeight = calcHeight + margin.top + margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  appendTitles(svg, margin)

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const xMax = d3.max(props.data, (d) => d.value) * 1.2 || 10
  const x = d3.scaleLinear().domain([0, xMax]).nice().range([0, width])
  const y = d3
    .scaleBand()
    .domain(props.data.map((d) => d.label))
    .range([0, calcHeight])
    .padding(barGap / (barHeight + barGap))

  const xTicks = x.ticks(tickCount.value)
  g.selectAll('.grid')
    .data(xTicks)
    .join('line')
    .attr('x1', (d) => x(d))
    .attr('x2', (d) => x(d))
    .attr('y1', 0)
    .attr('y2', calcHeight)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', (d) => x(d))
    .attr('y', calcHeight + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', fontSize.value.tick)
    .attr('fill', '#aaa')
    .text((d) => props.yFormat(d))

  g.selectAll('.bar-label')
    .data(props.data)
    .join('text')
    .attr('x', -8)
    .attr('y', (d) => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', fontSize.value.label)
    .attr('fill', '#555')
    .text((d) => {
      if (mobile && d.label.length > 10) return d.label.slice(0, 9) + '\u2026'
      return d.label
    })

  g.selectAll('.bar-bg')
    .data(props.data)
    .join('rect')
    .attr('x', 0)
    .attr('y', (d) => y(d.label))
    .attr('width', width)
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', 'rgba(0,0,0,0.03)')

  const bars = g.selectAll('.bar')
    .data(props.data)
    .join('rect')
    .attr('x', 0)
    .attr('y', (d) => y(d.label))
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', (d, i) => props.colors[i % props.colors.length])
    .attr('opacity', 0.85)

  if (dur > 0) {
    bars
      .attr('width', 0)
      .transition()
      .duration(dur)
      .delay((d, i) => i * stagger)
      .ease(d3.easeCubicOut)
      .attr('width', (d) => x(d.value))
  } else {
    bars.attr('width', (d) => x(d.value))
  }

  const vals = g.selectAll('.bar-value')
    .data(props.data)
    .join('text')
    .attr('x', (d) => x(d.value) + 8)
    .attr('y', (d) => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('font-size', fontSize.value.label)
    .attr('font-weight', '600')
    .attr('fill', '#050505')
    .text((d) => props.yFormat(d.value))

  if (dur > 0) {
    vals
      .style('opacity', 0)
      .transition()
      .duration(dur / 2)
      .delay((d, i) => dur + i * stagger)
      .style('opacity', 1)
  }
}

function renderGrouped(container) {
  const containerWidth = container.clientWidth
  const mobile = isMobile.value
  const dur = animationDuration.value
  const stagger = staggerDelay.value
  const hasTitle = props.title || props.subtitle
  const margin = mobile
    ? { top: hasTitle ? 40 : 12, right: 16, bottom: 48, left: 36 }
    : { top: hasTitle ? 52 : 16, right: 24, bottom: 60, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = mobile ? Math.min(props.height, 200) : props.height
  const totalHeight = height + margin.top + margin.bottom

  const groupKeys = Object.keys(props.data[0].values)

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  appendTitles(svg, margin)

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x0 = d3
    .scaleBand()
    .domain(props.data.map((d) => d.label))
    .range([0, width])
    .paddingInner(0.3)
    .paddingOuter(0.15)

  const x1 = d3
    .scaleBand()
    .domain(groupKeys)
    .range([0, x0.bandwidth()])
    .padding(0.1)

  const allVals = props.data.flatMap((d) => Object.values(d.values))
  const yMax = d3.max(allVals) * 1.2 || 10
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
    .attr('font-size', fontSize.value.tick)
    .attr('fill', '#aaa')
    .text((d) => props.yFormat(d))

  g.selectAll('.x-label')
    .data(props.data)
    .join('text')
    .attr('x', (d) => x0(d.label) + x0.bandwidth() / 2)
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', fontSize.value.tick)
    .attr('fill', '#888')
    .text((d) => {
      if (mobile && d.label.length > 8) return d.label.slice(0, 7) + '\u2026'
      return d.label
    })

  const groups = g
    .selectAll('.group')
    .data(props.data)
    .join('g')
    .attr('transform', (d) => `translate(${x0(d.label)},0)`)

  groupKeys.forEach((key, ki) => {
    const color = props.colors[ki % props.colors.length]

    const rects = groups
      .append('rect')
      .attr('x', x1(key))
      .attr('width', x1.bandwidth())
      .attr('rx', 3)
      .attr('fill', color)
      .attr('opacity', 0.85)

    if (dur > 0) {
      rects
        .attr('y', height)
        .attr('height', 0)
        .transition()
        .duration(dur)
        .delay((d, i) => i * (stagger + 20) + ki * stagger)
        .ease(d3.easeCubicOut)
        .attr('y', (d) => y(d.values[key]))
        .attr('height', (d) => height - y(d.values[key]))
    } else {
      rects
        .attr('y', (d) => y(d.values[key]))
        .attr('height', (d) => height - y(d.values[key]))
    }

    if (!mobile) {
      const labels = groups
        .append('text')
        .attr('x', x1(key) + x1.bandwidth() / 2)
        .attr('y', (d) => y(d.values[key]) - 6)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', color)
        .text((d) => props.yFormat(d.values[key]))

      if (dur > 0) {
        labels
          .style('opacity', 0)
          .transition()
          .duration(dur / 2)
          .delay((d, i) => dur + i * (stagger + 20))
          .style('opacity', 1)
      }
    }
  })

  // Legend
  const legend = svg
    .append('g')
    .attr(
      'transform',
      `translate(${containerWidth - margin.right}, ${hasTitle ? 14 : 4})`,
    )

  let offsetX = 0
  groupKeys.forEach((key, i) => {
    const color = props.colors[i % props.colors.length]
    const textWidth = key.length * 7 + 20

    legend
      .append('rect')
      .attr('x', -offsetX - textWidth)
      .attr('y', 0)
      .attr('width', 10)
      .attr('height', 10)
      .attr('rx', 2)
      .attr('fill', color)
      .attr('opacity', 0.85)

    legend
      .append('text')
      .attr('x', -offsetX - textWidth + 16)
      .attr('y', 9)
      .attr('font-size', fontSize.value.value)
      .attr('fill', '#555')
      .text(key)

    offsetX += textWidth + 12
  })
}

function appendTitles(svg, margin) {
  const fs = fontSize.value
  if (props.title) {
    svg
      .append('text')
      .attr('x', margin.left)
      .attr('y', isMobile.value ? 16 : 22)
      .attr('font-size', fs.title)
      .attr('font-weight', '600')
      .attr('fill', '#050505')
      .text(props.title)
  }
  if (props.subtitle) {
    svg
      .append('text')
      .attr('x', margin.left)
      .attr('y', isMobile.value ? 30 : 40)
      .attr('font-size', fs.subtitle)
      .attr('fill', '#888')
      .text(props.subtitle)
  }
}

watch(
  () => [props.data, props.colors, props.height, props.horizontal],
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
  <div
    ref="chartRef"
    class="w-full"
    role="img"
    :aria-label="title ? `${title} bar chart` : 'Bar chart'"
  />
  <table v-if="data.length" class="sr-only">
    <caption>{{ title || 'Bar chart data' }}</caption>
    <thead><tr><th scope="col">Label</th><th scope="col">Value</th></tr></thead>
    <tbody>
      <tr v-for="d in data" :key="d.label">
        <td>{{ d.label }}</td>
        <td>{{ d.value }}</td>
      </tr>
    </tbody>
  </table>
</template>
