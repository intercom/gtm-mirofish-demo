<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, select } from 'd3'

const svgRef = ref(null)
let sim = null
let pulseTimer = null

const BRAND = ['#2068FF', '#ff5600', '#AA00FF', '#009900']

function init() {
  const { width, height } = svgRef.value.parentElement.getBoundingClientRect()
  const svg = select(svgRef.value).attr('viewBox', [0, 0, width, height])

  const nodes = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    r: 3 + Math.random() * 7,
    color: BRAND[i % BRAND.length],
  }))

  const linkData = []
  const seen = new Set()
  while (linkData.length < 42) {
    const s = Math.floor(Math.random() * 30)
    const t = Math.floor(Math.random() * 30)
    const key = `${Math.min(s, t)}-${Math.max(s, t)}`
    if (s !== t && !seen.has(key)) {
      seen.add(key)
      linkData.push({ source: s, target: t })
    }
  }

  const links = svg.append('g').selectAll('line').data(linkData).join('line')
    .style('stroke', 'rgba(128,128,128,0.2)')
    .style('stroke-width', 1)

  const nodeEls = svg.append('g').selectAll('circle').data(nodes).join('circle')
    .attr('r', 0)
    .attr('fill', d => d.color)
    .attr('opacity', 0.85)

  nodeEls.transition().duration(600).delay((_, i) => i * 30)
    .attr('r', d => d.r)

  sim = forceSimulation(nodes)
    .force('link', forceLink(linkData).id(d => d.id).distance(50))
    .force('charge', forceManyBody().strength(-28))
    .force('center', forceCenter(width / 2, height / 2))
    .force('collide', forceCollide(d => d.r + 3))
    .on('tick', () => {
      links.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
           .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      nodeEls.attr('cx', d => d.x).attr('cy', d => d.y)
    })

  pulseTimer = setInterval(() => {
    const shuffled = [...linkData].sort(() => Math.random() - 0.5)
    const picked = shuffled.slice(0, 5)
    links.filter(d => picked.includes(d))
      .transition().duration(400)
      .style('stroke', '#2068FF').style('stroke-width', 2.5)
      .transition().duration(700)
      .style('stroke', 'rgba(128,128,128,0.2)').style('stroke-width', 1)
  }, 2000)
}

onMounted(() => svgRef.value && init())
onUnmounted(() => {
  sim?.stop()
  if (pulseTimer) clearInterval(pulseTimer)
})
</script>

<template>
  <svg ref="svgRef" class="w-full h-full" />
</template>
