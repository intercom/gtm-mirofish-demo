<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useMobileChart } from '../../composables/useMobileChart'

const {
  isMobile, animationDuration, staggerDelay, fontSize,
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
    default: () => ['#2068FF', '#ff5600', '#009900', '#AA00FF', '#888'],
  },
  centerText: { type: String, default: '' },
  centerSubtext: { type: String, default: '' },
  innerRatio: { type: Number, default: 0.55 },
  showLabels: { type: Boolean, default: true },
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
  if (!container || !props.data.length) return

  const mobile = isMobile.value
  const dur = animationDuration.value
  const stagger = staggerDelay.value
  const containerWidth = container.clientWidth
  const hasTitle = props.title || props.subtitle
  const titleOffset = hasTitle ? (mobile ? 40 : 50) : 0
  // On mobile, use a compact legend below instead of connector lines
  const useLegendList = mobile && props.showLabels
  const legendHeight = useLegendList ? props.data.length * 22 + 16 : 0
  const size = Math.min(containerWidth, mobile ? 260 : 400)
  const radius = size / 2 - (mobile ? 20 : 40)
  const innerRadius = radius * props.innerRatio
  const totalHeight = size + titleOffset + legendHeight

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
      .attr('x', containerWidth / 2)
      .attr('y', mobile ? 16 : 22)
      .attr('text-anchor', 'middle')
      .attr('font-size', fs.title)
      .attr('font-weight', '600')
      .attr('fill', '#050505')
      .text(props.title)
  }
  if (props.subtitle) {
    svg
      .append('text')
      .attr('x', containerWidth / 2)
      .attr('y', mobile ? 30 : 40)
      .attr('text-anchor', 'middle')
      .attr('font-size', fs.subtitle)
      .attr('fill', '#888')
      .text(props.subtitle)
  }

  const g = svg
    .append('g')
    .attr(
      'transform',
      `translate(${containerWidth / 2},${size / 2 + titleOffset})`,
    )

  const pie = d3.pie().value((d) => d.value).sort(null).padAngle(0.02)

  const arc = d3
    .arc()
    .innerRadius(innerRadius)
    .outerRadius(radius)
    .cornerRadius(mobile ? 2 : 4)

  const arcs = pie(props.data)

  // Animated arcs
  const paths = g.selectAll('.arc')
    .data(arcs)
    .join('path')
    .attr('fill', (d, i) => props.colors[i % props.colors.length])
    .attr('opacity', 0.85)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)

  if (dur > 0) {
    paths
      .transition()
      .duration(dur)
      .delay((d, i) => i * stagger)
      .ease(d3.easeCubicOut)
      .attrTween('d', function (d) {
        const interp = d3.interpolate(
          { startAngle: d.startAngle, endAngle: d.startAngle },
          d,
        )
        return (t) => arc(interp(t))
      })
  } else {
    paths.attr('d', arc)
  }

  // Center text
  if (props.centerText) {
    const ct = g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', props.centerSubtext ? '-0.2em' : '0.35em')
      .attr('font-size', mobile ? '20px' : '24px')
      .attr('font-weight', '700')
      .attr('fill', '#050505')
      .text(props.centerText)

    if (dur > 0) {
      ct.style('opacity', 0)
        .transition().duration(dur * 0.6).delay(dur)
        .style('opacity', 1)
    }
  }

  if (props.centerSubtext) {
    const cs = g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.2em')
      .attr('font-size', fs.subtitle)
      .attr('fill', '#888')
      .text(props.centerSubtext)

    if (dur > 0) {
      cs.style('opacity', 0)
        .transition().duration(dur * 0.6).delay(dur + 50)
        .style('opacity', 1)
    }
  }

  // Labels: on mobile use a legend list below, on desktop use connector lines
  if (props.showLabels) {
    if (useLegendList) {
      renderMobileLegend(svg, containerWidth, size + titleOffset, dur)
    } else {
      renderConnectorLabels(g, arc, arcs, radius, dur, stagger)
    }
  }
}

function renderMobileLegend(svg, containerWidth, yStart, dur) {
  const legendG = svg.append('g')
    .attr('transform', `translate(16,${yStart + 8})`)

  props.data.forEach((d, i) => {
    const row = legendG.append('g')
      .attr('transform', `translate(0,${i * 22})`)

    row.append('rect')
      .attr('width', 10).attr('height', 10)
      .attr('rx', 2)
      .attr('fill', props.colors[i % props.colors.length])
      .attr('opacity', 0.85)

    row.append('text')
      .attr('x', 16).attr('y', 9)
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(d.label)

    row.append('text')
      .attr('x', containerWidth - 32).attr('y', 9)
      .attr('text-anchor', 'end')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', props.colors[i % props.colors.length])
      .text(d.value)

    if (dur > 0) {
      row.style('opacity', 0)
        .transition().duration(dur / 2).delay(dur + i * 40)
        .style('opacity', 1)
    }
  })
}

function renderConnectorLabels(g, arc, arcs, radius, dur, stagger) {
  const labelArc = d3
    .arc()
    .innerRadius(radius + 16)
    .outerRadius(radius + 16)

  const labelGroups = g
    .selectAll('.label-group')
    .data(arcs)
    .join('g')

  labelGroups.each(function (d, i) {
    const group = d3.select(this)
    const pos = labelArc.centroid(d)
    const midAngle = (d.startAngle + d.endAngle) / 2
    const isRight = midAngle < Math.PI
    const xOffset = isRight ? 12 : -12
    const color = props.colors[i % props.colors.length]

    const arcMid = arc.centroid(d)
    group
      .append('line')
      .attr('x1', arcMid[0] * 1.15)
      .attr('y1', arcMid[1] * 1.15)
      .attr('x2', pos[0] + xOffset)
      .attr('y2', pos[1])
      .attr('stroke', 'rgba(0,0,0,0.15)')
      .attr('stroke-width', 1)

    group
      .append('text')
      .attr('x', pos[0] + xOffset * 2)
      .attr('y', pos[1])
      .attr('dy', '-0.3em')
      .attr('text-anchor', isRight ? 'start' : 'end')
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(props.data[i].label)

    group
      .append('text')
      .attr('x', pos[0] + xOffset * 2)
      .attr('y', pos[1])
      .attr('dy', '0.9em')
      .attr('text-anchor', isRight ? 'start' : 'end')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', color)
      .text(props.data[i].value)
  })

  if (dur > 0) {
    labelGroups
      .style('opacity', 0)
      .transition()
      .duration(dur / 2)
      .delay((d, i) => dur + i * stagger)
      .style('opacity', 1)
  }
}

watch(
  () => [props.data, props.colors, props.innerRatio],
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
    :aria-label="title ? `${title} donut chart` : 'Donut chart'"
  />
  <table v-if="data.length" class="sr-only">
    <caption>{{ title || 'Donut chart data' }}</caption>
    <thead><tr><th scope="col">Segment</th><th scope="col">Value</th></tr></thead>
    <tbody>
      <tr v-for="d in data" :key="d.label">
        <td>{{ d.label }}</td>
        <td>{{ d.value }}</td>
      </tr>
    </tbody>
  </table>
</template>
