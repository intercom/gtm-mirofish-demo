<script setup>
import { ref, computed, watch } from 'vue'
import EditorPopover from './EditorPopover.vue'

const props = defineProps({
  open: Boolean,
  section: {
    type: Object,
    default: () => ({
      dataSource: 'agent_results',
      columns: [],
      sortBy: '',
      sortOrder: 'desc',
      filterText: '',
      rowLimit: 10,
    }),
  },
})

const emit = defineEmits(['update', 'done', 'cancel'])

const dataSource = ref('agent_results')
const selectedColumns = ref([])
const sortBy = ref('')
const sortOrder = ref('desc')
const filterText = ref('')
const rowLimit = ref(10)
let snapshot = null

const DATA_SOURCES = [
  { value: 'agent_results', label: 'Agent Results' },
  { value: 'simulation_metrics', label: 'Simulation Metrics' },
  { value: 'engagement_data', label: 'Engagement Data' },
  { value: 'persona_breakdown', label: 'Persona Breakdown' },
]

const COLUMN_OPTIONS = {
  agent_results: ['agent_name', 'persona', 'engagement', 'conversion', 'sentiment', 'response_time'],
  simulation_metrics: ['metric_name', 'value', 'change', 'trend', 'period', 'confidence'],
  engagement_data: ['channel', 'impressions', 'clicks', 'open_rate', 'click_rate', 'bounces'],
  persona_breakdown: ['persona', 'segment_size', 'avg_engagement', 'top_channel', 'conversion_rate'],
}

const ROW_LIMITS = [5, 10, 20, 50, 100]

const availableColumns = computed(() => COLUMN_OPTIONS[dataSource.value] || [])

const sortableColumns = computed(() => selectedColumns.value)

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    const s = props.section
    dataSource.value = s.dataSource || 'agent_results'
    selectedColumns.value = [...(s.columns || [])]
    sortBy.value = s.sortBy || ''
    sortOrder.value = s.sortOrder || 'desc'
    filterText.value = s.filterText || ''
    rowLimit.value = s.rowLimit || 10
    snapshot = JSON.parse(JSON.stringify(s))
  }
})

function emitUpdate() {
  emit('update', {
    ...props.section,
    dataSource: dataSource.value,
    columns: [...selectedColumns.value],
    sortBy: sortBy.value,
    sortOrder: sortOrder.value,
    filterText: filterText.value,
    rowLimit: rowLimit.value,
  })
}

function onDataSourceChange() {
  selectedColumns.value = []
  sortBy.value = ''
  emitUpdate()
}

function toggleColumn(col) {
  const idx = selectedColumns.value.indexOf(col)
  if (idx === -1) {
    selectedColumns.value.push(col)
  } else {
    selectedColumns.value.splice(idx, 1)
    if (sortBy.value === col) sortBy.value = ''
  }
  emitUpdate()
}

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  emitUpdate()
}

function formatColumnLabel(key) {
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
  <EditorPopover :open="open" title="Edit Table Section" @done="onDone" @cancel="onCancel">
    <div class="space-y-4">
      <!-- Data source -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Data Source</label>
        <select
          v-model="dataSource"
          @change="onDataSourceChange"
          class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
        >
          <option v-for="ds in DATA_SOURCES" :key="ds.value" :value="ds.value">{{ ds.label }}</option>
        </select>
      </div>

      <!-- Columns -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Columns</label>
        <div class="grid grid-cols-2 gap-1.5">
          <label
            v-for="col in availableColumns"
            :key="col"
            class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg cursor-pointer transition-colors"
            :class="selectedColumns.includes(col) ? 'bg-[rgba(32,104,255,0.08)]' : 'hover:bg-[var(--color-tint)]'"
          >
            <input
              type="checkbox"
              :checked="selectedColumns.includes(col)"
              @change="toggleColumn(col)"
              class="rounded border-[var(--color-border)] text-[#2068FF] focus:ring-[#2068FF] cursor-pointer"
            />
            <span class="text-sm text-[var(--color-text-secondary)]">{{ formatColumnLabel(col) }}</span>
          </label>
        </div>
      </div>

      <!-- Sort -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Sort By</label>
          <select
            v-model="sortBy"
            @change="emitUpdate"
            class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
          >
            <option value="">None</option>
            <option v-for="col in sortableColumns" :key="col" :value="col">{{ formatColumnLabel(col) }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Order</label>
          <button
            @click="toggleSortOrder"
            class="w-full flex items-center justify-center gap-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors cursor-pointer"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" :class="sortOrder === 'asc' && 'rotate-180'">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            {{ sortOrder === 'asc' ? 'Ascending' : 'Descending' }}
          </button>
        </div>
      </div>

      <!-- Filter -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Filter</label>
        <input
          v-model="filterText"
          @input="emitUpdate"
          type="text"
          placeholder="Filter rows containing..."
          class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
        />
      </div>

      <!-- Row limit -->
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Row Limit</label>
        <div class="flex gap-1.5">
          <button
            v-for="limit in ROW_LIMITS"
            :key="limit"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            :class="rowLimit === limit
              ? 'bg-[#2068FF] text-white'
              : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
            @click="rowLimit = limit; emitUpdate()"
          >
            {{ limit }}
          </button>
        </div>
      </div>
    </div>
  </EditorPopover>
</template>
