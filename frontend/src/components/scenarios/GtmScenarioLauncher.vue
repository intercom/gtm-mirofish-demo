<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useScenariosStore } from '../../stores/scenarios'
import { useSimulationStore } from '../../stores/simulation'
import { useToast } from '../../composables/useToast'
import { useDemoMode } from '../../composables/useDemoMode'
import { graphApi } from '../../api/graph'
import AppBadge from '../common/AppBadge.vue'

const emit = defineEmits(['launch', 'configure'])

const router = useRouter()
const scenariosStore = useScenariosStore()
const simulationStore = useSimulationStore()
const toast = useToast()
const { isDemoMode } = useDemoMode()

const launching = ref(null)

const SCENARIO_META = {
  outbound_campaign: {
    complexity: 'Medium',
    estimatedTime: '~8 min',
    audience: 'Sales Development, Marketing',
    demoReady: true,
    color: '#2068FF',
    emoji: '\u{1F4E7}',
  },
  personalization: {
    complexity: 'Low',
    estimatedTime: '~5 min',
    audience: 'Product Marketing, Growth',
    demoReady: true,
    color: '#AA00FF',
    emoji: '\u2728',
  },
  pricing_simulation: {
    complexity: 'High',
    estimatedTime: '~12 min',
    audience: 'Revenue Ops, Finance',
    demoReady: false,
    color: '#ff5600',
    emoji: '\u{1F4B0}',
  },
  signal_validation: {
    complexity: 'High',
    estimatedTime: '~12 min',
    audience: 'Sales Development, RevOps',
    demoReady: false,
    color: '#009900',
    emoji: '\u{1F4E1}',
  },
}

const DEFAULT_META = {
  complexity: 'Medium',
  estimatedTime: '~10 min',
  audience: 'GTM Teams',
  demoReady: false,
  color: '#2068FF',
  emoji: '\u{1F41F}',
}

function getMeta(scenario) {
  return SCENARIO_META[scenario.id] || DEFAULT_META
}

function getComplexityVariant(complexity) {
  if (complexity === 'Low') return 'success'
  if (complexity === 'High') return 'warning'
  return 'primary'
}

async function quickLaunch(scenario) {
  if (launching.value) return
  launching.value = scenario.id

  try {
    const detail = await scenariosStore.fetchScenarioById(scenario.id)
    if (!detail?.seed_text) {
      toast.error('Scenario has no seed text configured')
      return
    }

    const config = {
      seed_text: detail.seed_text,
      agent_count: detail.agent_config?.count || 200,
      persona_types: detail.agent_config?.persona_types || [],
      industries: detail.agent_config?.firmographic_mix?.industries || [],
      company_sizes: detail.agent_config?.firmographic_mix?.company_sizes || [],
      regions: detail.agent_config?.firmographic_mix?.regions || [],
      duration_hours: detail.simulation_config?.total_hours || 72,
      minutes_per_round: detail.simulation_config?.minutes_per_round || 30,
      platform_mode: detail.simulation_config?.platform_mode || 'parallel',
    }

    const { data: res } = await graphApi.build(config)
    const taskId = res.data?.task_id || res.task_id

    simulationStore.setScenarioConfig({
      scenarioId: scenario.id,
      scenarioName: detail.name,
      seedText: detail.seed_text,
      agentCount: config.agent_count,
      personas: config.persona_types,
      industries: config.industries,
      companySizes: config.company_sizes,
      regions: config.regions,
      duration: config.duration_hours,
      minutesPerRound: config.minutes_per_round,
      platformMode: config.platform_mode,
    })

    simulationStore.startGraphBuild(taskId)
    simulationStore.addSessionRun({
      id: taskId,
      scenarioId: scenario.id,
      scenarioName: detail.name,
      status: 'building_graph',
    })

    toast.success(`Launching "${detail.name}"...`)
    emit('launch', { scenarioId: scenario.id, taskId })
    router.push(`/workspace/${taskId}`)
  } catch (e) {
    toast.error(`Failed to launch: ${e.message}`)
  } finally {
    launching.value = null
  }
}

function configure(scenario) {
  emit('configure', scenario)
  router.push(`/scenarios/${scenario.id}`)
}

onMounted(() => {
  scenariosStore.fetchScenarios()
})

const scenarios = computed(() => scenariosStore.scenarios)
const loading = computed(() => scenariosStore.loading)
const error = computed(() => scenariosStore.error)
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="n in 4"
        :key="n"
        class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 animate-pulse"
      >
        <div class="flex items-start gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-[var(--color-tint)]" />
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-[var(--color-tint)] rounded w-3/4" />
            <div class="h-3 bg-[var(--color-tint)] rounded w-full" />
          </div>
        </div>
        <div class="flex gap-2">
          <div class="h-5 bg-[var(--color-tint)] rounded-full w-16" />
          <div class="h-5 bg-[var(--color-tint)] rounded-full w-14" />
        </div>
      </div>
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="text-center py-10 px-4 rounded-xl border border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/10"
    >
      <p class="text-sm text-red-600 dark:text-red-400 mb-3">{{ error }}</p>
      <button
        @click="scenariosStore.fetchScenarios(true)"
        class="text-sm font-medium text-[var(--color-primary)] hover:underline"
      >
        Try again
      </button>
    </div>

    <!-- Empty -->
    <div v-else-if="scenarios.length === 0" class="text-center py-12">
      <span class="text-3xl block mb-3">🐟</span>
      <p class="text-sm text-[var(--color-text-muted)]">No scenarios available yet.</p>
    </div>

    <!-- Scenario Cards -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="scenario in scenarios"
        :key="scenario.id"
        class="group relative rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden transition-all duration-200 hover:shadow-[var(--shadow)] hover:border-[var(--color-primary)]/40"
      >
        <!-- Color accent bar -->
        <div
          class="h-1 w-full"
          :style="{ backgroundColor: getMeta(scenario).color }"
        />

        <div class="p-5">
          <!-- Header row: icon + name + badges -->
          <div class="flex items-start gap-3 mb-3">
            <span class="text-2xl shrink-0 mt-0.5">{{ getMeta(scenario).emoji }}</span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap mb-1">
                <h3 class="text-sm font-semibold text-[var(--color-text)] truncate">
                  {{ scenario.name }}
                </h3>
                <AppBadge
                  v-if="getMeta(scenario).demoReady && isDemoMode"
                  variant="primary"
                >
                  Demo Mode
                </AppBadge>
                <AppBadge
                  v-if="scenario.comingSoon"
                  variant="neutral"
                >
                  Coming Soon
                </AppBadge>
              </div>
              <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed line-clamp-2">
                {{ scenario.description }}
              </p>
            </div>
          </div>

          <!-- Meta row: time, complexity, audience -->
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 text-[11px] text-[var(--color-text-muted)]">
            <span class="inline-flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              {{ getMeta(scenario).estimatedTime }}
            </span>
            <span class="inline-flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
              <AppBadge :variant="getComplexityVariant(getMeta(scenario).complexity)">
                {{ getMeta(scenario).complexity }}
              </AppBadge>
            </span>
            <span class="inline-flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
              </svg>
              {{ getMeta(scenario).audience }}
            </span>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-2">
            <button
              v-if="!scenario.comingSoon"
              @click="quickLaunch(scenario)"
              :disabled="launching !== null"
              class="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition-colors bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white disabled:opacity-50"
            >
              <svg
                v-if="launching === scenario.id"
                class="animate-spin w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
              </svg>
              {{ launching === scenario.id ? 'Launching...' : 'Quick Launch' }}
            </button>
            <button
              @click="configure(scenario)"
              class="inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition-colors border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]"
              :class="scenario.comingSoon ? 'flex-1 opacity-50 pointer-events-none' : ''"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
              </svg>
              Customize
            </button>
          </div>
        </div>
      </div>

      <!-- Custom Simulation Card -->
      <div
        @click="router.push('/scenarios/custom')"
        class="group relative rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden transition-all duration-200 hover:shadow-[var(--shadow)] hover:border-[var(--color-primary)]/40 cursor-pointer"
      >
        <div class="h-1 w-full bg-[var(--color-text-muted)]/20" />
        <div class="p-5 flex flex-col items-center justify-center text-center min-h-[180px]">
          <div class="w-10 h-10 rounded-full border-2 border-dashed border-[var(--color-text-muted)]/40 group-hover:border-[var(--color-primary)] flex items-center justify-center mb-3 transition-colors">
            <svg class="w-5 h-5 text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-[var(--color-text-secondary)] group-hover:text-[var(--color-text)] transition-colors mb-1">
            Custom Simulation
          </h3>
          <p class="text-xs text-[var(--color-text-muted)] leading-relaxed max-w-[220px]">
            Bring your own seed document and configure from scratch.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
