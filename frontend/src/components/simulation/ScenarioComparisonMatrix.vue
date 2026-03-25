<script setup>
import { ref, computed, onMounted } from 'vue'
import * as d3 from 'd3'
import { scenariosApi } from '../../api/scenarios'
import { useRouter } from 'vue-router'

const router = useRouter()

const loading = ref(true)
const error = ref(null)
const scenarios = ref([])
const dimensions = ref([])
const matrix = ref({})
const hoveredCell = ref(null)

const DIMENSION_LABELS = {
  agent_count: 'Agent Count',
  persona_count: 'Persona Types',
  industry_count: 'Industries / Segments',
  duration_hours: 'Duration (hours)',
  expected_outputs: 'Expected Outputs',
}

const colorScale = d3.scaleSequential()
  .domain([0, 1])
  .interpolator(d3.interpolate('#1a3a5f', '#2068FF'))

function rawValue(scenarioId, dim) {
  const s = scenarios.value.find(sc => sc.id === scenarioId)
  if (!s) return ''
  const ac = s.agent_config || {}
  const sc = s.simulation_config || {}
  const fm = ac.firmographic_mix || {}
  const industries = [...(fm.industries || []), ...(fm.segments || [])]
  const map = {
    agent_count: ac.count || 0,
    persona_count: (ac.persona_types || []).length,
    industry_count: industries.length,
    duration_hours: sc.total_hours || 0,
    expected_outputs: (s.expected_outputs || []).length,
  }
  return map[dim] ?? ''
}

function cellColor(scenarioId, dim) {
  const val = matrix.value[scenarioId]?.[dim] ?? 0
  return colorScale(val)
}

function textColor(scenarioId, dim) {
  const val = matrix.value[scenarioId]?.[dim] ?? 0
  return val > 0.5 ? '#ffffff' : '#e0e0e0'
}

function onCellHover(scenarioId, dim) {
  hoveredCell.value = { scenarioId, dim }
}

function onCellLeave() {
  hoveredCell.value = null
}

function isCellHovered(scenarioId, dim) {
  if (!hoveredCell.value) return false
  return hoveredCell.value.scenarioId === scenarioId && hoveredCell.value.dim === dim
}

function navigateToScenario(scenarioId) {
  router.push({ name: 'scenario-builder', params: { id: scenarioId } })
}

const scenarioNames = computed(() =>
  scenarios.value.map(s => ({ id: s.id, name: s.name, category: s.category, icon: s.icon }))
)

async function fetchComparison() {
  loading.value = true
  error.value = null
  try {
    const res = await scenariosApi.compare()
    scenarios.value = res.data.scenarios || []
    dimensions.value = res.data.dimensions || []
    matrix.value = res.data.matrix || {}
  } catch (e) {
    error.value = e.message || 'Failed to load comparison data'
  } finally {
    loading.value = false
  }
}

onMounted(fetchComparison)
</script>

<template>
  <div class="scenario-comparison-matrix">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-[--color-text]">Scenario Comparison</h2>
      <p class="text-sm text-[--color-text-secondary] mt-1">
        Compare configuration dimensions across GTM simulation scenarios
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="w-6 h-6 border-2 border-[--color-primary] border-t-transparent rounded-full animate-spin" />
      <span class="ml-3 text-sm text-[--color-text-secondary]">Loading scenarios…</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-[--color-error] text-sm">{{ error }}</p>
      <button
        class="mt-3 text-sm text-[--color-primary] hover:underline"
        @click="fetchComparison"
      >
        Retry
      </button>
    </div>

    <!-- Matrix -->
    <div v-else-if="scenarios.length" class="overflow-x-auto">
      <table class="w-full border-collapse text-sm">
        <!-- Scenario headers -->
        <thead>
          <tr>
            <th class="p-3 text-left text-xs font-medium text-[--color-text-secondary] uppercase tracking-wider w-44">
              Dimension
            </th>
            <th
              v-for="s in scenarioNames"
              :key="s.id"
              class="p-3 text-center cursor-pointer group min-w-[160px]"
              @click="navigateToScenario(s.id)"
            >
              <div class="flex flex-col items-center gap-1">
                <span
                  class="inline-block px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide"
                  :style="{
                    background: 'rgba(32,104,255,0.1)',
                    color: 'var(--color-primary)',
                  }"
                >
                  {{ s.category }}
                </span>
                <span class="font-semibold text-[--color-text] group-hover:text-[--color-primary] transition-colors text-xs leading-tight">
                  {{ s.name }}
                </span>
              </div>
            </th>
          </tr>
        </thead>

        <!-- Dimension rows -->
        <tbody>
          <tr
            v-for="dim in dimensions"
            :key="dim"
            class="border-t border-[--color-border]"
          >
            <td class="p-3 font-medium text-[--color-text] text-xs whitespace-nowrap">
              {{ DIMENSION_LABELS[dim] || dim }}
            </td>
            <td
              v-for="s in scenarioNames"
              :key="s.id + dim"
              class="p-0"
            >
              <div
                class="m-1 rounded-md flex items-center justify-center h-12 transition-all duration-150 cursor-default relative"
                :class="{ 'ring-2 ring-[--color-primary] ring-offset-1 ring-offset-[--color-surface] scale-105 z-10': isCellHovered(s.id, dim) }"
                :style="{ backgroundColor: cellColor(s.id, dim) }"
                @mouseenter="onCellHover(s.id, dim)"
                @mouseleave="onCellLeave"
              >
                <span
                  class="text-sm font-bold tabular-nums"
                  :style="{ color: textColor(s.id, dim) }"
                >
                  {{ rawValue(s.id, dim) }}
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Color legend -->
      <div class="mt-4 flex items-center gap-3 text-xs text-[--color-text-secondary]">
        <span>Low</span>
        <div class="flex h-3 rounded overflow-hidden" style="width: 120px;">
          <div
            v-for="i in 10"
            :key="i"
            class="flex-1"
            :style="{ backgroundColor: colorScale((i - 1) / 9) }"
          />
        </div>
        <span>High</span>
        <span class="ml-2 text-[10px] opacity-60">(relative across scenarios)</span>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="text-center py-12 text-[--color-text-secondary] text-sm">
      No scenarios available for comparison.
    </div>
  </div>
</template>
