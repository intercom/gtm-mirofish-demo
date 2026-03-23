<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ id: String })
const router = useRouter()

const scenario = ref(null)
const loading = ref(true)
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
  // TODO: Call /api/graph/build with seed text, then navigate to graph view
  router.push(`/graph/demo-task-id`)
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-6 py-10">
    <div v-if="loading" class="text-center text-[#888] dark:text-[#666] py-20">Loading scenario...</div>

    <div v-else-if="scenario">
      <h1 class="text-3xl font-semibold text-[#050505] dark:text-[#e0e0e0] mb-2">{{ scenario.name }}</h1>
      <p class="text-sm text-[#555] dark:text-[#aaa] mb-8">{{ scenario.description }}</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Seed Document -->
        <div class="md:col-span-2">
          <label class="block text-xs uppercase tracking-wider text-[#888] dark:text-[#666] mb-2">Seed Document</label>
          <textarea
            v-model="scenario.seed_text"
            rows="12"
            class="w-full border border-black/10 dark:border-white/10 rounded-lg p-4 text-sm bg-white dark:bg-white/5 text-[#050505] dark:text-[#e0e0e0] focus:ring-2 focus:ring-[#2068FF] focus:border-transparent resize-y"
          ></textarea>
        </div>

        <!-- Config Panel -->
        <div class="space-y-6">
          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] dark:text-[#666] mb-2">Agent Count</label>
            <input type="range" v-model.number="agentCount" min="10" max="500" step="10" class="w-full" />
            <div class="text-center text-2xl font-semibold text-[#2068FF]">{{ agentCount }}</div>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] dark:text-[#666] mb-2">Duration (hours)</label>
            <select v-model.number="duration" class="w-full border border-black/10 dark:border-white/10 rounded-lg p-2 text-sm bg-white dark:bg-white/5 text-[#050505] dark:text-[#e0e0e0]">
              <option :value="24">24 hours</option>
              <option :value="48">48 hours</option>
              <option :value="72">72 hours (recommended)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wider text-[#888] dark:text-[#666] mb-2">Platform</label>
            <div class="flex gap-2">
              <button
                v-for="mode in ['twitter', 'reddit', 'parallel']"
                :key="mode"
                @click="platformMode = mode"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors capitalize"
                :class="platformMode === mode
                  ? 'bg-[#2068FF] text-white border-[#2068FF]'
                  : 'bg-white dark:bg-white/5 text-[#555] dark:text-[#aaa] border-black/10 dark:border-white/10 hover:border-[#2068FF]'"
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

    <div v-else class="text-center py-20">
      <p class="text-[#888] dark:text-[#666]">Scenario not found</p>
      <router-link to="/" class="text-[#2068FF] text-sm mt-2 inline-block">Back to Home</router-link>
    </div>
  </div>
</template>
