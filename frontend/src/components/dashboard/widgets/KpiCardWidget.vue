<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useCountUp } from '../../../composables/useCountUp'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({
      data_source: '',
      metric_name: '',
      label: 'Metric',
      prefix: '',
      suffix: '',
      show_trend: true,
      show_sparkline: true,
      color: 'auto',
    }),
  },
  data: {
    type: Object,
    default: () => ({
      value: 0,
      previous_value: null,
      sparkline: [],
    }),
  },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  onConfigChange: { type: Function, default: null },
})

const editing = ref(false)
const editForm = ref({ ...props.config })
const sparklineRef = ref(null)
let resizeObserver = null

const currentValue = computed(() => props.data?.value ?? 0)
const displayValue = useCountUp(currentValue)

const trend = computed(() => {
  const curr = props.data?.value
  const prev = props.data?.previous_value
  if (curr == null || prev == null || prev === 0) return null
  const pct = ((curr - prev) / Math.abs(prev)) * 100
  return {
    direction: pct >= 0 ? 'up' : 'down',
    percentage: Math.abs(pct).toFixed(1),
  }
})

const BRAND_COLORS = {
  primary: '#2068FF',
  navy: '#050505',
  orange: '#ff5600',
  success: '#009900',
  error: '#ef4444',
  accent: '#AA00FF',
}

const resolvedColor = computed(() => {
  const c = props.config.color
  if (c && c !== 'auto') return BRAND_COLORS[c] || c
  if (!trend.value) return BRAND_COLORS.primary
  return trend.value.direction === 'up' ? BRAND_COLORS.success : BRAND_COLORS.error
})

const trendColorClass = computed(() => {
  if (!trend.value) return ''
  return trend.value.direction === 'up'
    ? 'text-[var(--color-success)]'
    : 'text-[var(--color-error)]'
})

function formatValue(val) {
  if (val == null) return '--'
  if (Math.abs(val) >= 1_000_000) return (val / 1_000_000).toFixed(1) + 'M'
  if (Math.abs(val) >= 1_000) return (val / 1_000).toFixed(1) + 'K'
  return val.toLocaleString()
}

function renderSparkline() {
  const container = sparklineRef.value
  if (!container) return
  const points = props.data?.sparkline
  if (!points || points.length < 2) return

  d3.select(container).selectAll('*').remove()

  const width = container.clientWidth
  const height = 32

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const x = d3.scaleLinear()
    .domain([0, points.length - 1])
    .range([2, width - 2])

  const y = d3.scaleLinear()
    .domain(d3.extent(points))
    .range([height - 2, 2])

  const line = d3.line()
    .x((_, i) => x(i))
    .y(d => y(d))
    .curve(d3.curveMonotoneX)

  const area = d3.area()
    .x((_, i) => x(i))
    .y0(height)
    .y1(d => y(d))
    .curve(d3.curveMonotoneX)

  const color = resolvedColor.value

  svg.append('path')
    .datum(points)
    .attr('d', area)
    .attr('fill', color)
    .attr('opacity', 0.08)

  const path = svg.append('path')
    .datum(points)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', color)
    .attr('stroke-width', 1.5)
    .attr('stroke-linecap', 'round')

  const totalLength = path.node().getTotalLength()
  path
    .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(600)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)

  svg.append('circle')
    .attr('cx', x(points.length - 1))
    .attr('cy', y(points[points.length - 1]))
    .attr('r', 2.5)
    .attr('fill', color)
    .style('opacity', 0)
    .transition()
    .delay(600)
    .duration(200)
    .style('opacity', 1)
}

function saveEdit() {
  if (props.onConfigChange) {
    props.onConfigChange({ ...editForm.value })
  }
  editing.value = false
}

function cancelEdit() {
  editForm.value = { ...props.config }
  editing.value = false
}

watch(
  () => [props.data?.sparkline, props.config.show_sparkline, props.config.color],
  () => {
    if (props.config.show_sparkline && props.data?.sparkline?.length >= 2) {
      nextTick(renderSparkline)
    }
  },
  { deep: true },
)

onMounted(() => {
  if (props.config.show_sparkline && props.data?.sparkline?.length >= 2) {
    renderSparkline()
  }
  if (sparklineRef.value) {
    resizeObserver = new ResizeObserver(() => {
      if (props.config.show_sparkline && props.data?.sparkline?.length >= 2) {
        renderSparkline()
      }
    })
    resizeObserver.observe(sparklineRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
})

const COLOR_OPTIONS = [
  { value: 'auto', label: 'Auto (trend)' },
  { value: 'primary', label: 'Blue' },
  { value: 'orange', label: 'Orange' },
  { value: 'success', label: 'Green' },
  { value: 'accent', label: 'Purple' },
  { value: 'navy', label: 'Navy' },
]
</script>

<template>
  <!-- Edit Mode -->
  <div
    v-if="editing"
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4"
  >
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm font-semibold text-[var(--color-text)]">Configure KPI Card</span>
      <div class="flex gap-2">
        <button
          class="text-xs px-2 py-1 rounded border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg)]"
          @click="cancelEdit"
        >
          Cancel
        </button>
        <button
          class="text-xs px-2 py-1 rounded bg-[var(--color-primary)] text-white hover:opacity-90"
          @click="saveEdit"
        >
          Save
        </button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3 text-xs">
      <label class="block">
        <span class="text-[var(--color-text-secondary)] mb-1 block">Label</span>
        <input
          v-model="editForm.label"
          class="w-full px-2 py-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]"
        />
      </label>
      <label class="block">
        <span class="text-[var(--color-text-secondary)] mb-1 block">Metric Name</span>
        <input
          v-model="editForm.metric_name"
          class="w-full px-2 py-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]"
        />
      </label>
      <label class="block">
        <span class="text-[var(--color-text-secondary)] mb-1 block">Prefix</span>
        <input
          v-model="editForm.prefix"
          placeholder="e.g. $"
          class="w-full px-2 py-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]"
        />
      </label>
      <label class="block">
        <span class="text-[var(--color-text-secondary)] mb-1 block">Suffix</span>
        <input
          v-model="editForm.suffix"
          placeholder="e.g. %"
          class="w-full px-2 py-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]"
        />
      </label>
      <label class="block">
        <span class="text-[var(--color-text-secondary)] mb-1 block">Color</span>
        <select
          v-model="editForm.color"
          class="w-full px-2 py-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]"
        >
          <option v-for="opt in COLOR_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </label>
      <label class="block">
        <span class="text-[var(--color-text-secondary)] mb-1 block">Data Source</span>
        <input
          v-model="editForm.data_source"
          class="w-full px-2 py-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]"
        />
      </label>
      <label class="flex items-center gap-2 col-span-2">
        <input v-model="editForm.show_trend" type="checkbox" class="accent-[var(--color-primary)]" />
        <span class="text-[var(--color-text-secondary)]">Show trend</span>
      </label>
      <label class="flex items-center gap-2 col-span-2">
        <input v-model="editForm.show_sparkline" type="checkbox" class="accent-[var(--color-primary)]" />
        <span class="text-[var(--color-text-secondary)]">Show sparkline</span>
      </label>
    </div>
  </div>

  <!-- Loading State -->
  <div
    v-else-if="loading"
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4"
  >
    <div class="animate-pulse space-y-3">
      <div class="h-3 w-20 bg-[var(--color-tint)] rounded" />
      <div class="h-8 w-28 bg-[var(--color-tint)] rounded" />
      <div class="h-4 w-full bg-[var(--color-tint)] rounded" />
    </div>
  </div>

  <!-- Error State -->
  <div
    v-else-if="error"
    class="bg-[var(--color-surface)] border border-[var(--color-error-light)] rounded-lg p-4"
  >
    <p class="text-xs text-[var(--color-text-secondary)]">{{ config.label }}</p>
    <p class="text-sm text-[var(--color-error)] mt-1">{{ error }}</p>
  </div>

  <!-- Preview Mode (normal display) -->
  <div
    v-else
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 group"
    @dblclick="onConfigChange && (editing = true)"
  >
    <div class="flex items-start justify-between">
      <p class="text-xs text-[var(--color-text-secondary)] leading-tight">
        {{ config.label }}
      </p>
      <button
        v-if="onConfigChange"
        class="opacity-0 group-hover:opacity-100 transition-opacity text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
        @click="editing = true"
        aria-label="Edit KPI card"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
      </button>
    </div>

    <div class="mt-1 flex items-baseline gap-1">
      <span v-if="config.prefix" class="text-lg font-semibold text-[var(--color-text)]">
        {{ config.prefix }}
      </span>
      <span class="text-2xl font-bold text-[var(--color-text)] tracking-tight">
        {{ formatValue(displayValue) }}
      </span>
      <span v-if="config.suffix" class="text-lg font-semibold text-[var(--color-text-secondary)]">
        {{ config.suffix }}
      </span>
    </div>

    <div
      v-if="config.show_trend && trend"
      class="mt-1 flex items-center gap-1 text-xs font-medium"
      :class="trendColorClass"
    >
      <svg
        width="12"
        height="12"
        viewBox="0 0 12 12"
        fill="currentColor"
        :style="trend.direction === 'down' ? 'transform: rotate(180deg)' : ''"
      >
        <path d="M6 2L10 7H2L6 2Z" />
      </svg>
      <span>{{ trend.percentage }}%</span>
      <span class="text-[var(--color-text-muted)] font-normal">vs prior</span>
    </div>

    <div
      v-if="config.show_sparkline"
      ref="sparklineRef"
      class="mt-2 w-full h-8"
    />
  </div>
</template>
