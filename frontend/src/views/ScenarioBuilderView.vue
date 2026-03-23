<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import { useToast } from '../composables/useToast'
import { generateOntology, buildGraph } from '../services/api.js'

const props = defineProps({ id: String })
const router = useRouter()
const toast = useToast()

const scenario = ref(null)
const loading = ref(true)
const error = ref(null)
const seedText = ref('')
const statusMessage = ref('')
const agentCount = ref(200)
const duration = ref(72)
const platformMode = ref('parallel')
const selectedPersonas = ref([])
const selectedIndustries = ref([])
const running = ref(false)

async function loadScenario() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/gtm/scenarios/${props.id}`)
    if (!res.ok) throw new Error(`Failed to load scenario (${res.status})`)
    const data = await res.json()
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
    // Step 1: Create project via ontology generation
    statusMessage.value = 'Analyzing scenario and generating ontology...'
    const text = seedText.value
    const blob = new Blob([text], { type: 'text/plain' })

    const formData = new FormData()
    formData.append('files', blob, `${props.id}_seed.txt`)
    formData.append('simulation_requirement', text)
    formData.append('project_name', scenario.value.name || props.id)

    const ontologyRes = await generateOntology(formData)
    const projectId = ontologyRes.data.project_id

    // Step 2: Build knowledge graph
    statusMessage.value = 'Starting knowledge graph build...'
    const buildRes = await buildGraph({
      projectId,
      graphName: scenario.value.name || 'GTM Simulation Graph',
    })
    const taskId = buildRes.data.task_id

    // Navigate to graph view with task_id and project_id in query
    router.push({
      path: `/graph/${taskId}`,
      query: { projectId },
    })
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
  <div class="max-w-5xl mx-auto px-6 py-10">
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
      <h1 class="text-3xl font-semibold text-[var(--color-text)] mb-2">{{ scenario.name }}</h1>
      <p class="text-sm text-[var(--color-text-secondary)] mb-8">{{ scenario.description }}</p>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Seed Document (left 2/3) -->
        <div class="lg:col-span-2">
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Seed Document</label>
          <textarea
            v-model="seedText"
            rows="16"
            class="w-full border border-[var(--color-border)] rounded-lg p-4 text-sm leading-relaxed focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent resize-y bg-[var(--color-surface)]"
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
        <div class="space-y-6">
          <!-- Agent Count Slider -->
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
          <div v-if="error" class="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            {{ error }}
          </div>

          <!-- Status display -->
          <div v-if="statusMessage" class="text-xs text-[var(--color-primary)] bg-[rgba(32,104,255,0.05)] border border-[var(--color-primary)]/20 rounded-lg p-3">
            {{ statusMessage }}
          </div>

          <!-- Run Simulation Button -->
          <button
            @click="runSimulation"
            :disabled="running"
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
