<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ id: String })
const router = useRouter()

const scenario = ref(null)
const loading = ref(true)
const error = ref(null)
const agentCount = ref(200)
const duration = ref(72)
const platformMode = ref('parallel')

async function loadScenario() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/gtm/scenarios/${props.id}`)
    if (!res.ok) throw new Error(`Server returned ${res.status}`)
    scenario.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadScenario)

async function runSimulation() {
  // TODO: Call /api/graph/build with seed text, then navigate to graph view
  router.push(`/graph/demo-task-id`)
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-6 py-10">
    <div v-if="loading" class="text-center py-20">
      <div class="inline-block w-6 h-6 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin mb-4"></div>
      <p class="text-sm text-[#888]">Loading scenario...</p>
    </div>

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

          <button
            @click="runSimulation"
            class="w-full bg-[#2068FF] hover:bg-[#1a5ae0] text-white font-semibold py-3 rounded-lg transition-colors"
          >
            Run Simulation
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="text-center py-20">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[rgba(255,86,0,0.1)] mb-4">
        <span class="text-xl">⚠️</span>
      </div>
      <p class="text-sm text-[#050505] font-medium mb-1">Failed to load scenario</p>
      <p class="text-xs text-[#888] mb-4">{{ error }}</p>
      <div class="flex items-center justify-center gap-3">
        <button @click="loadScenario" class="text-sm text-[#2068FF] hover:underline">Try again</button>
        <span class="text-[#888]">·</span>
        <router-link to="/" class="text-sm text-[#2068FF] hover:underline">Back to Home</router-link>
      </div>
    </div>

    <div v-else class="text-center py-20">
      <p class="text-[#888]">Scenario not found</p>
      <router-link to="/" class="text-[#2068FF] text-sm mt-2 inline-block hover:underline">Back to Home</router-link>
    </div>
  </div>
</template>
