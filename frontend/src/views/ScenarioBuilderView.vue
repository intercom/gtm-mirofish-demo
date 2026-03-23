<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { generateOntology, buildGraph } from '../services/api.js'

const props = defineProps({ id: String })
const router = useRouter()

const scenario = ref(null)
const loading = ref(true)
const running = ref(false)
const error = ref('')
const statusMessage = ref('')
const agentCount = ref(200)
const duration = ref(72)
const platformMode = ref('parallel')

onMounted(async () => {
  try {
    const res = await fetch(`/api/gtm/scenarios/${props.id}`)
    if (res.ok) scenario.value = await res.json()
  } catch (e) {
    console.error('Failed to load scenario:', e)
  } finally {
    loading.value = false
  }
})

async function runSimulation() {
  if (running.value || !scenario.value?.seed_text) return
  running.value = true
  error.value = ''

  try {
    // Step 1: Create project via ontology generation
    statusMessage.value = 'Analyzing scenario and generating ontology...'
    const seedText = scenario.value.seed_text
    const blob = new Blob([seedText], { type: 'text/plain' })

    const formData = new FormData()
    formData.append('files', blob, `${props.id}_seed.txt`)
    formData.append('simulation_requirement', seedText)
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
    console.error('Run simulation failed:', e)
  } finally {
    running.value = false
    statusMessage.value = ''
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-6 py-10">
    <div v-if="loading" class="text-center text-[#888] py-20">Loading scenario...</div>

    <div v-else-if="scenario">
      <h1 class="text-3xl font-semibold text-[#050505] mb-2">{{ scenario.name }}</h1>
      <p class="text-sm text-[#555] mb-8">{{ scenario.description }}</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Seed Document -->
        <div class="md:col-span-2">
          <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Seed Document</label>
          <textarea
            v-model="scenario.seed_text"
            rows="12"
            class="w-full border border-black/10 rounded-lg p-4 text-sm focus:ring-2 focus:ring-[#2068FF] focus:border-transparent resize-y"
          ></textarea>
        </div>

        <!-- Config Panel -->
        <div class="space-y-6">
          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Agent Count</label>
            <input type="range" v-model.number="agentCount" min="10" max="500" step="10" class="w-full" />
            <div class="text-center text-2xl font-semibold text-[#2068FF]">{{ agentCount }}</div>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Duration (hours)</label>
            <select v-model.number="duration" class="w-full border border-black/10 rounded-lg p-2 text-sm">
              <option :value="24">24 hours</option>
              <option :value="48">48 hours</option>
              <option :value="72">72 hours (recommended)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Platform</label>
            <div class="flex gap-2">
              <button
                v-for="mode in ['twitter', 'reddit', 'parallel']"
                :key="mode"
                @click="platformMode = mode"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors capitalize"
                :class="platformMode === mode
                  ? 'bg-[#2068FF] text-white border-[#2068FF]'
                  : 'bg-white text-[#555] border-black/10 hover:border-[#2068FF]'"
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
          <div v-if="statusMessage" class="text-xs text-[#2068FF] bg-[rgba(32,104,255,0.05)] border border-[#2068FF]/20 rounded-lg p-3">
            {{ statusMessage }}
          </div>

          <button
            @click="runSimulation"
            :disabled="running"
            class="w-full bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            {{ running ? 'Starting...' : 'Run Simulation' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-20">
      <p class="text-[#888]">Scenario not found</p>
      <router-link to="/" class="text-[#2068FF] text-sm mt-2 inline-block">Back to Home</router-link>
    </div>
  </div>
</template>
