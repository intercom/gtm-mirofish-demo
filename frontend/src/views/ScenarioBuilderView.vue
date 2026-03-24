<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import { useToast } from '../composables/useToast'
import { useScenariosStore } from '../stores/scenarios'
import { useSimulationStore } from '../stores/simulation'
import { graphApi } from '../api/graph'

const props = defineProps({ id: String })
const router = useRouter()
const toast = useToast()
const scenariosStore = useScenariosStore()
const simulationStore = useSimulationStore()

const scenario = ref(null)
const loading = ref(true)
const error = ref(null)
const seedText = ref('')
const statusMessage = ref('')
const agentCount = ref(200)
const selectedPersonas = ref([])
const selectedIndustries = ref([])
const duration = ref(72)
const platformMode = ref('parallel')
const running = ref(false)
const activeTab = ref('seed')

const canRun = computed(() =>
  seedText.value.trim().length > 0 && selectedPersonas.value.length > 0 && !running.value,
)


async function loadScenario() {
  loading.value = true
  error.value = null
  try {
    const data = await scenariosStore.fetchScenarioById(props.id)
    if (!data) throw new Error('Scenario not found')
    scenario.value = data

    seedText.value = data.seed_text || ''
    agentCount.value = data.agent_config?.count || 200
    duration.value = data.simulation_config?.total_hours || 72
    platformMode.value = data.simulation_config?.platform_mode || 'parallel'
    selectedPersonas.value = [...(data.agent_config?.persona_types || [])]
    selectedIndustries.value = [...(data.agent_config?.firmographic_mix?.industries || [])]
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadScenario)


function togglePersona(persona) {
  const idx = selectedPersonas.value.indexOf(persona)
  if (idx === -1) {
    selectedPersonas.value.push(persona)
  } else {
    selectedPersonas.value.splice(idx, 1)
  }
}

function toggleIndustry(industry) {
  const idx = selectedIndustries.value.indexOf(industry)
  if (idx === -1) {
    selectedIndustries.value.push(industry)
  } else {
    selectedIndustries.value.splice(idx, 1)
  }
}

async function runSimulation() {
  if (running.value || !seedText.value) return
  running.value = true
  error.value = ''

  try {
    const { data } = await graphApi.build({
      seed_text: seedText.value,
      agent_count: agentCount.value,
      persona_types: selectedPersonas.value,
      industries: selectedIndustries.value,
      duration_hours: duration.value,
      platform_mode: platformMode.value,
    })
    const taskId = data.task_id
    simulationStore.startBuild(taskId)
    toast.success('Building knowledge graph...')
    router.push(`/graph/${taskId}`)
  } catch (e) {
    error.value = e.message
    toast.error(`Failed to start simulation: ${e.message}`)
  } finally {
    running.value = false
    statusMessage.value = ''
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <LoadingSpinner v-if="loading" label="Loading scenario..." />

    <ErrorState
      v-else-if="error"
      title="Failed to load scenario"
      :message="error"
      @retry="loadScenario"
    />

    <div v-else-if="scenario">
      <!-- Header -->
      <router-link to="/" class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors mb-4 inline-block">&larr; Back to scenarios</router-link>
      <h1 class="text-2xl md:text-3xl font-semibold text-[var(--color-text)] mb-2">{{ scenario.name }}</h1>
      <p class="text-sm text-[var(--color-text-secondary)] mb-6 md:mb-8">{{ scenario.description }}</p>

      <!-- Mobile: tab switcher -->
      <div class="md:hidden flex gap-2 mb-4">
        <button
          @click="activeTab = 'seed'"
          class="flex-1 py-2 text-sm font-medium rounded-lg transition-colors"
          :class="activeTab === 'seed' ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)]'"
        >
          Seed Document
        </button>
        <button
          @click="activeTab = 'config'"
          class="flex-1 py-2 text-sm font-medium rounded-lg transition-colors"
          :class="activeTab === 'config' ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)]'"
        >
          Configuration
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Seed Document (left 2/3) -->
        <div class="lg:col-span-2" :class="{ 'hidden md:block': activeTab !== 'seed' }">
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Seed Document</label>
          <textarea
            v-model="seedText"
            rows="16"
            class="w-full border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-sm leading-relaxed focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent resize-y bg-[var(--color-surface)]"
            placeholder="Paste or edit your scenario seed text..."
          ></textarea>

          <!-- Persona Types Multiselect -->
          <div v-if="scenario.agent_config?.persona_types?.length" class="mt-6">
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Persona Types</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="persona in scenario.agent_config.persona_types"
                :key="persona"
                @click="togglePersona(persona)"
                class="px-3 py-1.5 text-xs rounded-full border transition-colors"
                :class="selectedPersonas.includes(persona)
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ persona }}
              </button>
            </div>
          </div>

          <!-- Industry Mix Checkboxes -->
          <div v-if="scenario.agent_config?.firmographic_mix?.industries?.length" class="mt-6">
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Industry Mix</label>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <label
                v-for="industry in scenario.agent_config.firmographic_mix.industries"
                :key="industry"
                class="flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors text-sm"
                :class="selectedIndustries.includes(industry)
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                  : 'border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                <input
                  type="checkbox"
                  :checked="selectedIndustries.includes(industry)"
                  @change="toggleIndustry(industry)"
                  class="accent-[var(--color-primary)]"
                />
                <span :class="selectedIndustries.includes(industry) ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-secondary)]'">{{ industry }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Config Panel (right 1/3) -->
        <div class="space-y-6" :class="{ 'hidden md:block': activeTab !== 'config' }">
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Agent Count</label>
            <input
              type="range"
              v-model.number="agentCount"
              min="50"
              max="500"
              step="10"
              class="w-full accent-[var(--color-primary)]"
            />
            <div class="text-center text-2xl font-semibold text-[var(--color-primary)]">{{ agentCount }}</div>
          </div>

          <!-- Simulation Duration -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Duration</label>
            <div class="flex gap-2">
              <button
                v-for="hours in [24, 48, 72]"
                :key="hours"
                @click="duration = hours"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors"
                :class="duration === hours
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ hours }}h
              </button>
            </div>
          </div>

          <!-- Platform Mode Toggle -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Platform</label>
            <div class="flex gap-2">
              <button
                v-for="mode in ['twitter', 'reddit', 'parallel']"
                :key="mode"
                @click="platformMode = mode"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors capitalize"
                :class="platformMode === mode
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ mode === 'parallel' ? 'Both' : mode }}
              </button>
            </div>
          </div>

          <!-- Error display -->
          <div v-if="error" class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-lg p-3">
            {{ error }}
          </div>

          <!-- Status display -->
          <div v-if="statusMessage" class="text-xs text-[var(--color-primary)] bg-[rgba(32,104,255,0.05)] border border-[var(--color-primary)]/20 rounded-lg p-3">
            {{ statusMessage }}
          </div>

          <!-- Run Simulation Button -->
          <button
            @click="runSimulation"
            :disabled="!canRun"
            class="w-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors mt-4"
          >
            {{ running ? 'Starting...' : 'Run Simulation' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-20">
      <p class="text-[var(--color-text-muted)]">Scenario not found</p>
      <router-link to="/" class="text-[var(--color-primary)] text-sm mt-2 inline-block hover:underline">Back to Home</router-link>
    </div>
  </div>
</template>
