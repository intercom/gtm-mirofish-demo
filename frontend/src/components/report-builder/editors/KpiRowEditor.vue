<script setup>
import { ref, watch } from 'vue'
import EditorPopover from './EditorPopover.vue'

const props = defineProps({
  open: Boolean,
  section: {
    type: Object,
    default: () => ({
      metrics: [],
      layout: 3,
      format: 'percentage',
    }),
  },
})

const emit = defineEmits(['update', 'done', 'cancel'])

const metrics = ref([])
const layout = ref(3)
const format = ref('percentage')
let snapshot = null

const LAYOUTS = [2, 3, 4]
const FORMATS = [
  { value: 'percentage', label: '%' },
  { value: 'number', label: '#' },
  { value: 'currency', label: '$' },
]
const TREND_OPTIONS = ['up', 'down', 'flat']

const METRIC_PRESETS = [
  { label: 'Open Rate', value: '34.7%', change: '+2.3%', trend: 'up' },
  { label: 'Click Rate', value: '12.1%', change: '-0.5%', trend: 'down' },
  { label: 'Conversion Rate', value: '8.4%', change: '+1.1%', trend: 'up' },
  { label: 'Response Time', value: '2.3s', change: '-0.4s', trend: 'up' },
]

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    const s = props.section
    metrics.value = (s.metrics || []).map(m => ({ ...m }))
    layout.value = s.layout || 3
    format.value = s.format || 'percentage'
    snapshot = JSON.parse(JSON.stringify(s))
  }
})

function emitUpdate() {
  emit('update', {
    ...props.section,
    metrics: metrics.value.map(m => ({ ...m })),
    layout: layout.value,
    format: format.value,
  })
}

function addMetric() {
  metrics.value.push({ label: '', value: '', change: '', trend: 'up' })
  emitUpdate()
}

function addPreset(preset) {
  const exists = metrics.value.some(m => m.label === preset.label)
  if (!exists) {
    metrics.value.push({ ...preset })
    emitUpdate()
  }
}

function removeMetric(index) {
  metrics.value.splice(index, 1)
  emitUpdate()
}

function updateMetricField(index, field, value) {
  metrics.value[index][field] = value
  emitUpdate()
}

function trendIcon(trend) {
  if (trend === 'up') return '↑'
  if (trend === 'down') return '↓'
  return '→'
}

function trendColor(trend) {
  if (trend === 'up') return 'text-green-600'
  if (trend === 'down') return 'text-red-500'
  return 'text-[var(--color-text-muted)]'
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
  <EditorPopover :open="open" title="Edit KPI Row" @done="onDone" @cancel="onCancel">
    <div class="space-y-4">
      <!-- Layout selector -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Cards Per Row</label>
        <div class="flex gap-1.5">
          <button
            v-for="n in LAYOUTS"
            :key="n"
            class="px-4 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            :class="layout === n
              ? 'bg-[#2068FF] text-white'
              : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
            @click="layout = n; emitUpdate()"
          >
            {{ n }} cards
          </button>
        </div>
      </div>

      <!-- Format selector -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Value Format</label>
        <div class="flex gap-1.5">
          <button
            v-for="f in FORMATS"
            :key="f.value"
            class="w-10 h-8 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
            :class="format === f.value
              ? 'bg-[#2068FF] text-white'
              : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
            @click="format = f.value; emitUpdate()"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <!-- Quick-add presets -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Quick Add</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="preset in METRIC_PRESETS"
            :key="preset.label"
            class="px-2.5 py-1 rounded-md text-xs text-[var(--color-text-secondary)] bg-[var(--color-tint)] hover:bg-[var(--color-border)] transition-colors cursor-pointer"
            @click="addPreset(preset)"
          >
            + {{ preset.label }}
          </button>
        </div>
      </div>

      <!-- Metrics list -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">
          Metrics ({{ metrics.length }})
        </label>
        <div class="space-y-2.5">
          <div
            v-for="(metric, i) in metrics"
            :key="i"
            class="border border-[var(--color-border)] rounded-lg p-3 bg-[var(--color-tint)]"
          >
            <div class="flex items-start justify-between gap-2 mb-2">
              <span class="text-xs text-[var(--color-text-muted)]">Card {{ i + 1 }}</span>
              <button
                @click="removeMetric(i)"
                class="text-[var(--color-text-muted)] hover:text-red-500 transition-colors cursor-pointer"
                title="Remove"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <input
                :value="metric.label"
                @input="updateMetricField(i, 'label', $event.target.value)"
                placeholder="Label"
                class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-2.5 py-1.5 text-xs text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] transition-colors"
              />
              <input
                :value="metric.value"
                @input="updateMetricField(i, 'value', $event.target.value)"
                placeholder="Value"
                class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-2.5 py-1.5 text-xs text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] transition-colors"
              />
              <input
                :value="metric.change"
                @input="updateMetricField(i, 'change', $event.target.value)"
                placeholder="Change (e.g. +2.3%)"
                class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-2.5 py-1.5 text-xs text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] transition-colors"
              />
              <div class="flex gap-1">
                <button
                  v-for="t in TREND_OPTIONS"
                  :key="t"
                  class="flex-1 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer"
                  :class="metric.trend === t
                    ? 'bg-[var(--color-surface)] border border-[var(--color-border)] ' + trendColor(t)
                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)]'"
                  @click="updateMetricField(i, 'trend', t)"
                >
                  {{ trendIcon(t) }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Add metric button -->
        <button
          @click="addMetric"
          class="mt-2 w-full py-2 rounded-lg border border-dashed border-[var(--color-border)] text-xs font-medium text-[var(--color-text-muted)] hover:text-[#2068FF] hover:border-[#2068FF] transition-colors cursor-pointer"
        >
          + Add Metric
        </button>
      </div>

      <!-- Preview -->
      <div>
        <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Preview</p>
        <div
          class="grid gap-2"
          :style="{ gridTemplateColumns: `repeat(${layout}, 1fr)` }"
        >
          <div
            v-for="(metric, i) in metrics"
            :key="'preview-' + i"
            class="border border-[var(--color-border)] rounded-lg p-3 bg-[var(--color-surface)]"
          >
            <p class="text-xs text-[var(--color-text-muted)] mb-1">{{ metric.label || 'Untitled' }}</p>
            <p class="text-lg font-semibold text-[var(--color-text)]">{{ metric.value || '—' }}</p>
            <p v-if="metric.change" class="text-xs mt-0.5" :class="trendColor(metric.trend)">
              {{ trendIcon(metric.trend) }} {{ metric.change }}
            </p>
          </div>
          <div
            v-if="metrics.length === 0"
            class="col-span-full text-center py-4 text-xs text-[var(--color-text-muted)]"
          >
            No metrics added yet
          </div>
        </div>
      </div>
    </div>
  </EditorPopover>
</template>
