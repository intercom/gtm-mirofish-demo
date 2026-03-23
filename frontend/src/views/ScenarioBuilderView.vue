<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ id: String })
const router = useRouter()

const scenario = ref(null)
const loading = ref(true)
const seedText = ref('')
const agentCount = ref(200)
const selectedPersonaTypes = ref([])
const selectedIndustries = ref([])
const duration = ref(72)
const platformMode = ref('parallel')

onMounted(async () => {
  try {
    const res = await fetch(`/api/gtm/scenarios/${props.id}`)
    if (res.ok) {
      const data = await res.json()
      scenario.value = data
      seedText.value = data.seed_text || ''
      agentCount.value = Math.max(50, data.agent_config?.count || 200)
      selectedPersonaTypes.value = [...(data.agent_config?.persona_types || [])]
      selectedIndustries.value = [...(data.agent_config?.firmographic_mix?.industries || [])]
      duration.value = data.simulation_config?.total_hours || 72
      platformMode.value = data.simulation_config?.platform_mode || 'parallel'
    }
  } catch (e) {
    console.error('Failed to load scenario:', e)
  } finally {
    loading.value = false
  }
})

function togglePersonaType(type) {
  const idx = selectedPersonaTypes.value.indexOf(type)
  if (idx >= 0) selectedPersonaTypes.value.splice(idx, 1)
  else selectedPersonaTypes.value.push(type)
}

function toggleIndustry(industry) {
  const idx = selectedIndustries.value.indexOf(industry)
  if (idx >= 0) selectedIndustries.value.splice(idx, 1)
  else selectedIndustries.value.push(industry)
}

async function runSimulation() {
  // TODO: Call /api/graph/build with seed text, then navigate to graph view
  router.push(`/graph/demo-task-id`)
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
            v-model="seedText"
            rows="18"
            class="w-full border border-black/10 rounded-lg p-4 text-sm leading-relaxed focus:ring-2 focus:ring-[#2068FF] focus:border-transparent resize-y"
            placeholder="Enter your simulation seed document..."
          ></textarea>
        </div>

        <!-- Config Panel -->
        <div class="space-y-6">
          <!-- Agent Count -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Agent Count</label>
            <input type="range" v-model.number="agentCount" min="50" max="500" step="10" class="w-full accent-[#2068FF]" />
            <div class="text-center text-2xl font-semibold text-[#2068FF]">{{ agentCount }}</div>
          </div>

          <!-- Persona Types (multiselect) -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Persona Types</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="persona in scenario.agent_config?.persona_types || []"
                :key="persona"
                @click="togglePersonaType(persona)"
                class="px-3 py-1.5 text-xs rounded-full border transition-colors"
                :class="selectedPersonaTypes.includes(persona)
                  ? 'bg-[#2068FF] text-white border-[#2068FF]'
                  : 'bg-white text-[#555] border-black/10 hover:border-[#2068FF]'"
              >
                {{ persona }}
              </button>
            </div>
          </div>

          <!-- Industry Mix (checkboxes) -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Industry Mix</label>
            <div class="space-y-2">
              <label
                v-for="industry in scenario.agent_config?.firmographic_mix?.industries || []"
                :key="industry"
                class="flex items-center gap-2 text-sm text-[#050505] cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="selectedIndustries.includes(industry)"
                  @change="toggleIndustry(industry)"
                  class="rounded border-black/20 text-[#2068FF] focus:ring-[#2068FF]"
                />
                {{ industry }}
              </label>
            </div>
          </div>

          <!-- Duration -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Duration</label>
            <select v-model.number="duration" class="w-full border border-black/10 rounded-lg p-2 text-sm">
              <option :value="24">24 hours</option>
              <option :value="48">48 hours</option>
              <option :value="72">72 hours (recommended)</option>
            </select>
          </div>

          <!-- Platform Mode -->
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

          <!-- Run Simulation -->
          <button
            @click="runSimulation"
            class="w-full bg-[#2068FF] hover:bg-[#1a5ae0] text-white font-semibold py-3 rounded-lg transition-colors"
          >
            Run Simulation
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
