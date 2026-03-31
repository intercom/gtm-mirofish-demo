<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { benchmarkApi } from '../api/benchmark'

const results = ref(null)
const loading = ref(false)
const error = ref(null)
const iterations = ref(10)
const chartEl = ref(null)

async function runBenchmark() {
  loading.value = true
  error.value = null
  results.value = null

  try {
    const { data } = await benchmarkApi.run(iterations.value)
    results.value = data.data
    await nextTick()
    drawChart()
  } catch (err) {
    error.value = err.message || 'Benchmark failed'
  } finally {
    loading.value = false
  }
}

function ratingColor(avgMs) {
  if (avgMs < 50) return '#22c55e'
  if (avgMs < 200) return '#2068FF'
  if (avgMs < 500) return '#f59e0b'
  return '#ef4444'
}

function ratingLabel(avgMs) {
  if (avgMs < 50) return 'Excellent'
  if (avgMs < 200) return 'Good'
  if (avgMs < 500) return 'Acceptable'
  return 'Slow'
}

function drawChart() {
  if (!chartEl.value || !results.value) return

  const data = results.value.results
  const container = chartEl.value
  container.innerHTML = ''

  const margin = { top: 20, right: 120, bottom: 40, left: 180 }
  const width = Math.min(container.clientWidth, 900) - margin.left - margin.right
  const barHeight = 32
  const gap = 8
  const height = data.length * (barHeight + gap) - gap

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(data, (d) => d.timings_ms.p99) || 100
  const x = d3.scaleLinear().domain([0, maxVal * 1.15]).range([0, width])

  const y = d3
    .scaleBand()
    .domain(data.map((d) => d.label))
    .range([0, height + gap])
    .padding(0.2)

  // Grid lines
  svg
    .append('g')
    .attr('class', 'grid')
    .call(
      d3
        .axisBottom(x)
        .ticks(5)
        .tickSize(height)
        .tickFormat('')
    )
    .attr('stroke-opacity', 0.08)
    .select('.domain')
    .remove()

  // P99 bar (background, lighter)
  svg
    .selectAll('.bar-p99')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', (d) => y(d.label))
    .attr('width', (d) => x(d.timings_ms.p99))
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', (d) => ratingColor(d.timings_ms.avg))
    .attr('opacity', 0.15)

  // Avg bar (foreground)
  svg
    .selectAll('.bar-avg')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', (d) => y(d.label))
    .attr('width', (d) => Math.max(x(d.timings_ms.avg), 2))
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', (d) => ratingColor(d.timings_ms.avg))
    .attr('opacity', 0.85)

  // Value labels
  svg
    .selectAll('.val-label')
    .data(data)
    .join('text')
    .attr('x', (d) => x(d.timings_ms.p99) + 8)
    .attr('y', (d) => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text-secondary, #6b7280)')
    .text((d) => `${d.timings_ms.avg.toFixed(1)} ms avg`)

  // Y axis (endpoint labels)
  svg
    .append('g')
    .call(d3.axisLeft(y).tickSize(0))
    .select('.domain')
    .remove()

  svg
    .selectAll('.tick text')
    .attr('font-size', '12px')
    .attr('fill', 'var(--color-text, #1a1a1a)')

  // X axis
  svg
    .append('g')
    .attr('transform', `translate(0,${height})`)
    .call(
      d3
        .axisBottom(x)
        .ticks(5)
        .tickFormat((d) => `${d}ms`)
    )
    .attr('font-size', '10px')
    .select('.domain')
    .attr('stroke', 'var(--color-border, #e5e7eb)')
}

onMounted(() => {
  runBenchmark()
})
</script>

<template>
  <div class="max-w-[1100px] mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 md:mb-8">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-[rgba(32,104,255,0.08)] flex items-center justify-center">
          <svg class="w-5 h-5 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        </div>
        <div>
          <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text,#1a1a1a)]">API Performance</h1>
          <p class="text-xs text-[var(--color-text-muted,#9ca3af)] mt-0.5">Response time benchmarks across API endpoints</p>
        </div>
      </div>

      <!-- Controls -->
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-2 text-xs text-[var(--color-text-secondary,#6b7280)]">
          Iterations
          <select
            v-model.number="iterations"
            class="rounded-md border border-[var(--color-border,#e5e7eb)] bg-[var(--color-surface,#fff)] text-xs px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#2068FF]"
          >
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
        </label>
        <button
          @click="runBenchmark"
          :disabled="loading"
          class="flex items-center gap-1.5 text-xs font-medium text-white bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-50 px-4 py-2 rounded-lg transition-colors"
        >
          <svg v-if="loading" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          {{ loading ? 'Running...' : 'Run Benchmark' }}
        </button>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6 text-sm text-red-700 dark:text-red-300">
      {{ error }}
    </div>

    <!-- Chart -->
    <section class="bg-[var(--color-surface,#fff)] border border-[var(--color-border,#e5e7eb)] rounded-xl p-5 md:p-6 mb-6">
      <h2 class="text-sm font-semibold text-[var(--color-text,#1a1a1a)] mb-1">Response Times</h2>
      <p class="text-xs text-[var(--color-text-muted,#9ca3af)] mb-4">Solid bar = avg, transparent = p99 tail latency</p>

      <div v-if="loading && !results" class="flex items-center justify-center h-48 text-sm text-[var(--color-text-muted,#9ca3af)]">
        Running benchmark...
      </div>
      <div ref="chartEl" class="overflow-x-auto" />
    </section>

    <!-- Stats table -->
    <section v-if="results" class="bg-[var(--color-surface,#fff)] border border-[var(--color-border,#e5e7eb)] rounded-xl overflow-hidden">
      <table class="w-full text-xs">
        <thead>
          <tr class="border-b border-[var(--color-border,#e5e7eb)] bg-[var(--color-bg,#f9fafb)]">
            <th class="text-left px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">Endpoint</th>
            <th class="text-right px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">Avg</th>
            <th class="text-right px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">Min</th>
            <th class="text-right px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">Median</th>
            <th class="text-right px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">P95</th>
            <th class="text-right px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">P99</th>
            <th class="text-right px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">Max</th>
            <th class="text-center px-4 py-2.5 font-medium text-[var(--color-text-secondary,#6b7280)]">Rating</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in results.results"
            :key="r.endpoint"
            class="border-b border-[var(--color-border,#e5e7eb)] last:border-0 hover:bg-[var(--color-bg,#f9fafb)] transition-colors"
          >
            <td class="px-4 py-2.5 font-medium text-[var(--color-text,#1a1a1a)]">
              <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold mr-1.5 bg-[rgba(32,104,255,0.08)] text-[#2068FF]">{{ r.method }}</span>
              {{ r.label }}
            </td>
            <td class="text-right px-4 py-2.5 font-mono" :style="{ color: ratingColor(r.timings_ms.avg) }">
              {{ r.timings_ms.avg.toFixed(1) }}ms
            </td>
            <td class="text-right px-4 py-2.5 font-mono text-[var(--color-text-secondary,#6b7280)]">
              {{ r.timings_ms.min.toFixed(1) }}ms
            </td>
            <td class="text-right px-4 py-2.5 font-mono text-[var(--color-text-secondary,#6b7280)]">
              {{ r.timings_ms.median.toFixed(1) }}ms
            </td>
            <td class="text-right px-4 py-2.5 font-mono text-[var(--color-text-secondary,#6b7280)]">
              {{ r.timings_ms.p95.toFixed(1) }}ms
            </td>
            <td class="text-right px-4 py-2.5 font-mono text-[var(--color-text-secondary,#6b7280)]">
              {{ r.timings_ms.p99.toFixed(1) }}ms
            </td>
            <td class="text-right px-4 py-2.5 font-mono text-[var(--color-text-secondary,#6b7280)]">
              {{ r.timings_ms.max.toFixed(1) }}ms
            </td>
            <td class="text-center px-4 py-2.5">
              <span
                class="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold text-white"
                :style="{ backgroundColor: ratingColor(r.timings_ms.avg) }"
              >
                {{ ratingLabel(r.timings_ms.avg) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
