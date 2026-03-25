<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  type: { type: String, default: 'sparkline', validator: (v) => ['sparkline', 'bar', 'donut'].includes(v) },
  title: { type: String, required: true },
  data: { type: Array, default: () => [] },
  color: { type: String, default: '#2068FF' },
})

const chartRef = ref(null)
let resizeObserver = null

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function render() {
  clearChart()
  if (!chartRef.value || !props.data.length) return
  nextTick(() => {
    if (props.type === 'sparkline') renderSparkline()
    else if (props.type === 'bar') renderBar()
    else if (props.type === 'donut') renderDonut()
  })
}

function renderSparkline() {
  const el = chartRef.value
  const width = el.clientWidth
  const height = el.clientHeight
  const margin = { top: 4, right: 4, bottom: 4, left: 4 }
  const w = width - margin.left - margin.right
  const h = height - margin.top - margin.bottom

  const svg = d3.select(el).append('svg')
    .attr('width', width).attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear().domain([0, props.data.length - 1]).range([0, w])
  const y = d3.scaleLinear().domain([0, d3.max(props.data, d => d.value) || 1]).range([h, 0])

  const area = d3.area()
    .x((d, i) => x(i))
    .y0(h)
    .y1(d => y(d.value))
    .curve(d3.curveMonotoneX)

  const line = d3.line()
    .x((d, i) => x(i))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(props.data)
    .attr('d', area)
    .attr('fill', props.color)
    .attr('fill-opacity', 0.1)

  g.append('path')
    .datum(props.data)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', props.color)
    .attr('stroke-width', 2)

  const last = props.data[props.data.length - 1]
  g.append('circle')
    .attr('cx', x(props.data.length - 1))
    .attr('cy', y(last.value))
    .attr('r', 3)
    .attr('fill', props.color)
}

function renderBar() {
  const el = chartRef.value
  const width = el.clientWidth
  const height = el.clientHeight
  const margin = { top: 4, right: 4, bottom: 16, left: 4 }
  const w = width - margin.left - margin.right
  const h = height - margin.top - margin.bottom

  const svg = d3.select(el).append('svg')
    .attr('width', width).attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleBand().domain(props.data.map(d => d.label)).range([0, w]).padding(0.3)
  const y = d3.scaleLinear().domain([0, d3.max(props.data, d => d.value) || 1]).range([h, 0])

  g.selectAll('rect')
    .data(props.data)
    .join('rect')
    .attr('x', d => x(d.label))
    .attr('y', d => y(d.value))
    .attr('width', x.bandwidth())
    .attr('height', d => h - y(d.value))
    .attr('fill', props.color)
    .attr('rx', 2)

  g.selectAll('.label')
    .data(props.data)
    .join('text')
    .attr('class', 'label')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', h + 12)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted)')
    .text(d => d.label)
}

function renderDonut() {
  const el = chartRef.value
  const width = el.clientWidth
  const height = el.clientHeight
  const radius = Math.min(width, height) / 2 - 4

  const svg = d3.select(el).append('svg')
    .attr('width', width).attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${width / 2},${height / 2})`)

  const colors = ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#f59e0b']
  const color = d3.scaleOrdinal().domain(props.data.map(d => d.label)).range(colors)

  const pie = d3.pie().value(d => d.value).sort(null)
  const arc = d3.arc().innerRadius(radius * 0.55).outerRadius(radius)

  g.selectAll('path')
    .data(pie(props.data))
    .join('path')
    .attr('d', arc)
    .attr('fill', d => color(d.data.label))

  const total = props.data.reduce((s, d) => s + d.value, 0)
  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text)')
    .text(total.toLocaleString())
}

onMounted(() => {
  render()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => render())
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
})

watch(() => props.data, render, { deep: true })
</script>

<template>
  <div class="flex flex-col min-w-[200px] snap-center">
    <div class="text-[11px] font-medium text-[var(--color-text-muted)] mb-1 px-1">{{ title }}</div>
    <div
      ref="chartRef"
      class="w-full h-[80px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden"
    />
  </div>
</template>
