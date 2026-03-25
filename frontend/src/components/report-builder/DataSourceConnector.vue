<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { reportApi } from '../../api/report'
import { simulationApi } from '../../api/simulation'

const props = defineProps({
  sectionId: { type: String, default: null },
  sectionType: { type: String, default: null },
  modelValue: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue'])

const sources = ref([])
const simulations = ref([])
const loading = ref(false)
const previewLoading = ref(false)
const preview = ref(null)
const error = ref(null)

const selectedSourceId = ref(props.modelValue?.sourceId || null)
const selectedSimulationId = ref(props.modelValue?.simulationId || null)

const selectedSource = computed(() =>
  sources.value.find((s) => s.id === selectedSourceId.value) || null,
)

const needsSimulationSelect = computed(() => selectedSourceId.value === 'simulation')

const connectedSources = computed(() => sources.value.filter((s) => s.connected))
const availableSources = computed(() => sources.value.filter((s) => !s.connected))

function emitConfig() {
  emit('update:modelValue', {
    sourceId: selectedSourceId.value,
    simulationId: needsSimulationSelect.value ? selectedSimulationId.value : null,
    sourceName: selectedSource.value?.name || null,
  })
}

async function loadSources() {
  loading.value = true
  error.value = null
  try {
    const res = await reportApi.listDataSources()
    sources.value = res.data?.data || []
  } catch (e) {
    error.value = e.message || 'Failed to load data sources'
  } finally {
    loading.value = false
  }
}

async function loadSimulations() {
  try {
    const res = await simulationApi.list({ limit: 20 })
    const list = res.data?.data || res.data || []
    simulations.value = Array.isArray(list) ? list : []
  } catch {
    simulations.value = []
  }
}

async function loadPreview() {
  if (!selectedSourceId.value) {
    preview.value = null
    return
  }
  if (selectedSourceId.value === 'simulation' && !selectedSimulationId.value) {
    preview.value = null
    return
  }
  previewLoading.value = true
  try {
    const params = {}
    if (selectedSimulationId.value) {
      params.simulation_id = selectedSimulationId.value
    }
    const res = await reportApi.previewDataSource(selectedSourceId.value, params)
    preview.value = res.data?.data || null
  } catch {
    preview.value = null
  } finally {
    previewLoading.value = false
  }
}

function selectSource(sourceId) {
  selectedSourceId.value = sourceId
  selectedSimulationId.value = null
  preview.value = null
  emitConfig()
  if (sourceId !== 'simulation') {
    loadPreview()
  }
}

function selectSimulation(simId) {
  selectedSimulationId.value = simId
  emitConfig()
  loadPreview()
}

function clearSelection() {
  selectedSourceId.value = null
  selectedSimulationId.value = null
  preview.value = null
  emitConfig()
}

const SOURCE_ICONS = {
  simulation: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>`,
  revenue: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>`,
  pipeline: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"/>`,
  salesforce: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>`,
  cpq: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>`,
  orders: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>`,
  campaigns: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/>`,
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      selectedSourceId.value = val.sourceId || null
      selectedSimulationId.value = val.simulationId || null
    }
  },
)

onMounted(() => {
  loadSources()
  loadSimulations()
  if (selectedSourceId.value) {
    loadPreview()
  }
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Data Source</h3>
      <button
        v-if="selectedSourceId"
        @click="clearSelection"
        class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      >
        Clear
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center gap-2 py-6 justify-center text-sm text-[var(--color-text-muted)]">
      <svg class="w-4 h-4 animate-spin text-[#2068FF]" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading sources...
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg p-3 text-sm text-red-700 dark:text-red-400">
      {{ error }}
    </div>

    <template v-else>
      <!-- Connected sources -->
      <div v-if="connectedSources.length">
        <p class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Connected</p>
        <div class="grid grid-cols-1 gap-2">
          <button
            v-for="source in connectedSources"
            :key="source.id"
            @click="selectSource(source.id)"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg border text-left transition-all"
            :class="selectedSourceId === source.id
              ? 'border-[#2068FF] bg-[rgba(32,104,255,0.06)]'
              : 'border-[var(--color-border)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-tint)]'"
          >
            <span class="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
              :class="selectedSourceId === source.id ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)]'">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" v-html="SOURCE_ICONS[source.icon] || SOURCE_ICONS.simulation" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-[var(--color-text)] truncate">{{ source.name }}</p>
              <p class="text-xs text-[var(--color-text-muted)] truncate">{{ source.description }}</p>
            </div>
            <svg v-if="selectedSourceId === source.id" class="w-4 h-4 shrink-0 text-[#2068FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Simulation selector -->
      <div v-if="needsSimulationSelect" class="space-y-2">
        <label class="text-xs font-medium text-[var(--color-text-muted)]">Select Simulation</label>
        <select
          :value="selectedSimulationId"
          @change="selectSimulation(($event.target).value || null)"
          class="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[#2068FF]/30 focus:border-[#2068FF]"
        >
          <option value="">Choose a simulation...</option>
          <option
            v-for="sim in simulations"
            :key="sim.simulation_id || sim.id"
            :value="sim.simulation_id || sim.id"
          >
            {{ sim.name || sim.scenarioName || sim.simulation_id || sim.id }}
          </option>
        </select>
        <p v-if="simulations.length === 0" class="text-xs text-[var(--color-text-muted)]">
          No simulations found. Run a simulation first.
        </p>
      </div>

      <!-- Available (unconnected) sources -->
      <div v-if="availableSources.length">
        <p class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Available</p>
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="source in availableSources"
            :key="source.id"
            @click="selectSource(source.id)"
            class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-left transition-all"
            :class="selectedSourceId === source.id
              ? 'border-[#2068FF] bg-[rgba(32,104,255,0.06)]'
              : 'border-[var(--color-border)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-tint)]'"
          >
            <span class="shrink-0 w-7 h-7 rounded-md flex items-center justify-center"
              :class="selectedSourceId === source.id ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-muted)]'">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" v-html="SOURCE_ICONS[source.icon] || SOURCE_ICONS.orders" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="text-xs font-medium text-[var(--color-text)] truncate">{{ source.name }}</p>
            </div>
            <span
              v-if="selectedSourceId !== source.id"
              class="shrink-0 text-[10px] font-medium text-[var(--color-text-muted)] bg-[var(--color-tint)] px-1.5 py-0.5 rounded"
            >
              Mock
            </span>
            <svg v-else class="w-3.5 h-3.5 shrink-0 text-[#2068FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Data Preview Panel -->
      <div v-if="selectedSourceId" class="border border-[var(--color-border)] rounded-lg overflow-hidden">
        <div class="px-3 py-2 bg-[var(--color-tint)] border-b border-[var(--color-border)] flex items-center justify-between">
          <span class="text-xs font-semibold text-[var(--color-text)]">Data Preview</span>
          <span v-if="preview?.is_mock" class="text-[10px] text-[var(--color-text-muted)] bg-[var(--color-surface)] px-1.5 py-0.5 rounded">
            Sample Data
          </span>
        </div>

        <!-- Preview loading -->
        <div v-if="previewLoading" class="flex items-center justify-center py-8 text-sm text-[var(--color-text-muted)]">
          <svg class="w-4 h-4 animate-spin text-[#2068FF] mr-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading preview...
        </div>

        <!-- No preview available -->
        <div v-else-if="!preview" class="py-8 text-center text-sm text-[var(--color-text-muted)]">
          <template v-if="needsSimulationSelect && !selectedSimulationId">
            Select a simulation to preview data
          </template>
          <template v-else>
            No preview data available
          </template>
        </div>

        <!-- Metrics -->
        <div v-else class="p-3 space-y-3">
          <div v-if="preview.metrics?.length" class="grid gap-2" :class="preview.metrics.length <= 3 ? 'grid-cols-3' : 'grid-cols-2'">
            <div
              v-for="(metric, i) in preview.metrics"
              :key="i"
              class="bg-[var(--color-tint)] rounded-md px-2.5 py-2"
            >
              <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">{{ metric.label }}</p>
              <p class="text-sm font-semibold text-[var(--color-text)] mt-0.5">{{ metric.value }}</p>
              <p v-if="metric.trend" class="text-[10px] mt-0.5"
                :class="metric.trend.startsWith('-') ? 'text-red-500' : 'text-emerald-600'">
                {{ metric.trend }}
              </p>
            </div>
          </div>

          <!-- Sample rows table -->
          <div v-if="preview.sample_rows?.length" class="overflow-x-auto">
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-[var(--color-border)]">
                  <th
                    v-for="key in Object.keys(preview.sample_rows[0])"
                    :key="key"
                    class="text-left py-1.5 px-2 font-medium text-[var(--color-text-muted)] uppercase tracking-wider"
                  >
                    {{ key.replace(/_/g, ' ') }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, i) in preview.sample_rows"
                  :key="i"
                  class="border-b border-[var(--color-border)] last:border-0"
                >
                  <td
                    v-for="key in Object.keys(row)"
                    :key="key"
                    class="py-1.5 px-2 text-[var(--color-text-secondary)]"
                  >
                    {{ row[key] }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
