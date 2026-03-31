<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { forceSimulation, forceX, forceY, forceManyBody, forceCollide, scaleSqrt, select } from 'd3'

const svgRef = ref(null)
let sim = null

const METRICS = [
  { label: 'Twitter', value: 85, color: '#2068FF' },
  { label: 'Reddit', value: 62, color: '#ff5600' },
  { label: 'Email', value: 48, color: '#AA00FF' },
  { label: 'LinkedIn', value: 40, color: '#009900' },
  { label: 'Slack', value: 30, color: '#2068FF' },
  { label: 'Discord', value: 24, color: '#ff5600' },
  { label: 'HN', value: 18, color: '#AA00FF' },
]

function init() {
  const { width, height } = svgRef.value.parentElement.getBoundingClientRect()
  const svg = select(svgRef.value).attr('viewBox', [0, 0, width, height])
  const rScale = scaleSqrt().domain([0, 100]).range([16, 48])

  const nodes = METRICS.map(m => ({
    ...m,
    r: rScale(m.value),
    x: width / 2 + (Math.random() - 0.5) * 80,
    y: height / 2 + (Math.random() - 0.5) * 80,
  }))

  const groups = svg.selectAll('g').data(nodes).join('g')

  groups.append('circle')
    .attr('r', 0)
    .attr('fill', d => d.color)
    .attr('opacity', 0.75)
    .transition().duration(700).delay((_, i) => i * 80)
    .attr('r', d => d.r)

  groups.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .style('fill', 'white')
    .style('font-size', d => `${Math.max(10, d.r / 3)}px`)
    .style('font-weight', '600')
    .style('pointer-events', 'none')
    .text(d => d.label)
    .attr('opacity', 0)
    .transition().duration(500).delay((_, i) => i * 80 + 400)
    .attr('opacity', 1)

  groups.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.1em')
    .style('fill', 'rgba(255,255,255,0.75)')
    .style('font-size', d => `${Math.max(9, d.r / 3.5)}px`)
    .style('pointer-events', 'none')
    .text(d => `${d.value}%`)
    .attr('opacity', 0)
    .transition().duration(500).delay((_, i) => i * 80 + 400)
    .attr('opacity', 1)

  sim = forceSimulation(nodes)
    .force('x', forceX(width / 2).strength(0.03))
    .force('y', forceY(height / 2).strength(0.03))
    .force('charge', forceManyBody().strength(3))
    .force('collide', forceCollide(d => d.r + 4).strength(0.8))
    .alphaDecay(0.005)
    .on('tick', () => {
      groups.attr('transform', d => `translate(${d.x},${d.y})`)
    })
}

onMounted(() => svgRef.value && init())
onUnmounted(() => sim?.stop())
</script>

<template>
  <svg ref="svgRef" class="w-full h-full" />
</template>
