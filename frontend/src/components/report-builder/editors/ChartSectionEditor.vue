<script setup>
import { ref, watch } from 'vue'
import EditorPopover from './EditorPopover.vue'

const props = defineProps({
  open: Boolean,
  section: {
    type: Object,
    default: () => ({
      chartType: 'bar',
      title: '',
      dataSource: 'simulation_metrics',
      metrics: [],
      colors: [],
      xAxisLabel: '',
      yAxisLabel: '',
    }),
  },
})

const emit = defineEmits(['update', 'done', 'cancel'])

const chartType = ref('bar')
const title = ref('')
const dataSource = ref('simulation_metrics')
const selectedMetrics = ref([])
const metricColors = ref({})
const xAxisLabel = ref('')
const yAxisLabel = ref('')
let snapshot = null

const CHART_TYPES = [
  { value: 'bar', label: 'Bar' },
  { value: 'line', label: 'Line' },
  { value: 'pie', label: 'Pie' },
  { value: 'donut', label: 'Donut' },
  { value: 'grouped-bar', label: 'Grouped Bar' },
]

const DATA_SOURCES = [
  { value: 'simulation_metrics', label: 'Simulation Metrics' },
  { value: 'agent_results', label: 'Agent Results' },
  { value: 'engagement_data', label: 'Engagement Data' },
  { value: 'custom', label: 'Custom Data' },
]

const AVAILABLE_METRICS = [
  'engagement_rate',
  'conversion_rate',
  'open_rate',
  'click_rate',
  'response_rate',
  'sentiment_score',
  'bounce_rate',
  'spam_rate',
]

const PRESET_COLORS = ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#050505', '#888888', '#E91E63', '#00BCD4']

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    const s = props.section
    chartType.value = s.chartType || 'bar'
    title.value = s.title || ''
    dataSource.value = s.dataSource || 'simulation_metrics'
    selectedMetrics.value = [...(s.metrics || [])]
    metricColors.value = { ...(s.colors || {}) }
    xAxisLabel.value = s.xAxisLabel || ''
    yAxisLabel.value = s.yAxisLabel || ''
    snapshot = JSON.parse(JSON.stringify(s))
  }
})

function emitUpdate() {
  emit('update', {
    ...props.section,
    chartType: chartType.value,
    title: title.value,
    dataSource: dataSource.value,
    metrics: [...selectedMetrics.value],
    colors: { ...metricColors.value },
    xAxisLabel: xAxisLabel.value,
    yAxisLabel: yAxisLabel.value,
  })
}

function toggleMetric(metric) {
  const idx = selectedMetrics.value.indexOf(metric)
  if (idx === -1) {
    selectedMetrics.value.push(metric)
    if (!metricColors.value[metric]) {
      metricColors.value[metric] = PRESET_COLORS[selectedMetrics.value.length - 1] || '#2068FF'
    }
  } else {
    selectedMetrics.value.splice(idx, 1)
    delete metricColors.value[metric]
  }
  emitUpdate()
}

function setMetricColor(metric, color) {
  metricColors.value[metric] = color
  emitUpdate()
}

function formatMetricLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function onDone() {
  emit('done')
}

function onCancel() {
  if (snapshot) emit('update', snapshot)
  emit('cancel')
}
</script>

<template>
  <EditorPopover :open="open" title="Edit Chart Section" @done="onDone" @cancel="onCancel">
    <div class="space-y-4">
      <!-- Chart type -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Chart Type</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="ct in CHART_TYPES"
            :key="ct.value"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            :class="chartType === ct.value
              ? 'bg-[#2068FF] text-white'
              : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
            @click="chartType = ct.value; emitUpdate()"
          >
            {{ ct.label }}
          </button>
        </div>
      </div>

      <!-- Title -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Chart Title</label>
        <input
          v-model="title"
          @input="emitUpdate"
          type="text"
          placeholder="e.g. Persona Engagement Rates"
          class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
        />
      </div>

      <!-- Data source -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Data Source</label>
        <select
          v-model="dataSource"
          @change="emitUpdate"
          class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
        >
          <option v-for="ds in DATA_SOURCES" :key="ds.value" :value="ds.value">{{ ds.label }}</option>
        </select>
      </div>

      <!-- Metrics -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Metrics</label>
        <div class="space-y-1.5">
          <div
            v-for="metric in AVAILABLE_METRICS"
            :key="metric"
            class="flex items-center gap-2"
          >
            <input
              type="checkbox"
              :id="'metric-' + metric"
              :checked="selectedMetrics.includes(metric)"
              @change="toggleMetric(metric)"
              class="rounded border-[var(--color-border)] text-[#2068FF] focus:ring-[#2068FF] cursor-pointer"
            />
            <label :for="'metric-' + metric" class="text-sm text-[var(--color-text-secondary)] flex-1 cursor-pointer">
              {{ formatMetricLabel(metric) }}
            </label>
            <!-- Color swatch (when selected) -->
            <div v-if="selectedMetrics.includes(metric)" class="flex gap-1">
              <button
                v-for="color in PRESET_COLORS"
                :key="color"
                class="w-4 h-4 rounded-full border transition-transform cursor-pointer"
                :class="metricColors[metric] === color ? 'border-[var(--color-text)] scale-125' : 'border-transparent hover:scale-110'"
                :style="{ backgroundColor: color }"
                @click="setMetricColor(metric, color)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Axis labels -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">X-Axis Label</label>
          <input
            v-model="xAxisLabel"
            @input="emitUpdate"
            type="text"
            placeholder="e.g. Persona"
            class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Y-Axis Label</label>
          <input
            v-model="yAxisLabel"
            @input="emitUpdate"
            type="text"
            placeholder="e.g. Rate (%)"
            class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
          />
        </div>
      </div>
    </div>
  </EditorPopover>
</template>
