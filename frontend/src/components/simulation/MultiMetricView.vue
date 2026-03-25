<script setup>
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useTimelineScrubberInject } from '../../composables/useTimelineScrubber'

const props = defineProps({
  timeline: { type: Array, default: () => [] },
  actions: { type: Array, default: () => [] },
})

const scrubber = useTimelineScrubberInject()
const containerRef = ref(null)
let resizeObserver = null

const metrics = computed(() => {
  const tl = props.timeline
  if (!tl.length) return []

  return [
    {
      key: 'engagement',
      label: 'Engagement',
      color: '#2068FF',
      data: tl.map(r => ({
        round: r.round_num,
        value: (r.twitter_actions || 0) + (r.reddit_actions || 0),
      })),
    },
    {
      key: 'twitter',
      label: 'Twitter',
      color: '#2068FF',
      data: tl.map(r => ({ round: r.round_num, value: r.twitter_actions || 0 })),
    },
    {
      key: 'reddit',
      label: 'Reddit',
      color: '#ff5600',
      data: tl.map(r => ({ round: r.round_num, value: r.reddit_actions || 0 })),
    },
  ]
})

const currentValues = computed(() => {
  if (!scrubber) return {}
  const round = scrubber.currentRound.value
  const result = {}
  for (const metric of metrics.value) {
    const entry = metric.data.find(d => d.round === round)
    result[metric.key] = entry?.value ?? 0
  }
  return result
})

function renderSparklines() {
  const container = containerRef.value
  if (!container) return

  container.querySelectorAll('.sparkline-svg').forEach(el => el.remove())

  for (const metric of metrics.value) {
    const sparkContainer = container.querySelector(`[data-sparkline="${metric.key}"]`)
    if (!sparkContainer) continue

    const width = sparkContainer.clientWidth
    const height = 32
    if (width === 0) return

    const data = metric.data
    if (data.length < 2) continue

    const svg = d3.select(sparkContainer)
      .append('svg')
      .attr('class', 'sparkline-svg')
      .attr('width', width)
      .attr('height', height)

    const x = d3.scaleLinear()
      .domain([data[0].round, data[data.length - 1].round])
      .range([4, width - 4])

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value) || 1])
      .range([height - 4, 4])

    const area = d3.area()
      .x(d => x(d.round))
      .y0(height)
      .y1(d => y(d.value))
      .curve(d3.curveMonotoneX)

    svg.append('path')
      .datum(data)
      .attr('d', area)
      .attr('fill', metric.color)
      .attr('fill-opacity', 0.08)

    const line = d3.line()
      .x(d => x(d.round))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX)

    svg.append('path')
      .datum(data)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', metric.color)
      .attr('stroke-width', 1.5)

    if (scrubber) {
      const cr = scrubber.currentRound.value
      const cx = x(cr)
      const entry = data.find(d => d.round === cr)

      svg.append('line')
        .attr('x1', cx).attr('y1', 0)
        .attr('x2', cx).attr('y2', height)
        .attr('stroke', metric.color)
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '2,2')
        .attr('opacity', 0.5)

      if (entry) {
        svg.append('circle')
          .attr('cx', cx)
          .attr('cy', y(entry.value))
          .attr('r', 3)
          .attr('fill', metric.color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.5)
      }
    }
  }
}

watch(
  [() => props.timeline.length, () => scrubber?.currentRound.value],
  () => nextTick(renderSparklines),
)

onMounted(() => {
  renderSparklines()
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => renderSparklines())
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div ref="containerRef" class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
    <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">
      Multi-Metric Overview
      <span v-if="scrubber" class="text-xs font-normal text-[var(--color-text-muted)] ml-2">
        Round {{ scrubber.currentRound.value }}
      </span>
    </h3>
    <div v-if="metrics.length" class="space-y-2">
      <div
        v-for="metric in metrics"
        :key="metric.key"
        class="flex items-center gap-3"
      >
        <span class="text-[11px] text-[var(--color-text-muted)] w-20 shrink-0">{{ metric.label }}</span>
        <div :data-sparkline="metric.key" class="flex-1 h-8" />
        <span
          class="text-sm font-semibold tabular-nums w-10 text-right"
          :style="{ color: metric.color }"
        >
          {{ currentValues[metric.key] ?? 0 }}
        </span>
      </div>
    </div>
    <div v-else class="flex items-center justify-center h-20 text-[var(--color-text-muted)] text-sm">
      No timeline data yet
    </div>
  </div>
</template>
